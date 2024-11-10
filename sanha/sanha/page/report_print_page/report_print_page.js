frappe.pages['report-print-page'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Report Print Page',
        single_column: true
    });
 // Action section
var action_section = $('<div>').addClass('action-section').appendTo(page.body);
// Add Print Button to the action section
var printButton = $('<button>').text('Print').addClass('btn btn-primary').appendTo(action_section);

// Attach event handler for the print button
printButton.on('click', function() {
    console.log("Print button clicked with selection logic!");

    // Update selected items from the current page before printing
    updateSelectedItems();

    // Fetch data based on selection or fetch all if no selection is made
    fetchSelectedDataOrAll(function(filteredData) {
        console.log("Data fetched for printing", filteredData);  // Debugging statement

        var groupedData = groupDataByHeader(filteredData);  // Group data as needed

        // Hide sections before printing
        page.$title_area.hide();
        $('.filter-row').hide();
        $('.filter-section').hide();
        $('.pagination-section').hide();
        $('.action-section').hide();

        // Render selected or all data into the table for printing
        renderTable(groupedData);  // This function will render the data into the table

        // Trigger print dialog
        window.print();

        // Show sections after printing
        page.$title_area.show();
        $('.filter-row').show();
        $('.filter-section').show();
        $('.pagination-section').show();
        $('.action-section').show();
    });
});

// Align action buttons to the right
action_section.css({
    'display': 'flex',
    'justify-content': 'flex-end',  // Align buttons to the right
    'margin-bottom': '10px'         // Add margin below the action section
});

// Align action buttons to the right
action_section.css({
    'display': 'flex',
    'justify-content': 'flex-end',  // Align buttons to the right
    'margin-bottom': '10px'         // Add margin below the action section
});
    
// Align action buttons to the right
    action_section.css({
        'display': 'flex',
        'justify-content': 'flex-end', // Align items to the right
        'margin-bottom': '10px' // Add margin below action section
    });


 // Create and append the Print button
 
     var header_section = $('<div>').addClass('header-section').appendTo(page.body);
     header_section.css({
         'padding': '20px',
         'margin-top': '30px',
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
 
     var logo = $('<img>').attr('src', '/files/sanha-logo.png').addClass('img').appendTo(logo_container);
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
 
     // Add a loading spinner during data fetch
 
 // Filter section styling
 
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
 var td = $('<td>').appendTo(table);
 var thead = $('<thead>').appendTo(table);
 var tbody = $('<tbody>').appendTo(table);
 var tableHeaders = ['Raw Material', 'Supplier', 'Manufacturer', 'Status'];
 
 // Header row with "Select All" checkbox
 var headerRow = $('<tr>').appendTo(thead);
 $('<th  class="checkbox-column">').append($('<input type="checkbox" id="select-all">')).appendTo(headerRow);
 tableHeaders.forEach(function(label) {
     $('<th>').text(label).appendTo(headerRow);
 });
 
 
 var filterRow = $('<tr>').addClass('filter-row').appendTo(thead); // Add class to the filter row
 // Add empty cell for checkbox column
 $('<td>').appendTo(filterRow);
 tableHeaders.forEach(function(label) {
 var filterInput = $('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label); // Create filter input
 $('<td>').append(filterInput).appendTo(filterRow); // Append input to filter row cell
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
             fields: ['name', 'raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types'],
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
                 $('<tr>').append($('<td colspan="5">').text(queryType).css('font-weight', 'bold')).appendTo(tbody); // Updated colspan to 5
                 groupedData[queryType].forEach(function(row) {
                     var tableRow = $('<tr>').appendTo(tbody);
                     $('<td  class="checkbox-column">').html('<input type="checkbox" class="select-checkbox" data-name="' + row.name + '">').appendTo(tableRow); // Checkbox for each row
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
 
// Function to update and display the total count of records
            // Now fetch detailed data and display it
            function updateOwnerTable() {
                owner_table_section.empty();
            
                // Fetch total count of queries for the current user
                frappe.call({
                    method: 'frappe.client.get_list',
                    args: {
                        doctype: 'Query',
                        filters: {
                            owner: frappe.session.user,
                            'workflow_state': ['!=', 'Draft']  // Exclude Draft records
                        },
                        fields: ['name'],
                        limit_start: 0,
                        limit_page_length: 0  // Only get the count
                    },
                    callback: function(response) {
                        var totalCount = response.message.length;
            
                        // Create table for Client Name and Client Code
                        var table = $('<table>').addClass('table table-bordered').appendTo(owner_table_section);
                        var thead = $('<thead>').appendTo(table);
                        var headerRow = $('<tr>').appendTo(thead);
                        $('<th>').text('Client Name').appendTo(headerRow);
                        $('<th>').text('Client Code').appendTo(headerRow);
            
                        var tbody = $('<tbody>').appendTo(table);
            
                        // Fetch detailed query data (client_name and client_code)
                        frappe.call({
                            method: 'frappe.client.get_list',
                            args: {
                                doctype: 'Query',
                                filters: {
                                    owner: frappe.session.user,
                                    client_name: ['!=', ''],  // Exclude null client names
                                    client_code: ['!=', '']   // Exclude null client codes
                                },
                                fields: ['name', 'client_name', 'client_code']
                            },
                            callback: function(response) {
                                var data = response.message;
                                var uniqueClients = new Set();
            
                                // Populate table with unique client names and codes
                                data.forEach(function(row) {
                                    if (!uniqueClients.has(row.client_code)) {
                                        uniqueClients.add(row.client_code);
                                        var tableRow = $('<tr>').appendTo(tbody);
            
                                        // Make Client Name and Client Code bold
                                        $('<td>').css('font-weight', 'bold').text(row.client_name).appendTo(tableRow);
                                        $('<td>').css('font-weight', 'bold').text(row.client_code).appendTo(tableRow);
                                    }
                                });
            
                                // Now, add the total query count row at the bottom of the table
                                var totalRow = $('<tr>').appendTo(tbody);
                                $('<td>').attr('colspan', 2).css({
                                    'font-weight': 'bold',
                                    'text-align': 'right'  // Align the text to the right
                                }).text('Total Queries: ' + totalCount).appendTo(totalRow);
            
                                // Add event listener for query selection (checkbox logic)
                                $('.select-checkbox').on('change', function() {
                                    var selectedCount = getSelectedItems().length; // Get the number of selected queries
            
                                    if (selectedCount > 0) {
                                        // If something is selected, show "1 of total"
                                        totalRow.find('td').text(`${selectedCount} of ${totalCount} Queries`);
                                    } else {
                                        // If nothing is selected, revert to showing total
                                        totalRow.find('td').text('Total Queries: ' + totalCount);
                                    }
                                });
                            }
                        });
                    }
                });
            }
 
 // Function to get selected items (assuming checkboxes are used for selection)
 // Function to get selected items (returns selected item names)
function getSelectedItems() {
    var selectedItems = [];
    $('.select-checkbox:checked').each(function() {
        selectedItems.push($(this).data('name'));
    });
    return selectedItems;
}

// Function to fetch and display the selected data (or all data if nothing is selected)
function fetchSelectedDataOrAll(callback) {
    var selectedItems = getSelectedItems();
    
    var filters = {
        workflow_state: ['!=', 'Draft'],  // Default filter to exclude Drafts
        owner: frappe.session.user  // Filter by current user
    };

    // If items are selected, fetch only those items
    if (selectedItems.length > 0) {
        filters['name'] = ['in', selectedItems];  // Filter by selected item names
    }

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Query',  // Adjust the doctype name to match your specific doctype
            filters: filters,
            fields: ['name', 'raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types']
        },
        callback: function(response) {
            callback(response.message);
        }
    });
}

 function getSelectedItems() {
     var selectedItems = [];
     $('.select-checkbox:checked').each(function() {
         selectedItems.push($(this).data('name'));
     });
     return selectedItems;
 }
 
 
 // Group data by header
 function groupDataByHeader(data) {
     var groupedData = {};
     data.forEach(function(item) {
         var queryType = item.query_types || 'Unknown';
         if (!groupedData[queryType]) {
             groupedData[queryType] = [];
         }
         groupedData[queryType].push(item);
     });
     return groupedData;
 }
 
 // Render table with data
 function renderTable(groupedData) {
     tbody.empty();
 
     Object.keys(groupedData).forEach(function(queryType) {
         var headerRow = $('<tr>').appendTo(tbody);
         $('<th>').attr('colspan', tableHeaders.length + 1).text(queryType).appendTo(headerRow);
 
         groupedData[queryType].forEach(function(row) {
             var tableRow = $('<tr>').appendTo(tbody);
             var checkbox = $('<input>').attr('type', 'checkbox').addClass('select-checkbox').data('name', row.name);
             
             // Add a class to the checkbox for styling when printing
             if (isPrinting()) {
                 checkbox.addClass('hide-on-print');
             }
             
             $('<td>').append(checkbox).appendTo(tableRow);
 
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
     });
 }
 
 // Function to check if the page is being printed
 
 // Function to update date range on filter dropdown change
 queryTypeDropdown.on('change', function() {
     var selectedQueryType = $(this).val();
     var filters = {
         workflow_state: ['!=', 'Draft'],
         owner: frappe.session.user
     };
 
     if (selectedQueryType !== 'Select Query Type') {
         filters.query_types = ['like', '%' + selectedQueryType + '%'];
     }
 
     // Update date range based on selected filters
     updateDateRange(filters);
 });
 
 // Function to update date range on checkbox selection change
 $('.select-checkbox').on('change', function() {
     var selectedItems = getSelectedItems();
     var filters = {
         workflow_state: ['!=', 'Draft'],
         owner: frappe.session.user
     };
 
     if (selectedItems.length > 0) {
         filters['name'] = ['in', selectedItems];
     }
 
     // Update date range based on selected filters
     updateDateRange(filters);
 });
 
 // Function to update date range on filter dropdown change
 queryTypeDropdown.on('change', function() {
 var selectedQueryType = $(this).val();
 var filters = {
     workflow_state: ['!=', 'Draft'],
     owner: frappe.session.user
 };
 
 if (selectedQueryType !== 'Select Query Type') {
     filters.query_types = ['like', '%' + selectedQueryType + '%'];
 }
 
 // Update date range based on selected filters
 updateDateRange(filters);
 });
 
 // Function to update date range on checkbox selection change
 $('.select-checkbox').on('change', function() {
 var selectedItems = getSelectedItems();
 var filters = {
     workflow_state: ['!=', 'Draft'],
     owner: frappe.session.user
 };
 
 if (selectedItems.length > 0) {
     filters['name'] = ['in', selectedItems];
 }
 
 // Update date range based on selected filters
 updateDateRange(filters);
});

// Function to update the date range based on the fetched data
function updateDateRange(filters) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Query',  // Adjust the doctype name to match your specific doctype
            filters: filters,
            fields: ['creation'],  // Fetch only the 'creation' field
            order_by: 'creation asc',  // Ensure it’s sorted by creation date
        },
        callback: function(response) {
            if (response.message && response.message.length > 0) {
                var dates = response.message.map(item => new Date(item.creation));
                
                // Format dates as 'DD-MM-YYYY hh:mm AM/PM'
                function formatDate(date) {
                    let day = String(date.getDate()).padStart(2, '0');
                    let month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-based
                    let year = date.getFullYear();
                    let hours = date.getHours();
                    let minutes = String(date.getMinutes()).padStart(2, '0');
                    let ampm = hours >= 12 ? 'PM' : 'AM';
                    hours = hours % 12 || 12;  // Convert to 12-hour format and handle midnight
                    return `${day}-${month}-${year} ${hours}:${minutes} ${ampm}`;
                }

                // Get formatted oldest and latest dates
                var oldestDate = formatDate(dates[0]);
                var latestDate = formatDate(dates[dates.length - 1]);

                // Update the date range section
                date_range_section.empty();
                $('<p>').html(`Date Range: <strong>From: ${oldestDate}</strong> To: <strong>${latestDate}</strong>`).appendTo(date_range_section);
            } else {
                date_range_section.empty();
                $('<p>').text('Date Range: No Data Available').appendTo(date_range_section);
            }
        },
        error: function(error) {
            console.error("Error fetching date range:", error);
            date_range_section.empty();
            $('<p>').text('Date Range: Error fetching data').appendTo(date_range_section);
        }
    });
}


 // Update date range for selected items
 
 
 
 // Get selected items
 function getSelectedItems() {
     var selectedItems = [];
     $('.select-checkbox:checked').each(function() {
         selectedItems.push($(this).data('name'));
     });
     return selectedItems;
 }
 
 // Fetch data for selected items
 // Fetch data for selected items and exclude "Draft" state
 
 function fetchSelectedData(selectedItems, callback) {
     frappe.call({
         method: 'frappe.client.get_list',
         args: {
             doctype: 'Query',
             filters: { 'name': ['in', selectedItems] },
             fields: ['name', 'raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types']
         },
         callback: function(response) {
             callback(response.message);
         }
     });
 }
 
 // Get selected items
 function getSelectedItems() {
 var selectedItems = [];
 $('.select-checkbox:checked').each(function() {
     selectedItems.push($(this).data('name'));
 });
 return selectedItems;
 }
 
 // Fetch data for selected items
 function fetchSelectedData(selectedItems, callback) {
 frappe.call({
     method: 'frappe.client.get_list',
     args: {
         doctype: 'Query',
         filters: { 'name': ['in', selectedItems] },
         fields: ['name', 'raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types']
     },
     callback: function(response) {
         callback(response.message);
     }
 });
 }
 
 // Update date range on checkbox change
 function onCheckboxChange() {
 var selectedItems = getSelectedItems();
 if (selectedItems.length > 0) {
     fetchSelectedData(selectedItems, function(filteredData) {
         updateDateRangeForSelected(filteredData);
     });
 } else {
     updateDateRange(defaultFilters); // Reset to default date range if no items are selected
 }
 }
 
 // Attach event listener to checkboxes
 $(document).on('change', '.select-checkbox', onCheckboxChange);
 
 // Select all checkboxes
 $('#select-all').on('change', function() {
 $('.select-checkbox').prop('checked', $(this).prop('checked')).trigger('change');
 });
 
 fetchData(currentPage, itemsPerPage);
 updateOwnerTable();
 
 // Pagination event listeners
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
 
 // Filter event listener
 filterRow.find('input').on('input', function() {
     currentPage = 1;
     fetchData(currentPage, itemsPerPage);
 });
 
 // Query type dropdown event listener
 queryTypeDropdown.on('change', function() {
     currentPage = 1;
     fetchData(currentPage, itemsPerPage);
 });
 // Function to hide sections and prepare the page for printing
 var selectedItems = new Set();  // Track selected items globally

 // Function to get selected items from the current page and update the global set
function updateSelectedItems() {
    // Add checked items to the Set
    $('.select-checkbox:checked').each(function() {
        selectedItems.add($(this).data('name'));  // Add selected items to Set
    });

    // Remove unchecked items from the Set
    $('.select-checkbox:not(:checked)').each(function() {
        selectedItems.delete($(this).data('name'));  // Remove unselected items
    });
}
// Function to fetch selected data or all data if no selection is made
function fetchSelectedDataOrAll(callback) {
    // If no items are selected, fetch all data
    if (selectedItems.size === 0) {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',  // Adjust this to your doctype
                filters: { workflow_state: ['!=', 'Draft'], owner: frappe.session.user },
                fields: ['name', 'raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types'],
                limit_page_length: 0  // Fetch all items (no pagination limit)
            },
            callback: function(response) {
                callback(response.message);  // Pass fetched data to the callback
            }
        });
    } else {
        // If items are selected, fetch only the selected items
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Query',  // Adjust this to your doctype
                filters: { 'name': ['in', Array.from(selectedItems)] },  // Fetch only selected items
                fields: ['name', 'raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types'],
                limit_page_length: 0  // Fetch all selected items without pagination limit
            },
            callback: function(response) {
                callback(response.message);  // Pass fetched data to the callback
            }
        });
    }
}
// Function to render the table with data for printing
function renderTable(groupedData) {
    tbody.empty();  // Clear the table before rendering

    // Render grouped data into the table
    Object.keys(groupedData).forEach(function(queryType) {
        var headerRow = $('<tr>').appendTo(tbody);
        $('<th>').attr('colspan', tableHeaders.length + 1).text(queryType).appendTo(headerRow);  // Add query type header

        groupedData[queryType].forEach(function(row) {
            var tableRow = $('<tr>').appendTo(tbody);
            $('<td>').html('<input type="checkbox" class="select-checkbox" data-name="' + row.name + '" style="display: none;">').appendTo(tableRow);  // Hidden checkbox

            tableHeaders.forEach(function(key) {
                // Use the fieldMap to match header to field name
                var fieldMap = {
                    'Raw Material': 'raw_material',
                    'Supplier': 'supplier',
                    'Manufacturer': 'manufacturer',
                    'Status': 'workflow_state'  // Correctly map 'Status' to 'workflow_state'
                };

                var field = fieldMap[key];  // Get the correct field from the map

                if (field === 'workflow_state') {
                    // Special case for workflow_state
                    $('<td>').text(row['workflow_state'] || 'N/A').appendTo(tableRow);  // Add status field to the table
                } else if (field === 'creation') {
                    // Handle creation field separately
                    var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
                    $('<td>').text(formattedDate).appendTo(tableRow);  // Add formatted date
                } else {
                    $('<td>').text(row[field] || 'N/A').appendTo(tableRow);  // Add other data fields
                }
            });
        });
    });
}

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

