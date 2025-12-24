// Copyright (c) 2024, Sanha Halal Pakistan  and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Query", {
// 	refresh(frm) {

// 	},
// });

// one-time CSS (highlight box around the child table)
// frappe.ui.form.on('Query', {
//   refresh(frm) {
//     const is_new = frm.is_new();

//     // Always show table
//     frm.toggle_display('documents', true);

//     // If new: block adding rows + show message
//     if (is_new) {
//       frm.set_df_property('documents', 'read_only', 1);

//       frm.dashboard.set_headline(`
//         <div class="text-muted">
//           Please save this Query first. After saving, you can add Documents and upload attachments.
//         </div>
//       `);
//     } else {
//       frm.set_df_property('documents', 'read_only', 0);
//       frm.dashboard.clear_headline();
//     }
//   }
// });

// frappe.dom.set_style(`
//   .mandatory-documents-glow{
//     box-shadow: 0 0 0 3px rgba(255,165,0,0.35);
//     border-radius: 6px;
//     transition: box-shadow 0.2s ease;
//   }
// `);

// function ensure_documents_row_and_focus(frm) {
//   // if no row, add one
//   if (!frm.doc.documents || !frm.doc.documents.length) {
//     frm.add_child("documents", {});
//     frm.refresh_field("documents");
//   }

//   const field = frm.get_field("documents");
//   if (!field || !field.grid) return;

//   // scroll to table + glow
//   frappe.utils.scroll_to(field.wrapper);
//   $(field.wrapper).addClass("mandatory-documents-glow");
//   setTimeout(() => $(field.wrapper).removeClass("mandatory-documents-glow"), 4000);

//   // focus first row -> "documents" link input
//   setTimeout(() => {
//     const grid = field.grid;
//     const row = grid.grid_rows && grid.grid_rows[0];
//     if (!row) return;

//     // OPTIONAL: open row form (if you prefer row form view)
//     // row.toggle_view(true);

//     const $inp = $(row.row).find('[data-fieldname="documents"] input');
//     if ($inp.length) $inp.focus();
//   }, 200);
// }

// frappe.ui.form.on("Query", {
//   refresh(frm) {
//     // UX: auto add row only on new doc
//     if (frm.is_new()) {
//       ensure_documents_row_and_focus(frm);
//     }
//   },

//   validate(frm) {
//     // UX safety: if user removed all rows, re-add and stop save (server will also block)
//     if (!frm.doc.documents || !frm.doc.documents.length) {
//       ensure_documents_row_and_focus(frm);
//       frappe.msgprint(__("Please fill at least one row in Documents before saving."));
//       frappe.validated = false;
//     }
//   }
// });
// Query Client Script
// Feature: Auto-save on required fields -> show Documents table -> auto add 1 row -> highlight + focus first row field

frappe.dom.set_style(`
  .mandatory-documents-glow{
    box-shadow: 0 0 0 3px rgba(255,165,0,0.35);
    border-radius: 6px;
    transition: box-shadow 0.2s ease;
  }
`);

function glow_documents_table(frm) {
  const f = frm.get_field("documents");
  if (!f || !f.wrapper) return;

  frappe.utils.scroll_to(f.wrapper);
  $(f.wrapper).addClass("mandatory-documents-glow");
  setTimeout(() => $(f.wrapper).removeClass("mandatory-documents-glow"), 4000);
}

function ensure_documents_row_and_focus(frm) {
  // add row if empty
  if (!frm.doc.documents || !frm.doc.documents.length) {
    frm.add_child("documents", {});
    frm.refresh_field("documents");
  }

  const field = frm.get_field("documents");
  if (!field || !field.grid) return;

  glow_documents_table(frm);

  // focus first row -> "documents" link input
  setTimeout(() => {
    const grid = field.grid;
    const row = grid.grid_rows && grid.grid_rows[0];
    if (!row) return;

    // focus the first row's 'documents' link input
    const $inp = $(row.row).find('[data-fieldname="documents"] input');
    if ($inp.length) $inp.focus();
  }, 250);
}

