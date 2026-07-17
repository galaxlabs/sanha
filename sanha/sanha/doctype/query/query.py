# Copyright (c) 2024, Sanha Halal Pakistan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


LOCKED_PARENT_FIELDS = (
    "raw_material",
    "query_types",
    "supplier",
    "supplier_contact",
    "manufacturer",
    "manufacturer_contact",
    "client_name",
    "workflow_state",
)
DOCUMENT_FIELDS = ("documents", "issue_date", "expiry_date", "attachment")


def _same_value(left, right):
    return str(left or "") == str(right or "")


class Query(Document):
    def validate(self):
        self.validate_client_edit_lock()
        self.validate_duplicate_document_attachments()
        self.validate_client_submission_documents()

    def on_update(self):
        self.relink_query_attachment_files()

    def validate_client_edit_lock(self):
        if self.is_new():
            return

        roles = set(frappe.get_roles(frappe.session.user))
        staff_roles = {"Evaluation", "SB User", "Certificate Manager", "Admin", "System Manager", "Administrator"}
        if "Client" not in roles or staff_roles.intersection(roles):
            return

        previous_state = frappe.db.get_value("Query", self.name, "workflow_state") or "Draft"
        if previous_state == "Draft":
            return

        previous = frappe.get_doc("Query", self.name)
        for field in LOCKED_PARENT_FIELDS:
            if not _same_value(self.get(field), previous.get(field)):
                frappe.throw("Submitted queries are locked for client users. Only new document rows can be added.", frappe.PermissionError)

        existing_rows = {row.name: row for row in previous.get("documents") or []}
        submitted_rows = {row.name: row for row in self.get("documents") or [] if row.name in existing_rows}

        if set(existing_rows) - set(submitted_rows):
            frappe.throw("Existing document rows cannot be removed after submission.", frappe.PermissionError)

        for row_name, old_row in existing_rows.items():
            new_row = submitted_rows[row_name]
            for field in DOCUMENT_FIELDS:
                if not _same_value(new_row.get(field), old_row.get(field)):
                    frappe.throw("Existing document rows cannot be changed after submission. Add a new document row instead.", frappe.PermissionError)

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
                    supplier: str | None = None,
                    exclude_name: str | None = None):
    """Return helpful existing Queries for the same raw material/manufacturer/supplier."""
    raw_material = (raw_material or "").strip()
    manufacturer = (manufacturer or "").strip()
    supplier = (supplier or "").strip()
    if not raw_material or not manufacturer:
        return {"matches": []}

    roles = set(frappe.get_roles(frappe.session.user))
    staff_roles = {"Evaluation", "SB User", "Certificate Manager", "Admin", "System Manager", "Administrator"}

    conditions = [
        "q.docstatus < 2",
        "q.workflow_state NOT IN ('Draft', 'Delisted')",
        "LOWER(TRIM(IFNULL(q.raw_material, ''))) = LOWER(TRIM(%(raw_material)s))",
        "LOWER(TRIM(IFNULL(q.manufacturer, ''))) = LOWER(TRIM(%(manufacturer)s))",
    ]
    params = {"raw_material": raw_material, "manufacturer": manufacturer}

    if supplier:
        conditions.append("LOWER(TRIM(IFNULL(q.supplier, ''))) = LOWER(TRIM(%(supplier)s))")
        params["supplier"] = supplier

    if exclude_name:
        conditions.append("q.name != %(exclude_name)s")
        params["exclude_name"] = exclude_name

    if not staff_roles.intersection(roles):
        conditions.append("q.owner = %(user)s")
        params["user"] = frappe.session.user

    matches = frappe.db.sql(f"""
        SELECT
            q.name,
            q.raw_material,
            q.supplier,
            q.manufacturer,
            q.workflow_state,
            q.client_name,
            q.owner,
            q.modified
        FROM `tabQuery` q
        WHERE {' AND '.join(conditions)}
        ORDER BY q.modified DESC
        LIMIT 5
    """, params, as_dict=True)

    for match in matches:
        match["documents"] = frappe.get_all(
            "Documents",
            filters={"parent": match.name, "parenttype": "Query"},
            fields=["documents", "issue_date", "expiry_date", "attachment", "idx"],
            order_by="idx asc",
            ignore_permissions=True,
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

