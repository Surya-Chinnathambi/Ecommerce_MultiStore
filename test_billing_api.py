"""
Test script for Billing Integration API
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
BILLING_URL = f"{BASE_URL}/billing"

# Colors for terminal output
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_info(message):
    print(f"{BLUE}ℹ️  {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠️  {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def test_get_providers():
    """Test getting list of supported providers"""
    print_info("Testing GET /billing/providers")
    try:
        response = requests.get(f"{BILLING_URL}/providers")
        if response.status_code == 200:
            data = response.json()
            providers = data.get('providers', [])
            print_success(f"Found {len(providers)} supported providers:")
            for provider in providers:
                oauth_status = "OAuth2" if provider.get('requires_oauth') else "API Key/Direct"
                print(f"  • {provider['name']} ({provider['id']}) - {oauth_status}")
                print(f"    Features: {', '.join(provider.get('features', []))}")
            return True
        else:
            print_error(f"Failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False

def test_list_integrations():
    """Test listing integrations (should be empty initially)"""
    print_info("\nTesting GET /billing/integrations")
    try:
        # Login first to get admin token
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": "admin@test.com", "password": "admin123"}
        )
        
        if login_response.status_code != 200:
            print_warning("Login failed - some tests require authentication")
            return False
            
        token = login_response.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BILLING_URL}/integrations", headers=headers)
        if response.status_code == 200:
            integrations = response.json()
            print_success(f"Found {len(integrations)} integrations")
            if len(integrations) == 0:
                print_info("  No integrations configured yet (expected for new setup)")
            else:
                for integration in integrations:
                    print(f"  • {integration['name']} ({integration['provider']})")
            return True, headers
        else:
            print_error(f"Failed with status {response.status_code}")
            return False, None
    except Exception as e:
        print_error(f"Exception: {e}")
        return False, None

def test_create_csv_integration(headers):
    """Test creating a CSV integration"""
    print_info("\nTesting POST /billing/integrations (CSV provider)")
    try:
        integration_data = {
            "name": "Test CSV Export",
            "provider": "csv_excel",
            "config": {},
            "auto_sync": False,
            "sync_direction": "push",
            "sync_entities": ["invoice", "product"],
            "is_active": True
        }
        
        response = requests.post(
            f"{BILLING_URL}/integrations",
            json=integration_data,
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print_success(f"Created integration: {data['name']} (ID: {data['id']})")
            return data['id']
        else:
            print_error(f"Failed with status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print_error(f"Exception: {e}")
        return None

def test_connection_test(headers):
    """Test connection testing"""
    print_info("\nTesting POST /billing/test-connection")
    try:
        test_data = {
            "provider": "csv_excel",
            "config": {}
        }
        
        response = requests.post(
            f"{BILLING_URL}/test-connection",
            json=test_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print_success(f"Connection test passed: {result['message']}")
            else:
                print_warning(f"Connection test failed: {result.get('error', 'Unknown error')}")
            return True
        else:
            print_error(f"Failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False

def test_download_sample_csv(headers):
    """Test downloading sample CSV"""
    print_info("\nTesting GET /billing/sample-csv/product")
    try:
        response = requests.get(
            f"{BILLING_URL}/sample-csv/product",
            headers=headers
        )
        
        if response.status_code == 200:
            content = response.text
            lines = content.strip().split('\n')
            print_success(f"Downloaded sample CSV ({len(lines)} lines)")
            print(f"  Header: {lines[0][:80]}..." if len(lines[0]) > 80 else f"  Header: {lines[0]}")
            if len(lines) > 1:
                print(f"  Sample row: {lines[1][:80]}..." if len(lines[1]) > 80 else f"  Sample row: {lines[1]}")
            return True
        else:
            print_error(f"Failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False

def test_get_sync_logs(integration_id, headers):
    """Test getting sync logs"""
    print_info(f"\nTesting GET /billing/integrations/{integration_id}/sync-logs")
    try:
        response = requests.get(
            f"{BILLING_URL}/integrations/{integration_id}/sync-logs",
            headers=headers,
            params={"limit": 10}
        )
        
        if response.status_code == 200:
            logs = response.json()
            print_success(f"Retrieved {len(logs)} sync logs")
            if len(logs) == 0:
                print_info("  No sync operations yet (expected for new integration)")
            return True
        else:
            print_error(f"Failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🧪 Billing Integration API Test Suite")
    print("="*60 + "\n")
    
    # Test 1: Get providers (public endpoint)
    test_get_providers()
    
    # Test 2: List integrations (requires auth)
    result = test_list_integrations()
    if isinstance(result, tuple):
        success, headers = result
        if not success:
            print_warning("\nSome tests skipped due to authentication failure")
            return
    else:
        print_warning("\nTests require admin authentication")
        return
    
    # Test 3: Connection test
    test_connection_test(headers)
    
    # Test 4: Download sample CSV
    test_download_sample_csv(headers)
    
    # Test 5: Create CSV integration
    integration_id = test_create_csv_integration(headers)
    
    # Test 6: Get sync logs
    if integration_id:
        test_get_sync_logs(integration_id, headers)
    
    print("\n" + "="*60)
    print_success("✨ Billing Integration API Test Complete!")
    print("="*60 + "\n")
    
    print_info("Next steps:")
    print("  1. Create integrations via API or UI")
    print("  2. Test CSV export: POST /billing/export/csv")
    print("  3. Test CSV import: POST /billing/import/csv")
    print("  4. Configure OAuth for cloud providers (QuickBooks, Xero)")
    print("  5. Set up auto-sync schedules")
    print()

if __name__ == "__main__":
    main()
