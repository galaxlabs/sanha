import frappe
from frappe.utils import cint
from sanha.api.auth import _find_client

STAFF = {"Admin", "System Manager", "Administrator", "Evaluation", "SB User", "Certificate Manager"}


def is_staff(user):
    return user == "Administrator" or bool(STAFF.intersection(frappe.get_roles(user)))


def allowed_contact(user, other):
    if not is_staff(user) and "Client" not in frappe.get_roles(user):
        return False
    if user == other or other in {"Guest", "Administrator"} or not frappe.db.get_value("User", other, "enabled"):
        return False
    if is_staff(other):
        return True
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
    doc = frappe.get_doc("Query", query)
    if not is_staff(user):
        client = _find_client(user, frappe.db.get_value("User", user, "email"))
        if not client or doc.client_name != client.name:
            frappe.throw("This query is not available to this conversation.", frappe.PermissionError)
    elif not frappe.has_permission("Query", "read", doc, user=user):
        frappe.throw("Query is not accessible.", frappe.PermissionError)


@frappe.whitelist()
def query_options(search="", start=0):
    user = frappe.session.user
    filters = []
    if not is_staff(user):
        client = _find_client(user, frappe.db.get_value("User", user, "email"))
        if not client:
            return []
        filters.append(["client_name", "=", client.name])
    return frappe.get_list("Query", filters=filters, or_filters=[["name", "like", "%" + search + "%"], ["raw_material", "like", "%" + search + "%"]], fields=["name", "raw_material"], limit_start=max(0, cint(start)), limit_page_length=30, order_by="modified desc")


@frappe.whitelist()
def conversation(contact):
    user = frappe.session.user
    if not allowed_contact(user, contact):
        frappe.throw("Contact is not allowed.", frappe.PermissionError)
    return frappe.get_all("Portal Message", filters={"sender": ["in", [user, contact]], "recipient": ["in", [user, contact]]}, fields=["name", "sender", "recipient", "message", "query_reference", "creation"], order_by="creation desc", limit_page_length=100)[::-1]


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
