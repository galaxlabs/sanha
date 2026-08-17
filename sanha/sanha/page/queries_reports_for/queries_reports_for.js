frappe.pages['queries-reports-for'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Queries Reports',
		single_column: true
	});
	var action_section = $('<div>').addClass('action-section').appendTo(page.body);

    // Print button
    var printButton = $('<button>').text('Print').addClass('btn btn-primary').appendTo(action_section);
    printButton.on('click', function() {
        // Update print date/time before printing
        $('.print-datetime').html('<strong>Print Date/Time:</strong> ' + moment().format('DD-MM-YYYY hh:mm A'));
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

    // Print Selected button
    var printSelectedButton = $('<button>').text('Print Selected').addClass('btn btn-secondary ml-2').appendTo(action_section);
    printSelectedButton.on('click', function() {
        openPrintSelectedWindow();
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
    'margin-top': '30px', 
    'margin-bottom': '20px', // Add margin below the header section
    'border-bottom': '1px solid #ccc', // Add horizontal line at the bottom of the header
    'display': 'table',
    'width': '100%'
});

// Logo container
var logo_container = $('<div>').addClass('logo-container').appendTo(header_section);
logo_container.css({
    'display': 'table-cell',
    'text-align': 'right',
    'width': '55%',
    'margin-top': '20px'
});
var logo = $('<img>').attr('src', '/files/sanha-logo.png').addClass('img').appendTo(logo_container);
// Resize the logo to a standard size
logo.css({
    'width': '150px',
    'height': 'auto'
});

// Slogan container
var slogan_container = $('<div>').addClass('slogan-container').appendTo(header_section);
slogan_container.css({
    'display': 'table-cell',
    'text-align': 'right',
    'vertical-align': 'middle',
    'width': '45%'
});
$('<span>').text('Eat Halal, Be Healthy.').appendTo(slogan_container);

var reference_section = $('<div>').addClass('reference-section').appendTo(page.body);
reference_section.css({
    'margin-bottom': '20px',
    'text-align': 'center',
    'font-size': '14px',
    'font-weight': 'bold'
});
$('<span>').text('SANHA/PR-09/FM-01').appendTo(reference_section);
$('<span>').addClass('print-datetime').css({
    'display': 'block',
    'margin-top': '5px',
    'font-size': '12px',
    'font-weight': 'normal'
}).html('<strong>Print Date/Time:</strong> ' + moment().format('DD-MM-YYYY hh:mm A')).appendTo(reference_section);

// var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
// filterSection.css({
//     'margin-bottom': '35px', // Add margin below the filter section
//     'display': 'flex',
//     'justify-content': 'space-between', // Align items with space between
//     'align-items': 'center' // Align items at the center vertically
// });
// var clientNameDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
// $('<option>').text('Select Client').appendTo(clientNameDropdown);
// clientNameDropdown.css({
//     'margin-right': '10px' // Adjust as needed
// });
// // Query type selection dropdown
// var queryTypeDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
// $('<option>').text('Select Query Type').appendTo(queryTypeDropdown);

// var owner_table_section_container = $('<div>').appendTo(page.body);

// var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(owner_table_section_container);
// owner_table_section.css({
//     'margin-bottom': '20px',
//     'text-align': 'center'
// });

// // Date range section
// var date_range_section_container = $('<div>').appendTo(page.body);
// $('<hr>').appendTo(date_range_section_container);
// var date_range_section = $('<div>').addClass('date-range-section').appendTo(date_range_section_container);
// date_range_section.css({
//     'margin-bottom': '20px',
//     'text-align': 'center'
// });
// // Initialize data section and table
// // Define the table section

// var data_section = $('<div>').addClass('data-section').appendTo(page.body);
// data_section.css({
//     'margin-bottom': '20px',
//     'display': 'flex',
//     'align-items': 'center',
//     'flex-wrap': 'wrap'
// });

// var table = $('<table>').addClass('table').appendTo(data_section);
// var thead = $('<thead>').appendTo(table);
// var tbody = $('<tbody>').appendTo(table);
// var tfoot = $('<tfoot>').appendTo(table);
// var tableHeaders = ['S No','Raw Material', 'Supplier', 'Manufacturer', 'Query Types', 'Status'];

// var headerRow = $('<tr>').appendTo(thead);
// tableHeaders.forEach(function(label) {
//     $('<th>').text(label).appendTo(headerRow);
// });

// // Add input fields for filtering below the headers
// var filterRow = $('<tr>').addClass('filter-row').appendTo(thead);
//     tableHeaders.forEach(function(label) {
//         $('<td>').append($('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label)).appendTo(filterRow);
//     });
// // Add pagination controls
// var pagination_section = $('<div>').addClass('pagination-section').appendTo(page.body);
// pagination_section.css({
//     'display': 'flex',
//     'justify-content': 'center',
//     'margin-top': '20px'
// });

// var prevButton = $('<button>').text('Previous').addClass('btn btn-secondary').appendTo(pagination_section);
// var nextButton = $('<button>').text('Next').addClass('btn btn-secondary').appendTo(pagination_section);

// prevButton.css({
//     'order': '1', // Display the "Previous" button first
//     'margin-right': 'auto' // Push the "Previous" button to the left
// });

// nextButton.css({
//     'order': '2' // Display the "Next" button second
// });

// var currentPage = 1;
// var itemsPerPage = 200;

// function fetchAllData(doctype, fields, filters, callback) {
//     var start = 0;
//     var limit = 500; // Adjust limit as necessary for your environment
//     var allData = [];

//     function fetchData() {
//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: doctype,
//                 fields: fields,
//                 filters: filters,
//                 limit_start: start,
//                 limit_page_length: limit,
//                 order_by: 'raw_material asc'
//             },
//             callback: function(response) {
//                 var data = response.message;
//                 if (data.length > 0) {
//                     allData = allData.concat(data);
//                     start += limit;
//                     fetchData();
//                 } else {
//                     callback(allData);
//                 }
//             }
//         });
//     }

//     fetchData();
// }

// // Populate client dropdown
// fetchAllData('Query', ['client_name'], [], function(clients) {
//     var uniqueClients = new Set();
//     clients.forEach(function(client) {
//         if (!uniqueClients.has(client.client_name)) {
//             uniqueClients.add(client.client_name);
//             $('<option>').text(client.client_name).appendTo(clientNameDropdown);
//         }
//     });
// });

// // Populate query type dropdown
// fetchAllData('Query', ['query_types'], [], function(queryTypes) {
//     var uniqueQueryTypes = new Set();
//     queryTypes.forEach(function(query) {
//         if (query.query_types) {
//             query.query_types.split(',').forEach(function(type) {
//                 type = type.trim();
//                 if (type) uniqueQueryTypes.add(type);
//             });
//         }
//     });
//     uniqueQueryTypes.forEach(function(type) {
//         $('<option>').text(type).appendTo(queryTypeDropdown);
//     });
// });

// // Fetch and display data for the selected client and query type
// function fetchData(client, queryType, page, limit) {
//     var filters = { 
//         workflow_state: ['in', ['Submitted','Approved', 'Halal', 'Haram', 'Rejected', 'Hold', 'Doubtful']],
//         workflow_state: ['not in', ['Draft']],
//     };
//     if (client && client !== 'Select Client') {
//         filters.client_name = client;
//     }
//     if (queryType && queryType !== 'Select Query Type') {
//         filters.query_types = ['like', '%' + queryType + '%'];
//     }

//     var additionalFilters = {};
//     filterRow.find('input').each(function(index) {
//         var value = $(this).val();
//         if (value) {
//             // Map label to actual field name
//             var fieldMap = {
//                 'Raw Material': 'raw_material',
//                 'Supplier': 'supplier',
//                 'Manufacturer': 'manufacturer',
//                 'Query Types': 'query_types',
//                 'Status': 'workflow_state' // Map Status to workflow_state
//             };
//             var field = fieldMap[tableHeaders[index]];
//             if (field) {
//                 additionalFilters[field] = ['like', '%' + value + '%'];
//             }
//         }
//     });

//     Object.assign(filters, additionalFilters);

//     frappe.call({
//         method: 'frappe.client.get_list',
//         args: {
//             doctype: 'Query',
//             fields: ['raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state', 'creation'],
//             filters: filters,
//             limit_start: (page - 1) * limit,
//             limit_page_length: limit,
//             order_by: 'raw_material asc'
//         },
//         callback: function(response) {
//             var data = response.message;
//             tbody.empty(); // Clear existing table data
//             data.forEach(function(row) {
//                 var tableRow = $('<tr>').appendTo(tbody);
//                 tableHeaders.forEach(function(key) {
//                     var field = key.toLowerCase().replace(' ', '_');
//                     if (field === 'status') field = 'workflow_state'; // Use actual field name for Status
//                     if (field === 'creation') {
//                         // Format the creation date using moment.js
//                         var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
//                         $('<td>').text(formattedDate).appendTo(tableRow);
//                     } else {
//                         $('<td>').text(row[field]).appendTo(tableRow);
//                     }
//                 });
//             });
//             updateDateRange(filters);
//         }
//     });
// }

// // Update owner table based on selected client
// function updateOwnerTable(selectedClient) {
//     if (selectedClient !== 'Select Client') {
//         owner_table_section.empty();

//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 filters: {
//                     client_name: selectedClient
//                 },
//                 fields: ['client_code']
//             },
//             callback: function(response) {
//                 var clientData = response.message[0];
//                 if (clientData) {
//                     var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
//                     var tbody = $('<tbody>').appendTo(ownerTable);
//                     var firstRow = $('<tr>').appendTo(tbody);
//                     var firstRowData = $('<td>').addClass('text-center').appendTo(firstRow);
//                     $('<h2>').text(selectedClient + ' (Code: ' + clientData.client_code + ')').appendTo(firstRowData);
//                 }
//             }
//         });
//     } else {
//         owner_table_section.empty();
//     }
// }

// // Update date range based on filtered data
// function updateDateRange(filters) {
//     frappe.call({
//         method: 'frappe.client.get_list',
//         args: {
//             doctype: 'Query',
//             fields: ['creation'],
//             filters: filters,
//             order_by: 'creation asc'
//         },
//         callback: function(response) {
//             var data = response.message;
//             if (data.length > 0) {
//                 var oldestDate = moment(data[0].creation).format('DD-MM-YYYY hh:mm A');
//                 var latestDate = moment(data[data.length - 1].creation).format('DD-MM-YYYY hh:mm A');
//                 date_range_section.empty();
//                 $('<p>').html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>').appendTo(date_range_section);
//             } else {
//                 date_range_section.empty();
//                 $('<p>').text('Date Range: No Data Available').appendTo(date_range_section);
//             }
//         }
//     });
// }

// clientNameDropdown.on('change', function() {
//     selectedClient = clientNameDropdown.val();
//     updateOwnerTable(selectedClient);
//     currentPage = 1;
//     fetchData(selectedClient, queryTypeDropdown.val(), currentPage, itemsPerPage);
// });

// queryTypeDropdown.on('change', function() {
//     currentPage = 1;
//     fetchData(clientNameDropdown.val(), $(this).val(), currentPage, itemsPerPage);
// });

// filterRow.find('input').on('input', function() {
//     fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// });

// prevButton.on('click', function() {
//     if (currentPage > 1) {
//         currentPage--;
//         fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
//     }
// });

// nextButton.on('click', function() {
//     currentPage++;
//     fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// });

// fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
filterSection.css({
    'margin-bottom': '35px',
    'display': 'flex',
    'justify-content': 'space-between',
    'align-items': 'center'
});

var clientNameDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
$('<option>').text('Select Client').appendTo(clientNameDropdown);
clientNameDropdown.css({
    'margin-right': '10px'
});

var queryTypeDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
$('<option>').text('Select Query Type').appendTo(queryTypeDropdown);

var owner_table_section_container = $('<div>').appendTo(page.body);
var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(owner_table_section_container);
owner_table_section.css({
    'margin-bottom': '20px',
    'text-align': 'center'
});

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
var tfoot = $('<tfoot>').appendTo(table);
var tableHeaders = ['S No', 'Raw Material', 'Supplier', 'Manufacturer', 'Query Types', 'Status'];

var headerRow = $('<tr>').appendTo(thead);
var selectAllCheckbox = $('<input>').attr('type', 'checkbox').attr('id', 'selectAll').appendTo($('<th>').appendTo(headerRow));
tableHeaders.forEach(function(label) {
    $('<th>').text(label).appendTo(headerRow);
});

var filterRow = $('<tr>').addClass('filter-row').appendTo(thead);
$('<td>').appendTo(filterRow);
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
    'order': '1',
    'margin-right': 'auto'
});

