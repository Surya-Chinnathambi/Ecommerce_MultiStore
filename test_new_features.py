"""
Test New Features - Redis Monitoring, Enhanced Search, Performance Metrics
"""
import requests
import time
from datetime import datetime


class NewFeaturesTest:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.passed = 0
        self.failed = 0
    
    def print_result(self, test_name: str, passed: bool, details: str = ""):
        """Print test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")
        if details:
            print(f"      → {details}")
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def login(self):
        """Login and get token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"email": "admin@test.com", "password": "admin123"},
                timeout=10
            )
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                return True
        except:
            pass
        return False
    
    def test_redis_monitoring(self):
        """Test Redis monitoring endpoints"""
        print("\n" + "="*70)
        print("REDIS MONITORING TESTS")
        print("="*70)
        
        # Test Redis health
        try:
            response = requests.get(f"{self.base_url}/api/v1/monitoring/redis/health")
            data = response.json().get("data", {})
            self.print_result(
                "Redis Health Check",
                response.status_code == 200 and data.get("connected"),
                f"Status: {data.get('status')}, Latency: {data.get('latency_ms')}ms"
            )
        except Exception as e:
            self.print_result("Redis Health Check", False, str(e))
        
        # Test Redis stats
        try:
            response = requests.get(f"{self.base_url}/api/v1/monitoring/redis/stats")
            data = response.json().get("data", {})
            self.print_result(
                "Redis Statistics",
                response.status_code == 200 and "version" in data,
                f"Version: {data.get('version')}, Memory: {data.get('used_memory')}"
            )
        except Exception as e:
            self.print_result("Redis Statistics", False, str(e))
        
        # Test cache performance
        try:
            response = requests.get(f"{self.base_url}/api/v1/monitoring/redis/cache-performance")
            data = response.json().get("data", {})
            self.print_result(
                "Cache Performance Metrics",
                response.status_code == 200 and "hit_rate_percent" in data,
                f"Hit Rate: {data.get('hit_rate_percent')}%, Total Requests: {data.get('total_requests')}"
            )
        except Exception as e:
            self.print_result("Cache Performance Metrics", False, str(e))
        
        # Test key statistics
        try:
            response = requests.get(f"{self.base_url}/api/v1/monitoring/redis/keys")
            data = response.json().get("data", {})
            self.print_result(
                "Redis Key Statistics",
                response.status_code == 200 and "total_keys" in data,
                f"Total Keys: {data.get('total_keys')}"
            )
        except Exception as e:
            self.print_result("Redis Key Statistics", False, str(e))
    
    def test_enhanced_search(self):
        """Test enhanced search features"""
        print("\n" + "="*70)
        print("ENHANCED SEARCH TESTS")
        print("="*70)
        
        # Test search with query
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/search",
                params={"q": "rice"}
            )
            data = response.json().get("data", [])
            self.print_result(
                "Product Search",
                response.status_code == 200 and len(data) > 0,
                f"Found {len(data)} results for 'rice'"
            )
        except Exception as e:
            self.print_result("Product Search", False, str(e))
        
        # Test search suggestions
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/search/suggestions",
                params={"q": "ri"}
            )
            data = response.json().get("data", [])
            self.print_result(
                "Search Suggestions",
                response.status_code == 200 and len(data) > 0,
                f"Got {len(data)} suggestions"
            )
        except Exception as e:
            self.print_result("Search Suggestions", False, str(e))
        
        # Test popular searches
        try:
            response = requests.get(f"{self.base_url}/api/v1/search/popular")
            data = response.json().get("data", [])
            self.print_result(
                "Popular Searches",
                response.status_code == 200 and len(data) > 0,
                f"Found {len(data)} popular terms"
            )
        except Exception as e:
            self.print_result("Popular Searches", False, str(e))
        
        # Test search analytics
        try:
            response = requests.get(f"{self.base_url}/api/v1/search/analytics")
            data = response.json().get("data", {})
            self.print_result(
                "Search Analytics",
                response.status_code == 200 and "total_searches" in data,
                f"Total Searches: {data.get('total_searches')}"
            )
        except Exception as e:
            self.print_result("Search Analytics", False, str(e))
    
    def test_fixed_endpoints(self):
        """Test the 3 endpoints we fixed"""
        print("\n" + "="*70)
        print("FIXED ENDPOINTS TESTS")
        print("="*70)
        
        if not self.login():
            self.print_result("Login for Tests", False, "Could not authenticate")
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test profile endpoint
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/auth/profile",
                headers=headers
            )
            self.print_result(
                "Profile Endpoint (/api/v1/auth/profile)",
                response.status_code == 200,
                "Profile retrieval working"
            )
        except Exception as e:
            self.print_result("Profile Endpoint", False, str(e))
        
        # Test stores list
        try:
            response = requests.get(f"{self.base_url}/api/v1/stores")
            data = response.json().get("data", [])
            self.print_result(
                "Stores List Endpoint (/api/v1/stores)",
                response.status_code == 200 and len(data) > 0,
                f"Found {len(data)} store(s)"
            )
        except Exception as e:
            self.print_result("Stores List Endpoint", False, str(e))
        
        # Test orders list
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/orders",
                headers=headers
            )
            self.print_result(
                "Orders List Endpoint (/api/v1/orders)",
                response.status_code == 200,
                "Orders endpoint accessible"
            )
        except Exception as e:
            self.print_result("Orders List Endpoint", False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n" + "="*70)
        if success_rate == 100:
            print("🎉 ALL NEW FEATURES WORKING PERFECTLY!")
        elif success_rate >= 80:
            print("✓ NEW FEATURES OPERATIONAL")
        else:
            print("⚠ SOME FEATURES NEED ATTENTION")
        print("="*70 + "\n")
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*70)
        print("NEW FEATURES TESTING")
        print("Redis Monitoring + Enhanced Search + Fixed Endpoints")
        print("="*70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target: {self.base_url}")
        
        self.test_fixed_endpoints()
        self.test_redis_monitoring()
        self.test_enhanced_search()
        
        self.print_summary()


def main():
    tester = NewFeaturesTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
