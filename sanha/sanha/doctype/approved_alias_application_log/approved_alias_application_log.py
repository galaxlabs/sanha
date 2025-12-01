# Copyright (c) 2025, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe.utils import now_datetime


@frappe.whitelist()
def apply_approved_aliases_to_queries():
    rm_aliases = frappe.get_all("Raw Material Alias", fields=["alias", "normalized_key"], filters={"is_preferred": 1})
    mf_aliases = frappe.get_all("Manufacturer Alias", fields=["alias", "normalized_key"], filters={"is_preferred": 1})

    raw_map = {a.alias.lower().strip(): a.normalized_key for a in rm_aliases}
    manu_map = {a.alias.lower().strip(): a.normalized_key for a in mf_aliases}

    queries = frappe.get_all("Query", fields=["name", "raw_material", "manufacturer"])

    for q in queries:
        raw_old, manu_old = q.raw_material or "", q.manufacturer or ""
        raw_new = raw_map.get(raw_old.lower().strip())
        manu_new = manu_map.get(manu_old.lower().strip())

        if raw_new and raw_new != raw_old:
            frappe.db.set_value("Query", q.name, "raw_material", raw_new)
            log_change(q.name, "raw_material", raw_old, raw_new)

        if manu_new and manu_new != manu_old:
            frappe.db.set_value("Query", q.name, "manufacturer", manu_new)
            log_change(q.name, "manufacturer", manu_old, manu_new)

    frappe.db.commit()
    return "Done applying aliases"

def log_change(query_name, field, old, new):
    frappe.get_doc({
        "doctype": "Approved Alias Application Log",
        "query": query_name,
        "field_updated": field,
        "old_value": old,
        "new_value": new,
        "applied_on": now_datetime(),
        "applied_by": frappe.session.user
    }).insert(ignore_permissions=True)


class ApprovedAliasApplicationLog(Document):
	pass
