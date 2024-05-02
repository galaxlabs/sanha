# Copyright (c) 2024, Sanha Halal Pakistan  and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Query(Document):
    

    def validate(self):
        # Check if the documents table is hidden
        if not self.get("documents"):
            # Documents table is hidden, allow saving
            return
        
        # Documents table is visible, perform validation
        if not self.documents:
            frappe.throw('Please add documents before saving.')

        required_documents = ["TDS", "SDS", "Product Spec", "PDS", "Lab Sample Report", "Halal Questionnaire", "Declaration", "Halal Certificate", "MSDS", "COA"]
        found_msd = False
        found_halal_certificate = False
        
        for row in self.documents:
            
            # Check if both issue date and attachment are provided for required_documents
            if row.documents in required_documents and not row.issue_date and not row.attachment:
                frappe.throw(f"Issue Date and Attachment are required for {row.documents}.")
            # Check if issue date is provided for required_documents
            if row.documents in required_documents and not row.issue_date:
                frappe.throw(f"Issue Date is required for {row.documents}.")
                    
            # Check for mandatory attachment for all documents
            if not row.attachment:
                frappe.throw(f"Attachment is required for {row.documents}.")    
            
            # Check if MSDS is present
            if row.documents == "MSDS":
                found_msd = True
                # Check if issue date is provided for MSDS
                if not row.issue_date:
                    frappe.throw("Issue Date and Attachment are required for MSDS.")
        
            # Check if Halal Certificate is present
            if row.documents == "Halal Certificate":
                found_halal_certificate = True
                # Check if both issue date and expiry date are provided for Halal Certificate
                if not row.issue_date or not row.expiry_date:
                    frappe.throw("Halal Certificate requires both Issue Date and Expiry Date.")
                # Check if attachment is provided for Halal Certificate
                if not row.attachment:
                    frappe.throw("Attachment is required for Halal Certificate.")
        
        # If MSDS is not found, raise an exception
        if not found_msd:
            frappe.throw("MSDS is mandatory.")
            
        # If Halal Certificate is found but no expiry date is provided, raise an exception
        if found_halal_certificate and not any(doc.documents == "Halal Certificate" for doc in self.documents):
            frappe.throw("Halal Certificate requires Expiry Date.")




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

