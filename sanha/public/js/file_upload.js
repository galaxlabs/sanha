// # Define a client-side function to customize file upload options based on user roles
frappe.ui.form.on('File', {
  refresh: function(frm) {
      if (frappe.user_roles.includes('Client')) {
          // Hide all other file upload options except "My Device"
          setTimeout(function() {
              $('.file-upload-area .btn-file-upload').each(function() {
                  var button = $(this);
                  if (!button.text().includes('My Device')) {
                      button.hide();
                  }
              });
          }, 500); // Added delay to ensure the DOM is fully loaded
      }
  }
});

$(document).on('shown.bs.modal', '.modal', function() {
  var modal = $(this);
  if (modal.find('.modal-title').text().trim() === 'Upload') {
      setTimeout(function() {
          modal.find('.btn-file-upload').each(function() {
              var button = $(this);
              if (!button.text().includes('My Device')) {
                  button.hide();
              }
          });
      }, 500); // Added delay to ensure the DOM is fully loaded

      // Custom upload event listener
      modal.find('input[type="file"]').off('change').on('change', function() {
          var file = this.files[0];
          if (file) {
              var reader = new FileReader();
              reader.onload = function(e) {
                  var filedata = e.target.result.split(',')[1];
                  frappe.call({
                      method: 'your_app.your_module.custom_upload',
                      args: {
                          doctype: cur_frm.doctype,
                          docname: cur_frm.docname,
                          filename: file.name,
                          filedata: filedata,
                          is_private: 1 // or 0 if not private
                      },
                      callback: function(r) {
                          if (r.message) {
                              console.log(r.message);
                          }
                      }
                  });
              };
              reader.readAsDataURL(file);
          }
      });
  }
});


// frappe.ui.form.on('File', {
//     refresh: function(frm) {
//         // Check if the user has the 'Client' role
//         if (frappe.user_roles.includes('Client')) {
//             // Hide other upload options except 'My Device' and 'Upload Button'
//             $('.file-upload-area .btn-file-upload').each(function() {
//                 var button = $(this);
//                 if (!button.text().includes('My Device') && !button.text().includes('Upload Button')) {
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

// // Modify the upload modal when it's opened
// $(document).on('shown.bs.modal', '.modal', function() {
//     var modal = $(this);
//     if (modal.find('.modal-title').text().trim() === 'Upload') {
//         modal.find('.btn-file-upload').each(function() {
//             var button = $(this);
//             if (!button.text().includes('My Device') && !button.text().includes('Upload Button')) {
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
//     onload: function(frm) {
//         if (frappe.user_roles.includes('Client')) {
//             // Hide attachment options for clients
//             frm.set_df_property('attached_to_name', 'hidden', true);
//             frm.set_df_property('attached_to_doctype', 'hidden', true);
//             frm.set_df_property('file_url', 'read_only', true); // Disable file URL editing
//         }
//     },
//     refresh: function(frm) {
//         if (frappe.user_roles.includes('Client')) {
//             // Hide attachment options for clients
//             frm.set_df_property('attached_to_name', 'hidden', true);
//             frm.set_df_property('attached_to_doctype', 'hidden', true);
//             frm.set_df_property('file_url', 'read_only', true); // Disable file URL editing
//         }
//     }
// });

// frappe.ui.form.on('File', {
//     refresh: function(frm) {
//         if (frappe.user_roles.includes('Client')) {
//             // Disable the 'is_private' checkbox and ensure it's always checked
//             frm.set_value('is_private', 1);
//             frm.toggle_enable('is_private', false);

//             // Hide the 'Set all public' and 'Set all private' buttons
//             $('.btn-modal-primary').hide(); // Assuming this is the "Set all public" button
//             $('.btn-modal-secondary').hide(); // Assuming this is the "Set all private" button
//         }
//     }
// });

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