nextButton.css({
    'order': '2'
});

var currentPage = 1;
var itemsPerPage = 200;

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

fetchAllData('Query', ['client_name'], [], function(clients) {
    var uniqueClients = new Set();
    clients.forEach(function(client) {
        if (!uniqueClients.has(client.client_name)) {
            uniqueClients.add(client.client_name);
            $('<option>').text(client.client_name).appendTo(clientNameDropdown);
        }
    });
});

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

function fetchData(client, queryType, page, limit) {
    var filters = { 
        workflow_state: ['in', ['Submitted','Approved', 'Halal', 'Haram', 'Rejected', 'Hold', 'Doubtful']],
        workflow_state: ['not in', ['Draft']],
    };
    if (client && client !== 'Select Client') {
        filters.client_name = client;
    }
    if (queryType && queryType !== 'Select Query Type') {
        filters.query_types = ['like', '%' + queryType + '%'];
    }

    var additionalFilters = {};
    filterRow.find('input').each(function(index) {
        var value = $(this).val();
        if (value) {
            var fieldMap = {
                'Raw Material': 'raw_material',
                'Supplier': 'supplier',
                'Manufacturer': 'manufacturer',
                'Query Types': 'query_types',
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
            fields: ['raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state', 'creation'],
            filters: filters,
            limit_start: (page - 1) * limit,
            limit_page_length: limit,
            order_by: 'raw_material asc'
        },
        callback: function(response) {
            var data = response.message;
            tbody.empty();
            data.forEach(function(row, index) {
                var tableRow = $('<tr>').appendTo(tbody);
                tableRow.attr('data-creation', row.creation || '');
                $('<td>').append($('<input>').attr('type', 'checkbox').addClass('row-checkbox').attr('data-id', row.name || '')).appendTo(tableRow);
                $('<td>').text((page - 1) * limit + index + 1).appendTo(tableRow); // Serial number
                tableHeaders.forEach(function(key) {
                    var field = key.toLowerCase().replace(' ', '_');
                    if (field === 's_no') return;
                    if (field === 'status') field = 'workflow_state';
                    if (field === 'creation') {
                        var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
                        $('<td>').text(formattedDate).appendTo(tableRow);
                    } else {
                        $('<td>').text(row[field] || '').appendTo(tableRow);
                    }
                });
            });
            updateDateRange(filters);
        }
    });
}

function updateOwnerTable(selectedClient) {
    if (selectedClient !== 'Select Client') {
        owner_table_section.empty();
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',
                filters: { client_name: selectedClient },
                fields: ['client_code']
            },
            callback: function(response) {
                var clientData = response.message[0];
                if (clientData) {
                    var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
                    var tbody = $('<tbody>').appendTo(ownerTable);
                    var firstRow = $('<tr>').appendTo(tbody);
                    $('<h2>').text(selectedClient + ' (Code: ' + clientData.client_code + ')').appendTo(firstRow);
                }
            }
        });
    } else {
        owner_table_section.empty();
    }
}

