# Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt

# Create a new Script Report
# Go to Report List -> New Report -> Enter details
# Type: Script Report
# Apply to: Query

# In the Script section, add the following code

import frappe


STAFF_ROLES = {"Evaluation", "SB User", "Certificate Manager", "Admin", "System Manager", "Administrator"}


def get_client_name_for_user(user):
    client_name = frappe.db.get_value("Client", {"email": user}, "name")
    if client_name:
        return client_name
    return frappe.db.get_value("Client", {"owner": user}, "name")


def get_scope_condition():
    roles = set(frappe.get_roles(frappe.session.user))
    if STAFF_ROLES.intersection(roles):
        return "", {}

    client_name = get_client_name_for_user(frappe.session.user)
    if client_name:
        return "AND (q.client_name = %(client_name)s OR q.owner = %(user)s)", {"client_name": client_name, "user": frappe.session.user}
    return "AND q.owner = %(user)s", {"user": frappe.session.user}

def execute(filters=None):
    columns, data = [], []
    columns = [
        {"fieldname": "query_name", "label": "Query Name", "fieldtype": "Link", "options": "Query", "width": 200},
        {"fieldname": "raw_material", "label": "Raw Material", "fieldtype": "Data", "width": 150},
        {"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 100},
        {"fieldname": "creation_from", "label": "Submit Date", "fieldtype": "Date", "width": 100},
        {"fieldname": "owner_full_name", "label": "Owner Full Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "client_name", "label": "Client", "fieldtype": "Data", "width": 150},
        {"fieldname": "document_name", "label": "Document Name", "fieldtype": "Link", "options": "Documents", "width": 200},
        {"fieldname": "issue_date", "label": "Issue Date", "fieldtype": "Date", "width": 100},
        {"fieldname": "expiry_date", "label": "Expiry Date", "fieldtype": "Date", "width": 100},
        {"fieldname": "attachment", "label": "Attachment", "fieldtype": "Data", "width": 220},
    ]

    scope_condition, params = get_scope_condition()

    data = frappe.db.sql(f"""
        SELECT
            q.name AS query_name,
            q.raw_material AS raw_material,
            q.workflow_state AS status,
            q.creation AS creation_from,
            u.full_name AS owner_full_name,
            q.client_name AS client_name,
            d.documents AS document_name,
            d.issue_date AS issue_date,
            d.expiry_date AS expiry_date,
            d.attachment AS attachment
        FROM
            `tabQuery` q
        JOIN
            `tabUser` u ON q.owner = u.name
        JOIN
            `tabDocuments` d ON q.name = d.parent
        WHERE
            q.workflow_state <> 'Draft'
            AND q.workflow_state <> 'Delisted'
            AND d.expiry_date < CURDATE()
            AND NOT EXISTS (
                SELECT 1
                FROM `tabDocuments` newer
                WHERE newer.parent = d.parent
                  AND IFNULL(newer.documents, '') = IFNULL(d.documents, '')
                  AND newer.idx > d.idx
            )
            {scope_condition}
        ORDER BY d.expiry_date ASC, q.modified DESC
    """, params, as_dict=True)

    return columns, data
