# Copyright (c) 2024, Sanha Halal Pakistan and Contributors
# See license.txt

from unittest.mock import patch

from frappe.tests.utils import FrappeTestCase

from sanha.sanha.report.expired_documents.expired_documents import execute


class TestExpiredDocuments(FrappeTestCase):
	@patch("sanha.sanha.report.expired_documents.expired_documents.get_scope_condition", return_value=("", {}))
	@patch("sanha.sanha.report.expired_documents.expired_documents.frappe.db.sql", return_value=[])
	def test_report_prefers_valid_document_before_latest_expired(self, sql, get_scope_condition):
		execute()

		query = sql.call_args.args[0]
		self.assertIn("valid.expiry_date >= CURDATE()", query)
		self.assertIn("newer_expired.expiry_date < CURDATE()", query)
		self.assertIn("newer_expired.idx > d.idx", query)
