import frappe
from frappe.model.document import Document


class EntityNameAlias(Document):
    def validate(self):
        from sanha.api.decision_support import company_key, real_company
        if not real_company(self.original_name) or not real_company(self.canonical_name):
            frappe.throw("Company aliases require actual company names, not placeholders.")
        self.normalized_name = company_key(self.original_name)
        if self.verified and not all((self.identity_key, self.source_url, self.evidence_json)):
            frappe.throw("Verified aliases require identity and public/document evidence.")
