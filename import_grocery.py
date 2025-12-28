"""
Import grocery products using direct file upload
"""
import requests
import sys

API_BASE_URL = "http://localhost:8000/api/v1"
CSV_FILE = "grocery_store_products.csv"

# Login
print("🔐 Logging in...")
response = requests.post(
    f"{API_BASE_URL}/auth/login",
    json={"email": "admin@test.com", "password": "admin123"}
)

if response.status_code != 200:
    print(f"❌ Login failed: {response.status_code}")
    print(response.text)
    sys.exit(1)

token = response.json()['access_token']
print("✅ Logged in successfully")

# Upload CSV
print(f"\n📤 Uploading {CSV_FILE}...")
headers = {"Authorization": f"Bearer {token}"}

with open(CSV_FILE, 'rb') as f:
    files = {'file': (CSV_FILE, f, 'text/csv')}
    params = {
        'entity_type': 'product',
        'update_existing': 'true',
        'auto_create': 'true'
    }
    
    response = requests.post(
        f"{API_BASE_URL}/billing/import/csv",
        headers=headers,
        files=files,
        params=params
    )

if response.status_code == 200:
    data = response.json()
    result = data.get('data', data)  # Handle both formats
    print("\n" + "="*60)
    print("✅ IMPORT SUCCESSFUL!")
    print("="*60)
    print(f"\n📊 Results:")
    print(f"   Total Rows: {result.get('total_rows', 0)}")
    print(f"   ✅ Succeeded: {result.get('succeeded', 0)}")
    print(f"   ❌ Failed: {result.get('failed', 0)}")
    print(f"   ⏭️  Skipped: {result.get('skipped', 0)}")
    print(f"   🆕 Created: {len(result.get('created_ids', []))}")
    print(f"   🔄 Updated: {len(result.get('updated_ids', []))}")
    
    # Debug: Show first few IDs if any
    if result.get('created_ids'):
        print(f"\n   First created IDs: {result['created_ids'][:3]}")
    if result.get('updated_ids'):
        print(f"   First updated IDs: {result['updated_ids'][:3]}")
    
    if result.get('errors'):
        print(f"\n⚠️  Errors ({len(result['errors'])}):")
        for err in result['errors'][:10]:
            print(f"   Row {err['row']}: {err['error']}")
    
    print(f"\n🎉 {result['succeeded']} grocery products imported!")
    print(f"🛒 View at: http://localhost:3000/products")
else:
    print(f"\n❌ Import failed: {response.status_code}")
    print(response.text)
