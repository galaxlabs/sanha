# # custom_report.py

# import frappe

# @frappe.whitelist()
# def generate_custom_report(filters=None):
#     # Fetch report data
#     report_data = get_report_data(filters)

#     # Return HTML content as response
#     return report_data

# def get_report_data(filters):
#     # Fetch report data based on filters
#     report_data = [
#         {"index": 1, "query_name": "Query 1", "raw_material": "Material 1"},
#         {"index": 2, "query_name": "Query 2", "raw_material": "Material 2"},
#         # Add more data rows as needed
#     ]

#     # Prepare additional data for rendering
#     report_title = "Custom Report"
#     current_datetime = frappe.utils.now()

#     # Render HTML template with data
#     html_content = frappe.render_template("includes/cr.html", {
#         "report_title": report_title,
#         "report_data": report_data,
#         "current_datetime": current_datetime
#     })

#     return html_content
