# Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt
import frappe

def execute(filters=None):
    columns, data = [], []
    columns = [
        {"fieldname": "raw_material", "label": "Raw Material", "fieldtype": "Data", "width": 200},
        {"fieldname": "supplier", "label": "Supplier", "fieldtype": "Data", "width": 150},
        {"fieldname": "manufacturer", "label": "Manufacturer", "fieldtype": "Data", "width": 150},
        {"fieldname": "creation_count", "label": "Creation Count", "fieldtype": "Int", "width": 100}
        # {"label": "Status", "fieldname": "workflow_state", "fieldtype": "Data", "width": 100}
    ]

    data = frappe.db.sql("""
        SELECT
            q.raw_material AS raw_material,
            q.supplier AS supplier,
            q.manufacturer AS manufacturer,
            COUNT(DISTINCT q.name) AS creation_count,
            q.workflow_state AS workflow_state
        FROM
            `tabQuery` q
        WHERE
            q.workflow_state NOT IN ('Draft', 'Delisted')
        GROUP BY
            q.raw_material, q.supplier, q.manufacturer, q.workflow_state
    """, as_dict=True)

    return columns, data


# import frappe

# def execute(filters=None):
#     columns, data = [], []
#     columns = [
#         {"fieldname": "raw_material", "label": "Raw Material", "fieldtype": "Data", "width": 200},
#         {"fieldname": "supplier", "label": "Supplier", "fieldtype": "Data", "width": 150},
#         {"fieldname": "manufacturer", "label": "Manufacturer", "fieldtype": "Data", "width": 150},
#         {"fieldname": "owner", "label": "Owner", "fieldtype": "Data", "width": 150},
#         {"fieldname": "creation_count", "label": "Creation Count", "fieldtype": "Int", "width": 100}
#     ]

#     data = frappe.db.sql("""
#         SELECT
#             q.raw_material AS raw_material,
#             q.supplier AS supplier,
#             q.manufacturer AS manufacturer,
#             q.owner AS owner,
#             COUNT(q.name) AS creation_count
#         FROM
#             `tabQuery` q
#         GROUP BY
#             q.raw_material, q.supplier, q.manufacturer, q.owner
#         HAVING
#             COUNT(q.name) > 1
#     """, as_dict=True)

#     return columns, data
