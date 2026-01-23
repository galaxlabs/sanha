# # Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# # For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.permissions import add_user_permission
from frappe.utils import getdate, today
from frappe.model.rename_doc import rename_doc


class Client(Document):
    def validate(self):
        self.compute_status_from_expiry()

    def before_save(self):
        """Capture old email before it gets overwritten (for rename flow)."""
        self._old_email = None
        if not self.is_new():
            self._old_email = (frappe.db.get_value("Client", self.name, "email") or "").strip().lower()

    def after_insert(self):
        # CREATE FLOW (always complete this first)
        self.provision_access()

    def on_update(self):
        # UPDATE FLOW (only if required)
        self.handle_email_change_if_needed()

        # Always enforce latest sync after any update
        self.provision_access()

    # -------------------------
    # MAIN FLOW: Provision Access
    # -------------------------
    def provision_access(self):
        """
        Ensures for the CURRENT client email:
        - User exists
        - User has Client role
        - role_profile_name/module_profile set to Client
        - allowed_in_mentions set (0)
        - User permissions for Client and User exist
        - User first/last name kept in sync
        """
        if not self.email:
            frappe.throw(_("Email is required."))

        email = (self.email or "").strip().lower()

        user = self.get_or_create_user(email)

        # Sync names + enforce settings
        user.first_name = self.client_name
        user.last_name = self.business_name
        user.allowed_in_mentions = 0  # keep OFF as per your requirement
        user.module_profile = "Client"
        user.role_profile_name = "Client"

        # Ensure "Client" role row exists
        existing_roles = {d.role for d in (user.get("roles") or [])}
        if "Client" not in existing_roles:
            user.append("roles", {"role": "Client"})

        user.save(ignore_permissions=True)

        # Ensure permissions exist (safe to call repeatedly)
        self.ensure_user_permissions(email)

    def get_or_create_user(self, email: str):
        """Create or reuse User doc by email (User.name)."""
        if frappe.db.exists("User", email):
            return frappe.get_doc("User", email)

        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": self.client_name,
            "last_name": self.business_name,
            "enabled": 1,
            "send_welcome_email": 0,
            "allowed_in_mentions": 0,
            "module_profile": "Client",
            "role_profile_name": "Client",
            "roles": [{"role": "Client"}],
              
        })
        user.insert(ignore_permissions=True)
        return user

    def ensure_user_permissions(self, email: str):
        """Guarantee self permissions to Client doc and to their User doc."""
        add_user_permission("Client", self.name, email, is_default=True, ignore_permissions=True)
        add_user_permission("User", email, email, ignore_permissions=True)

    # -------------------------
    # UPDATE FLOW: Email Change Handler
    # -------------------------
    def handle_email_change_if_needed(self):
        old_email = (getattr(self, "_old_email", None) or "").strip().lower()
        new_email = (self.email or "").strip().lower()

        if not old_email or not new_email or old_email == new_email:
            return

        # If old user doesn't exist, nothing to rename; just continue provisioning on new email
        if not frappe.db.exists("User", old_email):
            return

        # If new user doesn't exist, rename old -> new
        if not frappe.db.exists("User", new_email):
            rename_doc("User", old_email, new_email, force=True, merge=False, ignore_permissions=True)

        # Update Query ownership for this client only
        frappe.db.sql(
            """
            UPDATE `tabQuery`
               SET owner = %s
             WHERE owner = %s
               AND client_name = %s
            """,
            (new_email, old_email, self.name),
        )

        # Update User Permission rows from old -> new
        frappe.db.sql(
            """
            UPDATE `tabUser Permission`
               SET user = %s
             WHERE user = %s
            """,
            (new_email, old_email),
        )

        frappe.db.commit()
        frappe.msgprint(_("Email changed: user, query owners, and permissions updated."))

    # -------------------------
    # Existing Status Logic
    # -------------------------
    def compute_status_from_expiry(self):
        if not self.certified_expiry:
            self.status = None
            return

        today_date = getdate(today())
        expiry_date = getdate(self.certified_expiry)
        days_remaining = (expiry_date - today_date).days

        if days_remaining < 0:
            new_status = "Expired"
        elif days_remaining <= 60:
            new_status = f"{days_remaining} Days Remaining"
        else:
            new_status = "Valid"

        if self.status != new_status:
            self.status = new_status


