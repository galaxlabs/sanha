"""
Clone all Query records from DIVINE FOOD HUB → NS Trade International.
Reassigns: client_name, client_code, owner.
Uses raw SQL inserts to bypass business-logic validators that are
not relevant for a data-migration context (e.g. enforce_client_from_owner).
Run with:
    bench --site evaluation.sanha.org.pk execute sanha.scripts.clone_divine_to_nstrade.run
"""
import frappe
from frappe.utils import now_datetime, generate_hash


SOURCE_CLIENT_NAME = "DIVINE FOOD HUB"
TARGET_CLIENT_NAME = "NS Trade International"
TARGET_CLIENT_CODE = "K-0082"
TARGET_OWNER       = "talha.habib@dulzer.ae"

# Fields to copy verbatim from source (excluding identity/meta fields)
COPY_FIELDS = [
    "query_types", "raw_material", "supplier", "supplier_contact",
    "manufacturer", "manufacturer_contact", "workflow_state",
    "is_duplicate", "is_master", "can_delete",
    "duplicate_group_key", "notify_client",
]


def run(**kwargs):
    _clone()
    frappe.db.commit()
    print("Done – all queries cloned and committed.")
    _provision_ns_trade()


def _clone():
    source_queries = frappe.db.get_all(
        "Query",
        filters={"client_name": SOURCE_CLIENT_NAME},
        fields=COPY_FIELDS,
        limit_page_length=0,
        ignore_permissions=True,
    )

    if not source_queries:
        print(f"No queries found for '{SOURCE_CLIENT_NAME}'. Aborting.")
        return

    print(f"Found {len(source_queries)} queries for '{SOURCE_CLIENT_NAME}'."
          f" Cloning to '{TARGET_CLIENT_NAME}'…")

    now = now_datetime()
    count = 0

    for src in source_queries:
        # Generate a unique name in the same Query-XXXXXXXXXX format
        new_name = frappe.model.naming.make_autoname("Query-.########")

        row = {
            "name":           new_name,
            "creation":       now,
            "modified":       now,
            "modified_by":    TARGET_OWNER,
            "owner":          TARGET_OWNER,
            "docstatus":      0,
            "idx":            0,
            "client_name":    TARGET_CLIENT_NAME,
            "client_code":    TARGET_CLIENT_CODE,
        }
        for f in COPY_FIELDS:
            row[f] = src.get(f)

        # Raw INSERT – bypasses all validate/before_save hooks
        cols   = ", ".join(f"`{c}`" for c in row)
        placeholders = ", ".join(["%s"] * len(row))
        frappe.db.sql(
            f"INSERT INTO `tabQuery` ({cols}) VALUES ({placeholders})",
            list(row.values()),
        )
        count += 1

    frappe.db.commit()
    print(f"Successfully cloned {count} queries → '{TARGET_CLIENT_NAME}'"
          f" (owner: {TARGET_OWNER}).")


def _provision_ns_trade():
    """Re-save NS Trade International client to trigger provision_access()."""
    try:
        client = frappe.get_doc("Client", TARGET_CLIENT_NAME)
        client.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"Provision access applied for '{TARGET_CLIENT_NAME}'.")
    except Exception as e:
        print(f"Warning: could not re-save client doc: {e}")
