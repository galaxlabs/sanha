frappe.pages['cr-report'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Reports',
        single_column: true
    });

    // Header section with company logo and tagline
    var header_section = $('<div>').addClass('header-section').appendTo(page.body);
    header_section.css({
        'display': 'flex',
        'align-items': 'center',
        'justify-content': 'space-between',
        'padding': '20px',
        'margin-top': '40px', // Set header top margin to 40px
        'border-bottom': '1px solid #ccc' // Add horizontal line at the bottom of the header
    });

    // Left part of the header - empty space
    var left_header = $('<div>').appendTo(header_section);

    // Center part of the header - company logo
    var center_header = $('<div>').appendTo(header_section);
    center_header.css({
        'flex': '2',
        'text-align': 'center' // Center the logo horizontally
    });
    $('<img>').attr('src', 'http://portal.sanha.org.pk/assets/dist/img/sanha-logo.png').addClass('img').css({
        'width': 'auto',
        'height': '95px',
        'margin': 'auto' // Center the logo horizontally
    }).appendTo(center_header);

    // Right part of the header - slogan
    var right_header = $('<div>').appendTo(header_section);
    right_header.css({
        'text-align': 'right'
    });
    $('<span>').text('Eat Halal, Be Healthy.').css({
        'vertical-align': 'middle', // Align the slogan vertically to the center
        'display': 'inline-block' // Set display to inline-block for vertical alignment
    }).appendTo(right_header);

    // Add a table to display the report
    var table = $('<table>').addClass('table').appendTo(page.body);
    var tbody = $('<tbody>').appendTo(table);

    // Add a container to display the report content
    var report_container = $('<div>').addClass('report-container').appendTo(page.body);

    // Fetch data from the server and populate the table
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Query',
            filters: {
                workflow_state: ['!=', 'Draft']
            },
            fields: ['raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state', 'creation', 'owner']
        },
        callback: function(response) {
            var data = response.message;
            $.each(data, function(index, row) {
                var tableRow = $('<tr>').appendTo(tbody);
                $('<td>').text(row.raw_material).appendTo(tableRow);
                $('<td>').text(row.supplier).appendTo(tableRow);
                $('<td>').text(row.manufacturer).appendTo(tableRow);
                $('<td>').text(row.query_types).appendTo(tableRow);
                $('<td>').text(row.workflow_state).appendTo(tableRow);
                $('<td>').text(row.creation).appendTo(tableRow);
                $('<td>').text(row.owner).appendTo(tableRow);
               
            });
        }
    });

    // Add footer with page number
    var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
    footer_section.css({
        'margin-top': '25px', // Set footer top margin to 25px
        'border-top': '1px solid #ccc', // Add horizontal line at the top of the footer
        'padding-top': '10px', // Add padding to the top of the footer
        'text-align': 'center'
    });

    // Add horizontal lines on both ends of the footer
    $('<hr>').appendTo(footer_section);
    $('<hr>').appendTo(footer_section);
};

// frappe.pages['cr-report'].on_page_load = function(wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Reports',
//         single_column: true
//     });

//     // Header section with company logo and tagline
//     var header_section = $('<div>').addClass('header-section').appendTo(page.body);
//     header_section.css({
//         'display': 'flex',
//         'align-items': 'center',
//         'justify-content': 'space-between',
//         'padding': '20px'
//     });

//     // Left part of the header - company name and tagline
//     var left_header = $('<div>').appendTo(header_section);
//     $('<span>').text('Eat Halal, Be Healthy.').appendTo(right_header);

//     // Center part of the header - company logo
//     var center_header = $('<div>').appendTo(header_section);
//     $('<img>').attr('src', 'http://portal.sanha.org.pk/assets/dist/img/sanha-logo.png').addClass('img').css({
//         'width': 'auto',
//         'height': '95px'
//     }).appendTo(center_header);

//     // Right part of the header - empty space
//     var right_header = $('<div>').appendTo(header_section);