# import email
# from pydoc import doc
# import frappe
# from frappe import _
# from frappe.model.document import Document
# from frappe.permissions import add_user_permission
# from frappe.utils import getdate, today
# from frappe.model.rename_doc import rename_doc


# class Client(Document):
#     def validate(self):
#         self.compute_status_from_expiry()

#     def before_save(self):
#         """Capture old email before it gets overwritten."""
#         self._old_email = None
#         if not self.is_new():
#             self._old_email = frappe.db.get_value("Client", self.name, "email")

#     def after_insert(self):
#         user_doc = self.create_user()
#         if user_doc:
#             self.assign_user_roles(user_doc)
#             self.assign_user_permissions(user_doc)

#     def on_update(self):
#         # 1) handle email change (rename User + update owners)
#         self.handle_email_change()

#         # 2) always sync latest names + enforce profiles
#         self.sync_user()

#     def handle_email_change(self):
#         old_email = getattr(self, "_old_email", None)
#         new_email = (self.email or "").strip().lower()

#         if not old_email:
#             return

#         old_email = old_email.strip().lower()

#         # no change
#         if not new_email or old_email == new_email:
#             return

#         # If old user doesn't exist, nothing to rename; just continue
#         old_user_exists = frappe.db.exists("User", old_email)
#         if not old_user_exists:
#             return

#         # If new user already exists, don't rename; just shift ownership + permissions
#         new_user_exists = frappe.db.exists("User", new_email)

#         if not new_user_exists:
#             # Rename User (User.name is email)
#             rename_doc("User", old_email, new_email, force=True, merge=False, ignore_permissions=True)

#         # Update Query ownership for this client (only where client_name matches)
#         frappe.db.sql(
#             """
#             UPDATE `tabQuery`
#                SET owner = %s
#              WHERE owner = %s
#                AND client_name = %s
#             """,
#             (new_email, old_email, self.name),
#         )

#         # Update User Permission rows (user column)
#         frappe.db.sql(
#             """
#             UPDATE `tabUser Permission`
#                SET user = %s
#              WHERE user = %s
#             """,
#             (new_email, old_email),
#         )

#         frappe.db.commit()
#         frappe.msgprint(_("Email changed: user & linked ownership synced."))

#     def create_user(self):
#         if not self.email:
#             frappe.throw(_("Email is required to create a user."))

#         email = self.email.strip().lower()

#         # Reuse existing user or create a new one
#         if frappe.db.exists("User", email):
#             user_doc = frappe.get_doc("User", email)
#         else:
#             full_name = " ".join(filter(None, [self.client_name, self.business_name]))
#             user_doc = frappe.get_doc({
#                 "doctype": "User",
#                 "email": email,
#                 "first_name": self.client_name,
#                 "last_name": self.business_name,
#                 "enabled": 1,
#                 "allowed_in_mentions": 0,
#                 "send_welcome_email": 0,
#             })
#             user_doc.insert(ignore_permissions=True)

#         # ALWAYS enforce profiles on create/reuse
#         user_doc.module_profile = "Client"
#         user_doc.role_profile_name = "Client"
#         user_doc.save(ignore_permissions=True)

#         email = self.email.strip().lower()
#         add_user_permission("Client", self.name, email, is_default=True, ignore_permissions=True)
#         add_user_permission("User", email, email, ignore_permissions=True)


#         return user_doc
    
#         # Ensure permissions exist for the new user as well (safe to call again)


