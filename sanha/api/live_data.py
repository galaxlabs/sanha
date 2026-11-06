"""Permission-checked dataset deltas. Browser receives only changed/deleted rows."""
import hashlib
import json
import re
from uuid import uuid4

import frappe
from frappe.utils import now, cint
from sanha.api.auth import _find_client
from sanha.api.messaging import is_staff
from sanha.api.dashboard import overview_metrics

SCHEMA = 1
FIELDS = {
    "Query": ["name", "raw_material", "supplier", "supplier_contact", "manufacturer", "manufacturer_contact", "workflow_state", "query_types", "client_name", "client_code", "owner", "creation", "modified", "is_duplicate", "is_master"],
    "Client": ["name", "client_name", "client_code", "email", "city", "creation", "modified", "owner", "business_name", "certified_since", "certified_expiry", "ext", "standards", "region", "scope", "category", "status", "contact_person", "contact_no", "telephone", "address", "address_type", "products", "is_active"],
    "E-NUMBERS": ["name", "code", "name1", "alternative_name", "function", "status", "source", "health_info", "uses", "other_uses", "creation", "modified"],
    "Templates": ["name", "title", "text_template", "modified"],
    "Learning Playlist": ["name", "title", "subject", "youtube_url", "description", "sort_order", "published", "modified"],
}
REPORTS = {"Expired Documents", "Approved Raw Materials", "Duplicate Queries", "Missing Supplier Manufacturer", "Raw Material Counts"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def scope(doctype):
    report = doctype.removeprefix("Report:") if doctype.startswith("Report:") else None
    if doctype not in FIELDS and report not in REPORTS:
        frappe.throw("Unsupported live dataset.")
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required.", frappe.AuthenticationError)
    if not frappe.has_permission("Query" if report else doctype, "read"):
        frappe.throw("Dataset is not available.", frappe.PermissionError)
    filters = []
    client_name = None
    if not is_staff(user):
        if "Client" not in frappe.get_roles(user):
            frappe.throw("Portal access required.", frappe.PermissionError)
        client = _find_client(user, frappe.db.get_value("User", user, "email"))
        if not client:
            frappe.throw("Client account is not linked.", frappe.PermissionError)
        client_name = client.name
        if doctype == "Query":
            filters.append(["client_name", "=", client_name])
        if doctype == "Client":
            filters.append(["name", "=", client_name])
        if doctype == "Learning Playlist":
            filters.append(["published", "=", 1])
        if report and report != "Expired Documents":
            frappe.throw("This report is for staff.", frappe.PermissionError)
    permissions = frappe.get_all("User Permission", filters={"user": user}, fields=["name", "allow", "for_value", "modified"], order_by="name asc", limit_page_length=0)
    signature = digest({"schema": SCHEMA, "user": user, "roles": sorted(frappe.get_roles(user)), "client": client_name, "permissions": permissions})
    return filters, signature


def read_rows(doctype, filters):
    if not doctype.startswith("Report:"):
        rows = frappe.get_list(doctype, fields=FIELDS[doctype], filters=filters, order_by="name asc", limit_page_length=0)
        if doctype == "Query" and rows:
            # Huge IN lists cause expensive optimizer/index-dive work on MariaDB.
            # Small Client datasets use indexed lookups; large datasets use one
            # ordered aggregate, then discard all unauthorized parent metadata.
            visible = {row.name for row in rows}
            child_filters = {"parenttype": "Query"}
            if len(visible) <= 200:
                child_filters["parent"] = ["in", sorted(visible)]
            children = frappe.get_all("Documents", filters=child_filters, fields=["parent", "count(name) as row_count", "max(modified) as latest"], group_by="parent", order_by="parent asc", limit_page_length=0)
            stamps = {row.parent: f"{row.row_count}:{row.latest or ''}" for row in children if row.parent in visible}
            for row in rows:
                row["__child_stamp"] = stamps.get(row.name, "0:")
        return rows, None
    report = doctype.removeprefix("Report:")
    if report == "Expired Documents":
        from sanha.sanha.report.expired_documents.expired_documents import execute
        columns, raw = execute()
        visible = set(frappe.get_list("Query", fields=["name"], pluck="name", limit_page_length=0))
        raw = [row for row in raw if row.query_name in visible]
    else:
        result = frappe.get_attr("frappe.desk.query_report.run")(report_name=report, filters={}, ignore_prepared_report=True)
        columns, raw = result.get("columns", []), result.get("result", [])
    rows = []
    occurrences = {}
    names = [column.get("fieldname", str(index)) if isinstance(column, dict) else str(index) for index, column in enumerate(columns)]
    for row in raw:
        item = dict(row) if isinstance(row, dict) else dict(zip(names, row))
        identity = digest(item)[:24]
        count = occurrences.get(identity, 0)
        occurrences[identity] = count + 1
        item["__sync_id"] = identity + ":" + str(count)
        rows.append(frappe._dict(item))
    return rows, {"columns": columns}


def client_count():
    if not frappe.has_permission("Client", "read"):
        return None
    filters = []
    if not is_staff(frappe.session.user):
        client = _find_client(frappe.session.user, frappe.db.get_value("User", frappe.session.user, "email"))
        filters = [["name", "=", client.name if client else ""]]
    rows = frappe.get_list("Client", filters=filters, fields=["count(name) as value"], limit_page_length=0)
    return int(rows[0].value) if rows else 0


def actor_client():
    if is_staff(frappe.session.user):
        return None
    client = _find_client(frappe.session.user, frappe.db.get_value("User", frappe.session.user, "email"))
    return client.name if client else None


@frappe.whitelist(allow_guest=True)
def access_status(doctype="Query"):
    """Current-session proof for a single retry; never grants any permission."""
    user = frappe.session.user
    if user == "Guest":
        return {"user": "Guest", "allowed": False, "scope": None, "client_scope": None}
    try:
        _, signature = scope(doctype)
    except (frappe.PermissionError, frappe.AuthenticationError):
        return {"user": user, "allowed": False, "scope": None, "client_scope": actor_client()}
    return {"user": user, "allowed": True, "scope": signature, "client_scope": actor_client()}


@frappe.whitelist()
def sync(doctype, cursor=None, fork=0):
    filters, signature = scope(doctype)
    # Read all authorized lightweight scalar rows to also detect deletions,
    # permission loss and update_modified=False edits. Never read document bytes.
    rows, meta = read_rows(doctype, filters)
    key_for = lambda row: row.get("__sync_id") or row.name
    hashes = {key_for(row): digest(row) for row in rows}
    order = [key_for(row) for row in rows] if meta else None
    count = client_count() if doctype == "Query" else None
    current = digest({"schema": SCHEMA, "scope": signature, "hashes": hashes, "clients": count, "meta": meta, "order": order})
    valid = isinstance(cursor, str) and re.fullmatch(r"[0-9a-f]{32}:[0-9a-f]{64}", cursor)
    token, previous_digest = cursor.split(":") if valid else (uuid4().hex, None)
    key = "portal-live:" + token
    previous = frappe.cache().get_value(key) if valid else None
    authorized_previous = previous and previous.get("user") == frappe.session.user and previous.get("doctype") == doctype
    if previous and not authorized_previous:
        token = uuid4().hex
        key = "portal-live:" + token
    reset = not (authorized_previous and previous.get("scope") == signature and previous.get("digest") == previous_digest and previous.get("schema") == SCHEMA)
    old_hashes = previous.get("hashes", {}) if not reset else {}
    if cint(fork) and authorized_previous:
        token = uuid4().hex
        key = "portal-live:" + token
    upserts = [row for row in rows if old_hashes.get(key_for(row)) != hashes[key_for(row)]]
    deleted = [name for name in old_hashes if name not in hashes]
    metrics = None
    if doctype == "Query":
        if not reset and previous.get("digest") == current:
            metrics = previous.get("metrics")
        else:
            metrics = overview_metrics(filters)
            metrics["clients"] = count
            if int(metrics["total_queries"]) != len(rows):
                frappe.throw("Records changed during sync. Please retry.")
    frappe.cache().set_value(key, {"schema": SCHEMA, "user": frappe.session.user, "doctype": doctype, "scope": signature, "digest": current, "hashes": hashes, "metrics": metrics}, expires_in_sec=86400)
    return {"schema": SCHEMA, "user": frappe.session.user, "doctype": doctype, "scope": signature, "client_scope": actor_client(), "cursor": token + ":" + current, "reset": bool(reset), "upserts": upserts, "deleted": deleted, "total": len(rows), "metrics": metrics, "meta": meta, "order": order if reset or previous_digest != current else None, "checked_at": now()}
