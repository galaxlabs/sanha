# Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, add_days
from frappe.email.queue import flush

# Transitions that count as a client "submission"
CLIENT_SUBMIT_TRANSITIONS = {
    ("Draft", "Submitted"),
    ("Returned", "Submitted to SB"),
    ("Delisted", "Submitted"),
}

def is_client_user() -> bool:
    # Keep this tight to only your real client role name
    return "Client" in set(frappe.get_roles(frappe.session.user))

class Query(Document):
    def validate(self):
        # Determine previous and current workflow states
        previous_state = "Draft"
        if frappe.db.exists(self.doctype, self.name):
            previous_state = frappe.db.get_value(self.doctype, self.name, "workflow_state") or "Draft"
        current_state = self.workflow_state or "Draft"

        # Strict only for client submit-type transitions
        strict = is_client_user() and ((previous_state, current_state) in CLIENT_SUBMIT_TRANSITIONS)

        # Optional: quick debug to server log (remove after testing)
        frappe.logger().info(
            f"[Query.validate] user={frappe.session.user} prev={previous_state} curr={current_state} strict={strict}"
        )

        self.run_validations(strict)

    # ---------------- main runner ----------------
    def run_validations(self, strict: bool):
        self.validate_documents_table(strict)
        if strict:
            self.validate_workflow_rules()

    # ---------------- child table validation ----------------
    def validate_documents_table(self, strict: bool):
        """
        Non-strict (draft/staff actions): allow empty/partial docs (nudge only).
        Strict (client submit transitions): enforce rows, attachments, dates, MSDS, halal rules.
        """
        # If the child table field doesn't exist at all, skip
        if "documents" not in self.meta.get_valid_columns():
            return

        docs = self.get("documents") or []

        # Require at least one row only in strict mode
        if not docs:
            if strict:
                frappe.throw("You must add at least one document before submitting.")
            else:
                frappe.msgprint("Tip: add your required documents before submit.", alert=True)
                return

        required_documents = [
            "TDS", "SDS", "Product Spec", "PDS",
            "Lab Sample Report", "Halal Questionnaire",
            "Declaration", "Halal Certificate", "MSDS", "COA"
        ]

        today = getdate(nowdate())
        sixty_days_later = add_days(today, 60)
        expiring_documents = []
        found_msds = False

        for i, row in enumerate(docs, start=1):
            docname = (row.documents or "").strip() or "(No Type)"

            # Attachment required only in strict mode
            if strict and not row.attachment:
                frappe.throw(f"Row {i}: Attachment is required for {docname}.")

            # Issue Date required for required docs in strict mode
            if strict and (docname in required_documents) and not row.issue_date:
                frappe.throw(f"Row {i}: Issue Date is required for {docname}.")

            # MSDS rules
            if docname == "MSDS":
                found_msds = True
                if strict and not row.issue_date:
                    frappe.throw(f"Row {i}: MSDS requires Issue Date.")

            # Halal Certificate rules (strict only)
            if docname == "Halal Certificate" and strict:
                if not row.issue_date or not row.expiry_date:
                    frappe.throw(
                        f"Row {i}: Halal Certificate requires both Issue Date and Expiry Date."
                    )
                if getdate(row.expiry_date) <= getdate(row.issue_date):
                    frappe.throw(
                        f"Row {i}: Expiry Date must be after Issue Date for Halal Certificate."
                    )
                if getdate(row.expiry_date) < today:
                    frappe.throw(f"Row {i}: Halal Certificate expired on {row.expiry_date}.")
                if today <= getdate(row.expiry_date) <= sixty_days_later:
                    remaining = (getdate(row.expiry_date) - today).days
                    expiring_documents.append({
                        "name": docname,
                        "expiry_date": row.expiry_date,
                        "remaining_days": remaining
                    })

            # Declaration rule
            if strict and docname == "Declaration" and not row.issue_date:
                frappe.throw(f"Row {i}: Declaration requires Issue Date.")

        # Summary-level checks (strict only)
        if strict and not found_msds:
            frappe.throw("MSDS document is mandatory.")

        self.expiring_documents = expiring_documents

    # ---------------- submission-only extras ----------------
    def validate_workflow_rules(self):
        # Example: email warnings for soon-to-expire docs on submit
        if getattr(self, "expiring_documents", []):
            self.send_query_notification(self.expiring_documents)

    def send_query_notification(self, expiring_documents):
        if not expiring_documents:
            return
        expiring_list = "\n".join(
            f"- {d['name']} (expires in {d['remaining_days']} days, on {d['expiry_date']})"
            for d in expiring_documents
        )
        message = f"""
        <p>The following documents are nearing expiry:</p>
        <pre>{frappe.utils.escape_html(expiring_list)}</pre>
        """
        recipients = ["karachi@sanha.org.pk", "evaluation@sanha.org.pk"]
        frappe.sendmail(
            recipients=recipients,
            subject=f"[SANHA] Expiring Document Alert for Query {self.name}",
            message=message
        )
        flush()


# import frappe
# from frappe.model.document import Document
# from frappe.utils import getdate, nowdate, add_days
# from frappe.email.queue import flush

# SUBMITTED_STATES = ["Submitted"]
                    

# class Query(Document):

#     # Enforce strict checks when user clicks a workflow action
#     def before_workflow_action(self, action):
#         self._strict = True
#         self._run_validations(strict=True)

