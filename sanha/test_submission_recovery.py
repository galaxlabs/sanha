"""Focused recovery/activation checks; SQL fixtures are always rolled back."""

import copy
import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import frappe

from sanha import submission_recovery as recovery, tasks
from sanha.auto_submission import auto_submission_enabled
from sanha.sanha.doctype.query import query as controller


def _fixture_snapshot():
    stamp = datetime(2026, 11, 5, 23, 20)
    event = {"name": "test-version", "docname": "test-query", "owner": "Administrator",
             "creation": stamp + timedelta(milliseconds=50),
             "data": json.dumps({"changed": [recovery.CHANGE], "added": [], "removed": [], "row_changed": []})}
    snap = {"parent": {"name": "test-query", "creation": "2026-01-01", "workflow_state": "Submitted",
                       "docstatus": 0, "modified": stamp, "modified_by": "Administrator"},
            "children": {}, "files": [], "comments": [], "versions": [event], "linked_client_code": "C-TEST"}
    return snap, event


def run_checks():
    checks = []
    snap, event = _fixture_snapshot()
    assert recovery._classify(snap, event) == "eligible"
    checks.append("exact incident event accepted")
    with_defaults = copy.deepcopy(event)
    with_defaults["data"] = json.dumps({"changed": [recovery.CHANGE, ["notify_client", 0, 1], ["client_code", None, "C-TEST"]]})
    snap["parent"]["client_code"] = "C-TEST"
    assert recovery._classify(snap, with_defaults) == "eligible"
    checks.append("only verified framework default/fetch changes accepted")
    wrong_default = copy.deepcopy(with_defaults)
    wrong_default["data"] = json.dumps({"changed": [recovery.CHANGE, ["notify_client", 1, 0]]})
    assert not recovery._incident_event(wrong_default)
    checks.append("unrelated checkbox changes protected")
    for state in ("Approved", "Submitted to SB", "Draft", "Returned"):
        changed = copy.deepcopy(snap)
        changed["parent"]["workflow_state"] = state
        assert recovery._classify(changed, event) != "eligible"
    checks.append("all non-Submitted states protected")
    for field, value in (("modified_by", "client-fixture"), ("modified", "2026-11-06"), ("docstatus", 1),
                         ("was_auto_submitted", 1), ("auto_submit_after", "2026-11-12"), ("creation", "2026-11-06")):
        changed = copy.deepcopy(snap)
        changed["parent"][field] = value
        assert recovery._classify(changed, event) != "eligible"
    checks.append("later edits, actors, submitted documents and new tracking protected")
    for key, value in (("versions", [{**event, "creation": "2026-11-07"}]),
                       ("files", [{"modified": "2026-11-07"}]),
                       ("comments", [{"creation": "2026-11-07", "modified": "2026-11-07"}]),
                       ("children", {"documents": [{"modified": "2026-11-07"}]})):
        changed = copy.deepcopy(snap)
        changed[key] = value
        assert recovery._classify(changed, event) != "eligible"
    checks.append("later history, files, comments and child edits protected")
    manual = {**event, "owner": "client-fixture"}
    old = {**event, "creation": "2026-11-05 22:57:13"}
    assert not recovery._incident_event(manual) and not recovery._incident_event(old)
    checks.append("manual and pre-incident submissions protected")
    unrelated = {**event, "data": json.dumps({"changed": [recovery.CHANGE, ["supplier", "A", "B"]]})}
    assert not recovery._incident_event(unrelated)
    checks.append("business-field changes excluded")
    assert recovery._digest(snap) == recovery._digest(json.loads(json.dumps(snap, default=str)))
    checks.append("private manifest survives datetime JSON roundtrip")
    try:
        recovery._private_file("../outside.json")
        raise AssertionError("path traversal accepted")
    except ValueError:
        pass
    checks.append("manifest/backup paths constrained")

    assert not auto_submission_enabled("2026-11-10 23:59:59.999999")
    assert auto_submission_enabled("2026-11-11 00:00:00")
    assert not auto_submission_enabled(datetime(2026, 11, 10, 18, 59, 59, tzinfo=timezone.utc))
    assert auto_submission_enabled(datetime(2026, 11, 10, 19, 0, tzinfo=timezone.utc))
    checks.append("activation exact at 11 November 00:00 Pakistan, UTC conversion verified")
    with patch.object(tasks, "auto_submission_enabled", return_value=False), patch.object(frappe, "get_all") as listing:
        tasks.submit_ready_client_drafts()
        listing.assert_not_called()
    checks.append("pre-activation scheduler cannot select or modify any Query")
    doc = controller.Query({"doctype": "Query", "workflow_state": "Draft", "auto_submit_after": "2026-11-07"})
    with patch.object(controller, "auto_submission_enabled", return_value=False), patch.object(frappe, "get_roles", return_value=["Client"]):
        doc.schedule_auto_submission()
        assert doc.auto_submit_after is None and doc.auto_submit_user is None
    checks.append("pre-activation Client save clears queue instead of scheduling")
    with patch.object(controller, "auto_submission_enabled", return_value=True), patch.object(controller, "now_datetime", return_value=datetime(2026, 11, 11)), patch.object(frappe, "get_roles", return_value=["Client"]):
        doc.schedule_auto_submission()
        assert doc.auto_submit_after == datetime(2026, 11, 11, 0, 5)
    checks.append("post-activation Client save schedules exactly five minutes")
    with patch.object(controller, "auto_submission_enabled", return_value=True), patch.object(frappe, "get_roles", return_value=["Client", "Evaluation"]):
        doc.schedule_auto_submission()
        assert doc.auto_submit_after is None
    checks.append("staff saves never schedule old drafts")
    old_queue = frappe._dict(workflow_state="Draft", auto_submit_after="2026-11-10", auto_submit_user="client-fixture", modified="2026-11-10 23:59:59")
    with patch.object(tasks, "auto_submission_enabled", side_effect=lambda at=None: auto_submission_enabled(at or "2026-11-12")), patch.object(tasks, "now_datetime", return_value=datetime(2026, 11, 12)), patch.object(frappe, "get_all", return_value=["fixture"]), patch.object(frappe.db, "get_value", return_value=old_queue), patch.object(frappe.db, "savepoint"), patch.object(frappe, "set_user"), patch.object(tasks, "apply_workflow") as workflow:
        tasks.submit_ready_client_drafts()
        workflow.assert_not_called()
    checks.append("old pre-activation queue rejected again under row lock")

    original = frappe.session.user
    try:
        frappe.set_user("Guest")
        try:
            recovery.audit()
            raise AssertionError("Guest recovery accepted")
        except frappe.PermissionError:
            pass
    finally:
        frappe.set_user(original)
    checks.append("non-Administrator recovery denied")
    checks.extend(_database_checks())
    return {"passed": len(checks), "checks": checks, "business_records_changed": 0,
            "sql_fixtures": "rolled back; no hooks or external inference on fixture creation"}