// frappe.pages['report-print-page'].on_page_load = function(wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Report Print Page',
//         single_column: true
//     });

//     var action_section = $('<div>').addClass('action-section').appendTo(page.body);

//     // Print button
//     var printButton = $('<button>').text('Print').addClass('btn btn-primary').appendTo(action_section);
//  // Print button click handler
//  printButton.on('click', function() {
//     var selectedItems = getSelectedItems();
//     if (selectedItems.length > 0) {
//         fetchSelectedData(selectedItems, function(filteredData) {
//             var groupedData = groupDataByHeader(filteredData);
//             updateDateRangeForSelected(filteredData);

//             // Hide sections before printing
//             hideSections();

//             // Render selected data into table for printing
//             renderTable(groupedData);

//             window.print();

//             // Show sections after printing
//             showSections();
//         });
//     } else {
//         // Hide sections before printing
//         hideSections();

//         // Render data into table for printing
//         renderTable(groupedData);

//         window.print();

//         // Show sections after printing
//         showSections();
//     }
// });

// // Function to hide sections before printing
// function hideSections() {
//     page.$title_area.hide();
//     $('.filter-row').hide();
//     $('.filter-section').hide();
//     $('.pagination-section').hide();
//     $('.action-section').hide();

//     // Add a print media query to hide checkboxes during printing
//     $('<style>@media print {.select-checkbox {display: none;}} </style>').appendTo('head');
// }

// // Function to show sections after printing
// function showSections() {
//     page.$title_area.show();
//     $('.filter-row').show();
//     $('.filter-section').show();
//     $('.pagination-section').show();
//     $('.action-section').show();

//     // Remove the print media query after printing
//     $('style').remove();
// }

    
// // Align action buttons to the right
//     action_section.css({
//         'display': 'flex',
//         'justify-content': 'flex-end', // Align items to the right
//         'margin-bottom': '10px' // Add margin below action section
//     });

//     var header_section = $('<div>').addClass('header-section').appendTo(page.body);
//     header_section.css({
//         'padding': '20px',
//         'margin-top': '30px',
//         'margin-bottom': '20px',
//         'border-bottom': '1px solid #ccc',
//         'display': 'table',
//         'width': '100%'
//     });

//     var logo_container = $('<div>').addClass('logo-container').appendTo(header_section);
//     logo_container.css({
//         'display': 'table-cell',
//         'text-align': 'right',
//         'width': '55%'
//     });

//     var logo = $('<img>').attr('src', '/files/sanha-logo.png').addClass('img').appendTo(logo_container);
//     logo.css({
//         'width': '150px',
//         'height': 'auto'
//     });

//     var slogan_container = $('<div>').addClass('slogan-container').appendTo(header_section);
//     slogan_container.css({
//         'display': 'table-cell',
//         'text-align': 'right',
//         'vertical-align': 'middle',
//         'width': '45%'
//     });

//     $('<span>').text('Eat Halal, Be Healthy.').appendTo(slogan_container);

//     // Add a loading spinner during data fetch
// var loadingSpinner = $('<div>').addClass('loading-spinner').text('Loading...').hide().appendTo(page.body);

// // Filter section styling


//     var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
//     filterSection.css({
//         'margin-bottom': '35px', // Add margin below the filter section
//         'display': 'flex',
//         'justify-content': 'space-between', // Align items with space between
//         'align-items': 'center' // Align items at the center vertically
//     });

//     // Query type selection dropdown
//     var queryTypeDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
//     queryTypeDropdown.append('<option>Select Query Type</option>');

//     var owner_table_section_container = $('<div>').appendTo(page.body);

//     var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(owner_table_section_container);
//     owner_table_section.css({
//         'margin-bottom': '20px',
//         'text-align': 'center'
//     });

//     // Date range section
//     var date_range_section_container = $('<div>').appendTo(page.body);
//     $('<hr>').appendTo(date_range_section_container);
//     var date_range_section = $('<div>').addClass('date-range-section').appendTo(date_range_section_container);
//     date_range_section.css({
//         'margin-bottom': '20px',
//         'text-align': 'center'
//     });

//     var data_section = $('<div>').addClass('data-section').appendTo(page.body);
//     data_section.css({
//         'margin-bottom': '20px',
//         'display': 'flex',
//         'align-items': 'center',
//         'flex-wrap': 'wrap'
//     });

//     var table = $('<table>').addClass('table').appendTo(data_section);
//     var thead = $('<thead>').appendTo(table);
//     var tbody = $('<tbody>').appendTo(table);
//     var tableHeaders = ['Raw Material', 'Supplier', 'Manufacturer', 'Status'];

//     // Header row with "Select All" checkbox
//     var headerRow = $('<tr>').appendTo(thead);
//     $('<th  class="checkbox-column">').append($('<input type="checkbox" id="select-all">')).appendTo(headerRow);
//     tableHeaders.forEach(function(label) {
//         $('<th>').text(label).appendTo(headerRow);
//     });
   

// var filterRow = $('<tr>').addClass('filter-row').appendTo(thead); // Add class to the filter row
// // Add empty cell for checkbox column
// $('<td>').appendTo(filterRow);
// tableHeaders.forEach(function(label) {
//     var filterInput = $('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label); // Create filter input
//     $('<td>').append(filterInput).appendTo(filterRow); // Append input to filter row cell
// });


//     var pagination_section = $('<div>').addClass('pagination-section').appendTo(page.body);
//     pagination_section.css({
//         'display': 'flex',
//         'justify-content': 'center',
//         'margin-top': '20px'
//     });

//     var prevButton = $('<button>').text('Previous').addClass('btn btn-secondary').appendTo(pagination_section);
//     var nextButton = $('<button>').text('Next').addClass('btn btn-secondary').appendTo(pagination_section);

//     prevButton.css({
//         'order': '1', // Display the "Previous" button first
//         'margin-right': 'auto' // Push the "Previous" button to the left
//     });

//     nextButton.css({
//         'order': '2' // Display the "Next" button second
//     });

//     var currentPage = 1;
//     var itemsPerPage = 50;

//     function fetchAllData(doctype, fields, filters, callback) {
//         var start = 0;
//         var limit = 500;
//         var allData = [];

//         function fetchData() {
//             frappe.call({
//                 method: 'frappe.client.get_list',
//                 args: {
//                     doctype: doctype,
//                     fields: fields,
//                     filters: filters,
//                     limit_start: start,
//                     limit_page_length: limit,
//                     order_by: 'raw_material asc'
//                 },
//                 callback: function(response) {
//                     var data = response.message;
//                     if (data.length > 0) {
//                         allData = allData.concat(data);
//                         start += limit;
//                         fetchData();
//                     } else {
//                         callback(allData);
//                     }
//                 }
//             });
//         }

//         fetchData();
//     }

//     // Populate query type dropdown
//     fetchAllData('Query', ['query_types'], [], function(queryTypes) {
//         var uniqueQueryTypes = new Set();
//         queryTypes.forEach(function(query) {
//             if (query.query_types) {
//                 query.query_types.split(',').forEach(function(type) {
//                     type = type.trim();
//                     if (type) uniqueQueryTypes.add(type);
//                 });
//             }
//         });
//         uniqueQueryTypes.forEach(function(type) {
//             $('<option>').text(type).appendTo(queryTypeDropdown);
//         });
//     });

//     // Fetch and display data for the session user
//     function fetchData(page, limit) {
//         var filters = {
//             workflow_state: ['!=', 'Draft'],
//             owner: frappe.session.user
//         };
    
//         if (queryTypeDropdown.val() !== 'Select Query Type') {
//             filters.query_types = ['like', '%' + queryTypeDropdown.val() + '%'];
//         }
    
//         var additionalFilters = {};
//         filterRow.find('input').each(function(index) {
//             var value = $(this).val();
//             if (value) {
//                 var fieldMap = {
//                     'Raw Material': 'raw_material',
//                     'Supplier': 'supplier',
//                     'Manufacturer': 'manufacturer',
//                     'Status': 'workflow_state'
//                 };
//                 var field = fieldMap[tableHeaders[index]];
//                 if (field) {
//                     additionalFilters[field] = ['like', '%' + value + '%'];
//                 }
//             }
//         });
    
//         Object.assign(filters, additionalFilters);
    
//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 fields: ['name', 'raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types'],
//                 filters: filters,
//                 limit_start: (page - 1) * limit,
//                 limit_page_length: limit,
//                 order_by: 'raw_material asc'
//             },
//             callback: function(response) {
//                 var data = response.message;
//                 tbody.empty();
    
//                 var groupedData = {};
//                 data.forEach(function(row) {
//                     var queryType = row.query_types || 'Unknown';
//                     if (!groupedData[queryType]) {
//                         groupedData[queryType] = [];
//                     }
//                     groupedData[queryType].push(row);
//                 });
    
//                 for (var queryType in groupedData) {
//                     $('<tr>').append($('<td colspan="5">').text(queryType).css('font-weight', 'bold')).appendTo(tbody); // Updated colspan to 5
//                     groupedData[queryType].forEach(function(row) {
//                         var tableRow = $('<tr>').appendTo(tbody);
//                         $('<td  class="checkbox-column">').html('<input type="checkbox" class="select-checkbox" data-name="' + row.name + '">').appendTo(tableRow); // Checkbox for each row
//                         tableHeaders.forEach(function(key) {
//                             var field = key.toLowerCase().replace(' ', '_');
//                             if (field === 'status') field = 'workflow_state';
//                             if (field === 'creation') {
//                                 var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
//                                 $('<td>').text(formattedDate).appendTo(tableRow);
//                             } else {
//                                 $('<td>').text(row[field]).appendTo(tableRow);
//                             }
//                         });
//                     });
//                 }
    
//                 updateDateRange(filters);
//             }
//         });
//     }
    

//     // Update owner table based on session user queries
//     function updateOwnerTable() {
//         owner_table_section.empty();
//         var uniqueClients = new Set();

//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 filters: {
//                     owner: frappe.session.user,
//                     client_name: ['!=', ''], // Filter out null client names
//                     client_code: ['!=', ''] // Filter out null client codes
//                 },
//                 fields: ['client_name', 'client_code']
//             },
//             callback: function(response) {
//                 var data = response.message;
//                 data.forEach(function(row) {
//                     if (!uniqueClients.has(row.client_code)) {
//                         uniqueClients.add(row.client_code);
//                         var text = row.client_name + ' (' + row.client_code + ')';
//                         var paragraph = $('<p>').text(text);
//                         owner_table_section.append(paragraph);
//                     }
//                 });
//             }
//         });
//     }

