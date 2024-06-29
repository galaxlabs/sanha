# Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.email.queue import flush
from frappe import _
from datetime import datetime


# # Configure logging

class Query(Document):

    def validate(self):

        if not self.get("documents"):

            return
        

        if not self.documents:
            frappe.throw('Please add documents before saving.')

        required_documents = ["TDS", "SDS", "Product Spec", "PDS", "Lab Sample Report", "Halal Questionnaire", "Declaration", "Halal Certificate", "MSDS", "COA"]
        found_msd = False
        found_halal_certificate = False
        

        for row in self.documents:

            if row.documents in required_documents and not row.issue_date and not row.attachment:
                frappe.throw(f"Issue Date and Attachment are required for {row.documents}.")

            if row.documents in required_documents and not row.issue_date:
                frappe.throw(f"Issue Date is required for {row.documents}.")

            if not row.attachment:
                frappe.throw(f"Attachment is required for {row.documents}.")    

            if row.documents == "MSDS":
                found_msd = True

                if not row.issue_date:
                    frappe.throw("Issue Date and Attachment are required for MSDS.")

            if row.documents == "Halal Certificate":
                found_halal_certificate = True

                if not row.issue_date or not row.expiry_date:
                    frappe.throw("Halal Certificate requires both Issue Date and Expiry Date.")

                if not row.attachment:
                    frappe.throw("Attachment is required for Halal Certificate.")        

        if not found_msd:
            frappe.throw("MSDS is mandatory.")

        if found_halal_certificate and not any(doc.documents == "Halal Certificate" for doc in self.documents):
            frappe.throw("Halal Certificate requires Expiry Date.")
    
#     def send_query_notification(doc, method=None):
#         if doc.workflow_state == "Submitted":
#             send_email_to_client(doc)
#             send_email_to_admin_and_evaluation(doc)
#             flush_email_queue()

# def send_status_update_notification(doc, method=None):
#     if doc.workflow_state in ["Rejected", "Approved", "Haram", "Hold", "Halal"]:
#         send_status_email_to_client_and_admin(doc)
#     flush_email_queue()

# def send_email_to_client(doc):
#     subject = "Confirmation of Query Submission"
#     message = f"""
#     <b>Dear {doc.client_name},</b><br><br>
#     We are pleased to inform you that your query about <b>{doc.raw_material}</b> has been successfully submitted.<br>
#     It has been forwarded to our Evaluation Department for further processing.<br><br>
#     You can expect a response from us within the next 24 hours. We appreciate your patience and understanding.<br><br>
#     If you have any further questions or require additional assistance, please do not hesitate to contact us at <b>karachi@sanha.org.pk</b>.<br><br>
#     Best regards,<br><br>
#     System Generated Email
#     """
#     recipients = [doc.owner]
#     send_email(subject, message, recipients)

# def send_email_to_admin_and_evaluation(doc):
#     subject = f"{doc.client_name} Query Submission Notification"
#     message = f"""
#     Dear Admin/Evaluation Department,<br><br>
#     This is to inform you that our client, {doc.client_name}, has successfully submitted a query titled {doc.name} about {doc.raw_material}.<br>
#     The query has been forwarded to the Evaluation Department for further processing.<br><br>
#     Please review the query and respond accordingly within the next 24 hours.<br><br>
#     If you have any further questions or require additional information, please do not hesitate to contact us.<br><br>
#     Best regards,<br><br>
#     System Generated Email
#     """
#     recipients = ["karachi@sanha.org.pk", "evaluation@sanha.org.pk"]
#     send_email(subject, message, recipients)

# def send_status_email_to_client_and_admin(doc):
#     subject = f"Your Query has been {doc.workflow_state}"
#     message = f"""
#     <b>Dear {doc.client_name},</b><br><br>
#     Your query has been marked as {doc.workflow_state}.<br>
#     Please check the portal or find the attached document for more details.<br><br>
#     If you have any further questions or require additional assistance, please do not hesitate to contact us.<br><br>
#     Best regards,<br><br>
#     System Generated Email
#     """
#     recipients = [doc.owner, "karachi@sanha.org.pk"]
#     send_email(subject, message, recipients)
<<<<<<< HEAD
    
