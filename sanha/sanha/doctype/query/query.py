# Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, add_days
from frappe.email.queue import flush


class Query(Document):
    def validate(self):
        # 1. Figure out if current user is a Client
        user_roles = frappe.get_roles(frappe.session.user)
        is_client = "Client" in user_roles

        # 2. Get the previous workflow_state from DB (before this save)
        previous_state = "Draft"
        if frappe.db.exists("Query", self.name):
            previous_state = frappe.db.get_value("Query", self.name, "workflow_state") or "Draft"

        # 3. Get the new workflow_state (what user is trying to set now)
        current_state = self.workflow_state or "Draft"

        # 4. Which states count as "submitted/finalized"
        submitted_states = ["Submitted"]  # add more like "Final Approval" later if you want

        # 5. We ONLY enforce in this exact situation:
        #    - user has role Client
        #    - document is moving from Draft -> Submitted
        is_client_submitting_now = (
            is_client
            and previous_state == "Draft"
            and current_state in submitted_states
        )

        # 6. If it's not that situation:
        #    - Draft save? allowed.
        #    - Admin submitting? allowed.
        #    - Return (Submitted -> Draft)? allowed.
        if not is_client_submitting_now:
            return

        # 7. Now we are in Draft -> Submitted by a Client.
        #    Enforce: must have at least one row in documents table.
        if not self.documents or len(self.documents) == 0:
            frappe.throw("You must add at least one document before submission.")



# class Query(Document):

    # def validate(self):
    #     if not self.get("documents"):
    #         return

    #     if not self.documents:
    #         frappe.throw('Please add documents before saving.')

    #     required_documents = ["TDS", "SDS", "Product Spec", "PDS", "Lab Sample Report", "Halal Questionnaire", "Declaration", "Halal Certificate", "MSDS", "COA"]
    #     found_msd = False
    #     found_halal_certificate = False
        
    #     for row in self.documents:
    #         if row.documents in required_documents and not row.issue_date and not row.attachment:
    #             frappe.throw(f"Issue Date and Attachment are required for {row.documents}.")

    #         if row.documents in required_documents and not row.issue_date:
    #             frappe.throw(f"Issue Date is required for {row.documents}.")

    #         if not row.attachment:
    #             frappe.throw(f"Attachment is required for {row.documents}.")

    #         if row.documents == "MSDS":
    #             found_msds = True
    #             if not row.issue_date:
    #                 frappe.throw("Issue Date and Attachment are required for MSDS.")

    #         if row.documents == "Halal Certificate":
    #             found_halal_certificate = True
    #             if not row.issue_date or not row.expiry_date:
    #                 frappe.throw("Halal Certificate requires both Issue Date and Expiry Date.")

    #             if not row.attachment:
    #                 frappe.throw("Attachment is required for Halal Certificate.")


    #     if not found_msds:
    #         frappe.throw("MSDS is mandatory.")

    #     if found_halal_certificate and not any(doc.documents == "Halal Certificate" for doc in self.documents):
    #         frappe.throw("Halal Certificate requires Expiry Date.")
            
    # def validate(self):
    #     # Get previous state from DB (if exists)
    #     previous_state = "Draft"
    #     if frappe.db.exists("Query", self.name):
    #         previous_state = frappe.db.get_value("Query", self.name, "workflow_state") or "Draft"

    #     # Define workflow states considered as "submission"
    #     submitted_states = ["Submitted"]

    #     # Block transition from Draft → Submitted if no documents
    #     if previous_state == "Draft" and self.workflow_state in submitted_states:
    #         if not self.documents or len(self.documents) == 0:
    #             frappe.throw("You must attach at least one document before submitting.")

    #         for i, row in enumerate(self.documents):
    #             if not row.attachment:
    #                 frappe.throw(f"Row {i+1}: Attachment is required in the Documents table.")

    
    
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