//     // Group data by header
//     function groupDataByHeader(data) {
//         var groupedData = {};
//         data.forEach(function(item) {
//             var queryType = item.query_types || 'Unknown';
//             if (!groupedData[queryType]) {
//                 groupedData[queryType] = [];
//             }
//             groupedData[queryType].push(item);
//         });
//         return groupedData;
//     }

//     // Render table with data
//     function renderTable(groupedData) {
//         tbody.empty();

//         Object.keys(groupedData).forEach(function(queryType) {
//             var headerRow = $('<tr>').appendTo(tbody);
//             $('<th>').attr('colspan', tableHeaders.length + 1).text(queryType).appendTo(headerRow);

//             groupedData[queryType].forEach(function(row) {
//                 var tableRow = $('<tr>').appendTo(tbody);
//                 var checkbox = $('<input>').attr('type', 'checkbox').addClass('select-checkbox').data('name', row.name);
                
//                 // Add a class to the checkbox for styling when printing
//                 if (isPrinting()) {
//                     checkbox.addClass('hide-on-print');
//                 }
                
//                 $('<td>').append(checkbox).appendTo(tableRow);
    
//                 tableHeaders.forEach(function(key) {
//                     var field = key.toLowerCase().replace(' ', '_');
//                     if (field === 'status') field = 'workflow_state';
//                     if (field === 'creation') {
//                         var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
//                         $('<td>').text(formattedDate).appendTo(tableRow);
//                     } else {
//                         $('<td>').text(row[field]).appendTo(tableRow);
//                     }
//                 });
//             });
//         });
//     }
    
//     // Function to check if the page is being printed
//     function isPrinting() {
//         return window.matchMedia && window.matchMedia('print').matches;
//     }

//     function updateDateRange(filters) {
//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 fields: ['creation'],
//                 filters: filters,
//                 order_by: 'creation asc'
//             },
//             callback: function(response) {
//                 var data = response.message;
//                 if (data.length > 0) {
//                     var oldestDate = moment(data[0].creation).format('DD-MM-YYYY hh:mm A');
//                     var latestDate = moment(data[data.length - 1].creation).format('DD-MM-YYYY hh:mm A');
//                     $('.date-range').html('Date Range: From: ' + oldestDate + ' To: ' + latestDate);
//                 } else {
//                     $('.date-range').html('Date Range: No Data Available');
//                 }
//             }
//         });
//     }
    
//     // Function to update date range on filter dropdown change
//     queryTypeDropdown.on('change', function() {
//         var selectedQueryType = $(this).val();
//         var filters = {
//             workflow_state: ['!=', 'Draft'],
//             owner: frappe.session.user
//         };
    
//         if (selectedQueryType !== 'Select Query Type') {
//             filters.query_types = ['like', '%' + selectedQueryType + '%'];
//         }
    
//         // Update date range based on selected filters
//         updateDateRange(filters);
//     });
    
//     // Function to update date range on checkbox selection change
//     $('.select-checkbox').on('change', function() {
//         var selectedItems = getSelectedItems();
//         var filters = {
//             workflow_state: ['!=', 'Draft'],
//             owner: frappe.session.user
//         };
    
//         if (selectedItems.length > 0) {
//             filters['name'] = ['in', selectedItems];
//         }
    
//         // Update date range based on selected filters
//         updateDateRange(filters);
//     });

// // Function to update date range on filter dropdown change
// queryTypeDropdown.on('change', function() {
//     var selectedQueryType = $(this).val();
//     var filters = {
//         workflow_state: ['!=', 'Draft'],
//         owner: frappe.session.user
//     };

//     if (selectedQueryType !== 'Select Query Type') {
//         filters.query_types = ['like', '%' + selectedQueryType + '%'];
//     }

//     // Update date range based on selected filters
//     updateDateRange(filters);
// });

// // Function to update date range on checkbox selection change
// $('.select-checkbox').on('change', function() {
//     var selectedItems = getSelectedItems();
//     var filters = {
//         workflow_state: ['!=', 'Draft'],
//         owner: frappe.session.user
//     };

//     if (selectedItems.length > 0) {
//         filters['name'] = ['in', selectedItems];
//     }

//     // Update date range based on selected filters
//     updateDateRange(filters);
// });
//     // Update date range based on filters
//     function updateDateRange(filters) {
//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 filters: filters,
//                 fields: ['creation']
//             },
//             callback: function(response) {
//                 var dates = response.message.map(item => item.creation);
//                 if (dates.length > 0) {
//                     var oldestDate = moment(Math.min.apply(null, dates)).format('DD-MM-YYYY hh:mm A');
//                     var latestDate = moment(Math.max.apply(null, dates)).format('DD-MM-YYYY hh:mm A');
//                     date_range_section.empty();
//                     $('<p>').html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>').appendTo(date_range_section);
//                 } else {
//                     date_range_section.empty();
//                     $('<p>').text('Date Range: No Data Available').appendTo(date_range_section);
//                 }
//             }
//         });
//     }
//     // Update date range for selected items
    


//     // Get selected items
//     function getSelectedItems() {
//         var selectedItems = [];
//         $('.select-checkbox:checked').each(function() {
//             selectedItems.push($(this).data('name'));
//         });
//         return selectedItems;
//     }

//     // Fetch data for selected items
//     function fetchSelectedData(selectedItems, callback) {
//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 filters: { 'name': ['in', selectedItems] },
//                 fields: ['name', 'raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types']
//             },
//             callback: function(response) {
//                 callback(response.message);
//             }
//         });
//     }

//     // Update date range for selected items
//     // Update date range for selected items
// function updateDateRangeForSelected(data) {
//     var dates = data.map(item => moment(item.creation));
//     if (dates.length > 0) {
//         var oldestDate = moment.min(dates).format('DD-MM-YYYY hh:mm A');
//         var latestDate = moment.max(dates).format('DD-MM-YYYY hh:mm A');
//         date_range_section.empty();
//         $('<p>').html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>').appendTo(date_range_section);
//     } else {
//         date_range_section.empty();
//         $('<p>').text('Date Range: No Data Available').appendTo(date_range_section);
//     }
// }

// // Get selected items
// function getSelectedItems() {
//     var selectedItems = [];
//     $('.select-checkbox:checked').each(function() {
//         selectedItems.push($(this).data('name'));
//     });
//     return selectedItems;
// }

// // Fetch data for selected items
// function fetchSelectedData(selectedItems, callback) {
//     frappe.call({
//         method: 'frappe.client.get_list',
//         args: {
//             doctype: 'Query',
//             filters: { 'name': ['in', selectedItems] },
//             fields: ['name', 'raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types']
//         },
//         callback: function(response) {
//             callback(response.message);
//         }
//     });
// }

// // Update date range on checkbox change
// function onCheckboxChange() {
//     var selectedItems = getSelectedItems();
//     if (selectedItems.length > 0) {
//         fetchSelectedData(selectedItems, function(filteredData) {
//             updateDateRangeForSelected(filteredData);
//         });
//     } else {
//         updateDateRange(defaultFilters); // Reset to default date range if no items are selected
//     }
// }

// // Attach event listener to checkboxes
// $(document).on('change', '.select-checkbox', onCheckboxChange);

// // Select all checkboxes
// $('#select-all').on('change', function() {
//     $('.select-checkbox').prop('checked', $(this).prop('checked')).trigger('change');
// });

//     fetchData(currentPage, itemsPerPage);
//     updateOwnerTable();

//     // Pagination event listeners
//     prevButton.on('click', function() {
//         if (currentPage > 1) {
//             currentPage--;
//             fetchData(currentPage, itemsPerPage);
//         }
//     });

//     nextButton.on('click', function() {
//         currentPage++;
//         fetchData(currentPage, itemsPerPage);
//     });

//     // Filter event listener
//     filterRow.find('input').on('input', function() {
//         currentPage = 1;
//         fetchData(currentPage, itemsPerPage);
//     });

//     // Query type dropdown event listener
//     queryTypeDropdown.on('change', function() {
//         currentPage = 1;
//         fetchData(currentPage, itemsPerPage);
//     });

    
//     // Footer section
//     var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
//     footer_section.css({
//         'margin-top': '25px',
//         'border-top': '1px solid #ccc',
//         'padding-top': '10px',
//         'text-align': 'left'
//     });

//     $('<hr>').appendTo(footer_section);
//     $('<p>').html('<strong>Disclaimer:</strong>This Halal Evaluation Report is issued based on the information and documentation provided at the time of evaluation. It is valid only for the specified batch/lot and for the specific materials/products mentioned. Any misuse, alteration, or use of this report beyond its intended purpose is strictly prohibited. SANHA Halal Pakistan reserves the right to revoke this evaluation in case of any non-compliance or deviation from the Halal standards.').appendTo(footer_section);
//     $('<hr>').appendTo(footer_section);

//     // Add company address
//     $('<p>').html('<strong>Sanha Halal Associates Pakistan PVT. LTD.</strong> Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama D.H.A. phase 5  <strong> Email: </strong>evaluation@sanha.org.pk - <strong>Ph: +92 21 35295263</strong>').appendTo(footer_section);
// };
//     // Footer section

// //   ############################## with out check box 
// frappe.pages['report-print-page'].on_page_load = function(wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Report Print Page',
//         single_column: true
//     });
// 	var action_section = $('<div>').addClass('action-section').appendTo(page.body);

//     // Print button
//     var printButton = $('<button>').text('Print').addClass('btn btn-primary').appendTo(action_section);
//     printButton.on('click', function() { 
//         var selectedItems = getSelectedItems();
//         if (selectedItems.length > 0) {
//             fetchSelectedData(selectedItems, function(filteredData) {
//                 var groupedData = groupDataByHeader(filteredData);
//                 updateDateRangeForSelected(filteredData);

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
   
// } else {

//     alert('No items selected');

// }
// });


//     // Align action buttons to the right
//     action_section.css({
//         'display': 'flex',
//         'justify-content': 'flex-end', // Align items to the right
//         'margin-bottom': '10px' // Add margin below action section
//     });

//     var header_section = $('<div>').addClass('header-section').appendTo(page.body);
//     header_section.css({
//         'padding': '20px',
//         'margin-top': '30px', 
//         'margin-bottom': '20px',
//         'border-bottom': '1px solid #ccc',
//         'display': 'table',
//         'width': '100%'
//     });

//     var logo_container = $('<div>').addClass('logo-container').appendTo(header_section);
//     logo_container.css({
//         'display': 'table-cell',
//         'text-align': 'right',
//         'width': '55%'
//     });
//     var logo = $('<img>').attr('src', 'http://portal.sanha.org.pk/assets/dist/img/sanha-logo.png').addClass('img').appendTo(logo_container);
//     logo.css({
//         'width': '150px',
//         'height': 'auto'
//     });

//     var slogan_container = $('<div>').addClass('slogan-container').appendTo(header_section);
//     slogan_container.css({
//         'display': 'table-cell',
//         'text-align': 'right',
//         'vertical-align': 'middle',
//         'width': '45%'
//     });
//     $('<span>').text('Eat Halal, Be Healthy.').appendTo(slogan_container);
//     var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
//     filterSection.css({
//         'margin-bottom': '35px', // Add margin below the filter section
//         'display': 'flex',
//         'justify-content': 'space-between', // Align items with space between
//         'align-items': 'center' // Align items at the center vertically
//     });
    
//     // Query type selection dropdown
//     var queryTypeDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
//     queryTypeDropdown.append('<option>Select Query Type</option>');


//     var owner_table_section_container = $('<div>').appendTo(page.body);

//     var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(owner_table_section_container);
//     owner_table_section.css({
//         'margin-bottom': '20px',
//         'text-align': 'center'
//     });
    
//     // Date range section
//     var date_range_section_container = $('<div>').appendTo(page.body);
//     $('<hr>').appendTo(date_range_section_container);
//     var date_range_section = $('<div>').addClass('date-range-section').appendTo(date_range_section_container);
//     date_range_section.css({
//         'margin-bottom': '20px',
//         'text-align': 'center'
//     });

//     var data_section = $('<div>').addClass('data-section').appendTo(page.body);
//     data_section.css({
//         'margin-bottom': '20px',
//         'display': 'flex',
//         'align-items': 'center',
//         'flex-wrap': 'wrap'
//     });

//     var table = $('<table>').addClass('table').appendTo(data_section);
//     var thead = $('<thead>').appendTo(table);
//     var tbody = $('<tbody>').appendTo(table);
//     var tableHeaders = ['Raw Material', 'Supplier', 'Manufacturer', 'Status'];

//     var headerRow = $('<tr>').appendTo(thead);
//     $('<th>').append($('<input type="checkbox" id="select-all">')).appendTo(headerRow);
//     tableHeaders.forEach(function(label) {
//         $('<th>').text(label).appendTo(headerRow);
//     });

//     var filterRow = $('<tr>').addClass('filter-row').appendTo(thead);
//     tableHeaders.forEach(function(label) {
//         $('<td>').append($('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label)).appendTo(filterRow);
//     });

//     var pagination_section = $('<div>').addClass('pagination-section').appendTo(page.body);
//     pagination_section.css({
//         'display': 'flex',
//         'justify-content': 'center',
//         'margin-top': '20px'
//     });

//     var prevButton = $('<button>').text('Previous').addClass('btn btn-secondary').appendTo(pagination_section);
//     var nextButton = $('<button>').text('Next').addClass('btn btn-secondary').appendTo(pagination_section);
    
//     prevButton.css({
//         'order': '1', // Display the "Previous" button first
//         'margin-right': 'auto' // Push the "Previous" button to the left
//     });
    
//     nextButton.css({
//         'order': '2' // Display the "Next" button second
//     });
    

//     var currentPage = 1;
//     var itemsPerPage = 50;

