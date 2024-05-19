frappe.pages['print-page-'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Report Print Page ',
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
        
        window.print();
        // Show page title after printing
        page.$title_area.show();
        // Show filter row after printing
        $('.filter-row').show();
        // Show filter section after printing
        $('.filter-section').show();
    });
    // Align action buttons to the right
    action_section.css({
        'display': 'flex',
        'justify-content': 'flex-end', // Align items to the right
        'margin-bottom': '20px' // Add margin below action section
    });
	var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);

    var clientNameDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
    $('<option>').text('Select Client').appendTo(clientNameDropdown);

    var queryTypeInput = $('<input>').attr('type', 'text').attr('placeholder', 'Filter Query Type').addClass('form-control').appendTo(filterSection);

    // Data section
    var data_section = $('<div>').addClass('data-section').appendTo(page.body);
    data_section.css({
        'margin-bottom': '20px',
        'display': 'flex',
        'align-items': 'center',
        'flex-wrap': 'wrap'
    });

    var table = $('<table>').addClass('table').appendTo(page.body);
    var thead = $('<thead>').appendTo(table);
    var tbody = $('<tbody>').appendTo(table);

    var headerRow = $('<tr>').appendTo(thead);
    ['Raw Material', 'Supplier', 'Manufacturer', 'Query Types', 'Status', 'Client Name'].forEach(function(label) {
        $('<th>').text(label).appendTo(headerRow);
    });

    var data; // Store the data for filtering

    // Client information table section
    var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(page.body);
    owner_table_section.css({
        'margin-bottom': '20px',
        'text-align': 'center'
    });

    // Fetch client names and codes from Query doctype
    var uniqueClients = new Set(); // Keep track of unique client names
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Query',
            fields: ['client_name', 'client_code']
        },
        callback: function(response) {
            var clients = response.message;

            clients.forEach(function(client) {
                // Check if client name is already added to the dropdown
                if (!uniqueClients.has(client.client_name)) {
                    uniqueClients.add(client.client_name);
                    $('<option>').text(client.client_name).appendTo(clientNameDropdown).attr('data-client-name', client.client_name).attr('data-client-code', client.client_code);
                }
            });
        }
    });

    clientNameDropdown.on('change', function() {
        var selectedClientName = $(this).find('option:selected').attr('data-client-name');
        var selectedClientCode = $(this).find('option:selected').attr('data-client-code');

        // Display client information in owner table
        owner_table_section.empty();
        var owner_table = $('<table>').addClass('table').appendTo(owner_table_section);
        var tbody = $('<tbody>').appendTo(owner_table);

        var first_row = $('<tr>').appendTo(tbody);
        var first_row_data = $('<td>').addClass('text-center').appendTo(first_row);
        $('<h2>').text(selectedClientName + ' (Code: ' + selectedClientCode + ')').appendTo(first_row_data);
    });

    queryTypeInput.on('input', filterTable);

    function filterTable() {
        var queryTypeFilter = queryTypeInput.val().trim().toLowerCase();

        tbody.empty(); // Clear the table body before appending filtered rows

        data.forEach(function(row) {
            var queryType = row.query_types.toLowerCase();

            if (queryType.includes(queryTypeFilter)) {
                var tableRow = $('<tr>').appendTo(tbody);
                ['raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state', 'client_name'].forEach(function(field) {
                    $('<td>').text(row[field]).appendTo(tableRow);
                });
            }
        });
    }

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
// Create filter section for query types dropdown
// var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
// filterSection.css({
// 	'margin-bottom': '20px',
// 	'display': 'flex',
// 	'justify-content': 'space-between',
// 	'align-items': 'center'
// });

// var clientNameDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
// $('<option>').text('Select Client').appendTo(clientNameDropdown);

// var queryTypeInput = $('<input>').attr('type', 'text').attr('placeholder', 'Filter Query Type').addClass('form-control').appendTo(filterSection);



// // Header section


//     var header_section = $('<div>').addClass('header-section').appendTo(page.body);
// header_section.css({
//     'padding': '20px',
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
//     'width': '55%'
// });
// var logo = $('<img>').attr('src', 'http://portal.sanha.org.pk/assets/dist/img/sanha-logo.png').addClass('img').appendTo(logo_container);
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

// var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(header_section);
// owner_table_section.css({
// 	'margin-bottom': '20px',
// 	'text-align': 'center'
// });

