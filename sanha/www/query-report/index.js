frappe.ready(function () {
    let currentPage = 1;
    let itemsPerPage = 100;

    const tableBody = $('#dataTable tbody');

    function updateDropdown(dropdown, values, defaultLabel) {
        dropdown.empty().append(`<option value="">${defaultLabel}</option>`);
        values.forEach(val => dropdown.append(`<option value="${val}">${val}</option>`));
    }

    function fetchFilterOptions() {
        frappe.call({
            method: 'sanha.api.query_report.get_filter_options',
            callback: function (r) {
                updateDropdown($('#clientFilter'), r.message.clients || [], "All Clients");
                updateDropdown($('#queryTypeFilter'), r.message.query_types || [], "All Query Types");
            }
        });
    }

    function fetchData() {
        const filters = [['workflow_state', 'not in', ['Draft']]];
        const client = $('#clientFilter').val();
        const queryType = $('#queryTypeFilter').val();
        const fromDate = $('#fromDate').val();
        const toDate = $('#toDate').val();

        if (fromDate) {
            filters.push(['creation', '>=', fromDate + ' 00:00:00']);
        }
        if (toDate) {
            filters.push(['creation', '<=', toDate + ' 23:59:59']);
        }


        if (client) filters.push(['client_name', 'like', `%${client}%`]);
        if (queryType) filters.push(['query_types', 'like', `%${queryType}%`]);

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',
                fields: ['name', 'client_name', 'client_code', 'raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state', 'creation'],
                filters: filters,
                limit_start: (currentPage - 1) * itemsPerPage,
                limit_page_length: itemsPerPage,
                order_by: 'raw_material, creation asc'
            },
            callback: function (r) {
                const data = r.message || [];
                tableBody.empty();

                if (data.length > 0) {
                    data.forEach((row, i) => {
                        const tr = $('<tr>');
                        tr.append(`<td><input type="checkbox" class="row-checkbox" data-id="${row.name}"></td>`);
                        tr.append(`<td>${(currentPage - 1) * itemsPerPage + i + 1}</td>`);
                        tr.append(`<td>${row.raw_material || ''}</td>`);
                        tr.append(`<td>${row.supplier || ''}</td>`);
                        tr.append(`<td>${row.manufacturer || ''}</td>`);
                        tr.append(`<td>${row.query_types || ''}</td>`);
                        tr.append(`<td>${row.workflow_state || ''}</td>`);
                        tableBody.append(tr);
                    });

                 
                    const selectedClient = client;
                    const foundClient = data.find(d => d.client_name === selectedClient);
                    const code = foundClient?.client_code || 'N/A';
                    $('#client-details-heading').html(`<b>Client:</b> <b>${selectedClient || 'All'}</b> | <b>Code:</b> <b>${code}</b>`);

                    const startDate = frappe.datetime.str_to_user(data[0].creation);
                    const endDate = frappe.datetime.str_to_user(data[data.length - 1].creation);
                    $('#date-range').html(`<b>Date Range:</b> <b>${startDate}</b> to <b>${endDate}</b>`);
                } else {
                    tableBody.html(`<tr><td colspan="6" class="text-center">No data found.</td></tr>`);
                }

                $('#pageIndicator').text(`Page ${currentPage}`);
            }
        });
    }

    function openPrint(rows, title = "Print Report") {
    const win = window.open('', '_blank');

    win.document.write(`<html>
    <head>
        <title>${title}</title>
        <style>
            body { font-family: Arial, sans-serif; }
            .header-section {
                padding: 20px;
                margin-top: 30px;
                margin-bottom: 20px;
                border-bottom: 1px solid rgb(204, 204, 204);
                display: table;
                width: 100%;
            }
            .logo-container {
                display: table-cell;
                text-align: right;
                width: 55%;
                margin-top: 20px;
            }
            .slogan-container {
                display: table-cell;
                text-align: right;
                vertical-align: middle;
                width: 45%;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                border: 1px solid #333;
                padding: 6px;
                text-align: left;
            }
            h3 {
                text-align: center;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>`);

    // Header with logo and slogan
    win.document.write(`
        <div class="header-section">
            <div class="logo-container">
                <img src="/files/sanha-logo.png" style="width: 150px; height: auto;">
            </div>
            <div class="slogan-container">
                <span>Eat Halal, Be Healthy.</span>
            </div>
        </div>
    `);

    // Page Title
    win.document.write('<h3>Query Report</h3>');

    // Start table
    win.document.write('<table><thead><tr><th>#</th><th>Raw Material</th><th>Supplier</th><th>Manufacturer</th><th>Query Type</th><th>Status</th></tr></thead><tbody>');

    // Add rows
    rows.each(function () {
        const cells = $(this).find('td').slice(1); // Skip checkbox if present
        win.document.write('<tr>');
        cells.each(function () {
            win.document.write(`<td>${$(this).html()}</td>`);
        });
        win.document.write('</tr>');
    });

    // End HTML
    win.document.write('</tbody></table></body></html>');
    win.document.close();

    // Wait for content to load before printing
    win.onload = function () {
        win.print();
        win.close();
    };
}

    // Event bindings]
    $('#fromDate, #toDate').on('change', () => { currentPage = 1; fetchData(); });
    $('#clientFilter, #queryTypeFilter').on('change', () => { currentPage = 1; fetchData(); });
    $('#itemsPerPage').on('change', function () {
        itemsPerPage = parseInt(this.value); currentPage = 1; fetchData();
    });
    $('#prevPage').on('click', () => { if (currentPage > 1) { currentPage--; fetchData(); } });
    $('#nextPage').on('click', () => { currentPage++; fetchData(); });

    $('#printBtn').on('click', () => {
        const rows = $('#dataTable tbody tr');
        openPrint(rows);
    });

    $('#printBtnSelected').on('click', () => {
        const selected = $('.row-checkbox:checked').closest('tr');
        if (selected.length === 0) {
            frappe.msgprint('Please select at least one record to print.');
            return;
        }
        openPrint(selected);
    });

    $('#selectAll').on('change', function () {
        $('.row-checkbox').prop('checked', this.checked);
    });

    fetchFilterOptions();
    fetchData();
});
// frappe.ready(function () {
//     let currentPage = 1;
//     const itemsPerPage = 100;

    

