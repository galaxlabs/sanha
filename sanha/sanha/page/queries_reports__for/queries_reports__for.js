frappe.pages['queries-reports--for'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Queries Reports',
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

    var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
    filterSection.css({
        'margin-bottom': '35px',
        'display': 'flex',
        'justify-content': 'space-between',
        'align-items': 'center'
    });
    
    var clientNameDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
    $('<option>').text('Select Client').appendTo(clientNameDropdown);
    clientNameDropdown.css({'margin-right': '10px'});
    
    var queryTypeDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
    $('<option>').text('Select Query Type').appendTo(queryTypeDropdown);

// ###with owner Table #########

var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
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
// Initialize data section and table
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
var tableHeaders = ['Raw Material', 'Supplier', 'Manufacturer', 'Query Types', 'Status'];

var headerRow = $('<tr>').appendTo(thead);
tableHeaders.forEach(function(label) {
    $('<th>').text(label).appendTo(headerRow);
});

// Add input fields for filtering below the headers
var filterRow = $('<tr>').appendTo(thead);
tableHeaders.forEach(function(label) {
    $('<td>').append($('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label)).appendTo(filterRow);
});

// Add pagination controls
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
    var limit = 500; // Adjust limit as necessary for your environment
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

// Populate client dropdown
fetchAllData('Query', ['client_name'], [], function(clients) {
    var uniqueClients = new Set();
    clients.forEach(function(client) {
        if (!uniqueClients.has(client.client_name)) {
            uniqueClients.add(client.client_name);
            $('<option>').text(client.client_name).appendTo(clientNameDropdown);
        }
    });
});

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

// Fetch and display data for the selected client and query type
function fetchData(client, queryType, page, limit) {
    var filters = { workflow_state: ['!=', 'Draft'] };
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
            // Map label to actual field name
            var fieldMap = {
                'Raw Material': 'raw_material',
                'Supplier': 'supplier',
                'Manufacturer': 'manufacturer',
                'Query Types': 'query_types',
                'Status': 'workflow_state' // Map Status to workflow_state
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
            tbody.empty(); // Clear existing table data
            data.forEach(function(row) {
                var tableRow = $('<tr>').appendTo(tbody);
                tableHeaders.forEach(function(key) {
                    var field = key.toLowerCase().replace(' ', '_');
                    if (field === 'status') field = 'workflow_state'; // Use actual field name for Status
                    if (field === 'creation') {
                        // Format the creation date using moment.js
                        var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
                        $('<td>').text(formattedDate).appendTo(tableRow);
                    } else {
                        $('<td>').text(row[field]).appendTo(tableRow);
                    }
                });
            });
            updateDateRange(filters);
        }
    });
}

// Update owner table based on selected client
function updateOwnerTable(selectedClient) {
    if (selectedClient !== 'Select Client') {
        owner_table_section.empty();

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',
                filters: {
                    client_name: selectedClient
                },
                fields: ['client_code']
            },
            callback: function(response) {
                var clientData = response.message[0];
                if (clientData) {
                    var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
                    var tbody = $('<tbody>').appendTo(ownerTable);
                    var firstRow = $('<tr>').appendTo(tbody);
                    var firstRowData = $('<td>').addClass('text-center').appendTo(firstRow);
                    $('<h2>').text(selectedClient + ' (Code: ' + clientData.client_code + ')').appendTo(firstRowData);
                }
            }
        });
    } else {
        owner_table_section.empty();
    }
}

// Update date range based on filtered data
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
// ############################################
		// Footer section
		var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
		footer_section.css({
			'margin-top': '25px',
			'border-top': '1px solid #ccc',
			'padding-top': '10px',
			'text-align': 'center'
		});
	
		$('<hr>').appendTo(footer_section);
	
		$('<p>').html('<strong>Sanha Halal Associates Pakistan PVT. LTD.</strong> Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama D.H.A. phase 5<br>Email: evaluation@sanha.org.pk - Ph: +92 21 35295263').appendTo(footer_section);
	
		$('<hr>').appendTo(footer_section);
// frappe.pages['queries-reports--for'].on_page_load = function(wrapper) {
// 	var page = frappe.ui.make_app_page({
// 		parent: wrapper,
// 		title: 'Queries Reports',
// 		single_column: true
// 	});
// 	var action_section = $('<div>').addClass('action-section').appendTo(page.body);

//     // Print button
//     var printButton = $('<button>').text('Print').addClass('btn btn-primary').appendTo(action_section);
//     printButton.on('click', function() {
//         // Hide page title before printing
//         page.$title_area.hide();
//         // Hide filter row before printing
//         $('.filter-row').hide();
//         // Hide filter section before printing
//         $('.filter-section').hide();
//         // Print the page
//         $('.pagination-section').hide();
//         $('.action-section').hide();
        

//         window.print();
//         // Show page title after printing
//         page.$title_area.show();
//         // Show filter row after printing
//         $('.filter-row').show();
//         // Show filter section after printing
//         $('.filter-section').show();
//         $('.pagination-section').show();
//         $('.action-section').show();

//     });
//     // Align action buttons to the right
//     action_section.css({
//         'display': 'flex',
//         'justify-content': 'flex-end', // Align items to the right
//         'margin-bottom': '10px' // Add margin below action section
//     });