# def send_expired_document_notification(self, expired_documents):
#     subject = "Notification of Expired Documents"
#     message = f"""
#     <b>Dear Admin,</b><br><br>
#     The following documents in Query <b>{self.name}</b> have expired:<br>
#     <ul>
#     {"".join(f"<li>{doc}</li>" for doc in expired_documents)}
#     </ul>
#     Please take necessary actions to renew these documents.<br><br>
#     Best regards,<br><br>
#     System Generated Email
#     """
#     recipients = [doc.owner, "karachi@sanha.org.pk"]  # Adjust admin email as needed
#     send_email(subject, message, recipients)
#     flush_email_queue()
    
    
# def send_email(subject, message, recipients):
#     frappe.sendmail(
#         recipients=recipients,
#         subject=subject,
#         message=message,
#         delayed=False
#     )

# def flush_email_queue():
#     flush()
#     frappe.logger().info("Email queue flushed and emails sent.")
=======

# def send_email(subject, message, recipients):
#     frappe.sendmail(
#         recipients=recipients,
#         subject=subject,
#         message=message,
#         delayed=False
#     )
>>>>>>> 8dec8ca4567c0ad696abc85290516dcddb4a3098

# def flush_email_queue():
#     flush()
#     frappe.logger().info("Email queue flushed and emails sent.")
    pass
# ########################################################################

    # def flush_email_queue():
#     # Your custom logic here
#     flush()
#     frappe.logger().info("Email sent.")
#     pass        
#     def on_submit(self):
#         send_query_notification(self)
    
#     def on_update(self):
#         send_status_update_notification(self)

# def send_query_notification(doc, method=None):
#     if doc.workflow_state == "Submitted":
#         send_email_to_client(doc)
#         send_email_to_admin_and_evaluation(doc)

# def send_status_update_notification(doc, method=None):
#     if doc.workflow_state in ["Rejected", "Approved", "Haram", "Hold", "Halal"]:
#         send_status_email_to_client(doc)
#     elif doc.workflow_state == "Draft":
#         send_draft_return_email_to_client(doc)

# def send_email_to_client(doc):
#     subject = "Confirmation of Query Submission"
#     message = f"""
#     <b> Dear {doc.client_name},</b><br><br>
#     We are pleased to inform you that your query about <b>{doc.raw_material}</b> has been successfully submitted.<br>
#     It has been forwarded to our Evaluation Department for further processing.<br><br>
#     You can expect a response from us within the next 24 hours. We appreciate your patience and understanding.<br><br>
#     If you have any further questions or require additional assistance, please do not hesitate to contact us at <b>karachi@sanha.org.pk</b>.<br><br>
#     Best regards,<br><br>
#     System Generated Email
#     """
#     recipients = [doc.owner]
#     send_email(subject, message, recipients)

# def send_email_to_admin_and_evaluation(doc):
#     subject = f"{doc.client_name} Query Submission Notification"
#     message = f"""
#     Dear [Admin/Evaluation Department],<br><br>
#     This is to inform you that our client, {doc.client_name}, has successfully submitted a query titled {doc.name} about {doc.raw_material}.<br>
#     The query has been forwarded to the Evaluation Department for further processing.<br><br>
#     Please review the query and respond accordingly within the next 24 hours.<br><br>
#     If you have any further questions or require additional information, please do not hesitate to contact us.<br><br>
#     Best regards,<br><br>
#     System Generated Email
#     """
#     recipients = ["karachi@sanha.org.pk", "evaluation@sanha.org.pk"]  # Replace with actual email addresses
#     send_email(subject, message, recipients)

# def send_status_email_to_client(doc):
#     subject = "Your Query has been Answered"
#     message = f"""
#     <b> Dear {doc.client_name},</b><br><br>
#     Your query has been marked as {doc.workflow_state}.<br>
#     Please check the portal or find the attached document for more details.<br><br>
#     If you have any further questions or require additional assistance, please do not hesitate to contact us.<br><br>
#     Best regards,<br><br>
#     System Generated Email
#     """
#     recipients = [doc.owner]
#     send_email(subject, message, recipients)

