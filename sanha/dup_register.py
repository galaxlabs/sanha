import frappe
import hashlib
import json
from frappe.utils import now_datetime


# ------------------------------
# Helpers
# ------------------------------

def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _has_workflow_state() -> bool:
    return frappe.db.has_column("Query", "workflow_state")


def _wf_value(row: dict, has_wf: bool) -> str:
    if not has_wf:
        return "Draft"
    ws = (row.get("workflow_state") or "").strip()
    return ws or "Draft"


def _make_group_key(scope: str, rm_norm: str, mf_norm: str) -> str:
    raw = "||".join([scope, rm_norm, mf_norm])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _scope_for_row(r: dict) -> str:
    """
    Scope:
      - if client_name present => client::<client_name_norm>
      - else                  => user::<owner>
    """
    cn_norm = _norm(r.get("client_name"))
    if cn_norm:
        return f"client::{cn_norm}"
    owner = (r.get("owner") or "").strip()
    return f"user::{owner}"


# ------------------------------
# SCAN DUPLICATES ON tabQuery
# ------------------------------

def scan_and_sync():
    """
    Duplicate rules:

      Key fields: raw_material + manufacturer
      Scope:
        - If client_name is set: same client_name (any user)
        - Else: same owner

      A duplicate group is: same (scope, raw_material_norm, manufacturer_norm)
      with count >= 2.

      For each group:
        - master = oldest (or oldest non-Draft)
        - is_duplicate = 1 for all in group
        - is_master    = 1 for master, 0 for others
        - can_delete   = 1 only for non-master draft docs
        - duplicate_group_key = hash(scope, rm, mf)

      Everything is done DIRECTLY on tabQuery (no Duplicate Register).
    """

    has_wf = _has_workflow_state()
    wf_select = ", workflow_state" if has_wf else ""

    # 1) Clear flags first
    frappe.db.sql("""
        UPDATE `tabQuery`
        SET is_duplicate = 0,
            is_master = 0,
            can_delete = 0,
            duplicate_group_key = NULL
    """)

    # 2) Load all queries (docstatus < 2)
    rows = frappe.db.sql(
        f"""
        SELECT
            name,
            creation,
            raw_material,
            manufacturer,
            client_name,
            owner,
            docstatus
            {wf_select}
        FROM `tabQuery`
        WHERE docstatus < 2
        """,
        as_dict=True,
    )

    # 3) Bucket by (scope, raw_material_norm, manufacturer_norm)
    buckets = {}
    for r in rows:
        rm_norm = _norm(r.get("raw_material"))
        mf_norm = _norm(r.get("manufacturer"))

        # Ignore rows without both rm & mf
        if not rm_norm and not mf_norm:
            continue

        scope = _scope_for_row(r)
        key = (scope, rm_norm, mf_norm)
        buckets.setdefault(key, []).append(r)

    # 4) Process buckets as duplicate groups
    for (scope, rm_norm, mf_norm), members in buckets.items():
        if len(members) < 2:
            continue

        group_key = _make_group_key(scope, rm_norm, mf_norm)
        members_sorted = sorted(members, key=lambda x: x["creation"])

        def wf(m):
            return _wf_value(m, has_wf)

        has_non_draft = any(wf(m) != "Draft" for m in members_sorted)

        # master = oldest non-draft if exists, else oldest
        master_name = None
        if has_non_draft:
            for m in members_sorted:
                if wf(m) != "Draft":
                    master_name = m["name"]
                    break
        if not master_name:
            master_name = members_sorted[0]["name"]

        # Mark flags using direct DB updates
        for m in members_sorted:
            name = m["name"]
            if not frappe.db.exists("Query", name):
                continue

            state = wf(m)
            is_master = (name == master_name)
            is_draft = (m.get("docstatus", 0) == 0 and state == "Draft")
            can_delete = (not is_master) and is_draft

            frappe.db.set_value(
                "Query",
                name,
                {
                    "is_duplicate": 1,
                    "is_master": 1 if is_master else 0,
                    "can_delete": 1 if can_delete else 0,
                    "duplicate_group_key": group_key,
                },
                update_modified=False,
            )

    frappe.db.commit()


# ------------------------------
# UI methods (buttons / list view)
# ------------------------------

