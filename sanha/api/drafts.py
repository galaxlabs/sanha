import frappe

from sanha.api.draft_templates import PURPOSES, RECIPIENTS, build_draft
from sanha.api.messaging import check_query


@frappe.whitelist(methods=["POST"])
def draft_text(query, purpose, recipient, details=""):
    """Return text for the user to copy. Nothing is sent and no other client's data is used."""
    user = frappe.session.user
    if not query or not isinstance(query, str):
        frappe.throw("Query is required.")
    if purpose not in PURPOSES or recipient not in RECIPIENTS:
        frappe.throw("Unknown purpose or recipient.")
    check_query(query, user)
    doc = frappe.get_doc("Query", query)
    doc.check_permission("read")
    sender = frappe.db.get_value("User", user, "full_name") or ""
    return build_draft(purpose, recipient, doc.name, doc.raw_material, details, sender)