# def send_draft_return_email_to_client(doc):
#     subject = "Your Query has been Returned"
#     message = f"""
#     <b> Dear {doc.client_name},</b><br><br>
#     Your query has been returned to draft status for further action.<br>
#     Please review and make the necessary updates.<br><br>
#     If you have any further questions or require additional assistance, please do not hesitate to contact us.<br><br>
#     Best regards,<br><br>
#     System Generated Email
#     """
#     recipients = [doc.owner]
#     send_email(subject, message, recipients)

# def send_email(subject, message, recipients):
#     frappe.sendmail(
#         recipients=recipients,
#         subject=subject,
#         message=message,
#         delayed=False
#     )



    # def before_save(doc, method):
    #     # Check if client name and client code are not set
    #     if not doc.client_name and not doc.client_code:
    #     # Fetch the session user's full name
    #         user = frappe.get_doc("User", frappe.session.user)
    #         full_name = user.full_name if user else frappe.session.user

    #     # Use the full name as the client name
    #     doc.client_name = full_name

    #     # Use the email address as the client code (optional)
    #     doc.client_code = frappe.session.user
        
    #     pass
    # def before_save(self):
    #     if not self.client_name and not self.client_code:
    #         # Fetch the session user's full name and location
    #         user = frappe.get_doc("User", frappe.session.user_fullname)
    #         full_name = user.full_name
    #         location = user.location

    #         # Use the location as the client code
    #         client_code = location

    #         # Update the client_name and client_code fields
    #         self.client_name = full_name
    #         self.client_code = client_code
    



        #     first_name = user.first_name
        #     location = user.location

        #     # Use the location as the client code
        #     client_code = location

        #     # Update the client_name and client_code fields
        #     self.client_name = first_name
        #     self.client_code = client_code

        # # Set the client_name to the session user
        # self.client_name = frappe.session.user

   

    # def on_update(self):
    #     # Fetch the session user's first name and location
    #     first_name = frappe.get_value("User", frappe.session.user, "first_name")
    #     location = frappe.get_value("User", frappe.session.user, "location")

    #     # Use the location as the client code
    #     client_code = location

    #     # Update the client_name and client_code fields
    #     self.client_name = first_name
    #     self.client_code = client_code
    # Define function to apply role-based and status-based filtering to list view



#00005
    # def validate(self):
    #     # Check if the documents table is hidden
    #     if not self.get("documents"):
    #         # Documents table is hidden, allow saving
    #         return
        
    #     # Documents table is visible, perform validation
    #     if not self.documents:
    #         frappe.throw('Please add documents before saving.')

    #     required_documents = ["TDS", "SDS", "Product Spec", "PDS", "Lab Sample Report", "Halal Questionnaire", "Declaration", "Halal Certificate", "MSDS", "COA"]
    #     required_with_expiry = ["Halal Certificate"]
    #     found_msd = False
    #     found_halal_certificate = False
        
    #     for row in self.documents:
    #         # Check if issue date is provided for required_documents
    #         if row.documents in required_documents and not row.issue_date:
    #             frappe.throw(f"Issue Date is required for {row.documents}.")
                
    #         # Check for mandatory attachment for all documents
    #         if not row.attachment:
    #             frappe.throw(f"An attachment is required for {row.documents}.")    
            
    #         # Check if MSDS is present
    #         if row.documents == "MSDS":
    #             found_msd = True
    #             # Check if issue date is provided for MSDS
    #             if not row.issue_date:
    #                 frappe.throw("Issue Date is required for MSDS.")
        
    #         # Check if Halal Certificate is present
    #         if row.documents == "Halal Certificate":
    #             found_halal_certificate = True
    #             # Check if both issue date and expiry date are provided for Halal Certificate
    #             if not row.issue_date or not row.expiry_date:
    #                 frappe.throw("Both Issue Date and Expiry Date are required for Halal Certificate.")
        
    #     # If MSDS is not found, raise an exception
    #     if not found_msd:
    #         frappe.throw("MSDS is mandatory.")
            
    #     # Halal Certificate is required only if it's found in the documents
    #     if found_halal_certificate and not any(doc.documents == "Halal Certificate" for doc in self.documents):
    #         frappe.throw("Halal Certificate requires both Issue Date and Expiry Date.")
            
    # def on_submit(self):
    #     # Perform the same validation as in the `validate` method
    #     self.validate()