@frappe.whitelist()
def scan_and_sync_ui():
    frappe.only_for(("System Manager", "Admin", "SB Uesr", "Administrator"))
    scan_and_sync()
    return {"ok": True, "message": "Duplicate flags updated on Query."}


@frappe.whitelist()
def delete_query_force(names):
    """
    Force delete queries from LIST VIEW.

    - is_master = 1 => skip (protect master).
    - Others: delete with force=1.
    - After deletion, re-run scan_and_sync() so flags are correct.
    """
    frappe.only_for(("System Manager", "Admin", "SB Uesr", "Administrator"))

    if isinstance(names, str):
        try:
            names = json.loads(names)
        except Exception:
            names = [names]

    if not isinstance(names, (list, tuple)):
        names = [names]

    deleted = []
    skipped_master = []
    missing = []

    for n in names:
        n = (n or "").strip()
        if not n:
            continue

        if not frappe.db.exists("Query", n):
            missing.append(n)
            continue

        q_is_master = frappe.db.get_value("Query", n, "is_master") or 0
        if int(q_is_master) == 1:
            skipped_master.append(n)
            continue

        frappe.delete_doc("Query", n, force=1, ignore_permissions=True)
        deleted.append(n)

    frappe.db.commit()

    try:
        scan_and_sync()
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "delete_query_force: scan_and_sync failed",
        )

    return {
        "deleted": deleted,
        "skipped_master": skipped_master,
        "missing": missing,
    }


# ------------------------------
# VALIDATE HOOK: block creating duplicates
# ------------------------------

def prevent_duplicate_on_validate(doc, method=None):
    """
    Block creation of duplicate Query for same scope:

      Scope:
        - If client_name: same client_name (any user)
        - Else: same owner

      Existing duplicate if:
        - same raw_material_norm
        - same manufacturer_norm
        - same scope
    """

    if doc.doctype != "Query":
        return

    rm_norm = _norm(getattr(doc, "raw_material", None))
    mf_norm = _norm(getattr(doc, "manufacturer", None))

    if not rm_norm and not mf_norm:
        return

    cn_norm = _norm(getattr(doc, "client_name", None))
    owner = (getattr(doc, "owner", None) or frappe.session.user or "").strip()

    if cn_norm:
        # Same client_name
        existing = frappe.db.sql(
            """
            SELECT name, raw_material, manufacturer, client_name
            FROM `tabQuery`
            WHERE name != %s
              AND docstatus < 2
              AND LOWER(TRIM(IFNULL(raw_material,''))) = %s
              AND LOWER(TRIM(IFNULL(manufacturer,''))) = %s
              AND LOWER(TRIM(IFNULL(client_name,''))) = %s
            """,
            (doc.name or "", rm_norm, mf_norm, cn_norm),
            as_dict=True,
        )
    else:
        # No client_name → same owner
        existing = frappe.db.sql(
            """
            SELECT name, raw_material, manufacturer, client_name
            FROM `tabQuery`
            WHERE name != %s
              AND docstatus < 2
              AND LOWER(TRIM(IFNULL(raw_material,''))) = %s
              AND LOWER(TRIM(IFNULL(manufacturer,''))) = %s
              AND owner = %s
            """,
            (doc.name or "", rm_norm, mf_norm, owner),
            as_dict=True,
        )

    if not existing:
        return

    ref = existing[0]
    url = f"/app/query/{ref['name']}"
    rm_label = ref.get("raw_material") or doc.raw_material or ""
    msg = (
        f"You already have this Query for <b>{frappe.utils.escape_html(rm_label)}</b>.<br>"
        f"Existing record: <a href='{url}' target='_blank'>{ref['name']}</a>"
    )

    frappe.throw(msg, frappe.DuplicateEntryError)

# import frappe
# import hashlib
# import json
# from frappe.utils import now_datetime


# # ------------------------------
# # Helpers
# # ------------------------------

# def _norm(s: str) -> str:
#     return (s or "").strip().lower()


# def _has_workflow_state() -> bool:
#     return frappe.db.has_column("Query", "workflow_state")


# def _wf_value(row: dict, has_wf: bool) -> str:
#     if not has_wf:
#         return "Draft"
#     ws = (row.get("workflow_state") or "").strip()
#     return ws or "Draft"


