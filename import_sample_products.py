"""
Import sample products from CSV file
"""
import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
CSV_FILE = "grocery_store_products.csv"

def login_admin():
    """Login as admin to get token"""
    print("🔐 Logging in as admin...")
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": "admin@test.com",
            "password": "admin123"
        }
    )
    
    if response.status_code == 200:
        token = response.json()['access_token']
        print("✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None

def import_products_csv(token):
    """Import products from CSV file"""
    print(f"\n📦 Importing products from {CSV_FILE}...")
    
    with open(CSV_FILE, 'rb') as f:
        files = {'file': (CSV_FILE, f, 'text/csv')}
        data = {
            'entity_type': 'product',
            'auto_create': 'true',
            'update_existing': 'true'
        }
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.post(
            f"{API_BASE_URL}/billing/import/csv",
            files=files,
            data=data,
            headers=headers
        )
    
    if response.status_code in [200, 201]:
        result = response.json()
        print("\n✅ Import completed successfully!")
        print(f"   Total rows: {result['total_rows']}")
        print(f"   Processed: {result['processed']}")
        print(f"   Succeeded: {result['succeeded']}")
        print(f"   Failed: {result['failed']}")
        print(f"   Skipped: {result['skipped']}")
        
        if result.get('errors'):
            print("\n⚠️  Errors:")
            for error in result['errors'][:5]:  # Show first 5 errors
                if isinstance(error, dict):
                    print(f"   {error}")
                else:
                    print(f"   {error}")
        
        if result.get('created_ids'):
            print(f"\n✨ Created {len(result['created_ids'])} new products")
        
        if result.get('updated_ids'):
            print(f"📝 Updated {len(result['updated_ids'])} existing products")
        
        return result
    else:
        print(f"\n❌ Import failed: {response.status_code}")
        print(response.text)
        return None

def verify_products(token):
    """Verify products were imported"""
    print("\n🔍 Verifying imported products...")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f"{API_BASE_URL}/products",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # Handle both list and dict responses
        if isinstance(data, dict):
            products = data.get('products', data.get('data', []))
        else:
            products = data
        
        print(f"✅ Found {len(products)} total products in store")
        
        # Show a few sample products
        if products and isinstance(products, list) and len(products) > 0:
            print("\n📋 Sample products:")
            for product in products[:5]:
                name = product.get('name', 'N/A')
                price = product.get('selling_price', product.get('price', 'N/A'))
                stock = product.get('quantity', product.get('stock_quantity', 'N/A'))
                print(f"   • {name} - ${price} (Stock: {stock})")
        
        return products
    else:
        print(f"❌ Failed to fetch products: {response.status_code}")
        return []

def main():
    print("="*60)
    print("🧪 Product CSV Import Test")
    print("="*60)
    
    # Step 1: Login
    token = login_admin()
    if not token:
        return
    
    # Step 2: Import products from CSV
    result = import_products_csv(token)
    if not result:
        return
    
    # Step 3: Verify products
    products = verify_products(token)
    
    print("\n" + "="*60)
    print("✨ Import Process Complete!")
    print("="*60)
    print("\n📊 Summary:")
    print(f"   CSV File: {CSV_FILE}")
    print(f"   Products Imported: {result['succeeded']}")
    print(f"   Total Products in Store: {len(products) if products else 'N/A'}")
    print("\n🛍️  Customers can now purchase these products!")
    print("   Access storefront at: http://localhost:3000/products")
    print()

if __name__ == "__main__":
    main()
