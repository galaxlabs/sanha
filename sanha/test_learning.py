from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from sanha.api.learning import canonical_playlist_url, get_playlist_videos


class TestLearning(FrappeTestCase):
    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        self.url = f"https://www.youtube.com/playlist?list=PL{frappe.generate_hash(length=32)}"
        self.doc = frappe.get_doc({"doctype": "Learning Playlist", "title": frappe.generate_hash(length=12), "subject": "Test subject", "youtube_url": self.url, "published": 1}).insert()

    def tearDown(self):
        frappe.set_user("Administrator")
        for start in [0, 50, 100]:
            frappe.cache().delete_value(f"sanha:learning:{self.url}:{start}:50")
        super().tearDown()

    def client_user(self):
        for row in frappe.get_all("Client", fields=["email"]):
            if frappe.db.get_value("User", row.email, "enabled") and "Client" in frappe.get_roles(row.email):
                return row.email
        self.skipTest("Linked Client fixture required.")

    def test_reads_all_continuation_pages_not_only_rss_entries(self):
        entries = [{"id": f"vid{index:08d}", "title": f"Lesson {index}", "channel": "Test", "duration": 60} for index in range(125)]
        class Extractor:
            def __init__(self, options):
                self.options = options
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def extract_info(self, url, download=False):
                return {"entries": entries[self.options["playliststart"] - 1:self.options["playlistend"]]}
        with patch("sanha.api.learning.YoutubeDL", Extractor):
            videos, start = [], 0
            while True:
                page = get_playlist_videos(self.url, start)
                videos.extend(page["videos"])
                if not page["has_more"]:
                    break
                start = page["next_start"]
        self.assertEqual(len(videos), 125)
        self.assertEqual(len({video["id"] for video in videos}), 125)
        self.assertEqual(videos[-1]["title"], "Lesson 124")

    def test_edit_preserves_record_and_updates_all_admin_fields(self):
        name = self.doc.name
        self.doc.update({"title": "Updated title", "subject": "Updated subject", "youtube_url": self.url + "&index=2", "description": "Updated description", "sort_order": 7, "published": 0})
        self.doc.save()
        self.doc.reload()
        self.assertEqual(self.doc.name, name)
        self.assertEqual(self.doc.title, "Updated title")
        self.assertEqual(self.doc.subject, "Updated subject")
        self.assertEqual(self.doc.youtube_url, self.url)
        self.assertEqual(self.doc.description, "Updated description")
        self.assertEqual(self.doc.sort_order, 7)
        self.assertEqual(self.doc.published, 0)

    def test_unpublished_playlist_denied_in_list_detail_and_api(self):
        self.doc.published = 0
        self.doc.save()
        frappe.set_user(self.client_user())
        self.assertFalse(frappe.get_list("Learning Playlist", filters={"name": self.doc.name}))
        self.assertFalse(frappe.has_permission("Learning Playlist", "read", doc=self.doc))
        with self.assertRaises(frappe.PermissionError):
            get_playlist_videos(self.url)

    def test_client_cannot_edit_playlist(self):
        frappe.set_user(self.client_user())
        self.assertFalse(frappe.has_permission("Learning Playlist", "write", doc=self.doc))

    def test_external_urls_are_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            canonical_playlist_url("https://example.com/playlist?list=PL1234567890")
