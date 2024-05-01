# Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime ,timedelta
from frappe.model.document import Document

class Client(Document):
    def after_insert(self):
        # After inserting a new client, create a user
        user_doc = self.create_user()
        if user_doc:
            self.assign_user_roles(user_doc)

    def create_user(self):
        # Create a user based on client data
        user_doc = frappe.new_doc("User")
        user_doc.update({
            "full_name": self.business_name,
            "email": self.email,
            "first_name": self.client_name,
            "phone": self.phone,            
            # Add other relevant fields from the client DocType to the user
        })

        try:
            user_doc.insert(ignore_permissions=True)
            # Calculate expiry details and color indicator
            self.calculate_expiry_details(client_doc)
            return user_doc
        except Exception as e:
            frappe.log_error(f"Error creating user: {e}", _("Create User Error"))
            return None
            
    def assign_user_roles(self, user_doc):
        # Assign roles to the user
        frappe.add_role(user_doc.name, "Client")  # Assign 'Client' role

        # Set role profile and module profile for the user
        user_doc.role_profile_name = "Client"  # Set role profile to 'Client'
        user_doc.module_profile_name = "Client"  # Set module profile to 'Client'

        # Set user type as 'System User'
        user_doc.user_type = "System User"
        # Save the user document with updated properties
        user_doc.save()