// // Create filter section for query types dropdown
// // var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
// // filterSection.css({
// //     'margin-bottom': '35px', // Add margin below the filter section
// //     'display': 'flex',
// //     'justify-content': 'space-between', // Align items with space between
// //     'align-items': 'center' // Align items at the center vertically
// // });
// // var clientNameDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
// // $('<option>').text('Select Client').appendTo(clientNameDropdown);
// // // Client selection dropdown
// // // var clientNameDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
// // // $('<option>').text('Select Client').appendTo(clientNameDropdown);

// // // Query type selection dropdown
// // var queryTypeDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
// // $('<option>').text('Select Query Type').appendTo(queryTypeDropdown);
// // Header section


//     var header_section = $('<div>').addClass('header-section').appendTo(page.body);
// header_section.css({
//     'padding': '20px',
//     'margin-top': '30px', 
//     'margin-bottom': '20px', // Add margin below the header section
//     'border-bottom': '1px solid #ccc', // Add horizontal line at the bottom of the header
//     'display': 'table',
//     'width': '100%'
// });

// // Logo container
// var logo_container = $('<div>').addClass('logo-container').appendTo(header_section);
// logo_container.css({
//     'display': 'table-cell',
//     'text-align': 'right',
//     'width': '55%',
//     'margin-top': '20px'
// });
// var logo = $('<img>').attr('src', '/files/sanha-logo.png').addClass('img').appendTo(logo_container);
// // Resize the logo to a standard size
// logo.css({
//     'width': '150px',
//     'height': 'auto'
// });

// // Slogan container
// var slogan_container = $('<div>').addClass('slogan-container').appendTo(header_section);
// slogan_container.css({
//     'display': 'table-cell',
//     'text-align': 'right',
//     'vertical-align': 'middle',
//     'width': '45%'
// });
// $('<span>').text('Eat Halal, Be Healthy.').appendTo(slogan_container);

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
// // Client selection dropdown
// // var clientNameDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
// // $('<option>').text('Select Client').appendTo(clientNameDropdown);

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
// var tableHeaders = ['Raw Material', 'Supplier', 'Manufacturer', 'Query Types', 'Status'];

// var headerRow = $('<tr>').appendTo(thead);
// tableHeaders.forEach(function(label) {
//     $('<th>').text(label).appendTo(headerRow);
// });

// // Add input fields for filtering below the headers
// var filterRow = $('<tr>').appendTo(thead);
// tableHeaders.forEach(function(label) {
//     $('<td>').append($('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label)).appendTo(filterRow);
// });

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
// var itemsPerPage = 50;

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
//     var filters = { workflow_state: ['!=', 'Draft'] };
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

// // var owner_table_section_container = $('<div>').appendTo(page.body);

// // var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(owner_table_section_container);
// // owner_table_section.css({
// //     'margin-bottom': '20px',
// //     'text-align': 'center'
// // });

// // // Date range section
// // var date_range_section_container = $('<div>').appendTo(page.body);
// // $('<hr>').appendTo(date_range_section_container);
// // var date_range_section = $('<div>').addClass('date-range-section').appendTo(date_range_section_container);
// // date_range_section.css({
// //     'margin-bottom': '20px',
// //     'text-align': 'center'
// // });
// // // Initialize data section and table
// // var data_section = $('<div>').addClass('data-section').appendTo(page.body);
// // data_section.css({
// //     'margin-bottom': '20px',
// //     'display': 'flex',
// //     'align-items': 'center',
// //     'flex-wrap': 'wrap'
// // });

// // var table = $('<table>').addClass('table').appendTo(data_section);
// // var thead = $('<thead>').appendTo(table);
// // var tbody = $('<tbody>').appendTo(table);
// // var tableHeaders = ['Raw Material', 'Supplier', 'Manufacturer', 'Query Types', 'Status'];

// // var headerRow = $('<tr>').appendTo(thead);
// // tableHeaders.forEach(function(label) {
// //     $('<th>').text(label).appendTo(headerRow);
// // });

// // // Add input fields for filtering below the headers
// // var filterRow = $('<tr>').appendTo(thead);
// // tableHeaders.forEach(function(label) {
// //     $('<td>').append($('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label)).appendTo(filterRow);
// // });

// // // Add pagination controls
// // var pagination_section = $('<div>').addClass('pagination-section').appendTo(page.body);
// // pagination_section.css({
// //     'display': 'flex',
// //     'justify-content': 'center',
// //     'margin-top': '20px'
// // });

// // var prevButton = $('<button>').text('Previous').addClass('btn btn-secondary').appendTo(pagination_section);
// // var nextButton = $('<button>').text('Next').addClass('btn btn-secondary').appendTo(pagination_section);

// // var currentPage = 1;
// // var itemsPerPage = 10;

// // function fetchAllData(doctype, fields, filters, callback) {
// //     var start = 0;
// //     var limit = 500; // Adjust limit as necessary for your environment
// //     var allData = [];

