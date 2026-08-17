frappe.ready(function () {
    let currentPage = 1;
    let itemsPerPage = 100;

    const tableBody = $('#dataTable tbody');

    function formatPrintDateTime(d) {
        d = d || new Date();
        const pad = n => (n < 10 ? '0' + n : n);
        const day = pad(d.getDate());
        const month = pad(d.getMonth() + 1);
        const year = d.getFullYear();
        let hours = d.getHours();
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12 || 12;
        return `${day}-${month}-${year} ${pad(hours)}:${pad(d.getMinutes())} ${ampm}`;
    }

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
                        tr.attr('data-creation', row.creation || '');
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
                } else {
                    tableBody.html(`<tr><td colspan="6" class="text-center">No data found.</td></tr>`);
                    $('#client-details-heading').html('<b>Client:</b> <b>All</b> | <b>Code:</b> <b>N/A</b>');
                }

                refreshDateRange();
                $('#pageIndicator').text(`Page ${currentPage}`);
            }
        });
    }

    // Live update of the date range: uses selected rows when any are checked, else the current filtered data
    function refreshDateRange() {
        const checked = $('.row-checkbox:checked');
        let dates;
        if (checked.length) {
            dates = checked.closest('tr').map(function () {
                return $(this).data('creation');
            }).get().filter(Boolean);
        } else {
            dates = tableBody.find('tr').map(function () {
                return $(this).data('creation');
            }).get().filter(Boolean);
        }
        dates.sort();
        $('#date-range').html(dates.length
            ? `<b>Date Range:</b> <b>${frappe.datetime.str_to_user(dates[0])}</b> to <b>${frappe.datetime.str_to_user(dates[dates.length - 1])}</b>`
            : '<b>Date Range:</b> <b>N/A</b>');
    }

    // ✅ Local print function – used by "Print All", "Print Selected" and client fallback
    function openPrint(rows, title = "Print Report", clientDetails, dateRange) {
        const win = window.open('', '_blank');

        win.document.write(`
            <html>
            <head>
                <title>${title}</title>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;500;700&display=swap');
                    body { font-family: 'Ubuntu', Arial, sans-serif; }
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
                    .reference-section {
                        margin-bottom: 20px;
                        text-align: center;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    .print-datetime {
                        display: block;
                        margin-top: 5px;
                        font-size: 12px;
                        font-weight: normal;
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

        // Reference + print date/time (SANHA/PR-09/FM-01)
        const printDateTime = formatPrintDateTime(new Date());
        win.document.write(`
            <div class="reference-section">
                <span>SANHA/PR-09/FM-01</span>
                <span class="print-datetime"><strong>Print Date/Time:</strong> ${printDateTime}</span>
            </div>
        `);

        // Client details -- Date range
        const clientDetailsHtml = clientDetails || $('#client-details-heading').html() || '<b>Client:</b> <b>All</b> | <b>Code:</b> <b>N/A</b>';
        const dateRangeHtml = dateRange || $('#date-range').html() || '<b>Date Range:</b> <b>N/A</b>';
        win.document.write(`
            <div style="text-align: center; margin-top: 10px; margin-bottom: 20px;">
                <p style="margin: 5px 0;">${clientDetailsHtml}</p>
                <p style="margin: 5px 0;">${dateRangeHtml}</p>
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
                <p style="margin: 0; font-size: 12px; text-align: left; line-height: 1.6; color: #334155;"><strong>Disclaimer:</strong> This Halal Evaluation Report is issued based on the information and documentation provided at the time of evaluation. It is valid only for the specified batch/lot and for the specific materials/products mentioned. Any misuse, alteration, or use of this report beyond its intended purpose is strictly prohibited. SANHA Halal Pakistan reserves the right to revoke this evaluation in case of any non-compliance or deviation from the Halal standards.</p>
                <hr>
                <p style="margin: 0; font-weight: bold; color: #14532d;">Sanha Halal Associates Pakistan (Pvt.) Ltd.</p>
                <p style="margin: 3px 0; font-size: 12px; color: #475569;">Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama Commercial Lane 5, D.H.A. Phase 5, Karachi, Pakistan</p>
                <p style="margin: 3px 0; font-size: 12px; color: #475569;">Tel: +92 21 35295263 &nbsp;|&nbsp; Email: evaluation@sanha.org.pk</p>
                <hr>
                <span style="font-size: 12px; color: #94a3b8;">&copy; 2023 SANHA. All rights reserved.</span>
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

    // Live update of the date range: uses selected rows when any are checked, else the full filtered set
    function refreshDateRange() {
        const checked = $('.row-checkbox:checked');
        if (checked.length) {
            const dates = checked.closest('tr').map(function () {
                return $(this).data('creation');
            }).get().filter(Boolean).sort();
            $('#date-range').html(dates.length
                ? `<b>Date Range:</b> <b>${frappe.datetime.str_to_user(dates[0])}</b> to <b>${frappe.datetime.str_to_user(dates[dates.length - 1])}</b>`
                : '<b>Date Range:</b> <b>N/A</b>');
            return;
        }
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',
                fields: ['creation'],
                filters: buildFilters().filters,
                order_by: 'creation asc',
                limit_page_length: 0
            },
            callback: function (r) {
                const dates = (r.message || []).map(d => d.creation).filter(Boolean).sort();
                $('#date-range').html(dates.length
                    ? `<b>Date Range:</b> <b>${frappe.datetime.str_to_user(dates[0])}</b> to <b>${frappe.datetime.str_to_user(dates[dates.length - 1])}</b>`
                    : '<b>Date Range:</b> <b>N/A</b>');
            }
        });
    }
    $('#dataTable').on('change', '.row-checkbox', refreshDateRange);

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
                    tr.attr('data-creation', row.creation || '');
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

    // ✅ PRINT SELECTED – selected rows from current page, or whole selected client if none checked
    $('#printBtnSelected').on('click', () => {
        const selected = $('.row-checkbox:checked').closest('tr');
        if (selected.length > 0) {
            // PART A: print exactly the checked rows
            const rows = selected;
            const sortedDates = rows.map(function () { return $(this).data('creation'); }).get().sort();
            const client = $('#clientFilter').val();
            const clientDetails = client
                ? `<b>Client:</b> <b>${client}</b> | <b>Code:</b> <b>N/A</b>`
                : '<b>Client:</b> <b>All</b> | <b>Code:</b> <b>N/A</b>';
            const dateRange = sortedDates.length
                ? `<b>Date Range:</b> <b>${frappe.datetime.str_to_user(sortedDates[0])}</b> to <b>${frappe.datetime.str_to_user(sortedDates[sortedDates.length - 1])}</b>`
                : '<b>Date Range:</b> <b>N/A</b>';
            openPrint(rows, "Selected Queries", clientDetails, dateRange);
            return;
        }

        // PART B: nothing checked -> print all data for the selected client (respect filters)
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',
                fields: ['name', 'client_name', 'client_code', 'raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state', 'creation'],
                filters: buildFilters().filters,
                order_by: 'raw_material, creation asc',
                limit_page_length: 0
            },
            callback: function (r) {
                const data = r.message || [];
                if (!data.length) {
                    frappe.msgprint('No records found to print.');
                    return;
                }
                const tempTable = $('<tbody>');
                data.forEach((row, i) => {
                    const tr = $('<tr>');
                    tr.append(`<td><input type="checkbox" class="row-checkbox" data-id="${row.name}"></td>`);
                    tr.append(`<td>${i + 1}</td>`);
                    tr.append(`<td>${row.raw_material || ''}</td>`);
                    tr.append(`<td>${row.supplier || ''}</td>`);
                    tr.append(`<td>${row.manufacturer || ''}</td>`);
                    tr.append(`<td>${row.query_types || ''}</td>`);
                    tr.append(`<td>${row.workflow_state || ''}</td>`);
                    tempTable.append(tr);
                });

                const client = buildFilters().client;
                const clientDetails = client
                    ? `<b>Client:</b> <b>${client}</b> | <b>Code:</b> <b>${data[0].client_code || 'N/A'}</b>`
                    : '<b>Client:</b> <b>All</b> | <b>Code:</b> <b>N/A</b>';
                const sortedDates = data.map(d => d.creation).sort();
                const dateRange = sortedDates.length
                    ? `<b>Date Range:</b> <b>${frappe.datetime.str_to_user(sortedDates[0])}</b> to <b>${frappe.datetime.str_to_user(sortedDates[sortedDates.length - 1])}</b>`
                    : '<b>Date Range:</b> <b>N/A</b>';
                openPrint(tempTable.find('tr'), "Query Report", clientDetails, dateRange);
            }
        });
    });

    $('#selectAll').on('change', function () {
        $('.row-checkbox').prop('checked', this.checked);
        refreshDateRange();
    });

    // Init
    $('#pagePrintDateTime').text(formatPrintDateTime(new Date()));
    fetchFilterOptions();
    fetchData();
});