frappe.ui.form.on("Query", {
  onload(frm) {
    if (frm.is_new()) {
      frm.toggle_display("documents", false);
      frm.set_df_property("documents", "read_only", 1);
    }
  },

  refresh(frm) {
    if (!frm.is_new()) {
      frm.toggle_display("documents", true);
      frm.set_df_property("documents", "read_only", 0);
      frm.dashboard.clear_headline();
      return;
    }

    frm.toggle_display("documents", false);
    frm.set_df_property("documents", "read_only", 1);

    frm.dashboard.set_headline(`
      <div class="text-muted">
        Fill <b>Query Types</b> and <b>Raw Material</b>. The record will auto-save, then Documents will appear.
      </div>
    `);

    frm.events.try_autosave_and_show_documents(frm);
  },

  raw_material(frm) {
    frm.events.try_autosave_and_show_documents(frm);
  },

  query_types(frm) {
    frm.events.try_autosave_and_show_documents(frm);
  },

  try_autosave_and_show_documents(frm) {
    if (!frm.is_new()) return;
    if (frm.__sanha_autosaving || frm.__sanha_autosaved_once) return;

    // required for autosave
    if (!frm.doc.raw_material) return;
    if (!frm.doc.query_types) return;

    frm.__sanha_autosaving = true;

    frm.save()
      .then(() => {
        frm.__sanha_autosaved_once = true;

        // show + enable table
        frm.toggle_display("documents", true);
        frm.set_df_property("documents", "read_only", 0);
        frm.dashboard.clear_headline();

        // ✅ after save: auto add row + highlight + focus
        ensure_documents_row_and_focus(frm);

        frappe.show_alert({
          message: __("Record created. Add Documents and upload attachments."),
          indicator: "green"
        });
      })
      .finally(() => {
        frm.__sanha_autosaving = false;
      });
  }
});

// frappe.ui.form.on("Query", {
//   onload(frm) {
//     // For new docs: hide documents table until first auto-save
//     if (frm.is_new()) {
//       frm.toggle_display("documents", false);
//       frm.set_df_property("documents", "read_only", 1);
//     }
//   },

//   refresh(frm) {
//     // If already saved, always show and allow
//     if (!frm.is_new()) {
//       frm.toggle_display("documents", true);
//       frm.set_df_property("documents", "read_only", 0);
//       frm.dashboard.clear_headline();
//       return;
//     }

//     // New: keep hidden until autosave
//     frm.toggle_display("documents", false);
//     frm.set_df_property("documents", "read_only", 1);

//     frm.dashboard.set_headline(`
//       <div class="text-muted">
//         Fill <b>Raw Material</b> (and Query Type if required). The record will auto-save and then Documents will appear.
//       </div>
//     `);

//     // in case fields already filled
//     frm.events.try_autosave_and_show_documents(frm);
//   },

//   // Trigger when raw material changed
//   raw_material(frm) {
//     frm.events.try_autosave_and_show_documents(frm);
//   },

//   // If Query Types is also required, trigger on it too
//   query_types(frm) {
//     frm.events.try_autosave_and_show_documents(frm);
//   },

//   try_autosave_and_show_documents(frm) {
//     // only for new docs
//     if (!frm.is_new()) return;

//     // prevent repeated saves
//     if (frm.__sanha_autosaving || frm.__sanha_autosaved_once) return;

//     // require fields before autosave
//     // Raw Material is required
//     if (!frm.doc.raw_material) return;

//     // Query Types is required in your DocType, so keep this check
//     if (!frm.doc.query_types) return;

//     frm.__sanha_autosaving = true;

//     frm.save()
//       .then(() => {
//         frm.__sanha_autosaved_once = true;

//         // Now doc has real name (Query-0000...), so enable table + show it
//         frm.toggle_display("documents", true);
//         frm.set_df_property("documents", "read_only", 0);
//         frm.dashboard.clear_headline();

//         frappe.show_alert({
//           message: __("Record created. You can now add Documents and upload attachments."),
//           indicator: "green"
//         });
//       })
//       .finally(() => {
//         frm.__sanha_autosaving = false;
//       });
//   }
// });







