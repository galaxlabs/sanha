# Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt


import frappe

def execute(filters=None):
    # Define columns for the report
    columns = [
        {"label": "Owner", "fieldname": "owner", "fieldtype": "Data", "width": 120},
        {"label": "Raw Material", "fieldname": "raw_material", "fieldtype": "Link", "options": "Query", "width": 150},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 150},
        {"label": "Manufacturer", "fieldname": "manufacturer", "fieldtype": "Data", "width": 150},
        {"label": "Query Types", "fieldname": "query_types", "fieldtype": "Data", "width": 150},
        {"label": "Status", "fieldname": "workflow_state", "fieldtype": "Data", "width": 100},
        {"label": "From", "fieldname": "creation", "fieldtype": "Date", "width": 100},
        {"label": "To", "fieldname": "creation", "fieldtype": "Date", "width": 100}
    ]

    # Fetch query data based on the current user and additional filters
    data = get_user_queries(filters)

    return columns, data

def get_user_queries(filters):
    # Fetch queries owned by the current user and not in "Draft" or "Delisted" states
    user = frappe.session.user
    query_data = frappe.db.sql("""
        SELECT
            owner, name, raw_material, supplier, manufacturer, query_types, workflow_state, creation
        FROM `tabQuery`
        WHERE owner = %s
            AND workflow_state NOT IN ('Draft', 'Delisted')
    """, user, as_dict=True)

    return query_data