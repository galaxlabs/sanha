import json
import frappe
from sanha.sanha.report.expired_documents.expired_documents import execute as get_expired_documents


@frappe.whitelist()
def state_counts(filters=None):
    """Return all visible Query workflow totals without a REST page-size cap."""
    filters = json.loads(filters) if isinstance(filters, str) else (filters or [])
    rows = frappe.get_list(
        "Query",
        filters=filters,
        fields=["workflow_state as state", "count(name) as count"],
        group_by="workflow_state",
        limit_page_length=0,
    )
    return rows


@frappe.whitelist()
def expired_documents():
    """Return expiry rows with the report's role-aware scope applied."""
    columns, data = get_expired_documents()
    return {"columns": columns, "data": data}


@frappe.whitelist()
def overview_metrics(filters=None):
    """Return dashboard totals directly from the database without REST page limits."""
    filters = json.loads(filters) if isinstance(filters, str) else (filters or [])
    # Fixed aggregate expressions; Frappe validates caller filters and applies
    # role, User Permission, sharing and Query permission-condition hooks.
    grouped = frappe.get_list(
        "Query", filters=filters,
        fields=["raw_material", "is_duplicate", "count(name) as row_count"],
        group_by="raw_material, is_duplicate", limit_page_length=0,
    )
    total = sum(int(row.row_count) for row in grouped)
    material_groups = frappe.get_list("Query", filters=filters, fields=["raw_material"], group_by="raw_material", limit_page_length=0)
    material_count = sum(1 for row in material_groups if row.raw_material and row.raw_material.rstrip())
    duplicates = sum(int(row.row_count) for row in grouped if int(row.is_duplicate or 0) == 1)
    clients = None
    if frappe.has_permission("Client", "read"):
        client_count = frappe.get_list("Client", fields=["count(name) as row_count"], limit_page_length=0)
        clients = int(client_count[0].row_count) if client_count else 0
    return {"total_queries": total, "unique_materials": material_count, "duplicate_queries": duplicates, "clients": clients}


@frappe.whitelist()
def playlist_videos(url, start=0, page_size=50):
    from sanha.api.learning import get_playlist_videos
    return get_playlist_videos(url, start, page_size)


@frappe.whitelist()
def client_resources(kind):
    from sanha.api.auth import _find_client
    user = frappe.session.user
    client = _find_client(user, frappe.db.get_value("User", user, "email"))
    if not client:
        frappe.throw("Client account is not linked.", frappe.PermissionError)
    if kind == "records":
        doc = frappe.get_doc("Client", client.name)
        return [{"name": row.name, "doc_type": row.doc_type, "date": row.date, "attachment": row.attach_ilxb} for row in doc.records_hub or []]
    if kind == "templates":
        return frappe.get_list("Templates", fields=["name", "title", "text_template", "modified"], order_by="modified desc", limit_page_length=100)
    frappe.throw("Unsupported resource.")
