// sm_report.js

frappe.query_reports["SM Report"] = {
    "filters": [
        {
            "fieldname": "query_types",
            "label": __("Query Types"),
            "fieldtype": "Link",
            "options": "Query Types",
            "default": "",
        },
    ],

    onload: function (report) {
        // Customization of the header section to add the logo and client information
        const header = $(report.page.main.find(".page-header-content"));
        header.empty().append(`
            <div style="text-align: center;">
                <img src="/files/your_logo.png" alt="Company Logo" style="width: 150px;"/>
                <h3>Client Information</h3>
                <div>Client Name: ${frappe.user.full_name}</div>
                <div>Client Code: ${frappe.user.user_code}</div>
            </div>
        `);
    },

    formatter: function (value, row, column, data, default_formatter) {
        // This handles specific row customizations if needed.
        if (column.fieldname === "query_status" && data.query_status !== "Draft") {
            value = `<span style="color: green;">${value}</span>`;
        }
        return default_formatter(value, row, column, data);
    }
};
