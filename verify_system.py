"""
Real-Time System Verification Script
Tests all critical endpoints to ensure system is working
"""
import requests
import json

API_BASE = "http://localhost:8000/api/v1"
STORE_ID = "a8e00641-d794-4ae1-a8c0-6bd2bd8fee2a"

def test_endpoint(name, method, url, **kwargs):
    """Test an endpoint and print results"""
    try:
        if method == "GET":
            response = requests.get(url, **kwargs)
        else:
            response = requests.post(url, **kwargs)
        
        status = "✅" if response.status_code < 400 else "❌"
        print(f"{status} {name}: {response.status_code}")
        if response.status_code >= 400:
            print(f"   Error: {response.text[:100]}")
        return response.status_code < 400
    except Exception as e:
        print(f"❌ {name}: ERROR - {str(e)}")
        return False

print("=" * 60)
print("REAL-TIME SYSTEM VERIFICATION")
print("=" * 60)

results = {}

# Test storefront endpoints
print("\n📦 STOREFRONT ENDPOINTS:")
results['store_info'] = test_endpoint(
    "Store Info", "GET",
    f"{API_BASE}/storefront/store-info?store_id={STORE_ID}"
)

results['products'] = test_endpoint(
    "Products List", "GET",
    f"{API_BASE}/storefront/products?store_id={STORE_ID}&page=1&per_page=5"
)

results['categories'] = test_endpoint(
    "Categories", "GET",
    f"{API_BASE}/storefront/categories?store_id={STORE_ID}"
)

results['featured'] = test_endpoint(
    "Featured Products", "GET",
    f"{API_BASE}/storefront/featured-products?store_id={STORE_ID}&limit=5"
)

# Test marketing endpoints
print("\n🎯 MARKETING ENDPOINTS:")
results['social_proof'] = test_endpoint(
    "Social Proof", "GET",
    f"{API_BASE}/marketing/social-proof/recent?limit=10&store_id={STORE_ID}"
)

results['banners'] = test_endpoint(
    "Marketing Banners", "GET",
    f"{API_BASE}/marketing/banners?banner_type=hero&store_id={STORE_ID}"
)

results['flash_sales'] = test_endpoint(
    "Flash Sales", "GET",
    f"{API_BASE}/marketing/flash-sales?active_only=true&store_id={STORE_ID}"
)

# Test auth endpoints
print("\n🔐 AUTH ENDPOINTS:")
results['login'] = test_endpoint(
    "Login", "POST",
    f"{API_BASE}/auth/login",
    json={"email": "admin@test.com", "password": "admin123"}
)

# Test health
print("\n💚 HEALTH CHECK:")
results['health'] = test_endpoint(
    "Health Check", "GET",
    "http://localhost:8000/health"
)

# Summary
print("\n" + "=" * 60)
print("SUMMARY:")
print("=" * 60)
passed = sum(1 for v in results.values() if v)
total = len(results)
print(f"✅ Passed: {passed}/{total}")
print(f"❌ Failed: {total - passed}/{total}")

if passed == total:
    print("\n🎉 ALL SYSTEMS OPERATIONAL!")
else:
    print("\n⚠️  Some endpoints need attention")
    failed = [k for k, v in results.items() if not v]
    print(f"Failed endpoints: {', '.join(failed)}")

print("\n" + "=" * 60)