//     function fetchAllData(doctype, fields, filters, callback) {
//         var start = 0;
//         var limit = 500;
//         var allData = [];

//         function fetchData() {
//             frappe.call({
//                 method: 'frappe.client.get_list',
//                 args: {
//                     doctype: doctype,
//                     fields: fields,
//                     filters: filters,
//                     limit_start: start,
//                     limit_page_length: limit,
//                     order_by: 'raw_material asc'
//                 },
//                 callback: function(response) {
//                     var data = response.message;
//                     if (data.length > 0) {
//                         allData = allData.concat(data);
//                         start += limit;
//                         fetchData();
//                     } else {
//                         callback(allData);
//                     }
//                 }
//             });
//         }

//         fetchData();
//     }

//     // Populate query type dropdown
//     fetchAllData('Query', ['query_types'], [], function(queryTypes) {
//         var uniqueQueryTypes = new Set();
//         queryTypes.forEach(function(query) {
//             if (query.query_types) {
//                 query.query_types.split(',').forEach(function(type) {
//                     type = type.trim();
//                     if (type) uniqueQueryTypes.add(type);
//                 });
//             }
//         });
//         uniqueQueryTypes.forEach(function(type) {
//             $('<option>').text(type).appendTo(queryTypeDropdown);
//         });
//     });

//     // Fetch and display data for the session user
//     function fetchData(page, limit) {
//         var filters = {
//             workflow_state: ['!=', 'Draft'],
//             owner: frappe.session.user
//         };

//         if (queryTypeDropdown.val() !== 'Select Query Type') {
//             filters.query_types = ['like', '%' + queryTypeDropdown.val() + '%'];
//         }

//         var additionalFilters = {};
//         filterRow.find('input').each(function(index) {
//             var value = $(this).val();
//             if (value) {
//                 var fieldMap = {
//                     'Raw Material': 'raw_material',
//                     'Supplier': 'supplier',
//                     'Manufacturer': 'manufacturer',
//                     'Status': 'workflow_state'
//                 };
//                 var field = fieldMap[tableHeaders[index]];
//                 if (field) {
//                     additionalFilters[field] = ['like', '%' + value + '%'];
//                 }
//             }
//         });

//         Object.assign(filters, additionalFilters);

//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 fields: ['raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types'],
//                 filters: filters,
//                 limit_start: (page - 1) * limit,
//                 limit_page_length: limit,
//                 order_by: 'raw_material asc'
//             },
//             callback: function(response) {
//                 var data = response.message;
//                 tbody.empty();

//                 var groupedData = {};
//                 data.forEach(function(row) {
//                     var queryType = row.query_types || 'Unknown';
//                     if (!groupedData[queryType]) {
//                         groupedData[queryType] = [];
//                     }
//                     groupedData[queryType].push(row);
//                 });

//                 for (var queryType in groupedData) {
//                     $('<tr>').append($('<td colspan="4">').text(queryType).css('font-weight', 'bold')).appendTo(tbody);
//                     groupedData[queryType].forEach(function(row) {
//                         var tableRow = $('<tr>').appendTo(tbody);
//                         tableHeaders.forEach(function(key) {
//                             var field = key.toLowerCase().replace(' ', '_');
//                             if (field === 'status') field = 'workflow_state';
//                             if (field === 'creation') {
//                                 var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
//                                 $('<td>').text(formattedDate).appendTo(tableRow);
//                             } else {
//                                 $('<td>').text(row[field]).appendTo(tableRow);
//                             }
//                         });
//                     });
//                 }

//                 updateDateRange(filters);
//             }
//         });
//     }

//     // Update owner table based on session user queries
//     function updateOwnerTable() {
//         owner_table_section.empty();
//         var uniqueClients = new Set();
    
//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 filters: {
//                     owner: frappe.session.user,
//                     client_name: ['!=', ''], // Filter out null client names
//                     client_code: ['!=', ''] // Filter out null client codes
//                 },
//                 fields: ['client_name', 'client_code']
//             },
//             callback: function(response) {
//                 if (response.message.length > 0) {
//                     var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
//                     var tbody = $('<tbody>').appendTo(ownerTable);
    
//                     response.message.forEach(function(query) {
//                         var clientName = query.client_name;
//                         var clientCode = query.client_code;
//                         var clientIdentifier = clientName + clientCode;
//                         if (!uniqueClients.has(clientIdentifier)) {
//                             uniqueClients.add(clientIdentifier);
    
//                             // Create table for owner data with specific format
//                             var first_row = $('<tr>').appendTo(tbody);
//                             var first_row_data = $('<td>').addClass('text-center').appendTo(first_row);
//                             $('<h2>').text('Account: ' + clientName + ' (Code: ' + clientCode + ')').appendTo(first_row_data);
//                         }
//                     });
//                 } else {
//                     // If no data, show a message
//                     $('<p>').text('No client data available').appendTo(owner_table_section);
//                 }
//             }
//         });
//     }
    
//     // // Initial fetch and display data


//     function updateDateRange(filters) {
//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 fields: ['creation'],
//                 filters: filters,
//                 order_by: 'creation asc'
//             },
//             callback: function(response) {
//                 var data = response.message;
//                 if (data.length > 0) {
//                     var oldestDate = moment(data[0].creation).format('DD-MM-YYYY hh:mm A');
//                     var latestDate = moment(data[data.length - 1].creation).format('DD-MM-YYYY hh:mm A');
//                     date_range_section.empty();
//                     $('<p>').html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>').appendTo(date_range_section);
//                 } else {
//                     date_range_section.empty();
//                     $('<p>').text('Date Range: No Data Available').appendTo(date_range_section);
//                 }
//             }
//         });
//     }

//     // Initial fetch and display data
//     updateOwnerTable();
//     fetchData(currentPage, itemsPerPage);

//     filterRow.find('input').on('input', function() {
//         fetchData(currentPage, itemsPerPage);
//     });

//     queryTypeDropdown.on('change', function() {
//         fetchData(currentPage, itemsPerPage);
//     });

//     prevButton.on('click', function() {
//         if (currentPage > 1) {
//             currentPage--;
//             fetchData(currentPage, itemsPerPage);
//         }
//     });

//     nextButton.on('click', function() {
//         currentPage++;
//         fetchData(currentPage, itemsPerPage);
//     });

//     groupedData[queryType].forEach(function(row) {
//         var tableRow = $('<tr>').appendTo(tbody);
//         $('<td>').append($('<input>').attr('type', 'checkbox').addClass('select-checkbox').data('name', row.name)).appendTo(tableRow);  // Add this line for row checkboxes
//         tableHeaders.forEach(function(key) {
//             var field = key.toLowerCase().replace(' ', '_');
//             if (field === 'status') field = 'workflow_state';
//             if (field === 'creation') {
//                 var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
//                 $('<td>').text(formattedDate).appendTo(tableRow);
//             } else {
//                 $('<td>').text(row[field]).appendTo(tableRow);
//             }
//         });
//     });
//     $('#select-all').on('change', function() {
//         var isChecked = $(this).is(':checked');
//         $('.select-checkbox').prop('checked', isChecked);
//     });
//     function getSelectedItems() {
//         var selectedItems = [];
//         $('.select-checkbox:checked').each(function() {
//             selectedItems.push($(this).data('name'));
//         });
//         return selectedItems;
//     }
//     function fetchSelectedData(selectedItems, callback) {
//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 filters: { 'name': ['in', selectedItems] },
//                 fields: ['name', 'raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types']
//             },
//             callback: function(response) {
//                 callback(response.message);
//             }
//         });
//     }
//     function groupDataByHeader(data) {
//         var groupedData = {};
//         data.forEach(function(item) {
//             var queryType = item.query_types || 'Unknown';
//             if (!groupedData[queryType]) {
//                 groupedData[queryType] = [];
//             }
//             groupedData[queryType].push(item);
//         });
//         return groupedData;
//     }
//     function updateDateRangeForSelected(data) {
//         var dates = data.map(item => item.creation);
//         if (dates.length > 0) {
//             var oldestDate = moment(Math.min.apply(null, dates)).format('DD-MM-YYYY hh:mm A');
//             var latestDate = moment(Math.max.apply(null, dates)).format('DD-MM-YYYY hh:mm A');
//             date_range_section.empty();
//             $('<p>').html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>').appendTo(date_range_section);
//         } else {
//             date_range_section.empty();
//             $('<p>').text('Date Range: No Data Available').appendTo(date_range_section);
//         }
//     }
    
    
        
    
    
//     // Footer section
//     var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
//     footer_section.css({
//         'margin-top': '25px',
//         'border-top': '1px solid #ccc',
//         'padding-top': '10px',
//         'text-align': 'left'
//     });

//     $('<hr>').appendTo(footer_section);
//     $('<p>').html('<strong>Disclaimer:</strong>This Halal Evaluation Report is issued based on the information and documentation provided at the time of evaluation. It is valid only for the specified batch/lot and for the specific materials/products mentioned. Any misuse, alteration, or use of this report beyond its intended purpose is strictly prohibited. SANHA Halal Pakistan reserves the right to revoke this evaluation in case of any non-compliance or deviation from the Halal standards.').appendTo(footer_section);
//     $('<hr>').appendTo(footer_section);

//     // Add company address
//     $('<p>').html('<strong>Sanha Halal Associates Pakistan PVT. LTD.</strong> Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama D.H.A. phase 5  <strong> Email: </strong>evaluation@sanha.org.pk - <strong>Ph: +92 21 35295263</strong>').appendTo(footer_section);
// };







// #######################################

// frappe.pages['report-print-page'].on_page_load = function(wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Report Print Page',
//         single_column: true
//     });
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

//     var header_section = $('<div>').addClass('header-section').appendTo(page.body);
//     header_section.css({
//         'padding': '20px',
//         'margin-top': '30px', 
//         'margin-bottom': '20px',
//         'border-bottom': '1px solid #ccc',
//         'display': 'table',
//         'width': '100%'
//     });

//     var logo_container = $('<div>').addClass('logo-container').appendTo(header_section);
//     logo_container.css({
//         'display': 'table-cell',
//         'text-align': 'right',
//         'width': '55%'
//     });
//     var logo = $('<img>').attr('src', 'http://portal.sanha.org.pk/assets/dist/img/sanha-logo.png').addClass('img').appendTo(logo_container);
//     logo.css({
//         'width': '150px',
//         'height': 'auto'
//     });

//     var slogan_container = $('<div>').addClass('slogan-container').appendTo(header_section);
//     slogan_container.css({
//         'display': 'table-cell',
//         'text-align': 'right',
//         'vertical-align': 'middle',
//         'width': '45%'
//     });
//     $('<span>').text('Eat Halal, Be Healthy.').appendTo(slogan_container);
//     var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
//     filterSection.css({
//         'margin-bottom': '35px', // Add margin below the filter section
//         'display': 'flex',
//         'justify-content': 'space-between', // Align items with space between
//         'align-items': 'center' // Align items at the center vertically
//     });
    
//     // Query type selection dropdown
//     var queryTypeDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
//     queryTypeDropdown.append('<option>Select Query Type</option>');

//     // Define main elements for sections

//     var owner_table_section_container = $('<div>').appendTo(page.body);

//     var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(owner_table_section_container);
//     owner_table_section.css({
//         'margin-bottom': '20px',
//         'text-align': 'center'
//     });
    
//     // Date range section
//     var date_range_section_container = $('<div>').appendTo(page.body);
//     $('<hr>').appendTo(date_range_section_container);
//     var date_range_section = $('<div>').addClass('date-range-section').appendTo(date_range_section_container);
//     date_range_section.css({
//         'margin-bottom': '20px',
//         'text-align': 'center'
//     });

//     var data_section = $('<div>').addClass('data-section').appendTo(page.body);
//     data_section.css({
//         'margin-bottom': '20px',
//         'display': 'flex',
//         'align-items': 'center',
//         'flex-wrap': 'wrap'
//     });

//     var table = $('<table>').addClass('table').appendTo(data_section);
//     var thead = $('<thead>').appendTo(table);
//     var tbody = $('<tbody>').appendTo(table);
//     var tableHeaders = ['Raw Material', 'Supplier', 'Manufacturer', 'Status'];

//     var headerRow = $('<tr>').appendTo(thead);
//     tableHeaders.forEach(function(label) {
//         $('<th>').text(label).appendTo(headerRow);
//     });

//     var filterRow = $('<tr>').addClass('filter-row').appendTo(thead);
//     tableHeaders.forEach(function(label) {
//         $('<td>').append($('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label)).appendTo(filterRow);
//     });

//     var pagination_section = $('<div>').addClass('pagination-section').appendTo(page.body);
//     pagination_section.css({
//         'display': 'flex',
//         'justify-content': 'center',
//         'margin-top': '20px'
//     });

//     var prevButton = $('<button>').text('Previous').addClass('btn btn-secondary').appendTo(pagination_section);
//     var nextButton = $('<button>').text('Next').addClass('btn btn-secondary').appendTo(pagination_section);
    
//     prevButton.css({
//         'order': '1', // Display the "Previous" button first
//         'margin-right': 'auto' // Push the "Previous" button to the left
//     });
    
//     nextButton.css({
//         'order': '2' // Display the "Next" button second
//     });
    

//     var currentPage = 1;
//     var itemsPerPage = 50;

//     function fetchAllData(doctype, fields, filters, callback) {
//         var start = 0;
//         var limit = 500;
//         var allData = [];

//         function fetchData() {
//             frappe.call({
//                 method: 'frappe.client.get_list',
//                 args: {
//                     doctype: doctype,
//                     fields: fields,
//                     filters: filters,
//                     limit_start: start,
//                     limit_page_length: limit,
//                     order_by: 'raw_material asc'
//                 },
//                 callback: function(response) {
//                     var data = response.message;
//                     if (data.length > 0) {
//                         allData = allData.concat(data);
//                         start += limit;
//                         fetchData();
//                     } else {
//                         callback(allData);
//                     }
//                 }
//             });
//         }

//         fetchData();
//     }

