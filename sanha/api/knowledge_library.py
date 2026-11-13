import base64
import json

import frappe
from frappe.utils.file_manager import save_file

from sanha.api.messaging import is_staff
from sanha.sanha.doctype.knowledge_source.knowledge_source import usable_for_ai

FIELDS = ["name", "title", "source_type", "publisher", "url", "file", "content_scope", "topics", "e_numbers",
          "language", "badge", "trust_level", "version", "last_checked_on", "status", "valid_from", "valid_till"]
PUBLIC_KEYS = ["name", "title", "source_type", "publisher", "url", "content_scope", "topics", "e_numbers",
               "language", "badge", "trust_level", "version", "last_checked_on"]
EDITABLE = ["title", "source_type", "publisher", "language", "url", "content_scope", "topics", "e_numbers",
            "trust_level", "status", "badge", "valid_from", "valid_till", "version", "last_checked_on", "notes"]
MANAGE_ROLES = {"Admin", "System Manager", "Administrator", "Evaluation"}
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".png", ".jpg", ".jpeg"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


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


def _require_manage():
    roles = set(frappe.get_roles())
    if frappe.session.user != "Administrator" and not (MANAGE_ROLES & roles):
        frappe.throw("Knowledge Source management is for Admin and Evaluation only.", frappe.PermissionError)


@frappe.whitelist()
def admin_list():
    """Every Knowledge Source, including drafts, for management."""
    _require_manage()
    return frappe.get_all(
        "Knowledge Source",
        fields=["name", "title", "source_type", "publisher", "status", "badge", "trust_level", "file", "last_checked_on", "modified"],
        order_by="modified desc",
        limit_page_length=1000,
    )


@frappe.whitelist()
def get_source(name):
    _require_manage()
    doc = frappe.get_doc("Knowledge Source", name)
    data = {key: doc.get(key) for key in EDITABLE}
    data.update({"name": doc.name, "file_url": doc.file, "badge_set_by": doc.badge_set_by, "badge_set_on": str(doc.badge_set_on or "")})
    return data


@frappe.whitelist(methods=["POST"])
def save_source(name=None, data=None):
    """Create or update a Knowledge Source. The controller decides who may change status or badge."""
    _require_manage()
    values = json.loads(data) if isinstance(data, str) else (data or {})
    clean = {key: values.get(key) for key in EDITABLE if key in values}
    if name:
        doc = frappe.get_doc("Knowledge Source", name)
        doc.update(clean)
    else:
        doc = frappe.get_doc({"doctype": "Knowledge Source", **clean})
    doc.save()
    return {"name": doc.name}


@frappe.whitelist(methods=["POST"])
def upload_file(name, filename, content):
    """Attach a private file to a Knowledge Source (base64 content)."""
    _require_manage()
    doc = frappe.get_doc("Knowledge Source", name)
    extension = ("." + filename.rsplit(".", 1)[-1]).lower() if "." in (filename or "") else ""
    if extension not in ALLOWED_EXTENSIONS:
        frappe.throw("Allowed files: PDF, Word, text or image.")
    raw = base64.b64decode(content or "")
    if not raw or len(raw) > MAX_UPLOAD_BYTES:
        frappe.throw("File must be between 1 byte and 25 MB.")
    saved = save_file(filename, raw, "Knowledge Source", name, is_private=1)
    doc.file = saved.file_url
    doc.save()
    return {"file_url": saved.file_url}
