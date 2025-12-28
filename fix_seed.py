with open('/app/seed_data.py', 'r') as f:
    content = f.read()

content = content.replace('price=product_data["price"],', 'mrp=product_data["price"],
                        selling_price=product_data["price"],')
content = content.replace('quantity=100, external_id=product_data[sku],', 'quantity=100,
                        external_id=product_data["sku"],')

with open('/app/seed_data.py', 'w') as f:
    f.write(content)

print('Fixed')