"""Delta protocol tests and read-only production reconciliation helpers."""
import json
from time import perf_counter
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


def verify_any_client():
    for client in frappe.get_all("Client", fields=["name", "email"]):
        if not frappe.db.count("Query", {"client_name": client.name}):
            continue
        users = [client.email] + frappe.get_all("User Permission", filters={"allow": "Client", "for_value": client.name}, pluck="user")
        for user in users:
            if user and frappe.db.get_value("User", user, "enabled") and "Client" in frappe.get_roles(user) and not live_data.is_staff(user):
                return verify_client(user)
    raise AssertionError("No populated Client account available")


def verify_stamp_strategy():
    rows = [frappe._dict(name=f"Q{index}") for index in range(201)]
    metadata = [frappe._dict(parent="Q0", row_count=2, latest="2026-01-01"), frappe._dict(parent="FOREIGN", row_count=9, latest="OTHER-CLIENT-METADATA")]
    with patch.object(frappe, "get_list", return_value=rows), patch.object(frappe, "get_all", return_value=metadata) as children:
        output, _ = live_data.read_rows("Query", [])
        assert "parent" not in children.call_args.kwargs["filters"]
        assert children.call_args.kwargs["order_by"] == "parent asc"
        assert len(output) == 201 and output[0]["__child_stamp"] == "2:2026-01-01"
        assert "OTHER-CLIENT-METADATA" not in json.dumps(output)
        assert all(row.name != "FOREIGN" for row in output)
    with patch.object(frappe, "get_list", return_value=rows[:1]), patch.object(frappe, "get_all", return_value=metadata) as children:
        output, _ = live_data.read_rows("Query", [])
        assert children.call_args.kwargs["filters"]["parent"] == ["in", ["Q0"]]
        assert output[0]["__child_stamp"] == "2:2026-01-01"
    return {"checks": ["large datasets avoid huge IN", "ordered grouped read", "foreign child metadata not returned", "small Client datasets stay indexed"], "passed": 4, "records_changed": 0}


def verify_access_proof():
    with patch.object(live_data, "scope", return_value=([], "verified-scope")), patch.object(live_data, "actor_client", return_value=None):
        proof = live_data.access_status()
        assert proof["user"] == frappe.session.user and proof["allowed"] and proof["scope"] == "verified-scope"
        assert "rows" not in proof and "upserts" not in proof
    with patch.object(live_data, "scope", side_effect=frappe.PermissionError("denied")), patch.object(live_data, "actor_client", return_value=None):
        proof = live_data.access_status()
        assert not proof["allowed"] and proof["scope"] is None
    original = frappe.session.user
    try:
        frappe.set_user("Guest")
        proof = live_data.access_status()
        assert proof["user"] == "Guest" and not proof["allowed"] and proof["client_scope"] is None
    finally:
        frappe.set_user(original)
    return {"checks": ["proof includes no record data", "denial cannot become access grant", "Guest cannot receive proof"], "passed": 3, "records_changed": 0}


def verify_child_deltas():
    cache = MemoryCache()
    child = [frappe._dict(parent="A", row_count=1, latest="2026-01-01")]
    with patch.object(live_data, "scope", return_value=([], "same-scope")), patch.object(frappe, "get_list", side_effect=lambda *args, **kwargs: [frappe._dict(name="A", modified="unchanged-parent")]), patch.object(frappe, "get_all", side_effect=lambda *args, **kwargs: child), patch.object(live_data, "client_count", return_value=1), patch.object(live_data, "overview_metrics", return_value={"total_queries": 1}), patch.object(frappe, "cache", return_value=cache):
        result = live_data.sync("Query")
        for count, latest in [(2, "2026-01-02"), (2, "2026-01-03")]:
            child[:] = [frappe._dict(parent="A", row_count=count, latest=latest)]
            result = live_data.sync("Query", result["cursor"])
            assert not result["reset"] and [row.name for row in result["upserts"]] == ["A"]
            assert result["upserts"][0]["__child_stamp"] == f"{count}:{latest}"
        child.clear()
        result = live_data.sync("Query", result["cursor"])
        assert result["upserts"][0]["__child_stamp"] == "0:"
    return {"checks": ["child insertion updates parent delta", "child edit updates parent delta without parent modified bump", "child removal updates parent delta"], "passed": 3, "records_changed": 0}


def benchmark(user="Administrator"):
    original = frappe.session.user
    first = None
    try:
        frappe.set_user(user)
        started = perf_counter()
        first = live_data.sync("Query")
        first_done = perf_counter()
        second = live_data.sync("Query", first["cursor"])
        second_done = perf_counter()
        assert not second["reset"] and not second["upserts"] and not second["deleted"]
        serialized = json.dumps(first, default=str)
        serialization_done = perf_counter()
        return {"initial_server_ms": round((first_done - started) * 1000), "unchanged_server_ms": round((second_done - first_done) * 1000), "serialization_ms": round((serialization_done - second_done) * 1000), "rows": first["total"], "unchanged_rows": len(second["upserts"]), "initial_bytes": len(serialized.encode()), "checks": "passed", "records_changed": 0}
    finally:
        if first:
            frappe.cache().delete_value("portal-live:" + first["cursor"].split(":")[0])
        frappe.set_user(original)
