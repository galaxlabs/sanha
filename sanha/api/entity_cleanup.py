"""Ten distinct Queries/day, researched before mutation; no workflow changes."""
import hashlib
import json
import re
from collections import defaultdict, deque

import frappe
from frappe.utils import cint, today

from sanha.api.decision_support import company_key, real_company, text_key
from sanha.api.public_references import resolve_company, registry_candidates

DAILY_LIMIT = 10
ENTITY_FIELDS = ("manufacturer", "supplier")
TO_BE_ADDED = {"tobeadded", "tobeadedd"}
SAME_AS_MANUFACTURER = {"sameasmanufacturer", "sameasmanufactur", "sameasmanufacture"}


def matched_material_text(material, texts):
    expected = text_key(material)
    if not expected:
        return ""
    matching = []
    for text in texts:
        labels = re.findall(r"(?:product(?: name)?|material(?: name)?|chemical(?: name)?|trade name|raw material)\s*[:\-]\s*([^\n]{2,200})", text, re.I)
        if any(text_key(label) == expected for label in labels):
            matching.append(text)
    return "\n".join(matching)


def _placeholder_updates(row, changes, evidence, reasons, text):
    # The user's earlier exact rules remain in force under the new ten-row cap.
    # A to-be-added marker NEVER licenses extracting/overwriting Supplier.
    if company_key(row.get("manufacturer")) in TO_BE_ADDED:
        product_text = matched_material_text(row.get("raw_material"), [text])
        labels = re.findall(r"(?:manufacturer|manufactured by)\s*[:\-]\s*([^\n]{2,140})", product_text, re.I)
        resolved_names = {}
        for label in labels[:5]:
            resolved, _ = resolve_company(label.strip(), document_text=text, role="manufacturer")
            if resolved:
                resolved_names[resolved["identity_key"]] = resolved
        if len(resolved_names) == 1:
            resolved = next(iter(resolved_names.values()))
            changes["manufacturer"] = resolved["canonical_name"]
            evidence["manufacturer"] = resolved
            reasons["manufacturer"] = "manufacturer_label_and_public_identity"
    for field, other, markers in (("manufacturer", "supplier", {"sameassupplier"}),
                                   ("supplier", "manufacturer", SAME_AS_MANUFACTURER)):
        if company_key(row.get(field)) not in markers:
            continue
        source = changes.get(other, row.get(other))
        if real_company(source):
            changes[field] = source
            evidence[field] = {"canonical_name": source, "identity_key": "EXPLICIT:" + company_key(source),
                               "source_url": "/app/query/" + row["name"], "kind": "explicit_same_as", "source_field": other,
                               "excerpt": "Original marker explicitly requests copying the actual " + other + " field."}
            reasons[field] = "explicit_same_as_marker; copied actual counterpart only"


def require_admin():
    from sanha.api.staff_review import require_admin as check
    check()


def settings_enabled():
    return (frappe.db.exists("DocType", "Entity Cleanup Settings")
            and cint(frappe.db.get_single_value("Entity Cleanup Settings", "enabled")))


def diverse_candidates(rows, previous, already_today, limit=DAILY_LIMIT):
    """Rotate oldest/unattempted records, then round-robin material/type families."""
    cohorts = defaultdict(list)
    rows = sorted(rows, key=lambda r: (str(previous.get(r["name"], "")), r["name"]))
    for row in rows:
        eligible = (any(real_company(row.get(field)) for field in ENTITY_FIELDS)
                    or company_key(row.get("manufacturer")) in TO_BE_ADDED | {"sameassupplier"}
                    or company_key(row.get("supplier")) in SAME_AS_MANUFACTURER)
        if row["name"] in already_today or not eligible:
            continue
        cohorts[str(previous.get(row["name"], ""))].append(row)
    selected = []
    maximum = min(max(0, int(limit)), DAILY_LIMIT)
    for epoch in sorted(cohorts):
        buckets = defaultdict(deque)
        for row in cohorts[epoch]:
            buckets[(text_key(row.get("raw_material")), row.get("query_types") or "")].append(row)
        while buckets and len(selected) < maximum:
            for key in list(buckets):
                selected.append(buckets[key].popleft())
                if not buckets[key]:
                    del buckets[key]
                if len(selected) == maximum:
                    break
        if len(selected) == maximum:
            break
    return selected


