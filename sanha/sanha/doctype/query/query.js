// Copyright (c) 2024, Sanha Halal Pakistan and contributors
// For license information, please see license.txt

const QUERY_REQUIRED_BEFORE_DOCUMENTS = ["query_types", "raw_material"];

frappe.dom.set_style(`
  .mandatory-documents-glow {
    box-shadow: 0 0 0 3px rgba(255,165,0,0.35);
    border-radius: 6px;
    transition: box-shadow 0.2s ease;
  }
`);

function query_header_is_complete(frm) {
  return QUERY_REQUIRED_BEFORE_DOCUMENTS.every((fieldname) => Boolean(frm.doc[fieldname]));
}

function glow_documents_table(frm) {
  const field = frm.get_field("documents");
  if (!field || !field.wrapper) return;

  frappe.utils.scroll_to(field.wrapper);
  $(field.wrapper).addClass("mandatory-documents-glow");
  setTimeout(() => $(field.wrapper).removeClass("mandatory-documents-glow"), 4000);
}

function update_documents_gate(frm) {
  const can_show_documents = !frm.is_new() && query_header_is_complete(frm);

  frm.toggle_display("documents", can_show_documents);
  frm.set_df_property("documents", "read_only", can_show_documents ? 0 : 1);

  frm.dashboard.clear_headline();
}

function ensure_documents_row_and_focus(frm) {
  if (!frm.doc.documents || !frm.doc.documents.length) {
    frm.add_child("documents", {});
    frm.refresh_field("documents");
  }

  const field = frm.get_field("documents");
  if (!field || !field.grid) return;

  glow_documents_table(frm);

  setTimeout(() => {
    const row = field.grid.grid_rows && field.grid.grid_rows[0];
    if (!row) return;

    const $input = $(row.row).find('[data-fieldname="documents"] input');
    if ($input.length) $input.focus();
  }, 250);
}

function remove_duplicate_document_attachments(frm) {
  const seen = new Set();
  const duplicates = [];

  (frm.doc.documents || []).forEach((row) => {
    if (!row.attachment) return;
    if (seen.has(row.attachment)) {
      duplicates.push(row);
      return;
    }
    seen.add(row.attachment);
  });

  duplicates.forEach((row) => frappe.model.clear_doc(row.doctype, row.name));

  if (duplicates.length) {
    frm.refresh_field("documents");
    frappe.show_alert({
      message: __("Duplicate attachment rows removed."),
      indicator: "orange",
    });
  }
}

frappe.ui.form.on("Query", {
  onload(frm) {
    update_documents_gate(frm);
  },

  refresh(frm) {
    update_documents_gate(frm);
    frm.events.try_autosave_and_show_documents(frm);
  },

  raw_material(frm) {
    update_documents_gate(frm);
    frm.events.try_autosave_and_show_documents(frm);
  },

  query_types(frm) {
    update_documents_gate(frm);
    frm.events.try_autosave_and_show_documents(frm);
  },

  validate(frm) {
    remove_duplicate_document_attachments(frm);
  },

  try_autosave_and_show_documents(frm) {
    if (!frm.is_new()) return;
    if (frm.__sanha_autosaving || frm.__sanha_autosaved_once) return;
    if (!query_header_is_complete(frm)) return;

    frm.__sanha_autosaving = true;

    frm.save()
      .then(() => {
        frm.__sanha_autosaved_once = true;
        update_documents_gate(frm);
        ensure_documents_row_and_focus(frm);

        frappe.show_alert({
          message: __("Record created. Add Documents and upload attachments."),
          indicator: "green",
        });
      })
      .finally(() => {
        frm.__sanha_autosaving = false;
      });
  },
});

frappe.ui.form.on("Documents", {
  attachment(frm) {
    remove_duplicate_document_attachments(frm);
  },
});
