"""
KasaPOS Sync Agent
Synchronizes products and inventory from KasaPOS to E-Commerce Platform

For Tamil Nadu Grocery Shops using KasaPOS Billing Software
"""
import os
import sys
import time
import json
import logging
import argparse
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from kasapos_adapter import KasaPOSAdapter, KasaPOSConfig, KasaPOSConnectionType

# Configuration - Set these or use environment variables
API_BASE_URL = os.getenv("ECOMMERCE_API_URL", "http://localhost:8000/api/v1")
STORE_ID = os.getenv("STORE_ID", "")
API_KEY = os.getenv("API_KEY", "")

# Setup logging
log_file = Path("kasapos_sync.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class KasaPOSSyncAgent:
    """
    Sync Agent for KasaPOS to E-Commerce Platform
    
    Features:
    - Delta sync (only changed products)
    - Full sync (all products)
    - Inventory-only sync (fast stock updates)
    - Real-time sales sync
    - Automatic retry on failure
    - Offline queue for network issues
    """
    
    def __init__(
        self,
        kasapos_config: KasaPOSConfig,
        api_url: str,
        store_id: str,
        api_key: str
    ):
        self.adapter = KasaPOSAdapter(kasapos_config)
        self.api_url = api_url
        self.store_id = store_id
        self.api_key = api_key
        
        # HTTP session for API calls
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "X-Store-ID": store_id,
            "Content-Type": "application/json"
        })
        
        # Sync state
        self.offline_queue = []
        self.last_sync_stats = {}
        
    def verify_api_connection(self) -> bool:
        """Verify connection to e-commerce API"""
        try:
            response = self.session.get(
                f"{self.api_url}/health",
                timeout=10
            )
            if response.status_code == 200:
                logger.info("E-Commerce API connection verified")
                return True
            else:
                logger.error(f"API returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to API: {e}")
            return False
    
    def sync_products(self, sync_type: str = "delta") -> Dict[str, Any]:
        """
        Sync products from KasaPOS to E-Commerce Platform
        
        Args:
            sync_type: 'delta', 'full', or 'inventory_only'
        
        Returns:
            Sync result statistics
        """
        stats = {
            "sync_type": sync_type,
            "started_at": datetime.now().isoformat(),
            "products_fetched": 0,
            "products_created": 0,
            "products_updated": 0,
            "products_failed": 0,
            "success": False,
            "error": None
        }
        
        try:
            # Connect to KasaPOS
            if not self.adapter.connect():
                stats["error"] = "Failed to connect to KasaPOS"
                return stats
            
            # Fetch products
            full_sync = sync_type == "full"
            if sync_type == "inventory_only":
                products = self._convert_inventory_to_products(
                    self.adapter.fetch_inventory()
                )
            else:
                products = self.adapter.fetch_products(full_sync=full_sync)
            
            stats["products_fetched"] = len(products)
            
            if not products:
                logger.info("No products to sync")
                stats["success"] = True
                self.adapter.disconnect()
                return stats
            
            # Sync to API in batches
            batch_size = 500
            batches = [products[i:i + batch_size] for i in range(0, len(products), batch_size)]
            
            for batch_num, batch in enumerate(batches, 1):
                logger.info(f"Syncing batch {batch_num}/{len(batches)} ({len(batch)} products)")
                
                result = self._send_batch_to_api(batch, sync_type)
                
                if result:
                    stats["products_created"] += result.get("created", 0)
                    stats["products_updated"] += result.get("updated", 0)
                    stats["products_failed"] += result.get("failed", 0)
                else:
                    # Queue for retry if API fails
                    self.offline_queue.extend(batch)
                    stats["products_failed"] += len(batch)
                
                # Small delay between batches
                time.sleep(0.5)
            
            # Mark sync complete
            if stats["products_failed"] == 0:
                self.adapter.mark_sync_complete()
                stats["success"] = True
            
            # Disconnect
            self.adapter.disconnect()
            
        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            stats["error"] = str(e)
            self.adapter.disconnect()
        
        stats["completed_at"] = datetime.now().isoformat()
        self.last_sync_stats = stats
        
        logger.info(f"Sync completed: {json.dumps(stats, indent=2)}")
        return stats
    
    def _convert_inventory_to_products(self, inventory: List[Dict]) -> List[Dict]:
        """Convert inventory records to product format for inventory-only sync"""
        return [
            {
                "external_id": item["external_id"],
                "sku": item.get("sku", ""),
                "quantity": item["quantity"]
            }
            for item in inventory
        ]
    
    def _send_batch_to_api(
        self,
        products: List[Dict[str, Any]],
        sync_type: str
    ) -> Optional[Dict[str, Any]]:
        """Send product batch to e-commerce API"""
        try:
            payload = {
                "store_id": self.store_id,
                "sync_type": sync_type,
                "timestamp": datetime.utcnow().isoformat(),
                "products": products
            }
            
            response = self.session.post(
                f"{self.api_url}/sync/products/batch",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return result.get("data", {})
                else:
                    logger.error(f"API error: {result.get('error')}")
                    return None
            else:
                logger.error(f"API returned status {response.status_code}: {response.text}")
                return None
                
        except requests.Timeout:
            logger.error("API request timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to send batch: {e}")
            return None
    
    def sync_sales(self, days: int = 1) -> Dict[str, Any]:
        """Sync recent sales/orders to e-commerce platform for analytics"""
        stats = {
            "started_at": datetime.now().isoformat(),
            "sales_fetched": 0,
            "sales_synced": 0,
            "success": False,
            "error": None
        }
        
        try:
            if not self.adapter.connect():
                stats["error"] = "Failed to connect to KasaPOS"
                return stats
            
            sales = self.adapter.fetch_recent_sales(days=days)
            stats["sales_fetched"] = len(sales)
            
            if sales:
                result = self._send_sales_to_api(sales)
                if result:
                    stats["sales_synced"] = result.get("synced", 0)
                    stats["success"] = True
            else:
                stats["success"] = True
            
            self.adapter.disconnect()
            
        except Exception as e:
            logger.error(f"Sales sync failed: {e}", exc_info=True)
            stats["error"] = str(e)
            self.adapter.disconnect()
        
        stats["completed_at"] = datetime.now().isoformat()
        return stats
    
    def _send_sales_to_api(self, sales: List[Dict]) -> Optional[Dict]:
        """Send sales data to API"""
        try:
            payload = {
                "store_id": self.store_id,
                "orders": sales
            }
            
            response = self.session.post(
                f"{self.api_url}/sync/orders/batch",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get("data", {})
            else:
                logger.error(f"Sales sync API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to send sales: {e}")
            return None
    
    def process_offline_queue(self) -> int:
        """Process any items in the offline queue"""
        if not self.offline_queue:
            return 0
        
        logger.info(f"Processing {len(self.offline_queue)} items from offline queue")
        
        processed = 0
        remaining = []
        
        # Process in batches
        batch_size = 100
        for i in range(0, len(self.offline_queue), batch_size):
            batch = self.offline_queue[i:i + batch_size]
            result = self._send_batch_to_api(batch, "delta")
            
            if result:
                processed += len(batch)
            else:
                remaining.extend(batch)
        
        self.offline_queue = remaining
        logger.info(f"Processed {processed} items, {len(remaining)} remaining in queue")
        
        return processed
    
    def run_continuous_sync(
        self,
        interval_minutes: int = 5,
        inventory_interval_minutes: int = 1
    ):
        """
        Run continuous sync loop
        
        Args:
            interval_minutes: Full/delta sync interval
            inventory_interval_minutes: Inventory-only sync interval (during business hours)
        """
        logger.info(f"Starting continuous sync (interval: {interval_minutes}min, inventory: {inventory_interval_minutes}min)")
        
        last_full_sync = datetime.now() - timedelta(hours=24)  # Force initial full sync
        last_delta_sync = datetime.now()
        last_inventory_sync = datetime.now()
        
        while True:
            try:
                current_time = datetime.now()
                current_hour = current_time.hour
                
                # Business hours check (9 AM to 10 PM IST)
                is_business_hours = 9 <= current_hour <= 22
                
                # Full sync once per day (at 3 AM)
                if current_hour == 3 and (current_time - last_full_sync) > timedelta(hours=20):
                    logger.info("Running scheduled full sync")
                    self.sync_products(sync_type="full")
                    last_full_sync = current_time
                
                # Inventory-only sync during business hours (every 1-2 min)
                elif is_business_hours and (current_time - last_inventory_sync) > timedelta(minutes=inventory_interval_minutes):
                    logger.info("Running inventory sync")
                    self.sync_products(sync_type="inventory_only")
                    last_inventory_sync = current_time
                
                # Delta sync at regular intervals
                elif (current_time - last_delta_sync) > timedelta(minutes=interval_minutes):
                    logger.info("Running delta sync")
                    self.sync_products(sync_type="delta")
                    last_delta_sync = current_time
                
                # Process offline queue if any
                if self.offline_queue:
                    self.process_offline_queue()
                
                # Sync sales once per hour
                if current_time.minute == 0:
                    self.sync_sales(days=1)
                
                # Wait before next check
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                logger.info("Sync agent stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in sync loop: {e}", exc_info=True)
                time.sleep(60)  # Wait before retry
    
    def get_status(self) -> Dict[str, Any]:
        """Get current sync agent status"""
        return {
            "api_url": self.api_url,
            "store_id": self.store_id,
            "connection_type": self.adapter.config.connection_type.value,
            "last_sync": self.last_sync_stats,
            "offline_queue_size": len(self.offline_queue),
            "kasapos_connected": self.adapter.test_connection().get("connected", False)
        }


def create_config_from_args(args) -> KasaPOSConfig:
    """Create KasaPOS config from command line arguments"""
    return KasaPOSConfig(
        connection_type=KasaPOSConnectionType(args.connection_type),
        mysql_host=args.mysql_host,
        mysql_port=args.mysql_port,
        mysql_user=args.mysql_user,
        mysql_password=args.mysql_password,
        mysql_database=args.mysql_database,
        sqlite_path=args.sqlite_path or "",
        export_folder=args.export_folder or "",
        products_file=args.products_file,
        inventory_file=args.inventory_file,
        orders_file=args.orders_file,
        store_code=args.store_code,
        sync_interval_minutes=args.sync_interval
    )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="KasaPOS Sync Agent - Sync your grocery store to e-commerce platform"
    )
    
    # General options
    parser.add_argument("--api-url", default=API_BASE_URL,
                       help="E-Commerce API URL")
    parser.add_argument("--store-id", default=STORE_ID,
                       help="Your store ID")
    parser.add_argument("--api-key", default=API_KEY,
                       help="Your API key")
    
    # KasaPOS connection options
    parser.add_argument("--connection-type", 
                       choices=["mysql", "sqlite", "csv", "excel"],
                       default="mysql",
                       help="How to connect to KasaPOS")
    
    # MySQL options
    parser.add_argument("--mysql-host", default="localhost",
                       help="KasaPOS MySQL host")
    parser.add_argument("--mysql-port", type=int, default=3306,
                       help="KasaPOS MySQL port")
    parser.add_argument("--mysql-user", default="root",
                       help="KasaPOS MySQL username")
    parser.add_argument("--mysql-password", default="",
                       help="KasaPOS MySQL password")
    parser.add_argument("--mysql-database", default="kasapos",
                       help="KasaPOS MySQL database name")
    
    # SQLite options
    parser.add_argument("--sqlite-path",
                       help="Path to KasaPOS SQLite database file")
    
    # CSV/Excel options
    parser.add_argument("--export-folder",
                       help="Folder with KasaPOS CSV/Excel exports")
    parser.add_argument("--products-file", default="products.csv",
                       help="Products file name")
    parser.add_argument("--inventory-file", default="inventory.csv",
                       help="Inventory file name")
    parser.add_argument("--orders-file", default="sales.csv",
                       help="Sales/orders file name")
    
    # Store info
    parser.add_argument("--store-code", default="STORE001",
                       help="Your store code in KasaPOS")
    
    # Sync options
    parser.add_argument("--sync-interval", type=int, default=5,
                       help="Sync interval in minutes")
    parser.add_argument("--inventory-interval", type=int, default=1,
                       help="Inventory sync interval in minutes")
    
    # Commands
    parser.add_argument("--test", action="store_true",
                       help="Test connections and exit")
    parser.add_argument("--sync-once", action="store_true",
                       help="Run single sync and exit")
    parser.add_argument("--sync-type", choices=["delta", "full", "inventory_only"],
                       default="delta",
                       help="Type of sync for --sync-once")
    parser.add_argument("--continuous", action="store_true",
                       help="Run continuous sync (default)")
    
    args = parser.parse_args()
    
    # Print banner
    print("=" * 65)
    print("  KasaPOS Sync Agent for E-Commerce Platform")
    print("  For Tamil Nadu Grocery Shops")
    print("=" * 65)
    
    # Validate required settings
    if not args.store_id or args.store_id == "":
        print("\n❌ ERROR: Store ID is required!")
        print("   Set --store-id or STORE_ID environment variable")
        print("   Contact platform administrator to get your Store ID")
        return
    
    if not args.api_key or args.api_key == "":
        print("\n⚠️  WARNING: API Key not set!")
        print("   Set --api-key or API_KEY environment variable")
    
    # Create config
    kasapos_config = create_config_from_args(args)
    
    # Create sync agent
    agent = KasaPOSSyncAgent(
        kasapos_config=kasapos_config,
        api_url=args.api_url,
        store_id=args.store_id,
        api_key=args.api_key
    )
    
    print(f"\n📍 Store ID: {args.store_id}")
    print(f"🌐 API URL: {args.api_url}")
    print(f"🔌 Connection: {args.connection_type}")
    
    # Test mode
    if args.test:
        print("\n🔍 Testing connections...")
        
        # Test KasaPOS
        print("\n1. Testing KasaPOS connection...")
        kasapos_result = agent.adapter.test_connection()
        if kasapos_result["connected"]:
            print(f"   ✅ KasaPOS: Connected")
            print(f"   📦 Products found: {kasapos_result['product_count']}")
            if kasapos_result.get("tables_found"):
                print(f"   📋 Tables: {', '.join(kasapos_result['tables_found'][:10])}")
        else:
            print(f"   ❌ KasaPOS: {kasapos_result['message']}")
        
        # Test API
        print("\n2. Testing E-Commerce API...")
        if agent.verify_api_connection():
            print("   ✅ E-Commerce API: Connected")
        else:
            print("   ❌ E-Commerce API: Failed to connect")
        
        print("\n" + "=" * 65)
        return
    
    # Verify API connection
    if not agent.verify_api_connection():
        print("\n❌ Cannot connect to E-Commerce API!")
        print("   Check your internet connection and API URL")
        return
    
    # Single sync mode
    if args.sync_once:
        print(f"\n🔄 Running {args.sync_type} sync...")
        stats = agent.sync_products(sync_type=args.sync_type)
        
        if stats["success"]:
            print(f"\n✅ Sync completed successfully!")
            print(f"   📦 Products fetched: {stats['products_fetched']}")
            print(f"   ➕ Created: {stats['products_created']}")
            print(f"   🔄 Updated: {stats['products_updated']}")
            print(f"   ❌ Failed: {stats['products_failed']}")
        else:
            print(f"\n❌ Sync failed: {stats.get('error', 'Unknown error')}")
        return
    
    # Continuous sync mode (default)
    print(f"\n🚀 Starting continuous sync...")
    print(f"   📅 Delta sync every {args.sync_interval} minutes")
    print(f"   📦 Inventory sync every {args.inventory_interval} minute(s)")
    print(f"   🌙 Full sync at 3 AM daily")
    print("\nPress Ctrl+C to stop\n")
    print("-" * 65)
    
    agent.run_continuous_sync(
        interval_minutes=args.sync_interval,
        inventory_interval_minutes=args.inventory_interval
    )


if __name__ == "__main__":
    main()
