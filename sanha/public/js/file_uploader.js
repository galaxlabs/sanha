frappe.ui.form.ControlAttach = frappe.ui.form.ControlAttach.extend({
    make_input() {
      this._super();
      this.$input_wrapper.append(`
        <div class="file-upload-area">
          <button class="btn btn-file-upload" id="upload-from-device">
            My Device
          </button>
          <input type="file" id="file-input" style="display: none;" />
        </div>
      `);
  
      // Event listener for file input
      this.$wrapper.on('click', '#upload-from-device', () => {
        $('#file-input').click();
      });
  
      $('#file-input').on('change', (e) => {
        let file = e.target.files[0];
        if (file) {
          this.upload_file(file);
        }
      });
    },
  
    upload_file(file) {
      // Custom file upload logic
      let formData = new FormData();
      formData.append('file', file);
  
      frappe.call({
        method: 'sanha.api.upload_file',
        args: {
          file: formData,
        },
        callback: (response) => {
          if (response.message) {
            frappe.msgprint(__('File uploaded successfully'));
          }
        },
      });
    },
  });
  