"""
System Monitoring Dashboard Script
Real-time monitoring of all services
"""
import requests
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List
import os


class SystemMonitor:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.services_status = {}
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def check_backend(self) -> Dict:
        """Check backend service status"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "UP",
                    "response_time": f"{response_time:.0f}ms",
                    "database": data.get("database", "unknown"),
                    "redis": data.get("redis", "unknown"),
                    "color": "\033[92m"  # Green
                }
            else:
                return {
                    "status": "DEGRADED",
                    "response_time": f"{response_time:.0f}ms",
                    "database": "unknown",
                    "redis": "unknown",
                    "color": "\033[93m"  # Yellow
                }
        except Exception as e:
            return {
                "status": "DOWN",
                "response_time": "N/A",
                "database": "unknown",
                "redis": "unknown",
                "error": str(e)[:50],
                "color": "\033[91m"  # Red
            }
    
    def check_frontend(self) -> Dict:
        """Check frontend service status"""
        try:
            start_time = time.time()
            response = requests.get(self.frontend_url, timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return {
                    "status": "UP",
                    "response_time": f"{response_time:.0f}ms",
                    "color": "\033[92m"  # Green
                }
            else:
                return {
                    "status": "DEGRADED",
                    "response_time": f"{response_time:.0f}ms",
                    "color": "\033[93m"  # Yellow
                }
        except Exception as e:
            return {
                "status": "DOWN",
                "response_time": "N/A",
                "error": str(e)[:50],
                "color": "\033[91m"  # Red
            }
    
    def check_docker_services(self) -> Dict:
        """Check Docker containers status"""
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd="C:\\ecommerce-platform"
            )
            
            services = {}
            if result.stdout:
                try:
                    # Parse each line as JSON
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            container = json.loads(line)
                            name = container.get('Service', 'unknown')
                            state = container.get('State', 'unknown')
                            
                            color = "\033[92m" if state == "running" else "\033[91m"
                            services[name] = {
                                "state": state,
                                "color": color
                            }
                except json.JSONDecodeError:
                    pass
            
            return services
        except Exception as e:
            return {"error": str(e)[:50]}
    
    def check_api_endpoints(self) -> List[Dict]:
        """Test critical API endpoints"""
        endpoints = [
            ("/api/v1/products", "Products"),
            ("/api/v1/storefront/featured-products", "Featured"),
            ("/api/v1/storefront/categories", "Categories"),
        ]
        
        results = []
        for endpoint, name in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                response_time = (time.time() - start_time) * 1000
                
                status_ok = response.status_code == 200
                results.append({
                    "name": name,
                    "status": "✓" if status_ok else "✗",
                    "response_time": f"{response_time:.0f}ms",
                    "color": "\033[92m" if status_ok else "\033[91m"
                })
            except Exception:
                results.append({
                    "name": name,
                    "status": "✗",
                    "response_time": "N/A",
                    "color": "\033[91m"
                })
        
        return results
    
    def print_dashboard(self):
        """Print monitoring dashboard"""
        self.clear_screen()
        
        # Header
        print("\033[96m" + "="*80)
        print("  E-COMMERCE PLATFORM - SYSTEM MONITORING DASHBOARD")
        print("  Real-time Service Status")
        print("="*80 + "\033[0m")
        print(f"  Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Backend Status
        backend = self.check_backend()
        print(f"{backend['color']}┌─ BACKEND SERVICE ─────────────────────────────────────┐\033[0m")
        print(f"{backend['color']}│ Status:        {backend['status']:<40}│\033[0m")
        print(f"{backend['color']}│ Response Time: {backend['response_time']:<40}│\033[0m")
        print(f"{backend['color']}│ Database:      {backend['database']:<40}│\033[0m")
        print(f"{backend['color']}│ Redis:         {backend['redis']:<40}│\033[0m")
        if 'error' in backend:
            print(f"{backend['color']}│ Error:         {backend['error']:<40}│\033[0m")
        print(f"{backend['color']}└───────────────────────────────────────────────────────┘\033[0m\n")
        
        # Frontend Status
        frontend = self.check_frontend()
        print(f"{frontend['color']}┌─ FRONTEND SERVICE ────────────────────────────────────┐\033[0m")
        print(f"{frontend['color']}│ Status:        {frontend['status']:<40}│\033[0m")
        print(f"{frontend['color']}│ Response Time: {frontend['response_time']:<40}│\033[0m")
        if 'error' in frontend:
            print(f"{frontend['color']}│ Error:         {frontend['error']:<40}│\033[0m")
        print(f"{frontend['color']}└───────────────────────────────────────────────────────┘\033[0m\n")
        
        # Docker Services
        docker_services = self.check_docker_services()
        print("\033[94m┌─ DOCKER CONTAINERS ───────────────────────────────────┐\033[0m")
        if 'error' not in docker_services:
            for name, info in docker_services.items():
                status = info['state'].upper()
                color = info['color']
                print(f"│ {name:<20} {color}{status:<32}\033[0m│")
        else:
            print(f"\033[91m│ Error: {docker_services['error']:<46}│\033[0m")
        print("\033[94m└───────────────────────────────────────────────────────┘\033[0m\n")
        
        # API Endpoints
        endpoints = self.check_api_endpoints()
        print("\033[95m┌─ API ENDPOINTS STATUS ────────────────────────────────┐\033[0m")
        for endpoint in endpoints:
            print(f"│ {endpoint['name']:<20} {endpoint['color']}{endpoint['status']}\033[0m  {endpoint['response_time']:<28}│")
        print("\033[95m└───────────────────────────────────────────────────────┘\033[0m\n")
        
        # System Health Summary
        all_up = (backend['status'] == 'UP' and 
                  frontend['status'] == 'UP' and
                  all(e['status'] == '✓' for e in endpoints))
        
        if all_up:
            print("\033[92m✓ ALL SYSTEMS OPERATIONAL\033[0m")
        else:
            print("\033[93m⚠ SOME SERVICES NEED ATTENTION\033[0m")
        
        print("\n\033[90mPress Ctrl+C to exit\033[0m")
    
    def run(self, interval: int = 5):
        """Run monitoring loop"""
        try:
            while True:
                self.print_dashboard()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")


def main():
    """Main entry point"""
    monitor = SystemMonitor()
    print("\033[96mStarting System Monitor...\033[0m")
    time.sleep(1)
    monitor.run(interval=5)


if __name__ == "__main__":
    main()
