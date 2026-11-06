"""Delta protocol tests and read-only production reconciliation helpers."""
import json
from unittest.mock import patch

import frappe
from sanha.api import live_data


class MemoryCache:
    def __init__(self):
        self.values = {}
    def get_value(self, key):
        return self.values.get(key)
    def set_value(self, key, value, **kwargs):
        self.values[key] = value


def run_checks():
    cache = MemoryCache()
    rows = [frappe._dict(name="A", raw_material="First", modified="same"), frappe._dict(name="B", raw_material="Second", modified="same")]
    signature = ["scope-a"]
    metrics = lambda filters: {"total_queries": len(rows), "unique_materials": len(rows), "duplicate_queries": 0, "clients": 1}
    with patch.object(live_data, "scope", side_effect=lambda doctype: ([], signature[0])), patch.object(live_data, "read_rows", side_effect=lambda *args: (rows, None)), patch.object(live_data, "client_count", return_value=1), patch.object(live_data, "overview_metrics", side_effect=metrics), patch.object(frappe, "cache", return_value=cache):
        first = live_data.sync("Query")
        assert first["reset"] and len(first["upserts"]) == 2
        unchanged = live_data.sync("Query", first["cursor"])
        assert not unchanged["reset"] and unchanged["upserts"] == [] and unchanged["deleted"] == []
        rows[:] = [frappe._dict(name="A", raw_material="Edited without modified bump", modified="same"), frappe._dict(name="C", raw_material="New", modified="same")]
        changed = live_data.sync("Query", unchanged["cursor"])
        assert {row.name for row in changed["upserts"]} == {"A", "C"} and changed["deleted"] == ["B"]
        forked = live_data.sync("Query", changed["cursor"], fork=1)
        assert not forked["reset"] and forked["upserts"] == [] and forked["cursor"] != changed["cursor"]
        stale = live_data.sync("Query", first["cursor"])
        assert stale["reset"] and len(stale["upserts"]) == 2
        signature[0] = "new-permissions"
        scoped = live_data.sync("Query", stale["cursor"])
        assert scoped["reset"]
        # A cursor copied from another authenticated account cannot expose its rows/deletions.
        token = scoped["cursor"].split(":")[0]
        cache.values["portal-live:" + token]["user"] = "someone-else"
        foreign = live_data.sync("Query", scoped["cursor"])
        assert foreign["reset"] and foreign["deleted"] == [] and foreign["cursor"].split(":")[0] != token
    return {"checks": ["initial complete snapshot", "unchanged zero-row delta", "insert/edit/delete delta", "update_modified=False scalar edit", "independent browser cursor fork", "stale cursor safe reset", "permission signature reset", "foreign cursor isolation"], "passed": 8, "records_changed": 0}


def verify_existing(doctype="Query"):
    first = second = None
    try:
        first = live_data.sync(doctype)
        second = live_data.sync(doctype, first["cursor"])
        assert len(first["upserts"]) == first["total"]
        assert second["upserts"] == [] and second["deleted"] == [] and not second["reset"]
        return {"dataset": doctype, "total": first["total"], "initial_rows": len(first["upserts"]), "unchanged_rows_transferred": len(second["upserts"]), "initial_bytes": len(json.dumps(first, default=str).encode()), "unchanged_bytes": len(json.dumps(second, default=str).encode()), "metrics": first["metrics"], "checks": "passed", "records_changed": 0}
    finally:
        if first:
            frappe.cache().delete_value("portal-live:" + first["cursor"].split(":")[0])


def verify_client(user):
    from sanha.api.auth import _find_client
    original = frappe.session.user
    staff = live_data.sync("Query")
    try:
        frappe.set_user(user)
        client = _find_client(user, frappe.db.get_value("User", user, "email"))
        assert client
        response = live_data.sync("Query", staff["cursor"])
        try:
            assert response["reset"]
            assert all(row.client_name == client.name for row in response["upserts"])
            assert response["deleted"] == []
            result = verify_existing("Query")
            result["foreign_staff_cursor_isolated"] = True
            return result
        finally:
            frappe.cache().delete_value("portal-live:" + response["cursor"].split(":")[0])
    finally:
        frappe.set_user(original)
        frappe.cache().delete_value("portal-live:" + staff["cursor"].split(":")[0])
