import frappe
from frappe.utils import add_to_date, now_datetime


def submit_ready_client_drafts():
    """Submit unchanged, complete Client drafts after five minutes."""
    cutoff = add_to_date(now_datetime(), minutes=-5)
    names = frappe.get_all(
        "Query",
        filters={"workflow_state": "Draft", "modified": ["<=", cutoff]},
        pluck="name",
        limit_page_length=100,
    )
    for name in names:
        query = frappe.get_doc("Query", name)
        if not query.raw_material or not query.query_types or not query.documents:
            continue
        try:
            query.workflow_state = "Submitted"
            query.save(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Auto-submit draft failed: {name}")