//     const clientDropdown = $('#clientFilter');
//     const queryTypeDropdown = $('#queryTypeFilter');
//     const dateRangeDiv = $('#date-range');
//     const tableBody = $('#dataTable tbody');

//     function updateDropdown(dropdown, values, defaultLabel) {
//         dropdown.empty().append(`<option value="">${defaultLabel}</option>`);
//         values.forEach(val => {
//             dropdown.append(`<option value="${val}">${val}</option>`);
//         });
//     }

//     function fetchFilterOptions() {
//         frappe.call({
//             method: 'sanha.api.query_report.get_filter_options',
//             callback: function (r) {
//                 const filters = r.message || {};
//                 const clients = filters.clients || [];
//                 const queryTypes = filters.query_types || [];

//                 updateDropdown(clientDropdown, clients, "All Clients");
//                 updateDropdown(queryTypeDropdown, queryTypes, "All Query Types");
//             }
//         });
//     }

//     function fetchData() {
//         const client = clientDropdown.val();
//         const queryType = queryTypeDropdown.val();

//         const filters = [['workflow_state', 'not in', ['Draft']]];

//         if (client) filters.push(['client_name', 'like', `%${client}%`]);
//         if (queryType) filters.push(['query_types', 'like', `%${queryType}%`]);

//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 fields: ['name', 'client_name', 'client_code', 'raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state', 'creation'],
//                 filters: filters,
//                 limit_start: (currentPage - 1) * itemsPerPage,
//                 limit_page_length: itemsPerPage,
//                 order_by: 'creation asc'
//             },
//             callback: function (r) {
//                 const data = r.message || [];
//                 tableBody.empty();

//                 if (data.length > 0) {
//                     data.forEach((row, i) => {
//                         const tr = $('<tr>');
//                         tr.append(`<td>${(currentPage - 1) * itemsPerPage + i + 1}</td>`);
//                         tr.append(`<td>${row.raw_material || ''}</td>`);
//                         tr.append(`<td>${row.supplier || ''}</td>`);
//                         tr.append(`<td>${row.manufacturer || ''}</td>`);
//                         tr.append(`<td>${row.query_types || ''}</td>`);
//                         tr.append(`<td>${row.workflow_state || ''}</td>`);
//                         tableBody.append(tr);
//                     });

//                     const selectedClient = clientDropdown.val();
//                     if (selectedClient) {
//                         // Try to find the first match for the client code from data
//                         const clientData = data.find(d => d.client_name === selectedClient);
//                         const clientCode = clientData?.client_code || 'N/A';
            
//                         $('#client-details-heading').html(
//                             `<div>👤 <b>Client:</b> ${selectedClient} | 🆔 <b>Code:</b> ${clientCode}</div>`
//                         );
//                     } else {
//                         $('#client-details-heading').empty();
//                     }

//                     const startDate = frappe.datetime.str_to_user(data[0].creation);
//                     const endDate = frappe.datetime.str_to_user(data[data.length - 1].creation);

