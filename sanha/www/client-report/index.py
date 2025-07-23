# /www/query/index.py

import frappe
from frappe import _

def get_context(context):
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page."), frappe.PermissionError)
    
    context.user = frappe.session.user
    return context
