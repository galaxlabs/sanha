frappe.pages['cr-report'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Reports Page',
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
// Create filter section for query types dropdown

// Header section


    var header_section = $('<div>').addClass('header-section').appendTo(page.body);
header_section.css({
    'padding': '20px',
    'margin-bottom': '10px', // Add margin below the header section
    'border-bottom': '1px solid #ccc', // Add horizontal line at the bottom of the header
    'display': 'table',
    'width': '100%'
});

// Logo container
var logo_container = $('<div>').addClass('logo-container').appendTo(header_section);
logo_container.css({
    'display': 'table-cell',
    'text-align': 'right',
    'width': '55%'
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

    // Header section with company logo and slogan

   
    // Owner table section between the filter section and the data section
    var owner_table_section = $('<div>').addClass('owner-table-section').appendTo(page.body);
    owner_table_section.css({
        'margin-bottom': '20px', // Add margin below the owner table section
        'text-align': 'center' // Center the content within the owner table section
    });
    
    // Fetch current user's full name and location code
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'User',
            filters: {
                name: frappe.session.user // Get current session user's name
            },
            fields: ['full_name', 'location'] // Fetch full name and location fields
        },
        callback: function(response) {
            var user = response.message;
            if (user) {
                // Create table for owner data
                var owner_table = $('<table>').addClass('table').appendTo(owner_table_section);
                var tbody = $('<tbody>').appendTo(owner_table);
    
                // First row: Full name and location code
                var first_row = $('<tr>').appendTo(tbody);
                var first_row_data = $('<td>').addClass('text-center').appendTo(first_row);
                $('<h2>').text(user.full_name + ' (Code: ' + user.location + ')').appendTo(first_row_data);
    
                // Second row: Date range
                var second_row = $('<tr>').appendTo(tbody);
                var second_row_data = $('<td>').addClass('text-center').appendTo(second_row);
                $('<span>').append($('<strong>').text('From Date: 09-Mar-2024 - To Date: 08-May-2024')).appendTo(second_row_data);
            }
        }
    });
    var data_section = $('<div>').addClass('data-section').appendTo(page.body);
        data_section.css({
            'margin-bottom': '20px', // Add margin below the data section
            'display': 'flex',
            'align-items': 'center',
            'flex-wrap': 'wrap'
        });
        

    var table = $('<table>').addClass('table').appendTo(page.body);
    var thead = $('<thead>').appendTo(table);
    var tbody = $('<tbody>').appendTo(table);
    var tableHeaders = ['Raw Material', 'Supplier', 'Manufacturer', 'Query Types', 'Status'];

    // Add table headers
    var headerRow = $('<tr>').appendTo(thead);
    $.each(tableHeaders, function(index, label) {
        $('<th>').text(label).appendTo(headerRow);
    });

    // Fetch data from the server and populate the table
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Query',
            filters: {
                workflow_state: ['!=', 'Draft']
            },
            fields: ['raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state']
        },
        callback: function(response) {
            var data = response.message;
            $.each(data, function(index, row) {
                var tableRow = $('<tr>').appendTo(tbody);
                $.each(tableHeaders, function(index, key) {
                    if (key === 'Status') {
                        $('<td>').text(row['workflow_state']).appendTo(tableRow);
                    } else {
                        $('<td>').text(row[key.toLowerCase().replace(' ', '_')]).appendTo(tableRow);
                    }
                });
            });

            // Initialize DataTable with search and pagination
            $(table).DataTable();
        }
    });

    // Filter function for each column
    var filterColumns = {};
    $.each(tableHeaders, function(index, label) {
        filterColumns[label] = '';
    });

    // Add input fields for filtering
    var filterRow = $('<tr>').appendTo(thead).addClass('filter-row');
$.each(tableHeaders, function(index, label) {
    var filterInput = $('<input>').attr('type', 'text').attr('placeholder', 'Filter ' + label).addClass('filter-input').appendTo($('<th>').appendTo(filterRow));
    filterInput.css({
        'border-radius': '20px', // Set border radius to 20px for rounded corners
        'padding': '5px', // Add padding to the input fields
        'margin': '5px' // Add margin around each input field
    });
    filterInput.on('keyup', function() {
        filterColumns[label] = $(this).val().toLowerCase();
        filterTable();
    });
});

    // Function to filter the table based on input values
    function filterTable() {
        $(tbody).find('tr').each(function() {
            var rowVisible = true;
            var row = $(this);
            $.each(tableHeaders, function(index, label) {
                var cellText = row.find('td').eq(index).text().toLowerCase();
                if (filterColumns[label] && cellText.indexOf(filterColumns[label]) === -1) {
                    rowVisible = false;
                }
            });
            if (rowVisible) {
                row.show();
            } else {
                row.hide();
            }
        });
    }

// ### Working with filter ####
    $('<hr>').appendTo(footer_section);
    var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
    footer_section.css({
        'margin-top': '25px', // Set footer top margin to 25px
        'border-top': '1px solid #ccc', // Add horizontal line at the top of the footer
        'padding-top': '10px', // Add padding to the top of the footer
        'text-align': 'right'
    });
    
    // Add horizontal lines on both ends of the footer
    $('<hr>').appendTo(footer_section);
    
    // Add company address
    $('<p>').html('<strong>Sanha Halal Associates Pakistan PVT. LTD.</strong> Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama D.H.A. phase 5<br>Email: evaluation@sanha.org.pk - Ph: +92 21 35295263').appendTo(footer_section);
    
    // Add footer with page number
};