//     // Populate query type dropdown
//     fetchAllData('Query', ['query_types'], [], function(queryTypes) {
//         var uniqueQueryTypes = new Set();
//         queryTypes.forEach(function(query) {
//             if (query.query_types) {
//                 query.query_types.split(',').forEach(function(type) {
//                     type = type.trim();
//                     if (type) uniqueQueryTypes.add(type);
//                 });
//             }
//         });
//         uniqueQueryTypes.forEach(function(type) {
//             $('<option>').text(type).appendTo(queryTypeDropdown);
//         });
//     });

//     // Fetch and display data for the session user
//     function fetchData(page, limit) {
//         var filters = {
//             workflow_state: ['!=', 'Draft'],
//             owner: frappe.session.user
//         };

//         if (queryTypeDropdown.val() !== 'Select Query Type') {
//             filters.query_types = ['like', '%' + queryTypeDropdown.val() + '%'];
//         }

//         var additionalFilters = {};
//         filterRow.find('input').each(function(index) {
//             var value = $(this).val();
//             if (value) {
//                 var fieldMap = {
//                     'Raw Material': 'raw_material',
//                     'Supplier': 'supplier',
//                     'Manufacturer': 'manufacturer',
//                     'Status': 'workflow_state'
//                 };
//                 var field = fieldMap[tableHeaders[index]];
//                 if (field) {
//                     additionalFilters[field] = ['like', '%' + value + '%'];
//                 }
//             }
//         });

//         Object.assign(filters, additionalFilters);

//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 fields: ['raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types'],
//                 filters: filters,
//                 limit_start: (page - 1) * limit,
//                 limit_page_length: limit,
//                 order_by: 'raw_material asc'
//             },
//             callback: function(response) {
//                 var data = response.message;
//                 tbody.empty();

//                 var groupedData = {};
//                 data.forEach(function(row) {
//                     var queryType = row.query_types || 'Unknown';
//                     if (!groupedData[queryType]) {
//                         groupedData[queryType] = [];
//                     }
//                     groupedData[queryType].push(row);
//                 });

//                 for (var queryType in groupedData) {
//                     $('<tr>').append($('<td colspan="4">').text(queryType).css('font-weight', 'bold')).appendTo(tbody);
//                     groupedData[queryType].forEach(function(row) {
//                         var tableRow = $('<tr>').appendTo(tbody);
//                         tableHeaders.forEach(function(key) {
//                             var field = key.toLowerCase().replace(' ', '_');
//                             if (field === 'status') field = 'workflow_state';
//                             if (field === 'creation') {
//                                 var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
//                                 $('<td>').text(formattedDate).appendTo(tableRow);
//                             } else {
//                                 $('<td>').text(row[field]).appendTo(tableRow);
//                             }
//                         });
//                     });
//                 }

//                 updateDateRange(filters);
//             }
//         });
//     }

//     // Update owner table based on session user queries
//     function updateOwnerTable() {
//         owner_table_section.empty();
//         var uniqueClients = new Set();
    
//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 filters: {
//                     owner: frappe.session.user,
//                     client_name: ['!=', ''], // Filter out null client names
//                     client_code: ['!=', ''] // Filter out null client codes
//                 },
//                 fields: ['client_name', 'client_code']
//             },
//             callback: function(response) {
//                 if (response.message.length > 0) {
//                     var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
//                     var tbody = $('<tbody>').appendTo(ownerTable);
    
//                     response.message.forEach(function(query) {
//                         var clientName = query.client_name;
//                         var clientCode = query.client_code;
//                         var clientIdentifier = clientName + clientCode;
//                         if (!uniqueClients.has(clientIdentifier)) {
//                             uniqueClients.add(clientIdentifier);
    
//                             // Create table for owner data with specific format
//                             var first_row = $('<tr>').appendTo(tbody);
//                             var first_row_data = $('<td>').addClass('text-center').appendTo(first_row);
//                             $('<h2>').text('Account: ' + clientName + ' (Code: ' + clientCode + ')').appendTo(first_row_data);
//                         }
//                     });
//                 } else {
//                     // If no data, show a message
//                     $('<p>').text('No client data available').appendTo(owner_table_section);
//                 }
//             }
//         });
//     }
    
//     // // Initial fetch and display data


//     function updateDateRange(filters) {
//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 fields: ['creation'],
//                 filters: filters,
//                 order_by: 'creation asc'
//             },
//             callback: function(response) {
//                 var data = response.message;
//                 if (data.length > 0) {
//                     var oldestDate = moment(data[0].creation).format('DD-MM-YYYY hh:mm A');
//                     var latestDate = moment(data[data.length - 1].creation).format('DD-MM-YYYY hh:mm A');
//                     date_range_section.empty();
//                     $('<p>').html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>').appendTo(date_range_section);
//                 } else {
//                     date_range_section.empty();
//                     $('<p>').text('Date Range: No Data Available').appendTo(date_range_section);
//                 }
//             }
//         });
//     }

//     // Initial fetch and display data
//     updateOwnerTable();
//     fetchData(currentPage, itemsPerPage);

//     filterRow.find('input').on('input', function() {
//         fetchData(currentPage, itemsPerPage);
//     });

//     queryTypeDropdown.on('change', function() {
//         fetchData(currentPage, itemsPerPage);
//     });

//     prevButton.on('click', function() {
//         if (currentPage > 1) {
//             currentPage--;
//             fetchData(currentPage, itemsPerPage);
//         }
//     });

//     nextButton.on('click', function() {
//         currentPage++;
//         fetchData(currentPage, itemsPerPage);
//     });

//     // #Footer section
//     var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
//     footer_section.css({
//         'margin-top': '25px',
//         'border-top': '1px solid #ccc',
//         'padding-top': '10px',
//         'text-align': 'left'
//     });

//     $('<hr>').appendTo(footer_section);
//     $('<p>').html('<strong>Disclaimer:</strong>This Halal Evaluation Report is issued based on the information and documentation provided at the time of evaluation. It is valid only for the specified batch/lot and for the specific materials/products mentioned. Any misuse, alteration, or use of this report beyond its intended purpose is strictly prohibited. SANHA Halal Pakistan reserves the right to revoke this evaluation in case of any non-compliance or deviation from the Halal standards.').appendTo(footer_section);
//     $('<hr>').appendTo(footer_section);

//     // Add company address
//     $('<p>').html('<strong>Sanha Halal Associates Pakistan PVT. LTD.</strong> Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama D.H.A. phase 5  <strong> Email: </strong>evaluation@sanha.org.pk - <strong>Ph: +92 21 35295263</strong>').appendTo(footer_section);
// };
// ##################
// frappe.pages['report-print-page'].on_page_load = function(wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Report Print Page',
//         single_column: true
//     });

//     var action_section = $('<div>').addClass('action-section').appendTo(page.body);

//     // Print button
//     var printButton = $('<button>').text('Print').addClass('btn btn-primary').appendTo(action_section);
//     printButton.on('click', function() {
//         // Save current visibility state of elements
//         var titleVisible = page.$title_area.is(':visible');
//         var filterRowVisible = $('.filter-row').is(':visible');
//         var filterSectionVisible = $('.filter-section').is(':visible');
//         var paginationSectionVisible = $('.pagination-section').is(':visible');
//         var actionSectionVisible = $('.action-section').is(':visible');

//         // Hide elements before printing
//         page.$title_area.hide();
//         $('.filter-row').hide();
//         $('.filter-section').hide();
//         $('.pagination-section').hide();
//         $('.action-section').hide();

//         // Print the entire page
//         window.print();

//         // Restore visibility after printing
//         if (titleVisible) page.$title_area.show();
//         if (filterRowVisible) $('.filter-row').show();
//         if (filterSectionVisible) $('.filter-section').show();
//         if (paginationSectionVisible) $('.pagination-section').show();
//         if (actionSectionVisible) $('.action-section').show();
//     });

//     // Align action buttons to the right
//     action_section.css({
//         'display': 'flex',
//         'justify-content': 'flex-end',
//         'margin-bottom': '10px'
//     });

//     // Header Section
//     var header_section = $('<div>').addClass('header-section').appendTo(page.body);
//     header_section.css({
//         'padding': '20px',
//         'margin-top': '30px',
//         'margin-bottom': '20px',
//         'border-bottom': '1px solid #ccc',
//         'display': 'table',
//         'width': '100%'
//     });

//     // Logo Container
//     var logo_container = $('<div>').addClass('logo-container').appendTo(header_section);
//     logo_container.css({
//         'display': 'table-cell',
//         'text-align': 'right',
//         'width': '55%'
//     });
//     var logo = $('<img>').attr('src', 'http://portal.sanha.org.pk/assets/dist/img/sanha-logo.png').addClass('img').appendTo(logo_container);
//     logo.css({
//         'width': '150px',
//         'height': 'auto'
//     });

//     // Slogan Container
//     var slogan_container = $('<div>').addClass('slogan-container').appendTo(header_section);
//     slogan_container.css({
//         'display': 'table-cell',
//         'text-align': 'right',
//         'vertical-align': 'middle',
//         'width': '45%'
//     });
//     $('<span>').text('Eat Halal, Be Healthy.').appendTo(slogan_container);

//     // Filter Section
//     var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
//     filterSection.css({
//         'margin-bottom': '35px',
//         'display': 'flex',
//         'justify-content': 'space-between',
//         'align-items': 'center'
//     });

//     // Query Type Dropdown
//     var queryTypeDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
//     queryTypeDropdown.append('<option>Select Query Type</option>');

//     // Define Main Elements for Sections
//     var owner_table_section_container = $('<div>').appendTo(page.body);
//     var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(owner_table_section_container);
//     owner_table_section.css({
//         'margin-bottom': '20px',
//         'text-align': 'center'
//     });

//     // Date Range Section
//     var date_range_section_container = $('<div>').appendTo(page.body);
//     $('<hr>').appendTo(date_range_section_container);
//     var date_range_section = $('<div>').addClass('date-range-section').appendTo(date_range_section_container);
//     date_range_section.css({
//         'margin-bottom': '20px',
//         'text-align': 'center'
//     });

//     // Data Section
//     var data_section = $('<div>').addClass('data-section').appendTo(page.body);
//     data_section.css({
//         'margin-bottom': '20px',
//         'display': 'flex',
//         'align-items': 'center',
//         'flex-wrap': 'wrap'
//     });

//     var table = $('<table>').addClass('table').appendTo(data_section);
//     var thead = $('<thead>').appendTo(table);
//     var tbody = $('<tbody>').appendTo(table);
//     var tableHeaders = ['Raw Material', 'Supplier', 'Manufacturer', 'Status'];

//     var headerRow = $('<tr>').appendTo(thead);
//     tableHeaders.forEach(function(label) {
//         $('<th>').text(label).appendTo(headerRow);
//     });

//     var filterRow = $('<tr>').addClass('filter-row').appendTo(thead);
//     tableHeaders.forEach(function(label) {
//         $('<td>').append($('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label)).appendTo(filterRow);
//     });

//     // Pagination Section
//     var pagination_section = $('<div>').addClass('pagination-section').appendTo(page.body);
//     pagination_section.css({
//         'display': 'flex',
//         'justify-content': 'center',
//         'margin-top': '20px'
//     });

//     var prevButton = $('<button>').text('Previous').addClass('btn btn-secondary').appendTo(pagination_section);
//     var nextButton = $('<button>').text('Next').addClass('btn btn-secondary').appendTo(pagination_section);

//     prevButton.css({
//         'order': '1',
//         'margin-right': 'auto'
//     });

//     nextButton.css({
//         'order': '2'
//     });

//     var currentPage = 1;
//     var itemsPerPage = 50;

//     // Fetch All Data Function
//     function fetchAllData(doctype, fields, filters, callback) {
//         var start = 0;
//         var limit = 500;
//         var allData = [];

//         function fetchData() {
//             frappe.call({
//                 method: 'frappe.client.get_list',
//                 args: {
//                     doctype: doctype,
//                     fields: fields,
//                     filters: filters,
//                     limit_start: start,
//                     limit_page_length: limit,
//                     order_by: 'raw_material asc'
//                 },
//                 callback: function(response) {
//                     var data = response.message;
//                     if (data.length > 0) {
//                         allData = allData.concat(data);
//                         start += limit;
//                         fetchData();
//                     } else {
//                         callback(allData);
//                     }
//                 }
//             });
//         }

//         fetchData();
//     }

//     // Populate Query Type Dropdown
//     fetchAllData('Query', ['query_types'], [], function(queryTypes) {
//         var uniqueQueryTypes = new Set();
//         queryTypes.forEach(function(query) {
//             if (query.query_types) {
//                 query.query_types.split(',').forEach(function(type) {
//                     type = type.trim();
//                     if (type) uniqueQueryTypes.add(type);
//                 });
//             }
//         });
//         uniqueQueryTypes.forEach(function(type) {
//             $('<option>').text(type).appendTo(queryTypeDropdown);
//         });
//     });

//     // Fetch and Display Data for Session User
//     function fetchData(page, limit) {
//         var filters = {
//             workflow_state: ['!=', 'Draft'],
//             owner: frappe.session.user
//         };

//         if (queryTypeDropdown.val() !== 'Select Query Type') {
//             filters.query_types = ['like', '%' + queryTypeDropdown.val() + '%'];
//         }

//         var additionalFilters = {};
//         filterRow.find('input').each(function(index) {
//             var value = $(this).val();
//             if (value) {
//                 var fieldMap = {
//                     'Raw Material': 'raw_material',
//                     'Supplier': 'supplier',
//                     'Manufacturer': 'manufacturer',
//                     'Status': 'workflow_state'
//                 };
//                 var field = fieldMap[tableHeaders[index]];
//                 if (field) {
//                     additionalFilters[field] = ['like', '%' + value + '%'];
//                 }
//             }
//         });

//         Object.assign(filters, additionalFilters);

