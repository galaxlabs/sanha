# Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.utils import random_string
from frappe.utils import get_fullname
from datetime import datetime ,timedelta
from frappe.model.document import Document
from frappe.utils import today, add_days

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
            "location": self.client_code,
            "phone": self.telephone,
            "mobile_no": self.contact_no,          
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
    


# @frappe.whitelist()
# def update_status():
#     clients = frappe.get_all('Client', filters={'docstatus': 1})
#     for client in clients:
#         doc = frappe.get_doc('Client', client.name)
#         days_until_expiry = (doc.certified_expiry - frappe.utils.today()).days

#         if days_until_expiry > 60:
#             doc.status = 'Expiring Soon'
#         elif 30 <= days_until_expiry <= 60:
#             doc.status = 'Expiring'
#         elif 0 <= days_until_expiry < 30:
#             doc.status = 'Expired'
#         else:
#             doc.status = 'Valid'
        
#         doc.save()

#     frappe.msgprint(_('Status updated successfully.'), indicator='green')    
# @frappe.whitelist()

# def get_user_info():
#     # Get the session user's email
#     session_email = frappe.session.user
#     # Fetch relevant data from the Client doctype
#     client_data = frappe.get_all("Client", filters={"email": session_email}, fields=["*"])
#     if not client_data:
#         return None  # No client data found for the session user
    
#     client_name = client_data[0].get("client_name")
#     # Fetch relevant data from the User doctype
#     user_data = frappe.get_all("User", filters={"email": session_email, "full_name": client_name}, fields=["*"])
#     if not user_data:
#         return None  # No user data found for the session user
    
#     # Combine and return both sets of data
#     return {"client_data": client_data[0], "user_data": user_data[0]}
