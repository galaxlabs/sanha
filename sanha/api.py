import frappe

@frappe.whitelist()
def make_file_private(file_url):
    # Ensure the function is getting called correctly
    frappe.msgprint(f"Making file private: {file_url}")

    # Fetch the file document
    file = frappe.get_doc("File", {"file_url": file_url})
    if file:
        file.is_private = 1
        file.save()
        return {"message": "File is now private", "file_url": file_url}
    else:
        return {"error": "File not found", "file_url": file_url}



# @frappe.whitelist()
# def make_file_private(file_url):
#     # Fetch the file document
#     file = frappe.get_doc("File", {"file_url": file_url})
#     if file:
#         file.is_private = 1
#         file.save()
#         return {"message": "File is now private", "file_url": file_url}
#     else:
#         return {"error": "File not found", "file_url": file_url}