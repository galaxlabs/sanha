"""One-off, Administrator-only recovery of the November 2026 scheduler incident.

Not a whitelisted API or scheduler task. Never select records by their status alone.
The private manifest, database backup and per-record history guards are mandatory.
"""

import gzip
import hashlib
import json
import os
import time
from collections import Counter
from datetime import timedelta
from pathlib import Path

import frappe
from frappe.utils import get_datetime, now_datetime

INCIDENT_START = "2026-11-05 23:17:10"
INCIDENT_END = "2026-11-06 00:23:00"
INCIDENT = "legacy-client-scheduler-2026-11-05"
CHANGE = ["workflow_state", "Draft", "Submitted"]


def _admin():
    if frappe.session.user != "Administrator":
        raise frappe.PermissionError("Recovery is restricted to Administrator bench execution.")


def _digest(value):
    return hashlib.sha256(json.dumps(value, default=str, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _data(version):
    return json.loads(version["data"] or "{}")


def _incident_event(version):
    data = _data(version)
    changes = data.get("changed") or []
    fields = [change[0] for change in changes]
    return (
        version["owner"] == "Administrator"
        and get_datetime(INCIDENT_START) <= get_datetime(version["creation"]) <= get_datetime(INCIDENT_END)
        and CHANGE in changes
        and len(fields) == len(set(fields))
        # Frappe applied this existing checkbox default and fetched the linked
        # Client code during the bad save. No other field/child edits qualify.
        and set(fields) <= {"workflow_state", "notify_client", "client_code"}
        and all(change[1] in (None, 0) and change[2] == 1 for change in changes if change[0] == "notify_client")
        and not any(data.get(key) for key in ("added", "removed", "row_changed", "data_import", "updater_reference"))
    )


def _versions(name):
    return frappe.db.sql(
        "SELECT name,docname,owner,creation,data FROM tabVersion "
        "WHERE ref_doctype=%s AND docname=%s ORDER BY creation,name",
        ("Query", name), as_dict=True,
    )


def _snapshot(name, lock=False):
    rows = frappe.db.sql("SELECT * FROM tabQuery WHERE name=%s" + (" FOR UPDATE" if lock else ""), (name,), as_dict=True)
    if not rows:
        return None
    # The old scheduler saved all child rows too. Include every child-table field.
    children = {}
    for field in frappe.get_meta("Query").get_table_fields():
        table = frappe.qb.DocType(field.options)
        children[field.fieldname] = (
            frappe.qb.from_(table).select(table.star)
            .where((table.parent == name) & (table.parenttype == "Query") & (table.parentfield == field.fieldname))
            .orderby(table.idx).run(as_dict=True)
        )
    files = frappe.get_all("File", filters={"attached_to_doctype": "Query", "attached_to_name": name},
                           fields=["name", "creation", "modified", "file_url", "attached_to_field", "is_private"], order_by="name")
    comments = frappe.get_all("Comment", filters={"reference_doctype": "Query", "reference_name": name},
                              fields=["name", "creation", "modified", "comment_type"], order_by="name")
    client_code = frappe.db.get_value("Client", rows[0].get("client_name"), "client_code") if rows[0].get("client_name") else None
    return {"parent": rows[0], "children": children, "files": files, "comments": comments, "versions": _versions(name), "linked_client_code": client_code}


def _classify(snapshot, event):
    """Reject ambiguity and any work after the specific incident save."""
    if not snapshot:
        return "missing"
    row = snapshot["parent"]
    if not _incident_event(event):
        return "not_exact_incident_event"
    if get_datetime(row["creation"]) >= get_datetime(INCIDENT_START):
        return "created_after_activation"
    if row["workflow_state"] != "Submitted":
        return "current_state:" + str(row["workflow_state"])
    if row["docstatus"] != 0:
        return "nonzero_docstatus"
    if row.get("was_auto_submitted") or row.get("auto_submit_after") or row.get("auto_submit_user"):
        return "new_tracking_or_schedule"
    if row["modified_by"] != "Administrator":
        return "different_last_actor"
    if any(change[2] != snapshot["linked_client_code"] or change[2] != row.get("client_code")
           for change in _data(event)["changed"] if change[0] == "client_code"):
        return "client_code_not_current_fetch"
    delta = get_datetime(event["creation"]) - get_datetime(row["modified"])
    if not timedelta(0) <= delta <= timedelta(seconds=2):
        return "modified_outside_incident_save"
    later = [v for v in snapshot["versions"] if get_datetime(v["creation"]) > get_datetime(event["creation"])]
    if later:
        return "later_version"
    # Child row timestamps from that same save equal the parent timestamp.
    if any(get_datetime(c["modified"]) > get_datetime(row["modified"])
           for children in snapshot["children"].values() for c in children):
        return "later_child_edit"
    if any(get_datetime(f["modified"]) > get_datetime(event["creation"]) for f in snapshot["files"]):
        return "later_file_edit"
    if any(get_datetime(c["creation"]) > get_datetime(event["creation"])
           or get_datetime(c["modified"]) > get_datetime(event["creation"]) for c in snapshot["comments"]):
        return "later_comment"
    return "eligible"


def _baseline():
    return frappe.db.sql("SELECT name,workflow_state,modified,modified_by,docstatus FROM tabQuery ORDER BY name", as_dict=True)


def _build_plan():
    events = frappe.db.sql(
        "SELECT name,docname,owner,creation,data FROM tabVersion "
        "WHERE ref_doctype=%s AND owner=%s AND creation BETWEEN %s AND %s ORDER BY creation,name",
        ("Query", "Administrator", INCIDENT_START, INCIDENT_END), as_dict=True,
    )
    grouped = {}
    for event in events:
        if _incident_event(event):
            grouped.setdefault(event.docname, []).append(event)
    eligible, excluded = [], []
    for name, history in grouped.items():
        event = history[-1]
        snap = _snapshot(name)
        # More than one qualifying transition is itself evidence of intervening work.
        reason = "multiple_incident_transitions" if len(history) != 1 else _classify(snap, event)
        record = {"name": name, "event": event, "reason": reason}
        if reason == "eligible":
            record["snapshot"] = snap
            record["snapshot_digest"] = _digest(snap)
            eligible.append(record)
        else:
            record["current_state"] = snap["parent"]["workflow_state"] if snap else None
            excluded.append(record)
    baseline = _baseline()
    unaffected_submitted = [r for r in baseline if r["workflow_state"] == "Submitted" and r["name"] not in grouped]
    # Keep IDs/history in the private manifest, not ordinary application logs.
    protected = [{"row": r, "versions": _versions(r["name"])} for r in unaffected_submitted]
    return {"incident": INCIDENT, "site": frappe.local.site, "created_at": now_datetime(),
            "eligible": eligible, "excluded": excluded, "baseline": baseline,
            "unaffected_submitted": protected}


def _summary(plan):
    return {"incident": INCIDENT, "site": plan["site"], "incident_queries": len(plan["eligible"]) + len(plan["excluded"]),
            "eligible": len(plan["eligible"]), "excluded": dict(Counter(r["reason"] for r in plan["excluded"])),
            "states_before": dict(Counter(r["workflow_state"] for r in plan["baseline"])),
            "protected_submitted_outside_incident": len(plan["unaffected_submitted"])}


def audit():
    _admin()
    return _summary(_build_plan())


def _private_file(name):
    if Path(name).name != name:
        raise ValueError("A backup basename is required.")
    return Path(frappe.get_site_path("private", "backups", name))


def _write_private(path, value):
    # Never overwrite prior evidence, and do not expose Query data publicly.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(value, default=str, indent=2, sort_keys=True, ensure_ascii=False))
        handle.flush()
        os.fsync(handle.fileno())


def prepare():
    _admin()
    plan = _build_plan()
    digest = _digest(plan)
    name = "submission-recovery-" + now_datetime().strftime("%Y%m%d-%H%M%S") + ".json"
    _write_private(_private_file(name), plan)
    return {**_summary(plan), "manifest": name, "sha256": digest}


def _restore_one(record):
    name, event = record["name"], record["event"]
    current = _snapshot(name, lock=True)
    if _classify(current, event) != "eligible" or _digest(current) != record["snapshot_digest"]:
        raise RuntimeError("Query changed since preparation; entire batch aborted: " + name)
    # Deliberately bypass normal save hooks: this is a narrow audited correction,
    # not a Client edit, submission, document update or new AI-review request.
    frappe.db.set_value("Query", name, {"workflow_state": "Draft", "auto_submit_after": None,
                                        "auto_submit_user": None, "auto_submit_error": None})
    frappe.get_doc({"doctype": "Version", "ref_doctype": "Query", "docname": name,
                    "data": json.dumps({"changed": [["workflow_state", "Submitted", "Draft"]],
                                        "added": [], "removed": [], "row_changed": [],
                                        "recovery_incident": INCIDENT, "reversed_version": event["name"]})}).insert(ignore_permissions=True)
    frappe.get_doc({"doctype": "Comment", "comment_type": "Info", "reference_doctype": "Query",
                    "reference_name": name,
                    "content": "Restored to Draft after the unintended legacy scheduler submission. "
                               "No later work was present. Incident: " + INCIDENT + "; original Version: " + event["name"]
                               + ". Automatic scheduling cleared; only a future Client save can schedule submission."}).insert(ignore_permissions=True)
    after = _snapshot(name)
    expected = dict(current["parent"])
    actual = dict(after["parent"])
    for field in ("workflow_state", "auto_submit_after", "auto_submit_user", "auto_submit_error", "modified", "modified_by", "_comments"):
        expected.pop(field, None)
        actual.pop(field, None)
    if _digest(expected) != _digest(actual) or _digest(current["children"]) != _digest(after["children"]) or _digest(current["files"]) != _digest(after["files"]):
        raise RuntimeError("Unexpected data change; entire batch aborted: " + name)
    if after["parent"]["workflow_state"] != "Draft" or after["parent"].get("auto_submit_after"):
        raise RuntimeError("Recovery state verification failed: " + name)
    return name


def apply(manifest, sha256, expected_count, database_backup):
    _admin()
    plan = json.loads(_private_file(manifest).read_text(encoding="utf-8"))
    if _digest(plan) != sha256 or plan["incident"] != INCIDENT or plan["site"] != frappe.local.site:
        raise ValueError("Manifest digest, site or incident mismatch.")
    if len(plan["eligible"]) != int(expected_count) or not plan["eligible"]:
        raise ValueError("Explicit nonzero manifest count required.")
    if now_datetime() - get_datetime(plan["created_at"]) > timedelta(minutes=30):
        raise ValueError("Manifest expired; repeat preparation.")
    backup = _private_file(database_backup)
    if not backup.name.endswith("database.sql.gz") or backup.stat().st_size < 1024:
        raise ValueError("A real compressed database backup is required.")
    if time.time() - backup.stat().st_mtime > 3600:
        raise ValueError("Database backup must be less than one hour old.")
    with gzip.open(backup, "rb") as handle:
        header = handle.read(8192)
        if b"MariaDB" not in header and b"MySQL" not in header:
            raise ValueError("Backup is not a database dump.")
    before = _baseline()
    if _digest(before) != _digest(plan["baseline"]):
        raise RuntimeError("Queries changed since preparation; repeat audit and preparation.")
    result_path = _private_file(manifest.removesuffix(".json") + "-result.json")
    if result_path.exists():
        raise RuntimeError("This manifest has already been executed.")
    restored = []
    try:
        for record in plan["eligible"]:
            restored.append(_restore_one(record))
        after = _baseline()
        names = set(restored)
        if _digest([r for r in before if r["name"] not in names]) != _digest([r for r in after if r["name"] not in names]):
            raise RuntimeError("Protected Query changed; entire batch aborted.")
        expected_states = Counter(r["workflow_state"] for r in before)
        expected_states["Submitted"] -= len(restored)
        expected_states["Draft"] += len(restored)
        if expected_states != Counter(r["workflow_state"] for r in after):
            raise RuntimeError("Unexpected workflow totals; entire batch aborted.")
        result = {"incident": INCIDENT, "site": frappe.local.site, "manifest": manifest, "sha256": sha256,
                  "database_backup": database_backup, "restored": restored, "count": len(restored),
                  "states_after": dict(expected_states), "protected_queries_unchanged": len(after) - len(restored),
                  "completed_at": now_datetime()}
        # Keep evidence durable before committing. Its transaction label is explicit.
        _write_private(result_path, {**result, "transaction": "prepared_for_commit"})
        frappe.db.commit()
        return {k: v for k, v in result.items() if k != "restored"}
    except Exception:
        frappe.db.rollback()
        raise