//                     dateRangeDiv.html(`<strong>Date Range:</strong> From <b>${startDate}</b> to <b>${endDate}</b>`);
//                 } else {
//                     tableBody.append(`<tr><td colspan="6" class="text-center">No data found.</td></tr>`);
//                     dateRangeDiv.html(`<strong>Date Range:</strong> No records found.`);
//                 }

//                 $('#pageIndicator').text(`Page ${currentPage}`);
//             }
//         });
//     }

//     // Pagination
//     $('#prevPage').click(() => {
//         if (currentPage > 1) {
//             currentPage--;
//             fetchData();
//         }
//     });

//     $('#nextPage').click(() => {
//         currentPage++;
//         fetchData();
//     });

//     clientDropdown.on('change', () => {
//         currentPage = 1;
//         fetchData();
//     });

//     queryTypeDropdown.on('change', () => {
//         currentPage = 1;
//         fetchData();
//     });

//     // Initial setup
//     fetchFilterOptions();
//     fetchData();
// });

// // /www/query/index.js

// frappe.ready(function () {
//     let currentPage = 1;
//     const itemsPerPage = 100;

//     const clientDropdown = $('#clientFilter');
//     const queryTypeDropdown = $('#queryTypeFilter');
//     const dateRangeDiv = $('#date-range');
//     const tableBody = $('#dataTable tbody');

//     function fetchDistinctField(field, callback) {
//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 fields: [field],
//                 distinct: 1,
//                 limit_page_length: 999
//             },
//             callback: function (r) {
//                 const values = new Set();
//                 (r.message || []).forEach(row => {
//                     const val = row[field];
//                     if (val) {
//                         if (field === 'query_types') {
//                             val.split(',').map(q => q.trim()).forEach(t => values.add(t));
//                         } else {
//                             values.add(val);
//                         }
//                     }
//                 });
//                 callback(Array.from(values));
//             }
//         });
//     }

//     function updateDropdown(dropdown, values) {
//         dropdown.empty().append(`<option value="">All</option>`);
//         values.forEach(v => {
//             dropdown.append(`<option value="${v}">${v}</option>`);
//         });
//     }

//     function fetchData() {
//         const client = clientDropdown.val();
//         const queryType = queryTypeDropdown.val();

//         const filters = [
//             ['workflow_state', 'not in', ['Draft']]
//         ];

//         if (client) filters.push(['client_name', 'like', `%${client}%`]);
//         if (queryType) filters.push(['query_types', 'like', `%${queryType}%`]);

//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 fields: ['name', 'raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state', 'creation'],
//                 filters: filters,
//                 limit_start: (currentPage - 1) * itemsPerPage,
//                 limit_page_length: itemsPerPage,
//                 order_by: 'creation asc'
//             },
//             callback: function (r) {
//                 const data = r.message || [];
//                 tableBody.empty();

//                 if (data.length > 0) {
//                     data.forEach((row, i) => {
//                         const tr = $('<tr>');
//                         tr.append(`<td>${(currentPage - 1) * itemsPerPage + i + 1}</td>`);
//                         tr.append(`<td>${row.raw_material || ''}</td>`);
//                         tr.append(`<td>${row.supplier || ''}</td>`);
//                         tr.append(`<td>${row.manufacturer || ''}</td>`);
//                         tr.append(`<td>${row.query_types || ''}</td>`);
//                         tr.append(`<td>${row.workflow_state || ''}</td>`);
//                         tableBody.append(tr);
//                     });

//                     const startDate = frappe.datetime.str_to_user(data[0].creation);
//                     const endDate = frappe.datetime.str_to_user(data[data.length - 1].creation);

//                     dateRangeDiv.html(`<strong>Date Range:</strong> From <b>${startDate}</b> to <b>${endDate}</b>`);
//                 } else {
//                     tableBody.append(`<tr><td colspan="6" class="text-center">No data found.</td></tr>`);
//                     dateRangeDiv.html(`<strong>Date Range:</strong> No records found.`);
//                 }

//                 $('#pageIndicator').text(`Page ${currentPage}`);
//             }
//         });
//     }

//     $('#prevPage').click(() => {
//         if (currentPage > 1) {
//             currentPage--;
//             fetchData();
//         }
//     });

//     $('#nextPage').click(() => {
//         currentPage++;
//         fetchData();
//     });

//     clientDropdown.on('change', () => {
//         currentPage = 1;
//         fetchData();
//     });

//     queryTypeDropdown.on('change', () => {
//         currentPage = 1;
//         fetchData();
//     });

//     // Initial population
//     fetchDistinctField('client_name', clients => updateDropdown(clientDropdown, clients));
//     fetchDistinctField('query_types', types => updateDropdown(queryTypeDropdown, types));

//     fetchData();
// });