//     // Add a table to display the report
//     var table = $('<table>').addClass('table').appendTo(page.body);
//     var tbody = $('<tbody>').appendTo(table);

//     // Add a container to display the report content
//     var report_container = $('<div>').addClass('report-container').appendTo(page.body);

//     // Fetch data from the server and populate the table
//     frappe.call({
//         method: 'frappe.client.get_list',
//         args: {
//             doctype: 'Query',
//             filters: {
//                 workflow_state: ['!=', 'Draft']
//             },
//             fields: ['name', 'raw_material', 'supplier', 'manufacturer', 'query_types', 'workflow_state', 'creation', 'owner',]
//         },
//         callback: function(response) {
//             var data = response.message;
//             $.each(data, function(index, row) {
//                 var tableRow = $('<tr>').appendTo(tbody);
//                 $('<td>').text(row.name).appendTo(tableRow);
//                 $('<td>').text(row.raw_material).appendTo(tableRow);
//                 $('<td>').text(row.supplier).appendTo(tableRow);
//                 $('<td>').text(row.manufacturer).appendTo(tableRow);
//                 $('<td>').text(row.query_types).appendTo(tableRow);
//                 $('<td>').text(row.workflow_state).appendTo(tableRow);
//                 $('<td>').text(row.creation).appendTo(tableRow);
//                 $('<td>').text(row.owner).appendTo(tableRow);
                
//             });
//         }
//     });
// };

// frappe.pages['cr-report'].on_page_load = function(wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Reports',
//         single_column: true
//     });

//     // Add the static header HTML
//     var static_header = `
//         <div class="header-section">
//             <!-- Center part of the header - company logo -->
//             <div style="flex: 1; text-align: center;">
//                 <img src="http://portal.sanha.org.pk/assets/dist/img/sanha-logo.png" class="img" style="width: auto; height: 95px;">
//             </div>
//             <hr>
//             <!-- Section with owner's full name and code -->
//             <div class="owner-section" style="text-align: center;">
//                 <strong>Name: John Doe</strong> <span> | </span> <strong>Code: ABC123</strong>
//             </div>
//             <hr>
//             <!-- Last section - Date range "From - To" -->
//             <div class="date-section" style="text-align: center;">
//                 <span>From: </span><strong>2022-01-01</strong> <span> - </span> <span>To: </span><strong>2022-12-31</strong>
//             </div>
//             <hr>
//             <!-- Right part of the header - company tagline -->
//             <div style="flex: 1; text-align: right;">
//                 <span>Eat Halal, Be Healthy.</span>
//             </div>
//             <hr>
//         </div>
//     `;

//     // Append the static header HTML to the page body
//     $(static_header).appendTo(page.body);

//     // Fetch dynamic table data and populate the table
//     fetchDynamicTableData();
// };

// function fetchDynamicTableData() {
//     // Make an AJAX request to fetch dynamic table data from the server
//     // Replace this with your actual AJAX call to fetch data from the database
//     $.ajax({
//         url: '/your-api-endpoint',
//         method: 'GET',
//         success: function(response) {
//             // Populate the dynamic table content with the fetched data
//             populateTable(response);
//         },
//         error: function(xhr, status, error) {
//             console.error(error);
//         }
//     });
// }

// function populateTable(data) {
//     // Construct the HTML for the dynamic table based on the fetched data
//     var tableContent = `
//         <div class="table-section">
//             <table class="table table-bordered">
//                 <thead>
//                     <tr>
//                         <th>Raw Material</th>
//                         <th>Supplier</th>
//                         <th>Manufacturer</th>
//                         <th>Status</th>
//                     </tr>
//                 </thead>
//                 <tbody>
//                     <!-- Table body content goes here -->
//                 </tbody>
//             </table>
//         </div>
//     `;

//     // Append the dynamic table HTML to the page body
//     $(tableContent).appendTo('div.header-section');

