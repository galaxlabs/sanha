from unittest.mock import patch
import frappe
from sanha.api import messaging


def run_policy_checks():
    roles = {"client-a": ["Client"], "client-b": ["Client"], "eval": ["Evaluation"], "sb": ["SB User"], "cm": ["Certificate Manager"], "other": []}
    with patch.object(frappe, "get_roles", side_effect=lambda user: roles.get(user, [])), patch.object(frappe.db, "get_value", return_value=1):
        assert not messaging.allowed_contact("client-a", "client-b")
        assert not messaging.allowed_contact("other", "eval")
        for staff in ("eval", "sb", "cm"):
            assert messaging.allowed_contact("client-a", staff)
            assert messaging.allowed_contact(staff, "client-b")
        assert not messaging.allowed_contact("client-a", "Guest")
        assert not messaging.allowed_contact("eval", "Administrator")
        assert messaging.allowed_contact("eval", "sb")
        assert messaging.allowed_contact("cm", "eval")
    with patch.object(messaging, "allowed_contact", return_value=False), patch.object(frappe, "get_doc") as create:
        try:
            messaging.send("client-b", "Blocked message")
        except frappe.PermissionError:
            pass
        else:
            raise AssertionError("Client-to-client send must be rejected")
        create.assert_not_called()
    with patch.object(messaging, "is_staff", return_value=False), patch.object(messaging, "_find_client", return_value=frappe._dict(name="Client A")), patch.object(frappe.db, "get_value", return_value="client-a"), patch.object(frappe, "get_doc", return_value=frappe._dict(client_name="Client B")):
        try:
            messaging.check_query("OTHER-QUERY", "client-a")
        except frappe.PermissionError:
            pass
        else:
            raise AssertionError("Cross-client Query reference must be rejected")
    return {"policy_checks": "passed", "database_messages_written": 0}
