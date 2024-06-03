// Copyright (c) 2024, Sanha Halal Pakistan  and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Query", {
// 	refresh(frm) {

// 	},
// });
// frappe.ui.form.on('Query', {
//     onload: function(frm) {
//         // Check if the document is in Draft mode
//         if (frm.doc.workflow_status != 'Draft') {
//             // Hide the delete button from the menu
//             frm.page.clear_menu();
//             // Hide the delete button from the links
//             frm.page.hide_menu_item('Delete');
//             // Disable the delete button in the form
//             frm.disable_delete();
//             // Hide the "Jump to" field
//             frm.page.clear_secondary_action();
//         }
//     }
// });
// frappe.ui.form.on('Query', {
//     onload: function(frm) {
//         // Hide the child table on load if it's a new document
//         if (frm.doc.__islocal) {
//             frm.toggle_display('documents', false);
//         }
//     },
//     after_save: function(frm) {
//         // Show the child table after saving the document
//         frm.toggle_display('documents', true);
//     },
//     validate: function(frm) {
//         // Check if the documents table is hidden
//         if (!frm.fields_dict.documents.$wrapper.is(':visible')) {
//             // Documents table is hidden, allow saving
//             return;
//         }
//         // Documents table is visible, perform validation
//         if (!frm.doc.documents || !frm.doc.documents.length) {
//             frappe.msgprint('Please add documents before saving.');
//             frappe.validated = false; // Prevent saving the document
//             return;
//         }

//         // Check if MSDS is present
//         var msds_found = false;
//         for (var i = 0; i < frm.doc.documents.length; i++) {
//             if (frm.doc.documents[i].documents === "MSDS") {
//                 msds_found = true;
//                 break;
//             }
//         }

//         // If MSDS is not found, show message after save
//         if (!msds_found) {
//             frm._msds_required = true; // Flag to show message after save
//         }
//     },
//     custom_workflow_actions: {
//         // Custom workflow action for submission
//         submit_document: function(frm) {
//             // Check if MSDS is present before submission
//             var msds_found = false;
//             for (var i = 0; i < frm.doc.documents.length; i++) {
//                 if (frm.doc.documents[i].documents === "MSDS") {
//                     msds_found = true;
//                     break;
//                 }
//             }

//             // If MSDS is not found, show message and prevent submission
//             if (!msds_found) {
//                 frappe.msgprint('MSDS is required. Please provide the required document before submitting.');
//                 return false; // Prevent submission
//             }
//         }
//     }
// });

// frappe.ui.form.on('Query', {
//     onload: function(frm) {
//         // Hide the child table on load if it's a new document
//         if (frm.doc.__islocal) {
//             frm.toggle_display('documents', false);
//         }
//     },
//     after_save: function(frm) {
//         // Show the child table after saving the document
//         frm.toggle_display('documents', true);
//     },
//     validate: function(frm) {
//         // Check if the documents table is hidden
//         if (!frm.fields_dict.documents.$wrapper.is(':visible')) {
//             // Documents table is hidden, allow saving
//             return;
//         }
//         // Documents table is visible, perform validation
//         if (!frm.doc.documents || !frm.doc.documents.length) {
//             frappe.msgprint('Please add documents before saving.');
//             frappe.validated = false; // Prevent saving the document
//             return;
//         }

//         // Check if MSDS is present
//         var msds_found = false;
//         for (var i = 0; i < frm.doc.documents.length; i++) {
//             if (frm.doc.documents[i].documents === "MSDS") {
//                 msds_found = true;
//                 break;
//             }
//         }

//         // If MSDS is not found, show message after save
//         if (!msds_found) {
//             frm._msds_required = true; // Flag to show message after save
//         }
//     },
//     before_submit: function(frm) {
//         // Check if MSDS is present before submission
//         var msds_found = false;
//         for (var i = 0; i < frm.doc.documents.length; i++) {
//             if (frm.doc.documents[i].documents === "MSDS") {
//                 msds_found = true;
//                 break;
//             }
//         }

//         // If MSDS is not found, show message
//         if (!msds_found) {
//             frappe.msgprint('MSDS is required. Please provide the required document before submitting.');
//             frappe.validated = false; // Prevent submission
//         }
//     }
// });

frappe.ui.form.on('Query', {
    validate: function(frm) {
        // Check if the documents table is hidden
        if (!frm.fields_dict.documents.$wrapper.is(':visible')) {
            // Documents table is hidden, allow saving
            return;
        }
        // Documents table is visible, perform validation
        // Your validation logic here
        if (!frm.doc.documents || !frm.doc.documents.length) {
            frappe.msgprint('Please add documents before saving.');
            frappe.validated = false; // Prevent saving the document
        }
    },
    onload: function(frm) {
        // Hide the child table on load if it's a new document
        if (frm.doc.__islocal) {
            frm.toggle_display('documents', false);
        }
    },
    after_save: function(frm) {
        // Show the child table after saving the document
        frm.toggle_display('documents', true);
    }
});
frappe.ui.form.on('Query', {
    onload: function(frm) {
        // Hide the child table on load if it's a new document
        if (frm.doc.__islocal) {
            frm.toggle_display('documents', false);
        }
    },
    after_save: function(frm) {
        // Show the child table after saving the document
        frm.toggle_display('documents', true);
    }
});

frappe.ui.form.on('Query', {
    onload: function(frm) {
        // Fetch user document based on session user's email
        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "User",
                name: frappe.session.user
            },
            callback: function(r) {
                if (r.message) {
                    // Set client_name field with user's full name if it's empty
                    if (!frm.doc.client_name) {
                        frm.set_value('client_name', r.message.full_name);
                    }
                    
                    // Set client_code field with user's location if it's empty
                    if (!frm.doc.client_code) {
                        frm.set_value('client_code', r.message.location);
                    }
                }
            }
        });
    },

    on_submit: function(frm) {
        // Check if the document is transitioning from draft state
        if (frm.doc.__islocal) {
            // Fetch the current user's full name
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "User",
                    name: frappe.session.user
                },
                callback: function(r) {
                    if (r.message) {
                        // Set owner_user_full_name field with user's full name
                        frm.set_value('owner_user_full_name', r.message.full_name);
                    }
                }
            });
        }
    }
});

// frappe.ui.form.on('Query', {
// 	    onload: function(frm) {
//         // Fetch user document based on session user's email
//         frappe.call({
//             method: "frappe.client.get",
//             args: {
//                 doctype: "User",
//                 name: frappe.session.user
//             },
//             callback: function(r) {
//                 if (r.message) {
//                     // Set client_name field with user's full name
//                     frm.set_value('client_name', r.message.full_name);
                    
//                     // Set client_code field with user's location
//                     frm.set_value('client_code', r.message.location);
//                 }
//             }
//         });
//     }
// });

