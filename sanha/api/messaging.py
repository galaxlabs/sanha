import frappe
import json
import re
from frappe.utils import cint, now_datetime
from sanha.api.auth import _find_client

STAFF = {"Admin", "System Manager", "Administrator", "Evaluation", "SB User", "Certificate Manager"}
# Roles that can be contacted in messaging. System Manager is not listed; the Web Admin account keeps Admin.
CONTACT_ROLES = {"Admin", "Evaluation", "SB User", "Certificate Manager"}


def is_staff(user):
    return user == "Administrator" or bool(STAFF.intersection(frappe.get_roles(user)))


def allowed_contact(user, other):
    if not is_staff(user) and "Client" not in frappe.get_roles(user):
        return False
    if user == other or other in {"Guest", "Administrator"} or not frappe.db.get_value("User", other, "enabled"):
        return False
    if is_staff(other):
        return bool(CONTACT_ROLES.intersection(frappe.get_roles(other)))
    return is_staff(user) and "Client" in frappe.get_roles(other)


@frappe.whitelist()
def contacts():
    user = frappe.session.user
    roles = STAFF | ({"Client"} if is_staff(user) else set())
    names = frappe.get_all("Has Role", filters={"parenttype": "User", "role": ["in", list(roles)]}, pluck="parent")
    rows = frappe.get_all("User", filters={"name": ["in", list(set(names))], "enabled": 1}, fields=["name", "full_name"])
    return [{**row, "departments": sorted(STAFF.intersection(frappe.get_roles(row.name))) or ["Client"]} for row in rows if allowed_contact(user, row.name)]


def check_query(query, user):
    if not query:
        return
    if not is_staff(user):
        client = _find_client(user, frappe.db.get_value("User", user, "email"))
        visible = frappe.get_list("Query", filters={"name": query, "client_name": client.name}, fields=["name"], user=user, limit_page_length=1) if client else []
        if not visible:
            frappe.throw("This query is not available to this conversation.", frappe.PermissionError)
    else:
        doc = frappe.get_doc("Query", query)
        if not frappe.has_permission("Query", "read", doc, user=user):
            frappe.throw("Query is not accessible.", frappe.PermissionError)


def conversation_query_filters(contact):
    user = frappe.session.user
    if not contact or not allowed_contact(user, contact):
        frappe.throw("Contact is not allowed.", frappe.PermissionError)
    filters = []
    for participant in (user, contact):
        if not is_staff(participant):
            client = _find_client(participant, frappe.db.get_value("User", participant, "email"))
            if not client:
                frappe.throw("Client account is not linked.", frappe.PermissionError)
            filters.append(["client_name", "=", client.name])
    return filters


@frappe.whitelist()
def query_options(contact, search="", start=0):
    filters = conversation_query_filters(contact)
    search = str(search or "")[:100]
    return frappe.get_list("Query", filters=filters, or_filters=[["name", "like", "%" + search + "%"], ["raw_material", "like", "%" + search + "%"]], fields=["name", "raw_material", "workflow_state"], limit_start=max(0, cint(start)), limit_page_length=30, order_by="modified desc, name asc")


