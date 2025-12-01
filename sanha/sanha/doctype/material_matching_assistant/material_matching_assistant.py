# Copyright (c) 2025, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt

# Copyright (c) 2025, Sanha Halal Pakistan
# For license information, please see license.txt

import re
import frappe
from frappe.model.document import Document


class MaterialMatchingAssistant(Document):
    """DocType controller (currently no special hooks needed)."""
    pass


def _normalize(text: str) -> str:
    """
    Simple normalizer:
    - lowercase
    - remove non-alphanumeric chars -> space
    - collapse multiple spaces
    """
    if not text:
        return ""
    t = text.lower().strip()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


@frappe.whitelist()
def create_raw_material_aliases(material: str, aliases):
    """
    Create Raw Material Alias rows under a Raw Material Master.

    Args:
        material: name of Raw Material Master (e.g. "Sugar")
        aliases: list[dict] like:
            [
                {"alias": "White Cane Suger", "source_query": "Query-0001"},
                {"alias": "Refined Suger", "source_query": "Query-0002"},
                ...
            ]
    """
    if not material:
        frappe.throw("Material is required.")

    # aliases may come as JSON string from JS
    if isinstance(aliases, str):
        aliases = frappe.parse_json(aliases)

    if not aliases:
        return {"msg": "No aliases provided.", "created": 0}

    # Load Raw Material Master
    try:
        rm = frappe.get_doc("Raw Material Master", material)
    except frappe.DoesNotExistError:
        frappe.throw(f"Raw Material Master '{material}' not found.")

    # Existing aliases (case-insensitive) to avoid duplicates
    existing_aliases = set()
    for row in (rm.raw_material_alias or []):
        if row.alias:
            existing_aliases.add(row.alias.strip().lower())

    created = 0

    for a in aliases:
        alias_text = (a.get("alias") or "").strip()
        source_query = a.get("source_query")

        if not alias_text:
            continue

        # Skip if already present
        if alias_text.lower() in existing_aliases:
            continue

        norm_key = _normalize(alias_text)

        rm.append("raw_material_alias", {
            "alias": alias_text,
            "normalized_key": norm_key,
            "language": "",          # optional, can be filled later
            "source_type": "Query",
            "source_query": source_query,
            "is_preferred": 0,
        })

        existing_aliases.add(alias_text.lower())
        created += 1

    if created:
        rm.save(ignore_permissions=True)
        frappe.db.commit()

    return {"msg": f"Created {created} aliases for {material}.", "created": created}


@frappe.whitelist()
def create_manufacturer_aliases(manufacturer: str, aliases):
    """
    Create Manufacturer Alias rows under a Manufacturer Master.

    Args:
        manufacturer: name of Manufacturer Master
            (e.g. "Al Noor Sugar Mills Limited")
        aliases: list[dict] like:
            [
                {"alias": "Al Noor Sugar Mills", "source_query": "Query-0001"},
                {"alias": "Al Noor Sugar Mills Ltd.", "source_query": "Query-0002"},
                ...
            ]
    """
    if not manufacturer:
        frappe.throw("Manufacturer is required.")

    # aliases may come as JSON string from JS
    if isinstance(aliases, str):
        aliases = frappe.parse_json(aliases)

    if not aliases:
        return {"msg": "No aliases provided.", "created": 0}

    # Load Manufacturer Master
    try:
        mm = frappe.get_doc("Manufacturer Master", manufacturer)
    except frappe.DoesNotExistError:
        frappe.throw(f"Manufacturer Master '{manufacturer}' not found.")

    # Existing aliases (case-insensitive) to avoid duplicates
    existing_aliases = set()
    for row in (mm.manufacturer_alias or []):
        if row.alias:
            existing_aliases.add(row.alias.strip().lower())

    created = 0

    for a in aliases:
        alias_text = (a.get("alias") or "").strip()
        source_query = a.get("source_query")

        if not alias_text:
            continue

        # Skip if already present
        if alias_text.lower() in existing_aliases:
            continue

        norm_key = _normalize(alias_text)

        mm.append("manufacturer_alias", {
            "alias": alias_text,
            "normalized_key": norm_key,
            "language": "",          # optional, can be filled later
            "source_type": "Query",
            "source_query": source_query,
            "is_preferred": 0,
        })

        existing_aliases.add(alias_text.lower())
        created += 1

    if created:
        mm.save(ignore_permissions=True)
        frappe.db.commit()

    return {"msg": f"Created {created} aliases for {manufacturer}.", "created": created}