// //     function fetchData() {
// //         frappe.call({
// //             method: 'frappe.client.get_list',
// //             args: {
// //                 doctype: doctype,
// //                 fields: fields,
// //                 filters: filters,
// //                 limit_start: start,
// //                 limit_page_length: limit,
// //                 order_by: 'raw_material asc'
// //             },
// //             callback: function(response) {
// //                 var data = response.message;
// //                 if (data.length > 0) {
// //                     allData = allData.concat(data);
// //                     start += limit;
// //                     fetchData();
// //                 } else {
// //                     callback(allData);
// //                 }
// //             }
// //         });
// //     }

// //     fetchData();
// // }

// // // Populate client dropdown
// // fetchAllData('Query', ['client_name'], [], function(clients) {
// //     var uniqueClients = new Set();
// //     clients.forEach(function(client) {
// //         if (!uniqueClients.has(client.client_name)) {
// //             uniqueClients.add(client.client_name);
// //             $('<option>').text(client.client_name).appendTo(clientNameDropdown);
// //         }
// //     });
// // });

// // // Populate query type dropdown
// // fetchAllData('Query', ['query_types'], [], function(queryTypes) {
// //     var uniqueQueryTypes = new Set();
// //     queryTypes.forEach(function(query) {
// //         if (query.query_types) {
// //             query.query_types.split(',').forEach(function(type) {
// //                 type = type.trim();
// //                 if (type) uniqueQueryTypes.add(type);
// //             });
// //         }
// //     });
// //     uniqueQueryTypes.forEach(function(type) {
// //         $('<option>').text(type).appendTo(queryTypeDropdown);
// //     });
// // });

// // // Fetch and display data for the selected client and query type
// // function fetchData(client, queryType, page, limit) {
// //     var filters = { workflow_state: ['!=', 'Draft'] };
// //     if (client && client !== 'Select Client') {
// //         filters.client_name = client;
// //     }
// //     if (queryType && queryType !== 'Select Query Type') {
// //         filters.query_types = ['like', '%' + queryType + '%'];
// //     }

// //     var additionalFilters = {};
// //     filterRow.find('input').each(function(index) {
// //         var value = $(this).val();
// //         if (value) {
// //             additionalFilters[tableHeaders[index].toLowerCase().replace(' ', '_')] = ['like', '%' + value + '%'];
// //         }
// //     });

// //     Object.assign(filters, additionalFilters);

// //     frappe.call({
// //         method: 'frappe.client.get_list',
// //         args: {
// //             doctype: 'Query',
// //             fields: ['raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state', 'creation'],
// //             filters: filters,
// //             limit_start: (page - 1) * limit,
// //             limit_page_length: limit,
// //             order_by: 'raw_material asc'
// //         },
// //         callback: function(response) {
// //             var data = response.message;
// //             tbody.empty(); // Clear existing table data
// //             data.forEach(function(row) {
// //                 var tableRow = $('<tr>').appendTo(tbody);
// //                 tableHeaders.forEach(function(key) {
// //                     var field = key.toLowerCase().replace(' ', '_');
// //                     if (field === 'creation') {
// //                         // Format the creation date using moment.js
// //                         var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
// //                         $('<td>').text(formattedDate).appendTo(tableRow);
// //                     } else {
// //                         $('<td>').text(row[field] || row['workflow_state']).appendTo(tableRow);
// //                     }
// //                 });
// //             });
// //             updateDateRange(filters);
// //         }
// //     });
// // }

// // // Update owner table based on selected client
// // function updateOwnerTable(selectedClient) {
// //     if (selectedClient !== 'Select Client') {
// //         owner_table_section.empty();

// //         frappe.call({
// //             method: 'frappe.client.get_list',
// //             args: {
// //                 doctype: 'Query',
// //                 filters: {
// //                     client_name: selectedClient
// //                 },
// //                 fields: ['client_code']
// //             },
// //             callback: function(response) {
// //                 var clientData = response.message[0];
// //                 if (clientData) {
// //                     var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
// //                     var tbody = $('<tbody>').appendTo(ownerTable);
// //                     var firstRow = $('<tr>').appendTo(tbody);
// //                     var firstRowData = $('<td>').addClass('text-center').appendTo(firstRow);
// //                     $('<h2>').text(selectedClient + ' (Code: ' + clientData.client_code + ')').appendTo(firstRowData);
// //                 }
// //             }
// //         });
// //     } else {
// //         owner_table_section.empty();
// //     }
// // }

// // // Update date range based on filtered data
// // function updateDateRange(filters) {
// //     frappe.call({
// //         method: 'frappe.client.get_list',
// //         args: {
// //             doctype: 'Query',
// //             fields: ['creation'],
// //             filters: filters,
// //             order_by: 'creation asc'
// //         },
// //         callback: function(response) {
// //             var data = response.message;
// //             if (data.length > 0) {
// //                 var oldestDate = moment(data[0].creation).format('DD-MM-YYYY hh:mm A');
// //                 var latestDate = moment(data[data.length - 1].creation).format('DD-MM-YYYY hh:mm A');
// //                 date_range_section.empty();
// //                 $('<p>').html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>').appendTo(date_range_section);
// //             } else {
// //                 date_range_section.empty();
// //                 $('<p>').text('Date Range: No Data Available').appendTo(date_range_section);
// //             }
// //         }
// //     });
// // }

