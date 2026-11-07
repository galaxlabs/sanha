"""Persistent current-Query-only analysis, protected by staff and File permissions."""
import hashlib
import json

import frappe
from frappe.utils import cint, get_datetime, now_datetime, today
from sanha.api import staff_review
from sanha.api.ai_providers import ready_profiles, routing_signature, budget_signature


def review_config():
    return frappe.get_single("AI Agent Config")


def auto_enabled():
    if not frappe.get_meta("AI Agent Config").has_field("auto_staff_review"):
        return False
    return bool(cint(frappe.db.get_single_value("AI Agent Config", "auto_staff_review")))


def file_facts(doc):
    """Validate shared result access using metadata only, never file bytes."""
    facts = []
    for row in doc.documents or []:
        files = frappe.get_all("File", filters={"file_url": row.attachment or "", "is_folder": 0}, fields=["name", "content_hash", "file_size", "modified"], order_by="name asc", limit_page_length=0)
        if files and not any(frappe.has_permission("File", "read", doc=frappe.get_doc("File", item.name)) for item in files):
            frappe.throw("One or more current Query attachments are not accessible.", frappe.PermissionError)
        facts.append({"row": row.name, "type": row.documents, "issue": row.issue_date, "expiry": row.expiry_date, "url": row.attachment, "files": files})
    return facts


