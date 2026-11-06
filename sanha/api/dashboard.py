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
    query_conditions = []
    values = {}
    for index, item in enumerate(filters):
        field, operator, value = item
        key = f"value_{index}"
        query_conditions.append(f"q.`{field}` {operator} %({key})s")
        values[key] = value
    where = f"WHERE {' AND '.join(query_conditions)}" if query_conditions else ""
    metrics = frappe.db.sql(
        f"""
        SELECT
            COUNT(*) AS total_queries,
            COUNT(DISTINCT NULLIF(q.raw_material, '')) AS unique_materials,
            SUM(CASE WHEN q.is_duplicate = 1 THEN 1 ELSE 0 END) AS duplicate_queries
        FROM `tabQuery` q
        {where}
        """,
        values,
        as_dict=True,
    )[0]
    metrics["clients"] = frappe.db.count("Client") if not filters else None
    return metrics


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