//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 fields: ['raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types'],
//                 filters: filters,
//                 limit_start: (page - 1) * limit,
//                 limit_page_length: limit,
//                 order_by: 'raw_material asc'
//             },
//             callback: function(response) {
//                 var data = response.message;
//                 tbody.empty();

//                 var groupedData = {};
//                 data.forEach(function(row) {
//                     var queryType = row.query_types || 'Unknown';
//                     if (!groupedData[queryType]) {
//                         groupedData[queryType] = [];
//                     }
//                     groupedData[queryType].push(row);
//                 });

//                 for (var queryType in groupedData) {
//                     $('<tr>').append($('<td colspan="4">').text(queryType).css('font-weight', 'bold')).appendTo(tbody);
//                     groupedData[queryType].forEach(function(row) {
//                         var tableRow = $('<tr>').appendTo(tbody);
//                         tableHeaders.forEach(function(key) {
//                             var field = key.toLowerCase().replace(' ', '_');
//                             if (field === 'status') field = 'workflow_state';
//                             if (field === 'creation') {
//                                 var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
//                                 $('<td>').text(formattedDate).appendTo(tableRow);
//                             } else {
//                                 $('<td>').text(row[field]).appendTo(tableRow);
//                             }
//                         });
//                     });
//                 }

//                 updateDateRange(filters);
//             }
//         });
//     }

//     // Update Owner Table
//     function updateOwnerTable() {
//         owner_table_section.empty();
//         var uniqueClients = new Set();

//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 filters: {
//                     owner: frappe.session.user,
//                     client_name: ['!=', ''],
//                     client_code: ['!=', '']
//                 },
//                 fields: ['client_name', 'client_code']
//             },
//             callback: function(response) {
//                 if (response.message.length > 0) {
//                     var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
//                     var tbody = $('<tbody>').appendTo(ownerTable);

//                     response.message.forEach(function(query) {
//                         var clientName = query.client_name;
//                         var clientCode = query.client_code;
//                         var clientIdentifier = clientName + clientCode;
//                         if (!uniqueClients.has(clientIdentifier)) {
//                             uniqueClients.add(clientIdentifier);
//                             var first_row = $('<tr>').appendTo(tbody);
//                             var first_row_data = $('<td>').addClass('text-center').appendTo(first_row);
//                             $('<h2>').text('Account: ' + clientName + ' (Code: ' + clientCode + ')').appendTo(first_row_data);
//                         }
//                     });
//                 } else {
//                     $('<p>').text('No client data available').appendTo(owner_table_section);
//                 }
//             }
//         });
//     }

//     // Update Date Range
//     function updateDateRange(filters) {
//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 fields: ['creation'],
//                 filters: filters,
//                 order_by: 'creation asc'
//             },
//             callback: function(response) {
//                 var data = response.message;
//                 if (data.length > 0) {
//                     var oldestDate = moment(data[0].creation).format('DD-MM-YYYY hh:mm A');
//                     var latestDate = moment(data[data.length - 1].creation).format('DD-MM-YYYY hh:mm A');
//                     date_range_section.empty();
//                     $('<p>').html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>').appendTo(date_range_section);
//                 } else {
//                     date_range_section.empty();
//                     $('<p>').text('Date Range: No Data Available').appendTo(date_range_section);
//                 }
//             }
//         });
//     }

//     // Initial Fetch and Display Data
//     updateOwnerTable();
//     fetchData(currentPage, itemsPerPage);

//     filterRow.find('input').on('input', function() {
//         fetchData(currentPage, itemsPerPage);
//     });

//     queryTypeDropdown.on('change', function() {
//         fetchData(currentPage, itemsPerPage);
//     });

//     prevButton.on('click', function() {
//         if (currentPage > 1) {
//             currentPage--;
//             fetchData(currentPage, itemsPerPage);
//         }
//     });

//     nextButton.on('click', function() {
//         currentPage++;
//         fetchData(currentPage, itemsPerPage);
//     });

//     // Footer Section
//     var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
//     footer_section.css({
//         'margin-top': '25px',
//         'border-top': '1px solid #ccc',
//         'padding-top': '10px',
//         'text-align': 'left'
//     });

//     $('<hr>').appendTo(footer_section);
//     $('<p>').html('<strong>Disclaimer:</strong>This Halal Evaluation Report is issued based on the information and documentation provided at the time of evaluation. It is valid only for the specified batch/lot and for the specific materials/products mentioned. Any misuse, alteration, or use of this report beyond its intended purpose is strictly prohibited. SANHA Halal Pakistan reserves the right to revoke this evaluation in case of any non-compliance or deviation from the Halal standards.').appendTo(footer_section);
//     $('<hr>').appendTo(footer_section);
//     $('<p>').html('<strong>Sanha Halal Associates Pakistan PVT. LTD.</strong> Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama D.H.A. phase 5  <strong> Email: </strong>evaluation@sanha.org.pk - <strong>Ph: +92 21 35295263</strong>').appendTo(footer_section);
// };
// ##################### some missing 
// frappe.pages['report-print-page'].on_page_load = function(wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Report Print Page',
//         single_column: true
//     });

//     var action_section = $('<div>').addClass('action-section').appendTo(page.body);

//     // Print button
//     var printButton = $('<button>').text('Print').addClass('btn btn-primary').appendTo(action_section);
//     printButton.on('click', function() {
//         // Save current visibility state of elements
//         var titleVisible = page.$title_area.is(':visible');
//         var filterRowVisible = $('.filter-row').is(':visible');
//         var filterSectionVisible = $('.filter-section').is(':visible');
//         var paginationSectionVisible = $('.pagination-section').is(':visible');
//         var actionSectionVisible = $('.action-section').is(':visible');

//         // Hide elements before printing
//         page.$title_area.hide();
//         $('.filter-row').hide();
//         $('.filter-section').hide();
//         $('.pagination-section').hide();
//         $('.action-section').hide();

//         // Print the entire page
//         window.print();

//         // Restore visibility after printing
//         if (titleVisible) page.$title_area.show();
//         if (filterRowVisible) $('.filter-row').show();
//         if (filterSectionVisible) $('.filter-section').show();
//         if (paginationSectionVisible) $('.pagination-section').show();
//         if (actionSectionVisible) $('.action-section').show();
//     });

//     // Align action buttons to the right
//     action_section.css({
//         'display': 'flex',
//         'justify-content': 'flex-end',
//         'margin-bottom': '10px'
//     });

//     // Header Section
//     var header_section = $('<div>').addClass('header-section').appendTo(page.body);
//     header_section.css({
//         'padding': '20px',
//         'margin-top': '30px',
//         'margin-bottom': '20px',
//         'border-bottom': '1px solid #ccc',
//         'display': 'table',
//         'width': '100%'
//     });

//     // Logo Container
//     var logo_container = $('<div>').addClass('logo-container').appendTo(header_section);
//     logo_container.css({
//         'display': 'table-cell',
//         'text-align': 'right',
//         'width': '55%'
//     });
//     var logo = $('<img>').attr('src', 'http://portal.sanha.org.pk/assets/dist/img/sanha-logo.png').addClass('img').appendTo(logo_container);
//     logo.css({
//         'width': '150px',
//         'height': 'auto'
//     });

//     // Slogan Container
//     var slogan_container = $('<div>').addClass('slogan-container').appendTo(header_section);
//     slogan_container.css({
//         'display': 'table-cell',
//         'text-align': 'right',
//         'vertical-align': 'middle',
//         'width': '45%'
//     });
//     $('<span>').text('Eat Halal, Be Healthy.').appendTo(slogan_container);

//     // Filter Section
//     var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
//     filterSection.css({
//         'margin-bottom': '35px',
//         'display': 'flex',
//         'justify-content': 'space-between',
//         'align-items': 'center'
//     });

//     // Query type selection dropdown
//     var queryTypeDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
//     queryTypeDropdown.append('<option>Select Query Type</option>');

//     // Owner Table Section
//     var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(page.body);
//     owner_table_section.css({
//         'margin-bottom': '20px',
//         'text-align': 'center'
//     });

//     // Date range section
//     var date_range_section = $('<div>').addClass('date-range-section').appendTo(page.body);
//     date_range_section.css({
//         'margin-bottom': '20px',
//         'text-align': 'center'
//     });

//     // Data Section
//     var data_section = $('<div>').addClass('data-section').appendTo(page.body);
//     data_section.css({
//         'margin-bottom': '20px',
//         'display': 'flex',
//         'align-items': 'center',
//         'flex-wrap': 'wrap'
//     });

//     var table = $('<table>').addClass('table').appendTo(data_section);
//     var thead = $('<thead>').appendTo(table);
//     var tbody = $('<tbody>').appendTo(table);
//     var tableHeaders = ['S.No', 'Raw Material', 'Supplier', 'Manufacturer', 'Status', 'Select'];

//     var headerRow = $('<tr>').appendTo(thead);
//     tableHeaders.forEach(function(label) {
//         $('<th>').text(label).appendTo(headerRow);
//     });

//     var filterRow = $('<tr>').addClass('filter-row').appendTo(thead);
//     tableHeaders.forEach(function(label) {
//         $('<td>').append($('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label)).appendTo(filterRow);
//     });

//     var pagination_section = $('<div>').addClass('pagination-section').appendTo(page.body);
//     pagination_section.css({
//         'display': 'flex',
//         'justify-content': 'center',
//         'margin-top': '20px'
//     });

//     var prevButton = $('<button>').text('Previous').addClass('btn btn-secondary').appendTo(pagination_section);
//     var nextButton = $('<button>').text('Next').addClass('btn btn-secondary').appendTo(pagination_section);

//     prevButton.css({
//         'order': '1',
//         'margin-right': 'auto'
//     });

//     nextButton.css({
//         'order': '2'
//     });

//     var currentPage = 1;
//     var itemsPerPage = 50;

//     // Function to fetch and display data
//     function fetchData(page, limit) {
//         var filters = {
//             workflow_state: ['!=', 'Draft'],
//             owner: frappe.session.user
//         };

//         if (queryTypeDropdown.val() !== 'Select Query Type') {
//             filters.query_types = ['like', '%' + queryTypeDropdown.val() + '%'];
//         }

//         var additionalFilters = {};
//         filterRow.find('input').each(function(index) {
//             var value = $(this).val();
//             if (value) {
//                 var fieldMap = {
//                     'Raw Material': 'raw_material',
//                     'Supplier': 'supplier',
//                     'Manufacturer': 'manufacturer',
//                     'Status': 'workflow_state'
//                 };
//                 var field = fieldMap[tableHeaders[index + 1]]; // Offset by 1 for serial number
//                 if (field) {
//                     additionalFilters[field] = ['like', '%' + value + '%'];
//                 }
//             }
//         });

//         Object.assign(filters, additionalFilters);

//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 fields: ['raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types'],
//                 filters: filters,
//                 limit_start: (page - 1) * limit,
//                 limit_page_length: limit,
//                 order_by: 'raw_material asc'
//             },
//             callback: function(response) {
//                 var data = response.message;
//                 tbody.empty();

//                 // Add Serial Numbers and Populate Table
//                 data.forEach(function(row, index) {
//                     var tableRow = $('<tr>').appendTo(tbody);
//                     $('<td>').text((currentPage - 1) * itemsPerPage + index + 1).appendTo(tableRow); // Serial Number
//                     tableHeaders.slice(1).forEach(function(key) { // Slice to exclude 'S.No'
//                         var field = key.toLowerCase().replace(' ', '_');
//                         if (field === 'status') field = 'workflow_state';
//                         if (field === 'creation') {
//                             var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
//                             $('<td>').text(formattedDate).appendTo(tableRow);
//                         } else {
//                             $('<td>').text(row[field]).appendTo(tableRow);
//                         }
//                     });

//                     // Checkbox for selection
//                     var selectTd = $('<td>').appendTo(tableRow);
//                     var checkbox = $('<input>').attr('type', 'checkbox').addClass('item-select');
//                     selectTd.append(checkbox);

//                     // Event listener for checkbox change
//                     checkbox.on('change', function() {
//                         updateDateRange();
//                     });
//                 });

//                 updateTotalCount(data.length);
//                 updateDateRange();
//             }
//         });
//     }

//     // Update Total Count Function
//     function updateTotalCount(itemCount) {
//         var totalCountSection = $('<div>').addClass('total-count-section').appendTo(page.body);
//         totalCountSection.empty();
//         $('<strong>').text('Total Items: ' + itemCount).appendTo(totalCountSection);
        
//         var selectedCount = $('.item-select:checked').length;
//         $('<strong>').text('Selected Items: ' + selectedCount).appendTo(totalCountSection);
//     }

//     // Update Owner Table
//     function updateOwnerTable() {
//         owner_table_section.empty();
//         var uniqueClients = new Set();

//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 filters: {
//                     owner: frappe.session.user,
//                     client_name: ['!=', ''],
//                     client_code: ['!=', '']
//                 },
//                 fields: ['client_name', 'client_code']
//             },
//             callback: function(response) {
//                 if (response.message.length > 0) {
//                     var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
//                     var tbody = $('<tbody>').appendTo(ownerTable);

//                     response.message.forEach(function(query) {
//                         var clientName = query.client_name.toUpperCase(); // Capitalize client name
//                         var clientCode = query.client_code.toUpperCase(); // Capitalize client code
//                         var clientIdentifier = clientName + clientCode;
//                         if (!uniqueClients.has(clientIdentifier)) {
//                             uniqueClients.add(clientIdentifier);

//                             // Create table for owner data with specific format
//                             var first_row = $('<tr>').appendTo(tbody);
//                             var first_row_data = $('<td>').addClass('text-center').appendTo(first_row);
//                             $('<h2>').css({'font-weight': 'bold'}).text('Account: ' + clientName + ' (Code: ' + clientCode + ')').appendTo(first_row_data);
//                         }
//                     });
//                 } else {
//                     $('<p>').text('No client data available').appendTo(owner_table_section);
//                 }
//             }
//         });
//     }

//     // Update Date Range Function
//     function updateDateRange() {
//         var selectedItems = $('.item-select:checked');
//         var filters = { owner: frappe.session.user };

