// Copyright (c) 2024, Sanha Halal Pakistan and contributors
// For license information, please see license.txt

const QUERY_REQUIRED_BEFORE_DOCUMENTS = ["query_types", "raw_material"];
const CLIENT_EDITABLE_QUERY_STATES = new Set(["Draft", "Returned"]);

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
  const client_can_edit =
    !frappe.user.has_role("Client") ||
    CLIENT_EDITABLE_QUERY_STATES.has(frm.doc.workflow_state || "Draft");

  frm.toggle_display("documents", can_show_documents);
  frm.set_df_property("documents", "read_only", can_show_documents && client_can_edit ? 0 : 1);

  frm.dashboard.clear_headline();
}

function hide_standard_query_attachments(frm) {
  if (!frappe.user.has_role("Client")) return;

  const hide_attachments = () => {
    if (frm.attachments && frm.attachments.parent) {
      $(frm.attachments.parent).hide();
    }

    $(frm.page.wrapper)
      .find(".form-attachments, .attachments-actions, .add-attachment-btn")
      .hide();
  };

  hide_attachments();
  setTimeout(hide_attachments, 0);
}

function remember_saved_document_attachments(frm) {
  if (frm.is_new() || (frm.is_dirty && frm.is_dirty())) return;

  frm.__sanha_saved_document_attachments = new Map(
    (frm.doc.documents || []).map((row) => [row.name, row.attachment || ""]),
  );
}

async function preserve_replaced_attachment(frm, cdt, cdn) {
  if (frm.__sanha_preserving_attachment || !frappe.user.has_role("Client")) return false;
  if (!CLIENT_EDITABLE_QUERY_STATES.has(frm.doc.workflow_state || "Draft")) return false;

  const row = locals[cdt][cdn];
  const previous_attachment = frm.__sanha_saved_document_attachments?.get(row.name);
  if (!previous_attachment || !row.attachment || row.attachment === previous_attachment) return false;

  const new_attachment = row.attachment;
  frm.__sanha_preserving_attachment = true;

  try {
    await frappe.model.set_value(cdt, cdn, "attachment", previous_attachment);
    frm.add_child("documents", {
      documents: row.documents,
      issue_date: null,
      expiry_date: null,
      attachment: new_attachment,
    });
    frm.refresh_field("documents");
    frappe.show_alert({
      message: __("The previous file was kept. Complete the dates in the new Documents row."),
      indicator: "blue",
    });
    return true;
  } finally {
    frm.__sanha_preserving_attachment = false;
  }
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
    hide_standard_query_attachments(frm);
    remember_saved_document_attachments(frm);
    update_documents_gate(frm);
  },

  refresh(frm) {
    hide_standard_query_attachments(frm);
    remember_saved_document_attachments(frm);
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
  async attachment(frm, cdt, cdn) {
    if (await preserve_replaced_attachment(frm, cdt, cdn)) return;
    remove_duplicate_document_attachments(frm);
  },
});