# def _make_group_key(scope: str, rm_norm: str, mf_norm: str) -> str:
#     raw = "||".join([scope, rm_norm, mf_norm])
#     return hashlib.sha1(raw.encode("utf-8")).hexdigest()


# def _scope_for_row(r: dict) -> str:
#     """Scope:
#         - if client_name present => client::<client_name>
#         - else => user::<owner>
#     """
#     cn_norm = _norm(r.get("client_name"))
#     if cn_norm:
#         return f"client::{cn_norm}"
#     owner = (r.get("owner") or "").strip()
#     return f"user::{owner}"


# # ------------------------------
# # SCAN DUPLICATES ON tabQuery
# # ------------------------------

# def scan_and_sync():
#     """
#     Duplicate rules:

#       Key fields: raw_material + manufacturer
#       Scope:
#         - If client_name is set: same client_name (any user)
#         - If client_name is empty: same owner (session user / record owner)

#       A duplicate group is: same (scope, raw_material_norm, manufacturer_norm)
#       with count >= 2.

#       For each group:
#         - master = oldest (or oldest non-Draft)
#         - is_duplicate = 1 for all in group
#         - is_master    = 1 for master, 0 for others
#         - can_delete   = 1 only for non-master draft docs
#         - duplicate_group_key = hash(scope, rm, mf)

#       Everything is done DIRECTLY on tabQuery. No Duplicate Register used.
#     """

#     has_wf = _has_workflow_state()
#     wf_select = ", workflow_state" if has_wf else ""

#     # 1) Clear flags first
#     frappe.db.sql("""
#         UPDATE `tabQuery`
#         SET is_duplicate = 0,
#             is_master = 0,
#             can_delete = 0,
#             duplicate_group_key = NULL
#     """)

#     # 2) Load all queries (safety: docstatus < 2)
#     rows = frappe.db.sql(
#         f"""
#         SELECT
#             name,
#             creation,
#             raw_material,
#             manufacturer,
#             client_name,
#             owner,
#             docstatus
#             {wf_select}
#         FROM `tabQuery`
#         WHERE docstatus < 2
#         """,
#         as_dict=True,
#     )

#     # 3) Bucket by scope + (raw_material_norm, manufacturer_norm)
#     buckets = {}
#     for r in rows:
#         rm_norm = _norm(r.get("raw_material"))
#         mf_norm = _norm(r.get("manufacturer"))

#         # Ignore garbage rows without both rm & mf
#         if not rm_norm and not mf_norm:
#             continue

#         scope = _scope_for_row(r)
#         key = (scope, rm_norm, mf_norm)
#         buckets.setdefault(key, []).append(r)

#     # 4) Process buckets with size >= 2 as duplicate groups
#     for (scope, rm_norm, mf_norm), members in buckets.items():
#         if len(members) < 2:
#             continue

#         group_key = _make_group_key(scope, rm_norm, mf_norm)

#         # Sort by creation (oldest first)
#         members_sorted = sorted(members, key=lambda x: x["creation"])

#         def wf(m):
#             return _wf_value(m, has_wf)

#         # Prefer non-draft as master if any
#         has_non_draft = any(wf(m) != "Draft" for m in members_sorted)

#         master_name = None
#         if has_non_draft:
#             for m in members_sorted:
#                 if wf(m) != "Draft":
#                     master_name = m["name"]
#                     break
#         if not master_name:
#             master_name = members_sorted[0]["name"]

#         # Mark each member in the group
#         for m in members_sorted:
#             name = m["name"]
#             if not frappe.db.exists("Query", name):
#                 continue

#             state = wf(m)
#             is_master = (name == master_name)
#             is_draft = (m.get("docstatus", 0) == 0 and state == "Draft")

#             # Only draft non-master are safe deletable
#             can_delete = (not is_master) and is_draft

#             qdoc = frappe.get_doc("Query", name)
#             qdoc.is_duplicate = 1
#             qdoc.is_master = 1 if is_master else 0
#             qdoc.can_delete = 1 if can_delete else 0
#             qdoc.duplicate_group_key = group_key

#             qdoc.flags.ignore_mandatory = True
#             qdoc.save(ignore_permissions=True)

#     frappe.db.commit()


# # ------------------------------
# # UI methods (buttons / list view)
# # ------------------------------

# @frappe.whitelist()
# def scan_and_sync_ui():
#     frappe.only_for(("System Manager", "Admin", "SB Uesr", "Administrator"))
#     scan_and_sync()
#     return {"ok": True, "message": "Duplicate flags updated on Query."}


