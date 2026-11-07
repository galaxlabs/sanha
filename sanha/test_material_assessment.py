"""Meaningful decision, missing-document and identity normalization regressions."""
import json
import uuid
from unittest.mock import MagicMock, patch

import frappe

from sanha.api import decision_support as decisions, entity_cleanup as cleanup, public_references as public, staff_review as review
from sanha.api import ai_providers as providers


def run_checks():
    checks = []
    approved = frappe._dict(name="APPROVED", raw_material="Sugar", manufacturer="Al-Noor Sugar Mills Ltd", supplier="Trading Ltd",
                            workflow_state="Approved", modified="2026-01-01", owner="staff", client_name="Client")
    pending = [frappe._dict({**approved, "name": state, "workflow_state": state}) for state in ("Draft", "Submitted", "Submitted to SB", "Under Review", "Hold", "Doubtful", "Delisted", "Returned")]
    with patch.object(frappe, "get_list", return_value=[approved, *pending]) as listing, patch.object(decisions, "alias_index", return_value={}):
        matches, count = decisions.final_decisions("Sugar", "Al Noor Sugar Mills Limited", "Trading Ltd", require_manufacturer=True)
        assert count == 1 and matches[0]["name"] == "APPROVED" and matches[0]["same_manufacturer"]
        assert ["workflow_state", "in", list(decisions.FINAL_STATES)] in listing.call_args.kwargs["filters"]
        assert listing.call_args.kwargs["limit_page_length"] == 0
    checks.append("only final decisions; pending/Draft excluded at DB and defensive result layer")
    checks.append("same material and manufacturer punctuation/legal-suffix spelling match")
    with patch.object(frappe, "get_list", return_value=[approved]), patch.object(decisions, "alias_index", return_value={}):
        assert not decisions.final_decisions("Sugar", "Different Factory Ltd", require_manufacturer=True)[0]
        assert not decisions.final_decisions("Sugar", "same as supplier", require_manufacturer=True)[0]
    checks.append("different/placeholder manufacturer never treated as exact identity")
    assert not decisions.same_company("Al Noor Private Limited", "Al Noor Sugar Mills Limited", aliases={})
    assert decisions.company_key("آلنور شوگر ملز لمیٹڈ") == decisions.company_key("Al-Noor Sugar Mills Ltd")
    alias = {(decisions.company_key("Al Noor Sugar"), "sugar"): {("PSX:ALNRS", "Al-Noor Sugar Mills Limited")},
             (decisions.company_key("Al-Noor Sugar Mills Limited"), "sugar"): {("PSX:ALNRS", "Al-Noor Sugar Mills Limited")}}
    assert decisions.same_company("Al Noor Sugar", "Al-Noor Sugar Mills Limited", "Sugar", alias)
    assert not decisions.same_company("Al Noor Sugar", "Al-Noor Sugar Mills Limited", "Textile", alias)
    checks.append("only verified context-aware aliases bridge different company spellings")
    assert not decisions.real_company("open market") and not decisions.real_company("to be adedd")
    checks.append("market/placeholder supplier is not an exact company")
    marker_row = {"name": "marker", "manufacturer": "same as supplier", "supplier": "Actual Supplier Ltd"}
    changes, evidence, reasons = {}, {}, {}
    cleanup._placeholder_updates(marker_row, changes, evidence, reasons, "")
    assert changes == {"manufacturer": "Actual Supplier Ltd"}
    marker_row.update(manufacturer="Factory Ltd", supplier="same as manufactur")
    changes, evidence, reasons = {}, {}, {}
    cleanup._placeholder_updates(marker_row, changes, evidence, reasons, "")
    assert changes == {"supplier": "Factory Ltd"}
    checks.append("explicit same-as markers copy only the actual opposite company field")
    marker_row.update(manufacturer="to be adedd", supplier="Keep This Supplier", raw_material="Test Product")
    changes, evidence, reasons = {}, {}, {}
    known = {"canonical_name": "Documented Factory Ltd", "identity_key": "REG:TEST", "source_url": "https://example.invalid/fixture"}
    with patch.object(cleanup, "resolve_company", return_value=(known, "verified")):
        cleanup._placeholder_updates(marker_row, changes, evidence, reasons, "Product: Test Product\nManufacturer: Documented Factory Ltd")
    assert changes == {"manufacturer": "Documented Factory Ltd"} and "supplier" not in changes
    changes, evidence, reasons = {}, {}, {}
    with patch.object(cleanup, "resolve_company") as resolve:
        cleanup._placeholder_updates(marker_row, changes, evidence, reasons, "Product: Different Product\nManufacturer: Other Factory Ltd")
        resolve.assert_not_called()
    assert not changes
    checks.append("wrong-product attachment cannot rename a placeholder manufacturer")
    marker_row.update(manufacturer="same as supplier", supplier="same as manufacturer")
    changes, evidence, reasons = {}, {}, {}
    cleanup._placeholder_updates(marker_row, changes, evidence, reasons, "")
    assert not changes
    checks.append("to-be-added extracts Manufacturer only; cyclic placeholders never invent a company")

    absent = [{"id": "D1", "type": "MSDS", "pages": ["D1:P1"]}]
    observations = review.document_observations(absent, [{"id": "D1:P1", "text": "No MSDS found"}])
    assert observations[0]["status"] == "absence_notice" and observations[0]["blocking"] is False
    assert review.document_observations(absent, [])[0]["status"] == "unreadable"
    assert not review.document_observations(absent, [{"id": "D1:P1", "text": "No MSDS found in old folder. " + "Actual complete safety data. " * 60}])
    checks.append("absence notices and unreadable scans distinguished; no client blocking")
    checks.append("single phrase inside a full technical document is not a placeholder verdict")
    scan_doc = frappe._dict(name="SCAN-FIXTURE", documents=[frappe._dict(documents="MSDS", attachment="/private/files/test.pdf", issue_date=None, expiry_date=None)])
    from pypdf import PdfWriter
    import io
    writer = PdfWriter()
    for _ in range(3):
        writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO(); writer.write(buffer)
    fake_cache = MagicMock(); fake_cache.get_value.return_value = None
    with patch.object(review, "linked_content", return_value=(buffer.getvalue(), "/private/files/test.pdf")), patch.object(review, "has_ready_provider", return_value=True), patch.object(review, "routing_signature", return_value="test-route"), patch.object(frappe, "cache", return_value=fake_cache), patch.object(review, "vision_text", return_value="Readable fixture page") as vision:
        review.read_documents(scan_doc, config=MagicMock(), vision_budget=1)
        assert vision.call_count == 1
        vision.reset_mock()
        fake_cache.get_value.side_effect = lambda key, **kwargs: ({"pages": [(1, ""), (2, ""), (3, "")], "truncated": False}
                                                               if key.startswith("ai-document-text:") else "Cached readable page")
        _, cached_sources, _, _ = review.read_documents(scan_doc, config=MagicMock(), vision_budget=0)
        assert len(cached_sources) == 3
        vision.assert_not_called()
    checks.append("daily document extraction cannot request more than one new vision page per Query")

    doc = frappe._dict(name="CURRENT", raw_material="Sugar", manufacturer="Factory", supplier="Supplier", query_types="Food", documents=[], modified="test")
    config = MagicMock()
    config.modified = "policy"; config.get.return_value = ""; config.as_dict.return_value = {}
    response = {"analysis": {"text": "General guidance; manufacturer process not evidenced.", "sources": ["Q0", "H1"]},
                "assessment": {"missing_evidence": {"text": "Request source and process details.", "sources": ["Q0"]},
                               "identity": {"text": "Invented URL", "sources": ["P99"]}}, "findings": [],
                "follow_up_questions": [{"text": "What is its actual source?", "sources": ["Q0"]}, {"text": "Invented reference", "sources": ["P99"]}]}
    with patch.object(review, "read_documents", return_value=(absent, [], [], False)), patch.object(review, "similar_queries", return_value=([dict(approved)], 1, 0)), patch.object(review, "chemistry", return_value=([], "no_unambiguous_public_identity")), patch.object(review, "has_ready_provider", return_value=True), patch.object(review, "_call_llm", return_value=json.dumps(response)) as llm:
        result = review.collect_review(doc, config)
        payload = json.loads(llm.call_args.args[1][1]["content"])
        assert result["ai_status"] == "complete" and result["summaries"]
        assert payload["database_first_references"][0]["id"] == "H1" and payload["research_sources"][0]["id"] == "Q0"
        assert "owner" not in json.loads(payload["database_first_references"][0]["text"])
        assert "client_name" not in json.loads(payload["database_first_references"][0]["text"])
        assert "missing_evidence" in result["assessment"] and "identity" not in result["assessment"]
        assert len(result["follow_up_questions"]) == 1 and result["follow_up_questions"][0]["sources"] == ["Q0"]
    checks.append("analysis still runs on entered metadata/final decisions when OCR text unavailable")
    checks.append("database-first citations and actionable missing-evidence section preserved")
    checks.append("fabricated public references removed from structured assessment")
    lookup_cache = MagicMock(); lookup_cache.get_value.return_value = None
    properties = {"PropertyTable": {"Properties": [{"CID": 5988, "Title": "Sucrose", "MolecularFormula": "C12H22O11"}]}}
    description = {"InformationList": {"Information": [{"Description": "A disaccharide with a sweetening role.", "DescriptionSourceName": "ChEBI"}]}}
    with patch.object(public, "_json", side_effect=[properties, description]), patch.object(frappe, "cache", return_value=lookup_cache):
        references, lookup_status = public.chemistry("Sucrose")
        assert lookup_status == "retrieved" and [r["id"] for r in references] == ["P1", "P2"]
        assert "sweetening" in references[1]["text"] and "NOT manufacturing origins" in references[1]["scope"]
    checks.append("identity-only chemistry and actually retrieved scientific descriptions are separate sources")

    candidate = {"canonical_name": "Al-Noor Sugar Mills Limited", "names": ["Al-Noor Sugar Mills Limited"], "identity_key": "PSX:ALNRS", "status": "ACTIVE"}
    with patch.object(public, "registry_candidates", return_value=[candidate]):
        assert public.resolve_company("Al Noor Sugar")[0] is None
        assert public.resolve_company("Al Noor Sugar Mills Ltd")[0]
        assert public.resolve_company("Al Noor")[0] is None
        assert public.resolve_company("Al Noor Pvt Ltd")[0] is None
        assert public.resolve_company("Al Noor", document_text="Manufacturer: Al-Noor Sugar Mills Limited")[0]
        assert public.resolve_company("Al Noor", document_text="Supplier: Al-Noor Sugar Mills Limited", role="manufacturer")[0] is None
    checks.append("bare/contradictory company names unresolved without role-specific evidence")
    with patch.object(public, "registry_candidates", return_value=[candidate, {**candidate, "identity_key": "OTHER:LEGAL"}]):
        assert public.resolve_company(candidate["canonical_name"])[0] is None
    checks.append("multiple legal identities never silently merged")

    rows = [dict(name=f"Q{i:03}", raw_material="Sugar" if i < 12 else f"Material {i}", query_types="Food", manufacturer="Factory", supplier="Supplier") for i in range(24)]
    chosen = cleanup.diverse_candidates(rows, {}, set(), 50)
    assert len(chosen) == 10 and len({r["name"] for r in chosen}) == 10
    assert len({r["raw_material"] for r in chosen}) == 10
    next_rows = cleanup.diverse_candidates(rows, {r["name"]: "2026-11-07" for r in chosen}, set(), 10)
    assert not {r["name"] for r in chosen} & {r["name"] for r in next_rows}
    assert not cleanup.diverse_candidates(rows, {}, {r["name"] for r in rows}, 10)
    checks.append("daily quota hard-capped at ten DISTINCT Queries with material/type diversity")
    checks.append("oldest-attempt rotation and no repeated Query within same day")
    with patch.object(cleanup, "settings_enabled", return_value=True), patch.object(cleanup, "candidates") as select, patch.object(frappe.db, "commit"), patch.object(frappe.db, "sql", return_value=[(1,)]), patch.object(frappe.db, "count", return_value=10), patch.object(frappe, "set_user"):
        assert cleanup.run_daily()["processed"] == 0
        select.assert_not_called()
    checks.append("rerunning exhausted daily batch cannot reserve or correct an eleventh Query")
    assert providers.model_compatible("Qwen", "qwen-plus") and providers.vision_compatible("Qwen", "qwen-vl-max")
    assert not providers.vision_compatible("Qwen", "qwen-plus") and not providers.vision_compatible("DeepSeek", "deepseek-chat")
    assert providers.vision_compatible("OpenAI", "gpt-4o") and not providers.vision_compatible("OpenAI", "gpt-3.5-turbo")
    checks.append("Qwen supported and text-only models cannot masquerade as OCR routes")
    qwen = frappe._dict(provider="Qwen", provider_region="International", model="qwen-plus", get_password=lambda *args, **kwargs: "unit-test-secret")
    response_mock = MagicMock(status_code=200)
    response_mock.json.return_value = {"choices": [{"message": {"content": "test"}}], "usage": {"prompt_tokens": 2, "completion_tokens": 3}}
    with patch.object(providers.requests, "post", return_value=response_mock) as http:
        assert providers.invoke(qwen, [{"role": "user", "content": "test"}], 128) == ("test", (2, 3))
        assert http.call_args.args[0] == "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
    qwen.provider_region = "China"
    assert providers.endpoint(qwen)[0] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    checks.append("mocked Qwen inference maps API regions, payload and reported token usage")
    original = frappe.session.user
    try:
        frappe.set_user("Guest")
        try:
            cleanup.status()
            raise AssertionError("Guest accessed correction records")
        except frappe.PermissionError:
            pass
    finally:
        frappe.set_user(original)
    checks.append("cleanup administration private; Guest denied")
    checks.extend(_sql_checks())
    checks.extend(_daily_sql_checks())
    return {"passed": len(checks), "checks": checks, "business_records_changed": 0, "paid_provider_calls": 0}