//     // Populate the table body with the fetched data
//     var tbody = $('div.table-section tbody');
//     $.each(data, function(index, row_data) {
//         // Add the regular data row
//         var data_row = $('<tr>').appendTo(tbody);
//         $('<td>').text(row_data['Raw Material']).appendTo(data_row);
//         $('<td>').text(row_data['Supplier']).appendTo(data_row);
//         $('<td>').text(row_data['Manufacturer']).appendTo(data_row);
//         $('<td>').text(row_data['Status']).appendTo(data_row);
//     });

//     // Add CSS for page breaks and header/footer display
//     $("<style>")
//         .prop("type", "text/css")
//         .html(
//             `@page {
//                 size: A4 portrait;
//                 margin: 1cm;
//                 @bottom-right {
//                     content: counter(page);
//                 }
//             }
//             @media print {
//                 .header-section {
//                     display: block;
//                     position: fixed;
//                     left: 0;
//                     right: 0;
//                 }
//                 table {
//                     page-break-inside: auto;
//                 }
//                 tr {
//                     page-break-inside: avoid;
//                     page-break-after: auto;
//                 }
//                 thead {
//                     display: table-header-group;
//                 }
//                 tbody {
//                     display: table-row-group;
//                 }
//             }`
//         )
//         .appendTo("head");
// }

// frappe.pages['cr-report'].on_page_load = function(wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Reports',
//         single_column: true
//     });

//     // Add the static header HTML
//     var static_header = `
//         <div class="header-section" style="margin-top: 40px;">
//             <!-- Center part of the header - company logo -->
//             <div style="flex: 1; text-align: center;">
//                 <img src="http://portal.sanha.org.pk/assets/dist/img/sanha-logo.png" class="img" style="width: auto; height: 95px;">
//             </div>
//             <hr>
//             <!-- Section with owner's full name and code -->
//             <div class="owner-section" style="text-align: center;">
//                 <strong id="owner-name"></strong> <span> | </span> <strong id="owner-code"></strong>
//             </div>
//             <hr>
//             <!-- Last section - Date range "From - To" -->
//             <div class="date-section" style="text-align: center;">
//                 <span>From: </span><strong id="from-date"></strong> <span> - </span> <span>To: </span><strong id="to-date"></strong>
//             </div>
//             <hr>
//             <!-- Right part of the header - company tagline -->
//             <div style="flex: 1; text-align: right;">
//                 <span>Eat Halal, Be Healthy.</span>
//             </div>
//             <hr>
//         </div>
//     `;

//     // Append the static header HTML to the page body
//     $(static_header).appendTo(page.body);

//     // Fetch dynamic data for the owner's full name, code, and date range
//     fetchDynamicHeaderData();
// };
// function fetchDynamicHeaderData() {
//     // Make an AJAX request to fetch dynamic data from the server
//     // Replace this with your actual AJAX call to fetch data from the database
//     $.ajax({
//         url: '/your-api-endpoint',
//         method: 'GET',
//         success: function(response) {
//             // Populate the dynamic header content with the fetched data
//             populateHeader(response);
//         },
//         error: function(xhr, status, error) {
//             console.error(error);
//         }
//     });
// }

// function populateHeader(data) {
//     // Populate owner's full name and code
//     $('#owner-name').text(data.owner_name);
//     $('#owner-code').text(data.owner_code);

//     // Populate date range "From - To"
//     $('#from-date').text(data.from_date);
//     $('#to-date').text(data.to_date);
// }
// frappe.pages['cr-report'].on_page_load = function(wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Reports',
//         single_column: true
//     });

//     // Header section
//     var header_section = $('<div>').addClass('header-section').appendTo(page.body);

//     // Center part of the header - company logo
//     var center_header = $('<div>').appendTo(header_section).css({
//         'flex': '1',
//         'text-align': 'center'
//     });
//     $('<img>').attr('src', 'http://portal.sanha.org.pk/assets/dist/img/sanha-logo.png').addClass('img').css({
//         'width': 'auto',
//         'height': '95px'
//     }).appendTo(center_header);

