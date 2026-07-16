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

    function buildFilters() {
        const filters = [['workflow_state', 'not in', []]];
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

        return { filters, client };
    }

    function fetchData() {
        const { filters, client } = buildFilters();

        // Column filter (note: ideally bind once, but this is ok for now)
        $('#dataTable').off('keyup', '.col-filter').on('keyup', '.col-filter', function () {
            const columnIndex = $(this).data('column');
            const filterText = $(this).val().toLowerCase();

            $('#dataTable tbody tr').each(function () {
                const cellText = $(this).find('td').eq(columnIndex).text().toLowerCase();
                if (cellText.includes(filterText)) {
                    $(this).show();
                } else {
                    $(this).hide();
                }
            });
        });

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',
                fields: [
                    'name', 'client_name', 'client_code',
                    'raw_material', 'supplier', 'manufacturer',
                    'query_types', 'workflow_state', 'creation'
                ],
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
                    $('#client-details-heading').html(
                        `<b>Client:</b> <b>${selectedClient || 'All'}</b> | <b>Code:</b> <b>${code}</b>`
                    );

                    const sortedDates = data.map(d => d.creation).sort();  // ascending
                    const startDate = frappe.datetime.str_to_user(sortedDates[0]);
                    const endDate = frappe.datetime.str_to_user(sortedDates[sortedDates.length - 1]);
                    $('#date-range').html(
                        `<b>Date Range:</b> <b>${startDate}</b> to <b>${endDate}</b>`
                    );
                } else {
                    tableBody.html(`<tr><td colspan="6" class="text-center">No data found.</td></tr>`);
                    $('#date-range').html('');
                    $('#client-details-heading').html('<b>Client:</b> <b>All</b> | <b>Code:</b> <b>N/A</b>');
                }

                $('#pageIndicator').text(`Page ${currentPage}`);
            }
        });
    }

    // ✅ Local print function – used by both "Print All" and "Print Selected"
    function openPrint(rows, title = "Print Report") {
        const win = window.open('', '_blank');

        win.document.write(`
            <html>
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
                        word-wrap: break-word;
                        word-break: break-word;
                        white-space: normal;
                    }
                    table { table-layout: auto; }
                    td:nth-child(2) { min-width: 150px; max-width: 250px; }
                    td:nth-child(3), td:nth-child(4) { min-width: 110px; max-width: 190px; }
                    td:nth-child(5) { min-width: 90px; max-width: 150px; }
                    td:nth-child(6) { min-width: 70px; max-width: 110px; }
                    h3 {
                        text-align: center;
                        margin-top: 20px;
                    }
                    .footer-section {
                        margin-top: 30px;
                        text-align: center;
                        padding: 20px;
                        border-top: 1px solid rgb(204, 204, 204);
                    }
                </style>
            </head>
            <body>
        `);

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

        // Client details -- Date range (read from current page DOM)
        const clientDetails = $('#client-details-heading').html() || '<b>Client:</b> <b>All</b> | <b>Code:</b> <b>N/A</b>';
        const dateRange = $('#date-range').html() || '<b>Date Range:</b> <b>N/A</b>';
        win.document.write(`
            <div style="text-align: center; margin-top: 10px; margin-bottom: 20px;">
                <p style="margin: 5px 0;">${clientDetails}</p>
                <p style="margin: 5px 0;">${dateRange}</p>
            </div>
        `);

        // Start table
        win.document.write(`
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Raw Material</th>
                        <th>Supplier</th>
                        <th>Manufacturer</th>
                        <th>Query Type</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
        `);

        // Add rows
        rows.each(function () {
            const cells = $(this).find('td').slice(1); // Skip checkbox column
            win.document.write('<tr>');
            cells.each(function () {
                win.document.write(`<td>${$(this).html()}</td>`);
            });
            win.document.write('</tr>');
        });

        // End table + footer
        win.document.write(`
                </tbody>
            </table>
            <div class="footer-section">
                <hr>
                <p style="margin: 0;">Sanha Halal Associates Pakistan PVT. LTD.</p>
                <p style="margin: 0;">Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama D.H.A. phase 5</p>
                <p style="margin: 0;">Email: evaluation@sanha.org.pk - Ph: +92 21 35295263</p>
                <hr>
                <span>&copy; 2023 SANHA. All rights reserved.</span>
            </div>
            </body>
            </html>
        `);

        win.document.close();

        win.onload = function () {
            win.print();
            win.close();
        };
    }

    // 🔁 Event bindings
    $('#fromDate, #toDate').on('change', () => { currentPage = 1; fetchData(); });
    $('#clientFilter, #queryTypeFilter').on('change', () => { currentPage = 1; fetchData(); });
    $('#itemsPerPage').on('change', function () {
        itemsPerPage = parseInt(this.value);
        currentPage = 1;
        fetchData();
    });
    $('#prevPage').on('click', () => { if (currentPage > 1) { currentPage--; fetchData(); } });
    $('#nextPage').on('click', () => { currentPage++; fetchData(); });

    // ✅ PRINT ALL – fetch ALL matching records (ignore pagination)
    $('#printBtn').on('click', () => {
        const { filters, client } = buildFilters();

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',
                fields: [
                    'name', 'client_name', 'client_code',
                    'raw_material', 'supplier', 'manufacturer',
                    'query_types', 'workflow_state', 'creation'
                ],
                filters: filters,
                order_by: 'raw_material, creation asc',
                limit_page_length: 0      // ⚡ fetch ALL records
            },
            callback: function (r) {
                const data = r.message || [];
                if (!data.length) {
                    frappe.msgprint('No records found to print.');
                    return;
                }

                // Build temp table body for ALL rows
                const tempTable = $('<tbody>');
                data.forEach((row, i) => {
                    const tr = $('<tr>');
                    tr.append(`<td><input type="checkbox" class="row-checkbox" data-id="${row.name}"></td>`);
                    tr.append(`<td>${i + 1}</td>`); // serial across all
                    tr.append(`<td>${row.raw_material || ''}</td>`);
                    tr.append(`<td>${row.supplier || ''}</td>`);
                    tr.append(`<td>${row.manufacturer || ''}</td>`);
                    tr.append(`<td>${row.query_types || ''}</td>`);
                    tr.append(`<td>${row.workflow_state || ''}</td>`);
                    tempTable.append(tr);
                });

                // Update client + date range to reflect ALL records (for header)
                const selectedClient = client;
                let code = 'N/A';
                if (selectedClient) {
                    const foundClient = data.find(d => d.client_name === selectedClient);
                    if (foundClient) {
                        code = foundClient.client_code || 'N/A';
                    }
                }
                $('#client-details-heading').html(
                    `<b>Client:</b> <b>${selectedClient || 'All'}</b> | <b>Code:</b> <b>${code}</b>`
                );

                const sortedDates = data.map(d => d.creation).sort();
                const startDate = frappe.datetime.str_to_user(sortedDates[0]);
                const endDate = frappe.datetime.str_to_user(sortedDates[sortedDates.length - 1]);
                $('#date-range').html(
                    `<b>Date Range:</b> <b>${startDate}</b> to <b>${endDate}</b>`
                );

                // Print ALL rows
                openPrint(tempTable.find('tr'), "Query Report");
            }
        });
    });

    // ✅ PRINT SELECTED – only selected rows from current page
    $('#printBtnSelected').on('click', () => {
        const selected = $('.row-checkbox:checked').closest('tr');
        if (selected.length === 0) {
            frappe.msgprint('Please select at least one record to print.');
            return;
        }
        openPrint(selected, "Selected Queries");
    });

    $('#selectAll').on('change', function () {
        $('.row-checkbox').prop('checked', this.checked);
    });

    // Init
    fetchFilterOptions();
    fetchData();
});
