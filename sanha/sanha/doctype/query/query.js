// Copyright (c) 2024, Sanha Halal Pakistan  and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Query", {
// 	refresh(frm) {

// 	},
// });

// one-time CSS (highlight box around the child table)
frappe.dom.set_style(`
  .mandatory-documents-glow{
    box-shadow: 0 0 0 3px rgba(255,165,0,0.35);
    border-radius: 6px;
    transition: box-shadow 0.2s ease;
  }
`);

function ensure_documents_row_and_focus(frm) {
  // if no row, add one
  if (!frm.doc.documents || !frm.doc.documents.length) {
    frm.add_child("documents", {});
    frm.refresh_field("documents");
  }

  const field = frm.get_field("documents");
  if (!field || !field.grid) return;

  // scroll to table + glow
  frappe.utils.scroll_to(field.wrapper);
  $(field.wrapper).addClass("mandatory-documents-glow");
  setTimeout(() => $(field.wrapper).removeClass("mandatory-documents-glow"), 4000);

  // focus first row -> "documents" link input
  setTimeout(() => {
    const grid = field.grid;
    const row = grid.grid_rows && grid.grid_rows[0];
    if (!row) return;

    // OPTIONAL: open row form (if you prefer row form view)
    // row.toggle_view(true);

    const $inp = $(row.row).find('[data-fieldname="documents"] input');
    if ($inp.length) $inp.focus();
  }, 200);
}

frappe.ui.form.on("Query", {
  refresh(frm) {
    // UX: auto add row only on new doc
    if (frm.is_new()) {
      ensure_documents_row_and_focus(frm);
    }
  },

  validate(frm) {
    // UX safety: if user removed all rows, re-add and stop save (server will also block)
    if (!frm.doc.documents || !frm.doc.documents.length) {
      ensure_documents_row_and_focus(frm);
      frappe.msgprint(__("Please fill at least one row in Documents before saving."));
      frappe.validated = false;
    }
  }
});







