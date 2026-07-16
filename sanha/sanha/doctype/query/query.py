# Copyright (c) 2024, Sanha Halal Pakistan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Query(Document):
    def validate(self):
        self.validate_duplicate_document_attachments()
        self.validate_client_submission_documents()

    def on_update(self):
        self.relink_query_attachment_files()

    def validate_duplicate_document_attachments(self):
        seen = set()
        for row in self.get("documents") or []:
            attachment = (row.attachment or "").strip()
            if not attachment:
                continue
            if attachment in seen:
                frappe.throw(f"Duplicate attachment found in Documents table: {attachment}")
            seen.add(attachment)

    def validate_client_submission_documents(self):
        user_roles = frappe.get_roles(frappe.session.user)
        is_client = "Client" in user_roles

        previous_state = "Draft"
        if frappe.db.exists("Query", self.name):
            previous_state = frappe.db.get_value("Query", self.name, "workflow_state") or "Draft"

        current_state = self.workflow_state or "Draft"
        is_client_submitting_now = (
            is_client
            and previous_state == "Draft"
            and current_state in {"Submitted"}
        )

        if not is_client_submitting_now:
            return

        if not self.get("documents"):
            frappe.throw("You must add at least one document before submission.")

        for index, row in enumerate(self.get("documents") or [], start=1):
            if not row.attachment:
                frappe.throw(f"Row #{index}: Please attach a file.")

    def relink_query_attachment_files(self):
        for row in self.get("documents") or []:
            attachment = (row.attachment or "").strip()
            if not attachment:
                continue
            self.ensure_file_linked_to_query(attachment)

    def ensure_file_linked_to_query(self, attachment):
        existing = frappe.get_all(
            "File",
            filters={
                "file_url": attachment,
                "attached_to_doctype": "Query",
                "attached_to_name": self.name,
            },
            pluck="name",
            limit_page_length=1,
            ignore_permissions=True,
        )
        if existing:
            return

        temp_files = frappe.get_all(
            "File",
            filters={
                "file_url": attachment,
                "attached_to_doctype": "Query",
                "attached_to_name": ["like", "new-query-%"],
                "owner": self.owner,
            },
            fields=["name"],
            limit_page_length=2,
            ignore_permissions=True,
        )

        if len(temp_files) == 1:
            frappe.db.set_value(
                "File",
                temp_files[0].name,
                {
                    "attached_to_name": self.name,
                    "attached_to_field": "attachment",
                    "is_private": 1 if attachment.startswith("/private/files/") else 0,
                },
                update_modified=False,
            )
            return

        unattached = frappe.get_all(
            "File",
            filters={
                "file_url": attachment,
                "attached_to_doctype": ["is", "not set"],
                "attached_to_name": ["is", "not set"],
            },
            pluck="name",
            limit_page_length=1,
            ignore_permissions=True,
        )

        if unattached:
            frappe.db.set_value(
                "File",
                unattached[0],
                {
                    "attached_to_doctype": "Query",
                    "attached_to_name": self.name,
                    "attached_to_field": "attachment",
                    "is_private": 1 if attachment.startswith("/private/files/") else 0,
                },
                update_modified=False,
            )


@frappe.whitelist()
def find_similar_query(raw_material: str | None = None,
                    manufacturer: str | None = None,
                    exclude_name: str | None = None):
    """Return up to 3 most-recent Queries with same raw_material+manufacturer (excluding current)."""
    raw_material = (raw_material or "").strip()
    manufacturer = (manufacturer or "").strip()
    if not raw_material or not manufacturer:
        return {"matches": []}

    filters = {
        "raw_material": raw_material,
        "manufacturer": manufacturer,
    }
    if exclude_name:
        filters["name"] = ["!=", exclude_name]

    matches = frappe.get_all(
        "Query",
        filters=filters,
        fields=["name", "workflow_state", "client_name", "owner", "modified"],
        order_by="modified desc",
        limit=3,
    )
    return {"matches": matches}

@frappe.whitelist()
def find_duplicates(raw_material=None, supplier=None, manufacturer=None, for_current_user=False):
    user = frappe.session.user
    filters = {
        "raw_material": raw_material,
        "supplier": supplier,
        "manufacturer": manufacturer,
        "docstatus": ("<", 2)
    }
    if for_current_user and user != "Administrator":
        filters["owner"] = user

    # Get all matches except the earliest one
    records = frappe.get_all("Query", filters=filters, fields=["name", "owner", "modified", "client_name"])
    records_sorted = sorted(records, key=lambda x: x["modified"])
    return records_sorted[1:]  # skip the first (original) entry