#     def validate(self):
#         # In normal save, decide strictness based on workflow transition
#         self._strict = self.is_strict_mode()
#         self._run_validations(strict=self._strict)

#     # ---------- strict-mode detector ----------
#     def is_strict_mode(self) -> bool:
#         """Strict mode only when transitioning Draft → a submitted/closed state."""
#         previous_state = "Draft"
#         if frappe.db.exists("Query", self.name):
#             previous_state = frappe.db.get_value("Query", self.name, "workflow_state") or "Draft"
#         current_state = self.workflow_state or "Draft"
#         return previous_state == "Draft" and current_state in SUBMITTED_STATES

#     # ---------- main runner ----------
#     def _run_validations(self, strict: bool):
#         self.validate_documents_table(strict)
#         if strict:
#             self.validate_workflow_rules()  # extra checks on submit (e.g., attachments present for all rows)

#     # ---------- child table validation ----------
#     def validate_documents_table(self, strict: bool):
#         """
#         Draft (strict=False):
#           - Allow empty/partial documents; do not block.
#         Submit (strict=True):
#           - Enforce: at least one row, MSDS present, attachments, dates, etc.
#         """
#         # If no child table bound at all, bail out
#         if not self.get("documents"):
#             return

#         # In Draft, allow empty table. In Submit, require at least 1 row.
#         if (not self.documents or len(self.documents) == 0):
#             if strict:
#                 frappe.throw("You must add at least one document before submitting.")
#             else:
#                 # Optional gentle nudge
#                 frappe.msgprint("Tip: add your required documents before submit.", alert=True)
#                 return

#         required_documents = [
#             "TDS", "SDS", "Product Spec", "PDS",
#             "Lab Sample Report", "Halal Questionnaire",
#             "Declaration", "Halal Certificate", "MSDS", "COA"
#         ]

#         today = getdate(nowdate())
#         sixty_days_later = add_days(today, 60)
#         expiring_documents = []

#         found_msd = False
#         found_halal_certificate = False

#         for i, row in enumerate(self.documents, start=1):
#             docname = row.documents or "(No Type)"

#             # --- Attachment rule ---
#             if strict:
#                 if not row.attachment:
#                     frappe.throw(f"Row {i}: Attachment is required for {docname}.")
#             else:
#                 # Draft: do not block; optionally warn
#                 if not row.attachment and docname in required_documents:
#                     # mild hint only; no throw
#                     pass

#             # --- Issue date rule for required documents ---
#             if strict:
#                 if docname in required_documents and not row.issue_date:
#                     frappe.throw(f"Row {i}: Issue Date is required for {docname}.")

#             # --- MSDS presence & rule ---
#             if docname == "MSDS":
#                 found_msd = True
#                 if strict and not row.issue_date:
#                     frappe.throw(f"Row {i}: MSDS requires Issue Date.")

#             # --- Halal Certificate rules ---
#             if docname == "Halal Certificate":
#                 found_halal_certificate = True
#                 if strict:
#                     if not row.issue_date or not row.expiry_date:
#                         frappe.throw(f"Row {i}: Halal Certificate requires both Issue Date and Expiry Date.")
#                     if getdate(row.expiry_date) <= getdate(row.issue_date):
#                         frappe.throw(f"Row {i}: Expiry Date must be after Issue Date for Halal Certificate.")
#                     if getdate(row.expiry_date) < today:
#                         frappe.throw(f"Row {i}: Halal Certificate expired on {row.expiry_date}.")
#                     if today <= getdate(row.expiry_date) <= sixty_days_later:
#                         remaining = (getdate(row.expiry_date) - today).days
#                         expiring_documents.append({
#                             "name": docname,
#                             "expiry_date": row.expiry_date,
#                             "remaining_days": remaining
#                         })

#             # --- Declaration rule ---
#             if strict and docname == "Declaration" and not row.issue_date:
#                 frappe.throw(f"Row {i}: Declaration requires Issue Date.")

#         # --- summary-level checks (strict only) ---
#         if strict:
#             if not found_msd:
#                 frappe.throw("MSDS document is mandatory.")
#             # (found_halal_certificate implies there is at least one Halal row already)
#             # No need for the old self-contradictory check here.

#         # Save for optional notifications in workflow step
#         self.expiring_documents = expiring_documents

#     # ---------- submission-only checks & optional emails ----------
#     def validate_workflow_rules(self):
#         """Extra checks during submit transition. Also handles expiry notifications."""
#         # All strict row checks already ran; add any list-level checks here if needed.
#         if getattr(self, "expiring_documents", []):
#             self.send_query_notification(self.expiring_documents)

#     def send_query_notification(self, expiring_documents):
#         if not expiring_documents:
#             return
#         expiring_list = "\n".join(
#             f"- {d['name']} (expires in {d['remaining_days']} days, on {d['expiry_date']})"
#             for d in expiring_documents
#         )
#         message = f"""
#         <p>The following documents are nearing expiry:</p>
#         <pre>{frappe.utils.escape_html(expiring_list)}</pre>
#         """
#         recipients = ["karachi@sanha.org.pk", "evaluation@sanha.org.pk"]
#         frappe.sendmail(
#             recipients=recipients,
#             subject=f"[SANHA] Expiring Document Alert for Query {self.name}",
#             message=message
#         )
#         flush()

