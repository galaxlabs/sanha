frappe.ui.form.on('Workspace', {
    setup_actions: function(page) {
        // Check user roles and workspace context
        if (frappe.user.has_role("Client") && frappe.workspace === "client_dashboard") {
            // For clients accessing client_dashboard workspace
            // Hide "Create" button
            $(".custom-actions").addClass("hidden"); 

            // Hide "Edit" button
            $(".standard-actions .btn.btn-secondary.btn-default.btn-sm").addClass("hidden");
        } else {
            // For other roles or workspaces, retain default actions
            // You can optionally add logic for other roles or workspaces here
        }
    }
});

// frappe.ui.form.on('Workspace', {
//     setup_actions: function(page) {
//         // Check user roles and workspace context
//         if (frappe.user.has_role("Client") && frappe.workspace === "client_dashboard") {
//             // For clients accessing client_dashboard workspace
//             // Hide "Create" and "Edit" options
//             page.clear_primary_action(); // Hide "Create" button
//             page.clear_secondary_action(); // Hide "Edit" button
//         } else {
//             // For other roles or workspaces, retain default actions
//             // You can optionally add logic for other roles or workspaces here
//         }
//     }
// });
