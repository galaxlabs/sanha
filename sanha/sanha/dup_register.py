import frappe
import hashlib
import json
from frappe.utils import now_datetime


# ----------------------------
# Helpers
# ----------------------------

def _norm(s: str) -> str:
    return (s or "").strip().lower()


def make_key(raw_material_norm: str, manufacturer_norm: str,
             discriminator_type: str, discriminator_value: str) -> str:
    """
    Build a stable key for a duplicate group.

    discriminator_type: "CLIENT" or "OWNER"
    discriminator_value: normalized client_name or owner
    """
    raw = "||".join([
        raw_material_norm,
        manufacturer_norm,
        discriminator_type.upper(),
        _norm(discriminator_value),
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _has_workflow_state() -> bool:
    return frappe.db.has_column("Query", "workflow_state")


def _wf_value(row: dict, has_wf: bool) -> str:
    """Return workflow_state; treat empty/missing as Draft."""
    if not has_wf:
        return "Draft"
    ws = (row.get("workflow_state") or "").strip()
    return ws or "Draft"


def _prune_missing_query_links(reg_doc):
    """Remove child rows whose Query link no longer exists (prevents LinkValidationError)."""
    kept = []
    for r in (reg_doc.get("items") or []):
        q = getattr(r, "query", None)
        if q and frappe.db.exists("Query", q):
            kept.append({
                "query": q,
                "query_creation": getattr(r, "query_creation", None),
                "query_workflow_state": getattr(r, "query_workflow_state", "") or "",
                "is_master": 1 if getattr(r, "is_master", 0) else 0,
                "can_delete": 1 if getattr(r, "can_delete", 0) else 0,
                "mark_for_delete": 1 if getattr(r, "mark_for_delete", 0) else 0,
            })
    reg_doc.set("items", kept)


def _sync_totals_from_items(reg_doc):
    """Update total_records and total_draft_records based on child rows."""
    items = reg_doc.items or []
    reg_doc.total_records = len(items)
    reg_doc.total_draft_records = sum(
        1 for i in items
        if (getattr(i, "query_workflow_state", "") or "") == "Draft"
    )


def _build_register_for_group(
    key: str,
    members: list[dict],
    has_wf: bool,
    active_keys: set[str],
):
    """
    Build or update one Query Duplicate Register group for a set of Query rows
    that share: raw_material + manufacturer + (same client OR same owner).
    """

    if len(members) < 2:
        return

    active_keys.add(key)

    def wf(m):
        return _wf_value(m, has_wf)

    # sort by creation for stable master selection
    members_sorted = sorted(members, key=lambda x: x["creation"])

    # decide master:
    #   if any non-draft => oldest non-draft
    #   else => oldest overall
    has_non_draft = any(wf(m) != "Draft" for m in members_sorted)
    master = None
    if has_non_draft:
        for m in members_sorted:
            if wf(m) != "Draft":
                master = m["name"]
                break
    if not master:
        master = members_sorted[0]["name"]

    # upsert Query Duplicate Register
    reg_name = frappe.db.get_value(
        "Query Duplicate Register",
        {"duplicate_key": key},
        "name"
    )
    reg = (
        frappe.get_doc("Query Duplicate Register", reg_name)
        if reg_name else
        frappe.new_doc("Query Duplicate Register")
    )

    first = members_sorted[0]

    reg.duplicate_key = key
    reg.raw_material = first.get("raw_material")
    reg.client_name = first.get("client_name")
    reg.supplier = first.get("supplier")  # not used in grouping now, but kept
    reg.manufacturer = first.get("manufacturer")
    reg.master_query = master
    reg.last_scanned_on = now_datetime()
    reg.status = "Active"

    reg.set("items", [])

    for m in members_sorted:
        name = m["name"]
        state = wf(m)
        is_master = (name == master)
        is_draft = (state == "Draft")

        # Draft duplicates (non-master) are deletable
        can_delete = (not is_master) and is_draft

        # Auto mark for delete only if this subgroup has any non-draft
        mark_for_delete = 1 if (has_non_draft and can_delete) else 0

        reg.append("items", {
            "query": name,
            "query_creation": m.get("creation"),
            "query_workflow_state": state,
            "is_master": 1 if is_master else 0,
            "can_delete": 1 if can_delete else 0,
            "mark_for_delete": mark_for_delete,
        })

        # ---- Also push flags back to Query row ----
        frappe.db.set_value(
            "Query",
            name,
            {
                "is_duplicate": 1,
                "is_master": 1 if is_master else 0,
                "can_delete": 1 if can_delete else 0,
                "duplicate_group_key": key,
            },
            update_modified=False,
        )

    _prune_missing_query_links(reg)
    _sync_totals_from_items(reg)
    reg.save(ignore_permissions=True)


# ----------------------------
# Core scan logic
# ----------------------------

def scan_and_sync():
    """
    Duplicate detection logic:

    1) First, group by:
         - normalized raw_material
         - normalized manufacturer

    2) Inside each (rm, mf) bucket:

       a) For rows WITH client_name:
          - group by normalized client_name
          - if group size >= 2 => duplicate group by CLIENT

       b) For rows WITHOUT client_name:
          - group by owner
          - if group size >= 2 => duplicate group by OWNER

    3) For each duplicate group:
       - choose master query (see _build_register_for_group)
       - auto mark draft duplicates for delete (if any non-draft exists)
       - write Query Duplicate Register row
       - set flags on Query rows:
         * is_duplicate, is_master, can_delete, duplicate_group_key
    """

    has_wf = _has_workflow_state()
    wf_select = ", workflow_state" if has_wf else ""

    # Reset duplicate flags on Query before recomputing
    frappe.db.sql("""
        UPDATE `tabQuery`
        SET is_duplicate = 0,
            is_master = 0,
            can_delete = 0,
            duplicate_group_key = NULL
    """)

    # Fetch all Query rows (not submitted concept; just docstatus < 2 for safety)
    rows = frappe.db.sql(
        f"""
        SELECT
            name,
            creation,
            raw_material,
            client_name,
            supplier,
            manufacturer,
            owner
            {wf_select}
        FROM `tabQuery`
        WHERE docstatus < 2
        """,
        as_dict=True,
    )

    # Bucket by (raw_material, manufacturer)
    buckets = {}
    for r in rows:
        rm_norm = _norm(r.get("raw_material"))
        mf_norm = _norm(r.get("manufacturer"))

        # if no raw_material AND no manufacturer → ignore (not useful for your logic)
        if not rm_norm and not mf_norm:
            continue

        key = (rm_norm, mf_norm)
        buckets.setdefault(key, []).append(r)

    active_keys: set[str] = set()

    # Process each (raw_material, manufacturer) bucket
    for (rm_norm, mf_norm), members in buckets.items():
        if len(members) < 2:
            continue

        # --- A) group by client_name for rows WITH client ---
        by_client = {}
        without_client = []

        for m in members:
            cn_norm = _norm(m.get("client_name"))
            if cn_norm:
                by_client.setdefault(cn_norm, []).append(m)
            else:
                without_client.append(m)

        # CLIENT-based groups
        for cn_norm, grp in by_client.items():
            if len(grp) < 2:
                continue
            key = make_key(rm_norm, mf_norm, "CLIENT", cn_norm)
            _build_register_for_group(key, grp, has_wf, active_keys)

        # --- B) group by owner for rows WITHOUT client_name ---
        by_owner = {}
        for m in without_client:
            ow = (m.get("owner") or "").strip()
            if not ow:
                continue
            by_owner.setdefault(ow, []).append(m)

        for ow, grp in by_owner.items():
            if len(grp) < 2:
                continue
            key = make_key(rm_norm, mf_norm, "OWNER", ow)
            _build_register_for_group(key, grp, has_wf, active_keys)

    # 3) resolve old registers that are no longer duplicates
    existing_regs = frappe.get_all(
        "Query Duplicate Register",
        filters={"status": "Active"},
        fields=["name", "duplicate_key"],
    )

    for r in existing_regs:
        if r["duplicate_key"] in active_keys:
            # still an active duplicate group this scan
            continue

        # no longer in active_keys => not a duplicate anymore
        doc = frappe.get_doc("Query Duplicate Register", r["name"])
        _prune_missing_query_links(doc)

        doc.status = "Resolved"
        # clear items so they don't show deleted / old queries
        doc.set("items", [])
        _sync_totals_from_items(doc)
        doc.last_scanned_on = now_datetime()
        doc.save(ignore_permissions=True)

    frappe.db.commit()


# ----------------------------
# Whitelisted methods for UI / API
# ----------------------------

@frappe.whitelist()
def scan_and_sync():
    """
    Duplicate detection logic:

    1) Bucket by:
         - normalized raw_material
         - normalized manufacturer

    2) Inside each (rm, mf) bucket, treat Query rows as nodes in a graph:
         - connect two nodes if:
              same normalized client_name  OR
              same owner
         - then each connected component with size >= 2 is a duplicate group.

    3) For each duplicate group:
         - choose master query:
              if any non-draft => oldest non-draft
              else => oldest overall
         - auto mark draft duplicates for delete (if any non-draft exists)
         - write/refresh Query Duplicate Register row
         - set flags on Query rows:
              is_duplicate, is_master, can_delete, duplicate_group_key
    """

    has_wf = _has_workflow_state()
    wf_select = ", workflow_state" if has_wf else ""

    # Reset duplicate flags on Query before recomputing
    frappe.db.sql("""
        UPDATE `tabQuery`
        SET is_duplicate = 0,
            is_master = 0,
            can_delete = 0,
            duplicate_group_key = NULL
    """)

    # Fetch all Query rows (docstatus < 2 for safety)
    rows = frappe.db.sql(
        f"""
        SELECT
            name,
            creation,
            raw_material,
            client_name,
            supplier,
            manufacturer,
            owner
            {wf_select}
        FROM `tabQuery`
        WHERE docstatus < 2
        """,
        as_dict=True,
    )

    # Bucket by (raw_material, manufacturer)
    buckets = {}
    for r in rows:
        rm_norm = _norm(r.get("raw_material"))
        mf_norm = _norm(r.get("manufacturer"))

        # ignore entries with no rm + no manufacturer
        if not rm_norm and not mf_norm:
            continue

        key = (rm_norm, mf_norm)
        buckets.setdefault(key, []).append(r)

    active_keys: set[str] = set()

    # Process each (raw_material, manufacturer) bucket
    for (rm_norm, mf_norm), members in buckets.items():
        n = len(members)
        if n < 2:
            continue

        # ----- union-find for this bucket -----
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        # connect nodes: same client OR same owner
        for i in range(n):
            mi = members[i]
            cn_i = _norm(mi.get("client_name"))
            owner_i = (mi.get("owner") or "").strip()

            for j in range(i + 1, n):
                mj = members[j]
                cn_j = _norm(mj.get("client_name"))
                owner_j = (mj.get("owner") or "").strip()

                same_client = cn_i and (cn_i == cn_j)
                same_owner = owner_i and (owner_i == owner_j)

                if same_client or same_owner:
                    union(i, j)

        # build components from union-find
        comps = {}
        for idx in range(n):
            root = find(idx)
            comps.setdefault(root, []).append(members[idx])

        # each component with size >= 2 => duplicate group
        for comp_members in comps.values():
            if len(comp_members) < 2:
                continue

            # choose discriminator primarily for key stability (for logging)
            first = comp_members[0]
            cn_norm = _norm(first.get("client_name"))
            if cn_norm:
                disc_type = "CLIENT"
                disc_value = cn_norm
            else:
                disc_type = "OWNER"
                disc_value = (first.get("owner") or "").strip()

            key = make_key(rm_norm, mf_norm, disc_type, disc_value)
            _build_register_for_group(key, comp_members, has_wf, active_keys)

    # 3) resolve old registers that are no longer duplicates
    existing_regs = frappe.get_all(
        "Query Duplicate Register",
        filters={"status": "Active"},
        fields=["name", "duplicate_key"],
    )

    for r in existing_regs:
        if r["duplicate_key"] in active_keys:
            # still an active duplicate group this scan
            continue

        # no longer in active_keys => not a duplicate anymore
        doc = frappe.get_doc("Query Duplicate Register", r["name"])
        _prune_missing_query_links(doc)

        doc.status = "Resolved"
        # clear items so they don't show deleted / old queries
        doc.set("items", [])
        _sync_totals_from_items(doc)
        doc.last_scanned_on = now_datetime()
        doc.save(ignore_permissions=True)

    frappe.db.commit()


@frappe.whitelist()
def delete_marked(register_name: str):
    """
    Force delete Query docs that are:
      - in this register
      - mark_for_delete = 1
      - can_delete = 1
      - NOT the master

    No workflow_state restriction anymore:
    if group logic marked it, we delete with force=1.

    After deletion, re-scan so deleted ones
    no longer appear in Duplicate Register or Query flags.
    """
    frappe.only_for(("System Manager", "Admin", "SB Uesr", "Administrator"))

    reg = frappe.get_doc("Query Duplicate Register", register_name)
    reg.check_permission("write")

    master = reg.master_query
    deleted = []

    for row in reg.items:
        if not row.mark_for_delete:
            continue
        if not row.can_delete:
            continue
        if row.query == master:
            continue
        if not row.query:
            continue
        if not frappe.db.exists("Query", row.query):
            continue

        # FORCE delete regardless of workflow_state / links
        frappe.delete_doc("Query", row.query, force=1)
        deleted.append(row.query)

    frappe.db.commit()

    # Rebuild registers + Query flags
    scan_and_sync()

    return {"deleted": deleted}


@frappe.whitelist()
def delete_query_force(names):
    """
    Force delete Query docs **even if linked** in Query Duplicate Register,
    for use from Query List (list-view buttons).

    names: list of Query names (or JSON string list).
    """
    frappe.only_for(("System Manager", "Admin", "SB Uesr", "Administrator"))

    # names can come as string or list from JS
    if isinstance(names, str):
        try:
            names = json.loads(names)
        except Exception:
            names = [names]

    if not isinstance(names, (list, tuple)):
        names = [names]

    deleted = []

    for n in names:
        if not n:
            continue
        if not frappe.db.exists("Query", n):
            continue

        frappe.delete_doc("Query", n, force=1)
        deleted.append(n)

    frappe.db.commit()

    # Keep register + Query flags in sync
    scan_and_sync()

    return {"deleted": deleted}



# import frappe
# import hashlib
# from frappe.utils import now_datetime


# # ----------------------------
# # Helpers
# # ----------------------------
# def _count_queries_for_register(reg_doc) -> int:
#     """Count how many Query rows still exist for this register's group values."""
#     return frappe.db.sql("""
#         SELECT COUNT(*)
#         FROM `tabQuery`
#         WHERE LOWER(TRIM(IFNULL(raw_material,'')))=%s
#           AND LOWER(TRIM(IFNULL(client_name,'')))=%s
#           AND LOWER(TRIM(IFNULL(supplier,'')))=%s
#           AND LOWER(TRIM(IFNULL(manufacturer,'')))=%s
#     """, (
#         _norm(getattr(reg_doc, "raw_material", "")),
#         _norm(getattr(reg_doc, "client_name", "")),
#         _norm(getattr(reg_doc, "supplier", "")),
#         _norm(getattr(reg_doc, "manufacturer", "")),
#     ))[0][0]


# def _norm(s: str) -> str:
#     return (s or "").strip().lower()


# def make_key(raw_material, client_name, supplier, manufacturer) -> str:
#     raw = "||".join([
#         _norm(raw_material),
#         _norm(client_name),
#         _norm(supplier),
#         _norm(manufacturer),
#     ])
#     return hashlib.sha1(raw.encode("utf-8")).hexdigest()


# def _has_workflow_state() -> bool:
#     return frappe.db.has_column("Query", "workflow_state")


# def _wf_value(row: dict, has_wf: bool) -> str:
#     """Return workflow_state; treat empty/missing as Draft."""
#     if not has_wf:
#         return "Draft"
#     ws = (row.get("workflow_state") or "").strip()
#     return ws or "Draft"


# def _prune_missing_query_links(reg_doc):
#     """Remove child rows whose Query link no longer exists (prevents LinkValidationError)."""
#     kept = []
#     for r in (reg_doc.get("items") or []):
#         q = getattr(r, "query", None)
#         if q and frappe.db.exists("Query", q):
#             kept.append({
#                 "query": q,
#                 "query_creation": getattr(r, "query_creation", None),
#                 "query_workflow_state": getattr(r, "query_workflow_state", "") or "",
#                 "is_master": 1 if getattr(r, "is_master", 0) else 0,
#                 "can_delete": 1 if getattr(r, "can_delete", 0) else 0,
#                 "mark_for_delete": 1 if getattr(r, "mark_for_delete", 0) else 0,
#             })
#     reg_doc.set("items", kept)


# def _sync_totals_from_items(reg_doc):
#     """Update total_records and total_draft_records based on child rows."""
#     items = reg_doc.items or []
#     reg_doc.total_records = len(items)
#     reg_doc.total_draft_records = sum(
#         1 for i in items
#         if (getattr(i, "query_workflow_state", "") or "") == "Draft"
#     )



# # ----------------------------
# # Core scan logic
# # ----------------------------
# def scan_and_sync():
#     """
#     Duplicate group (EXACT match, normalized):
#       raw_material + client_name + supplier + manufacturer

#     Rules:
#     - If ANY non-Draft exists in group:
#         master = oldest non-Draft
#         auto mark_for_delete=1 for Draft duplicates (non-master) only
#     - If ALL Draft:
#         master = oldest overall
#         mark_for_delete=0 (so you will NOT delete rest of drafts)
#     """
#     has_wf = _has_workflow_state()
#     wf_select = ", workflow_state" if has_wf else ""

#     # 1) find duplicate groups
#     groups = frappe.db.sql("""
#         SELECT
#           LOWER(TRIM(IFNULL(raw_material,''))) rm,
#           LOWER(TRIM(IFNULL(client_name,''))) cn,
#           LOWER(TRIM(IFNULL(supplier,''))) sp,
#           LOWER(TRIM(IFNULL(manufacturer,''))) mf,
#           COUNT(*) cnt
#         FROM `tabQuery`
#         GROUP BY rm, cn, sp, mf
#         HAVING cnt > 1
#     """, as_dict=True)

#     active_keys = set()

#     # 2) create/update registers for current duplicates
#     for g in groups:
#         key = make_key(g.rm, g.cn, g.sp, g.mf)
#         active_keys.add(key)

#         # fetch all members in this group, oldest first
#         members = frappe.db.sql(f"""
#             SELECT
#               name, creation,
#               raw_material, client_name, supplier, manufacturer
#               {wf_select}
#             FROM `tabQuery`
#             WHERE LOWER(TRIM(IFNULL(raw_material,'')))=%s
#               AND LOWER(TRIM(IFNULL(client_name,'')))=%s
#               AND LOWER(TRIM(IFNULL(supplier,'')))=%s
#               AND LOWER(TRIM(IFNULL(manufacturer,'')))=%s
#             ORDER BY creation ASC
#         """, (g.rm, g.cn, g.sp, g.mf), as_dict=True)

#         # filter out Query docs that were already deleted
#         members = [m for m in members if frappe.db.exists("Query", m["name"])]
#         if len(members) < 2:
#             # no longer duplicate, nothing to build for this group
#             continue

#         def wf(m):
#             return _wf_value(m, has_wf)

#         has_non_draft = any(wf(m) != "Draft" for m in members)

#         # master selection:
#         #   if any non-draft => oldest non-draft
#         #   else => oldest overall
#         master = None
#         if has_non_draft:
#             for m in members:
#                 if wf(m) != "Draft":
#                     master = m["name"]
#                     break
#         if not master:
#             master = members[0]["name"]

#         # upsert Query Duplicate Register
#         reg_name = frappe.db.get_value("Query Duplicate Register", {"duplicate_key": key}, "name")
#         reg = frappe.get_doc("Query Duplicate Register", reg_name) if reg_name else frappe.new_doc("Query Duplicate Register")

#         # group identity (Data fields on register)
#         reg.duplicate_key = key
#         reg.raw_material = members[0].get("raw_material")
#         reg.client_name = members[0].get("client_name")
#         reg.supplier = members[0].get("supplier")
#         reg.manufacturer = members[0].get("manufacturer")

#         reg.master_query = master
#         reg.last_scanned_on = now_datetime()
#         reg.status = "Active"

#         reg.set("items", [])

#         for m in members:
#             name = m["name"]
#             state = wf(m)

#             is_master = (name == master)
#             is_draft = (state == "Draft")

#             # Draft duplicates (non-master) are deletable
#             can_delete = (not is_master) and is_draft

#             # Only auto-mark for delete when the group has any non-draft
#             mark_for_delete = 1 if (has_non_draft and can_delete) else 0

#             reg.append("items", {
#                 "query": name,
#                 "query_creation": m.get("creation"),
#                 "query_workflow_state": state,
#                 "is_master": 1 if is_master else 0,
#                 "can_delete": 1 if can_delete else 0,
#                 "mark_for_delete": mark_for_delete,
#             })

#         # safety + totals
#         _prune_missing_query_links(reg)
#         _sync_totals_from_items(reg)
#         reg.save(ignore_permissions=True)

#     # 3) resolve old registers that are no longer duplicates
#     existing_regs = frappe.get_all(
#         "Query Duplicate Register",
#         filters={"status": "Active"},
#         fields=["name", "duplicate_key"],
#     )

#     for r in existing_regs:
#         if r["duplicate_key"] in active_keys:
#             # still an active duplicate group this scan
#             continue

#         # no longer in active_keys => not a duplicate anymore
#         doc = frappe.get_doc("Query Duplicate Register", r["name"])
#         _prune_missing_query_links(doc)
#         doc.status = "Resolved"
#         # optional: you can keep items for history, or clear them:
#         # doc.set("items", [])
#         _sync_totals_from_items(doc)
#         doc.last_scanned_on = now_datetime()
#         doc.save(ignore_permissions=True)

#     frappe.db.commit()


# # ----------------------------
# # Whitelisted methods for UI / API
# # ----------------------------
# @frappe.whitelist()
# def scan_and_sync_ui():
#     """Called from UI button."""
#     frappe.only_for(("System Manager", "Administrator"))
#     scan_and_sync()
#     return {"ok": True}


# @frappe.whitelist()
# def delete_marked(register_name: str):
#     """
#     Delete Query docs that are:
#       - in this register
#       - mark_for_delete = 1
#       - can_delete = 1
#       - NOT the master
#       - and (if workflow_state column exists) currently Draft
#     """
#     frappe.only_for(("System Manager", "Administrator"))

#     reg = frappe.get_doc("Query Duplicate Register", register_name)
#     reg.check_permission("write")

#     has_wf = _has_workflow_state()
#     master = reg.master_query
#     deleted = []

#     for row in reg.items:
#         if not row.mark_for_delete:
#             continue
#         if not row.can_delete:
#             continue
#         if row.query == master:
#             continue
#         if not row.query:
#             continue
#         if not frappe.db.exists("Query", row.query):
#             continue

#         # Safety: delete only Draft rows if workflow exists
#         if has_wf:
#             ws = (frappe.db.get_value("Query", row.query, "workflow_state") or "").strip() or "Draft"
#             if ws != "Draft":
#                 continue

#         frappe.delete_doc("Query", row.query, force=1)
#         deleted.append(row.query)

#     frappe.db.commit()

#     # After deletion, rebuild all registers (updates totals + resolves if needed)
#     scan_and_sync()

#     return {"deleted": deleted}
