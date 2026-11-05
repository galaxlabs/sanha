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