#     def assign_user_roles(self, user_doc):
#         client_role = "Client"
#         if client_role not in [r.role for r in user_doc.get("roles")]:
#             user_doc.append("roles", {"role": client_role})
#             user_doc.save(ignore_permissions=True)

#     def assign_user_permissions(self, user_doc):
#         email = user_doc.name  # user name is email
#         add_user_permission("Client", self.name, email, is_default=True, ignore_permissions=True)
#         add_user_permission("User", email, email, ignore_permissions=True)

#     def sync_user(self):
#         """Sync name + enforce module/role profile even if user already existed."""
#         if not self.email:
#             return

#         email = self.email.strip().lower()

#         if not frappe.db.exists("User", email):
#             # if user missing, create it
#             user_doc = self.create_user()
#             if user_doc:
#                 self.assign_user_roles(user_doc)
#                 self.assign_user_permissions(user_doc)
#             return

#         user_doc = frappe.get_doc("User", email)
#         user_doc.first_name = self.client_name
#         user_doc.last_name = self.business_name
#         user_doc.allowed_in_mentions = 0
#         user_doc.module_profile = "Client"
#         user_doc.role_profile_name = "Client"
#         user_doc.save(ignore_permissions=True)

#     def compute_status_from_expiry(self):
#         if not self.certified_expiry:
#             self.status = None
#             return

#         today_date = getdate(today())
#         expiry_date = getdate(self.certified_expiry)
#         days_remaining = (expiry_date - today_date).days

#         if days_remaining < 0:
#             new_status = "Expired"
#         elif days_remaining <= 60:
#             new_status = f"{days_remaining} Days Remaining"
#         else:
#             new_status = "Valid"

#         if self.status != new_status:
#             self.status = new_status

# def update_all_client_statuses():
#     """Daily job to update status of all Clients based on certified_expiry."""
#     today_date = getdate(today())
#     clients = frappe.get_all("Client", fields=["name", "certified_expiry", "status"])

#     for c in clients:
#         doc = frappe.get_doc("Client", c.name)

#         if not doc.certified_expiry:
#             continue

#         days_remaining = (getdate(doc.certified_expiry) - today_date).days

#         if days_remaining < 0:
#             new_status = "Expired"
#         elif days_remaining <= 60:
#             new_status = f"{days_remaining} Days Remaining"
#         else:
#             new_status = "Valid"

#         if doc.status != new_status:
#             doc.db_set("status", new_status)





# import email
# from pydoc import doc
# import frappe
# from frappe import _
# from frappe.model.document import Document
# from frappe.permissions import add_user_permission
# from frappe.utils import getdate, today


# class Client(Document):
#     def validate(self):
#         # keep status in sync on every save
#         self.compute_status_from_expiry()

#     def after_insert(self):
#         user_doc = self.create_user()
#         if user_doc:
#             self.assign_user_roles(user_doc)
#             self.assign_user_permissions(user_doc)

#     def on_update(self):
#         self.sync_user()

#     def create_user(self):
#         if not self.email:
#             frappe.throw(_("Email is required to create a user."))

#         # Reuse existing user or create a new one
#         if frappe.db.exists("User", self.email):
#             user_doc = frappe.get_doc("User", self.email)
#             frappe.msgprint(f"User already exists: {self.email}")
#         else:
#             full_name = " ".join(filter(None, [self.client_name, self.business_name]))
#             user_doc = frappe.get_doc({
#                 "doctype": "User",
#                 "email": self.email,
#                 "first_name": self.client_name,
#                 "last_name": self.business_name,
#                 "enabled": 1,
#                 "allowed_in_mentions": 0,
#                 "send_welcome_email": 0,
#             })
#             try:
#                 user_doc.insert(ignore_permissions=True)
#                 # Assign profiles right after insert
#                 user_doc.module_profile = "Client"
#                 user_doc.role_profile_name = "Client"
#                 user_doc.save(ignore_permissions=True)
#                 frappe.msgprint(f"User created and role/module profile assigned for: {self.email}")
#             except Exception:
#                 frappe.log_error(frappe.get_traceback(), "Client User Creation Failed")
#                 return None