def _sql_checks():
    if frappe.local.site != "eval.portal":
        return ["real SQL fixtures development-only"]
    frappe.db.savepoint("entity_cleanup_test")
    try:
        name = "_TEST_ENTITY_" + uuid.uuid4().hex[:16]
        frappe.db.sql("INSERT INTO tabQuery (name,creation,modified,owner,modified_by,workflow_state,docstatus,raw_material,manufacturer,supplier) VALUES (%s,NOW(6),NOW(6),%s,%s,%s,0,%s,%s,%s)",
                      (name, "Administrator", "Administrator", "Approved", "Sugar", "Al Noor Sugar", "Independent Supplier"))
        before = frappe.db.get_value("Query", name, ["name", "raw_material", "modified", "workflow_state", "manufacturer", "supplier"], as_dict=True)
        log = frappe._dict(name="_TEST_LOG", status="Reserved")
        resolved = {"canonical_name": "Al-Noor Sugar Mills Limited", "identity_key": "PSX:ALNRS", "source_url": "https://dps.psx.com.pk/company/ALNRS", "excerpt": "fixture registry evidence"}
        result = {"changes": {"manufacturer": resolved["canonical_name"]}, "evidence": {"manufacturer": resolved}}
        cleanup.apply_proposal(before, result, log)
        after = frappe.db.get_value("Query", name, ["workflow_state", "manufacturer", "supplier"], as_dict=True)
        assert after.workflow_state == "Approved" and after.supplier == "Independent Supplier"
        assert after.manufacturer == resolved["canonical_name"] and log.status == "Corrected"
        assert frappe.db.count("Version", {"ref_doctype": "Query", "docname": name}) == 1
        assert frappe.db.count("Comment", {"reference_doctype": "Query", "reference_name": name}) == 1
        stale = frappe._dict(name="stale", status="Reserved")
        cleanup.apply_proposal(before, result, stale)
        assert stale.status == "Conflict"
        fresh = frappe.db.get_value("Query", name, ["name", "raw_material", "modified", "workflow_state", "manufacturer", "supplier"], as_dict=True)
        changed_file = frappe._dict(name="file-changed", status="Reserved")
        from sanha.api import review_cache
        with patch.object(review_cache, "file_facts", return_value=[{"changed_file": True}]):
            cleanup.apply_proposal(fresh, {**result, "document_facts": []}, changed_file)
        assert changed_file.status == "Conflict" and "document metadata" in changed_file.reason
        return ["real SQL canonicalization preserves Approved decision and independent Supplier",
                "correction Version/Info evidence and verified alias written", "stale original values protected against overwrite",
                "document evidence changing during public research prevents correction"]
    finally:
        frappe.db.rollback(save_point="entity_cleanup_test")