function updateDateRange(filters) {
    var start = 0;
    var limit = 500;
    var allData = [];
    var oldestDate = null;
    var latestModified = null;

    function fetchDateRange() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',
                fields: ['creation', 'modified'],
                filters: filters,
                order_by: 'creation asc',
                limit_start: start,
                limit_page_length: limit
            },
            callback: function(response) {
                var data = response.message || [];
                if (data.length > 0) {
                    data.forEach(function(row) {
                        if (!oldestDate || row.creation < oldestDate) {
                            oldestDate = row.creation;
                        }
                        if (!latestModified || row.modified > latestModified) {
                            latestModified = row.modified;
                        }
                    });
                    start += limit;
                    fetchDateRange();
                } else {
                    if (oldestDate && latestModified) {
                        var oldestDateStr = moment(oldestDate).format('DD-MM-YYYY hh:mm A');
                        var latestDateStr = moment(latestModified).format('DD-MM-YYYY hh:mm A');
                        date_range_section.empty();
                        $('<p>').html('Date Range: <strong>From: ' + oldestDateStr + '</strong> To: <strong>' + latestDateStr + '</strong>').appendTo(date_range_section);
                    } else {
                        date_range_section.empty();
                        $('<p>').text('Date Range: No Data Available').appendTo(date_range_section);
                    }
                }
            }
        });
    }

    fetchDateRange();
}

