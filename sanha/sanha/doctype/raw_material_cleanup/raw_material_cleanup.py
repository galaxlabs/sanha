# Copyright (c) 2025, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt

# sanha/sanha/doctype/raw_material_cleanup/raw_material_cleanup.py

import frappe
from frappe.model.document import Document

def normalize(text: str) -> str:
    """Simple normalization used for normalized_key."""
    if not text:
        return ""
    t = text.strip().lower()
    # remove extra spaces
    t = " ".join(t.split())
    return t

class RawMaterialCleanup(Document):
    pass


@frappe.whitelist()
def apply_mappings(docname: str):
    """
    Use one Raw Material Cleanup doc as a 'batch' to:
    - Take all candidate raw_material texts
    - Attach them as aliases under core_raw_material (Raw Material Master)
    """
    doc = frappe.get_doc("Raw Material Cleanup", docname)

    if not doc.core_raw_material:
        frappe.throw("Please select a Core Raw Material before applying mappings.")

    # Load the Raw Material Master once
    rm = frappe.get_doc("Raw Material Master", doc.core_raw_material)

    # Build a set of existing aliases (to avoid duplicates)
    existing_aliases = {
        (a.alias or "").strip().lower()
        for a in (rm.raw_material_alias or [])
    }

    created = 0
    skipped = 0

    for row in (doc.candidates or []):
        alias_text = (row.raw_material or "").strip()
        if not alias_text:
            continue

        key = alias_text.lower()
        if key in existing_aliases:
            skipped += 1
            continue

        # Append new alias row
        child = rm.append("raw_material_alias", {})
        child.alias = alias_text
        child.normalized_key = normalize(alias_text)
        child.source_type = "Query"
        child.source_query = row.query
        child.is_preferred = 0

        existing_aliases.add(key)
        created += 1

    if created:
        rm.save(ignore_permissions=True)
        frappe.db.commit()

    msg = f"Alias mapping complete. Created {created} new aliases, skipped {skipped} existing."
    return msg