//     // Add HR element below the header
//     $('<hr>').appendTo(page.body);

//     // Section with owner's full name and code
//     var owner_section = $('<div>').addClass('owner-section').appendTo(page.body).css({
//         'text-align': 'center'
//     });
//     $('<strong>').text('Name: John Doe').appendTo(owner_section); // Dummy data for owner's full name, replace with actual data from location field
//     $('<span>').text(' | ').appendTo(owner_section); // Separator (you can change this to any other character)
//     $('<strong>').text('Code: ABC123').appendTo(owner_section); // Dummy data for owner's code, replace with actual data

//     // Add HR element below the owner section
//     $('<hr>').appendTo(page.body);

//     // Last section - Date range "From - To"
//     var date_section = $('<div>').addClass('date-section').appendTo(page.body).css({
//         'text-align': 'center'
//     });
//     $('<span>').text('From: ').appendTo(date_section);
//     $('<strong>').text('2022-01-01').appendTo(date_section); // Replace with the actual "From" date
//     $('<span>').text(' - ').appendTo(date_section);
//     $('<span>').text('To: ').appendTo(date_section);
//     $('<strong>').text('2022-12-31').appendTo(date_section); // Replace with the actual "To" date

// 	$('<hr>').appendTo(page.body);

//     // Right part of the header - company tagline
//     var right_header = $('<div>').appendTo(header_section).css({
//         'flex': '1',
//         'text-align': 'right',
// 		'align-self': 'center'
//     });
//     $('<span>').text('Eat Halal, Be Healthy.').appendTo(right_header);

// 	$('<hr>').appendTo(page.body);

//     // Table section
//     var table_section = $('<div>').appendTo(page.body);

//     // Table
//     var table = $('<table>').addClass('table table-bordered').appendTo(table_section);
//     var thead = $('<thead>').appendTo(table);
//     var tbody = $('<tbody>').appendTo(table);

//     // Table headers
//     var headers = ['Raw Material', 'Supplier', 'Manufacturer', 'Status']; // Add more headers if needed
//     var header_row = $('<tr>').appendTo(thead);
//     $.each(headers, function(index, header) {
//         $('<th>').text(header).appendTo(header_row);
//     });

//     // Table rows - sample data
//     var sample_data = [
//         { 'Raw Material': 'Material 1', 'Supplier': 'Supplier A', 'Manufacturer': 'Manufacturer X', 'Status': 'Approved' },
//         { 'Raw Material': 'Material 2', 'Supplier': 'Supplier B', 'Manufacturer': 'Manufacturer Y', 'Status': 'Pending' },
//         // Add more rows with actual data from your SQL query
//     ];

//     $.each(sample_data, function(index, row_data) {
// 		if (index === 0 || row_data['Query Type'] !== sample_data[index - 1]['Query Type']) {
// 			// Add a row to categorize the report by query type
// 			var category_row = $('<tr>').appendTo(tbody);
// 			category_row.css('line-height', '0px'); // Reduce line height for spacing
// 			var category_cell = $('<td>').attr('colspan', headers.length).addClass('table-primary').css('background-color', '#b8daff').appendTo(category_row);
// 			$('<h3>').text('Query Type: ' + row_data['Query Type']).appendTo(category_cell);
// 		}
	
// 		// Add the regular data row
// 		var data_row = $('<tr>').appendTo(tbody);
// 		$.each(headers, function(index, header) {
// 			$('<td>').text(row_data[header]).appendTo(data_row);
// 		});
// 	});
// 	var footer_section = $('<div>').addClass('footer-section').appendTo(page.body);
// $('<span>').text('Page ').appendTo(footer_section);
// var page_number_span = $('<span>').addClass('page-number').appendTo(footer_section);
// $('<hr>').appendTo(footer_section);