# ########### Working 
    # def validate(self):
    #     required_documents = ["TDS", "SDS", "Product Spec", "PDS", "Lab Sample Report", "Halal Questionnaire", "Declaration", "Halal Certificate", "MSDS", "COA"]
    #     required_with_expiry = ["Halal Certificate"]
    #     found_msd = False
    #     found_halal_certificate = False
        
    #     # Check if the documents table is hidden
    #     if not self.get("documents"):
    #         # Documents table is hidden, allow saving
    #         return
        
    #     # Documents table is visible, perform validation
    #     if not self.documents:
    #         frappe.throw('Please add documents before saving.')

    #     for row in self.documents:
    #         # Check if issue date is provided for required_documents
    #         if row.documents == "Halal Certificate":
    #             found_halal_certificate = True
    #             # Check if both issue date and expiry date are provided for Halal Certificate
    #             if not row.issue_date or not row.expiry_date:
    #                 frappe.throw("Both Issue Date and Expiry Date are required for Halal Certificate.")
            
    #         if row.documents in required_documents and not row.issue_date:
    #             frappe.throw(f"Issue Date is required for {row.documents}.")
                
    #         # Check for mandatory attachment for all documents
    #         if not row.attachment:
    #             frappe.throw(f"An attachment is required for {row.documents}.")    
            
    #         # Check if MSDS is present
    #         if row.documents == "MSDS":
    #             found_msd = True
    #             # Check if issue date is provided for MSDS
    #             if not row.issue_date:
    #                 frappe.throw("Issue Date is required for MSDS.")
        
    #         # Check if Halal Certificate is present
            
        
    #     # If MSDS is not found, raise an exception
    #     if not found_msd:
    #         frappe.throw("MSDS is mandatory.")
            
    #     # Halal Certificate is required only if it's found in the documents
    #     if found_halal_certificate and not any(doc.documents == "Halal Certificate" for doc in self.documents):
    #         frappe.throw("Halal Certificate requires both Issue Date and Expiry Date.")
            
#     def validate(self):
#         # Check if the documents table is hidden
#         if not self.get("documents"):
#             # Documents table is hidden, allow saving
#             return
        
#         # Documents table is visible, perform validation
#         if not self.documents:
#             frappe.throw('Please add documents before saving.')

#         # Check if MSDS is present
#         msds_found = any(doc.documents == "MSDS" for doc in self.documents)

#         # If MSDS is not found, raise an exception
#         if not msds_found:
#             frappe.msgprint('MSDS is required. Please provide the required document before submitting.')
#             frappe.throw('MSDS is required.')
    
#     def validate(self):
#         required_documents = ["TDS", "SDS", "Product Spec", "PDS", "Lab Sample Report", "Halal Questionnaire", "Declaration", "Halal Certificate", "MSDS", "COA"]
#         required_with_expiry = ["Halal Certificate"]
#         found_msd = False
        
#         for row in self.documents:
#             # Check if issue date is provided for required_documents
#             if row.documents in required_documents and not row.issue_date:
#                 frappe.throw(f"Issue Date is required for {row.documents}.")
                
#             # Check for mandatory attachment for all documents
#             if not row.attachment:
#                 frappe.throw(f"An attachment is required for {row.documents}.")    
            
#             # Check if MSDS is present
#             if row.documents == "MSDS":
#                 found_msd = True
#                 # Check if issue date is provided for MSDS
#                 if not row.issue_date:
#                     frappe.throw("Issue Date is required for MSDS.")
        