def candidates(limit=DAILY_LIMIT, run_date=None):
    rows = frappe.get_all("Query", fields=["name", "raw_material", "query_types", "manufacturer", "supplier", "manufacturer_contact", "supplier_contact", "modified", "workflow_state"],
                          filters={"docstatus": ["<", 2]}, limit_page_length=0)
    history = frappe.db.sql("SELECT query,MAX(run_date) last_date FROM `tabEntity Correction Log` GROUP BY query", as_dict=True)
    already = frappe.get_all("Entity Correction Log", filters={"run_date": run_date or today()}, pluck="query", limit_page_length=0)
    return diverse_candidates(rows, {r.query: r.last_date for r in history}, set(already), limit)


def proposal(row):
    # Read only THIS selected Query's native cached text; no other Query files.
    from sanha.api.staff_review import read_documents
    doc = frappe.get_doc("Query", row["name"])
    from sanha.api.review_cache import file_facts
    document_facts = file_facts(doc)
    # One NEW vision transcription per selected Query; existing extraction is
    # reused. Enabled provider daily budgets remain an independent hard limit.
    _, sources, _, _ = read_documents(doc, config=frappe.get_single("AI Agent Config"), vision_budget=1)
    # Wrong uploaded documents are not blocked. They also must not silently
    # rename this product's manufacturer: identity anchors need its own label.
    text = matched_material_text(row.get("raw_material"), [source["text"] for source in sources])[:60000]
    changes, evidence, reasons = {}, {}, {}
    for field in ENTITY_FIELDS:
        original = row.get(field)
        # Previous to-be-added extraction rule is separate: never fill Supplier
        # from that marker or equate independent companies in this name cleanup.
        if not real_company(original):
            reasons[field] = "placeholder_or_unknown; no name invented"
            continue
        resolved, reason = resolve_company(original, row.get(field + "_contact", ""), text, role=field)
        reasons[field] = reason
        if not resolved:
            try:
                suggestions = registry_candidates(original)
                if suggestions:
                    reasons[field] += "; unverified candidate: " + suggestions[0]["canonical_name"]
            except Exception:
                pass
        if resolved:
            evidence[field] = resolved
            if original != resolved["canonical_name"]:
                changes[field] = resolved["canonical_name"]
    _placeholder_updates(row, changes, evidence, reasons, text)
    return {"query": row["name"], "changes": changes, "evidence": evidence, "reasons": reasons, "document_facts": document_facts}


def _remember_alias(original, resolved, material):
    normalized = company_key(original)
    context = "" if company_key(original) == company_key(resolved["canonical_name"]) or "sugar" in original.casefold() else text_key(material)
    existing = frappe.db.exists("Entity Name Alias", {"normalized_name": normalized, "identity_key": resolved["identity_key"], "material_context": context})
    if not existing:
        frappe.get_doc({"doctype": "Entity Name Alias", "original_name": original, "canonical_name": resolved["canonical_name"],
                        "identity_key": resolved["identity_key"], "material_context": context, "source_url": resolved["source_url"],
                        "evidence_json": json.dumps(resolved, ensure_ascii=False), "verified": 1}).insert(ignore_permissions=True)


def apply_proposal(row, result, log):
    """Compare-and-set only identity fields; preserve decisions, files and saves."""
    require_admin()
    if log.get("run_date") and str(log.run_date) != today():
        log.status = "Conflict"
        log.reason = "Research crossed the daily boundary; no Query fields changed."
        return
    locked = frappe.db.sql("SELECT name,raw_material,modified,workflow_state,manufacturer,supplier FROM tabQuery WHERE name=%s FOR UPDATE", (row["name"],), as_dict=True)
    if not locked or any(str(locked[0].get(field) or "") != str(row.get(field) or "") for field in ("modified", "raw_material", "workflow_state", *ENTITY_FIELDS)):
        log.status = "Conflict"
        log.reason = "Query changed during public research; no field was overwritten."
        return
    if "document_facts" in result:
        from sanha.api.review_cache import file_facts
        current_facts = file_facts(frappe.get_doc("Query", row["name"]))
        if json.dumps(current_facts, default=str, sort_keys=True) != json.dumps(result["document_facts"], default=str, sort_keys=True):
            log.status = "Conflict"
            log.reason = "Current document metadata changed during research; no company field overwritten."
            return
    changes = result["changes"]
    if set(changes) - set(ENTITY_FIELDS) or any(not real_company(value) for value in changes.values()):
        raise ValueError("Only real supplier/manufacturer identities can be corrected.")
    for field, value in changes.items():
        resolved = result["evidence"].get(field)
        if not resolved or value != resolved["canonical_name"] or not resolved.get("identity_key") or not resolved.get("source_url"):
            raise ValueError("Correction has no verified identity evidence.")
        if resolved.get("kind") == "explicit_same_as":
            other = resolved.get("source_field")
            valid_marker = company_key(row.get(field)) in ({"sameassupplier"} if field == "manufacturer" else SAME_AS_MANUFACTURER)
            if other not in ENTITY_FIELDS or other == field or not valid_marker or value != changes.get(other, locked[0].get(other)):
                raise ValueError("Same-as correction does not match the explicit marker and current counterpart.")
    if not changes:
        log.status = "Unchanged" if all(real_company(row.get(field)) and field in result["evidence"] for field in ENTITY_FIELDS) else "Unresolved"
        return
    # Frappe adds modified/modified_by to the supplied dict; do not contaminate
    # the approved entity-only proposal or its audit diff with those mutations.
    frappe.db.set_value("Query", row["name"], dict(changes))
    changed = [[field, row.get(field), value] for field, value in changes.items()]
    frappe.get_doc({"doctype": "Version", "ref_doctype": "Query", "docname": row["name"],
                    "data": json.dumps({"changed": changed, "added": [], "removed": [], "row_changed": [],
                                        "entity_correction": log.name})}).insert(ignore_permissions=True)
    for field in changes:
        if real_company(row[field]):
            _remember_alias(row[field], result["evidence"][field], row["raw_material"])
    frappe.get_doc({"doctype": "Comment", "comment_type": "Info", "reference_doctype": "Query", "reference_name": row["name"],
                    "content": "Evidence-based company-field correction or explicit same-as rule; workflow and documents unchanged. Audit: " + frappe.utils.escape_html(log.name)}).insert(ignore_permissions=True)
    log.status = "Corrected"


