import frappe

from sanha.sanha.doctype.knowledge_source.knowledge_source import _can_set_badge

FIELDS = ["name", "title", "source_type", "publisher", "language", "url", "file", "content_scope", "topics", "e_numbers",
          "trust_level", "status", "badge", "badge_set_by", "badge_set_on", "valid_from", "valid_till", "version",
          "last_checked_on", "notes", "modified"]
EDITABLE = ["title", "source_type", "publisher", "language", "url", "file", "content_scope", "topics", "e_numbers",
            "trust_level", "status", "badge", "valid_from", "valid_till", "version", "last_checked_on", "notes"]


def _require_admin():
    user = frappe.session.user
    if not _can_set_badge(user):
        frappe.throw("Only Admin or System Manager can manage knowledge sources.", frappe.PermissionError)
    return user


@frappe.whitelist()
def admin_list():
    """All knowledge sources, including drafts and retired ones, for administrators."""
    _require_admin()
    return frappe.get_all("Knowledge Source", fields=FIELDS, order_by="modified desc", limit_page_length=1000)


@frappe.whitelist(methods=["POST"])
def admin_save(name=None, data=None):
    """Create or update one knowledge source. Status and badge rules are enforced by the doctype."""
    _require_admin()
    values = frappe.parse_json(data) if isinstance(data, str) else (data or {})
    values = {key: values.get(key) for key in EDITABLE if key in values}
    if name:
        doc = frappe.get_doc("Knowledge Source", name)
        doc.update(values)
        doc.save()
    else:
        values["doctype"] = "Knowledge Source"
        doc = frappe.get_doc(values)
        doc.insert()
    frappe.db.commit()
    return {key: doc.get(key) for key in FIELDS}