def _daily_sql_checks():
    if frappe.local.site != "eval.portal":
        return []
    marker = uuid.uuid4().hex[:12]
    run_date = "2199-12-31"
    if frappe.db.count("Entity Correction Log", {"run_date": run_date}):
        raise AssertionError("Isolated quota fixture date already used; no records deleted")
    names = ["_TEST_DAILY_" + marker + str(i) for i in range(12)]
    identity_key = "TEST:" + marker
    before_count = frappe.db.count("Query")
    try:
        for index, name in enumerate(names):
            frappe.db.sql("INSERT INTO tabQuery (name,creation,modified,owner,modified_by,workflow_state,docstatus,raw_material,manufacturer,supplier) VALUES (%s,NOW(6),NOW(6),%s,%s,%s,0,%s,%s,%s)",
                          (name, "Administrator", "Administrator", "Approved", "Material " + str(index), "Maker " + marker, "Independent Supplier"))
        rows = frappe.get_all("Query", filters={"name": ["in", names]}, fields=["name", "modified", "workflow_state", "raw_material", "manufacturer", "supplier"], order_by="name", limit_page_length=0)
        def researched(row):
            evidence = {"canonical_name": "Canonical Maker " + marker, "identity_key": identity_key,
                        "source_url": "https://example.invalid/fixture", "excerpt": "Mocked public identity; SQL quota test only"}
            return {"changes": {"manufacturer": evidence["canonical_name"]}, "evidence": {"manufacturer": evidence}, "reasons": {"manufacturer": "fixture"}}
        with patch.object(cleanup, "today", return_value=run_date), patch.object(cleanup, "settings_enabled", return_value=True), patch.object(cleanup, "candidates", side_effect=lambda limit, run_date=None: rows[:limit]), patch.object(cleanup, "proposal", side_effect=researched):
            first = cleanup.run_daily()
            second = cleanup.run_daily()
        assert first["processed"] == 10 and all(item["status"] == "Corrected" for item in first["results"]), first
        assert second["processed"] == 0 and frappe.db.count("Entity Correction Log", {"run_date": run_date}) == 10
        assert frappe.db.count("Query", {"name": ["in", names], "manufacturer": "Canonical Maker " + marker}) == 10
        assert frappe.db.count("Query", {"name": ["in", names], "workflow_state": "Approved", "supplier": "Independent Supplier"}) == 12
        return ["real persistent daily reservations cap two consecutive runs at ten of twelve Queries",
                "actual ten diverse-material corrections preserve all decisions and independent Suppliers"]
    finally:
        frappe.db.rollback()
        frappe.db.delete("Entity Correction Log", {"query": ["in", names]})
        frappe.db.delete("Entity Name Alias", {"identity_key": identity_key})
        frappe.db.delete("Version", {"ref_doctype": "Query", "docname": ["in", names]})
        frappe.db.delete("Comment", {"reference_doctype": "Query", "reference_name": ["in", names]})
        frappe.db.delete("Query", {"name": ["in", names]})
        frappe.db.commit()
        assert frappe.db.count("Query") == before_count


def check_existing_client_scope():
    """Read-only real-permission check; never send these rows to a provider."""
    from sanha.api.auth import _find_client
    original = frappe.session.user
    try:
        users = frappe.get_all("Has Role", filters={"role": "Client", "parenttype": "User"}, pluck="parent", limit_page_length=1000)
        for user in users:
            if set(frappe.get_roles(user)) & review.STAFF:
                continue
            client = _find_client(user, frappe.db.get_value("User", user, "email"))
            if not client:
                continue
            material = frappe.db.get_value("Query", {"client_name": client.name, "workflow_state": ["in", list(decisions.FINAL_STATES)]}, "raw_material")
            if not material:
                continue
            frappe.set_user(user)
            matches, count = decisions.final_decisions(material)
            assert all(row["client_name"] == client.name and row["workflow_state"] in decisions.FINAL_STATES for row in matches)
            return {"client_scoped": True, "authorized_final_references": count, "foreign_or_pending_references": 0,
                    "historical_file_reads": 0, "provider_requests": 0, "records_changed": 0}
        return {"client_scoped": "No linked Client with a final decision available for this check", "records_changed": 0}
    finally:
        frappe.set_user(original)
