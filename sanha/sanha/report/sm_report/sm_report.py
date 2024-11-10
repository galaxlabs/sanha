# sm_report.py

import frappe
from frappe import _

def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Serial No"), "fieldname": "serial_no", "fieldtype": "Data", "width": 50},
        {"label": _("Raw Material"), "fieldname": "raw_material", "fieldtype": "Data", "width": 150},
        {"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Data", "width": 150},
        {"label": _("Manufacturer"), "fieldname": "manufacturer", "fieldtype": "Data", "width": 150},
        {"label": _("Query Status"), "fieldname": "workflow_state", "fieldtype": "Data", "width": 150},
    ]

def get_data(filters):
    query = """
        SELECT 
            ROW_NUMBER() OVER() as serial_no,
            raw_material,
            supplier,
            manufacturer,
            workflow_state AS query_status
        FROM
            `tabQuery Doctype`
        WHERE 
            workflow_state != 'Draft'
        ORDER BY 
            raw_material ASC
    """
    data = frappe.db.sql(query, as_dict=True)
    return data
