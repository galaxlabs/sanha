import frappe

from sanha.api.messaging import is_staff
from sanha.sanha.doctype.knowledge_source.knowledge_source import usable_for_ai

FIELDS = ["name", "title", "source_type", "publisher", "url", "file", "content_scope", "topics", "e_numbers",
          "language", "badge", "trust_level", "version", "last_checked_on", "status", "valid_from", "valid_till"]
PUBLIC_KEYS = ["name", "title", "source_type", "publisher", "url", "content_scope", "topics", "e_numbers",
               "language", "badge", "trust_level", "version", "last_checked_on"]


@frappe.whitelist()
def list_sources():
    """Published reference library: only Active, badged, in-date sources. Clients see Authoritative sources only."""
    staff = is_staff(frappe.session.user)
    rows = frappe.get_all(
        "Knowledge Source",
        filters={"status": "Active", "badge": ["in", ["Approved", "Authentic"]]},
        fields=FIELDS,
        order_by="modified desc",
        limit_page_length=500,
    )
    output = []
    for row in rows:
        if not usable_for_ai(frappe._dict(row)):
            continue
        if not staff and row.trust_level != "Authoritative":
            continue
        item = {key: row.get(key) for key in PUBLIC_KEYS}
        item["file_url"] = row.file if staff else None
        output.append(item)
    return output
