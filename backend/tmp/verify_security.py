import requests
import time

BASE_URL = "http://localhost:8000/api/v1"
STORE_ID = "67890000-0000-0000-0000-000000000000"  # Example store ID
HEADERS = {"X-Store-Id": STORE_ID}

def test_jwt_rotation():
    print("Testing JWT Rotation...")
    
    # 1. Login
    login_data = {"username": "admin@example.com", "password": "password123"}
    r = requests.post(f"{BASE_URL}/auth/login", json=login_data, headers=HEADERS)
    if r.status_code != 200:
        print(f"FAILED: Login failed: {r.text}")
        return
    
    tokens = r.json()["data"]
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    print(f"Got initial tokens. Access: {access_token[:10]}... Refresh: {refresh_token[:10]}...")

    # 2. Refresh
    r = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": refresh_token}, headers=HEADERS)
    if r.status_code != 200:
        print(f"FAILED: Refresh failed: {r.text}")
        return
    
    new_tokens = r.json()["data"]
    new_access = new_tokens["access_token"]
    new_refresh = new_tokens["refresh_token"]
    print(f"Got new tokens. Access: {new_access[:10]}... Refresh: {new_refresh[:10]}...")

    # 3. Verify old refresh token is revoked (should fail)
    r = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": refresh_token}, headers=HEADERS)
    if r.status_code == 401:
        print("SUCCESS: Old refresh token rejected as revoked.")
    else:
        print(f"FAILED: Old refresh token should have been rejected (Status: {r.status_code})")

    # 4. Access protected endpoint with new token
    headers = {**HEADERS, "Authorization": f"Bearer {new_access}"}
    r = requests.get(f"{BASE_URL}/stores/dashboard/stats", headers=headers)
    if r.status_code == 200:
        print("SUCCESS: New access token works for protected endpoint.")
    else:
        print(f"FAILED: New access token rejected (Status: {r.status_code})")

    # 5. Logout
    r = requests.post(f"{BASE_URL}/auth/logout", json={"refresh_token": new_refresh}, headers=headers)
    if r.status_code == 200:
        print("SUCCESS: Logout successful.")
    else:
        print(f"FAILED: Logout failed (Status: {r.status_code})")

    # 6. Verify new refresh token is now revoked
    r = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": new_refresh}, headers=HEADERS)
    if r.status_code == 401:
        print("SUCCESS: Refresh token revoked after logout.")
    else:
        print(f"FAILED: Refresh token should be revoked after logout (Status: {r.status_code})")

def test_rbac_cross_store():
    print("\nTesting RBAC Cross-Store isolation...")
    # This requires two stores and an admin belonging to one.
    # We'll assume the setup has these. 
    # For now, let's just test that a random store ID fails if the token is for a specific store.
    pass

if __name__ == "__main__":
    # Ensure server is running
    try:
        test_jwt_rotation()
    except Exception as e:
        print(f"Error during testing: {e}")
