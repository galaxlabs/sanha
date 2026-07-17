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
        {"fieldname": "duplicate_key", "label": "Duplicate Key", "fieldtype": "Data", "width": 240},
        {"fieldname": "duplicate_count", "label": "Count", "fieldtype": "Int", "width": 80},
        {"fieldname": "query_name", "label": "Query", "fieldtype": "Link", "options": "Query", "width": 160},
        {"fieldname": "raw_material", "label": "Raw Material", "fieldtype": "Data", "width": 180},
        {"fieldname": "manufacturer", "label": "Manufacturer", "fieldtype": "Data", "width": 160},
        {"fieldname": "supplier", "label": "Supplier", "fieldtype": "Data", "width": 160},
        {"fieldname": "client_name", "label": "Client", "fieldtype": "Data", "width": 160},
        {"fieldname": "owner", "label": "Owner", "fieldtype": "Data", "width": 180},
        {"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 120},
        {"fieldname": "creation", "label": "Created", "fieldtype": "Datetime", "width": 150},
    ]

    scope_condition, params = get_scope_condition()
    data = frappe.db.sql(f"""
        WITH base AS (
            SELECT
                q.name,
                q.raw_material,
                q.manufacturer,
                q.supplier,
                q.client_name,
                q.owner,
                q.workflow_state,
                q.creation,
                LOWER(TRIM(IFNULL(q.raw_material, ''))) AS rm_key,
                LOWER(TRIM(IFNULL(q.manufacturer, ''))) AS mf_key,
                LOWER(TRIM(IFNULL(q.supplier, ''))) AS supplier_key,
                COALESCE(NULLIF(LOWER(TRIM(IFNULL(q.client_name, ''))), ''), CONCAT('owner:', q.owner)) AS scope_key
            FROM `tabQuery` q
            WHERE q.docstatus < 2
              AND q.workflow_state <> 'Delisted'
              AND IFNULL(TRIM(q.raw_material), '') <> ''
              {scope_condition}
        ), dupes AS (
            SELECT rm_key, mf_key, supplier_key, scope_key, COUNT(*) AS duplicate_count
            FROM base
            GROUP BY rm_key, mf_key, supplier_key, scope_key
            HAVING COUNT(*) > 1
        )
        SELECT
            CONCAT_WS(' / ', b.rm_key, NULLIF(b.mf_key, ''), NULLIF(b.supplier_key, ''), b.scope_key) AS duplicate_key,
            d.duplicate_count,
            b.name AS query_name,
            b.raw_material,
            b.manufacturer,
            b.supplier,
            b.client_name,
            b.owner,
            b.workflow_state AS status,
            b.creation
        FROM base b
        JOIN dupes d
          ON d.rm_key = b.rm_key
         AND d.mf_key = b.mf_key
         AND d.supplier_key = b.supplier_key
         AND d.scope_key = b.scope_key
        ORDER BY d.duplicate_count DESC, b.rm_key, b.creation DESC
    """, params, as_dict=True)

    return columns, data