// // clientNameDropdown.on('change', function() {
// //     selectedClient = clientNameDropdown.val();
// //     updateOwnerTable(selectedClient);
// //     currentPage = 1;
// //     fetchData(selectedClient, queryTypeDropdown.val(), currentPage, itemsPerPage);
// // });

// // queryTypeDropdown.on('change', function() {
// //     currentPage = 1;
// //     fetchData(clientNameDropdown.val(), $(this).val(), currentPage, itemsPerPage);
// // });

// // filterRow.find('input').on('input', function() {
// //     fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// // });

// // prevButton.on('click', function() {
// //     if (currentPage > 1) {
// //         currentPage--;
// //         fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// //     }
// // });

// // nextButton.on('click', function() {
// //     currentPage++;
// //     fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// // });

// // fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);

// // #################################################################################################################################

// // var owner_table_section_container = $('<div>').appendTo(page.body);

// // var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(owner_table_section_container);
// // owner_table_section.css({
// //     'margin-bottom': '20px',
// //     'text-align': 'center'
// // });

// // // Date range section
// // var date_range_section_container = $('<div>').appendTo(page.body);
// // $('<hr>').appendTo(date_range_section_container);
// // var date_range_section = $('<div>').addClass('date-range-section').appendTo(date_range_section_container);
// // date_range_section.css({
// //     'margin-bottom': '20px',
// //     'text-align': 'center'
// // });
// // // Initialize data section and table
// // var data_section = $('<div>').addClass('data-section').appendTo(page.body);
// // data_section.css({
// //     'margin-bottom': '20px',
// //     'display': 'flex',
// //     'align-items': 'center',
// //     'flex-wrap': 'wrap'
// // });

// // var table = $('<table>').addClass('table').appendTo(data_section);
// // var thead = $('<thead>').appendTo(table);
// // var tbody = $('<tbody>').appendTo(table);
// // var tableHeaders = ['Raw Material', 'Supplier', 'Manufacturer', 'Query Types', 'Status'];

// // var headerRow = $('<tr>').appendTo(thead);
// // tableHeaders.forEach(function(label) {
// //     $('<th>').text(label).appendTo(headerRow);
// // });

// // // Add input fields for filtering below the headers
// // var filterRow = $('<tr>').appendTo(thead);
// // tableHeaders.forEach(function(label) {
// //     $('<td>').append($('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label)).appendTo(filterRow);
// // });

// // // Add pagination controls
// // var pagination_section = $('<div>').addClass('pagination-section').appendTo(page.body);
// // pagination_section.css({
// //     'display': 'flex',
// //     'justify-content': 'center',
// //     'margin-top': '20px'
// // });

// // var prevButton = $('<button>').text('Previous').addClass('btn btn-secondary').appendTo(pagination_section);
// // var nextButton = $('<button>').text('Next').addClass('btn btn-secondary').appendTo(pagination_section);

// // var currentPage = 1;
// // var itemsPerPage = 10;

// // function fetchAllData(doctype, fields, filters, callback) {
// //     var start = 0;
// //     var limit = 500; // Adjust limit as necessary for your environment
// //     var allData = [];

// //     function fetchData() {
// //         frappe.call({
// //             method: 'frappe.client.get_list',
// //             args: {
// //                 doctype: doctype,
// //                 fields: fields,
// //                 filters: filters,
// //                 limit_start: start,
// //                 limit_page_length: limit,
// //                 order_by: 'raw_material asc'
// //             },
// //             callback: function(response) {
// //                 var data = response.message;
// //                 if (data.length > 0) {
// //                     allData = allData.concat(data);
// //                     start += limit;
// //                     fetchData();
// //                 } else {
// //                     callback(allData);
// //                 }
// //             }
// //         });
// //     }

// //     fetchData();
// // }

// // // Populate client dropdown
// // fetchAllData('Query', ['client_name'], [], function(clients) {
// //     var uniqueClients = new Set();
// //     clients.forEach(function(client) {
// //         if (!uniqueClients.has(client.client_name)) {
// //             uniqueClients.add(client.client_name);
// //             $('<option>').text(client.client_name).appendTo(clientNameDropdown);
// //         }
// //     });
// // });

// // // Populate query type dropdown
// // fetchAllData('Query', ['query_types'], [], function(queryTypes) {
// //     var uniqueQueryTypes = new Set();
// //     queryTypes.forEach(function(query) {
// //         if (query.query_types) {
// //             query.query_types.split(',').forEach(function(type) {
// //                 type = type.trim();
// //                 if (type) uniqueQueryTypes.add(type);
// //             });
// //         }
// //     });
// //     uniqueQueryTypes.forEach(function(type) {
// //         $('<option>').text(type).appendTo(queryTypeDropdown);
// //     });
// // });

// // // Fetch and display data for the selected client and query type
// // function fetchData(client, queryType, page, limit) {
// //     var filters = { workflow_state: ['!=', 'Draft'] };
// //     if (client && client !== 'Select Client') {
// //         filters.client_name = client;
// //     }
// //     if (queryType && queryType !== 'Select Query Type') {
// //         filters.query_types = ['like', '%' + queryType + '%'];
// //     }

