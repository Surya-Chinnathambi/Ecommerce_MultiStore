"""
Frontend Connection Test Script
Tests frontend-backend integration and all API connections
"""
import requests
import json
from typing import Dict, List
from datetime import datetime


class FrontendBackendTester:
    def __init__(self, backend_url: str = "http://localhost:8000", frontend_url: str = "http://localhost:3000"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.passed = 0
        self.failed = 0
    
    def print_result(self, test_name: str, passed: bool, details: str = ""):
        """Print test result with formatting"""
        status = "✓ PASS" if passed else "✗ FAIL"
        color = "\033[92m" if passed else "\033[91m"
        print(f"{color}{status}\033[0m | {test_name}")
        if details:
            print(f"       → {details}")
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def test_backend_availability(self):
        """Test if backend is running"""
        print("\n" + "="*70)
        print("BACKEND AVAILABILITY TESTS")
        print("="*70)
        
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            self.print_result(
                "Backend Health Check",
                response.status_code == 200,
                f"Backend is running at {self.backend_url}"
            )
            return True
        except requests.exceptions.ConnectionError:
            self.print_result(
                "Backend Health Check",
                False,
                f"Cannot connect to backend at {self.backend_url}"
            )
            return False
        except Exception as e:
            self.print_result("Backend Health Check", False, str(e))
            return False
    
    def test_frontend_availability(self):
        """Test if frontend is running"""
        print("\n" + "="*70)
        print("FRONTEND AVAILABILITY TESTS")
        print("="*70)
        
        try:
            response = requests.get(self.frontend_url, timeout=5)
            self.print_result(
                "Frontend Server",
                response.status_code == 200,
                f"Frontend is running at {self.frontend_url}"
            )
            return True
        except requests.exceptions.ConnectionError:
            self.print_result(
                "Frontend Server",
                False,
                f"Cannot connect to frontend at {self.frontend_url}"
            )
            return False
        except Exception as e:
            self.print_result("Frontend Server", False, str(e))
            return False
    
    def test_cors_configuration(self):
        """Test CORS headers"""
        print("\n" + "="*70)
        print("CORS CONFIGURATION TESTS")
        print("="*70)
        
        try:
            headers = {
                "Origin": self.frontend_url,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            }
            
            response = requests.options(
                f"{self.backend_url}/api/v1/products",
                headers=headers,
                timeout=5
            )
            
            cors_allowed = "access-control-allow-origin" in response.headers
            self.print_result(
                "CORS Headers Present",
                cors_allowed,
                "Frontend can make cross-origin requests" if cors_allowed else "CORS not configured"
            )
            
        except Exception as e:
            self.print_result("CORS Configuration", False, str(e))
    
    def test_api_endpoints_from_frontend(self):
        """Test all API endpoints that frontend uses"""
        print("\n" + "="*70)
        print("FRONTEND-BACKEND INTEGRATION TESTS")
        print("="*70)
        
        # Simulate frontend API calls
        endpoints = [
            ("GET", "/api/v1/products", {}, "Products List"),
            ("GET", "/api/v1/products", {"search": "rice"}, "Product Search"),
            ("GET", "/api/v1/storefront/featured-products", {}, "Featured Products"),
            ("GET", "/api/v1/storefront/categories", {}, "Categories List"),
            ("GET", "/api/v1/stores", {}, "Stores List"),
        ]
        
        for method, endpoint, params, name in endpoints:
            try:
                url = f"{self.backend_url}{endpoint}"
                if method == "GET":
                    response = requests.get(url, params=params, timeout=10)
                
                self.print_result(
                    name,
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
            except Exception as e:
                self.print_result(name, False, str(e))
    
    def test_authentication_flow(self):
        """Test complete authentication flow"""
        print("\n" + "="*70)
        print("AUTHENTICATION FLOW TESTS")
        print("="*70)
        
        # Test login endpoint (as frontend would)
        try:
            login_data = {
                "email": "admin@test.com",
                "password": "admin123"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/v1/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                self.print_result(
                    "Login Endpoint",
                    token is not None,
                    f"Token received: {token[:20]}..." if token else "No token"
                )
                
                # Test authenticated request
                if token:
                    headers = {"Authorization": f"Bearer {token}"}
                    profile_response = requests.get(
                        f"{self.backend_url}/api/v1/auth/profile",
                        headers=headers,
                        timeout=10
                    )
                    
                    self.print_result(
                        "Authenticated Request (Profile)",
                        profile_response.status_code == 200,
                        "Token authentication working"
                    )
            else:
                self.print_result("Login Endpoint", False, f"Status: {response.status_code}")
        
        except Exception as e:
            self.print_result("Authentication Flow", False, str(e))
    
    def test_data_flow(self):
        """Test data consistency between frontend and backend"""
        print("\n" + "="*70)
        print("DATA FLOW TESTS")
        print("="*70)
        
        try:
            # Get products from backend
            response = requests.get(
                f"{self.backend_url}/api/v1/products",
                params={"page": 1, "page_size": 5},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("data", {}).get("items", [])
                
                self.print_result(
                    "Product Data Structure",
                    len(products) > 0,
                    f"Received {len(products)} products with proper structure"
                )
                
                # Validate product schema
                if products:
                    product = products[0]
                    required_fields = ["id", "name", "selling_price", "mrp", "quantity"]
                    has_all_fields = all(field in product for field in required_fields)
                    
                    self.print_result(
                        "Product Schema Validation",
                        has_all_fields,
                        f"All required fields present: {', '.join(required_fields)}"
                    )
            else:
                self.print_result("Product Data Structure", False, f"Status: {response.status_code}")
        
        except Exception as e:
            self.print_result("Data Flow", False, str(e))
    
    def test_response_times(self):
        """Test API response times"""
        print("\n" + "="*70)
        print("PERFORMANCE TESTS")
        print("="*70)
        
        import time
        
        endpoints = [
            "/health",
            "/api/v1/products",
            "/api/v1/storefront/featured-products",
        ]
        
        for endpoint in endpoints:
            try:
                start = time.time()
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                duration = (time.time() - start) * 1000
                
                # Good: <200ms, Acceptable: <500ms, Slow: >500ms
                passed = duration < 500
                status = "FAST" if duration < 200 else "OK" if duration < 500 else "SLOW"
                
                self.print_result(
                    f"Response Time: {endpoint}",
                    passed,
                    f"{duration:.0f}ms ({status})"
                )
            except Exception as e:
                self.print_result(f"Response Time: {endpoint}", False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"\033[92mPassed: {self.passed}\033[0m")
        print(f"\033[91mFailed: {self.failed}\033[0m")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n" + "="*70)
        if success_rate == 100:
            print("\033[92m✓ ALL SYSTEMS OPERATIONAL\033[0m")
        elif success_rate >= 80:
            print("\033[93m⚠ SYSTEM OPERATIONAL WITH WARNINGS\033[0m")
        else:
            print("\033[91m✗ SYSTEM NEEDS ATTENTION\033[0m")
        print("="*70 + "\n")
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*70)
        print("E-COMMERCE PLATFORM - INTEGRATION TESTS")
        print("Frontend-Backend Connection Validation")
        print("="*70)
        print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Backend:  {self.backend_url}")
        print(f"Frontend: {self.frontend_url}")
        
        backend_up = self.test_backend_availability()
        frontend_up = self.test_frontend_availability()
        
        if backend_up:
            self.test_cors_configuration()
            self.test_api_endpoints_from_frontend()
            self.test_authentication_flow()
            self.test_data_flow()
            self.test_response_times()
        else:
            print("\n⚠ Skipping remaining tests - backend not available")
        
        self.print_summary()


def main():
    """Main entry point"""
    tester = FrontendBackendTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
