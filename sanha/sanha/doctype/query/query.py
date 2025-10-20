# Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, add_days
from frappe.email.queue import flush


class Query(Document):

    def validate(self):
        if not self.get("documents"):
            return

        if not self.documents:
            frappe.throw('Please add documents before saving.')

        required_documents = ["TDS", "SDS", "Product Spec", "PDS", "Lab Sample Report", "Halal Questionnaire", "Declaration", "Halal Certificate", "MSDS", "COA"]
        found_msd = False
        found_halal_certificate = False
        
        for row in self.documents:
            if row.documents in required_documents and not row.issue_date and not row.attachment:
                frappe.throw(f"Issue Date and Attachment are required for {row.documents}.")

            if row.documents in required_documents and not row.issue_date:
                frappe.throw(f"Issue Date is required for {row.documents}.")

            if not row.attachment:
                frappe.throw(f"Attachment is required for {row.documents}.")

            if row.documents == "MSDS":
                found_msd = True
                if not row.issue_date:
                    frappe.throw("Issue Date and Attachment are required for MSDS.")

            if row.documents == "Halal Certificate":
                found_halal_certificate = True
                if not row.issue_date or not row.expiry_date:
                    frappe.throw("Halal Certificate requires both Issue Date and Expiry Date.")

                if not row.attachment:
                    frappe.throw("Attachment is required for Halal Certificate.")


        if not found_msd:
            frappe.throw("MSDS is mandatory.")

        if found_halal_certificate and not any(doc.documents == "Halal Certificate" for doc in self.documents):
            frappe.throw("Halal Certificate requires Expiry Date.")
            
    def validate(self):
        # Get previous state from DB (if exists)
        previous_state = "Draft"
        if frappe.db.exists("Query", self.name):
            previous_state = frappe.db.get_value("Query", self.name, "workflow_state") or "Draft"

        # Define workflow states considered as "submission"
        submitted_states = ["Submitted", "Final Approval", "Closed"]

        # Block transition from Draft → Submitted if no documents
        if previous_state == "Draft" and self.workflow_state in submitted_states:
            if not self.documents or len(self.documents) == 0:
                frappe.throw("You must attach at least one document before submitting.")

            for i, row in enumerate(self.documents):
                if not row.attachment:
                    frappe.throw(f"Row {i+1}: Attachment is required in the Documents table.")    


# class Query(Document):
#     def validate(self):
#         """Main validation logic for Query documents."""
#         self.validate_documents_table()
#         self.validate_workflow_rules()

#     # -------------------------------------------------------------
#     # 1️⃣ Validate child documents
#     # -------------------------------------------------------------
#     def validate_documents_table(self):
#         if not self.get("documents") or len(self.documents) == 0:
#             frappe.throw("Please add at least one document before saving.")

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
#             # --- Universal attachment check ---
#             if not row.attachment:
#                 frappe.throw(f"Row {i}: Attachment is required for {row.documents}.")

#             # --- Common issue_date check ---
#             if row.documents in required_documents and not row.issue_date:
#                 frappe.throw(f"Row {i}: Issue Date is required for {row.documents}.")

#             # --- MSDS rule ---
#             if row.documents == "MSDS":
#                 found_msd = True
#                 if not row.issue_date:
#                     frappe.throw(f"Row {i}: MSDS requires Issue Date.")

#             # --- Halal Certificate rules ---
#             if row.documents == "Halal Certificate":
#                 found_halal_certificate = True
#                 if not row.issue_date or not row.expiry_date:
#                     frappe.throw(f"Row {i}: Halal Certificate requires both Issue Date and Expiry Date.")
#                 elif getdate(row.expiry_date) <= getdate(row.issue_date):
#                     frappe.throw(f"Row {i}: Expiry Date must be after Issue Date for Halal Certificate.")
#                 elif getdate(row.expiry_date) < today:
#                     frappe.throw(f"Row {i}: Halal Certificate expired on {row.expiry_date}.")
#                 elif today <= getdate(row.expiry_date) <= sixty_days_later:
#                     remaining = (getdate(row.expiry_date) - today).days
#                     expiring_documents.append({
#                         "name": row.documents,
#                         "expiry_date": row.expiry_date,
#                         "remaining_days": remaining
#                     })

#             # --- Declaration rule ---
#             if row.documents == "Declaration" and not row.issue_date:
#                 frappe.throw(f"Row {i}: Declaration requires Issue Date.")

#         # --- Summary-level checks ---
#         if not found_msd:
#             frappe.throw("MSDS document is mandatory.")
#         if found_halal_certificate and not any(doc.documents == "Halal Certificate" for doc in self.documents):
#             frappe.throw("Halal Certificate requires Expiry Date.")

#         # Store for later notification use
#         self.expiring_documents = expiring_documents

#     # -------------------------------------------------------------
#     # 2️⃣ Workflow submission check
#     # -------------------------------------------------------------
#     def validate_workflow_rules(self):
#         """Extra validation when transitioning from Draft → Submitted."""
#         previous_state = frappe.db.get_value("Query", self.name, "workflow_state") if frappe.db.exists("Query", self.name) else "Draft"
#         current_state = self.workflow_state or "Draft"
        

#         if previous_state == "Draft" and current_state in submitted_states:
#             if not self.documents or len(self.documents) == 0:
#                 frappe.throw("You must attach at least one document before submitting.")

#             for i, row in enumerate(self.documents, start=1):
#                 if not row.attachment:
#                     frappe.throw(f"Row {i}: Attachment is required before submitting.")


