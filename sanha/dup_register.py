import frappe
import hashlib
import json

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
        - master = oldest non-draft if exists, else oldest
        - is_duplicate = 1 for all in group
        - is_master    = 1 for master, 0 for others
        - can_delete   = 1 only for non-master draft docs
        - duplicate_group_key = hash(scope, rm, mf)

      Everything is done DIRECTLY on tabQuery (no Duplicate Register).
    """

    has_wf = _has_workflow_state()
    wf_select = ", workflow_state" if has_wf else ""

    # 1) Clear flags first
    frappe.db.sql(
        """
        UPDATE `tabQuery`
        SET is_duplicate = 0,
            is_master = 0,
            can_delete = 0,
            duplicate_group_key = NULL
    """
    )

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
            is_master = name == master_name
            is_draft = (m.get("docstatus", 0) == 0) and (state == "Draft")
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

    # re-scan in background / best-effort
    try:
        scan_and_sync()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "delete_query_force: scan_and_sync failed")

    return {
        "deleted": deleted,
        "skipped_master": skipped_master,
        "missing": missing,
    }


# ------------------------------
# EMAIL WHITELIST  +  CLIENT BY OWNER
# ------------------------------


def apply_email_notification_whitelist(doc):
    """
    Set doc.notify_client = 1 if doc.client_name is present in
    Email Notification Settings.enabled_clients.clients.
    Uses normalized comparison to avoid space/case mismatch.
    """
    if doc.doctype != "Query":
        return

    client_name = (doc.client_name or "").strip()

    if not client_name:
        doc.notify_client = 0
        return

    try:
        settings = frappe.get_doc("Email Notification Settings")
    except frappe.DoesNotExistError:
        doc.notify_client = 0
        return

    allowed_clients = {
        (row.clients or "").strip().lower()
        for row in settings.enabled_clients
        if row.clients
    }

    doc.notify_client = 1 if client_name.lower() in allowed_clients else 0

    frappe.logger("sanha_email_notify").info({
        "query": doc.name,
        "client_name_checked": client_name,
        "notify_client": doc.notify_client,
    })


def debug_query_validate_flow(query_name):
    """
    Return current Query validate-related state without saving.
    Shows owner, client before/after enforce, notify before/after whitelist,
    and active whitelist matches.
    """
    q = frappe.get_doc("Query", query_name)

    before_client = q.client_name
    before_notify = q.notify_client

    try:
        enforce_client_from_owner(q)
        after_enforce_client = q.client_name
    except Exception as e:
        after_enforce_client = f"ERROR: {str(e)}"

    try:
        apply_email_notification_whitelist(q)
        after_notify = q.notify_client
    except Exception as e:
        after_notify = f"ERROR: {str(e)}"

    settings = frappe.get_doc("Email Notification Settings")
    client_name = (q.client_name or "").strip().lower()
    whitelist_matches = [
        row.clients for row in settings.enabled_clients
        if (row.clients or "").strip().lower() == client_name
    ]

    return {
        "query": q.name,
        "owner": q.owner,
        "before_client": before_client,
        "before_notify": before_notify,
        "after_enforce_client": after_enforce_client,
        "after_notify": after_notify,
        "whitelist_matches": whitelist_matches,
    }


def debug_email_notification_for_query(query_name):
    return debug_query_validate_flow(query_name)


def get_client_by_owner_email(owner_email: str) -> str:
    """
    Map owner email -> Client (unique).
    """
    if not owner_email:
        frappe.throw("Owner email is empty; cannot resolve Client.")

    names = frappe.get_all(
        "Client",
        filters={"email": owner_email},
        pluck="name",
        limit_page_length=2,
        ignore_permissions=True,
    )

    if not names:
        frappe.throw(f"No Client found with email = {owner_email}")

    if len(names) > 1:
        frappe.throw(f"Multiple Clients found for email = {owner_email}. Fix duplicates.")

    return names[0]


def enforce_client_from_owner(doc):
    """
    Ensure doc.client_name is always aligned to owner email.
    Called on validate BEFORE duplicate check so scope is correct.
    """
    owner_email = doc.owner or frappe.session.user
    if not owner_email:
        return

    target_client = get_client_by_owner_email(owner_email)

    # If empty or wrong, force it.
    if doc.client_name != target_client:
        doc.client_name = target_client


# ------------------------------
# DOCUMENTS VALIDATION ON STATE CHANGE
# ------------------------------


def validate_documents_on_state_change(doc):
    """
    Only enforce documents when moving OUT OF Draft (workflow_state).
    This avoids blocking the very first save when the doc is just being created.
    """

    old = doc.get_doc_before_save()
    old_state = (old.workflow_state if old and old.workflow_state else "Draft")
    new_state = (doc.workflow_state or "Draft")

    # Only validate when moving OUT of Draft
    should_validate = old_state == "Draft" and new_state != "Draft"
    if not should_validate:
        return

    if not doc.get("documents"):
        frappe.throw("Please add at least one row in Documents before proceeding.")

    req_issue = {
        "MSDS",
        "Halal Declaration",
        "TDS",
        "SDS",
        "Product Spec",
        "PDS",
        "Lab Sample Report",
        "Halal Questionnaire",
        "Declaration",
        "Halal Certificate",
    }

    for i, row in enumerate(doc.get("documents"), start=1):
        if not row.attachment:
            frappe.throw(f"Row #{i}: Please attach a file.")

        if row.documents in req_issue and not row.issue_date:
            frappe.throw(f"Row #{i}: Issue Date is required for {row.documents}.")

        if row.documents == "Halal Certificate" and not row.expiry_date:
            frappe.throw(f"Row #{i}: Expiry Date is required for Halal Certificate.")


# ------------------------------
# DUPLICATE PREVENTION ON VALIDATE
# ------------------------------


# def prevent_duplicate_on_validate(doc, method=None):
#     """
#     Block creation of duplicate Query for same scope:

