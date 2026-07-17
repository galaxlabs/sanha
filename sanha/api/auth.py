import frappe


CLIENT_FIELDS = [
    "name",
    "client_name",
    "client_code",
    "email",
    "business_name",
    "certified_since",
    "certified_expiry",
    "ext",
    "standards",
    "region",
    "city",
    "scope",
    "category",
    "status",
    "contact_person",
    "contact_no",
]

SYSTEM_ROLES = {"All", "Guest"}

STAFF_ROLES = {
    "Evaluation",
    "SB User",
    "Certificate Manager",
    "Admin",
    "System Manager",
    "Administrator",
}

PORTAL_ROLES = {
    "Client",
    "Evaluation",
    "SB User",
    "Certificate Manager",
    "Admin",
    "System Manager",
    "Administrator",
}

PORTAL_URL = "https://portal.sanha.org.pk/dashboard"


def _user_info(user):
    info = frappe.db.get_value(
        "User",
        user,
        ["name", "email", "full_name", "first_name", "last_name", "enabled"],
        as_dict=True,
    ) or {}

    return {
        "name": info.get("name") or user,
        "email": info.get("email") or user,
        "full_name": info.get("full_name") or info.get("first_name") or user,
        "first_name": info.get("first_name"),
        "last_name": info.get("last_name"),
        "enabled": info.get("enabled"),
    }


def _get_client(name):
    if not name:
        return None

    return frappe.db.get_value("Client", name, CLIENT_FIELDS, as_dict=True)


def _find_client(user, email):
    permission_rows = frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": "Client"},
        fields=["for_value", "is_default"],
        order_by="is_default desc, modified desc",
        limit=5,
        ignore_permissions=True,
    )

    for row in permission_rows:
        client = _get_client(row.get("for_value"))
        if client:
            return client

    if email:
        client_name = frappe.db.get_value("Client", {"email": email}, "name")
        client = _get_client(client_name)
        if client:
            return client

    client_name = frappe.db.get_value("Client", {"owner": user}, "name")
    return _get_client(client_name)


def _should_auto_redirect_to_portal(user, roles=None):
    """Auto-redirect only pure Client users.

    Staff users may still open the portal manually, but they are not forced there.
    """
    roles = set(roles or frappe.get_roles(user)) - SYSTEM_ROLES

    if STAFF_ROLES.intersection(roles):
        return False

    return "Client" in roles


def redirect_client_after_login(login_manager=None):
    """Redirect only pure Client users to SANHA React portal after Frappe login."""
    user = frappe.session.user

    if not user or user == "Guest":
        return

    roles = [role for role in frappe.get_roles(user) if role not in SYSTEM_ROLES]

    if _should_auto_redirect_to_portal(user, roles):
        frappe.local.response["home_page"] = PORTAL_URL


@frappe.whitelist(allow_guest=True)
def get_current_user():
    """Return SPA-safe auth state for the current Frappe session.

    This endpoint intentionally uses server-side lookups instead of requiring
    portal users to read User, User Permission, or Client through DocType REST.
    """
    user = frappe.session.user

    if not user or user == "Guest":
        return {
            "is_authenticated": False,
            "message": "Guest",
            "user": None,
            "name": "Guest",
            "email": None,
            "full_name": "Guest",
            "roles": [],
            "clientName": None,
            "clientData": None,
        }

    info = _user_info(user)
    roles = [role for role in frappe.get_roles(user) if role not in SYSTEM_ROLES]
    role_set = set(roles)

    client = None

    if not STAFF_ROLES.intersection(role_set):
        client = _find_client(user, info.get("email"))

        if client and "Client" not in role_set:
            roles.append("Client")
            role_set.add("Client")

    roles = [role for role in roles if role in PORTAL_ROLES]
    client_name = client.get("name") if client else None

    return {
        "is_authenticated": True,
        "message": user,
        "user": user,
        "name": user,
        "email": info.get("email"),
        "full_name": info.get("full_name"),
        "roles": roles,
        "clientName": client_name,
        "clientData": client,
    }


@frappe.whitelist(allow_guest=True)
def get_me():
    return get_current_user()