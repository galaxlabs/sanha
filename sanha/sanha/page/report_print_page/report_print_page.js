frappe.pages['report-print-page'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Report Print Page',
        single_column: true
    });
	var action_section = $('<div>').addClass('action-section').appendTo(page.body);

    // Print button
    var printButton = $('<button>').text('Print').addClass('btn btn-primary').appendTo(action_section);
    printButton.on('click', function() {
        // Hide page title before printing
        page.$title_area.hide();
        // Hide filter row before printing
        $('.filter-row').hide();
        // Hide filter section before printing
        $('.filter-section').hide();
        // Print the page
        $('.pagination-section').hide();
        $('.action-section').hide();
        

        window.print();
        // Show page title after printing
        page.$title_area.show();
        // Show filter row after printing
        $('.filter-row').show();
        // Show filter section after printing
        $('.filter-section').show();
        $('.pagination-section').show();
        $('.action-section').show();

    });
    // Align action buttons to the right
    action_section.css({
        'display': 'flex',
        'justify-content': 'flex-end', // Align items to the right
        'margin-bottom': '10px' // Add margin below action section
    });

    var header_section = $('<div>').addClass('header-section').appendTo(page.body);
    header_section.css({
        'padding': '20px',
        'margin-bottom': '20px',
        'border-bottom': '1px solid #ccc',
        'display': 'table',
        'width': '100%'
    });

    var logo_container = $('<div>').addClass('logo-container').appendTo(header_section);
    logo_container.css({
        'display': 'table-cell',
        'text-align': 'right',
        'width': '55%'
    });
    var logo = $('<img>').attr('src', 'http://portal.sanha.org.pk/assets/dist/img/sanha-logo.png').addClass('img').appendTo(logo_container);
    logo.css({
        'width': '150px',
        'height': 'auto'
    });

    var slogan_container = $('<div>').addClass('slogan-container').appendTo(header_section);
    slogan_container.css({
        'display': 'table-cell',
        'text-align': 'right',
        'vertical-align': 'middle',
        'width': '45%'
    });
    $('<span>').text('Eat Halal, Be Healthy.').appendTo(slogan_container);
    var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
    filterSection.css({
        'margin-bottom': '35px', // Add margin below the filter section
        'display': 'flex',
        'justify-content': 'space-between', // Align items with space between
        'align-items': 'center' // Align items at the center vertically
    });
    
    // Query type selection dropdown
    var queryTypeDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
    queryTypeDropdown.append('<option>Select Query Type</option>');


    var owner_table_section_container = $('<div>').appendTo(page.body);

    var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(owner_table_section_container);
    owner_table_section.css({
        'margin-bottom': '20px',
        'text-align': 'center'
    });
    
    // Date range section
    var date_range_section_container = $('<div>').appendTo(page.body);
    $('<hr>').appendTo(date_range_section_container);
    var date_range_section = $('<div>').addClass('date-range-section').appendTo(date_range_section_container);
    date_range_section.css({
        'margin-bottom': '20px',
        'text-align': 'center'
    });

    var data_section = $('<div>').addClass('data-section').appendTo(page.body);
    data_section.css({
        'margin-bottom': '20px',
        'display': 'flex',
        'align-items': 'center',
        'flex-wrap': 'wrap'
    });

    var table = $('<table>').addClass('table').appendTo(data_section);
    var thead = $('<thead>').appendTo(table);
    var tbody = $('<tbody>').appendTo(table);
    var tableHeaders = ['Raw Material', 'Supplier', 'Manufacturer', 'Status'];

    var headerRow = $('<tr>').appendTo(thead);
    tableHeaders.forEach(function(label) {
        $('<th>').text(label).appendTo(headerRow);
    });

    var filterRow = $('<tr>').addClass('filter-row').appendTo(thead);
    tableHeaders.forEach(function(label) {
        $('<td>').append($('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label)).appendTo(filterRow);
    });

    var pagination_section = $('<div>').addClass('pagination-section').appendTo(page.body);
    pagination_section.css({
        'display': 'flex',
        'justify-content': 'center',
        'margin-top': '20px'
    });

    var prevButton = $('<button>').text('Previous').addClass('btn btn-secondary').appendTo(pagination_section);
    var nextButton = $('<button>').text('Next').addClass('btn btn-secondary').appendTo(pagination_section);
    
    prevButton.css({
        'order': '1', // Display the "Previous" button first
        'margin-right': 'auto' // Push the "Previous" button to the left
    });
    
    nextButton.css({
        'order': '2' // Display the "Next" button second
    });
    

    var currentPage = 1;
    var itemsPerPage = 50;

    function fetchAllData(doctype, fields, filters, callback) {
        var start = 0;
        var limit = 500;
        var allData = [];

        function fetchData() {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: doctype,
                    fields: fields,
                    filters: filters,
                    limit_start: start,
                    limit_page_length: limit,
                    order_by: 'raw_material asc'
                },
                callback: function(response) {
                    var data = response.message;
                    if (data.length > 0) {
                        allData = allData.concat(data);
                        start += limit;
                        fetchData();
                    } else {
                        callback(allData);
                    }
                }
            });
        }

        fetchData();
    }

    // Populate query type dropdown
    fetchAllData('Query', ['query_types'], [], function(queryTypes) {
        var uniqueQueryTypes = new Set();
        queryTypes.forEach(function(query) {
            if (query.query_types) {
                query.query_types.split(',').forEach(function(type) {
                    type = type.trim();
                    if (type) uniqueQueryTypes.add(type);
                });
            }
        });
        uniqueQueryTypes.forEach(function(type) {
            $('<option>').text(type).appendTo(queryTypeDropdown);
        });
    });

    // Fetch and display data for the session user
    function fetchData(page, limit) {
        var filters = {
            workflow_state: ['!=', 'Draft'],
            owner: frappe.session.user
        };

        if (queryTypeDropdown.val() !== 'Select Query Type') {
            filters.query_types = ['like', '%' + queryTypeDropdown.val() + '%'];
        }

        var additionalFilters = {};
        filterRow.find('input').each(function(index) {
            var value = $(this).val();
            if (value) {
                var fieldMap = {
                    'Raw Material': 'raw_material',
                    'Supplier': 'supplier',
                    'Manufacturer': 'manufacturer',
                    'Status': 'workflow_state'
                };
                var field = fieldMap[tableHeaders[index]];
                if (field) {
                    additionalFilters[field] = ['like', '%' + value + '%'];
                }
            }
        });

        Object.assign(filters, additionalFilters);

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',
                fields: ['raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types'],
                filters: filters,
                limit_start: (page - 1) * limit,
                limit_page_length: limit,
                order_by: 'raw_material asc'
            },
            callback: function(response) {
                var data = response.message;
                tbody.empty();

                var groupedData = {};
                data.forEach(function(row) {
                    var queryType = row.query_types || 'Unknown';
                    if (!groupedData[queryType]) {
                        groupedData[queryType] = [];
                    }
                    groupedData[queryType].push(row);
                });

                for (var queryType in groupedData) {
                    $('<tr>').append($('<td colspan="4">').text(queryType).css('font-weight', 'bold')).appendTo(tbody);
                    groupedData[queryType].forEach(function(row) {
                        var tableRow = $('<tr>').appendTo(tbody);
                        tableHeaders.forEach(function(key) {
                            var field = key.toLowerCase().replace(' ', '_');
                            if (field === 'status') field = 'workflow_state';
                            if (field === 'creation') {
                                var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
                                $('<td>').text(formattedDate).appendTo(tableRow);
                            } else {
                                $('<td>').text(row[field]).appendTo(tableRow);
                            }
                        });
                    });
                }

                updateDateRange(filters);
            }
        });
    }

    // Update owner table based on session user queries
    function updateOwnerTable() {
        owner_table_section.empty();
        var uniqueClients = new Set();
    
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',
                filters: {
                    owner: frappe.session.user,
                    client_name: ['!=', ''], // Filter out null client names
                    client_code: ['!=', ''] // Filter out null client codes
                },
                fields: ['client_name', 'client_code']
            },
            callback: function(response) {
                if (response.message.length > 0) {
                    var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
                    var tbody = $('<tbody>').appendTo(ownerTable);
    
                    response.message.forEach(function(query) {
                        var clientName = query.client_name;
                        var clientCode = query.client_code;
                        var clientIdentifier = clientName + clientCode;
                        if (!uniqueClients.has(clientIdentifier)) {
                            uniqueClients.add(clientIdentifier);
    
                            // Create table for owner data with specific format
                            var first_row = $('<tr>').appendTo(tbody);
                            var first_row_data = $('<td>').addClass('text-center').appendTo(first_row);
                            $('<h2>').text('Account: ' + clientName + ' (Code: ' + clientCode + ')').appendTo(first_row_data);
                        }
                    });
                } else {
                    // If no data, show a message
                    $('<p>').text('No client data available').appendTo(owner_table_section);
                }
            }
        });
    }
    
    // // Initial fetch and display data


    function updateDateRange(filters) {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',
                fields: ['creation'],
                filters: filters,
                order_by: 'creation asc'
            },
            callback: function(response) {
                var data = response.message;
                if (data.length > 0) {
                    var oldestDate = moment(data[0].creation).format('DD-MM-YYYY hh:mm A');
                    var latestDate = moment(data[data.length - 1].creation).format('DD-MM-YYYY hh:mm A');
                    date_range_section.empty();
                    $('<p>').html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>').appendTo(date_range_section);
                } else {
                    date_range_section.empty();
                    $('<p>').text('Date Range: No Data Available').appendTo(date_range_section);
                }
            }
        });
    }

    // Initial fetch and display data
    updateOwnerTable();
    fetchData(currentPage, itemsPerPage);

    filterRow.find('input').on('input', function() {
        fetchData(currentPage, itemsPerPage);
    });

    queryTypeDropdown.on('change', function() {
        fetchData(currentPage, itemsPerPage);
    });

    prevButton.on('click', function() {
        if (currentPage > 1) {
            currentPage--;
            fetchData(currentPage, itemsPerPage);
        }
    });

    nextButton.on('click', function() {
        currentPage++;
        fetchData(currentPage, itemsPerPage);
    });

    // Footer section
    var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
    footer_section.css({
        'margin-top': '25px',
        'border-top': '1px solid #ccc',
        'padding-top': '10px',
        'text-align': 'left'
    });

    $('<hr>').appendTo(footer_section);
    $('<p>').html('<strong>Disclaimer:</strong>This Halal Evaluation Report is issued based on the information and documentation provided at the time of evaluation. It is valid only for the specified batch/lot and for the specific materials/products mentioned. Any misuse, alteration, or use of this report beyond its intended purpose is strictly prohibited. SANHA Halal Pakistan reserves the right to revoke this evaluation in case of any non-compliance or deviation from the Halal standards.').appendTo(footer_section);
    $('<hr>').appendTo(footer_section);

    // Add company address
    $('<p>').html('<strong>Sanha Halal Associates Pakistan PVT. LTD.</strong> Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama D.H.A. phase 5  <strong> Email: </strong>evaluation@sanha.org.pk - <strong>Ph: +92 21 35295263</strong>').appendTo(footer_section);
};

