import frappe

@frappe.whitelist()
def get_filter_options():
    # Get all client names and query types from the Query doctype
    client_names = set()
    query_types = set()

    all_rows = frappe.get_all(
        "Query",
        fields=["client_name", "query_types"],
        filters={"docstatus": ["<", 2]},
        order_by="client_name asc"
    )

    for row in all_rows:
        if row.client_name:
            client_names.add(row.client_name.strip())

        if row.query_types:
            types = [t.strip() for t in row.query_types.split(',') if t.strip()]
            for t in types:
                query_types.add(t)

    return {
        "clients": sorted(client_names),
        "query_types": sorted(query_types)
    }

# import frappe

# @frappe.whitelist()
# def get_filter_options():
#     user = frappe.session.user
#     client_names = set()
#     query_types = set()

#     rows = frappe.db.get_all(
#         "Query",
#         fields=["client_name", "query_types"],
#         filters={"owner": user, "docstatus": ["<", 2]},
#         order_by="client_name asc"
#     )

#     for row in rows:
#         if row.client_name:
#             client_names.add(row.client_name.strip())
#         if row.query_types:
#             for q in row.query_types.split(','):
#                 q = q.strip()
#                 if q:
#                     query_types.add(q)

#     return {
#         "clients": sorted(client_names),
#         "query_types": sorted(query_types)
#     }

# import frappe

# @frappe.whitelist()
# def get_filter_options():
#     # Get the session user
#     user = frappe.session.user

#     # Use set to avoid duplicates
#     client_names = set()
#     query_types = set()

#     # Query all records created by current user
#     records = frappe.db.get_all(
#         "Query",
#         fields=["client_name", "query_types"],
#         filters={"owner": user, "docstatus": ["<", 2]},
#         order_by="client_name asc"
#     )

#     for row in records:
#         if row.client_name:
#             client_names.add(row.client_name)

#         if row.query_types:
#             for q in row.query_types.split(","):
#                 q = q.strip()
#                 if q:
#                     query_types.add(q)

#     return {
#         "clients": sorted(client_names),
#         "query_types": sorted(query_types)
#     }

