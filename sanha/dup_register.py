import frappe
import hashlib
from frappe.utils import now_datetime


# ----------------------------
# Helpers
# ----------------------------
def _norm(s: str) -> str:
    return (s or "").strip().lower()


def make_key(raw_material, client_name, supplier, manufacturer) -> str:
    raw = "||".join([
        _norm(raw_material),
        _norm(client_name),
        _norm(supplier),
        _norm(manufacturer),
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _has_workflow_state() -> bool:
    return frappe.db.has_column("Query", "workflow_state")


def _wf_value(row: dict, has_wf: bool) -> str:
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
    reg_doc.total_records = len(reg_doc.items or [])
    reg_doc.total_draft_records = sum(
        1 for i in (reg_doc.items or [])
        if (getattr(i, "query_workflow_state", "") or "") == "Draft"
    )


def _get_members_for_group(rm, cn, sp, mf, has_wf: bool):
    """Fetch all members for a group, oldest first."""
    wf_select = ", workflow_state" if has_wf else ""
    members = frappe.db.sql(f"""
        SELECT
          name, creation,
          raw_material, client_name, supplier, manufacturer
          {wf_select}
        FROM `tabQuery`
        WHERE LOWER(TRIM(IFNULL(raw_material,'')))=%s
          AND LOWER(TRIM(IFNULL(client_name,'')))=%s
          AND LOWER(TRIM(IFNULL(supplier,'')))=%s
          AND LOWER(TRIM(IFNULL(manufacturer,'')))=%s
        ORDER BY creation ASC
    """, (rm, cn, sp, mf), as_dict=True)

    # remove already deleted queries
    return [m for m in members if frappe.db.exists("Query", m["name"])]


def _refresh_register_doc(reg):
    """
    Refresh ONE register doc:
    - Rebuild items if still duplicate (>=2)
    - Otherwise mark Resolved and clear items + update totals
    """
    has_wf = _has_workflow_state()

    rm = _norm(reg.raw_material)
    cn = _norm(reg.client_name)
    sp = _norm(reg.supplier)
    mf = _norm(reg.manufacturer)

    members = _get_members_for_group(rm, cn, sp, mf, has_wf)

    if len(members) < 2:
        # no longer duplicate -> resolve + clear items (so totals become 0)
        reg.status = "Resolved"
        reg.master_query = None
        reg.set("items", [])
        reg.last_scanned_on = now_datetime()
        _sync_totals_from_items(reg)
        reg.save(ignore_permissions=True)
        return

    def wf(m):
        return _wf_value(m, has_wf)

    has_non_draft = any(wf(m) != "Draft" for m in members)

    # master: oldest non-draft if exists, else oldest overall
    master = None
    if has_non_draft:
        for m in members:
            if wf(m) != "Draft":
                master = m["name"]
                break
    if not master:
        master = members[0]["name"]

    reg.master_query = master
    reg.status = "Active"
    reg.last_scanned_on = now_datetime()

    reg.set("items", [])
    for m in members:
        name = m["name"]
        state = wf(m)

        is_master = (name == master)
        is_draft = (state == "Draft")

        can_delete = (not is_master) and is_draft

        # ✅ only auto-mark drafts if group has any non-draft
        # (so we will NOT delete the rest of draft-only groups)
        mark_for_delete = 1 if (has_non_draft and can_delete) else 0

        reg.append("items", {
            "query": name,
            "query_creation": m.get("creation"),
            "query_workflow_state": state,
            "is_master": 1 if is_master else 0,
            "can_delete": 1 if can_delete else 0,
            "mark_for_delete": mark_for_delete,
        })

    _prune_missing_query_links(reg)
    _sync_totals_from_items(reg)
    reg.save(ignore_permissions=True)


# ----------------------------
# Daily scan (creates/updates duplicates + resolves old)
# ----------------------------
def scan_and_sync():
    has_wf = _has_workflow_state()

    groups = frappe.db.sql("""
        SELECT
          LOWER(TRIM(IFNULL(raw_material,''))) rm,
          LOWER(TRIM(IFNULL(client_name,''))) cn,
          LOWER(TRIM(IFNULL(supplier,''))) sp,
          LOWER(TRIM(IFNULL(manufacturer,''))) mf,
          COUNT(*) cnt
        FROM `tabQuery`
        GROUP BY rm, cn, sp, mf
        HAVING cnt > 1
    """, as_dict=True)

    # 1) upsert registers for all duplicate groups
    for g in groups:
        key = make_key(g.rm, g.cn, g.sp, g.mf)

        reg_name = frappe.db.get_value("Query Duplicate Register", {"duplicate_key": key}, "name")
        reg = frappe.get_doc("Query Duplicate Register", reg_name) if reg_name else frappe.new_doc("Query Duplicate Register")

        # store group identity for future refresh (case-insensitive matching uses SQL lower/trim)
        members = _get_members_for_group(g.rm, g.cn, g.sp, g.mf, has_wf)
        if len(members) < 2:
            continue

        reg.duplicate_key = key
        reg.raw_material = members[0].get("raw_material")
        reg.client_name = members[0].get("client_name")
        reg.supplier = members[0].get("supplier")
        reg.manufacturer = members[0].get("manufacturer")

        _refresh_register_doc(reg)

    # 2) refresh ALL Active registers to resolve those that became non-duplicates
    active_regs = frappe.get_all("Query Duplicate Register", filters={"status": "Active"}, pluck="name")
    for name in active_regs:
        reg = frappe.get_doc("Query Duplicate Register", name)
        _refresh_register_doc(reg)

    frappe.db.commit()


# ----------------------------
# UI endpoints
# ----------------------------
@frappe.whitelist()
def scan_and_sync_ui():
    frappe.only_for(("System Manager", "Administrator"))
    scan_and_sync()
    return {"ok": True}


@frappe.whitelist()
def delete_marked(register_name: str):
    frappe.only_for(("System Manager", "Administrator"))

    reg = frappe.get_doc("Query Duplicate Register", register_name)
    reg.check_permission("write")

    has_wf = _has_workflow_state()
    master = reg.master_query
    deleted = []

    for row in reg.items:
        if not row.mark_for_delete:
            continue
        if not row.can_delete:
            continue
        if row.query == master:
            continue
        if not frappe.db.exists("Query", row.query):
            continue

        # Safety: delete only Draft rows
        if has_wf:
            ws = (frappe.db.get_value("Query", row.query, "workflow_state") or "").strip() or "Draft"
            if ws != "Draft":
                continue

        frappe.delete_doc("Query", row.query, force=1)
        deleted.append(row.query)

    frappe.db.commit()

    # ✅ key part: refresh THIS register immediately, so it becomes Resolved / counts update
    reg = frappe.get_doc("Query Duplicate Register", register_name)
    _refresh_register_doc(reg)

    return {"deleted": deleted, "status": reg.status, "total_records": reg.total_records}

# import frappe
# import hashlib
# from frappe.utils import now_datetime


# # ----------------------------
# # Helpers
# # ----------------------------
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
#     reg_doc.total_records = len(reg_doc.items or [])
#     reg_doc.total_draft_records = sum(
#         1 for i in (reg_doc.items or [])
#         if (getattr(i, "query_workflow_state", "") or "") == "Draft"
#     )


# def _count_queries_for_register(reg_doc) -> int:
#     """Count remaining Query records for this register's group values."""
#     return frappe.db.sql("""
#         SELECT COUNT(*)
#         FROM `tabQuery`
#         WHERE LOWER(TRIM(IFNULL(raw_material,'')))=%s
#           AND LOWER(TRIM(IFNULL(client_name,'')))=%s
#           AND LOWER(TRIM(IFNULL(supplier,'')))=%s
#           AND LOWER(TRIM(IFNULL(manufacturer,'')))=%s
#     """, (
#         _norm(reg_doc.raw_material),
#         _norm(reg_doc.client_name),
#         _norm(reg_doc.supplier),
#         _norm(reg_doc.manufacturer),
#     ))[0][0]


# ----------------------------
# Core Scan
# ----------------------------
def scan_and_sync():
    """
    Duplicate group (EXACT match, normalized):
      raw_material + client_name + supplier + manufacturer

    Rules:
    - If ANY non-Draft exists in group:
        master = oldest non-Draft
        auto mark_for_delete=1 for Draft duplicates (non-master) only
    - If ALL Draft:
        master = oldest overall
        mark_for_delete=0 (so you will NOT delete rest of drafts)
    """
    has_wf = _has_workflow_state()
    wf_select = ", workflow_state" if has_wf else ""

    # 1) find duplicate groups
    groups = frappe.db.sql("""
        SELECT
          LOWER(TRIM(IFNULL(raw_material,''))) rm,
          LOWER(TRIM(IFNULL(client_name,''))) cn,
          LOWER(TRIM(IFNULL(supplier,''))) sp,
          LOWER(TRIM(IFNULL(manufacturer,''))) mf,
          COUNT(*) cnt
        FROM `tabQuery`
        GROUP BY rm, cn, sp, mf
        HAVING cnt > 1
    """, as_dict=True)

    active_keys = set()

    # 2) create/update registers for current duplicates
    for g in groups:
        key = make_key(g.rm, g.cn, g.sp, g.mf)
        active_keys.add(key)

        members = frappe.db.sql(f"""
            SELECT
              name, creation,
              raw_material, client_name, supplier, manufacturer
              {wf_select}
            FROM `tabQuery`
            WHERE LOWER(TRIM(IFNULL(raw_material,'')))=%s
              AND LOWER(TRIM(IFNULL(client_name,'')))=%s
              AND LOWER(TRIM(IFNULL(supplier,'')))=%s
              AND LOWER(TRIM(IFNULL(manufacturer,'')))=%s
            ORDER BY creation ASC
        """, (g.rm, g.cn, g.sp, g.mf), as_dict=True)

        # keep only existing Query docs
        members = [m for m in members if frappe.db.exists("Query", m["name"])]
        if len(members) < 2:
            continue

        def wf(m):
            return _wf_value(m, has_wf)

        has_non_draft = any(wf(m) != "Draft" for m in members)

        # master selection
        master = None
        if has_non_draft:
            for m in members:
                if wf(m) != "Draft":
                    master = m["name"]
                    break
        if not master:
            master = members[0]["name"]

        # upsert register
        reg_name = frappe.db.get_value("Query Duplicate Register", {"duplicate_key": key}, "name")
        reg = frappe.get_doc("Query Duplicate Register", reg_name) if reg_name else frappe.new_doc("Query Duplicate Register")

        reg.duplicate_key = key
        reg.raw_material = members[0].get("raw_material")
        reg.client_name = members[0].get("client_name")  # Data
        reg.supplier = members[0].get("supplier")
        reg.manufacturer = members[0].get("manufacturer")
        reg.master_query = master
        reg.last_scanned_on = now_datetime()
        reg.status = "Active"

        reg.set("items", [])

        for m in members:
            name = m["name"]
            state = wf(m)

            is_master = (name == master)
            is_draft = (state == "Draft")

            can_delete = (not is_master) and is_draft

            # ✅ only auto-mark drafts if group has any non-draft
            mark_for_delete = 1 if (has_non_draft and can_delete) else 0

            reg.append("items", {
                "query": name,
                "query_creation": m.get("creation"),
                "query_workflow_state": state,
                "is_master": 1 if is_master else 0,
                "can_delete": 1 if can_delete else 0,
                "mark_for_delete": mark_for_delete,
            })

        # safety + totals
        _prune_missing_query_links(reg)
        _sync_totals_from_items(reg)

        reg.save(ignore_permissions=True)

    # 3) Resolve registers that are no longer duplicates (count < 2)
    for r in frappe.get_all("Query Duplicate Register", filters={"status": "Active"}, fields=["name", "duplicate_key"]):
        if r["duplicate_key"] in active_keys:
            continue

        doc = frappe.get_doc("Query Duplicate Register", r["name"])

        # if now only 0/1 Query exists => resolve
        if _count_queries_for_register(doc) < 2:
            _prune_missing_query_links(doc)
            doc.status = "Resolved"
            doc.last_scanned_on = now_datetime()
            _sync_totals_from_items(doc)
            doc.save(ignore_permissions=True)

    frappe.db.commit()


# ----------------------------
# UI + Delete
# ----------------------------
@frappe.whitelist()
def scan_and_sync_ui():
    frappe.only_for(("System Manager", "Administrator"))
    scan_and_sync()
    return {"ok": True}


@frappe.whitelist()
def delete_marked(register_name: str):
    frappe.only_for(("System Manager", "Administrator"))

    reg = frappe.get_doc("Query Duplicate Register", register_name)
    reg.check_permission("write")

    has_wf = _has_workflow_state()
    master = reg.master_query
    deleted = []

    for row in reg.items:
        if not row.mark_for_delete:
            continue
        if not row.can_delete:
            continue
        if row.query == master:
            continue
        if not frappe.db.exists("Query", row.query):
            continue

        # Safety: delete only Draft rows
        if has_wf:
            ws = (frappe.db.get_value("Query", row.query, "workflow_state") or "").strip() or "Draft"
            if ws != "Draft":
                continue

        frappe.delete_doc("Query", row.query, force=1)
        deleted.append(row.query)

    frappe.db.commit()

    # rebuild register/totals + resolve if no longer duplicate
    scan_and_sync()

    return {"deleted": deleted}

# import frappe
# import hashlib
# from frappe.utils import now_datetime


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


# def scan_and_sync():
#     """
#     Exact duplicates group:
#       raw_material + client_name + supplier + manufacturer (normalized)

#     Rules:
#     - If ANY non-Draft exists in group:
#         master = oldest non-Draft
#         mark_for_delete = 1 for Draft duplicates (non-master) only
#       Else (all Draft):
#         master = oldest overall
#         mark_for_delete = 0 (so you will NOT delete rest of drafts)
#     """
#     has_wf = _has_workflow_state()
#     wf_select = ", workflow_state" if has_wf else ""

#     # 1) find duplicate groups (no docstatus)
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

#     for g in groups:
#         key = make_key(g.rm, g.cn, g.sp, g.mf)
#         active_keys.add(key)

#         # 2) fetch members oldest first
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

#         # keep only existing Query docs
#         members = [m for m in members if frappe.db.exists("Query", m["name"])]
#         if len(members) < 2:
#             continue

#         def wf(m):
#             return _wf_value(m, has_wf)

#         has_non_draft = any(wf(m) != "Draft" for m in members)

#         # 3) master selection
#         master = None
#         if has_non_draft:
#             for m in members:
#                 if wf(m) != "Draft":
#                     master = m["name"]
#                     break
#         if not master:
#             master = members[0]["name"]

#         total_records = len(members)
#         total_draft_records = sum(1 for m in members if wf(m) == "Draft")

#         # 4) upsert register
#         reg_name = frappe.db.get_value("Query Duplicate Register", {"duplicate_key": key}, "name")
#         reg = frappe.get_doc("Query Duplicate Register", reg_name) if reg_name else frappe.new_doc("Query Duplicate Register")

#         reg.duplicate_key = key
#         reg.raw_material = members[0].get("raw_material")
#         reg.client_name = members[0].get("client_name")  # Data field
#         reg.supplier = members[0].get("supplier")
#         reg.manufacturer = members[0].get("manufacturer")
#         reg.master_query = master
#         reg.total_records = total_records
#         reg.total_draft_records = total_draft_records
#         reg.last_scanned_on = now_datetime()
#         reg.status = "Active"

#         reg.set("items", [])

#         for m in members:
#             name = m["name"]
#             state = wf(m)

#             is_master = (name == master)
#             is_draft = (state == "Draft")

#             can_delete = (not is_master) and is_draft
#             # ✅ IMPORTANT: do NOT delete rest of Drafts (only when non-draft exists)
#             mark_for_delete = 1 if (has_non_draft and can_delete) else 0

#             reg.append("items", {
#                 "query": name,
#                 "query_creation": m.get("creation"),
#                 "query_workflow_state": state,
#                 "is_master": 1 if is_master else 0,
#                 "can_delete": 1 if can_delete else 0,
#                 "mark_for_delete": mark_for_delete,
#             })

#         # extra safety: prune before save
#         _prune_missing_query_links(reg)
#         reg.save(ignore_permissions=True)

#     # 5) resolve old ones (ALSO prune before saving!)
#     for r in frappe.get_all("Query Duplicate Register", filters={"status": "Active"}, fields=["name", "duplicate_key"]):
#         if r["duplicate_key"] not in active_keys:
#             doc = frappe.get_doc("Query Duplicate Register", r["name"])
#             _prune_missing_query_links(doc)
#             doc.status = "Resolved"
#             doc.last_scanned_on = now_datetime()
#             doc.save(ignore_permissions=True)

#     frappe.db.commit()


# @frappe.whitelist()
# def scan_and_sync_ui():
#     frappe.only_for(("System Manager", "Administrator"))
#     scan_and_sync()
#     return {"ok": True}


# @frappe.whitelist()
# def delete_marked(register_name: str):
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
#         if not frappe.db.exists("Query", row.query):
#             continue

#         # Safety: delete ONLY Draft if workflow exists
#         if has_wf:
#             ws = (frappe.db.get_value("Query", row.query, "workflow_state") or "").strip() or "Draft"
#             if ws != "Draft":
#                 continue

#         frappe.delete_doc("Query", row.query, force=1)
#         deleted.append(row.query)

#     frappe.db.commit()

#     # After delete, a scan will rebuild + prune everywhere
#     scan_and_sync()
#     return {"deleted": deleted}

