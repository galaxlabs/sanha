import frappe
from frappe.model.workflow import apply_workflow
from frappe.utils import get_datetime, now_datetime

from sanha.api.auth import _find_client
from sanha.auto_submission import AUTO_SUBMISSION_START_LOCAL, auto_submission_enabled
from sanha.sanha.doctype.query.query import STAFF_ROLES


def submit_ready_client_drafts():
    """Process only explicitly scheduled drafts, as the Client who saved them."""
    if not auto_submission_enabled():
        return
    names = frappe.get_all(
        "Query", filters=[["workflow_state", "=", "Draft"], ["auto_submit_after", "is", "set"], ["auto_submit_after", "<=", now_datetime()], ["modified", ">=", AUTO_SUBMISSION_START_LOCAL]],
        pluck="name", order_by="auto_submit_after asc", limit_page_length=100,
    )
    original_user = frappe.session.user
    for name in names:
        frappe.db.savepoint("auto_submit_query")
        try:
            row = frappe.db.get_value("Query", name, ["workflow_state", "auto_submit_after", "auto_submit_user", "modified"], as_dict=True, for_update=True)
            if not row or row.workflow_state != "Draft" or not row.auto_submit_after or get_datetime(row.auto_submit_after) > now_datetime() or not row.modified or not auto_submission_enabled(get_datetime(row.modified)):
                continue
            user = row.auto_submit_user
            roles = set(frappe.get_roles(user)) if user else set()
            if not user or "Client" not in roles or STAFF_ROLES.intersection(roles) or not frappe.db.get_value("User", user, "enabled"):
                frappe.throw("Auto-submit requires an enabled Client user.")
            query = frappe.get_doc("Query", name)
            client = _find_client(user, frappe.db.get_value("User", user, "email"))
            if not client or query.client_name != client.name:
                frappe.throw("The draft is no longer linked to this Client user.")
            frappe.set_user(user)
            query.validate_submission_ready()
            apply_workflow(query, "Submit")
            # Prospective provenance only: never infer flags from old Submitted rows.
            frappe.db.set_value("Query", name, {
                "was_auto_submitted": 1,
                "auto_submitted_at": now_datetime(),
                "auto_submitted_by": user,
            }, update_modified=False)
            frappe.get_doc("Query", name).add_comment("Info", "Automatically submitted by the five-minute Client save scheduler. Client actor: " + frappe.utils.escape_html(user))
        except Exception as exc:
            frappe.db.rollback(save_point="auto_submit_query")
            # Remains a Draft. A later Client save schedules another attempt.
            frappe.db.set_value("Query", name, {"auto_submit_after": None, "auto_submit_user": None, "auto_submit_error": str(exc)[:1000]}, update_modified=False)
        finally:
            frappe.set_user(original_user)
