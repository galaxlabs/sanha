import frappe
from frappe.model.document import Document
from frappe.utils import cint
from uuid import uuid4


class AIProviderProfile(Document):
    def validate(self):
        from sanha.api.ai_providers import validate_model
        self.model = str(self.model or "").strip().removeprefix("models/")
        if self.enabled or self.model:
            validate_model(self.provider, self.model)
        if self.enabled and not (self.get("api_key") and self.api_key != "********") and not self.get_password("api_key", raise_exception=False):
            frappe.throw("Save an API key before enabling this connection.")
        if not self.use_for_text and not self.use_for_vision:
            frappe.throw("Choose at least one task for this connection.")
        if not 128 <= cint(self.max_output_tokens) <= 8192:
            frappe.throw("Maximum output tokens must be between 128 and 8192.")
        if not 0 <= cint(self.daily_token_budget) <= 100000000:
            frappe.throw("Daily token budget must be between 0 and 100000000.")
        if not 0 <= cint(self.priority) <= 999:
            frappe.throw("Priority must be between 0 and 999.")
        if self.get("api_key") and self.api_key != "********":
            self.credential_revision = uuid4().hex
