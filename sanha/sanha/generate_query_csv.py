import csv

def generate_csv(query_type):
    columns = ['Query Types', 'Raw Material', 'Supplier', 'Supplier Contact', 'Manufacturer', 'Manufacturer Contact']
    
    # Generate rows based on the selected query type
    rows = []
    for column in columns:
        if column == 'Query Types':
            rows.append(query_type)
        else:
            rows.append('')  # Empty string for other columns
    
    # Write data to CSV file
    with open(f'{query_type}_query.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerow(rows)
