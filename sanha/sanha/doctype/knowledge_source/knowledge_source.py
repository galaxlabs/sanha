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
            if self.badge != "None" and not _can_set_badge():
                frappe.throw("Only Admin or System Manager can set a badge.")
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