// //     var additionalFilters = {};
// //     filterRow.find('input').each(function(index) {
// //         var value = $(this).val();
// //         if (value) {
// //             additionalFilters[tableHeaders[index].toLowerCase().replace(' ', '_')] = ['like', '%' + value + '%'];
// //         }
// //     });

// //     Object.assign(filters, additionalFilters);

// //     frappe.call({
// //         method: 'frappe.client.get_list',
// //         args: {
// //             doctype: 'Query',
// //             fields: ['raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state', 'creation'],
// //             filters: filters,
// //             limit_start: (page - 1) * limit,
// //             limit_page_length: limit,
// //             order_by: 'raw_material asc'
// //         },
// //         callback: function(response) {
// //             var data = response.message;
// //             tbody.empty(); // Clear existing table data
// //             data.forEach(function(row) {
// //                 var tableRow = $('<tr>').appendTo(tbody);
// //                 tableHeaders.forEach(function(key) {
// //                     var field = key.toLowerCase().replace(' ', '_');
// //                     if (field === 'creation') {
// //                         // Format the creation date using moment.js
// //                         var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
// //                         $('<td>').text(formattedDate).appendTo(tableRow);
// //                     } else {
// //                         $('<td>').text(row[field] || row['workflow_state']).appendTo(tableRow);
// //                     }
// //                 });
// //             });
// //             updateDateRange(filters);
// //         }
// //     });
// // }

// // // Update owner table based on selected client
// // function updateOwnerTable(selectedClient) {
// //     if (selectedClient !== 'Select Client') {
// //         owner_table_section.empty();

// //         frappe.call({
// //             method: 'frappe.client.get_list',
// //             args: {
// //                 doctype: 'Query',
// //                 filters: {
// //                     client_name: selectedClient
// //                 },
// //                 fields: ['client_code']
// //             },
// //             callback: function(response) {
// //                 var clientData = response.message[0];
// //                 if (clientData) {
// //                     var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
// //                     var tbody = $('<tbody>').appendTo(ownerTable);
// //                     var firstRow = $('<tr>').appendTo(tbody);
// //                     var firstRowData = $('<td>').addClass('text-center').appendTo(firstRow);
// //                     $('<h2>').text(selectedClient + ' (Code: ' + clientData.client_code + ')').appendTo(firstRowData);
// //                 }
// //             }
// //         });
// //     } else {
// //         owner_table_section.empty();
// //     }
// // }

// // // Update date range based on filtered data
// // function updateDateRange(filters) {
// //     frappe.call({
// //         method: 'frappe.client.get_list',
// //         args: {
// //             doctype: 'Query',
// //             fields: ['creation'],
// //             filters: filters,
// //             order_by: 'creation asc'
// //         },
// //         callback: function(response) {
// //             var data = response.message;
// //             if (data.length > 0) {
// //                 var oldestDate = moment(data[0].creation).format('DD-MM-YYYY hh:mm A');
// //                 var latestDate = moment(data[data.length - 1].creation).format('DD-MM-YYYY hh:mm A');
// //                 date_range_section.empty();
// //                 $('<p>').html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>').appendTo(date_range_section);
// //             } else {
// //                 date_range_section.empty();
// //                 $('<p>').text('Date Range: No Data Available').appendTo(date_range_section);
// //             }
// //         }
// //     });
// // }

// // clientNameDropdown.on('change', function() {
// //     selectedClient = clientNameDropdown.val();
// //     updateOwnerTable(selectedClient);
// //     currentPage = 1;
// //     fetchData(selectedClient, queryTypeDropdown.val(), currentPage, itemsPerPage);
// // });

// // queryTypeDropdown.on('change', function() {
// //     currentPage = 1;
// //     fetchData(clientNameDropdown.val(), $(this).val(), currentPage, itemsPerPage);
// // });

// // filterRow.find('input').on('input', function() {
// //     fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// // });

// // prevButton.on('click', function() {
// //     if (currentPage > 1) {
// //         currentPage--;
// //         fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// //     }
// // });

// // nextButton.on('click', function() {
// //     currentPage++;
// //     fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// // });

// // fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);


// // ###################################################################################################################################




















// // ###with owner Table #########
// // var owner_table_section_container = $('<div>').appendTo(page.body);
// // $('<hr>').appendTo(owner_table_section_container);
// // var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(owner_table_section_container);
// // owner_table_section.css({
// //     'margin-bottom': '20px',
// //     'text-align': 'center'
// // });
// // $('<hr>').appendTo(owner_table_section_container);

// // // Initialize data section and table
// // var data_section = $('<div>').addClass('data-section').appendTo(page.body);
// // data_section.css({
// //     'margin-bottom': '20px',
// //     'display': 'flex',
// //     'align-items': 'center',
// //     'flex-wrap': 'wrap'
// // });

// // var table = $('<table>').addClass('table').appendTo(data_section);
// // var thead = $('<thead>').appendTo(table);
// // var tbody = $('<tbody>').appendTo(table);
// // var tableHeaders = ['Raw Material', 'Supplier', 'Manufacturer', 'Query Types', 'Status'];

// // var headerRow = $('<tr>').appendTo(thead);
// // tableHeaders.forEach(function(label) {
// //     $('<th>').text(label).appendTo(headerRow);
// // });