clientNameDropdown.on('change', function() {
    selectedClient = clientNameDropdown.val();
    updateOwnerTable(selectedClient);
    currentPage = 1;
    fetchData(selectedClient, queryTypeDropdown.val(), currentPage, itemsPerPage);
});

queryTypeDropdown.on('change', function() {
    currentPage = 1;
    fetchData(clientNameDropdown.val(), $(this).val(), currentPage, itemsPerPage);
});

filterRow.find('input').on('input', function() {
    fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
});

prevButton.on('click', function() {
    if (currentPage > 1) {
        currentPage--;
        fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
    }
});

nextButton.on('click', function() {
    currentPage++;
    fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
});

fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);

// Select all checkbox handler
$('#selectAll').on('change', function() {
    $('.row-checkbox').prop('checked', this.checked);
});

// Print Selected: open a fresh HTML window with selected rows (or all for the selected client if none checked)
function openPrintSelectedWindow() {
    var selected = $('.row-checkbox:checked').closest('tr');
    var client = clientNameDropdown.val();
    var queryType = queryTypeDropdown.val();

    var printRows = function(data) {
        if (!data || !data.length) {
            frappe.msgprint('No records found to print.');
            return;
        }
        var tempTable = $('<tbody>');
        var sortedDates = [];
        data.forEach(function(row, i) {
            var tr = $('<tr>');
            tr.attr('data-creation', row.creation || '');
            $('<td>').text(i + 1).appendTo(tr);
            $('<td>').text(row.raw_material || '').appendTo(tr);
            $('<td>').text(row.supplier || '').appendTo(tr);
            $('<td>').text(row.manufacturer || '').appendTo(tr);
            $('<td>').text(row.query_types || '').appendTo(tr);
            $('<td>').text(row.workflow_state || '').appendTo(tr);
            tempTable.append(tr);
            if (row.creation) sortedDates.push(row.creation);
        });
        var win = buildPrintWindow(tempTable.find('tr'), client, data[0].client_code || '', sortedDates);
        win.print();
    };

    if (selected.length > 0) {
        // PART A: print exactly the checked rows (date range from those rows)
        var sortedDates = selected.map(function() { return $(this).data('creation'); }).get().filter(Boolean).sort();
        var win = buildPrintWindow(selected, client, '', sortedDates);
        win.print();
    } else {
        // PART B: nothing checked -> print all data for the selected client
        var filters = {
            workflow_state: ['in', ['Submitted','Approved', 'Halal', 'Haram', 'Rejected', 'Hold', 'Doubtful']],
            workflow_state: ['not in', ['Draft']]
        };
        if (client && client !== 'Select Client') filters.client_name = client;
        if (queryType && queryType !== 'Select Query Type') filters.query_types = ['like', '%' + queryType + '%'];
        var additionalFilters = {};
        filterRow.find('input').each(function(index) {
            var value = $(this).val();
            if (value) {
                var fieldMap = {
                    'Raw Material': 'raw_material',
                    'Supplier': 'supplier',
                    'Manufacturer': 'manufacturer',
                    'Query Types': 'query_types',
                    'Status': 'workflow_state'
                };
                var field = fieldMap[tableHeaders[index - 1]];
                if (field) additionalFilters[field] = ['like', '%' + value + '%'];
            }
        });
        Object.assign(filters, additionalFilters);

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',
                fields: ['name', 'client_name', 'client_code', 'raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state', 'creation'],
                filters: filters,
                order_by: 'raw_material asc',
                limit_page_length: 0
            },
            callback: function(response) {
                printRows(response.message || []);
            }
        });
    }
}