// // Add CSS for page breaks and header/footer display
// // Add CSS for page breaks and header/footer display
// frappe.dom.freeze(__('Loading...'), 1);
// $("<style>")
//     .prop("type", "text/css")
//     .html(
//         `@page {
//             size: A4 portrait;
//             margin: 1cm;
//             @bottom-right {
//                 content: counter(page);
//             }
//         }
//         @media print {
//             .header-section, .footer-section {
//                 display: block;
//                 position: fixed;
//                 left: 0;
//                 right: 0;
//             }
//             .footer-section {
//                 bottom: 0;
//                 text-align: right;
//                 border-top: 1px solid #ccc;
//                 padding-top: 5px;
//             }
//             .page-number:after {
//                 content: counter(page);
//             }
//             table {
//                 page-break-inside: auto;
//             }
//             tr {
//                 page-break-inside: avoid;
//                 page-break-after: auto;
//             }
//             thead {
//                 display: table-header-group;
//             }
//             tbody {
//                 display: table-row-group;
//             }
//             .header-section, .footer-section {
//                 visibility: visible;
//             }
//             .header-section:not(:first-of-type), .footer-section:not(:first-of-type) {
//                 display: none;
//             }
//         }`
//     )
//     .appendTo("head");

// // Add page numbers
// var totalPages = $("table").length;
// $(".page-number").text("1 / " + totalPages);
// $(".table").each(function(index) {
//     if (index !== 0) {
//         $(this).find("tbody tr:first").before('<tr style="line-height: 0px;"><td colspan="10" class="table-primary" style="background-color: #b8daff;"> <h3>Query Type: Type ' + index + '</h3> </td></tr>');
//     }
// });

// frappe.dom.unfreeze();

// $('<hr>').appendTo(page.body);
// var footer_section = $('<div>').addClass('footer-section').appendTo(page.body).css({
//     'text-align': 'left'
// });

// // Add company address
// $('<p>').html('<strong>Sanha Halal AssociatesPakistan PVT. LTD.</strong> Suite 103, 2nd Floor, Plot 11-C, Lane 9, Zamzama D.H.A. phase 5<br>Email: evaluation@sanha.org.pk - Ph: +92 21 35295263').appendTo(footer_section);



// };

// frappe.pages['cr-report'].on_page_load = function(wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Reports',
//         single_column: true
//     });

//     // Header section
//     var header_section = $('<div>').addClass('header-section').appendTo(page.body);

//     // Center part of the header - company logo
//     var center_header = $('<div>').appendTo(header_section).css({
//         'flex': '1',
//         'text-align': 'center'
//     });
//     $('<img>').attr('src', 'http://portal.sanha.org.pk/assets/dist/img/sanha-logo.png').addClass('img').css({
//         'width': 'auto',
//         'height': '95px'
//     }).appendTo(center_header);

//     // Add HR element below the header
//     $('<hr>').appendTo(page.body);

//     // Section with owner's full name and code
//     var owner_section = $('<div>').addClass('owner-section').appendTo(page.body).css({
//         'text-align': 'center'
//     });
//     $('<strong>').text('Name: John Doe').appendTo(owner_section); // Dummy data for owner's full name, replace with actual data from location field
//     $('<span>').text(' | ').appendTo(owner_section); // Separator (you can change this to any other character)
//     $('<strong>').text('Code: ABC123').appendTo(owner_section); // Dummy data for owner's code, replace with actual data

//     // Add HR element below the owner section
//     $('<hr>').appendTo(page.body);

//     // Right part of the header - company tagline
//     var right_header = $('<div>').appendTo(header_section).css({
//         'flex': '1',
//         'text-align': 'right'
//     });
//     $('<span>').text('Eat Halal, Be Healthy.').appendTo(right_header);
// };



// frappe.pages['cr-report'].on_page_load = function(wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Reports',
//         single_column: true
//     });