// // // Add input fields for filtering below the headers
// // var filterRow = $('<tr>').appendTo(thead);
// // tableHeaders.forEach(function(label) {
// //     $('<td>').append($('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label)).appendTo(filterRow);
// // });

// // // Add pagination controls
// // var pagination_section = $('<div>').addClass('pagination-section').appendTo(page.body);
// // pagination_section.css({
// //     'display': 'flex',
// //     'justify-content': 'center',
// //     'margin-top': '20px'
// // });

// // var prevButton = $('<button>').text('Previous').addClass('btn btn-secondary').appendTo(pagination_section);
// // var nextButton = $('<button>').text('Next').addClass('btn btn-secondary').appendTo(pagination_section);

// // var currentPage = 1;
// // var itemsPerPage = 10;

// // function fetchAllData(doctype, fields, filters, callback) {
// //     var start = 0;
// //     var limit = 500; // Adjust limit as necessary for your environment
// //     var allData = [];

// //     function fetchData() {
// //         frappe.call({
// //             method: 'frappe.client.get_list',
// //             args: {
// //                 doctype: doctype,
// //                 fields: fields,
// //                 filters: filters,
// //                 limit_start: start,
// //                 limit_page_length: limit,
// //                 order_by: 'raw_material asc'
// //             },
// //             callback: function(response) {
// //                 var data = response.message;
// //                 if (data.length > 0) {
// //                     allData = allData.concat(data);
// //                     start += limit;
// //                     fetchData();
// //                 } else {
// //                     callback(allData);
// //                 }
// //             }
// //         });
// //     }

// //     fetchData();
// // }

// // // Populate client dropdown
// // fetchAllData('Query', ['client_name'], [], function(clients) {
// //     var uniqueClients = new Set();
// //     clients.forEach(function(client) {
// //         if (!uniqueClients.has(client.client_name)) {
// //             uniqueClients.add(client.client_name);
// //             $('<option>').text(client.client_name).appendTo(clientNameDropdown);
// //         }
// //     });
// // });

// // // Populate query type dropdown
// // fetchAllData('Query', ['query_types'], [], function(queryTypes) {
// //     var uniqueQueryTypes = new Set();
// //     queryTypes.forEach(function(query) {
// //         if (query.query_types) {
// //             query.query_types.split(',').forEach(function(type) {
// //                 type = type.trim();
// //                 if (type) uniqueQueryTypes.add(type);
// //             });
// //         }
// //     });
// //     uniqueQueryTypes.forEach(function(type) {
// //         $('<option>').text(type).appendTo(queryTypeDropdown);
// //     });
// // });

// // // Fetch and display data for the selected client and query type
// // function fetchData(client, queryType, page, limit) {
// //     var filters = { workflow_state: ['!=', 'Draft'] };
// //     if (client && client !== 'Select Client') {
// //         filters.client_name = client;
// //     }
// //     if (queryType && queryType !== 'Select Query Type') {
// //         filters.query_types = ['like', '%' + queryType + '%'];
// //     }

// //     var additionalFilters = {};
// //     filterRow.find('input').each(function(index) {
// //         var value = $(this).val();
// //         if (value) {
// //             additionalFilters[tableHeaders[index].toLowerCase().replace(' ', '_')] = ['like', '%' + value + '%'];
// //         }
// //     });

// //     Object.assign(filters, additionalFilters);

// //     frappe.call({
// //         method: 'frappe.client.get_list',
// //         args: {
// //             doctype: 'Query',
// //             fields: ['raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state'],
// //             filters: filters,
// //             limit_start: (page - 1) * limit,
// //             limit_page_length: limit,
// //             order_by: 'raw_material asc'
// //         },
// //         callback: function(response) {
// //             var data = response.message;
// //             tbody.empty(); // Clear existing table data
// //             data.forEach(function(row) {
// //                 var tableRow = $('<tr>').appendTo(tbody);
// //                 tableHeaders.forEach(function(key) {
// //                     var field = key.toLowerCase().replace(' ', '_');
// //                     $('<td>').text(row[field] || row['workflow_state']).appendTo(tableRow);
// //                 });
// //             });
// //         }
// //     });
// // }

// // // Update owner table based on selected client
// // function updateOwnerTable(selectedClient) {
// //     if (selectedClient !== 'Select Client') {
// //         owner_table_section.empty();

// //         frappe.call({
// //             method: 'frappe.client.get_list',
// //             args: {
// //                 doctype: 'Query',
// //                 filters: {
// //                     client_name: selectedClient
// //                 },
// //                 fields: ['client_code']
// //             },
// //             callback: function(response) {
// //                 var clientData = response.message[0];
// //                 if (clientData) {
// //                     var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
// //                     var tbody = $('<tbody>').appendTo(ownerTable);
// //                     var firstRow = $('<tr>').appendTo(tbody);
// //                     var firstRowData = $('<td>').addClass('text-center').appendTo(firstRow);
// //                     $('<h2>').text(selectedClient + ' (Code: ' + clientData.client_code + ')').appendTo(firstRowData);
// //                 }
// //             }
// //         });
// //     } else {
// //         owner_table_section.empty();
// //     }
// // }