@frappe.whitelist()
def query_timeline(contact, query):
    conversation_query_filters(contact)
    check_query(query, frappe.session.user)
    check_query(query, contact)
    doc = frappe.get_doc("Query", query)
    doc.check_permission("read")
    events = [{"id": "created", "time": str(doc.creation), "kind": "created", "label": "Query created"}]
    versions = frappe.get_all("Version", filters={"ref_doctype": "Query", "docname": doc.name}, fields=["name", "creation", "data"], order_by="creation asc", limit_page_length=0)
    for version in versions:
        try:
            data = json.loads(version.data or "{}")
        except (ValueError, TypeError):
            continue
        if not isinstance(data, dict):
            continue
        changes = data.get("changed") or []
        if not isinstance(changes, list):
            continue
        for index, change in enumerate(changes):
            if isinstance(change, (list, tuple)) and len(change) >= 3 and change[0] == "workflow_state":
                events.append({"id": f"{version.name}:{index}", "time": str(version.creation), "kind": "workflow", "label": "Workflow status changed", "from_state": change[1], "to_state": change[2]})
    events.append({"id": "updated", "time": str(doc.modified), "kind": "updated", "label": "Last record update"})
    if is_staff(frappe.session.user):
        comments = frappe.get_all(
            "Comment",
            filters={"reference_doctype": "Query", "reference_name": doc.name, "comment_type": "Comment"},
            fields=["name", "content", "comment_by", "creation"],
            limit_page_length=500,
        )
        for comment in comments:
            text = re.sub(r"<[^>]+>", "", comment.content or "").strip()
            events.append({"id": f"comment:{comment.name}", "time": str(comment.creation), "kind": "comment", "label": "Team comment", "author": comment.comment_by, "text": text[:2000]})
    events.sort(key=lambda event: event["time"])
    return {"query": doc.name, "raw_material": doc.raw_material, "current_state": doc.workflow_state, "events": events, "history_note": "Only recorded workflow changes are shown. Internal comments and other document fields are not included; earlier history may be unavailable if version tracking was not enabled."}


@frappe.whitelist()
def conversation(contact):
    user = frappe.session.user
    if not allowed_contact(user, contact):
        frappe.throw("Contact is not allowed.", frappe.PermissionError)
    rows = frappe.get_all("Portal Message", filters={"sender": ["in", [user, contact]], "recipient": ["in", [user, contact]]}, fields=["name", "sender", "recipient", "message", "query_reference", "creation", "delivered_at", "read_at"], order_by="creation desc", limit_page_length=100)
    return [row for row in rows[::-1] if (row.sender == user and row.recipient == contact) or (row.sender == contact and row.recipient == user)]


@frappe.whitelist(methods=["POST"])
def send(contact, message, query_reference=None):
    user = frappe.session.user
    if not allowed_contact(user, contact):
        frappe.throw("Contact is not allowed.", frappe.PermissionError)
    if not isinstance(message, str) or not message.strip() or len(message) > 10000:
        frappe.throw("Message must contain 1–10000 characters.")
    check_query(query_reference, user)
    check_query(query_reference, contact)
    doc = frappe.get_doc({"doctype": "Portal Message", "sender": user, "recipient": contact, "message": message.strip(), "query_reference": query_reference or None})
    doc.insert(ignore_permissions=True)
    return doc.name


@frappe.whitelist()
def unread_summary():
    """Unread counts for the signed-in user. Calling this marks incoming messages as delivered."""
    user = frappe.session.user
    if not is_staff(user) and "Client" not in frappe.get_roles(user):
        frappe.throw("Messaging is not available for this account.", frappe.PermissionError)
    now = now_datetime()
    frappe.db.sql("UPDATE `tabPortal Message` SET delivered_at=%s WHERE recipient=%s AND delivered_at IS NULL", (now, user))
    rows = frappe.db.sql("SELECT sender, COUNT(name) FROM `tabPortal Message` WHERE recipient=%s AND read_at IS NULL GROUP BY sender", (user,))
    by_contact = {sender: int(count) for sender, count in rows if allowed_contact(user, sender)}
    return {"total": sum(by_contact.values()), "by_contact": by_contact}


@frappe.whitelist(methods=["POST"])
def mark_read(contact):
    """Mark messages from this contact to the signed-in user as read."""
    user = frappe.session.user
    if not allowed_contact(user, contact):
        frappe.throw("Contact is not allowed.", frappe.PermissionError)
    now = now_datetime()
    frappe.db.sql("UPDATE `tabPortal Message` SET read_at=%s, delivered_at=COALESCE(delivered_at, %s) WHERE recipient=%s AND sender=%s AND read_at IS NULL", (now, now, user, contact))
    return True
