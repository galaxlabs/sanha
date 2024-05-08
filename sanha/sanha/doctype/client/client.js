// Copyright (c) 2024, Sanha Halal Pakistan  and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Client", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Client', {
    refresh: function(frm) {
        // Add Extend button if status is not Extended
        if (frm.doc.status !== "Extended") {
            frm.add_custom_button(__('Extend'), function() {
                // Call custom function to handle extension
                frm.events.extend_expiry_date(frm);
            });
        }

        // Update status field based on conditions
        updateStatusField(frm);
    }
});

// Function to update the status field based on days remaining
function updateStatusField(frm) {
    var expiryDate = frm.doc.certified_expiry;
    var today = frappe.datetime.get_today();
    var daysRemaining = frappe.datetime.get_diff(expiryDate, today);

    if (daysRemaining < 0) {
        frm.set_value('status', 'Expired');
    } else if (daysRemaining <= 60) {
        frm.set_value('status', daysRemaining + ' Days Remaining');
    } else {
        frm.set_value('status', 'Valid');
    }
}