# Copyright (c) 2024, Sanha Halal Pakistan and contributors
# For license information, please see license.txt

import re
from urllib.parse import unquote

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import strip_html
from frappe.utils.user import get_system_managers
from frappe.utils import add_to_date, now_datetime
from sanha.api.auth import _find_client
from sanha.auto_submission import auto_submission_enabled


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
STAFF_ROLES = {"Evaluation", "SB User", "Certificate Manager", "Admin", "System Manager", "Administrator"}
CLIENT_EDITABLE_STATES = {"Draft", "Returned"}
CLIENT_SUBMISSION_TRANSITIONS = {("Draft", "Submitted"), ("Returned", "Submitted to SB")}
ISSUE_DATE_REQUIRED_DOCUMENTS = {
    "MSDS",
    "Halal Declaration",
    "TDS",
    "SDS",
    "Product Spec",
    "PDS",
    "Lab Sample Report",
    "Halal Questionnaire",
    "Declaration",
    "Halal Certificate",
}
EXPIRY_DATE_REQUIRED_DOCUMENTS = {"Halal Certificate"}


def _client_scope(user):
    roles = set(frappe.get_roles(user))
    if "Client" not in roles or STAFF_ROLES.intersection(roles):
        return None

    email = frappe.db.get_value("User", user, "email")
    client = _find_client(user, email)
    return client.get("name") if client else ""


def get_permission_query_conditions(user=None):
    """Limit pure Client accounts to records for their linked Client."""
    client_name = _client_scope(user or frappe.session.user)
    if client_name is None:
        return None
    return "`tabQuery`.client_name = {0}".format(frappe.db.escape(client_name))


def has_permission(doc, user=None, ptype=None, permission_type=None):
    client_name = _client_scope(user or frappe.session.user)
    if client_name is None:
        return True
    if not client_name:
        return False
    if ptype == "create" and not doc.client_name:
        doc.client_name = client_name
    return doc.client_name == client_name


def _same_value(left, right):
    return str(left or "") == str(right or "")


PLACEHOLDER_FILE = re.compile(r"(no[\s_-]+[\w\s_-]{0,30}[\s_-]+found|not[\s_-]+found|placeholder|dummy|not[\s_-]+available|missing)", re.IGNORECASE)


def is_placeholder_file(attachment):
    name = unquote((attachment or "").rsplit("/", 1)[-1])
    return bool(PLACEHOLDER_FILE.search(name))


