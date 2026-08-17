frappe.ready(function () {
    let currentPage = 1;
    let itemsPerPage = 100;
    let clientName = '';
    let clientCode = '';
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

    function fetchClientDetailsFromQuery() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',
                filters: { owner: frappe.session.user },
                fields: ['client_name', 'client_code'],
                limit: 1
            },
            callback: function (res) {

            if (res.message && res.message.length > 0) {
                // ✅ Display field values, not session user email
                clientName = res.message[0].client_name || client_name;
                clientCode = res.message[0].client_code || client_code;
            } else {
                clientName = 'Unknown Client';
                clientCode = 'N/A';
            }

            // ✅ Show actual field values in the UI
            $('#client-details-heading').html(
                `<b>Client:</b> <b>${clientName}</b> | <b>Code:</b> <b>${clientCode}</b>`
            );



                fetchFilterOptions();
                fetchData();
            }
        });
    }

    function fetchFilterOptions() {
        frappe.call({
            method: 'sanha.api.query_report.get_filter_options',
            callback: function (r) {
                updateDropdown($('#queryTypeFilter'), r.message.query_types || [], "All Query Types");
            }
        });
    }

    function fetchData() {
        const filters = [
            ['owner', '=', frappe.session.user],
            ['workflow_state', 'not in', []]
        ];

        const fromDate = $('#fromDate').val();
        const toDate = $('#toDate').val();
        const queryType = $('#queryTypeFilter').val();

        if (fromDate) filters.push(['creation', '>=', fromDate + ' 00:00:00']);
        if (toDate) filters.push(['creation', '<=', toDate + ' 23:59:59']);
        if (queryType) filters.push(['query_types', 'like', `%${queryType}%`]);


            $('#dataTable').on('keyup', '.col-filter', function () {
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

                    const sortedDates = data.map(d => d.creation).sort();
                    const startDate = frappe.datetime.str_to_user(sortedDates[0]);
                    const endDate = frappe.datetime.str_to_user(sortedDates[sortedDates.length - 1]);
                    $('#date-range').html(`<b>Date Range:</b> <b>${startDate}</b> to <b>${endDate}</b>`);
                } else {
                    tableBody.html(`<tr><td colspan="7" class="text-center">No data found.</td></tr>`);
                    $('#date-range').html('');
                }

                refreshDateRange();
                $('#pageIndicator').text(`Page ${currentPage}`);
            }
        });
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
        const filters = [
            ['owner', '=', frappe.session.user],
            ['workflow_state', 'not in', []]
        ];
        const fromDate = $('#fromDate').val();
        const toDate = $('#toDate').val();
        const queryType = $('#queryTypeFilter').val();
        if (fromDate) filters.push(['creation', '>=', fromDate + ' 00:00:00']);
        if (toDate) filters.push(['creation', '<=', toDate + ' 23:59:59']);
        if (queryType) filters.push(['query_types', 'like', `%${queryType}%`]);

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',
                fields: ['creation'],
                filters: filters,
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

    function openPrint(rows, title = "Print Report", clientDetails, dateRange) {
        const win = window.open('', '_blank');
        win.document.write(`<html><head><title>${title}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;500;700&display=swap');
            @page { margin: 12mm 10mm; }
            * { box-sizing: border-box; }
            html, body { margin: 0; padding: 0; }
            body { font-family: 'Ubuntu', Arial, sans-serif; }
            .header-section {
                padding: 10px 0; margin-top: 0; margin-bottom: 16px;
                border-bottom: 2px solid #14532d; display: flex; width: 100%;
                align-items: center; justify-content: space-between; gap: 20px;
                background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
            }
            .logo-container {
                flex: 0 0 auto;
            }
            .slogan-container {
                text-align: right; flex: 0 1 auto; white-space: nowrap;
            }
            .slogan { font-style: italic; color: #14532d; font-size: 18px; font-weight: 600; }
            .reference-section {
                margin-bottom: 20px; text-align: center; font-size: 14px; font-weight: bold;
            }
            .print-datetime {
                display: block; margin-top: 5px; font-size: 12px; font-weight: normal;
            }
            table {
                width: 100%; border-collapse: collapse; margin-top: 20px; table-layout: auto;
            }
            th, td {
                border: 1px solid #e2e8f0; padding: 7px; text-align: left;
                word-wrap: break-word; word-break: break-word; white-space: normal;
            }
            th { background: #14532d; color: #fff; font-size: 13px; }
            tbody tr:nth-child(even) { background: #f8fafc; }
            td:nth-child(2) { min-width: 150px; max-width: 250px; }
            td:nth-child(3), td:nth-child(4) { min-width: 110px; max-width: 190px; }
            td:nth-child(5) { min-width: 90px; max-width: 150px; }
            td:nth-child(6) { min-width: 70px; max-width: 110px; }
            h3 { text-align: center; margin-top: 20px; }
            .footer-section { margin-top: 30px; padding: 20px; border-top: 2px solid #14532d; text-align: center; }
            .footer-section .disclaimer { text-align: left; font-size: 12px; line-height: 1.6; color: #334155; margin: 0 0 16px; }
            .org-address { margin: 16px 0; }
            .org-address .org-name { font-weight: 700; font-size: 14px; color: #14532d; margin: 0 0 4px; }
            .org-address p { margin: 3px 0; font-size: 12px; color: #475569; }
        </style>
        </head><body>`);

        win.document.write(`
            <div class="header-section">
                <div class="logo-container">
                    <img src="/files/sanha-logo.png" style="width: 150px; height: auto;">
                </div>
                <div class="slogan-container"><span class="slogan">Eat Halal, Be Healthy.</span></div>
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

        win.document.write('<table><thead><tr><th>#</th><th>Raw Material</th><th>Supplier</th><th>Manufacturer</th><th>Query Type</th><th>Status</th></tr></thead><tbody>');

        rows.each(function () {
            const cells = $(this).find('td').slice(1);
            win.document.write('<tr>');
            cells.each(function () {
                win.document.write(`<td>${$(this).html()}</td>`);
            });
            win.document.write('</tr>');
        });

        win.document.write('</tbody></table>');
            // Add footer
    win.document.write(`
    <div class="footer-section">
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 14px 0;">
        <p class="disclaimer"><strong>Disclaimer:</strong> This Halal Evaluation Report is issued based on the information and documentation provided at the time of evaluation. It is valid only for the specified batch/lot and for the specific materials/products mentioned. Any misuse, alteration, or use of this report beyond its intended purpose is strictly prohibited. SANHA Halal Pakistan reserves the right to revoke this evaluation in case of any non-compliance or deviation from the Halal standards.</p>
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 14px 0;">
        <div class="org-address">
            <p class="org-name">Sanha Halal Associates Pakistan (Pvt.) Ltd.</p>
            <p>Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama Commercial Lane 5, D.H.A. Phase 5, Karachi, Pakistan</p>
            <p>Tel: +92 21 35295263 &nbsp;|&nbsp; Email: evaluation@sanha.org.pk</p>
        </div>
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 14px 0;">
        <span style="font-size: 12px; color: #94a3b8;">&copy; 2023 SANHA. All rights reserved.</span>
    </div>
    </body></html>`);

        win.document.close();
        win.onload = function () {
            win.print();
            win.close();
        };
    }

    // Event Bindings
    $('#fromDate, #toDate').on('change', () => { currentPage = 1; fetchData(); });
    $('#queryTypeFilter').on('change', () => { currentPage = 1; fetchData(); });
    // $('#itemsPerPage').on('change', function () {
    //     itemsPerPage = parseInt(this.value);
    //     currentPage = 1;
    //     fetchData();
    // });
    $('#prevPage').on('click', () => { if (currentPage > 1) { currentPage--; fetchData(); } });
    $('#nextPage').on('click', () => { currentPage++; fetchData(); });

    // $('#printBtn').on('click', () => {
    //     const rows = $('#dataTable tbody tr');
    //     openPrint(rows);
    // });
    $('#printBtn').on('click', () => {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Query',
            fields: [
                'name', 'client_name', 'client_code', 
                'raw_material', 'supplier', 'manufacturer', 
                'query_types', 'workflow_state', 'creation'
            ],
            filters: [
                ['owner', '=', frappe.session.user],
                ['workflow_state', 'not in', []]
            ],
            order_by: 'raw_material, creation asc',
            limit_page_length: 0 // ⚡ fetch ALL records
        },
        callback: function (r) {
            const data = r.message || [];
            if (data.length === 0) {
                frappe.msgprint('No records found to print.');
                return;
            }

            // Build rows exactly like fetchData() does
            const tempTable = $('<tbody>');
            data.forEach((row, i) => {
                const tr = $('<tr>');
                tr.attr('data-creation', row.creation || '');
                tr.append(`<td><input type="checkbox" class="row-checkbox" data-id="${row.name}"></td>`);
                tr.append(`<td>${i + 1}</td>`); // ✅ Serial number preserved
                tr.append(`<td>${row.raw_material || ''}</td>`);
                tr.append(`<td>${row.supplier || ''}</td>`);
                tr.append(`<td>${row.manufacturer || ''}</td>`);
                tr.append(`<td>${row.query_types || ''}</td>`);
                tr.append(`<td>${row.workflow_state || ''}</td>`);
                tempTable.append(tr);
            });

            // ✅ Pass all rows to your existing print function
            const sortedDates = data.map(d => d.creation).filter(Boolean).sort();
            const dateRange = sortedDates.length
                ? `<b>Date Range:</b> <b>${frappe.datetime.str_to_user(sortedDates[0])}</b> to <b>${frappe.datetime.str_to_user(sortedDates[sortedDates.length - 1])}</b>`
                : '<b>Date Range:</b> <b>N/A</b>';
            openPrint(tempTable.find('tr'), "Query Report", $('#client-details-heading').html(), dateRange);
        }
    });
});


    $('#printBtnSelected').on('click', () => {
        const selected = $('.row-checkbox:checked').closest('tr');
        const rows = selected.length > 0 ? selected : $('#dataTable tbody tr');
        if (rows.length === 0) {
            frappe.msgprint('No records found to print.');
            return;
        }
        const sortedDates = rows.map(function () { return $(this).data('creation'); }).get().filter(Boolean).sort();
        const dateRange = sortedDates.length
            ? `<b>Date Range:</b> <b>${frappe.datetime.str_to_user(sortedDates[0])}</b> to <b>${frappe.datetime.str_to_user(sortedDates[sortedDates.length - 1])}</b>`
            : '<b>Date Range:</b> <b>N/A</b>';
        openPrint(rows, "Selected Queries", $('#client-details-heading').html(), dateRange);
    });

    $('#selectAll').on('change', function () {
        $('.row-checkbox').prop('checked', this.checked);
        refreshDateRange();
    });

    // Init
    $('#pagePrintDateTime').text(formatPrintDateTime(new Date()));
    fetchClientDetailsFromQuery();
});
                