import frappe
from frappe.model.workflow import apply_workflow
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime

from sanha.api.auth import _find_client
from sanha.tasks import submit_ready_client_drafts


class TestPortalDrafts(FrappeTestCase):
    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        self.client = frappe.get_all("Client", fields=["name", "email"], limit_page_length=100)
        self.user = next((row.email for row in self.client if frappe.db.get_value("User", row.email, "enabled") and "Client" in frappe.get_roles(row.email)), None)
        if not self.user:
            self.skipTest("An enabled linked Client fixture is required.")
        self.linked = _find_client(self.user, self.user)
        self.query_type = frappe.db.get_value("Query Types", {}, "name")
        frappe.set_user(self.user)

    def tearDown(self):
        frappe.set_user("Administrator")
        super().tearDown()

    def draft(self, complete=False):
        doc = frappe.get_doc({"doctype": "Query", "workflow_state": "Draft", "client_name": self.linked.name})
        if complete:
            doc.raw_material = "Portal draft test " + frappe.generate_hash(length=12)
            doc.query_types = self.query_type
            doc.append("documents", {"documents": "Halal Certificate", "attachment": "/private/files/test-certificate.pdf", "issue_date": "2026-01-01", "expiry_date": "2030-01-01"})
        return doc.insert()

    def due(self, doc):
        frappe.db.set_value("Query", doc.name, "auto_submit_after", add_to_date(now_datetime(), minutes=-1), update_modified=False)

    def test_partial_draft_with_unfinished_child_survives_reload(self):
        doc = self.draft()
        doc.append("documents", {"documents": "Halal Certificate"})
        doc.save()
        reloaded = frappe.get_doc("Query", doc.name)
        self.assertEqual(reloaded.workflow_state, "Draft")
        self.assertFalse(reloaded.raw_material)
        self.assertEqual(len(reloaded.documents), 1)
        self.assertTrue(reloaded.auto_submit_after)
        with self.assertRaises(frappe.ValidationError):
            apply_workflow(reloaded, "Submit")

    def test_complete_draft_waits_and_then_submits_through_workflow(self):
        doc = self.draft(complete=True)
        submit_ready_client_drafts()
        self.assertEqual(frappe.db.get_value("Query", doc.name, "workflow_state"), "Draft")
        self.due(doc)
        submit_ready_client_drafts()
        self.assertEqual(frappe.db.get_value("Query", doc.name, "workflow_state"), "Submitted")
        self.assertFalse(frappe.db.get_value("Query", doc.name, "auto_submit_after"))

    def test_incomplete_draft_stays_draft_and_resave_restarts_timer(self):
        doc = self.draft(complete=True)
        doc.documents[0].expiry_date = None
        doc.save()
        self.due(doc)
        submit_ready_client_drafts()
        doc.reload()
        self.assertEqual(doc.workflow_state, "Draft")
        self.assertTrue(doc.auto_submit_error)
        self.assertFalse(doc.auto_submit_after)
        doc.documents[0].expiry_date = "2030-01-01"
        doc.save()
        self.assertTrue(doc.auto_submit_after)
        self.assertFalse(doc.auto_submit_error)

    def test_legacy_draft_is_never_picked_up(self):
        doc = self.draft(complete=True)
        frappe.db.set_value("Query", doc.name, {"auto_submit_after": None, "auto_submit_user": None}, update_modified=False)
        submit_ready_client_drafts()
        self.assertEqual(frappe.db.get_value("Query", doc.name, "workflow_state"), "Draft")

    def test_failure_does_not_block_later_due_draft(self):
        bad = self.draft()
        good = self.draft(complete=True)
        self.due(bad)
        self.due(good)
        submit_ready_client_drafts()
        self.assertEqual(frappe.db.get_value("Query", bad.name, "workflow_state"), "Draft")
        self.assertEqual(frappe.db.get_value("Query", good.name, "workflow_state"), "Submitted")

    def test_saving_again_restarts_the_five_minute_wait(self):
        doc = self.draft(complete=True)
        self.due(doc)
        doc.reload()
        doc.supplier = "Updated supplier"
        doc.save()
        submit_ready_client_drafts()
        self.assertEqual(frappe.db.get_value("Query", doc.name, "workflow_state"), "Draft")
        self.assertGreater(doc.auto_submit_after, now_datetime())


class TestPortalClientForm(FrappeTestCase):
    def test_client_and_all_child_tables_create_update_and_remove(self):
        frappe.set_user("Administrator")
        key = frappe.generate_hash(length=10)
        client = frappe.get_doc({
            "doctype": "Client", "client_name": "Portal Client " + key,
            "email": f"portal-{key}@example.invalid", "business_name": "Test Business",
            "client_code": "PT-" + key, "certified_since": "2026-01-01",
            "certified_expiry": "2030-01-01", "is_active": 1,
            "emails": [{"email_id": "contact@example.invalid", "is_primary": 1}],
            "phone_nos": [{"phone": "+923001234567", "is_primary_phone": 1}],
            "records_hub": [{"date": "2026-01-01", "attach_ilxb": "/private/files/test.pdf"}],
        }).insert()
        client.reload()
        self.assertEqual(len(client.emails), 1)
        self.assertEqual(len(client.phone_nos), 1)
        self.assertEqual(len(client.records_hub), 1)
        self.assertTrue(frappe.db.exists("User", client.email))
        original_row = client.records_hub[0].name
        client.emails[0].email_id = "updated@example.invalid"
        client.phone_nos[0].phone = "+923009876543"
        client.records_hub[0].date = "2026-02-01"
        client.append("records_hub", {"date": "2026-03-01"})
        client.save()
        client.reload()
        self.assertEqual(client.emails[0].email_id, "updated@example.invalid")
        self.assertEqual(client.phone_nos[0].phone, "+923009876543")
        self.assertEqual(client.records_hub[0].name, original_row)
        self.assertEqual(len(client.records_hub), 2)
        client.set("emails", [])
        client.set("phone_nos", [])
        client.set("records_hub", [])
        client.save()
        client.reload()
        self.assertEqual(len(client.records_hub), 0)
        self.assertEqual(len(client.phone_nos), 0)
        self.assertEqual(len(client.emails), 0)