def fingerprint(doc, config, facts=None):
    from sanha.api.decision_support import final_decisions
    decisions, count = final_decisions(doc.raw_material, doc.manufacturer, doc.supplier, doc.name)
    reference_facts = [{k: r[k] for k in ("name", "modified", "workflow_state", "match_basis", "same_entities")} for r in decisions[:10]]
    payload = {"revision": "material-assessment-v6-word", "decisions": reference_facts, "decision_count": count, "query": {field: doc.get(field) for field in ("name", "raw_material", "query_types", "supplier", "manufacturer")}, "documents": file_facts(doc) if facts is None else facts, "clauses": config.get("review_clauses"), "terms": config.get("review_terms"), "routes": routing_signature()}
    return hashlib.sha256(json.dumps(payload, default=str, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def public_result(record):
    parsed = json.loads(record.result_json or "{}")
    parsed["sources"] = [{field: source.get(field) for field in ("id", "query", "document", "page", "locator", "url", "extraction")} for source in parsed.get("sources", [])]
    parsed["similar"] = []
    parsed["research_sources"] = [{field: source.get(field) for field in ("id", "kind", "query", "title", "url", "retrieved_at", "scope")} for source in parsed.get("research_sources", [])]
    parsed["summaries"] = parsed.get("summaries", [])[:1]
    return parsed


@frappe.whitelist()
def latest(query):
    doc = staff_review.check_query(query)
    if doc.workflow_state == "Delisted":
        return {"query": query, "current_state": doc.workflow_state, "status": "not_applicable", "auto_enabled": False}
    config = review_config()
    key = fingerprint(doc, config)
    name = frappe.db.exists("AI Query Review", key)
    result = {"fingerprint": key, "request_key": key, "query": query, "current_material": doc.raw_material, "current_state": doc.workflow_state, "auto_enabled": auto_enabled(), "providers_ready": bool(ready_profiles("review")), "status": "missing"}
    if name:
        record = frappe.get_doc("AI Query Review", name)
        result.update(status=record.status.lower(), error=record.error)
        if record.status in {"Complete", "Unavailable"}:
            result["review"] = public_result(record)
        expired_worker = record.status in {"Working", "Queued"} and (now_datetime() - get_datetime(record.modified)).total_seconds() > 660
        retryable = record.status in {"Unavailable", "Failed"} and (str(record.attempt_date) != today() or record.budget_signature != budget_signature())
        if expired_worker or retryable:
            result["status"] = "retry_available"
            result["request_key"] = key + ":" + today() + ":" + budget_signature()
    elif not result["providers_ready"]:
        result["status"] = "needs_configuration"
    return result


@frappe.whitelist(methods=["POST"])
def ensure(query, retry=0):
    doc = staff_review.check_query(query)
    if doc.workflow_state == "Delisted": return {"status": "not_applicable"}
    key = fingerprint(doc, review_config())
    if not auto_enabled(): return {"status": "auto_disabled"}
    if not ready_profiles("review"): return {"status": "needs_configuration"}
    if cint(retry) and frappe.db.exists("AI Query Review", key):
        saved = frappe.get_doc("AI Query Review", key)
        if saved.status in {"Failed", "Unavailable"}:
            frappe.db.set_value("AI Query Review", key, {"status": "Queued", "error": ""})
    frappe.enqueue("sanha.api.review_cache.run", query=query, reviewer=frappe.session.user, queue="long", timeout=600, enqueue_after_commit=True)
    return {"status": "queued"}


def schedule_review(doc, method=None):
    try:
        if (doc.workflow_state or "Draft") in {"Draft", "Delisted"} or not auto_enabled() or not ready_profiles("review"):
            return
        name = doc.name
        frappe.db.after_commit.add(lambda: safe_enqueue(name))
    except Exception:
        # AI availability must never block a valid business document save.
        schedule_error("Summary scheduling unavailable; review can be retried from staff view.")


def schedule_error(message):
    try:
        frappe.log_error(message, "Staff AI scheduling")
    except Exception:
        pass


def safe_enqueue(query):
    try:
        frappe.enqueue("sanha.api.review_cache.run", query=query, queue="long", timeout=600)
    except Exception:
        schedule_error("Summary queue unavailable after Query commit.")


def run(query, reviewer=None):
    original = frappe.session.user
    record = None
    try:
        frappe.set_user(reviewer or "Administrator")
        doc = staff_review.check_query(query)
        if doc.workflow_state == "Delisted": return
        config = review_config()
        if not auto_enabled() or not ready_profiles("review"): return
        key = fingerprint(doc, config)
        existing = frappe.db.exists("AI Query Review", key)
        if existing:
            record = frappe.get_doc("AI Query Review", existing)
            if record.status == "Complete": return
            if record.status == "Working" and (now_datetime() - get_datetime(record.modified)).total_seconds() < 660: return
            if record.status in {"Unavailable", "Failed"} and str(record.attempt_date) == today() and record.budget_signature == budget_signature(): return
        else:
            record = frappe.get_doc({"doctype": "AI Query Review", "fingerprint": key, "query": query, "query_version": str(doc.modified), "status": "Queued", "requested_by": original})
            try:
                record.insert(ignore_permissions=True); frappe.db.commit()
            except frappe.DuplicateEntryError:
                frappe.db.rollback(); return
        locked = frappe.db.sql("SELECT status, modified FROM `tabAI Query Review` WHERE name=%s FOR UPDATE", (record.name,), as_dict=True)[0]
        if locked.status == "Complete" or (locked.status == "Working" and (now_datetime() - get_datetime(locked.modified)).total_seconds() < 660):
            frappe.db.rollback(); return
        record.status = "Working"; record.attempt_date = today(); record.attempts = cint(record.attempts) + 1; record.error = ""; record.budget_signature = budget_signature()
        record.save(ignore_permissions=True); frappe.db.commit()
        result = staff_review.collect_review(doc, config)
        record.status = "Complete" if result.get("ai_status") == "complete" else "Unavailable"
        record.result_json = json.dumps(result, default=str, ensure_ascii=False)
        record.error = "" if record.status == "Complete" else "No valid cited summary generated. Check connection, budget and readable current documents."
        if result.get("provider_failure_reason"):
            record.error = "AI provider: " + result["provider_failure_reason"][:300]
        elif result.get("ai_status") == "partial_cited_output":
            record.error = "Analysis is incomplete: some required sections/questions could not be cited. Available evidence is retained."
        record.save(ignore_permissions=True); frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        if record and frappe.db.exists("AI Query Review", record.name):
            frappe.db.set_value("AI Query Review", record.name, {"status": "Failed", "error": "Review failed. Check attachment access and provider settings.", "attempt_date": today()})
            frappe.db.commit()
    finally:
        frappe.set_user(original)


@frappe.whitelist()
def related(query):
    doc = staff_review.check_query(query)
    rows, count, _ = staff_review.similar_queries(doc, [], False)
    return {"rows": rows, "total": count, "historical_file_reads": 0}