//     // Add header section
//     var header_section = $('<div>').addClass('header-section').appendTo(page.body);
//     $('<h1>').text('Report Header').appendTo(header_section); // Add a heading for the header section
//     $('<p>').text('This is the header section of the report page. Add any relevant information here.').appendTo(header_section); // Add description or other elements as needed

//     // Add print button
//     var print_button = $('<button>').text('Print Report').addClass('btn btn-primary').appendTo(page.body);
//     print_button.on('click', function() {
//         // Handle print button click event
//         // You can add logic here to trigger printing functionality
//         // For example, you can call a function to generate and format the report for printing
//         frappe.msgprint('Printing functionality will be implemented here.');
//     });

//     // Add table
//     var table = $('<table>').addClass('table table-bordered').appendTo(page.body);
//     var thead = $('<thead>').appendTo(table);
//     var tbody = $('<tbody>').appendTo(table);

//     // Add table header row
//     var headerRow = $('<tr>').appendTo(thead);
//     $('<th>').text('#').appendTo(headerRow);
//     $('<th>').text('Raw Material').appendTo(headerRow);
//     $('<th>').text('RM. Type').appendTo(headerRow);
//     $('<th>').text('Supplier').appendTo(headerRow);
//     $('<th>').text('Supplier Code').appendTo(headerRow);
//     $('<th>').text('Supplier Contact').appendTo(headerRow);
//     $('<th>').text('Manufacturer').appendTo(headerRow);
//     $('<th>').text('Manufacturer Contact').appendTo(headerRow);
//     $('<th>').text('Status').appendTo(headerRow);
//     $('<th>').text('Remarks').appendTo(headerRow);

//     // Populate table with data
//     // Replace this with your actual data fetching logic
//     var data = [
//         { id: 1, raw_material: 'yuyrtyr', rm_type: 'jkljkl;', supplier: 'sdfg', supplier_code: 'uioui', supplier_contact: 'nmb', manufacturer: 'wqerwer', manufacturer_contact: 'vcbfgh', status: 'Halal', remarks: '.' },
//         // Add more data rows as needed
//     ];

//     // Add data rows to the table body
//     $.each(data, function(index, row) {
//         var tableRow = $('<tr>').appendTo(tbody);
//         $('<td>').text(row.id).appendTo(tableRow);
//         $('<td>').text(row.raw_material).appendTo(tableRow);
//         $('<td>').text(row.rm_type).appendTo(tableRow);
//         $('<td>').text(row.supplier).appendTo(tableRow);
//         $('<td>').text(row.supplier_code).appendTo(tableRow);
//         $('<td>').text(row.supplier_contact).appendTo(tableRow);
//         $('<td>').text(row.manufacturer).appendTo(tableRow);
//         $('<td>').text(row.manufacturer_contact).appendTo(tableRow);
//         $('<td>').text(row.status).appendTo(tableRow);
//         $('<td>').text(row.remarks).appendTo(tableRow);
//     });

//     // Add a container to display the report content
//     $(wrapper).append('<div class="report-container"></div>');
// };

// frappe.pages['cr-report'].on_page_load = function(wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Reports',
//         single_column: true
//     });

//     // Add header section
//     var header_section = $('<div>').addClass('header-section').appendTo(page.body);
//     $('<h1>').text('Report Header').appendTo(header_section); // Add a heading for the header section
//     $('<p>').text('This is the header section of the report page. Add any relevant information here.').appendTo(header_section); // Add description or other elements as needed

//     // Add print button
//     var print_button = $('<button>').text('Print Report').addClass('btn btn-primary').appendTo(page.body);
//     print_button.on('click', function() {
//         // Handle print button click event
//         // You can add logic here to trigger printing functionality
//         // For example, you can call a function to generate and format the report for printing
//         frappe.msgprint('Printing functionality will be implemented here.');
//     });

//     // Add a container to display the report content
//     $(wrapper).append('<div class="report-container"></div>');
// };