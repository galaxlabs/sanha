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
    columns = [
        {"fieldname": "query_name", "label": "Query", "fieldtype": "Link", "options": "Query", "width": 160},
        {"fieldname": "raw_material", "label": "Raw Material", "fieldtype": "Data", "width": 180},
        {"fieldname": "missing_fields", "label": "Missing Fields", "fieldtype": "Data", "width": 180},
        {"fieldname": "supplier", "label": "Supplier", "fieldtype": "Data", "width": 160},
        {"fieldname": "manufacturer", "label": "Manufacturer", "fieldtype": "Data", "width": 160},
        {"fieldname": "client_name", "label": "Client", "fieldtype": "Data", "width": 160},
        {"fieldname": "owner", "label": "Owner", "fieldtype": "Data", "width": 180},
        {"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 120},
        {"fieldname": "creation", "label": "Created", "fieldtype": "Datetime", "width": 150},
    ]

    scope_condition, params = get_scope_condition()
    data = frappe.db.sql(f"""
        SELECT
            q.name AS query_name,
            q.raw_material,
            CONCAT_WS(', ',
                IF(IFNULL(TRIM(q.supplier), '') = '', 'Supplier', NULL),
                IF(IFNULL(TRIM(q.manufacturer), '') = '', 'Manufacturer', NULL)
            ) AS missing_fields,
            q.supplier,
            q.manufacturer,
            q.client_name,
            q.owner,
            q.workflow_state AS status,
            q.creation
        FROM `tabQuery` q
        WHERE q.docstatus < 2
          AND q.workflow_state <> 'Delisted'
          AND (IFNULL(TRIM(q.supplier), '') = '' OR IFNULL(TRIM(q.manufacturer), '') = '')
          {scope_condition}
        ORDER BY q.modified DESC
    """, params, as_dict=True)

    return columns, data
