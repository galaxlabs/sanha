import frappe
from frappe.utils import now_datetime

from sanha.api.messaging import check_query, is_staff


def _require_staff():
    user = frappe.session.user
    if not is_staff(user):
        frappe.throw("Team comments are available to SANHA staff only.", frappe.PermissionError)
    return user


@frappe.whitelist()
def list_comments(query):
    """Team comments on a Query. Visible to every staff member who can read the Query; never to clients."""
    user = _require_staff()
    if not query or not isinstance(query, str):
        frappe.throw("Query is required.")
    check_query(query, user)
    rows = frappe.get_all(
        "Comment",
        filters={"reference_doctype": "Query", "reference_name": query, "comment_type": "Comment"},
        fields=["name", "content", "comment_email", "comment_by", "creation"],
        order_by="creation asc",
        limit_page_length=500,
    )
    # Only comments written by staff accounts; older client comments on the same Query are excluded.
    return [row for row in rows if is_staff(row.comment_email)]


@frappe.whitelist(methods=["POST"])
def add_comment(query, content):
    """Add a team comment to a Query. Staff only."""
    user = _require_staff()
    if not query or not isinstance(query, str):
        frappe.throw("Query is required.")
    text = (content or "").strip() if isinstance(content, str) else ""
    if not text or len(text) > 2000:
        frappe.throw("Comment must contain 1–2000 characters.")
    check_query(query, user)
    author = frappe.db.get_value("User", user, "full_name") or user
    doc = frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Comment",
        "reference_doctype": "Query",
        "reference_name": query,
        "comment_email": user,
        "comment_by": author,
        "content": text,
        "creation": now_datetime(),
    })
    doc.insert(ignore_permissions=True)
    return {"name": doc.name, "content": doc.content, "comment_by": doc.comment_by, "creation": str(doc.creation), "comment_email": user}
