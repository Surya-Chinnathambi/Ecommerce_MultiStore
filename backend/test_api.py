"""
Comprehensive API Testing Script
Tests all backend endpoints with authentication, database, and Redis connectivity
"""
import requests
import json
from typing import Dict, Optional
import time
from datetime import datetime


class Colors:
    """Terminal colors for output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    def print_test(self, name: str, passed: bool, details: str = ""):
        """Print test result"""
        if passed:
            print(f"{Colors.OKGREEN}✓ {name}{Colors.ENDC}")
            if details:
                print(f"  {Colors.OKCYAN}{details}{Colors.ENDC}")
            self.test_results["passed"] += 1
        else:
            print(f"{Colors.FAIL}✗ {name}{Colors.ENDC}")
            if details:
                print(f"  {Colors.WARNING}{details}{Colors.ENDC}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append({"test": name, "error": details})
    
    def test_health_check(self):
        """Test health endpoint"""
        self.print_header("HEALTH CHECK")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            data = response.json()
            
            self.print_test(
                "Health Endpoint",
                response.status_code == 200,
                f"Status: {data.get('status')}, DB: {data.get('database')}, Redis: {data.get('redis')}"
            )
            
            # Check individual components
            self.print_test(
                "Database Connection",
                data.get("database") == "connected",
                "PostgreSQL is accessible"
            )
            
            self.print_test(
                "Redis Connection",
                data.get("redis") == "connected",
                "Redis cache is accessible"
            )
            
        except Exception as e:
            self.print_test("Health Endpoint", False, str(e))
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            data = response.json()
            
            self.print_test(
                "Root Endpoint",
                response.status_code == 200 and "name" in data,
                f"API: {data.get('name')}, Version: {data.get('version')}"
            )
        except Exception as e:
            self.print_test("Root Endpoint", False, str(e))
    
    def test_authentication(self):
        """Test authentication endpoints"""
        self.print_header("AUTHENTICATION TESTS")
        
        # Test user registration
        try:
            timestamp = int(time.time())
            register_data = {
                "email": f"test_{timestamp}@example.com",
                "phone": f"98765{timestamp % 100000}",
                "password": "Test123!@#",
                "full_name": "Test User"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/auth/register",
                json=register_data,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                self.token = data.get("access_token")
                self.print_test(
                    "User Registration",
                    True,
                    f"User created: {register_data['email']}"
                )
            else:
                self.print_test(
                    "User Registration",
                    False,
                    f"Status: {response.status_code}, {response.text}"
                )
        except Exception as e:
            self.print_test("User Registration", False, str(e))
        
        # Test login with existing user
        try:
            login_data = {
                "email": "admin@test.com",
                "password": "admin123"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                user_info = data.get("user", {})
                self.print_test(
                    "User Login",
                    True,
                    f"Logged in as: {user_info.get('email')} (Role: {user_info.get('role')})"
                )
            else:
                self.print_test(
                    "User Login",
                    False,
                    f"Status: {response.status_code}, {response.text}"
                )
        except Exception as e:
            self.print_test("User Login", False, str(e))
        
        # Test protected endpoint (profile)
        if self.token:
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.get(
                    f"{self.base_url}/api/v1/auth/profile",
                    headers=headers,
                    timeout=10
                )
                
                self.print_test(
                    "Protected Endpoint (Profile)",
                    response.status_code == 200,
                    f"Token authentication working"
                )
            except Exception as e:
                self.print_test("Protected Endpoint (Profile)", False, str(e))
    
    def test_products_api(self):
        """Test products endpoints"""
        self.print_header("PRODUCTS API TESTS")
        
        # Test list products
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/products",
                params={"page": 1, "page_size": 10},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("data", {}).get("total", 0)
                items = len(data.get("data", {}).get("items", []))
                self.print_test(
                    "List Products",
                    True,
                    f"Found {total} products, showing {items}"
                )
            else:
                self.print_test(
                    "List Products",
                    False,
                    f"Status: {response.status_code}"
                )
        except Exception as e:
            self.print_test("List Products", False, str(e))
        
        # Test product search
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/products",
                params={"search": "rice"},
                timeout=10
            )
            
            self.print_test(
                "Product Search",
                response.status_code == 200,
                "Search functionality working"
            )
        except Exception as e:
            self.print_test("Product Search", False, str(e))
        
        # Test product filtering
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/products",
                params={"min_price": 100, "max_price": 500},
                timeout=10
            )
            
            self.print_test(
                "Product Filtering",
                response.status_code == 200,
                "Price range filtering working"
            )
        except Exception as e:
            self.print_test("Product Filtering", False, str(e))
    
    def test_stores_api(self):
        """Test stores endpoints"""
        self.print_header("STORES API TESTS")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/stores",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                stores = data.get("data", [])
                self.print_test(
                    "List Stores",
                    True,
                    f"Found {len(stores)} store(s)"
                )
            else:
                self.print_test(
                    "List Stores",
                    False,
                    f"Status: {response.status_code}"
                )
        except Exception as e:
            self.print_test("List Stores", False, str(e))
    
    def test_orders_api(self):
        """Test orders endpoints"""
        self.print_header("ORDERS API TESTS")
        
        if not self.token:
            self.print_test("Orders API", False, "No authentication token available")
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test list orders
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/orders",
                headers=headers,
                timeout=10
            )
            
            self.print_test(
                "List Orders",
                response.status_code == 200,
                "Orders retrieval working"
            )
        except Exception as e:
            self.print_test("List Orders", False, str(e))
    
    def test_storefront_api(self):
        """Test storefront endpoints"""
        self.print_header("STOREFRONT API TESTS")
        
        # Test featured products
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/storefront/featured-products",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                count = len(data.get("data", []))
                self.print_test(
                    "Featured Products",
                    True,
                    f"Found {count} featured product(s)"
                )
            else:
                self.print_test(
                    "Featured Products",
                    False,
                    f"Status: {response.status_code}"
                )
        except Exception as e:
            self.print_test("Featured Products", False, str(e))
        
        # Test categories
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/storefront/categories",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                count = len(data.get("data", []))
                self.print_test(
                    "Categories",
                    True,
                    f"Found {count} categor(ies)"
                )
            else:
                self.print_test(
                    "Categories",
                    False,
                    f"Status: {response.status_code}"
                )
        except Exception as e:
            self.print_test("Categories", False, str(e))
    
    def test_performance(self):
        """Test API performance"""
        self.print_header("PERFORMANCE TESTS")
        
        endpoints = [
            ("/health", "Health Check"),
            ("/api/v1/products", "Products List"),
            ("/api/v1/storefront/featured-products", "Featured Products"),
        ]
        
        for endpoint, name in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                duration = (time.time() - start_time) * 1000  # Convert to ms
                
                # Performance threshold: < 500ms
                passed = response.status_code == 200 and duration < 500
                
                self.print_test(
                    f"{name} Response Time",
                    passed,
                    f"{duration:.2f}ms {'(GOOD)' if duration < 200 else '(ACCEPTABLE)' if duration < 500 else '(SLOW)'}"
                )
            except Exception as e:
                self.print_test(f"{name} Response Time", False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        total = self.test_results["passed"] + self.test_results["failed"]
        passed_pct = (self.test_results["passed"] / total * 100) if total > 0 else 0
        
        print(f"{Colors.BOLD}Total Tests: {total}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}Passed: {self.test_results['passed']}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {self.test_results['failed']}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Success Rate: {passed_pct:.1f}%{Colors.ENDC}")
        
        if self.test_results["errors"]:
            print(f"\n{Colors.WARNING}Failed Tests:{Colors.ENDC}")
            for error in self.test_results["errors"]:
                print(f"  • {error['test']}: {error['error']}")
        
        print(f"\n{Colors.BOLD}Overall Status: ", end="")
        if passed_pct == 100:
            print(f"{Colors.OKGREEN}ALL TESTS PASSED ✓{Colors.ENDC}")
        elif passed_pct >= 80:
            print(f"{Colors.WARNING}MOSTLY PASSING ⚠{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}NEEDS ATTENTION ✗{Colors.ENDC}")
        
        print()
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}")
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║     E-COMMERCE PLATFORM - COMPREHENSIVE API TESTS        ║")
        print("║              DevOps Testing & Validation                 ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target: {self.base_url}")
        
        self.test_health_check()
        self.test_root_endpoint()
        self.test_authentication()
        self.test_products_api()
        self.test_stores_api()
        self.test_storefront_api()
        self.test_orders_api()
        self.test_performance()
        
        self.print_summary()


def main():
    """Main entry point"""
    tester = APITester(base_url="http://localhost:8000")
    tester.run_all_tests()


if __name__ == "__main__":
    main()
