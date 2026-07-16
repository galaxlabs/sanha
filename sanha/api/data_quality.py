import frappe
from frappe import _
from difflib import SequenceMatcher

def _get_user_filters():
    user = frappe.session.user
    roles = frappe.get_roles(user)
    if "System Manager" in roles or "Administrator" in roles:
        return {}
    client_name = frappe.db.get_value("Client", {"owner": user}, "client_name")
    if client_name:
        return {"client_name": client_name}
    return {"owner": user}

def _similarity(a, b):
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def _build_groups(items, threshold=0.6):
    checked = set()
    groups = []
    for i, item in enumerate(items):
        if i in checked:
            continue
        group = [item]
        checked.add(i)
        for j in range(i + 1, len(items)):
            if j in checked:
                continue
            if _similarity(item, items[j]) >= threshold:
                group.append(items[j])
                checked.add(j)
        if len(group) > 1:
            groups.append(group)
    return groups

@frappe.whitelist()
def analyze(scope="all"):
    filters = _get_user_filters()
    fields = ["supplier", "manufacturer", "raw_material", "manufacturer_contact", "supplier_contact"]
    queries = frappe.get_all("Query", filters=filters, fields=fields, limit=10000)

    suppliers, manufacturers, materials = {}, {}, {}
    contact_map = {}

    for q in queries:
        s = q.supplier
        m = q.manufacturer
        r = q.raw_material
        mc = q.manufacturer_contact
        sc = q.supplier_contact

        if s:
            suppliers.setdefault(s.lower().strip(), set()).add(s)
        if m:
            manufacturers.setdefault(m.lower().strip(), set()).add(m)
        if r:
            materials.setdefault(r.lower().strip(), set()).add(r)
        if mc and m:
            contact_map.setdefault(mc.strip().lower(), set()).add(m)
        if sc and s:
            contact_map.setdefault(sc.strip().lower(), set()).add(s)

    result = {}

    if scope in ("all", "supplier"):
        distinct = sorted(set(v.pop() for v in suppliers.values()))
        result["similar_suppliers"] = _build_groups(distinct, 0.55)

    if scope in ("all", "manufacturer"):
        distinct = sorted(set(v.pop() for v in manufacturers.values()))
        result["similar_manufacturers"] = _build_groups(distinct, 0.55)

    if scope in ("all", "raw_material"):
        distinct = sorted(set(v.pop() for v in materials.values()))
        result["similar_raw_materials"] = _build_groups(distinct, 0.65)

    result["same_contact_different_names"] = [
        {"contact": contact, "names": sorted(names)}
        for contact, names in contact_map.items()
        if len(names) > 1
    ]

    result["total_queries_analyzed"] = len(queries)
    return result