//         if (selectedItems.length > 0) {
//             var selectedDates = [];
//             selectedItems.each(function() {
//                 var rowIndex = $(this).closest('tr').index();
//                 var creationDate = moment(tbody.find('tr').eq(rowIndex).find('td').eq(5).text(), 'DD-MM-YYYY hh:mm A');
//                 selectedDates.push(creationDate);
//             });

//             if (selectedDates.length > 0) {
//                 var oldestDate = moment.min(selectedDates).format('DD-MM-YYYY hh:mm A');
//                 var latestDate = moment().format('DD-MM-YYYY hh:mm A');
//                 date_range_section.html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>');
//             }
//         } else {
//             // When no items are selected
//             frappe.call({
//                 method: 'frappe.client.get_list',
//                 args: {
//                     doctype: 'Query',
//                     fields: ['creation'],
//                     filters: filters,
//                     order_by: 'creation asc'
//                 },
//                 callback: function(response) {
//                     var data = response.message;
//                     if (data.length > 0) {
//                         var oldestDate = moment(data[0].creation).format('DD-MM-YYYY hh:mm A');
//                         var latestDate = moment().format('DD-MM-YYYY hh:mm A');
//                         date_range_section.html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>');
//                     } else {
//                         date_range_section.html('Date Range: No Data Available');
//                     }
//                 }
//             });
//         }
//     }

//     // Initial fetch and display data
//     updateOwnerTable();
//     fetchData(currentPage, itemsPerPage);

//     filterRow.find('input').on('input', function() {
//         fetchData(currentPage, itemsPerPage);
//     });

//     queryTypeDropdown.on('change', function() {
//         fetchData(currentPage, itemsPerPage);
//     });

//     prevButton.on('click', function() {
//         if (currentPage > 1) {
//             currentPage--;
//             fetchData(currentPage, itemsPerPage);
//         }
//     });

//     nextButton.on('click', function() {
//         currentPage++;
//         fetchData(currentPage, itemsPerPage);
//     });

//     // Footer Section
//     var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
//     footer_section.css({
//         'margin-top': '25px',
//         'border-top': '1px solid #ccc',
//         'padding-top': '10px',
//         'text-align': 'left'
//     });

//     $('<hr>').appendTo(footer_section);
//     $('<p>').html('<strong>Disclaimer:</strong>This Halal Evaluation Report is issued based on the information and documentation provided at the time of evaluation. It is valid only for the specified batch/lot and for the specific materials/products mentioned. Any misuse, alteration, or use of this report beyond its intended purpose is strictly prohibited. SANHA Halal Pakistan reserves the right to revoke this evaluation in case of any non-compliance or deviation from the Halal standards.').appendTo(footer_section);
//     $('<hr>').appendTo(footer_section);
//     $('<p>').html('<strong>Sanha Halal Associates Pakistan PVT. LTD.</strong> Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama D.H.A. phase 5  <strong> Email: </strong>evaluation@sanha.org.pk - <strong>Ph: +92 21 35295263</strong>').appendTo(footer_section);
// };
// #########################
// frappe.pages['report-print-page'].on_page_load = function(wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Report Print Page',
//         single_column: true
//     });

//     var action_section = $('<div>').addClass('action-section').appendTo(page.body);

//     // Print button
//     var printButton = $('<button>').text('Print').addClass('btn btn-primary').appendTo(action_section);
//     printButton.on('click', function() {
//         // Save current visibility state of elements
//         var titleVisible = page.$title_area.is(':visible');
//         var filterRowVisible = $('.filter-row').is(':visible');
//         var filterSectionVisible = $('.filter-section').is(':visible');
//         var paginationSectionVisible = $('.pagination-section').is(':visible');
//         var actionSectionVisible = $('.action-section').is(':visible');

//         // Hide elements before printing
//         page.$title_area.hide();
//         $('.filter-row').hide();
//         $('.filter-section').hide();
//         $('.pagination-section').hide();
//         $('.action-section').hide();

//         // Print the entire page
//         window.print();

//         // Restore visibility after printing
//         if (titleVisible) page.$title_area.show();
//         if (filterRowVisible) $('.filter-row').show();
//         if (filterSectionVisible) $('.filter-section').show();
//         if (paginationSectionVisible) $('.pagination_section').show();
//         if (actionSectionVisible) $('.action-section').show();
//     });

//     // Align action buttons to the right
//     action_section.css({
//         'display': 'flex',
//         'justify-content': 'flex-end',
//         'margin-bottom': '10px'
//     });

//     // Header Section
//     var header_section = $('<div>').addClass('header-section').appendTo(page.body);
//     header_section.css({
//         'padding': '20px',
//         'margin-top': '30px',
//         'margin-bottom': '20px',
//         'border-bottom': '1px solid #ccc',
//         'display': 'table',
//         'width': '100%'
//     });

//     // Logo Container
//     var logo_container = $('<div>').addClass('logo-container').appendTo(header_section);
//     logo_container.css({
//         'display': 'table-cell',
//         'text-align': 'right',
//         'width': '55%'
//     });
//     var logo = $('<img>').attr('src', 'http://portal.sanha.org.pk/assets/dist/img/sanha-logo.png').addClass('img').appendTo(logo_container);
//     logo.css({
//         'width': '150px',
//         'height': 'auto'
//     });

//     // Slogan Container
//     var slogan_container = $('<div>').addClass('slogan-container').appendTo(header_section);
//     slogan_container.css({
//         'display': 'table-cell',
//         'text-align': 'right',
//         'vertical-align': 'middle',
//         'width': '45%'
//     });
//     $('<span>').text('Eat Halal, Be Healthy.').appendTo(slogan_container);

//     // Filter Section
//     var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
//     filterSection.css({
//         'margin-bottom': '35px',
//         'display': 'flex',
//         'justify-content': 'space-between',
//         'align-items': 'center'
//     });

//     // Query type selection dropdown
//     var queryTypeDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
//     queryTypeDropdown.append('<option>Select Query Type</option>');

//     // Owner Table Section
//     var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(page.body);
//     owner_table_section.css({
//         'margin-bottom': '20px',
//         'text-align': 'center'
//     });

//     // Date range section
//     var date_range_section = $('<div>').addClass('date-range-section').appendTo(page.body);
//     date_range_section.css({
//         'margin-bottom': '20px',
//         'text-align': 'center'
//     });

//     // Data Section
//     var data_section = $('<div>').addClass('data-section').appendTo(page.body);
//     data_section.css({
//         'margin-bottom': '20px',
//         'display': 'flex',
//         'align-items': 'center',
//         'flex-wrap': 'wrap'
//     });

//     var table = $('<table>').addClass('table').appendTo(data_section);
//     var thead = $('<thead>').appendTo(table);
//     var tbody = $('<tbody>').appendTo(table);
//     var tableHeaders = ['S.No', 'Raw Material', 'Supplier', 'Manufacturer', 'Status'];

//     var headerRow = $('<tr>').appendTo(thead);
//     headerRow.append($('<th>').append($('<input>').attr('type', 'checkbox').attr('id', 'select-all').on('change', function() {
//         // Check/uncheck all checkboxes
//         $('.item-select').prop('checked', this.checked);
//         updateDateRange();
//         updateTotalCount();
//     })));
//     tableHeaders.forEach(function(label) {
//         $('<th>').text(label).appendTo(headerRow);
//     });

//     var filterRow = $('<tr>').addClass('filter-row').appendTo(thead);
//     tableHeaders.forEach(function(label) {
//         $('<td>').append($('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label)).appendTo(filterRow);
//     });

//     // Pagination Section
//     var pagination_section = $('<div>').addClass('pagination-section').appendTo(page.body);
//     pagination_section.css({
//         'display': 'flex',
//         'justify-content': 'center',
//         'margin-top': '20px'
//     });

//     var prevButton = $('<button>').text('Previous').addClass('btn btn-secondary').appendTo(pagination_section);
//     var nextButton = $('<button>').text('Next').addClass('btn btn-secondary').appendTo(pagination_section);

//     prevButton.css({
//         'order': '1',
//         'margin-right': 'auto'
//     });

//     nextButton.css({
//         'order': '2'
//     });

//     var currentPage = 1;
//     var itemsPerPage = 50;

//     // Function to fetch and display all data
//     function fetchData() {
//         var filters = {
//             workflow_state: ['!=', 'Draft'],
//             owner: frappe.session.user
//         };

//         if (queryTypeDropdown.val() !== 'Select Query Type') {
//             filters.query_types = ['like', '%' + queryTypeDropdown.val() + '%'];
//         }

//         var additionalFilters = {};
//         filterRow.find('input').each(function(index) {
//             var value = $(this).val();
//             if (value) {
//                 var fieldMap = {
//                     'Raw Material': 'raw_material',
//                     'Supplier': 'supplier',
//                     'Manufacturer': 'manufacturer',
//                     'Status': 'workflow_state'
//                 };
//                 var field = fieldMap[tableHeaders[index + 1]]; // Offset by 1 for serial number
//                 if (field) {
//                     additionalFilters[field] = ['like', '%' + value + '%'];
//                 }
//             }
//         });

//         Object.assign(filters, additionalFilters);

//         // Fetch all items without pagination
//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 fields: ['raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types'],
//                 filters: filters,
//                 limit_page_length: 9999, // Large limit to fetch all items
//                 order_by: 'raw_material asc'
//             },
//             callback: function(response) {
//                 var data = response.message;
//                 tbody.empty();

//                 // Add Serial Numbers and Populate Table
//                 data.forEach(function(row, index) {
//                     var tableRow = $('<tr>').appendTo(tbody);
//                     $('<td>').text(index + 1).appendTo(tableRow); // Serial Number
//                     tableHeaders.slice(1).forEach(function(key) { // Slice to exclude 'S.No'
//                         var field = key.toLowerCase().replace(' ', '_');
//                         if (field === 'status') field = 'workflow_state';
//                         if (field === 'creation') {
//                             var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
//                             $('<td>').text(formattedDate).appendTo(tableRow);
//                         } else {
//                             $('<td>').text(row[field]).appendTo(tableRow);
//                         }
//                     });

//                     // Checkbox for selection
//                     var selectTd = $('<td>').appendTo(tableRow);
//                     var checkbox = $('<input>').attr('type', 'checkbox').addClass('item-select');
//                     selectTd.append(checkbox);

//                     // Event listener for checkbox change
//                     checkbox.on('change', function() {
//                         updateDateRange();
//                         updateTotalCount();
//                     });
//                 });

//                 updateTotalCount(data.length);
//                 updateDateRange();
//             }
//         });
//     }

//     // Update Total Count Function
//     function updateTotalCount(itemCount) {
//         var totalCountSection = $('<div>').addClass('total-count-section').appendTo(page.body);
//         totalCountSection.empty();
//         $('<strong>').text('Total Items: ' + itemCount).appendTo(totalCountSection);
        
//         var selectedCount = $('.item-select:checked').length;
//         $('<strong>').text('Selected Items: ' + selectedCount).appendTo(totalCountSection);
//     }

//     // Update Owner Table
//     function updateOwnerTable() {
//         owner_table_section.empty();
//         var uniqueClients = new Set();

//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 filters: {
//                     owner: frappe.session.user,
//                     client_name: ['!=', ''],
//                     client_code: ['!=', '']
//                 },
//                 fields: ['client_name', 'client_code']
//             },
//             callback: function(response) {
//                 if (response.message.length > 0) {
//                     var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
//                     var tbody = $('<tbody>').appendTo(ownerTable);

//                     response.message.forEach(function(query) {
//                         var clientName = query.client_name.toUpperCase(); // Capitalize client name
//                         var clientCode = query.client_code.toUpperCase(); // Capitalize client code
//                         var clientIdentifier = clientName + clientCode;
//                         if (!uniqueClients.has(clientIdentifier)) {
//                             uniqueClients.add(clientIdentifier);

//                             // Create table for owner data with specific format
//                             var first_row = $('<tr>').appendTo(tbody);
//                             var first_row_data = $('<td>').addClass('text-center').appendTo(first_row);
//                             $('<h2>').css({'font-weight': 'bold'}).text('Account: ' + clientName + ' (Code: ' + clientCode + ')').appendTo(first_row_data);
//                         }
//                     });
//                 } else {
//                     $('<p>').text('No client data available').appendTo(owner_table_section);
//                 }
//             }
//         });
//     }

//     // Update Date Range Function
//     function updateDateRange() {
//         var selectedItems = $('.item-select:checked');
//         var filters = { owner: frappe.session.user };

//         if (selectedItems.length > 0) {
//             var selectedDates = [];
//             selectedItems.each(function() {
//                 var rowIndex = $(this).closest('tr').index();
//                 var creationDate = moment(tbody.find('tr').eq(rowIndex).find('td').eq(5).text(), 'DD-MM-YYYY hh:mm A');
//                 selectedDates.push(creationDate);
//             });

//             if (selectedDates.length > 0) {
//                 var oldestDate = moment.min(selectedDates).format('DD-MM-YYYY hh:mm A');
//                 var latestDate = moment().format('DD-MM-YYYY hh:mm A');
//                 date_range_section.html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>');
//             }
//         } else {
//             // When no items are selected
//             frappe.call({
//                 method: 'frappe.client.get_list',
//                 args: {
//                     doctype: 'Query',
//                     fields: ['creation'],
//                     filters: filters,
//                     order_by: 'creation asc'
//                 },
//                 callback: function(response) {
//                     var data = response.message;
//                     if (data.length > 0) {
//                         var oldestDate = moment(data[0].creation).format('DD-MM-YYYY hh:mm A');
//                         var latestDate = moment().format('DD-MM-YYYY hh:mm A');
//                         date_range_section.html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>');
//                     } else {
//                         date_range_section.html('Date Range: No Data Available');
//                     }
//                 }
//             });
//         }
//     }

//     // Initial fetch and display data
//     updateOwnerTable();
//     fetchData();

