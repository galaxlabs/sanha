frappe.ui.form.on('File', {
    refresh: function(frm) {
        if (frappe.user_roles.includes('Client')) {
            // Disable the 'is_private' checkbox and ensure it's always checked
            frm.set_value('is_private', 1);
            frm.toggle_enable('is_private', false);

            // Hide the 'Set all public' and 'Set all private' buttons
            $('.btn-modal-primary').hide(); // Assuming this is the "Set all public" button
            $('.btn-modal-secondary').hide(); // Assuming this is the "Set all private" button
        }
    }
});

// // Modify the upload modal when it's opened
// $(document).on('shown.bs.modal', '.modal', function() {
//     var modal = $(this);
//     if (modal.find('.modal-title').text().trim() === 'Upload') {
//         modal.find('.btn-file-upload').each(function() {
//             var button = $(this);
//             if (!button.text().includes('My Device')) {
//                 button.hide();
//             }
//         });

//         // Add event listener to set files as private
//         modal.find('input[type="file"]').on('change', function() {
//             frappe.call({
//                 method: 'sanha.api.make_file_private',
//                 args: {
//                     file_url: $(this).val()
//                 },
//                 callback: function(r) {
//                     // Handle the response if needed
//                     if (r.message) {
//                         console.log(r.message);
//                     }
//                 }
//             });
//         });
//     }
// });

// frappe.ui.form.on('File', {
//     refresh: function(frm) {
//         if (frappe.user_roles.includes('Client')) {
//             // Hide other upload options
//             $('.file-upload-area .btn-file-upload').each(function() {
//                 var button = $(this);
//                 if (!button.text().includes('My Device')) {
//                     button.hide();
//                 }
//             });

//             // Ensure the file is always private
//             frm.set_value('is_private', 1);
//             frm.fields_dict['is_private'].df.hidden = 1;
//             frm.refresh_field('is_private');
//         }
//     }
// });

// Modify the upload modal when it's opened
// $(document).on('shown.bs.modal', '.modal', function() {
//     var modal = $(this);
//     if (modal.find('.modal-title').text().trim() === 'Upload') {
//         modal.find('.btn-file-upload').each(function() {
//             var button = $(this);
//             if (!button.text().includes('My Device')) {
//                 button.hide();
//             }
//         });

//         // Add event listener to set files as private
//         modal.find('input[type="file"]').on('change', function() {
//             frappe.call({
//                 method: 'sanha.api.make_file_private',
//                 args: {
//                     file_url: $(this).val()
//                 },
//                 callback: function(r) {
//                     // Handle the response if needed
//                     if (r.message) {
//                         console.log(r.message);
//                     }
//                 }
//             });
//         });
//     }
// });
