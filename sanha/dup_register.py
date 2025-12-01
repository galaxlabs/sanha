import frappe
import hashlib
from frappe.utils import now_datetime


# ----------------------------
# Helpers
# ----------------------------
def _norm(s: str) -> str:
    return (s or "").strip().lower()


def make_key(raw_material, client_name, supplier, manufacturer) -> str:
    raw = "||".join([
        _norm(raw_material),
        _norm(client_name),
        _norm(supplier),
        _norm(manufacturer),
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _has_workflow_state() -> bool:
    return frappe.db.has_column("Query", "workflow_state")


def _wf_value(row: dict, has_wf: bool) -> str:
    """Return workflow_state; treat empty/missing as Draft."""
    if not has_wf:
        return "Draft"
    ws = (row.get("workflow_state") or "").strip()
    return ws or "Draft"


def _prune_missing_query_links(reg_doc):
    """Remove child rows whose Query link no longer exists (prevents LinkValidationError)."""
    kept = []
    for r in (reg_doc.get("items") or []):
        q = getattr(r, "query", None)
        if q and frappe.db.exists("Query", q):
            kept.append({
                "query": q,
                "query_creation": getattr(r, "query_creation", None),
                "query_workflow_state": getattr(r, "query_workflow_state", "") or "",
                "is_master": 1 if getattr(r, "is_master", 0) else 0,
                "can_delete": 1 if getattr(r, "can_delete", 0) else 0,
                "mark_for_delete": 1 if getattr(r, "mark_for_delete", 0) else 0,
            })
    reg_doc.set("items", kept)


def _sync_totals_from_items(reg_doc):
    """Update total_records and total_draft_records based on child rows."""
    items = reg_doc.items or []
    reg_doc.total_records = len(items)
    reg_doc.total_draft_records = sum(
        1 for i in items
        if (getattr(i, "query_workflow_state", "") or "") == "Draft"
    )


# ----------------------------
# Core scan logic
# ----------------------------
def scan_and_sync():
    """
    Duplicate group (EXACT match, normalized):
      raw_material + client_name + supplier + manufacturer

    Rules:
    - If ANY non-Draft exists in group:
        master = oldest non-Draft
        auto mark_for_delete=1 for Draft duplicates (non-master) only
    - If ALL Draft:
        master = oldest overall
        mark_for_delete=0 (so you will NOT delete rest of drafts)
    """
    has_wf = _has_workflow_state()
    wf_select = ", workflow_state" if has_wf else ""

    # 1) find duplicate groups
    groups = frappe.db.sql("""
        SELECT
          LOWER(TRIM(IFNULL(raw_material,''))) rm,
          LOWER(TRIM(IFNULL(client_name,''))) cn,
          LOWER(TRIM(IFNULL(supplier,''))) sp,
          LOWER(TRIM(IFNULL(manufacturer,''))) mf,
          COUNT(*) cnt
        FROM `tabQuery`
        GROUP BY rm, cn, sp, mf
        HAVING cnt > 1
    """, as_dict=True)

    active_keys = set()

    # 2) create/update registers for current duplicates
    for g in groups:
        key = make_key(g.rm, g.cn, g.sp, g.mf)
        active_keys.add(key)

        # fetch all members in this group, oldest first
        members = frappe.db.sql(f"""
            SELECT
              name, creation,
              raw_material, client_name, supplier, manufacturer
              {wf_select}
            FROM `tabQuery`
            WHERE LOWER(TRIM(IFNULL(raw_material,'')))=%s
              AND LOWER(TRIM(IFNULL(client_name,'')))=%s
              AND LOWER(TRIM(IFNULL(supplier,'')))=%s
              AND LOWER(TRIM(IFNULL(manufacturer,'')))=%s
            ORDER BY creation ASC
        """, (g.rm, g.cn, g.sp, g.mf), as_dict=True)

        # filter out Query docs that were already deleted
        members = [m for m in members if frappe.db.exists("Query", m["name"])]
        if len(members) < 2:
            # no longer duplicate, nothing to build for this group
            continue

        def wf(m):
            return _wf_value(m, has_wf)

        has_non_draft = any(wf(m) != "Draft" for m in members)

        # master selection:
        #   if any non-draft => oldest non-draft
        #   else => oldest overall
        master = None
        if has_non_draft:
            for m in members:
                if wf(m) != "Draft":
                    master = m["name"]
                    break
        if not master:
            master = members[0]["name"]

        # upsert Query Duplicate Register
        reg_name = frappe.db.get_value("Query Duplicate Register", {"duplicate_key": key}, "name")
        reg = frappe.get_doc("Query Duplicate Register", reg_name) if reg_name else frappe.new_doc("Query Duplicate Register")

        # group identity (Data fields on register)
        reg.duplicate_key = key
        reg.raw_material = members[0].get("raw_material")
        reg.client_name = members[0].get("client_name")
        reg.supplier = members[0].get("supplier")
        reg.manufacturer = members[0].get("manufacturer")

        reg.master_query = master
        reg.last_scanned_on = now_datetime()
        reg.status = "Active"

        reg.set("items", [])

        for m in members:
            name = m["name"]
            state = wf(m)

            is_master = (name == master)
            is_draft = (state == "Draft")

            # Draft duplicates (non-master) are deletable
            can_delete = (not is_master) and is_draft

            # Only auto-mark for delete when the group has any non-draft
            mark_for_delete = 1 if (has_non_draft and can_delete) else 0

            reg.append("items", {
                "query": name,
                "query_creation": m.get("creation"),
                "query_workflow_state": state,
                "is_master": 1 if is_master else 0,
                "can_delete": 1 if can_delete else 0,
                "mark_for_delete": mark_for_delete,
            })

        # safety + totals
        _prune_missing_query_links(reg)
        _sync_totals_from_items(reg)
        reg.save(ignore_permissions=True)

    # 3) resolve old registers that are no longer duplicates
    existing_regs = frappe.get_all(
        "Query Duplicate Register",
        filters={"status": "Active"},
        fields=["name", "duplicate_key"],
    )

    for r in existing_regs:
        if r["duplicate_key"] in active_keys:
            # still an active duplicate group this scan
            continue

        # no longer in active_keys => not a duplicate anymore
        doc = frappe.get_doc("Query Duplicate Register", r["name"])
        _prune_missing_query_links(doc)
        doc.status = "Resolved"
        _sync_totals_from_items(doc)
        doc.last_scanned_on = now_datetime()
        doc.save(ignore_permissions=True)

    frappe.db.commit()


# ----------------------------
# Whitelisted methods for UI / API
# ----------------------------
@frappe.whitelist()
def scan_and_sync_ui():
    """Called from UI button."""
    frappe.only_for(("System Manager", "Administrator"))
    scan_and_sync()
    return {"ok": True}


@frappe.whitelist()
def delete_marked(register_name: str):
    """
    Delete Query docs that are:
      - in this register
      - mark_for_delete = 1
      - can_delete = 1
      - NOT the master
      - and (if workflow_state column exists) currently Draft
    """
    frappe.only_for(("System Manager", "Administrator"))

    reg = frappe.get_doc("Query Duplicate Register", register_name)
    reg.check_permission("write")

    has_wf = _has_workflow_state()
    master = reg.master_query
    deleted = []

    for row in reg.items:
        if not row.mark_for_delete:
            continue
        if not row.can_delete:
            continue
        if row.query == master:
            continue
        if not row.query:
            continue
        if not frappe.db.exists("Query", row.query):
            continue

        # Safety: delete only Draft rows if workflow exists
        if has_wf:
            ws = (frappe.db.get_value("Query", row.query, "workflow_state") or "").strip() or "Draft"
            if ws != "Draft":
                continue

        frappe.delete_doc("Query", row.query, force=1)
        deleted.append(row.query)

    frappe.db.commit()

    # After deletion, rebuild all registers (updates totals + resolves if needed)
    scan_and_sync()

    return {"deleted": deleted}
 