def enqueue_daily():
    if settings_enabled():
        frappe.enqueue("sanha.api.entity_cleanup.run_daily", queue="long", timeout=1800)


def run_daily():
    if not settings_enabled():
        return {"enabled": False, "processed": 0}
    original = frappe.session.user
    run_date = today()
    lock = "entity-cleanup:" + hashlib.sha256((frappe.local.site + run_date).encode()).hexdigest()[:35]
    frappe.db.commit()
    if frappe.db.sql("SELECT GET_LOCK(%s,0)", (lock,))[0][0] != 1:
        return {"busy": True, "processed": 0}
    results = []
    try:
        frappe.set_user("Administrator")
        used = frappe.db.count("Entity Correction Log", {"run_date": run_date})
        for row in candidates(max(0, DAILY_LIMIT - used), run_date=run_date) if used < DAILY_LIMIT else []:
            if today() != run_date:
                break
            key = hashlib.sha256((run_date + ":" + row.name).encode()).hexdigest()
            log = frappe.get_doc({"doctype": "Entity Correction Log", "request_key": key, "run_date": run_date, "query": row.name,
                                  "raw_material": row.raw_material, "status": "Reserved", "before_json": json.dumps(row, default=str, ensure_ascii=False)})
            try:
                log.insert(ignore_permissions=True)
                frappe.db.commit()  # Durable quota reservation BEFORE any research.
                result = proposal(row)
                frappe.db.commit()  # End research read snapshot before compare-and-set.
                log.evidence_json = json.dumps(result, default=str, ensure_ascii=False)
                log.after_json = json.dumps(result["changes"], ensure_ascii=False)
                log.reason = json.dumps(result["reasons"], ensure_ascii=False)[:1000]
                apply_proposal(row, result, log)
                log.save(ignore_permissions=True)
                frappe.db.commit()
                results.append({"query": row.name, "status": log.status})
            except Exception:
                frappe.db.rollback()
                if frappe.db.exists("Entity Correction Log", key):
                    frappe.db.set_value("Entity Correction Log", key, {"status": "Failed", "reason": "Research/correction failed; no uncommitted Query edits retained."})
                    frappe.db.commit()
                results.append({"query": row.name, "status": "Failed"})
        return {"processed": len(results), "daily_limit": DAILY_LIMIT, "results": results}
    finally:
        frappe.db.sql("SELECT RELEASE_LOCK(%s)", (lock,))
        frappe.set_user(original)


@frappe.whitelist()
def status():
    require_admin()
    return {"enabled": bool(settings_enabled()), "daily_limit": DAILY_LIMIT,
            "today": frappe.get_all("Entity Correction Log", filters={"run_date": today()}, fields=["query", "raw_material", "status", "reason"], limit_page_length=DAILY_LIMIT)}


@frappe.whitelist(methods=["POST"])
def set_enabled(enabled=0):
    require_admin()
    doc = frappe.get_single("Entity Cleanup Settings")
    doc.enabled = 1 if cint(enabled) else 0
    doc.save(ignore_permissions=True)
    return status()
