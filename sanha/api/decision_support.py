"""Permission-scoped final decisions and evidence-backed company identities."""
import re
import unicodedata
from difflib import SequenceMatcher

import frappe

FINAL_STATES = ("Approved", "Halal", "Rejected", "Haram", "Doubtful")
PLACEHOLDERS = {"", "na", "none", "unknown", "tobeadded", "tobeadedd", "sameassupplier",
                "sameasmanufactur", "sameasmanufacture", "sameasmanufacturer", "openmarket", "localmarket"}


def text_key(value):
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return " ".join(re.sub(r"[\W_]+", " ", value).split())


def company_words(value):
    # Punctuation/spaces are spelling differences; private/public are NOT.
    words = text_key(value).split()
    substitutions = {"ltd": "limited", "pvt": "private", "co": "company", "inc": "incorporated",
                     "النور": "alnoor", "آلنور": "alnoor", "شوگر": "sugar", "ملز": "mills",
                     "پرائیویٹ": "private", "لمیٹڈ": "limited", "لیمیٹڈ": "limited"}
    return [substitutions.get(w, w) for w in words]


def company_key(value):
    return "".join(company_words(value))


def real_company(value):
    return company_key(value) not in PLACEHOLDERS


def alias_index():
    if not frappe.db.exists("DocType", "Entity Name Alias"):
        return {}
    index = {}
    for row in frappe.get_all("Entity Name Alias", filters={"verified": 1},
                              fields=["original_name", "canonical_name", "identity_key", "material_context"], limit_page_length=0):
        key = (company_key(row.original_name), text_key(row.material_context))
        index.setdefault(key, set()).add((row.identity_key, row.canonical_name))
        index.setdefault((company_key(row.canonical_name), key[1]), set()).add((row.identity_key, row.canonical_name))
    return index


def identity(value, material="", aliases=None):
    if not real_company(value):
        return None
    key = company_key(value)
    aliases = alias_index() if aliases is None else aliases
    context = text_key(material)
    choices = set(aliases.get((key, context), set())) | set(aliases.get((key, ""), set()))
    identities = {choice[0] for choice in choices}
    if len(identities) == 1:
        return "verified:" + next(iter(identities))
    # Conflicting aliases are never collapsed into a guessed identity.
    return "spelling:" + key if not choices else None


def same_company(left, right, material="", aliases=None):
    if not real_company(left) or not real_company(right):
        return False
    if company_key(left) == company_key(right):
        return True
    aliases = alias_index() if aliases is None else aliases
    return bool((a := identity(left, material, aliases)) and a == identity(right, material, aliases))


def final_decisions(raw_material, manufacturer="", supplier="", exclude_name=None, require_manufacturer=False):
    """Only final decisions; no historical file bytes or in-progress references."""
    key = text_key(raw_material)
    if not key or (require_manufacturer and not real_company(manufacturer)):
        return [], 0
    token = max(key.split(), key=len)
    rows = frappe.get_list("Query", filters=[["workflow_state", "in", list(FINAL_STATES)], ["docstatus", "<", 2], ["raw_material", "like", "%" + token + "%"]],
                           fields=["name", "raw_material", "manufacturer", "supplier", "workflow_state", "modified", "client_name", "owner"],
                           order_by="modified desc, name asc", limit_page_length=0)
    aliases = alias_index()
    matches = []
    for row in rows:
        if row.name == exclude_name or row.workflow_state not in FINAL_STATES:
            continue
        other = text_key(row.raw_material)
        exact = key == other
        score = SequenceMatcher(None, key, other).ratio() if other else 0
        if not exact and (len(key) < 4 or len(other) < 4 or score < .82):
            continue
        manufacturer_match = same_company(manufacturer, row.manufacturer, raw_material, aliases)
        if require_manufacturer and (not manufacturer_match or not exact):
            continue
        supplier_match = same_company(supplier, row.supplier, raw_material, aliases)
        matches.append({**row, "same_material": exact, "same_manufacturer": manufacturer_match,
                        "same_supplier": supplier_match, "same_entities": manufacturer_match and supplier_match,
                        "similarity": round(score * 100), "exact_documents": False, "documents_checked": False,
                        "match_basis": "same_material_and_manufacturer" if exact and manufacturer_match else "material_reference_only"})
    matches.sort(key=lambda r: (r["same_material"] and r["same_manufacturer"], r["same_material"], r["same_supplier"], r["similarity"], str(r["modified"])), reverse=True)
    return matches[:100], len(matches)
