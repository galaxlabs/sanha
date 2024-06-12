# import frappe
# import os
# import base64
# from frappe.utils.file_manager import save_file, get_files_path, MaxFileSizeReachedError
# from frappe import _, conf
# import zipfile
# import logging

# # Set up logging
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler('/tmp/upload_debug.log')
# handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)

# @frappe.whitelist()
# def custom_upload():
#     try:
#         user = frappe.session.user
#         dt = frappe.form_dict.doctype
#         dn = frappe.form_dict.docname
#         filename = frappe.form_dict.filename
#         is_private = cint(frappe.form_dict.is_private)

#         logger.debug(f"Starting upload for user: {user}, doctype: {dt}, docname: {dn}, filename: {filename}")

#         if not filename:
#             frappe.throw(_("Please select a file"), frappe.ValidationError)

#         user_folder = create_user_folder(user)
#         file_doc = save_uploaded_file(dt, dn, filename, user_folder, is_private)

#         return {
#             "name": file_doc.name,
#             "file_name": file_doc.file_name,
#             "file_url": file_doc.file_url,
#             "is_private": file_doc.is_private
#         }
#     except Exception as e:
#         logger.error(f"Error in custom_upload: {str(e)}")
#         frappe.throw(_("An error occurred during file upload. Please try again later."))

# def create_user_folder(user):
#     user_folder = get_files_path('private', user)
#     if not os.path.exists(user_folder):
#         os.makedirs(user_folder)
#     return user_folder

# def save_uploaded_file(dt, dn, filename, user_folder, is_private):
#     content = get_uploaded_content()
#     if content:
#         return save_file(filename, content, dt, dn, folder=user_folder, is_private=is_private)
#     else:
#         raise frappe.ValidationError(_("File content not found"))

# def get_uploaded_content():
#     if "filedata" in frappe.form_dict:
#         if "," in frappe.form_dict.filedata:
#             frappe.form_dict.filedata = frappe.form_dict.filedata.rsplit(",", 1)[1]
#         return base64.b64decode(frappe.form_dict.filedata)
#     else:
#         frappe.throw(_("No file attached"))

# @frappe.whitelist()
# def get_user_backup():
#     try:
#         user = frappe.session.user
#         user_folder = get_files_path('private', user)
#         if not os.path.exists(user_folder):
#             frappe.throw(_("No files found for the user."))

#         zip_file_path = create_backup_zip(user, user_folder)
#         with open(zip_file_path, 'rb') as file:
#             content = file.read()

#         return {
#             "filename": f"{user}_backup.zip",
#             "content": base64.b64encode(content).decode()
#         }
#     except Exception as e:
#         logger.error(f"Error in get_user_backup: {str(e)}")
#         frappe.throw(_("An error occurred while creating the backup. Please try again later."))

# def create_backup_zip(user, user_folder):
#     backup_folder = get_files_path('private', f"{user}_backup")
#     if not os.path.exists(backup_folder):
#         os.makedirs(backup_folder)

#     zip_file_path = os.path.join(backup_folder, f"{user}_backup.zip")
#     with zipfile.ZipFile(zip_file_path, 'w') as zipf:
#         for root, _, files in os.walk(user_folder):
#             for file in files:
#                 file_path = os.path.join(root, file)
#                 zipf.write(file_path, os.path.relpath(file_path, user_folder))

#     return zip_file_path

# import frappe
# import base64
# from urllib.parse import unquote
# from frappe import _
# from frappe.utils import cint, get_files_path
# from frappe.utils.file_manager import save_file

# @frappe.whitelist()
# def custom_upload():
#     dt = frappe.form_dict.doctype
#     dn = frappe.form_dict.docname
#     filename = frappe.form_dict.filename
#     frappe.form_dict.is_private = cint(frappe.form_dict.is_private)
    
#     if not filename:
#         frappe.msgprint(_("Please select a file"), raise_exception=True)

#     file_doc = save_uploaded_file(dt, dn, filename, frappe.form_dict.is_private)

#     return {
#         "name": file_doc.name,
#         "file_name": file_doc.file_name,
#         "file_url": file_doc.file_url,
#         "is_private": file_doc.is_private
#     }

# def save_uploaded_file(dt, dn, filename, is_private):
#     content = get_uploaded_content()
#     if content:
#         return save_file(filename, content, dt, dn, is_private=is_private)
#     else:
#         raise frappe.ValidationError(_("File content not found"))

# def get_uploaded_content():
#     if "filedata" in frappe.form_dict:
#         if "," in frappe.form_dict.filedata:
#             frappe.form_dict.filedata = frappe.form_dict.filedata.rsplit(",", 1)[1]
#         return base64.b64decode(frappe.form_dict.filedata)
#     else:
#         frappe.msgprint(_("No file attached"))
#         return None
