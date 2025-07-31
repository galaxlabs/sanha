# # Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# # For license information, please see license.txt
import email
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.permissions import add_user_permission
from frappe.utils import getdate, today



class Client(Document):
	def after_insert(self):
		user_doc = self.create_user()
		if user_doc:
			self.assign_user_roles(user_doc)
			self.assign_user_permissions(user_doc)

	def on_update(self):
		self.sync_user()

	def create_user(self):
		if not self.email:
			frappe.throw(_("Email is required to create a user."))

		user_doc = None

		# Check if user exists
		if frappe.db.exists("User", self.email):
			user_doc = frappe.get_doc("User", self.email)
			frappe.msgprint(f"User already exists: {self.email}")
		else:
			full_name = " ".join(filter(None, [self.client_name, self.business_name]))
			user_doc = frappe.get_doc({
				"doctype": "User",
				"email": self.email,
				"first_name": self.client_name,
				"last_name": self.business_name,
				"enabled": 1,
				"allowed_in_mentions": 0,
				"send_welcome_email": 0,
			})

			try:
				user_doc.insert(ignore_permissions=True)
				# Assign profiles right after insert
				user_doc.module_profile = "Client"
				user_doc.role_profile_name = "Client"
				user_doc.save(ignore_permissions=True)
				frappe.msgprint(f"User created and role/module profile assigned for: {self.email}")
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), "Client User Creation Failed")
				return None

		return user_doc

	def assign_user_roles(self, user_doc):
		client_role = "Client"
		if client_role not in [role.role for role in user_doc.get("roles")]:
			user_doc.append("roles", {"role": client_role})
			user_doc.save(ignore_permissions=True)
			frappe.msgprint(f"Role '{client_role}' assigned to user.")

	def assign_user_permissions(self, user_doc):
		email = user_doc.email

		# Assign permission to view their own client record

		# Assign permission to view the Client doctype
		add_user_permission("Client", self.name, email, is_default=True, ignore_permissions=True)

		add_user_permission("User", email, email, ignore_permissions=True)

		frappe.msgprint("All user permissions assigned to client.")

	def sync_user(self):
		if not self.email or not frappe.db.exists("User", self.email):
			frappe.msgprint("No linked user to sync.")
			return

		user_doc = frappe.get_doc("User", self.email)
		user_doc.first_name = self.client_name
		user_doc.last_name = self.business_name
		user_doc.allowed_in_mentions = 0
		user_doc.module_profile = "Client"
		user_doc.role_profile_name = "Client"
		user_doc.save(ignore_permissions=True)
		frappe.msgprint("User synced with latest Client data.")


def update_all_client_statuses():
	"""Daily job to update status of all Clients based on certified_expiry"""
	today_date = getdate(today())
	clients = frappe.get_all("Client", fields=["name", "certified_expiry", "status"])

	for client in clients:
		doc = frappe.get_doc("Client", client.name)

		if not doc.certified_expiry:
			continue  # Skip if no expiry date

		days_remaining = (getdate(doc.certified_expiry) - today_date).days

		# Decide new status
		if days_remaining < 0:
			new_status = "Expired"
		elif days_remaining <= 60:
			new_status = f"{days_remaining} Days Remaining"
		else:
			new_status = "Valid"

		if doc.status != new_status:
			doc.db_set("status", new_status)


# import frappe
# from frappe import _
# from frappe.utils import random_string
# from frappe.utils import get_fullname
# from datetime import datetime ,timedelta
# from frappe.model.document import Document
# from frappe.utils import today, add_days

# class Client(Document):
#     def after_insert(self):
#         # After inserting a new client, create a user
#         user_doc = self.create_user()
#         if user_doc:
#             self.assign_user_roles(user_doc)

#     def create_user(self):
#         # Create a user based on client data
#         user_doc = frappe.new_doc("User")
#         # Set the user ID as the full name
#         full_name = " ".join(filter(None, [self.client_name, self.business_name]))
#         user_doc = frappe.new_doc("User")
#         user_doc.update({
#             "first_name": self.client_name,
#             "last_name": self.business_name,
#             "email": self.email,
#             "location": self.client_code,
#             "phone": self.telephone,
#             "mobile_no": self.contact_no,
#             "name": full_name,  # Set user ID as the full name
#             # Add other relevant fields from the client DocType to the user
#         })

#         try:
#             user_doc.insert(ignore_permissions=True)
#             # Calculate expiry details and color indicator
#             self.calculate_expiry_details(client_doc)
#             return user_doc
#         except Exception as e:
#             frappe.log_error(f"Error creating user: {e}", _("Create User Error"))
#             return None

# class Client(Document):
#     def after_insert(self):
#         # After inserting a new client, create a user
#         user_doc = self.create_user()
#         if user_doc:
#             self.assign_user_roles(user_doc)

#     def create_user(self):
#         # Create a user based on client data
#         user_doc = frappe.new_doc("User")
#         # Set the user ID as the full name
#         full_name = " ".join(filter(None, [self.client_name, self.business_name]))
#         user_doc = frappe.new_doc("User")
#         user_doc.update({
#             "first_name": self.client_name,
#             "last_name": self.business_name,
#             "email": self.email,
#             "location": self.client_code,
#             "phone": self.telephone,
#             "mobile_no": self.contact_no,
#             "name": full_name,  # Set user ID as the full name
#             # Add other relevant fields from the client DocType to the user
#         })

#         try:
#             user_doc.insert(ignore_permissions=True)
#             # Calculate expiry details and color indicator
#             self.calculate_expiry_details(client_doc)
#             return user_doc
#         except Exception as e:
#             frappe.log_error(f"Error creating user: {e}", _("Create User Error"))
#             return None
            
#     def assign_user_roles(self, user_doc):
#         # Assign roles to the user
#         frappe.add_role(user_doc.name, "Client")  # Assign 'Client' role

#         # Set role profile and module profile for the user
#         user_doc.role_profile_name = "Client"  # Set role profile to 'Client'
#         user_doc.module_profile_name = "Client"  # Set module profile to 'Client'

#         # Set user type as 'System User'
#         user_doc.user_type = "System User"
#         # Save the user document with updated properties
#         user_doc.save()



# class Client(Document):
#     def after_insert(self):
#         # After inserting a new client, create a user
#         user_doc = self.create_user()
#         if user_doc:
#             self.assign_user_roles(user_doc)

#     def create_user(self):
#         # Create a user based on client data
#         user_doc = frappe.new_doc("User")
#         user_doc.update({
#             "first_name": self.client_name,
#             "last_name": self.business_name,
#             "email": self.email,
#             "location": self.client_code,
#             "phone": self.telephone,
#             "mobile_no": self.contact_no,          
#             # Add other relevant fields from the client DocType to the user
#         })

#         try:
#             user_doc.insert(ignore_permissions=True)
#             # Calculate expiry details and color indicator
#             self.calculate_expiry_details(client_doc)
#             return user_doc
#         except Exception as e:
#             frappe.log_error(f"Error creating user: {e}", _("Create User Error"))
#             return None
            
#     def assign_user_roles(self, user_doc):
#         # Assign roles to the user
#         frappe.add_role(user_doc.name, "Client")  # Assign 'Client' role

#         # Set role profile and module profile for the user
#         user_doc.role_profile_name = "Client"  # Set role profile to 'Client'
#         user_doc.module_profile_name = "Client"  # Set module profile to 'Client'

#         # Set user type as 'System User'
#         user_doc.user_type = "System User"
#         # Save the user document with updated properties
#         user_doc.save()
    


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
