// /www/query-report-preview/index.js

frappe.ready(function () {
    // ---------------- SAMPLE DATA (mock, no backend calls) ----------------
    var SAMPLE_CLIENTS = ['Shan Foods (Pvt) Ltd', 'National Foods Ltd', 'Engro Foods', 'Tapal Tea', 'Colgate-Palmolive'];
    var SAMPLE_TYPES = ['Flavour', 'Spices', 'Dairy Ingredient', 'Beverage', 'Personal Care'];
    var SAMPLE_STATUS = ['Submitted', 'Approved', 'Halal', 'Haram', 'Rejected', 'Hold', 'Doubtful'];
    var SAMPLE_RAW = ['Salt', 'Sugar', 'Palm Oil', 'Chilli Powder', 'Turmeric', 'Milk Powder', 'Lemon Flavour', 'Cocoa Butter', 'Gelatin', 'Citric Acid', 'Soy Lecithin', 'Vanilla Extract'];
    var SAMPLE_SUPPLIER = ['ABC Traders', 'Gulf Spice Co', 'Prime Ingredients', 'Punjab Foods', 'Global Flavors Ltd'];
    var SAMPLE_MANUFACTURER = ['Archer Daniels Midland', 'Cargill', 'Tate & Lyle', 'Symrise', 'Kerry Group'];

    function mockQueries() {
        var rows = [];
        var n = 240;
        for (var i = 0; i < n; i++) {
            var day = String(1 + (i % 28)).padStart(2, '0');
            var month = String(1 + ((i * 7) % 12)).padStart(2, '0');
            var year = 2026;
            rows.push({
                name: 'Q-' + (1000 + i),
                client_name: SAMPLE_CLIENTS[i % SAMPLE_CLIENTS.length],
                client_code: 'C-' + (101 + (i % SAMPLE_CLIENTS.length)),
                raw_material: SAMPLE_RAW[i % SAMPLE_RAW.length],
                supplier: SAMPLE_SUPPLIER[(i * 3) % SAMPLE_SUPPLIER.length],
                manufacturer: SAMPLE_MANUFACTURER[(i * 5) % SAMPLE_MANUFACTURER.length],
                query_types: SAMPLE_TYPES[i % SAMPLE_TYPES.length],
                workflow_state: SAMPLE_STATUS[i % SAMPLE_STATUS.length],
                creation: year + '-' + month + '-' + day + ' 09:' + String(i % 60).padStart(2, '0') + ':00'
            });
        }
        return rows;
    }

    // ---------------- STATE ----------------
    var ALL_DATA = mockQueries();
    var currentPage = 1;
    var itemsPerPage = 100;
    var tableBody = $('#dataTable tbody');

    // ---------------- HELPERS ----------------
    function formatPrintDateTime(d) {
        d = d || new Date();
        var pad = function (n) { return (n < 10 ? '0' + n : n); };
        var hours = d.getHours();
        var ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12 || 12;
        return pad(d.getDate()) + '-' + pad(d.getMonth() + 1) + '-' + d.getFullYear() + ' ' + pad(hours) + ':' + pad(d.getMinutes()) + ' ' + ampm;
    }
    function formatUserDate(iso) {
        var d = new Date(iso);
        if (isNaN(d)) return '';
        var pad = function (n) { return (n < 10 ? '0' + n : n); };
        return pad(d.getDate()) + '-' + pad(d.getMonth() + 1) + '-' + d.getFullYear();
    }
    function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
    function buildFilters() {
        var f = [];
        var client = $('#clientFilter').val();
        var qtype = $('#queryTypeFilter').val();
        var from = $('#fromDate').val();
        var to = $('#toDate').val();
        if (from) f.push(function (r) { return r.creation.slice(0, 10) >= from; });
        if (to) f.push(function (r) { return r.creation.slice(0, 10) <= to; });
        if (client) f.push(function (r) { return r.client_name === client; });
        if (qtype) f.push(function (r) { return r.query_types === qtype; });
        return { testers: f, client: client };
    }
    function fetchFiltered() {
        var filters = buildFilters();
        return ALL_DATA.filter(function (r) { return filters.testers.every(function (fn) { return fn(r); }); });
    }
    function fillOptions(sel, values, defaultLabel) {
        sel.empty().append($('<option>').val('').text(defaultLabel));
        values.forEach(function (v) { sel.append($('<option>').val(v).text(v)); });
    }

    // ---------------- FETCH / RENDER ----------------
    function fetchData() {
        var data = fetchFiltered();
        var pageSize = itemsPerPage === 0 ? data.length : itemsPerPage;
        var maxPage = Math.max(1, Math.ceil(data.length / pageSize));
        if (currentPage > maxPage) currentPage = maxPage;
        var pageData = data.slice((currentPage - 1) * pageSize, (currentPage - 1) * pageSize + pageSize);

        tableBody.empty();
        if (pageData.length) {
            pageData.forEach(function (row, i) {
                var tr = $('<tr>').attr('data-creation', row.creation).attr('data-client', row.client_name);
                tr.append('<td><input type="checkbox" class="row-checkbox" data-id="' + esc(row.name) + '"></td>');
                tr.append('<td>' + ((currentPage - 1) * pageSize + i + 1) + '</td>');
                tr.append('<td>' + esc(row.raw_material) + '</td>');
                tr.append('<td>' + esc(row.supplier) + '</td>');
                tr.append('<td>' + esc(row.manufacturer) + '</td>');
                tr.append('<td>' + esc(row.query_types) + '</td>');
                tr.append('<td>' + esc(row.workflow_state) + '</td>');
                tableBody.append(tr);
            });
        } else {
            tableBody.html('<tr><td colspan="7" class="text-center">No data found.</td></tr>');
        }
        updateSummary(pageData, buildFilters().client);
        $('#pageIndicator').text('Page ' + currentPage);
    }
    function updateSummary(rows, client) {
        var code = 'N/A';
        if (client) {
            var found = ALL_DATA.find(function (r) { return r.client_name === client; });
            if (found) code = found.client_code;
        }
        $('#client-details-heading').html('<b>Client:</b> <b>' + esc(client || 'All') + '</b> | <b>Code:</b> <b>' + esc(code) + '</b>');
        if (rows.length) {
            var dates = rows.map(function (r) { return r.creation; }).sort();
            $('#date-range').html('<b>Date Range:</b> <b>' + formatUserDate(dates[0]) + '</b> to <b>' + formatUserDate(dates[dates.length - 1]) + '</b>');
        } else {
            $('#date-range').html('');
        }
    }

    // ---------------- PRINT (fresh window) ----------------
    function openPrint(rows, title, clientDetails, dateRange) {
        var win = window.open('', '_blank');
        var html = [
            '<html><head><title>' + title + '</title><style>',
            '@import url("https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;500;700&display=swap");',
            '@page { margin: 12mm 10mm; }',
            '* { box-sizing: border-box; }',
            'html, body { margin: 0; padding: 0; }',
            'body { font-family: "Ubuntu", Arial, sans-serif; }',
            '.header-section { padding: 10px 0; margin-top: 0; margin-bottom: 16px; border-bottom: 1px solid #ccc; display: flex; width: 100%; align-items: center; justify-content: space-between; gap: 20px; }',
            '.logo-container { flex: 0 0 auto; }',
            '.slogan-container { text-align: right; flex: 0 1 auto; white-space: nowrap; }',
            '.slogan { font-style: italic; color: #14532d; font-size: 18px; font-weight: 600; }',
            '.reference-section { margin-bottom: 20px; text-align: center; font-size: 14px; font-weight: bold; }',
            '.print-datetime { display: block; margin-top: 5px; font-size: 12px; font-weight: normal; }',
            'table { width: 100%; border-collapse: collapse; margin-top: 20px; table-layout: auto; }',
            'th, td { border: 1px solid #333; padding: 6px; text-align: left; word-wrap: break-word; word-break: break-word; white-space: normal; }',
            'td:nth-child(2) { min-width: 150px; max-width: 250px; }',
            'td:nth-child(3), td:nth-child(4) { min-width: 110px; max-width: 190px; }',
            'td:nth-child(5) { min-width: 90px; max-width: 150px; }',
            'td:nth-child(6) { min-width: 70px; max-width: 110px; }',
            '.footer-section { margin-top: 30px; text-align: center; padding: 20px; border-top: 1px solid #ccc; }',
            '</style></head><body>',

            '<div class="header-section">',
            '<div class="logo-container"><img src="/files/sanha-logo.png" style="width: 150px; height: auto;"></div>',
            '<div class="slogan-container"><span class="slogan">Eat Halal, Be Healthy.</span></div>',
            '</div>',

            '<div class="reference-section"><span>SANHA/PR-09/FM-01</span>',
            '<span class="print-datetime"><strong>Print Date/Time:</strong> ' + formatPrintDateTime(new Date()) + '</span></div>',

            '<div style="text-align:center;margin-top:10px;margin-bottom:20px;">',
            '<p style="margin:5px 0;">' + (clientDetails || '<b>Client:</b> <b>All</b> | <b>Code:</b> <b>N/A</b>') + '</p>',
            '<p style="margin:5px 0;">' + (dateRange || '<b>Date Range:</b> <b>N/A</b>') + '</p>',
            '</div>',

            '<table><thead><tr><th>#</th><th>Raw Material</th><th>Supplier</th><th>Manufacturer</th><th>Query Type</th><th>Status</th></tr></thead><tbody>'
        ].join('');

        rows.forEach(function (row, i) {
            html += '<tr><td>' + (i + 1) + '</td><td>' + esc(row.raw_material) + '</td><td>' + esc(row.supplier) + '</td><td>' + esc(row.manufacturer) + '</td><td>' + esc(row.query_types) + '</td><td>' + esc(row.workflow_state) + '</td></tr>';
        });

        html += '</tbody></table>' +
            '<div class="footer-section"><hr>' +
            '<p style="margin:0;font-size:12px;text-align:left;line-height:1.6;color:#334155;"><strong>Disclaimer:</strong> This Halal Evaluation Report is issued based on the information and documentation provided at the time of evaluation. It is valid only for the specified batch/lot and for the specific materials/products mentioned. Any misuse, alteration, or use of this report beyond its intended purpose is strictly prohibited. SANHA Halal Pakistan reserves the right to revoke this evaluation in case of any non-compliance or deviation from the Halal standards.</p>' +
            '<hr>' +
            '<p style="margin:0;font-weight:bold;color:#14532d;">Sanha Halal Associates Pakistan (Pvt.) Ltd.</p>' +
            '<p style="margin:3px 0;font-size:12px;color:#475569;">Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama Commercial Lane 5, D.H.A. Phase 5, Karachi, Pakistan</p>' +
            '<p style="margin:3px 0;font-size:12px;color:#475569;">Tel: +92 21 35295263 &nbsp;|&nbsp; Email: evaluation@sanha.org.pk</p>' +
            '<hr><span style="font-size:12px;color:#94a3b8;">&copy; 2023 SANHA. All rights reserved.</span>' +
            '</div></body></html>';

        win.document.open();
        win.document.write(html);
        win.document.close();
        win.onload = function () { win.print(); };
        return win;
    }

    // ---------------- HANDLERS ----------------
    $('#printBtn').on('click', function () {
        var data = fetchFiltered();
        if (!data.length) { frappe.msgprint('No records found to print.'); return; }
        var client = buildFilters().client;
        var clientDetails = client
            ? '<b>Client:</b> <b>' + esc(client) + '</b> | <b>Code:</b> <b>' + esc(ALL_DATA.find(function (r) { return r.client_name === client; }).client_code) + '</b>'
            : '<b>Client:</b> <b>All</b> | <b>Code:</b> <b>N/A</b>';
        var dates = data.map(function (r) { return r.creation; }).sort();
        var dateRange = '<b>Date Range:</b> <b>' + formatUserDate(dates[0]) + '</b> to <b>' + formatUserDate(dates[dates.length - 1]) + '</b>';
        openPrint(data, 'Query Report', clientDetails, dateRange);
    });

    $('#printBtnSelected').on('click', function () {
        var checked = $('.row-checkbox:checked');
        var client = $('#clientFilter').val();

        if (checked.length > 0) {
            // PART A: exactly the checked rows
            var rows = checked.map(function () {
                var tr = $(this).closest('tr');
                var cells = tr.children();
                return {
                    raw_material: cells.eq(2).text(),
                    supplier: cells.eq(3).text(),
                    manufacturer: cells.eq(4).text(),
                    query_types: cells.eq(5).text(),
                    workflow_state: cells.eq(6).text(),
                    creation: tr.attr('data-creation'),
                    client_name: tr.attr('data-client')
                };
            }).get();
            var clientDetails = client
                ? '<b>Client:</b> <b>' + esc(client) + '</b> | <b>Code:</b> <b>N/A</b>'
                : '<b>Client:</b> <b>All</b> | <b>Code:</b> <b>N/A</b>';
            var dates = rows.map(function (r) { return r.creation; }).sort();
            var dateRange = '<b>Date Range:</b> <b>' + formatUserDate(dates[0]) + '</b> to <b>' + formatUserDate(dates[dates.length - 1]) + '</b>';
            openPrint(rows, 'Selected Queries', clientDetails, dateRange);
            return;
        }

        // PART B: nothing checked -> all rows for the selected client
        var data = fetchFiltered();
        if (!data.length) { frappe.msgprint('No records found to print.'); return; }
        var clientDetails2 = client
            ? '<b>Client:</b> <b>' + esc(client) + '</b> | <b>Code:</b> <b>' + esc(ALL_DATA.find(function (r) { return r.client_name === client; }).client_code) + '</b>'
            : '<b>Client:</b> <b>All</b> | <b>Code:</b> <b>N/A</b>';
        var dates2 = data.map(function (r) { return r.creation; }).sort();
        var dateRange2 = '<b>Date Range:</b> <b>' + formatUserDate(dates2[0]) + '</b> to <b>' + formatUserDate(dates2[dates2.length - 1]) + '</b>';
        openPrint(data, 'Query Report', clientDetails2, dateRange2);
    });

    $('#selectAll').on('change', function () {
        $('.row-checkbox').prop('checked', this.checked);
        refreshDateRange();
    });

    // Live update of the date range: uses selected rows when any are checked, else the rendered page rows
    function refreshDateRange() {
        var checked = $('.row-checkbox:checked');
        var dates;
        if (checked.length) {
            dates = checked.map(function () {
                return $(this).closest('tr').attr('data-creation');
            }).get().filter(Boolean);
        } else {
            dates = tableBody.find('tr').map(function () {
                return $(this).attr('data-creation');
            }).get().filter(Boolean);
        }
        dates.sort();
        $('#date-range').html(dates.length
            ? '<b>Date Range:</b> <b>' + formatUserDate(dates[0]) + '</b> to <b>' + formatUserDate(dates[dates.length - 1]) + '</b>'
            : '<b>Date Range:</b> <b>N/A</b>');
    }
    $('#dataTable').on('change', '.row-checkbox', refreshDateRange);

    $('#dataTable').on('keyup', '.col-filter', function () {
        var col = parseInt($(this).data('column'));
        var txt = $(this).val().toLowerCase();
        $('#dataTable tbody tr').each(function () {
            var cell = $(this).find('td').eq(col).text().toLowerCase();
            $(this).toggle(cell.includes(txt));
        });
    });

    $('#clientFilter, #queryTypeFilter, #fromDate, #toDate').on('change', function () { currentPage = 1; fetchData(); });
    $('#itemsPerPage').on('change', function () {
        itemsPerPage = parseInt(this.value);
        currentPage = 1;
        fetchData();
    });
    $('#prevPage').on('click', function () { if (currentPage > 1) { currentPage--; fetchData(); } });
    $('#nextPage').on('click', function () { currentPage++; fetchData(); });

    // ---------------- INIT ----------------
    $('#pagePrintDateTime').text(formatPrintDateTime(new Date()));
    fillOptions($('#clientFilter'), SAMPLE_CLIENTS, 'All Clients');
    fillOptions($('#queryTypeFilter'), SAMPLE_TYPES, 'All Query Types');
    fetchData();
});