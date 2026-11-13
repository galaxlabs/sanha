import hashlib
import json
import os

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime, nowdate

BADGE_ROLES = {"Admin", "System Manager", "Administrator"}
USABLE_BADGES = {"Approved", "Authentic"}


def _can_set_badge(user=None):
    roles = set(frappe.get_roles(user or frappe.session.user))
    return bool(BADGE_ROLES & roles) or (user or frappe.session.user) == "Administrator"


class KnowledgeSource(Document):
    def validate(self):
        self.validate_url()
        self.validate_dates()
        self.validate_e_numbers()
        self.guard_badge_and_status()

    def validate_url(self):
        if self.url and not self.url.strip().lower().startswith("https://"):
            frappe.throw("URL must start with https://")

    def validate_dates(self):
        if self.valid_from and self.valid_till and getdate(self.valid_till) < getdate(self.valid_from):
            frappe.throw("Valid Till cannot be before Valid From.")

    def validate_e_numbers(self):
        codes = [code.strip() for code in (self.e_numbers or "").split(",") if code.strip()]
        for code in codes:
            if not frappe.db.exists("E-NUMBERS", {"code": code}):
                frappe.throw(f"E-Number not found in E-NUMBERS: {code}")

    def guard_badge_and_status(self):
        before = self.get_doc_before_save()
        if not before:
            if self.badge != "None":
                if not _can_set_badge():
                    frappe.throw("Only Admin or System Manager can set a badge.")
                self.badge_set_by = frappe.session.user
                self.badge_set_on = now_datetime()
            return
        badge_changed = before.badge != self.badge
        status_changed = before.status != self.status
        if (badge_changed or status_changed) and not _can_set_badge():
            frappe.throw("Only Admin or System Manager can change the badge or status.")
        if badge_changed:
            self.badge_set_by = frappe.session.user
            self.badge_set_on = now_datetime()


def usable_for_ai(source, on_date=None):
    """A source may be cited by the bot or AI review only when it is Active, badged, and within its validity."""
    today = getdate(on_date or nowdate())
    if source.status != "Active" or source.badge not in USABLE_BADGES:
        return False
    if source.valid_from and getdate(source.valid_from) > today:
        return False
    if source.valid_till and getdate(source.valid_till) < today:
        return False
    return True


def _fingerprint(doc):
    basis = "|".join(str(doc.get(key) or "") for key in ("title", "publisher", "source_type", "content_scope", "topics", "e_numbers", "url", "version", "file"))
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


MAX_SOURCE_CHARS = 12000
MAX_SOURCE_BYTES = 16 * 1024 * 1024


def _source_text(doc):
    """Readable text of the attached PDF or text file (first pages only). Empty when there is no readable file."""
    if not doc.get("file"):
        return ""
    from sanha.api.staff_review import text_pages
    for entry in frappe.get_all("File", filters={"file_url": doc.file, "is_folder": 0}, fields=["name"], limit_page_length=5):
        path = frappe.get_doc("File", entry.name).get_full_path()
        if not os.path.isfile(path) or os.path.getsize(path) > MAX_SOURCE_BYTES:
            return ""
        with open(path, "rb") as handle:
            pages, _ = text_pages(handle.read(), doc.file)
        return "\n".join(text for _, text in pages if text).strip()[:MAX_SOURCE_CHARS]
    return ""


def fresh_summary(row):
    """The stored summary when it matches the current content. Never calls the AI."""
    if row.get("ai_summary") and row.get("ai_summary_hash") == _fingerprint(row):
        return row.get("ai_summary")
    return ""


def cached_summary(doc):
    """Return the stored AI summary, creating it once per content fingerprint. Stored in the database.

    Uses the attached document text when it can be read; otherwise only the metadata."""
    from sanha.api import chat
    current = _fingerprint(doc)
    if doc.get("ai_summary") and doc.get("ai_summary_hash") == current:
        return doc.get("ai_summary")
    config = frappe.get_single("AI Agent Config").as_dict()
    metadata = {key: doc.get(key) for key in ("title", "publisher", "source_type", "content_scope", "topics", "e_numbers", "version")}
    source_text = _source_text(doc)
    if source_text:
        instruction = "Summarize this approved knowledge source for SANHA staff in Urdu, in at most 600 characters. Use only the document text and metadata given. Do not invent requirements, numbers or claims; say when the details must be checked in the source document."
        content = {"metadata": metadata, "document_text": source_text}
    else:
        instruction = "Summarize this approved knowledge source for SANHA staff in Urdu, in at most 600 characters. Use only the metadata given. Do not invent requirements, numbers or claims; say when the details must be checked in the source document."
        content = metadata
    messages = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": json.dumps(content, ensure_ascii=False)},
    ]
    text = str(chat._call_llm(config, messages, purpose="knowledge_summary", reference=doc.name) or "").strip()[:2000]
    frappe.db.set_value("Knowledge Source", doc.name, {"ai_summary": text, "ai_summary_hash": current, "ai_summary_on": now_datetime()}, update_modified=False)
    return text