#         return user_doc

#     def assign_user_roles(self, user_doc):
#         client_role = "Client"
#         if client_role not in [r.role for r in user_doc.get("roles")]:
#             user_doc.append("roles", {"role": client_role})
#             user_doc.save(ignore_permissions=True)
#             frappe.msgprint(f"Role '{client_role}' assigned to user.")

#     def assign_user_permissions(self, user_doc):
#         email = user_doc.email
#         # Allow user to see their own Client record
#         add_user_permission("Client", self.name, email, is_default=True, ignore_permissions=True)
#         # Let them see their User doc
#         add_user_permission("User", email, email, ignore_permissions=True)
#         frappe.msgprint("All user permissions assigned to client.")

#     def sync_user(self):
#         if not self.email or not frappe.db.exists("User", self.email):
#             frappe.msgprint("No linked user to sync.")
#             return

#         user_doc = frappe.get_doc("User", self.email)
#         user_doc.first_name = self.client_name
#         user_doc.last_name = self.business_name
#         user_doc.allowed_in_mentions = 0
#         user_doc.module_profile = "Client"
#         user_doc.role_profile_name = "Client"
#         user_doc.save(ignore_permissions=True)
#         frappe.msgprint("User synced with latest Client data.")

#     def compute_status_from_expiry(self):
#         """Compute and set status based on certified_expiry."""
#         if not self.certified_expiry:
#             # Optional: clear if no expiry
#             self.status = None
#             return

#         today_date = getdate(today())
#         expiry_date = getdate(self.certified_expiry)
#         days_remaining = (expiry_date - today_date).days

#         if days_remaining < 0:
#             new_status = "Expired"
#         elif days_remaining <= 60:
#             new_status = f"{days_remaining} Days Remaining"
#         else:
#             new_status = "Valid"

#         if self.status != new_status:
#             self.status = new_status


# def update_all_client_statuses():
#     """Daily job to update status of all Clients based on certified_expiry."""
#     today_date = getdate(today())
#     clients = frappe.get_all("Client", fields=["name", "certified_expiry", "status"])

#     for c in clients:
#         doc = frappe.get_doc("Client", c.name)

#         if not doc.certified_expiry:
#             continue

#         days_remaining = (getdate(doc.certified_expiry) - today_date).days

#         if days_remaining < 0:
#             new_status = "Expired"
#         elif days_remaining <= 60:
#             new_status = f"{days_remaining} Days Remaining"
#         else:
#             new_status = "Valid"

#         if doc.status != new_status:
#             # Update without triggering full validate stack
#             doc.db_set("status", new_status)

# class Client(Document):
# 	def validate(self):
# 		self.compute_status_from_expiry()

# 	def after_insert(self):
# 		user_doc = self.create_user()
# 		if user_doc:
# 			self.assign_user_roles(user_doc)
# 			self.assign_user_permissions(user_doc)

# 	def on_update(self):
# 		self.sync_user()

# 	def create_user(self):
# 		if not self.email:
# 			frappe.throw(_("Email is required to create a user."))

# 		user_doc = None

# 		# Check if user exists
# 		if frappe.db.exists("User", self.email):
# 			user_doc = frappe.get_doc("User", self.email)
# 			frappe.msgprint(f"User already exists: {self.email}")
# 		else:
# 			full_name = " ".join(filter(None, [self.client_name, self.business_name]))
# 			user_doc = frappe.get_doc({
# 				"doctype": "User",
# 				"email": self.email,
# 				"first_name": self.client_name,
# 				"last_name": self.business_name,
# 				"enabled": 1,
# 				"allowed_in_mentions": 0,
# 				"send_welcome_email": 0,
# 			})