class Query(Document):
    def before_validate(self):
        # Provenance is assigned only by the scheduler after successful workflow.
        # Read-only UI fields alone do not prevent forged REST updates.
        provenance = ("was_auto_submitted", "auto_submitted_at", "auto_submitted_by")
        saved = frappe.db.get_value("Query", self.name, list(provenance), as_dict=True) if not self.is_new() else None
        for field in provenance:
            self.set(field, saved.get(field) if saved else (0 if field == "was_auto_submitted" else None))
        # Persist partially completed drafts, including unfinished document rows.
        self.flags.ignore_mandatory = (self.workflow_state or "Draft") == "Draft"

    def validate(self):
        self.validate_client_edit_lock()
        self.validate_duplicate_document_attachments()
        self.validate_client_document_rows()
        self.validate_client_submission_documents()
        old = self.get_doc_before_save()
        if (self.workflow_state or "Draft") != "Draft" and (not old or old.workflow_state in CLIENT_EDITABLE_STATES):
            self.validate_submission_ready()
        self.schedule_auto_submission()

    def validate_submission_ready(self):
        if not (self.raw_material or "").strip() or not self.query_types:
            frappe.throw("Raw Material and Query Type are required before submission.")
        self.validate_document_rows(require_documents=True)

    def schedule_auto_submission(self):
        self.auto_submit_after = None
        self.auto_submit_user = None
        self.auto_submit_error = None
        roles = set(frappe.get_roles())
        if auto_submission_enabled() and (self.workflow_state or "Draft") == "Draft" and "Client" in roles and not STAFF_ROLES.intersection(roles):
            self.auto_submit_after = add_to_date(now_datetime(), minutes=5)
            self.auto_submit_user = frappe.session.user

    def on_update(self):
        self.relink_query_attachment_files()

    def validate_client_edit_lock(self):
        if self.is_new():
            return

        roles = set(frappe.get_roles(frappe.session.user))
        if "Client" not in roles or STAFF_ROLES.intersection(roles):
            return

        previous_state = frappe.db.get_value("Query", self.name, "workflow_state") or "Draft"
        if previous_state in CLIENT_EDITABLE_STATES:
            return

        previous = frappe.get_doc("Query", self.name)
        for field in LOCKED_PARENT_FIELDS:
            if not _same_value(self.get(field), previous.get(field)):
                frappe.throw("Submitted queries are locked for client users.", frappe.PermissionError)

        existing_rows = {row.name: row for row in previous.get("documents") or []}
        submitted_rows = {row.name: row for row in self.get("documents") or [] if row.name in existing_rows}

        if set(existing_rows) - set(submitted_rows):
            frappe.throw("Existing document rows cannot be removed after submission.", frappe.PermissionError)

        if any(row.name not in existing_rows for row in self.get("documents") or []):
            frappe.throw("Documents can only be added in Draft or Returned state.", frappe.PermissionError)

        for row_name, old_row in existing_rows.items():
            new_row = submitted_rows[row_name]
            for field in DOCUMENT_FIELDS:
                if not _same_value(new_row.get(field), old_row.get(field)):
                    frappe.throw("Existing document rows cannot be changed outside Draft or Returned state.", frappe.PermissionError)

    def validate_duplicate_document_attachments(self):
        seen = set()
        for row in self.get("documents") or []:
            attachment = (row.attachment or "").strip()
            if not attachment:
                continue
            if attachment in seen:
                frappe.throw(f"Duplicate attachment found in Documents table: {attachment}")
            seen.add(attachment)

    def validate_client_document_rows(self):
        roles = set(frappe.get_roles(frappe.session.user))
        current_state = self.workflow_state or "Draft"
        if "Client" not in roles or current_state == "Draft" or current_state not in CLIENT_EDITABLE_STATES:
            return

        self.validate_document_rows()

    def validate_document_rows(self, require_documents=False):
        rows = self.get("documents") or []
        if require_documents and not rows:
            frappe.throw("You must add at least one document before submission.")

        for index, row in enumerate(rows, start=1):
            if not row.documents:
                frappe.throw(f"Row #{index}: Document Type is required.")
            if not row.attachment:
                frappe.throw(f"Row #{index}: Please attach a file.")
            if is_placeholder_file(row.attachment):
                frappe.throw(f"Row #{index}: The attached file looks like a placeholder (\"{row.attachment.rsplit('/', 1)[-1]}\"). Please upload the actual document.")
            if row.documents in ISSUE_DATE_REQUIRED_DOCUMENTS and not row.issue_date:
                frappe.throw(f"Row #{index}: Issue Date is required for {row.documents}.")
            if row.documents in EXPIRY_DATE_REQUIRED_DOCUMENTS and not row.expiry_date:
                frappe.throw(f"Row #{index}: Expiry Date is required for {row.documents}.")

    def validate_client_submission_documents(self):
        user_roles = frappe.get_roles(frappe.session.user)
        is_client = "Client" in user_roles

        previous_state = "Draft"
        if frappe.db.exists("Query", self.name):
            previous_state = frappe.db.get_value("Query", self.name, "workflow_state") or "Draft"

        current_state = self.workflow_state or "Draft"
        is_client_submitting_now = is_client and (previous_state, current_state) in CLIENT_SUBMISSION_TRANSITIONS

        if not is_client_submitting_now:
            return

        self.validate_document_rows(require_documents=True)

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


def notify_system_managers_on_client_query_comment(doc, method=None):
    if (
        doc.comment_type != "Comment"
        or doc.reference_doctype != "Query"
        or not doc.reference_name
    ):
        return

    actor = doc.comment_email or doc.owner or frappe.session.user
    roles = set(frappe.get_roles(actor))
    if "Client" not in roles or STAFF_ROLES.intersection(roles):
        return

    actor_name = frappe.db.get_value("User", actor, "full_name") or actor
    subject = _("{0} commented on Query {1}").format(actor_name, doc.reference_name)
    content = strip_html(doc.content or "").strip()

    for manager in get_system_managers(only_name=True):
        notification = frappe.new_doc("Notification Log")
        notification.update(
            {
                "type": "Alert",
                "for_user": manager,
                "from_user": actor,
                "document_type": "Query",
                "document_name": doc.reference_name,
                "subject": subject,
                "email_content": content,
                "read": 0,
            }
        )
        notification.insert(ignore_permissions=True)


@frappe.whitelist()
def find_similar_query(raw_material: str | None = None,
                    manufacturer: str | None = None,
                    supplier: str | None = None,
                    exclude_name: str | None = None):
    """Return decided, permission-scoped same material/manufacturer references."""
    from sanha.api.decision_support import final_decisions
    matches, count = final_decisions(raw_material, manufacturer, supplier, exclude_name, require_manufacturer=True)
    return {"matches": matches[:5], "total": count, "historical_file_reads": 0}


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
    scope = _client_scope(user)
    if scope is not None:
        filters["client_name"] = scope
    records = frappe.get_list("Query", filters=filters, fields=["name", "owner", "modified", "client_name"], limit_page_length=0)
    records_sorted = sorted(records, key=lambda x: x["modified"])
    return records_sorted[1:]  # skip the first (original) entry

