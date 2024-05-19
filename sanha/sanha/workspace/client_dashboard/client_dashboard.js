frappe.ui.form.on('Workspace', {
    setup: function(frm) {
        // Check if the current workspace is the one where you want to hide the buttons
        if (frappe.workspace === "client_dashboard") {
            // Hide the "Create Workspace" button
            frm.page.clear_primary_action();

            // Hide the "Edit" button
            frm.page.clear_secondary_action();
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