#       Scope:
#         - If client_name: same client_name (any user)
#         - Else: same owner

#       Existing duplicate if:
#         - same raw_material_norm
#         - same manufacturer_norm
#         - same scope
#         - docstatus < 2

#     NOTE:
#       - We allow early saves where raw_material or manufacturer is missing.
#       - Once both are present, this will strictly block duplicates, regardless of workflow_state.
#     """

#     if doc.doctype != "Query":
#         return

#     rm_norm = _norm(getattr(doc, "raw_material", None))
#     mf_norm = _norm(getattr(doc, "manufacturer", None))

#     # Allow saving while incomplete (only enforce once both filled)
#     if not rm_norm or not mf_norm:
#         return

#     cn_norm = _norm(getattr(doc, "client_name", None))
#     owner = (getattr(doc, "owner", None) or frappe.session.user or "").strip()

#     if cn_norm:
#         # Same client_name (any user)
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
#         # No client_name → protect per owner
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

#     ref = existing[0]
#     url = f"/app/query/{ref['name']}"
#     rm_label = ref.get("raw_material") or doc.raw_material or ""
#     msg = (
#         f"You already have this Query for <b>{frappe.utils.escape_html(rm_label)}</b>.<br>"
#         f"Existing record: <a href='{url}' target='_blank'>{ref['name']}</a>"
#     )

#     frappe.throw(msg, frappe.DuplicateEntryError)
def prevent_duplicate_on_validate(doc, method=None):
    """
    New rules:

    - We enforce duplicates as soon as raw_material is set.
    - If current doc has manufacturer:
        -> match duplicates on (raw_material + manufacturer + scope)
    - If current doc has NO manufacturer:
        -> match duplicates on (raw_material + scope) ONLY
          (manufacturer of existing records can be anything / empty).

    Scope:
      - If client_name present -> same client_name (any user)
      - Else                  -> same owner
    """

    if doc.doctype != "Query":
        return

    # 1) Must at least have raw_material; otherwise allow save
    rm_norm = _norm(getattr(doc, "raw_material", None))
    if not rm_norm:
        return

    mf_norm = _norm(getattr(doc, "manufacturer", None))

    cn_norm = _norm(getattr(doc, "client_name", None))
    owner = (getattr(doc, "owner", None) or frappe.session.user or "").strip()

    # 2) Build WHERE conditions dynamically
    conditions = [
        "name != %s",
        "docstatus < 2",
        "LOWER(TRIM(IFNULL(raw_material,''))) = %s",
    ]
    params = [doc.name or "", rm_norm]

    if cn_norm:
        # Same client
        conditions.append("LOWER(TRIM(IFNULL(client_name,''))) = %s")
        params.append(cn_norm)
    else:
        # Same owner
        conditions.append("owner = %s")
        params.append(owner)

    # 3) Manufacturer condition is OPTIONAL:
    #    - If current doc has manufacturer => require same manufacturer
    #    - If empty => ignore manufacturer in matching
    if mf_norm:
        conditions.append("LOWER(TRIM(IFNULL(manufacturer,''))) = %s")
        params.append(mf_norm)

    sql = f"""
        SELECT name, raw_material, manufacturer, client_name
        FROM `tabQuery`
        WHERE {' AND '.join(conditions)}
    """

    existing = frappe.db.sql(sql, params, as_dict=True)

    if not existing:
        return

    # 4) We found at least one duplicate in the same scope
    ref = existing[0]
    url = f"/app/query/{ref['name']}"
    rm_label = ref.get("raw_material") or doc.raw_material or ""
    msg = (
        f"You already have this Query for "
        f"<b>{frappe.utils.escape_html(rm_label)}</b>.<br>"
        f"Existing record: <a href='{url}' target='_blank'>{ref['name']}</a>"
    )

    frappe.throw(msg, frappe.DuplicateEntryError)


# ------------------------------
# MASTER VALIDATE ENTRY POINT
# ------------------------------


def validate_query(doc, method=None):
    """
    Single validate hook for Query that:
      1) Forces client_name from owner email
      2) Sets notify_client from Email Notification Settings
      3) Validates Documents when leaving Draft
      4) Prevents duplicates strictly (using above rules)
    """

    if doc.doctype != "Query":
        return

    # 1) Force client_name from owner email (scope must be correct)
    enforce_client_from_owner(doc)

    # 2) Set notify_client based on Email Notification Settings
    apply_email_notification_whitelist(doc)

    # 3) Validate documents only when workflow_state moves Draft -> anything else
    validate_documents_on_state_change(doc)

    # 4) Strict duplicate prevention (raw_material + manufacturer + scope)
    prevent_duplicate_on_validate(doc, method)
