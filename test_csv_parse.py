import csv
import io

content = open('grocery_store_products.csv').read()
reader = csv.DictReader(io.StringIO(content))
row = next(reader)

print(f"Headers: {list(row.keys())}")
print(f"First row SKU: [{row.get('SKU')}]")
print(f"First row Product Name: [{row.get('Product Name')}]")

# Test the mapping
default_mapping = {
    'SKU': 'sku',
    'Product Name': 'name',
    'Description': 'description',
    'Price': 'price',
    'Cost': 'cost',
    'Quantity': 'quantity',
    'Category': 'category',
    'Brand': 'brand'
}

product = {}
for csv_col, sys_field in default_mapping.items():
    if csv_col in row:
        value = row[csv_col].strip()
        print(f"{csv_col} -> {sys_field}: [{value}]")
        product[sys_field] = value
    else:
        print(f"{csv_col} NOT FOUND in row")

print(f"\nFinal product dict: {product}")
