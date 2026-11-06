"""Read-only checks for count/permission reconciliation; no fixture messages or Queries."""
import frappe
from sanha.api.dashboard import overview_metrics, state_counts
from sanha.api.auth import _find_client


def verify_counts(user="Administrator"):
    original = frappe.session.user
    try:
        frappe.set_user(user)
        metrics = overview_metrics()
        states = state_counts()
        assert sum(int(row["count"]) for row in states) == metrics["total_queries"]
        filters = {}
        roles = set(frappe.get_roles())
        if "Client" in roles and not roles.intersection({"Admin", "System Manager", "Administrator", "Evaluation", "SB User", "Certificate Manager"}):
            client = _find_client(user, frappe.db.get_value("User", user, "email"))
            filters = {"client_name": client.name if client else ""}
        expected_total = frappe.db.count("Query", filters)
        assert metrics["total_queries"] == expected_total, (metrics, expected_total)
        expected_duplicates = frappe.db.count("Query", {**filters, "is_duplicate": 1})
        assert metrics["duplicate_queries"] == expected_duplicates
        assert metrics["unique_materials"] <= metrics["total_queries"]
        # Apply an additional filter and ensure it cannot widen Client scope.
        approved = overview_metrics([["workflow_state", "=", "Approved"]])
        assert approved["total_queries"] == frappe.db.count("Query", {**filters, "workflow_state": "Approved"})
        pages = []
        offset = 0
        while True:
            rows = frappe.get_list("Query", fields=["name"], order_by="modified desc, name asc", limit_start=offset, limit_page_length=500)
            if not rows:
                break
            pages.extend(row.name for row in rows)
            offset += len(rows)
        assert len(pages) == len(set(pages)) == metrics["total_queries"]
        return {"scope": "Client" if filters else "staff", "metrics": metrics, "paged_rows": len(pages), "checks": "passed"}
    finally:
        frappe.set_user(original)


def verify_populated_client():
    """Choose an existing Client test account with Queries, without creating data."""
    for client in frappe.get_all("Client", fields=["name", "email"]):
        if not frappe.db.count("Query", {"client_name": client.name}):
            continue
        candidates = [client.email] + frappe.get_all("User Permission", filters={"allow": "Client", "for_value": client.name}, pluck="user")
        for user in candidates:
            if user and frappe.db.get_value("User", user, "enabled") and "Client" in frappe.get_roles(user):
                result = verify_counts(user)
                if result["scope"] == "Client" and result["paged_rows"]:
                    return result
    raise AssertionError("No populated Client account available for scope verification")