// // // Apply filter and pagination when dropdown values or filter inputs change
// // clientNameDropdown.add(queryTypeDropdown).on('change', function() {
// //     var selectedClient = clientNameDropdown.val();
// //     updateOwnerTable(selectedClient);
// //     currentPage = 1;
// //     fetchData(selectedClient, queryTypeDropdown.val(), currentPage, itemsPerPage);
// // });

// // // Apply filters when input fields change
// // filterRow.find('input').on('input', function() {
// //     fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// // });

// // // Pagination controls
// // prevButton.on('click', function() {
// //     if (currentPage > 1) {
// //         currentPage--;
// //         fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// //     }
// // });

// // nextButton.on('click', function() {
// //     currentPage++;
// //     fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// // });

// // // Initial data fetch
// // fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// // ###with owner Table #########

// // ############################################
// // ###with out owner Table #########
// // var data_section = $('<div>').addClass('data-section').appendTo(page.body);
// // data_section.css({
// //     'margin-bottom': '20px',
// //     'display': 'flex',
// //     'align-items': 'center',
// //     'flex-wrap': 'wrap'
// // });

// // var table = $('<table>').addClass('table').appendTo(data_section);
// // var thead = $('<thead>').appendTo(table);
// // var tbody = $('<tbody>').appendTo(table);
// // var tableHeaders = ['Raw Material', 'Supplier', 'Manufacturer', 'Query Types', 'Status'];

// // var headerRow = $('<tr>').appendTo(thead);
// // tableHeaders.forEach(function(label) {
// //     $('<th>').text(label).appendTo(headerRow);
// // });

// // // Add input fields for filtering below the headers
// // var filterRow = $('<tr>').appendTo(thead);
// // tableHeaders.forEach(function(label) {
// //     $('<td>').append($('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label)).appendTo(filterRow);
// // });

// // // Add pagination controls
// // var pagination_section = $('<div>').addClass('pagination-section').appendTo(page.body);
// // pagination_section.css({
// //     'display': 'flex',
// //     'justify-content': 'center',
// //     'margin-top': '20px'
// // });

// // var prevButton = $('<button>').text('Previous').addClass('btn btn-secondary').appendTo(pagination_section);
// // var nextButton = $('<button>').text('Next').addClass('btn btn-secondary').appendTo(pagination_section);

// // var currentPage = 1;
// // var itemsPerPage = 10;

// // function fetchAllData(doctype, fields, filters, callback) {
// //     var start = 0;
// //     var limit = 500; // Adjust limit as necessary for your environment
// //     var allData = [];

// //     function fetchData() {
// //         frappe.call({
// //             method: 'frappe.client.get_list',
// //             args: {
// //                 doctype: doctype,
// //                 fields: fields,
// //                 filters: filters,
// //                 limit_start: start,
// //                 limit_page_length: limit,
// //                 order_by: 'raw_material asc'
// //             },
// //             callback: function(response) {
// //                 var data = response.message;
// //                 if (data.length > 0) {
// //                     allData = allData.concat(data);
// //                     start += limit;
// //                     fetchData();
// //                 } else {
// //                     callback(allData);
// //                 }
// //             }
// //         });
// //     }

// //     fetchData();
// // }

// // // Populate client dropdown
// // fetchAllData('Query', ['client_name'], [], function(clients) {
// //     var uniqueClients = new Set();
// //     clients.forEach(function(client) {
// //         if (!uniqueClients.has(client.client_name)) {
// //             uniqueClients.add(client.client_name);
// //             $('<option>').text(client.client_name).appendTo(clientNameDropdown);
// //         }
// //     });
// // });

// // // Populate query type dropdown
// // fetchAllData('Query', ['query_types'], [], function(queryTypes) {
// //     var uniqueQueryTypes = new Set();
// //     queryTypes.forEach(function(query) {
// //         if (query.query_types) {
// //             query.query_types.split(',').forEach(function(type) {
// //                 type = type.trim();
// //                 if (type) uniqueQueryTypes.add(type);
// //             });
// //         }
// //     });
// //     uniqueQueryTypes.forEach(function(type) {
// //         $('<option>').text(type).appendTo(queryTypeDropdown);
// //     });
// // });

// // // Fetch and display data for the selected client and query type
// // function fetchData(client, queryType, page, limit) {
// //     var filters = { workflow_state: ['!=', 'Draft'] };
// //     if (client && client !== 'Select Client') {
// //         filters.client_name = client;
// //     }
// //     if (queryType && queryType !== 'Select Query Type') {
// //         filters.query_types = ['like', '%' + queryType + '%'];
// //     }

// //     var additionalFilters = {};
// //     filterRow.find('input').each(function(index) {
// //         var value = $(this).val();
// //         if (value) {
// //             additionalFilters[tableHeaders[index].toLowerCase().replace(' ', '_')] = ['like', '%' + value + '%'];
// //         }
// //     });

// //     Object.assign(filters, additionalFilters);

