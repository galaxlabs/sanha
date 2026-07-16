import frappe


def normalize_client_name(value):
    return " ".join((value or "").split()).strip()


def ensure_email_whitelist_client(client_name="Shan Foods Private Limited"):
    """
    Ensure a client exists in Email Notification Settings.enabled_clients.
    Safe to run multiple times.
    """

    client_name = normalize_client_name(client_name)

    if not client_name:
        frappe.throw("Client name is required.")

    settings = frappe.get_doc("Email Notification Settings")

    existing = {
        normalize_client_name(row.clients).lower()
        for row in settings.enabled_clients
        if row.clients
    }

    if client_name.lower() not in existing:
        settings.append("enabled_clients", {
            "clients": client_name
        })
        settings.save(ignore_permissions=True)
        frappe.db.commit()
        return {
            "ok": True,
            "action": "added",
            "client": client_name,
        }

    return {
        "ok": True,
        "action": "already_exists",
        "client": client_name,
    }


def resync_query_notify_client(client_name="Shan Foods Private Limited"):
    """
    Recalculate notify_client for existing Query records of one client.
    """

    client_name = normalize_client_name(client_name)

    settings = frappe.get_doc("Email Notification Settings")
    allowed = {
        normalize_client_name(row.clients).lower()
        for row in settings.enabled_clients
        if row.clients
    }

    notify_value = 1 if client_name.lower() in allowed else 0

    queries = frappe.get_all(
        "Query",
        filters={"client_name": client_name},
        fields=["name", "client_name", "notify_client"],
        limit_page_length=0,
        ignore_permissions=True,
    )

    updated = []

    for q in queries:
        if int(q.notify_client or 0) != notify_value:
            frappe.db.set_value(
                "Query",
                q.name,
                "notify_client",
                notify_value,
                update_modified=False,
            )
            updated.append(q.name)

    frappe.db.commit()

    return {
        "ok": True,
        "client": client_name,
        "notify_client": notify_value,
        "total_queries": len(queries),
        "updated": updated,
    }


def run():
    """
    Main bench-executable function.
    """

    client_name = "Shan Foods Private Limited"

    whitelist_result = ensure_email_whitelist_client(client_name)
    sync_result = resync_query_notify_client(client_name)

    return {
        "whitelist_result": whitelist_result,
        "sync_result": sync_result,
    }