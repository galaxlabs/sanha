# Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt

import frappe

def send_email_on_submit(doc, method):
    # Get the session user's full name
    user_fullname = frappe.get_fullname(frappe.session.user)

    # Define recipients: client (session user), admin, and evaluation users
    recipients = [doc.owner, 'admin@example.com', 'evaluation@example.com']  # Replace with actual email addresses

    # Define email subject and message for the client
    client_subject = f"Query Form Submitted: {doc.name}"
    client_message = f"""
    Dear {doc.client_name},

    We are pleased to inform you that <b>your query form No. {doc.name}</b> has been successfully <b>{doc.workflow_state}</b>.
    It has been forwarded to our Evaluation Department for further processing.

    You can expect a response from us within the next 24 hours. We appreciate your patience and understanding.
    If you have any further questions or require additional assistance, please do not hesitate to contact us at karachi@sanha.org.pk.

    Best regards,

    System Generated Email
    [Company Name]
    """

    # Define email subject and message for admin and evaluation
    admin_subject = "Client Query Submission Notification"
    admin_message = f"""
    Dear Admin/Evaluation Department,

    I hope this email finds you well.

    This is to inform you that our client, {doc.client_name}, has successfully submitted a query titled {doc.name}. The query has been forwarded to the Evaluation Department for further processing.

    Please review the query and respond accordingly within the next 24 hours.

    If you have any further questions or require additional information, please do not hesitate to contact us.

    Best regards,

    System Generated Email
    [Company Name]
    """

    # Send email to the client
    frappe.sendmail(
        recipients=[doc.owner],
        subject=client_subject,
        message=client_message
    )

    # Send email to admin and evaluation
    frappe.sendmail(
        recipients=['admin@example.com', 'evaluation@example.com'],  # Replace with actual email addresses
        subject=admin_subject,
        message=admin_message
    )

def send_email_on_workflow_change(doc, method):
    # Define recipient: only the owner of the document
    recipients = [doc.owner]

    # Define email subject and message for the client
    client_subject = f"Response to Your Query"
    client_message = f"""
    Dear {doc.client_name},

    I hope this email finds you well.

    We are pleased to inform you that a response to your query titled {doc.name} has been issued. Please visit our web portal to check the status and view the response.

    Thank you for your patience and understanding. If you have any further questions or need additional assistance, please do not hesitate to contact us.

    Best regards,

    System Generated Email
    [Company Name]
    """

    # Send email to the client
    frappe.sendmail(
        recipients=recipients,
        subject=client_subject,
        message=client_message
    )

