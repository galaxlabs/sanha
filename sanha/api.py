import frappe

# Define a server-side function to make a file private
@frappe.whitelist()
def make_file_private(file_url):
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
#     file = frappe.get_doc("FileUploader", {"file_url": file_url})
#     if file:
#         if file.is_private != 1:  # Check if not already private
#             file.is_private = 1
#             file.save()
#             return {"message": "File is now private", "file_url": file_url}
#         else:
#             return {"message": "File is already private", "file_url": file_url}
#     else:
#         return {"error": "File not found", "file_url": file_url}

# @frappe.whitelist()
# def make_file_private(file_url):
#     # Ensure the function is getting called correctly
#     frappe.msgprint(f"Making file private: {file_url}")

#     # Fetch the file document
#     file = frappe.get_doc("File", {"file_url": file_url})
#     if file:
#         file.is_private = 1
#         file.save()
#         return {"message": "File is now private", "file_url": file_url}
#     else:
#         return {"error": "File not found", "file_url": file_url}



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