// // Fetch current user's full name and location code
// frappe.call({
// 	method: 'frappe.client.get',
// 	args: {
// 		doctype: 'User',
// 		filters: {
// 			name: frappe.session.user // Get current session user's name
// 		},
// 		fields: ['full_name', 'location'] // Fetch full name and location fields
// 	},
// 	callback: function(response) {
// 		var user = response.message;
// 		if (user) {
// 			// Create table for owner data
// 			var owner_table = $('<table>').addClass('table').appendTo(owner_table_section);
// 			var tbody = $('<tbody>').appendTo(owner_table);

// 			// First row: Full name and location code
// 			var first_row = $('<tr>').appendTo(tbody);
// 			var first_row_data = $('<td>').addClass('text-center').appendTo(first_row);
// 			$('<h2>').text(user.full_name + ' (Code: ' + user.location + ')').appendTo(first_row_data);

// 			// Second row: Date range
// 			var second_row = $('<tr>').appendTo(tbody);
// 			var second_row_data = $('<td>').addClass('text-center').appendTo(second_row);
// 			$('<span>').append($('<strong>').text('From Date: 09-Mar-2024 - To Date: 08-May-2024')).appendTo(second_row_data);
// 		}
// 	}
// });

// clientNameDropdown.on('change', function() {
// 	var selectedClientName = $(this).find('option:selected').text();

// 	// Display client information in owner table
// 	owner_table_section.empty();
// 	var owner_table = $('<table>').addClass('table').appendTo(owner_table_section);
// 	var tbody = $('<tbody>').appendTo(owner_table);

// 	var first_row = $('<tr>').appendTo(tbody);
// 	var first_row_data = $('<td>').addClass('text-center').appendTo(first_row);
// 	$('<h2>').text(selectedClientName).appendTo(first_row_data);

// 	// Fetch client data based on the selected client
// 	frappe.call({
// 		method: 'frappe.client.get_list',
// 		args: {
// 			doctype: 'Query',
// 			filters: {
// 				client_name: selectedClientName // Filter by selected client name
// 			},
// 			fields: ['full_name', 'location'] // Fetch full name and location fields
// 		},
// 		callback: function(response) {
// 			var clientData = response.message;
// 			if (clientData) {
// 				clientData.forEach(function(client) {
// 					// Additional rows for client data
// 					var client_row = $('<tr>').appendTo(tbody);
// 					var client_row_data = $('<td>').addClass('text-center').appendTo(client_row);
// 					$('<span>').append($('<strong>').text('Client Data: ' + client.full_name + ' (Code: ' + client.location + ')')).appendTo(client_row_data);
// 				});
// 			}
// 		}
// 	});
// });

// queryTypeInput.on('input', filterTable);

// function filterTable() {
	
