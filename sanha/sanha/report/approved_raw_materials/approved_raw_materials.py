# Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	    # Define columns for the report
    columns = [
        {"label": "Raw Material", "fieldname": "raw_material", "fieldtype": "Data", "width": 150},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 150},
        {"label": "Manufacturer", "fieldname": "manufacturer", "fieldtype": "Data", "width": 150},
        {"label": "Submitted Date", "fieldname": "creation", "fieldtype": "Date", "width": 100},
        {"label": "Status", "fieldname": "workflow_state", "fieldtype": "Data", "width": 100}
    ]

    # Fetch query data based on the current user
    data = get_all_queries(filters)

    return columns, data

def get_all_queries(filters):
    # Fetch all queries submitted by users and not in "Draft" or "Delisted" states
    query_data = frappe.db.sql("""
        SELECT
            owner, name, raw_material, supplier, manufacturer, query_types, workflow_state, creation
        FROM `tabQuery`
        WHERE workflow_state NOT IN ('Draft', 'Delisted', 'Rejected', 'Submitted', 'Haram')
    """, as_dict=True)

    return query_data