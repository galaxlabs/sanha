import frappe
import base64
from urllib.parse import unquote
from frappe import _
from frappe.utils import cint, get_files_path
from frappe.utils.file_manager import save_file

@frappe.whitelist()
def custom_upload():
    dt = frappe.form_dict.doctype
    dn = frappe.form_dict.docname
    filename = frappe.form_dict.filename
    frappe.form_dict.is_private = cint(frappe.form_dict.is_private)
    
    if not filename:
        frappe.msgprint(_("Please select a file"), raise_exception=True)

    file_doc = save_uploaded_file(dt, dn, filename, frappe.form_dict.is_private)

    return {
        "name": file_doc.name,
        "file_name": file_doc.file_name,
        "file_url": file_doc.file_url,
        "is_private": file_doc.is_private
    }

def save_uploaded_file(dt, dn, filename, is_private):
    content = get_uploaded_content()
    if content:
        return save_file(filename, content, dt, dn, is_private=is_private)
    else:
        raise frappe.ValidationError(_("File content not found"))

def get_uploaded_content():
    if "filedata" in frappe.form_dict:
        if "," in frappe.form_dict.filedata:
            frappe.form_dict.filedata = frappe.form_dict.filedata.rsplit(",", 1)[1]
        return base64.b64decode(frappe.form_dict.filedata)
    else:
        frappe.msgprint(_("No file attached"))
        return None
