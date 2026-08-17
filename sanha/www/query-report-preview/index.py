# /www/query-report-preview/index.py

import frappe

def get_context(context):
    # Test page: guest-accessible, uses sample data (no login required)
    context.user = frappe.session.user or "Guest"
    return context