#         # If MSDS is not found, raise an exception
#         if not found_msd:
#             frappe.throw("MSDS is mandatory.")
            
            
#         if row.documents == "Halal Certificate":
#                 found_halal_certificate = True
#                 # Check if both issue date and expiry date are provided for Halal Certificate
#                 if not row.issue_date or not row.expiry_date:
#                     frappe.throw("Both Issue Date and Expiry Date are required for Halal Certificate.")
        
#         # Halal Certificate is required only if it's found in the documents
#         if "Halal Certificate" in self.documents and not any(doc.documents == "Halal Certificate" for doc in self.documents):
#             frappe.throw("Halal Certificate requires both Issue Date and Expiry Date.")

    # def validate(self):
    #     required_documents = ["TDS", "SDS", "Product Spec", "PDS", "Lab Sample Report", "Halal Questionnaire", "Declaration", "Halal Certificate", "MSDS", "COA"]
    # required_with_expiry = ["Halal Certificate"]
    # found_halal_certificate = False
    # found_msd = False
    
    # for row in self.documents:
    #     # Check if the document is one of the required types
    #     if row.documents in required_documents:
    #         # Check for mandatory attachment for required documents
    #         if not row.attachment:
    #             frappe.throw(f"An attachment is required for {row.documents}.")
            
    #         # Check if issue date is provided for all documents except MSDS
    #         if row.documents != "MSDS" and not row.issue_date:
    #             frappe.throw(f"Issue Date is required for {row.documents}.")
        
    #     # Check for MSDS and Halal Certificate
    #     if row.documents == "MSDS":
    #         found_msd = True
    #         # Check if issue date is provided for MSDS
    #         if not row.issue_date:
    #             frappe.throw("Issue Date is required for MSDS.")
        
    #     if row.documents in required_with_expiry:
    #         found_halal_certificate = True
    #         # Check if both issue date and expiry date are provided for Halal Certificate
    #         if not row.issue_date or not row.expiry_date:
    #             frappe.throw("Both Issue Date and Expiry Date are required for Halal Certificate.")
                
    # # If MSDS is not found, raise an exception
    # if not found_msd:
    #     frappe.throw("MSDS is mandatory.")
    
    # # Halal Certificate is required only if it's found in the documents
    # if found_halal_certificate and not any(doc.documents == "Halal Certificate" for doc in self.documents):
    #     frappe.throw("Halal Certificate requires both Issue Date and Expiry Date.")

    # def validate(self):
    #         required_documents = ["Declaration", "Lab Sample Report", "Halal Questionnaire", "Halal Certificate"]
    #         found_msd = False
        
    #         for row in self.documents:
    #         # Check if the document is one of the required types
    #             if row.documents in required_documents:
    #             # Check for mandatory attachment for required documents
    #                 if not row.attachment:
    #                     frappe.throw(f"An attachment is required for {row.documents}.")
                
    #             # Check if expiry date is provided for required documents
    #             if not row.expiry_date:
    #                 frappe.throw(f"Expiry Date is required for {row.documents}.")
                
        #         # Special check for MSDS
        #         if row.documents == "MSDS":
        #             found_msd = True

        # # Ensure MSDS is specifically included
        #         if not found_msd:
        #             frappe.throw("Including an MSDS is mandatory.")

    
    
    # Script Indet Error 00000001
# 	def validate(self):
#     		optional_documents = ["Declaration", "Lab Sample Report", "Halal Questionnaire", "Halal Certificate"]
# msds_found = False
        
# for row in self.document_types:
#             # Check for mandatory MSDS document
#             if row.documents == "MSDS":
#                 msds_found = True
#                 if not row.attachment:
#                     frappe.throw("An attachment is required for the MSDS document.")
            
#             # Check for optional documents
#             if row.documents in optional_documents:
#                 if not row.attachment or not row.expiry_date:
#                     frappe.throw(f"Both an attachment and an expiry date are required for {row.documents}.")

#         # Ensure MSDS is included
# if not msds_found:
#             frappe.throw("Including an MSDS is mandatory for each raw material.")