// //     frappe.call({
// //         method: 'frappe.client.get_list',
// //         args: {
// //             doctype: 'Query',
// //             fields: ['raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state'],
// //             filters: filters,
// //             limit_start: (page - 1) * limit,
// //             limit_page_length: limit,
// //             order_by: 'raw_material asc'
// //         },
// //         callback: function(response) {
// //             var data = response.message;
// //             tbody.empty(); // Clear existing table data
// //             data.forEach(function(row) {
// //                 var tableRow = $('<tr>').appendTo(tbody);
// //                 tableHeaders.forEach(function(key) {
// //                     var field = key.toLowerCase().replace(' ', '_');
// //                     $('<td>').text(row[field] || row['workflow_state']).appendTo(tableRow);
// //                 });
// //             });
// //         }
// //     });
// // }

// // // Apply filter and pagination when dropdown values or filter inputs change
// // clientNameDropdown.add(queryTypeDropdown).on('change', function() {
// //     currentPage = 1;
// //     fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// // });

// // filterRow.find('input').on('input', function() {
// //     currentPage = 1;
// //     fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// // });

// // prevButton.on('click', function() {
// //     if (currentPage > 1) {
// //         currentPage--;
// //         fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// //     }
// // });

// // nextButton.on('click', function() {
// //     currentPage++;
// //     fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// // });

// // // Initial fetch to display all data
// // fetchData(clientNameDropdown.val(), queryTypeDropdown.val(), currentPage, itemsPerPage);
// 	// ###withoutOwnertable###
		// Footer section
		var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
		footer_section.css({
			'margin-top': '25px',
			'border-top': '1px solid #ccc',
			'padding-top': '10px',
			'text-align': 'center'
		});
	
		$('<hr>').appendTo(footer_section);
	
		$('<p>').html('<strong>Sanha Halal Associates Pakistan PVT. LTD.</strong> Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama D.H.A. phase 5<br>Email: evaluation@sanha.org.pk - Ph: +92 21 35295263').appendTo(footer_section);
	
		$('<hr>').appendTo(footer_section);
	};

// // ########## without Owner Table########## 
//     // var uniqueClients = new Set(); // Keep track of unique client names
// // frappe.call({
// //     method: 'frappe.client.get_list',
// //     args: {
// //         doctype: 'Query',
// //         fields: ['client_name']
// //     },
// //     callback: function(response) {
// //         var clients = response.message;

// //         clients.forEach(function(client) {
// //             // Add client name to the set if it doesn't already exist
// //             if (!uniqueClients.has(client.client_name)) {
// //                 uniqueClients.add(client.client_name);
// //                 $('<option>').text(client.client_name).appendTo(clientNameDropdown);
// //             }
// //         });
// //     }
// // });

// // // Client selection change event
// // clientNameDropdown.on('change', function() {
// //     var selectedClient = $(this).val();
// //     var selectedClientCode = ''; // Fetch client code from the Query doctype
// //     if (selectedClient !== 'Select Client') {
// //         // Clear existing owner table content
// //         owner_table_section.empty();

// //         // Fetch and display client information in owner table
// //         frappe.call({
// //             method: 'frappe.client.get',
// //             args: {
// //                 doctype: 'Query',
// //                 filters: {
// //                     client_name: selectedClient
// //                 },
// //                 fields: ['client_code']
// //             },
// //             callback: function(response) {
// //                 var clientData = response.message;
// //                 if (clientData) {
// //                     // Display client name and client code in owner table
// //                     var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
// //                     var tbody = $('<tbody>').appendTo(ownerTable);
// //                     var firstRow = $('<tr>').appendTo(tbody);
// //                     var firstRowData = $('<td>').addClass('text-center').appendTo(firstRow);
// //                     $('<h2>').text(selectedClient + ' (Code: ' + clientData.client_code + ')').appendTo(firstRowData);
// //                 }
// //             }
// //         });

// //         // Fetch and display data for the selected client and query type
// //         fetchData(selectedClient, queryTypeDropdown.val());
// //     } else {
// //         // Clear owner table when 'Select Client' is selected
// //         owner_table_section.empty();
// //     }
// // });
// // Client selection change event
// // clientNameDropdown.on('change', function() {
// //     var selectedClient = $(this).val();
// //     var selectedClientCode = ''; // Fetch client code from the Query doctype
// //     fetchData(selectedClient, queryTypeDropdown.val()); // Fetch data for selected client and query type
// //     if (selectedClient !== 'Select Client') {
// //         frappe.call({
// //             method: 'frappe.client.get',
// //             args: {
// //                 doctype: 'Query',
// //                 filters: {
// //                     client_name: selectedClient
// //                 },
// //                 fields: ['client_code']
// //             },
// //             callback: function(response) {
// //                 var clientData = response.message;
// //                 if (clientData) {
// //                     // Display client name and client code in owner table
// //                     var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
// //                     var tbody = $('<tbody>').appendTo(ownerTable);
// //                     var firstRow = $('<tr>').appendTo(tbody);
// //                     var firstRowData = $('<td>').addClass('text-center').appendTo(firstRow);
// //                     $('<h2>').text(selectedClient + ' (Code: ' + clientData.client_code + ')').appendTo(firstRowData);
// //                 }
// //             }
// //         });
// //     } else {
// //         // Clear owner table when no client is selected
// //         owner_table_section.empty();
// //     }
// // });