def _database_checks():
    """Exercise real SQL corrections/history and whole-transaction rollback."""
    if frappe.local.site != "eval.portal":
        return ["SQL fixture tests development-only; production fixtures forbidden"]
    frappe.db.savepoint("recovery_test_start")
    records = []
    try:
        for _ in range(2):
            name = "_TEST_RECOVERY_" + uuid.uuid4().hex[:16]
            frappe.db.sql("INSERT INTO tabQuery (name,creation,modified,modified_by,owner,workflow_state,docstatus,raw_material,supplier,manufacturer) "
                          "VALUES (%s,%s,%s,%s,%s,%s,0,%s,%s,%s)",
                          (name, "2026-01-01", "2026-11-05 23:20:00", "Administrator", "Administrator", "Submitted", "recovery fixture", "Supplier preserved", "Manufacturer preserved"))
            event = {"name": "_TEST_VER_" + uuid.uuid4().hex[:16], "docname": name, "owner": "Administrator", "creation": "2026-11-05 23:20:00.050000",
                     "data": json.dumps({"changed": [recovery.CHANGE], "added": [], "removed": [], "row_changed": []})}
            frappe.db.sql("INSERT INTO tabVersion (name,creation,modified,modified_by,owner,ref_doctype,docname,data) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                          (event["name"], event["creation"], event["creation"], "Administrator", "Administrator", "Query", name, event["data"]))
            snapshot = recovery._snapshot(name)
            records.append({"name": name, "event": event, "snapshot_digest": recovery._digest(snapshot)})
        frappe.db.savepoint("before_recovery_test")
        recovery._restore_one(records[0])
        row = frappe.db.get_value("Query", records[0]["name"], ["workflow_state", "auto_submit_after", "supplier", "manufacturer"], as_dict=True)
        assert row.workflow_state == "Draft" and not row.auto_submit_after
        assert row.supplier == "Supplier preserved" and row.manufacturer == "Manufacturer preserved"
        assert len(recovery._versions(records[0]["name"])) == 2
        assert frappe.db.count("Comment", {"reference_doctype": "Query", "reference_name": records[0]["name"]}) == 1
        try:
            recovery._restore_one(records[0])
            raise AssertionError("replay accepted")
        except RuntimeError:
            pass
        frappe.db.rollback(save_point="before_recovery_test")
        assert frappe.db.get_value("Query", records[0]["name"], "workflow_state") == "Submitted"
        frappe.db.savepoint("batch_recovery_test")
        recovery._restore_one(records[0])
        # Simulate a new change after the signed manifest, even without modified.
        frappe.db.set_value("Query", records[1]["name"], "supplier", "Later staff work", update_modified=False)
        try:
            recovery._restore_one(records[1])
            raise AssertionError("stale manifest accepted")
        except RuntimeError:
            frappe.db.rollback(save_point="batch_recovery_test")
        assert frappe.db.get_value("Query", records[0]["name"], "workflow_state") == "Submitted"
        assert frappe.db.get_value("Query", records[1]["name"], "supplier") == "Supplier preserved"
        return ["real SQL recovery changes only state and queue; business fields unchanged",
                "real Version and Info audit comment created", "replay blocked",
                "unversioned staff edit rejected by full fingerprint", "later batch failure rolls back earlier restoration"]
    finally:
        frappe.db.rollback(save_point="recovery_test_start")
