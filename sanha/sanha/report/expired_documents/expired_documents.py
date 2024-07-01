# Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt

# Create a new Script Report
# Go to Report List -> New Report -> Enter details
# Type: Script Report
# Apply to: Query

# In the Script section, add the following code

import frappe
from frappe.utils import nowdate

def execute(filters=None):
    columns, data = [], []
    columns = [
        {"fieldname": "query_name", "label": "Query Name", "fieldtype": "Link", "options": "Query", "width": 200},
        {"fieldname": "raw_material", "label": "Raw Material", "fieldtype": "Data", "width": 150},
        {"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 100},
        {"fieldname": "creation_from", "label": "Submit Date", "fieldtype": "Date", "width": 100},
        {"fieldname": "owner_full_name", "label": "Owner Full Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "document_name", "label": "Document Name", "fieldtype": "Link", "options": "Documents", "width": 200},
        {"fieldname": "expiry_date", "label": "Expiry Date", "fieldtype": "Date", "width": 100}
    ]

    data = frappe.db.sql("""
        SELECT
            q.name AS query_name,
            q.raw_material AS raw_material,
            q.workflow_state AS status,
            q.creation AS creation_from,
            u.full_name AS owner_full_name,
            d.documents AS document_name,
            d.expiry_date AS expiry_date
        FROM
            `tabQuery` q
        JOIN
            `tabUser` u ON q.owner = u.name
        JOIN
            `tabDocuments` d ON q.name = d.parent
        WHERE
            q.workflow_state <> 'Draft'
            AND d.expiry_date < CURDATE()
    """, as_dict=True)

    return columns, data