// Build a fresh print window with logo, SANHA/PR-09/FM-01, print date/time, client+date range, table, disclaimer
function buildPrintWindow(rows, client, clientCode, sortedDates) {
    var win = window.open('', '_blank');
    var printDateTime = moment().format('DD-MM-YYYY hh:mm A');
    var clientDetails = client && client !== 'Select Client'
        ? '<b>Client:</b> <b>' + client + '</b> | <b>Code:</b> <b>' + (clientCode || 'N/A') + '</b>'
        : '<b>Client:</b> <b>All</b> | <b>Code:</b> <b>N/A</b>';
    var dateRange = '<b>Date Range:</b> <b>N/A</b>';
    if (sortedDates && sortedDates.length) {
        sortedDates.sort();
        dateRange = '<b>Date Range:</b> <b>' + moment(sortedDates[0]).format('DD-MM-YYYY hh:mm A') + '</b> to <b>' + moment(sortedDates[sortedDates.length - 1]).format('DD-MM-YYYY hh:mm A') + '</b>';
    }

    win.document.write('<html><head><title>Queries Reports</title><style>');
    win.document.write("@import url('https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;500;700&display=swap');");
    win.document.write("body { font-family: 'Ubuntu', Arial, sans-serif; }");
    win.document.write('.header-section { padding: 20px; margin-top: 30px; margin-bottom: 20px; border-bottom: 2px solid #14532d; display: table; width: 100%; background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); }');
    win.document.write('.logo-container { display: table-cell; text-align: right; width: 55%; margin-top: 20px; }');
    win.document.write('.slogan-container { display: table-cell; text-align: right; vertical-align: middle; width: 45%; }');
    win.document.write('.slogan { font-style: italic; color: #14532d; font-size: 18px; font-weight: 600; }');
    win.document.write('.reference-section { margin-bottom: 20px; text-align: center; font-size: 14px; font-weight: bold; }');
    win.document.write('.print-datetime { display: block; margin-top: 5px; font-size: 12px; font-weight: normal; }');
    win.document.write('table { width: 100%; border-collapse: collapse; margin-top: 20px; table-layout: auto; }');
    win.document.write('th, td { border: 1px solid #e2e8f0; padding: 7px; text-align: left; word-wrap: break-word; word-break: break-word; white-space: normal; }');
    win.document.write('th { background: #14532d; color: #fff; font-size: 13px; }');
    win.document.write('tbody tr:nth-child(even) { background: #f8fafc; }');
    win.document.write('td:nth-child(2) { min-width: 150px; max-width: 250px; }');
    win.document.write('td:nth-child(3), td:nth-child(4) { min-width: 110px; max-width: 190px; }');
    win.document.write('td:nth-child(5) { min-width: 90px; max-width: 150px; }');
    win.document.write('td:nth-child(6) { min-width: 70px; max-width: 110px; }');
    win.document.write('.footer-section { margin-top: 30px; text-align: center; padding: 20px; border-top: 2px solid #14532d; }');
    win.document.write('.footer-section .disclaimer { text-align: left; font-size: 12px; line-height: 1.6; color: #334155; margin: 0 0 16px; }');
    win.document.write('.org-address { margin: 16px 0; }');
    win.document.write('.org-address .org-name { font-weight: 700; font-size: 14px; color: #14532d; margin: 0 0 4px; }');
    win.document.write('.org-address p { margin: 3px 0; font-size: 12px; color: #475569; }');
    win.document.write('</style></head><body>');

    win.document.write('<div class="header-section">');
    win.document.write('<div class="logo-container"><img src="/files/sanha-logo.png" style="width: 150px; height: auto;"></div>');
    win.document.write('<div class="slogan-container"><span class="slogan">Eat Halal, Be Healthy.</span></div>');
    win.document.write('</div>');

    win.document.write('<div class="reference-section">');
    win.document.write('<span>SANHA/PR-09/FM-01</span>');
    win.document.write('<span class="print-datetime"><strong>Print Date/Time:</strong> ' + printDateTime + '</span>');
    win.document.write('</div>');

    win.document.write('<div style="text-align: center; margin-top: 10px; margin-bottom: 20px;">');
    win.document.write('<p style="margin: 5px 0;">' + clientDetails + '</p>');
    win.document.write('<p style="margin: 5px 0;">' + dateRange + '</p>');
    win.document.write('</div>');

    win.document.write('<table><thead><tr><th>#</th><th>Raw Material</th><th>Supplier</th><th>Manufacturer</th><th>Query Type</th><th>Status</th></tr></thead><tbody>');
    rows.each(function() {
        var cells = $(this).find('td').slice(1); // skip checkbox column
        win.document.write('<tr>');
        cells.each(function() {
            win.document.write('<td>' + $(this).text() + '</td>');
        });
        win.document.write('</tr>');
    });
    win.document.write('</tbody></table>');

    win.document.write('<div class="footer-section"><hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 14px 0;">');
    win.document.write('<p class="disclaimer"><strong>Disclaimer:</strong> This Halal Evaluation Report is issued based on the information and documentation provided at the time of evaluation. It is valid only for the specified batch/lot and for the specific materials/products mentioned. Any misuse, alteration, or use of this report beyond its intended purpose is strictly prohibited. SANHA Halal Pakistan reserves the right to revoke this evaluation in case of any non-compliance or deviation from the Halal standards.</p>');
    win.document.write('<hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 14px 0;">');
    win.document.write('<div class="org-address">');
    win.document.write('<p class="org-name">Sanha Halal Associates Pakistan (Pvt.) Ltd.</p>');
    win.document.write('<p>Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama Commercial Lane 5, D.H.A. Phase 5, Karachi, Pakistan</p>');
    win.document.write('<p>Tel: +92 21 35295263 &nbsp;|&nbsp; Email: evaluation@sanha.org.pk</p>');
    win.document.write('</div>');
    win.document.write('<hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 14px 0;"><span style="font-size: 12px; color: #94a3b8;">&copy; 2023 SANHA. All rights reserved.</span>');
    win.document.write('</div>');

    win.document.write('</body></html>');
    win.document.close();
    return win;
}

var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
footer_section.css({
    'margin-top': '25px',
    'border-top': '1px solid #ccc',
    'padding-top': '10px',
    'text-align': 'center'
});

$('<hr>').appendTo(footer_section);

$('<p>').html('<strong>Disclaimer:</strong> This Halal Evaluation Report is issued based on the information and documentation provided at the time of evaluation. It is valid only for the specified batch/lot and for the specific materials/products mentioned. Any misuse, alteration, or use of this report beyond its intended purpose is strictly prohibited. SANHA Halal Pakistan reserves the right to revoke this evaluation in case of any non-compliance or deviation from the Halal standards.').appendTo(footer_section);

$('<hr>').appendTo(footer_section);

// Add company address
$('<p>').html('<strong>Sanha Halal Associates Pakistan (Pvt.) Ltd.</strong><br>Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama Commercial Lane 5, D.H.A. Phase 5, Karachi, Pakistan<br>Tel: +92 21 35295263 | Email: evaluation@sanha.org.pk').appendTo(footer_section);

$('<hr>').appendTo(footer_section);
};

