import frappe


def flush_pending_email_queue(limit=50):
    """
    Send pending Email Queue records using the same Document send method
    that works when user clicks Send Now.

    Safe:
    - only status = Not Sent
    - only limited batch
    - commits after each successful send
    """

    pending = frappe.get_all(
        "Email Queue",
        filters={"status": "Not Sent"},
        fields=["name", "email_account", "creation"],
        order_by="creation asc",
        limit=limit,
    )

    sent = []
    failed = []

    for row in pending:
        try:
            q = frappe.get_doc("Email Queue", row.name)

            # Same backend action as manual send button in most Frappe versions
            q.send()

            frappe.db.commit()
            sent.append(row.name)

        except Exception:
            frappe.db.rollback()
            failed.append(row.name)
            frappe.log_error(
                frappe.get_traceback(),
                f"Auto Email Queue Send Failed: {row.name}",
            )

    return {
        "total_checked": len(pending),
        "sent": sent,
        "failed": failed,
    }