# 			try:
# 				user_doc.insert(ignore_permissions=True)
# 				# Assign profiles right after insert
# 				user_doc.module_profile = "Client"
# 				user_doc.role_profile_name = "Client"
# 				user_doc.save(ignore_permissions=True)
# 				frappe.msgprint(f"User created and role/module profile assigned for: {self.email}")
# 			except Exception as e:
# 				frappe.log_error(frappe.get_traceback(), "Client User Creation Failed")
# 				return None

# 		return user_doc

# 	def assign_user_roles(self, user_doc):
# 		client_role = "Client"
# 		if client_role not in [role.role for role in user_doc.get("roles")]:
# 			user_doc.append("roles", {"role": client_role})
# 			user_doc.save(ignore_permissions=True)
# 			frappe.msgprint(f"Role '{client_role}' assigned to user.")

# 	def assign_user_permissions(self, user_doc):
# 		email = user_doc.email

# 		# Assign permission to view their own client record

# 		# Assign permission to view the Client doctype
# 		add_user_permission("Client", self.name, email, is_default=True, ignore_permissions=True)

# 		add_user_permission("User", email, email, ignore_permissions=True)

# 		frappe.msgprint("All user permissions assigned to client.")

# 	def sync_user(self):
# 		if not self.email or not frappe.db.exists("User", self.email):
# 			frappe.msgprint("No linked user to sync.")
# 			return

# 		user_doc = frappe.get_doc("User", self.email)
# 		user_doc.first_name = self.client_name
# 		user_doc.last_name = self.business_name
# 		user_doc.allowed_in_mentions = 0
# 		user_doc.module_profile = "Client"
# 		user_doc.role_profile_name = "Client"
# 		user_doc.save(ignore_permissions=True)
# 		frappe.msgprint("User synced with latest Client data.")
	
# 	def compute_status_from_expiry(self):
# 		"""Compute and set status based on certified_expiry."""

# 		if not self.certified_expiry:
# 			self.status = None
# 			return

# 		today_date = getdate(today())
# 		expiry_date = getdate(self.certified_expiry)
# 		days_remaining = (expiry_date - today_date).days

# 		if days_remaining < 0:
# 			new_status = "Expired"
# 		elif days_remaining <= 60:
# 			new_status = f"{days_remaining} Days Remaining"
# 		else:
# 			new_status = "Valid"

# 		if self.status != new_status:
# 			self.status = new_status

# 	def update_all_client_statuses():
# 		"""Daily job to update status of all Clients based on certified_expiry"""
# 		today_date = getdate(today())
# 		clients = frappe.get_all("Client", fields=["name", "certified_expiry", "status"])

# 		for client in clients:
# 			doc = frappe.get_doc("Client", client.name)

# 		if not doc.certified_expiry:
# 			continue

# 		days_remaining = (getdate(doc.certified_expiry) - today_date).days

# 		if days_remaining < 0:
# 			new_status = "Expired"
# 		elif days_remaining <= 60:
# 			new_status = f"{days_remaining} Days Remaining"
# 		else:
# 			new_status = "Valid"

# 		if doc.status != new_status:
# 			doc.db_set("status", new_status)


# def update_all_client_statuses():
# 	"""Daily job to update status of all Clients based on certified_expiry"""
# 	today_date = getdate(today())
# 	clients = frappe.get_all("Client", fields=["name", "certified_expiry", "status"])

# 	for client in clients:
# 		doc = frappe.get_doc("Client", client.name)

# 		if not doc.certified_expiry:
# 			continue  # Skip if no expiry date

# 		days_remaining = (getdate(doc.certified_expiry) - today_date).days

# 		# Decide new status
# 		if days_remaining < 0:
# 			new_status = "Expired"
# 		elif days_remaining <= 60:
# 			new_status = f"{days_remaining} Days Remaining"
# 		else:
# 			new_status = "Valid"

# 		if doc.status != new_status:
# 			doc.db_set("status", new_status)


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
