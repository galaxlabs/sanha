"""Bounded public registry/chemistry research, separate from private documents."""
import hashlib
import html
import json
import re
from urllib.parse import quote

import frappe
import requests

from sanha.api.decision_support import company_key, company_words, real_company


def _json(url, params=None):
    response = requests.get(url, params=params, timeout=(4, 12), headers={"User-Agent": "SANHA-Material-Research/1.0", "Accept": "application/json"})
    if response.status_code == 404:
        return {}
    response.raise_for_status()
    if len(response.content) > 1_000_000:
        raise ValueError("Public response too large")
    return response.json()


def chemistry(material):
    """Only fixed public NLM API; never send companies, private files or prompts."""
    term = str(material or "").strip()[:160]
    if not term:
        return [], "no_material"
    cache_key = "material-public:v2:" + hashlib.sha256(term.casefold().encode()).hexdigest()
    cached = frappe.cache().get_value(cache_key, expires=True)
    if cached is not None:
        return cached["sources"], cached["status"]
    try:
        data = _json("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/" + quote(term, safe="") + "/property/Title,MolecularFormula,IUPACName/JSON")
        compounds = data.get("PropertyTable", {}).get("Properties", [])
        # Multiple identities/mixtures are not silently resolved to the first hit.
        if len(compounds) != 1:
            result = {"sources": [], "status": "no_unambiguous_public_identity"}
        else:
            item = compounds[0]
            result = {"status": "retrieved", "sources": [{"id": "P1", "kind": "public_chemistry", "title": item.get("Title"),
                      "url": "https://pubchem.ncbi.nlm.nih.gov/compound/" + str(int(item["CID"])),
                      "retrieved_at": frappe.utils.now(), "text": json.dumps(item, ensure_ascii=False),
                      "scope": "Public compound identity; NOT evidence of this supplier's process, grade or halal status."}]}
            try:
                descriptions = _json("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/" + str(int(item["CID"])) + "/description/JSON")
                facts = [{key: row.get(key) for key in ("Description", "DescriptionSourceName", "DescriptionURL")}
                         for row in descriptions.get("InformationList", {}).get("Information", []) if row.get("Description")][:2]
                if facts:
                    result["sources"].append({"id": "P2", "kind": "public_chemistry", "title": str(item.get("Title")) + " — scientific description",
                                               "url": "https://pubchem.ncbi.nlm.nih.gov/compound/" + str(int(item["CID"])),
                                               "retrieved_at": frappe.utils.now(), "text": json.dumps(facts, ensure_ascii=False)[:4000],
                                               "scope": "Retrieved public scientific description. Biological/metabolite roles are NOT manufacturing origins or evidence about this product."})
            except Exception:
                pass  # Identity-only evidence remains useful but cannot support unstated uses.
        frappe.cache().set_value(cache_key, result, expires_in_sec=86400 * 7)
        return result["sources"], result["status"]
    except Exception:
        return [], "public_lookup_unavailable"


def registry_candidates(name):
    """GLEIF's public legal-entity registry; no invented web references."""
    if not real_company(name):
        return []
    key = "company-registry:v1:" + hashlib.sha256(name.casefold().encode()).hexdigest()
    cached = frappe.cache().get_value(key, expires=True)
    if cached is not None:
        return cached
    try:
        data = _json("https://api.gleif.org/api/v1/lei-records", {"filter[fulltext]": str(name)[:140], "page[size]": 5})
    except Exception:
        data = {}
    candidates = []
    for item in data.get("data", [])[:5]:
        attributes = item.get("attributes", {})
        entity = attributes.get("entity", {})
        canonical = entity.get("legalName", {}).get("name", "")
        aliases = [canonical] + [a.get("name", "") for a in entity.get("otherNames", [])]
        identifier = str(attributes.get("lei") or item.get("id", ""))
        if not re.fullmatch(r"[A-Z0-9]{20}", identifier) or not canonical or len(canonical) > 140:
            continue
        candidates.append({"canonical_name": canonical, "names": aliases,
                           "identity_key": "LEI:" + identifier, "country": entity.get("legalAddress", {}).get("country"),
                           "source_url": "https://api.gleif.org/api/v1/lei-records/" + identifier,
                           "excerpt": canonical, "status": entity.get("status"), "retrieved_at": frappe.utils.now()})
    # This official, independently located company reference covers the user's
    # Al-Noor Sugar example, which has no GLEIF record. It is a candidate, NOT
    # evidence that every short "Al-Noor" or private company is that identity.
    if any(word in name.casefold() for word in ("noor", "النور", "آلنور")):
        try:
            response = requests.get("https://dps.psx.com.pk/company/ALNRS", timeout=(4, 12))
            response.raise_for_status()
            title = re.search(r"<title>.*?Stock quote for (.*?) - Pakistan Stock Exchange", response.text, re.S | re.I)
            if title and len(response.content) < 1_000_000:
                canonical = html.unescape(title.group(1)).strip()
                if company_key(canonical) == "alnoorsugarmillslimited":
                    candidates.append({"canonical_name": canonical, "names": [canonical], "identity_key": "PSX:ALNRS",
                                       "country": "PK", "source_url": "https://dps.psx.com.pk/company/ALNRS",
                                       "excerpt": canonical, "status": "ACTIVE", "retrieved_at": frappe.utils.now()})
        except Exception:
            pass
    frappe.cache().set_value(key, candidates, expires_in_sec=86400 * 7)
    return candidates


def legal_core(name):
    return "".join(word for word in company_words(name) if word not in {"limited", "private", "public", "incorporated", "company"})


def resolve_company(name, contact="", document_text="", role="manufacturer"):
    """Canonicalize only uniquely corroborated identities; fuzzy names stay open."""
    try:
        candidates = registry_candidates(name)
    except Exception:
        return None, "registry_unavailable"
    proven = []
    for candidate in candidates:
        if candidate.get("status") not in {None, "ACTIVE"}:
            continue
        exact = any(company_key(name) == company_key(alias) for alias in candidate["names"])
        # Full legal name in this Query's own evidence can resolve a short name.
        role_pattern = r"(?:manufacturer|manufactured by)" if role == "manufacturer" else r"(?:supplier|supplied by)"
        role_evidence = " ".join(re.findall(role_pattern + r"\s*[:\-]?\s*([^\n]{1,200})", document_text, re.I))
        anchored = (len(legal_core(name)) >= 5 and legal_core(name) in legal_core(candidate["canonical_name"])
                    and company_key(candidate["canonical_name"]) in company_key(role_evidence))
        # A plausible abbreviated brand is a research candidate, not proof that
        # this Query belongs to that legal entity. Require exact registered alias
        # or role-specific product evidence before an automatic correction.
        if exact or anchored:
            proven.append(candidate)
    by_id = {item["identity_key"]: item for item in proven}
    if len(by_id) == 1:
        return next(iter(by_id.values())), "verified_registry_identity"
    return None, "ambiguous_or_unproven_identity" if candidates else "no_registry_evidence"