//     filterRow.find('input').on('input', function() {
//         fetchData();
//     });

//     queryTypeDropdown.on('change', function() {
//         fetchData();
//     });

//     // Footer Section
//     var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
//     footer_section.css({
//         'margin-top': '25px',
//         'border-top': '1px solid #ccc',
//         'padding-top': '10px',
//         'text-align': 'left'
//     });

//     $('<hr>').appendTo(footer_section);
//     $('<p>').html('<strong>Disclaimer:</strong>This Halal Evaluation Report is issued based on the information and documentation provided at the time of evaluation. It is valid only for the specified batch/lot and for the specific materials/products mentioned. Any misuse, alteration, or use of this report beyond its intended purpose is strictly prohibited. SANHA Halal Pakistan reserves the right to revoke this evaluation in case of any non-compliance or deviation from the Halal standards.').appendTo(footer_section);
//     $('<hr>').appendTo(footer_section);
//     $('<p>').html('<strong>Sanha Halal Associates Pakistan PVT. LTD.</strong> Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama D.H.A. phase 5  <strong> Email: </strong>evaluation@sanha.org.pk - <strong>Ph: +92 21 35295263</strong>').appendTo(footer_section);
// };

// #################
// frappe.pages['report-print-page'].on_page_load = function(wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Report Print Page',
//         single_column: true
//     });

//     var action_section = $('<div>').addClass('action-section').appendTo(page.body);

//     // Print button
//     var printButton = $('<button>').text('Print').addClass('btn btn-primary').appendTo(action_section);
//     printButton.on('click', function() {
//         // Save current visibility state of elements
//         var titleVisible = page.$title_area.is(':visible');
//         var filterRowVisible = $('.filter-row').is(':visible');
//         var filterSectionVisible = $('.filter-section').is(':visible');
//         var paginationSectionVisible = $('.pagination-section').is(':visible');
//         var actionSectionVisible = $('.action-section').is(':visible');

//         // Hide elements before printing
//         page.$title_area.hide();
//         $('.filter-row').hide();
//         $('.filter-section').hide();
//         $('.pagination-section').hide();
//         $('.action-section').hide();

//         // Print the entire page
//         window.print();

//         // Restore visibility after printing
//         if (titleVisible) page.$title_area.show();
//         if (filterRowVisible) $('.filter-row').show();
//         if (filterSectionVisible) $('.filter-section').show();
//         if (paginationSectionVisible) $('.pagination-section').show();
//         if (actionSectionVisible) $('.action-section').show();
//     });

//     // Align action buttons to the right
//     action_section.css({
//         'display': 'flex',
//         'justify-content': 'flex-end',
//         'margin-bottom': '10px'
//     });

//     // Header Section
//     var header_section = $('<div>').addClass('header-section').appendTo(page.body);
//     header_section.css({
//         'padding': '20px',
//         'margin-top': '30px',
//         'margin-bottom': '20px',
//         'border-bottom': '1px solid #ccc',
//         'display': 'table',
//         'width': '100%'
//     });

//     // Logo Container
//     var logo_container = $('<div>').addClass('logo-container').appendTo(header_section);
//     logo_container.css({
//         'display': 'table-cell',
//         'text-align': 'right',
//         'width': '55%'
//     });
//     var logo = $('<img>').attr('src', 'http://portal.sanha.org.pk/assets/dist/img/sanha-logo.png').addClass('img').appendTo(logo_container);
//     logo.css({
//         'width': '150px',
//         'height': 'auto'
//     });

//     // Slogan Container
//     var slogan_container = $('<div>').addClass('slogan-container').appendTo(header_section);
//     slogan_container.css({
//         'display': 'table-cell',
//         'text-align': 'right',
//         'vertical-align': 'middle',
//         'width': '45%'
//     });
//     $('<span>').text('Eat Halal, Be Healthy.').appendTo(slogan_container);

//     // Filter Section
//     var filterSection = $('<div>').addClass('filter-section').appendTo(page.body);
//     filterSection.css({
//         'margin-bottom': '35px',
//         'display': 'flex',
//         'justify-content': 'space-between',
//         'align-items': 'center'
//     });

//     // Query type selection dropdown
//     var queryTypeDropdown = $('<select>').addClass('form-control').appendTo(filterSection);
//     queryTypeDropdown.append('<option>Select Query Type</option>');

//     // Owner Table Section
//     var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(page.body);
//     owner_table_section.css({
//         'margin-bottom': '20px',
//         'text-align': 'center'
//     });

//     // Date range section
//     var date_range_section = $('<div>').addClass('date-range-section').appendTo(page.body);
//     date_range_section.css({
//         'margin-bottom': '20px',
//         'text-align': 'center'
//     });

//     // Data Section
//     var data_section = $('<div>').addClass('data-section').appendTo(page.body);
//     data_section.css({
//         'margin-bottom': '20px',
//         'display': 'flex',
//         'align-items': 'center',
//         'flex-wrap': 'wrap'
//     });

//     var table = $('<table>').addClass('table').appendTo(data_section);
//     var thead = $('<thead>').appendTo(table);
//     var tbody = $('<tbody>').appendTo(table);
//     var tableHeaders = ['Select', 'S.No', 'Raw Material', 'Supplier', 'Manufacturer', 'Status'];

//     var headerRow = $('<tr>').appendTo(thead);
//     headerRow.append($('<th>').append($('<input>').attr('type', 'checkbox').attr('id', 'select-all').on('change', function() {
//         // Check/uncheck all checkboxes
//         $('.item-select').prop('checked', this.checked);
//         updateDateRange();
//         updateTotalCount();
//     })));
//     tableHeaders.slice(1).forEach(function(label) {
//         $('<th>').text(label).appendTo(headerRow);
//     });

//     var filterRow = $('<tr>').addClass('filter-row').appendTo(thead);
//     tableHeaders.slice(1).forEach(function(label) {
//         $('<td>').append($('<input>').addClass('form-control').attr('placeholder', 'Filter ' + label)).appendTo(filterRow);
//     });

//     var pagination_section = $('<div>').addClass('pagination-section').appendTo(page.body);
//     pagination_section.css({
//         'display': 'flex',
//         'justify-content': 'center',
//         'margin-top': '20px'
//     });

//     var prevButton = $('<button>').text('Previous').addClass('btn btn-secondary').appendTo(pagination_section);
//     var nextButton = $('<button>').text('Next').addClass('btn btn-secondary').appendTo(pagination_section);

//     prevButton.css({
//         'order': '1',
//         'margin-right': 'auto'
//     });

//     nextButton.css({
//         'order': '2'
//     });

//     // Function to fetch and display all data
//     function fetchData() {
//         var filters = {
//             workflow_state: ['!=', 'Draft'],
//             owner: frappe.session.user
//         };

//         if (queryTypeDropdown.val() !== 'Select Query Type') {
//             filters.query_types = ['like', '%' + queryTypeDropdown.val() + '%'];
//         }

//         var additionalFilters = {};
//         filterRow.find('input').each(function(index) {
//             var value = $(this).val();
//             if (value) {
//                 var fieldMap = {
//                     'Raw Material': 'raw_material',
//                     'Supplier': 'supplier',
//                     'Manufacturer': 'manufacturer',
//                     'Status': 'workflow_state'
//                 };
//                 var field = fieldMap[tableHeaders[index + 1]]; // Offset by 1 for serial number
//                 if (field) {
//                     additionalFilters[field] = ['like', '%' + value + '%'];
//                 }
//             }
//         });

//         Object.assign(filters, additionalFilters);

//         // Fetch all items without pagination
//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 fields: ['raw_material', 'supplier', 'manufacturer', 'workflow_state', 'client_name', 'client_code', 'creation', 'query_types'],
//                 filters: filters,
//                 limit_page_length: 9999, // Large limit to fetch all items
//                 order_by: 'raw_material asc'
//             },
//             callback: function(response) {
//                 var data = response.message;
//                 tbody.empty();

//                 // Add Checkboxes, Serial Numbers, and Populate Table
//                 data.forEach(function(row, index) {
//                     var tableRow = $('<tr>').appendTo(tbody);
                    
//                     // Checkbox for selection
//                     var selectTd = $('<td>').appendTo(tableRow);
//                     var checkbox = $('<input>').attr('type', 'checkbox').addClass('item-select');
//                     selectTd.append(checkbox);

//                     // Serial Number
//                     $('<td>').text(index + 1).appendTo(tableRow); 

//                     tableHeaders.slice(2).forEach(function(key) { // Slice to exclude 'Select' and 'S.No'
//                         var field = key.toLowerCase().replace(' ', '_');
//                         if (field === 'status') field = 'workflow_state';
//                         if (field === 'creation') {
//                             var formattedDate = moment(row.creation).format('DD-MM-YYYY hh:mm A');
//                             $('<td>').text(formattedDate).appendTo(tableRow);
//                         } else {
//                             $('<td>').text(row[field]).appendTo(tableRow);
//                         }
//                     });

//                     // Event listener for checkbox change
//                     checkbox.on('change', function() {
//                         updateDateRange();
//                         updateTotalCount();
//                     });
//                 });

//                 updateTotalCount(data.length);
//                 updateDateRange();
//             }
//         });
//     }

//     // Update Total Count Function
//     function updateTotalCount(itemCount) {
//         var totalCountSection = $('<div>').addClass('total-count-section').appendTo(page.body);
//         totalCountSection.empty();
//         $('<strong>').text('Total Items: ' + itemCount).appendTo(totalCountSection);
        
//         var selectedCount = $('.item-select:checked').length;
//         $('<strong>').text('Selected Items: ' + selectedCount).appendTo(totalCountSection);
//     }

//     // Update Owner Table
//     function updateOwnerTable() {
//         owner_table_section.empty();
//         var uniqueClients = new Set();

//         frappe.call({
//             method: 'frappe.client.get_list',
//             args: {
//                 doctype: 'Query',
//                 filters: {
//                     owner: frappe.session.user,
//                     client_name: ['!=', ''],
//                     client_code: ['!=', '']
//                 },
//                 fields: ['client_name', 'client_code']
//             },
//             callback: function(response) {
//                 if (response.message.length > 0) {
//                     var ownerTable = $('<table>').addClass('table').appendTo(owner_table_section);
//                     var tbody = $('<tbody>').appendTo(ownerTable);

//                     response.message.forEach(function(query) {
//                         var clientName = query.client_name.toUpperCase(); // Capitalize client name
//                         var clientCode = query.client_code.toUpperCase(); // Capitalize client code
//                         var clientIdentifier = clientName + clientCode;
//                         if (!uniqueClients.has(clientIdentifier)) {
//                             uniqueClients.add(clientIdentifier);

//                             // Create table for owner data with specific format
//                             var first_row = $('<tr>').appendTo(tbody);
//                             var first_row_data = $('<td>').addClass('text-center').appendTo(first_row);
//                             $('<h2>').css({'font-weight': 'bold'}).text('Account: ' + clientName + ' (Code: ' + clientCode + ')').appendTo(first_row_data);
//                         }
//                     });
//                 } else {
//                     $('<p>').text('No client data available').appendTo(owner_table_section);
//                 }
//             }
//         });
//     }

//     // Update Date Range Function
//     function updateDateRange() {
//         var selectedItems = $('.item-select:checked');
//         var filters = { owner: frappe.session.user };

//         if (selectedItems.length > 0) {
//             var selectedDates = [];
//             selectedItems.each(function() {
//                 var rowIndex = $(this).closest('tr').index();
//                 var creationDate = moment(tbody.find('tr').eq(rowIndex).find('td').eq(5).text(), 'DD-MM-YYYY hh:mm A');
//                 selectedDates.push(creationDate);
//             });

//             if (selectedDates.length > 0) {
//                 var oldestDate = moment.min(selectedDates).format('DD-MM-YYYY hh:mm A');
//                 var latestDate = moment().format('DD-MM-YYYY hh:mm A');
//                 date_range_section.html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>');
//             }
//         } else {
//             // When no items are selected
//             frappe.call({
//                 method: 'frappe.client.get_list',
//                 args: {
//                     doctype: 'Query',
//                     fields: ['creation'],
//                     filters: filters,
//                     order_by: 'creation asc'
//                 },
//                 callback: function(response) {
//                     var data = response.message;
//                     if (data.length > 0) {
//                         var oldestDate = moment(data[0].creation).format('DD-MM-YYYY hh:mm A');
//                         var latestDate = moment().format('DD-MM-YYYY hh:mm A');
//                         date_range_section.html('Date Range: <strong>From: ' + oldestDate + '</strong> To: <strong>' + latestDate + '</strong>');
//                     } else {
//                         date_range_section.html('Date Range: No Data Available');
//                     }
//                 }
//             });
//         }
//     }

//     // Initial fetch and display data
//     updateOwnerTable();
//     fetchData();

//     filterRow.find('input').on('input', function() {
//         fetchData();
//     });

//     queryTypeDropdown.on('change', function() {
//         fetchData();
//     });

//     // Footer Section
//     var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
//     footer_section.css({
//         'margin-top': '25px',
//         'border-top': '1px solid #ccc',
//         'padding-top': '10px',
//         'text-align': 'left'
//     });

//     $('<hr>').appendTo(footer_section);
//     $('<p>').html('<strong>Disclaimer:</strong>This Halal Evaluation Report is issued based on the information and documentation provided at the time of evaluation. It is valid only for the specified batch/lot and for the specific materials/products mentioned. Any misuse, alteration, or use of this report beyond its intended purpose is strictly prohibited. SANHA Halal Pakistan reserves the right to revoke this evaluation in case of any non-compliance or deviation from the Halal standards.').appendTo(footer_section);
//     $('<hr>').appendTo(footer_section);
//     $('<p>').html('<strong>Sanha Halal Associates Pakistan PVT. LTD.</strong> Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama D.H.A. phase 5  <strong> Email: </strong>evaluation@sanha.org.pk - <strong>Ph: +92 21 35295263</strong>').appendTo(footer_section);
// };
// ###########