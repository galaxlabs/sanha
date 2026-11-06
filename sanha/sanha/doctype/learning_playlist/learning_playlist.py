from frappe.model.document import Document
import frappe

from sanha.api.learning import ADMIN_ROLES, canonical_playlist_url


class LearningPlaylist(Document):
    def validate(self):
        self.youtube_url = canonical_playlist_url(self.youtube_url)
        self.title = (self.title or "").strip()
        self.subject = (self.subject or "").strip()
        if not self.title or not self.subject:
            frappe.throw("Playlist title and subject are required.")


def get_permission_query_conditions(user=None):
    if ADMIN_ROLES.intersection(frappe.get_roles(user or frappe.session.user)):
        return ""
    return "`tabLearning Playlist`.published = 1"


def has_permission(doc, user=None, ptype=None):
    return bool(ADMIN_ROLES.intersection(frappe.get_roles(user or frappe.session.user)) or doc.published)
