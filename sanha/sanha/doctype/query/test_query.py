# Copyright (c) 2024, Sanha Halal Pakistan  and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from sanha.sanha.doctype.query.query import (
	Query,
	notify_system_managers_on_client_query_comment,
)


class TestQuery(FrappeTestCase):
	def test_client_can_edit_returned_query(self):
		doc = Query(
			{
				"doctype": "Query",
				"name": "QUERY-RETURNED",
				"raw_material": "Updated",
				"workflow_state": "Submitted to SB",
			}
		)

		with (
			patch.object(Query, "is_new", return_value=False),
			patch("sanha.sanha.doctype.query.query.frappe.get_roles", return_value=["Client"]),
			patch("sanha.sanha.doctype.query.query.frappe.db.get_value", return_value="Returned"),
			patch("sanha.sanha.doctype.query.query.frappe.get_doc") as get_doc,
		):
			doc.validate_client_edit_lock()
			get_doc.assert_not_called()

	def test_client_cannot_edit_submitted_query(self):
		doc = Query({"doctype": "Query", "name": "QUERY-SUBMITTED", "raw_material": "Updated"})
		previous = frappe._dict({"raw_material": "Original", "documents": []})

		with (
			patch.object(Query, "is_new", return_value=False),
			patch("sanha.sanha.doctype.query.query.frappe.get_roles", return_value=["Client"]),
			patch("sanha.sanha.doctype.query.query.frappe.db.get_value", return_value="Submitted"),
			patch("sanha.sanha.doctype.query.query.frappe.get_doc", return_value=previous),
		):
			self.assertRaises(frappe.PermissionError, doc.validate_client_edit_lock)

	@patch("sanha.sanha.doctype.query.query.get_system_managers", return_value=["manager@example.com"])
	@patch("sanha.sanha.doctype.query.query.frappe.get_roles", return_value=["Client"])
	@patch("sanha.sanha.doctype.query.query.frappe.db.get_value", return_value="Client User")
	@patch("sanha.sanha.doctype.query.query.frappe.new_doc")
	def test_client_query_comment_notifies_system_managers(
		self, new_doc, get_value, get_roles, get_system_managers
	):
		notification = MagicMock()
		new_doc.return_value = notification
		comment = frappe._dict(
			{
				"comment_type": "Comment",
				"reference_doctype": "Query",
				"reference_name": "QUERY-COMMENTED",
				"comment_email": "client@example.com",
				"owner": "client@example.com",
				"content": "<p>Please review this Query.</p>",
			}
		)

		notify_system_managers_on_client_query_comment(comment)

		get_system_managers.assert_called_once_with(only_name=True)
		payload = notification.update.call_args.args[0]
		self.assertEqual(payload["for_user"], "manager@example.com")
		self.assertEqual(payload["document_name"], "QUERY-COMMENTED")
		self.assertEqual(payload["email_content"], "Please review this Query.")
		notification.insert.assert_called_once_with(ignore_permissions=True)

	@patch("sanha.sanha.doctype.query.query.get_system_managers")
	@patch("sanha.sanha.doctype.query.query.frappe.get_roles", return_value=["Evaluation"])
	def test_staff_query_comment_does_not_notify_system_managers(self, get_roles, get_system_managers):
		comment = frappe._dict(
			{
				"comment_type": "Comment",
				"reference_doctype": "Query",
				"reference_name": "QUERY-COMMENTED",
				"comment_email": "staff@example.com",
				"owner": "staff@example.com",
				"content": "Internal response",
			}
		)

		notify_system_managers_on_client_query_comment(comment)

		get_system_managers.assert_not_called()