# @frappe.whitelist()
# def delete_query_force(names):
#     """
#     Force delete queries from LIST VIEW.

#     - If is_master = 1 => skip (protect master).
#     - Others: delete with force=1.
#     - After deletion, re-run scan_and_sync() so flags are correct.
#     """
#     frappe.only_for(("System Manager", "Admin", "SB Uesr", "Administrator"))

#     if isinstance(names, str):
#         try:
#             names = json.loads(names)
#         except Exception:
#             names = [names]

#     if not isinstance(names, (list, tuple)):
#         names = [names]

#     deleted = []
#     skipped_master = []
#     missing = []

#     for n in names:
#         n = (n or "").strip()
#         if not n:
#             continue

#         if not frappe.db.exists("Query", n):
#             missing.append(n)
#             continue

#         qdoc = frappe.get_doc("Query", n)
#         if getattr(qdoc, "is_master", 0):
#             skipped_master.append(n)
#             continue

#         frappe.delete_doc("Query", n, force=1, ignore_permissions=True)
#         deleted.append(n)

#     frappe.db.commit()

#     try:
#         scan_and_sync()
#     except Exception:
#         frappe.log_error(
#             frappe.get_traceback(),
#             "delete_query_force: scan_and_sync failed",
#         )

#     return {
#         "deleted": deleted,
#         "skipped_master": skipped_master,
#         "missing": missing,
#     }


# # ------------------------------
# # VALIDATE HOOK: block creating duplicates
# # ------------------------------

# def prevent_duplicate_on_validate(doc, method=None):
#     """
#     Block creation of duplicate Query for same user/client scope.

#     Rules:
#       Scope:
#         - If client_name: same client_name (any user)
#         - Else: same owner

#       If a Query already exists with:
#         - same scope
#         - same raw_material
#         - same manufacturer

#       => Throw with a message:
#          "You already have this query: <link>"

#     Add in hooks.py:

#         doc_events = {
#             "Query": {
#                 "validate": "sanha.dup_register.prevent_duplicate_on_validate"
#             }
#         }
#     """

#     if doc.doctype != "Query":
#         return

#     rm_norm = _norm(getattr(doc, "raw_material", None))
#     mf_norm = _norm(getattr(doc, "manufacturer", None))

#     if not rm_norm and not mf_norm:
#         return

#     cn_norm = _norm(getattr(doc, "client_name", None))
#     owner = (getattr(doc, "owner", None) or frappe.session.user or "").strip()

#     # Where to look (scope logic)
#     # Case 1: client_name exists => match same client_name
#     if cn_norm:
#         existing = frappe.db.sql(
#             """
#             SELECT name, raw_material, manufacturer, client_name
#             FROM `tabQuery`
#             WHERE name != %s
#               AND docstatus < 2
#               AND LOWER(TRIM(IFNULL(raw_material,''))) = %s
#               AND LOWER(TRIM(IFNULL(manufacturer,''))) = %s
#               AND LOWER(TRIM(IFNULL(client_name,''))) = %s
#             """,
#             (doc.name or "", rm_norm, mf_norm, cn_norm),
#             as_dict=True,
#         )
#     else:
#         # Case 2: no client_name => same owner
#         existing = frappe.db.sql(
#             """
#             SELECT name, raw_material, manufacturer, client_name
#             FROM `tabQuery`
#             WHERE name != %s
#               AND docstatus < 2
#               AND LOWER(TRIM(IFNULL(raw_material,''))) = %s
#               AND LOWER(TRIM(IFNULL(manufacturer,''))) = %s
#               AND owner = %s
#             """,
#             (doc.name or "", rm_norm, mf_norm, owner),
#             as_dict=True,
#         )

#     if not existing:
#         return

#     # Just pick one reference record
#     ref = existing[0]
#     url = f"/app/query/{ref['name']}"
#     rm_label = ref.get("raw_material") or doc.raw_material or ""
#     msg = (
#         f"You already have this Query for <b>{frappe.utils.escape_html(rm_label)}</b>.<br>"
#         f"Existing record: <a href='{url}' target='_blank'>{ref['name']}</a>"
#     )

#     frappe.throw(msg, frappe.DuplicateEntryError)