// }
// Filtering logic goes here
    // Footer section
 
    // var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
    // filterSection.css({
    //     'margin-bottom': '20px', // Add margin below the filter section
    //     'display': 'flex',
    //     'justify-content': 'space-between', // Align items with space between
    //     'align-items': 'center' // Align items at the center vertically
    // });

    // // Client selection dropdown
    // var clientNameDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
    // $('<option>').text('Select Client').appendTo(clientNameDropdown);

    // // Query type selection dropdown
    // var queryTypeDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
    // $('<option>').text('Select Query Type').appendTo(queryTypeDropdown);

    // // Data section
    // var data_section = $('<div>').addClass('data-section').appendTo(page.body);
    // data_section.css({
    //     'margin-bottom': '20px', // Add margin below the data section
    //     'display': 'flex',
    //     'align-items': 'center',
    //     'flex-wrap': 'wrap'
    // });

    // // Query table
    // var table = $('<table>').addClass('table').appendTo(data_section);
    // var thead = $('<thead>').appendTo(table);
    // var tbody = $('<tbody>').appendTo(table);
    // var tableHeaders = ['Raw Material', 'Supplier', 'Manufacturer', 'Query Types', 'Status'];

    // // Add table headers
    // var headerRow = $('<tr>').appendTo(thead);
    // $.each(tableHeaders, function(index, label) {
    //     $('<th>').text(label).appendTo(headerRow);
    // });

    // // Fetch data from the server and populate the table
    // function fetchData(client, queryType) {
    //     var filters = {
    //         workflow_state: ['!=', 'Draft']
    //     };

    //     if (client && client !== 'Select Client') {
    //         filters.client_name = client;
    //     }

    //     if (queryType && queryType !== 'Select Query Type') {
    //         filters.query_types = ['like', '%' + queryType + '%'];
    //     }

    //     frappe.call({
    //         method: 'frappe.client.get_list',
    //         args: {
    //             doctype: 'Query',
    //             filters: filters,
    //             fields: ['raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state']
    //         },
    //         callback: function(response) {
    //             var data = response.message;
    //             tbody.empty(); // Clear existing table data
    //             $.each(data, function(index, row) {
    //                 var tableRow = $('<tr>').appendTo(tbody);
    //                 $.each(tableHeaders, function(index, key) {
    //                     if (key === 'Status') {
    //                         $('<td>').text(row['workflow_state']).appendTo(tableRow);
    //                     } else {
    //                         $('<td>').text(row[key.toLowerCase().replace(' ', '_')]).appendTo(tableRow);
    //                     }
    //                 });
    //             });
    //         }
    //     });
    // }

    // // Fetch client names and populate client dropdown
    // frappe.call({
    //     method: 'frappe.client.get_list',
    //     args: {
    //         doctype: 'Query',
    //         fields: ['client_name']
    //     },
    //     callback: function(response) {
    //         var clients = response.message;
    //         $.each(clients, function(index, client) {
    //             $('<option>').text(client.client_name).appendTo(clientNameDropdown);
    //         });
    //     }
    // });

    // // Fetch query types and populate query type dropdown
    // frappe.call({
    //     method: 'frappe.client.get_list',
    //     args: {
    //         doctype: 'Query',
    //         fields: ['query_types']
    //     },
    //     callback: function(response) {
    //         var queryTypes = response.message;
    //         var uniqueQueryTypes = [];
    //         $.each(queryTypes, function(index, query) {
    //             if (query.query_types) {
    //                 var types = query.query_types.split(',');
    //                 $.each(types, function(index, type) {
    //                     type = type.trim();
    //                     if (!uniqueQueryTypes.includes(type) && type !== '') {
    //                         uniqueQueryTypes.push(type);
    //                         $('<option>').text(type).appendTo(queryTypeDropdown);
    //                     }
    //                 });
    //             }
    //         });
    //     }
    // });

    // // Owner table section
    // var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(page.body);
    // owner_table_section.css({
    //     'margin-bottom': '20px', // Add margin below the owner table section
    //     'text-align': 'center' // Center the content within the owner table section
    // });

    // // Client selection change event
    // clientNameDropdown.on('change', function() {
    //     var selectedClient = $(this).val();
    //     var selectedClientCode = ''; // Fetch client code from the Query doctype
    //     fetchData(selectedClient, queryTypeDropdown.val()); // Fetch data for selected client and query type
    //     if (selectedClient !== 'Select Client') {
    //         frappe.call({
    //             method: 'frappe.client.get',
    //             args: {
    //                 doctype: 'Query',
    //                 filters: {
    //                     client_name: selectedClient
    //                 },
    //                 fields: ['client_code']
    //             },
    //             callback: function(response) {
    //                 var clientData = response.message;
    //                 if (clientData) {
    //                     // Display client name and client code in owner table
    //                     var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
    //                     var tbody = $('<tbody>').appendTo(ownerTable);
    //                     var firstRow = $('<tr>').appendTo(tbody);
    //                     var firstRowData = $('<td>').addClass('text-center').appendTo(firstRow);
    //                     $('<h2>').text(selectedClient + ' (Code: ' + clientData.client_code + ')').appendTo(firstRowData);
    //                 }
    //             }
    //         });
    //     } else {
    //         // Clear owner table when no client is selected
    //         owner_table_section.empty();
    //     }
    // });

    // // Apply filter when query type dropdown value changes
    // queryTypeDropdown.on('change', function() {
    //     fetchData(clientNameDropdown.val(), $(this).val());
    // });

// ### Working with filter ####
//     $('<hr>').appendTo(footer_section);
//     var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
//     footer_section.css({
//         'margin-top': '25px', // Set footer top margin to 25px
//         'border-top': '1px solid #ccc', // Add horizontal line at the top of the footer
//         'padding-top': '10px', // Add padding to the top of the footer
//         'text-align': 'center'
//     });
    
//     // Add horizontal lines on both ends of the footer
//     $('<hr>').appendTo(footer_section);
    
    
//     // Add company address
//     $('<p>').html('<strong>Sanha Halal Associates Pakistan PVT. LTD.</strong> Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama D.H.A. phase 5<br>Email: evaluation@sanha.org.pk - Ph: +92 21 35295263').appendTo(footer_section);
    
//     // Add footer with page number
// };