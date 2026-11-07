from frappe.model.document import Document


class EntityCleanupSettings(Document):
    def validate(self):
        self.daily_limit = 10
