from unittest.mock import MagicMock, patch
import frappe
from sanha import tasks
from sanha.sanha.doctype.query.query import Query


def run_checks():
    original = frappe.session.user
    doc = MagicMock()
    doc.client_name = "Client A"
    due = frappe._dict(workflow_state="Draft", auto_submit_after="2026-11-11 00:05:00", auto_submit_user="client-fixture", modified="2026-11-11 00:00:00")
    def value(doctype, *args, **kwargs):
        return due if doctype == "Query" else "client-fixture"
    try:
        with patch.object(tasks, "auto_submission_enabled", return_value=True), patch.object(tasks, "now_datetime", return_value=frappe.utils.get_datetime("2026-11-12")), patch.object(frappe, "get_all", return_value=["Q-TEST"]) as listing, patch.object(frappe.db, "get_value", side_effect=value), patch.object(frappe, "get_doc", return_value=doc), patch.object(frappe, "get_roles", return_value=["Client"]), patch.object(tasks, "_find_client", return_value=frappe._dict(name="Client A")), patch.object(frappe, "set_user"), patch.object(tasks, "apply_workflow") as workflow, patch.object(frappe.db, "savepoint"), patch.object(frappe.db, "rollback"), patch.object(frappe.db, "set_value") as write:
            tasks.submit_ready_client_drafts()
            workflow.assert_called_once_with(doc, "Submit")
            assert write.call_args.args[2]["was_auto_submitted"] == 1
            assert write.call_args.args[2]["auto_submitted_by"] == "client-fixture"
            assert write.call_args.args[2]["auto_submitted_at"]
            doc.add_comment.assert_called_once()
            assert ["auto_submit_after", "is", "set"] in listing.call_args.kwargs["filters"]
            write.reset_mock(); doc.add_comment.reset_mock()
            workflow.side_effect = frappe.ValidationError("incomplete")
            tasks.submit_ready_client_drafts()
            assert all("was_auto_submitted" not in call.args[2] for call in write.call_args_list)
            doc.add_comment.assert_not_called()
        draft = Query({"doctype": "Query", "was_auto_submitted": 1, "auto_submitted_by": "forged", "workflow_state": "Draft"})
        draft.before_validate()
        assert not draft.was_auto_submitted and not draft.auto_submitted_by
        saved = Query({"doctype": "Query", "name": "Q-EXISTING", "was_auto_submitted": 0, "workflow_state": "Draft"})
        history = frappe._dict(was_auto_submitted=1, auto_submitted_at="2026-11-07 10:00:00", auto_submitted_by="client-fixture")
        with patch.object(saved, "is_new", return_value=False), patch.object(frappe.db, "get_value", return_value=history):
            saved.before_validate()
            assert saved.was_auto_submitted == 1 and saved.auto_submitted_by == "client-fixture"
        return {"checks": ["successful scheduled submission stamped", "time and actor stored", "timeline Info audit entry", "unscheduled legacy drafts excluded", "failed submission unflagged", "forged creation flag ignored", "history retained after later edits/return to Draft"], "passed": 7, "business_records_changed": 0}
    finally:
        frappe.set_user(original)
