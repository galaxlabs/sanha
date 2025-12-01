import frappe, hashlib
from frappe.utils import now_datetime

def _norm(s):
    return (s or "").strip().lower()

def make_key(raw_material, client_name, supplier, manufacturer):
    raw = "||".join([_norm(raw_material), _norm(client_name), _norm(supplier), _norm(manufacturer)])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()

def scan_and_sync():
    has_wf = frappe.db.has_column("Query", "workflow_state")
    # has_wf = frappe.db.has_column("tabQuery", "workflow_state")

    # 1) find duplicate groups
    groups = frappe.db.sql("""
        SELECT
          LOWER(TRIM(IFNULL(raw_material,''))) rm,
          LOWER(TRIM(IFNULL(client_name,''))) cn,
          LOWER(TRIM(IFNULL(supplier,''))) sp,
          LOWER(TRIM(IFNULL(manufacturer,''))) mf,
          COUNT(*) cnt
        FROM `tabQuery`
        WHERE docstatus < 2
        GROUP BY rm, cn, sp, mf
        HAVING cnt > 1
    """, as_dict=True)

    active_keys = set()

    for g in groups:
        key = make_key(g.rm, g.cn, g.sp, g.mf)
        active_keys.add(key)

        wf_select = ", workflow_state" if has_wf else ""
        wf_field = "workflow_state" if has_wf else None

        # 2) fetch members ordered by oldest (master)
        members = frappe.db.sql(f"""
            SELECT name, creation, docstatus{wf_select},
                   raw_material, client_name, supplier, manufacturer
            FROM `tabQuery`
            WHERE LOWER(TRIM(IFNULL(raw_material,'')))=%s
              AND LOWER(TRIM(IFNULL(client_name,'')))=%s
              AND LOWER(TRIM(IFNULL(supplier,'')))=%s
              AND LOWER(TRIM(IFNULL(manufacturer,'')))=%s
              AND docstatus < 2
            ORDER BY creation ASC
        """, (g.rm, g.cn, g.sp, g.mf), as_dict=True)

        master = members[0]["name"]

        def is_draft(m):
            if m.get("docstatus") != 0:
                return False
            if not wf_field:
                return True
            return (m.get("workflow_state") == "Draft")

        draft_count = sum(1 for m in members if is_draft(m))

        # 3) upsert register
        reg_name = frappe.db.get_value("Query Duplicate Register", {"duplicate_key": key}, "name")
        reg = frappe.get_doc("Query Duplicate Register", reg_name) if reg_name else frappe.new_doc("Query Duplicate Register")

        reg.duplicate_key = key
        reg.raw_material = members[0].get("raw_material")
        reg.client_name = members[0].get("client_name")  # can be empty
        reg.supplier = members[0].get("supplier")
        reg.manufacturer = members[0].get("manufacturer")
        reg.master_query = master
        reg.total_records = len(members)
        reg.total_draft_records = draft_count
        reg.last_scanned_on = now_datetime()
        reg.status = "Active"

        reg.set("items", [])
        for m in members:
            is_master = (m["name"] == master)
            can_delete = (not is_master) and is_draft(m)

            reg.append("items", {
                "query": m["name"],
                "query_creation": m.get("creation"),
                "query_workflow_state": m.get("workflow_state") if has_wf else "",
                "query_docstatus": m.get("docstatus"),
                "is_master": 1 if is_master else 0,
                "can_delete": 1 if can_delete else 0,
                "mark_for_delete": 0,
            })

        reg.save(ignore_permissions=True)

    # 4) resolve old ones
    for r in frappe.get_all("Query Duplicate Register", filters={"status": "Active"}, fields=["name", "duplicate_key"]):
        if r["duplicate_key"] not in active_keys:
            doc = frappe.get_doc("Query Duplicate Register", r["name"])
            doc.status = "Resolved"
            doc.last_scanned_on = now_datetime()
            doc.save(ignore_permissions=True)

    frappe.db.commit()
