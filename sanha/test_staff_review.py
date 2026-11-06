import hashlib
import json
from unittest.mock import MagicMock, patch

import frappe
from sanha.api import staff_review as review


def run_checks():
    tests = []
    for placeholder in ("to be added", " To Be Adedd ", "same as supplier", "same as manufactur", "same as manufacturer", "", "N/A"):
        assert not review.real_entity(placeholder), placeholder
    assert review.real_entity("Example Manufacturing Ltd")
    tests.append("placeholder recognition")

    original = frappe.session.user
    try:
        frappe.set_user("Guest")
        with patch.object(frappe, "get_roles", return_value=["Client"]), patch.object(frappe, "enqueue") as enqueue:
            try:
                review.start("not-allowed")
            except frappe.PermissionError:
                pass
            else:
                raise AssertionError("Client started a staff review")
            enqueue.assert_not_called()
        tests.append("Client cannot enqueue review")
    finally:
        frappe.set_user(original)

    with patch.object(review, "require_staff"), patch.object(frappe, "get_doc", return_value=frappe._dict(workflow_state="Draft", check_permission=lambda _: None)):
        try:
            review.check_query("draft")
        except frappe.ValidationError:
            pass
        else:
            raise AssertionError("Draft review allowed")
    tests.append("Draft excluded")

    with patch.object(review, "require_staff"), patch.object(frappe, "cache") as cache:
        cache.return_value.get_value.return_value = {"user": "another-reviewer", "query": "Q"}
        try:
            review.status("foreign-token")
        except frappe.PermissionError:
            pass
        else:
            raise AssertionError("Cross-reviewer cache disclosure")
    tests.append("review result ownership")

    for url in ("https://example.com/private.pdf", "file:///etc/passwd"):
        try:
            review.linked_content(None, frappe._dict(attachment=url))
        except ValueError:
            pass
        else:
            raise AssertionError("External file read allowed")
    tests.append("external attachment denied")

    found = review.cited_findings([{"text": "valid", "sources": ["D1:P1"]}, {"text": "invented", "sources": ["D9:P9"]}, {"text": "uncited", "sources": []}], {"D1:P1"})
    assert len(found) == 1 and found[0]["text"] == "valid"
    tests.append("fabricated references discarded")

    doc = frappe._dict(name="Current", raw_material="Material", supplier="Supplier Ltd", manufacturer="Factory Ltd", documents=[], modified="test")
    candidate = frappe._dict(name="Prior", raw_material="Material", supplier="Supplier Ltd", manufacturer="Factory Ltd", workflow_state="Approved", modified="test")
    attachment = frappe._dict(documents="Halal Certificate", issue_date=None, expiry_date=None)
    prior = MagicMock()
    prior.documents = [attachment]
    signature = [("halal certificate", hashlib.sha256(b"certificate").hexdigest(), "", "")]
    with patch.object(frappe, "get_list", return_value=[candidate]), patch.object(frappe, "get_doc", return_value=prior), patch.object(review, "linked_content", return_value=(b"certificate", "/private/files/a.pdf")):
        matches, _, _ = review.similar_queries(doc, signature, True)
        assert matches[0]["exact_documents"]
        doc.supplier = "same as manufacturer"
        matches, _, _ = review.similar_queries(doc, signature, True)
        assert not matches[0]["exact_documents"] and not matches[0]["same_entities"]
        doc.supplier = "Supplier Ltd"
    tests.append("exact approval requires real companies and identical files")

    config = MagicMock()
    config.modified = "policy-test"
    policy = {"review_terms": "restricted-example", "review_clauses": "Policy clause example"}
    config.get.side_effect = lambda key: policy.get(key)
    config.as_dict.return_value = policy
    config.get_password.return_value = False
    source = {"id": "D1:P1", "text": "Certificate includes restricted-example", "url": "/private/files/a.pdf", "page": 1}
    with patch.object(review, "read_documents", return_value=([], [source], [], False)), patch.object(review, "similar_queries", return_value=([], 0, 0)), patch.object(review, "_call_llm") as llm:
        result = review.collect_review(doc, config)
        assert result["ai_status"] == "not_configured" and result["alerts"][0]["source"] == "D1:P1"
        llm.assert_not_called()
        config.get_password.return_value = True
        llm.return_value = json.dumps({"summaries": [{"text": "Evidence summary", "sources": ["D1:P1"]}], "findings": [{"text": "Unsupported", "sources": ["missing"]}]})
        result = review.collect_review(doc, config)
        assert result["ai_status"] == "complete" and len(result["summaries"]) == 1 and result["findings"] == []
    tests.append("missing key explicit; mocked AI citation and alert checks")
    return {"checks": tests, "passed": len(tests), "paid_provider_calls": 0, "records_changed": 0}
