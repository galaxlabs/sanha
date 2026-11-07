"""Provider regressions use disabled test profiles and mocked HTTP only."""
import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

import frappe
from sanha.api import ai_providers as providers, review_cache, staff_review


def run_checks():
    if frappe.local.site != "eval.portal":
        frappe.throw("Provider persistence fixtures run on development only.")
    profiles, caches, checks = [], [], []
    marker = "unit-test-credential-" + uuid4().hex
    review_query = "AI-REGRESSION-" + uuid4().hex
    cache = frappe.cache()
    original_set = cache.set_value
    def capture(key, value, *args, **kwargs):
        if str(key).startswith("ai-call:"): caches.append(key)
        return original_set(key, value, *args, **kwargs)
    try:
        for provider, model in [("OpenAI", "gpt-4o-mini"), ("Claude", "claude-test-model")]:
            saved = providers.save_profile({"title": "Regression " + provider + " " + uuid4().hex[:8], "provider": provider, "model": model, "api_key": marker, "enabled": 0, "use_for_text": 1, "use_for_vision": 0, "priority": len(profiles) + 1, "max_output_tokens": 128, "daily_token_budget": 5000})
            profiles.append(saved["name"])
        first, second = [frappe.get_doc("AI Provider Profile", name) for name in profiles]
        assert first.get_password("api_key") == marker and second.get_password("api_key") == marker
        revision = first.credential_revision
        providers.save_profile({"title": first.title + " edited", "api_key": ""}, first.name)
        reloaded = frappe.get_doc("AI Provider Profile", first.name)
        assert reloaded.get_password("api_key") == marker, "Blank update must preserve credential"
        assert reloaded.credential_revision == revision, "Blank update must preserve credential revision"
        assert marker not in json.dumps(providers.list_profiles(), default=str)
        checks.append("separate encrypted keys, blank preserves key, safe profile listing")

        assert not providers.model_compatible("Claude", "gpt-4o")
        assert not providers.model_compatible("OpenAI", "claude-test-model")
        assert providers.model_compatible("Gemini", "gemini-test-model")
        assert providers.model_compatible("DeepSeek", "deepseek-test-model")
        try:
            providers.save_profile({"model": "gpt-4o"}, second.name)
        except frappe.ValidationError:
            pass
        else:
            raise AssertionError("Incompatible profile saved")
        assert frappe.db.get_value("AI Provider Profile", second.name, "model") == "claude-test-model"
        checks.append("cross-provider model mismatch rejected")

        response = MagicMock(status_code=200)
        response.json.return_value = {"data": [{"id": "gpt-4o-mini"}, {"id": "claude-other"}]}
        with patch.object(providers.requests, "get", return_value=response), patch.object(providers.requests, "post") as inference:
            checked = providers.test_connection(first.name)
            assert checked["models"] == ["gpt-4o-mini"] and checked["generation_calls"] == 0
            inference.assert_not_called()
        checks.append("connection check authenticates catalog without generation")

        with patch.object(providers, "ready_profiles", return_value=[first, second]), patch.object(providers, "invoke", return_value=("Cached answer", (10, 20))) as inference, patch.object(cache, "set_value", side_effect=capture):
            messages = [{"role": "user", "content": "cache-" + uuid4().hex}]
            assert providers.call(messages) == "Cached answer"
            before = int(providers.day_usage(first.name)["tokens"])
            assert providers.call(messages) == "Cached answer"
            assert inference.call_count == 1 and int(providers.day_usage(first.name)["tokens"]) == before == 30, (inference.call_count, before, providers.day_usage(first.name))
        checks.append("cached response spends no additional tokens or calls")

        with patch.object(providers, "ready_profiles", return_value=[first, second]), patch.object(providers, "invoke", side_effect=[providers.ProviderError("provider_busy", 503), ("Fallback answer", (10, 20))]) as inference, patch.object(cache, "set_value", side_effect=capture):
            messages = [{"role": "user", "content": "fallback-" + uuid4().hex}]
            assert providers.call(messages) == "Fallback answer"
            assert providers.call(messages) == "Fallback answer" and inference.call_count == 2
        checks.append("priority fallback used once; fallback answer reused")

        frappe.db.set_value("AI Provider Profile", first.name, "daily_token_budget", 1)
        first = frappe.get_doc("AI Provider Profile", first.name)
        with patch.object(providers, "ready_profiles", return_value=[first]), patch.object(providers, "invoke") as inference:
            try:
                providers.call([{"role": "user", "content": "budget-" + uuid4().hex}])
            except providers.ProviderError:
                pass
            else:
                raise AssertionError("Budget was exceeded")
            inference.assert_not_called()
        checks.append("budget rejects request before inference")

        original_user = frappe.session.user
        try:
            frappe.set_user("Guest")
            for operation in (providers.list_profiles, lambda: providers.save_profile({}), lambda: providers.test_connection(first.name), lambda: review_cache.latest(review_query)):
                try: operation()
                except frappe.PermissionError: pass
                else: raise AssertionError("Non-admin/nonstaff access allowed")
        finally:
            frappe.set_user(original_user)
        checks.append("configuration and staff summary endpoints fail closed")

        doc = frappe._dict(name=review_query, raw_material="Current material", query_types="Type", supplier="Supplier", manufacturer="Factory", workflow_state="Submitted", documents=[], modified="version-one")
        config = MagicMock()
        config.modified = "policy-one"
        config.get.side_effect = lambda field: {"review_clauses": "Clause", "review_terms": "Term"}.get(field)
        result = {"ai_status": "complete", "reviewed_at": "test", "summaries": [{"text": "One consolidated summary", "sources": ["D1:P1"]}], "sources": [{"id": "D1:P1", "text": "PRIVATE EXTRACTION", "url": "/private/files/fake.pdf", "page": 1}], "documents": []}
        frappe.db.sql("INSERT INTO tabQuery (name,creation,modified,owner,modified_by,workflow_state,docstatus,raw_material) VALUES (%s,NOW(6),NOW(6),%s,%s,%s,0,%s)",
                      (review_query, "Administrator", "Administrator", "Submitted", "Provider regression fixture"))
        with patch.object(staff_review, "check_query", return_value=doc), patch.object(review_cache, "review_config", return_value=config), patch.object(review_cache, "file_facts", return_value=[]), patch.object(review_cache, "routing_signature", return_value="route-version"), patch.object(review_cache, "auto_enabled", return_value=True), patch.object(review_cache, "ready_profiles", return_value=[first]), patch.object(review_cache, "budget_signature", return_value="budget-version"), patch.object(staff_review, "collect_review", return_value=result) as collect:
            review_cache.run(review_query)
            review_cache.run(review_query)
            assert collect.call_count == 1
            public = review_cache.latest(review_query)
            assert public["status"] == "complete" and "PRIVATE EXTRACTION" not in json.dumps(public)
            old_key = public["fingerprint"]
            doc.workflow_state = "Under Review"; doc.modified = "version-two"
            assert review_cache.latest(review_query)["fingerprint"] == old_key
            doc.supplier = "Changed supplier"
            assert review_cache.latest(review_query)["fingerprint"] != old_key
        checks.append("persistent summary reused; raw source text hidden; material inputs invalidate")

        with patch.object(frappe, "enqueue", side_effect=RuntimeError("queue unavailable")), patch.object(frappe, "log_error", side_effect=RuntimeError("logger unavailable")):
            review_cache.safe_enqueue(review_query)
        checks.append("queue/logger failure cannot fail a Query save callback")

        source = {"id": "D1:P1", "text": "Current document only", "page": 1, "url": "/private/files/current.pdf"}
        config.as_dict.return_value = {}
        with patch.object(staff_review, "read_documents", return_value=([], [source], [], False)), patch.object(staff_review, "has_ready_provider", return_value=True), patch.object(staff_review, "similar_queries", return_value=([], 0, 0)), patch.object(staff_review, "chemistry", return_value=([], "test")), patch.object(staff_review, "linked_content", side_effect=AssertionError("Historical files must not be opened")), patch.object(staff_review, "_call_llm", return_value=json.dumps({"analysis": {"text": "Concise analysis", "sources": ["D1:P1"]}, "findings": []})) as llm:
            analyzed = staff_review.collect_review(doc, config)
            payload = json.loads(llm.call_args.args[1][1]["content"])
            assert "prior_matches" not in payload and analyzed["ai_status"] == "partial_cited_output" and len(analyzed["summaries"]) == 1
        checks.append("current Query files only; one cited analysis; historical references are metadata-only")
        return {"checks": checks, "passed": len(checks), "real_provider_requests": 0, "business_records_changed": 0}
    finally:
        frappe.db.rollback()
        for key in caches: cache.delete_value(key)
        frappe.db.delete("AI Query Review", {"query": review_query})
        frappe.db.delete("Query", {"name": review_query})
        if profiles:
            frappe.db.delete("AI Usage Log", {"profile": ["in", profiles]})
            for name in profiles:
                if frappe.db.exists("AI Provider Profile", name): frappe.delete_doc("AI Provider Profile", name, ignore_permissions=True, force=True)
        frappe.db.commit()
