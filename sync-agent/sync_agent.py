"""
Sync Agent - Runs on store's local computer
Synchronizes data from billing software to cloud platform
"""
import requests
import json
import time
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any
import sqlite3
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"  # Change to production URL
STORE_ID = "YOUR_STORE_ID_HERE"
API_KEY = "YOUR_API_KEY_HERE"
SYNC_INTERVAL_SECONDS = 300  # 5 minutes default
BILLING_DB_PATH = "path/to/billing/database.db"  # Configure for your billing software

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SyncAgent:
    """
    Sync agent for pushing data from billing software to cloud platform
    """
    
    def __init__(self, api_url: str, store_id: str, api_key: str):
        self.api_url = api_url
        self.store_id = store_id
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        })
        self.last_sync_timestamp = self.load_last_sync_timestamp()
    
    def load_last_sync_timestamp(self) -> datetime:
        """Load last successful sync timestamp from local file"""
        try:
            with open("last_sync.txt", "r") as f:
                timestamp_str = f.read().strip()
                return datetime.fromisoformat(timestamp_str)
        except FileNotFoundError:
            # First sync - use a date far in the past
            return datetime(2020, 1, 1)
    
    def save_last_sync_timestamp(self, timestamp: datetime):
        """Save last successful sync timestamp"""
        with open("last_sync.txt", "w") as f:
            f.write(timestamp.isoformat())
    
    def fetch_products_from_billing(self) -> List[Dict[str, Any]]:
        """
        Fetch products from billing software database
        
        IMPORTANT: Modify this method to match your billing software's schema
        """
        products = []
        
        try:
            # Example: SQLite database query
            # Adapt this to your billing software (Tally, Marg, etc.)
            conn = sqlite3.connect(BILLING_DB_PATH)
            cursor = conn.cursor()
            
            # Query products modified after last sync
            query = """
                SELECT 
                    product_id,
                    product_name,
                    description,
                    mrp,
                    selling_price,
                    quantity,
                    unit,
                    sku,
                    barcode,
                    category,
                    hsn_code,
                    gst_percent,
                    updated_at
                FROM products
                WHERE updated_at > ?
                ORDER BY updated_at ASC
            """
            
            cursor.execute(query, (self.last_sync_timestamp.isoformat(),))
            rows = cursor.fetchall()
            
            for row in rows:
                products.append({
                    "external_id": str(row[0]),
                    "name": row[1],
                    "description": row[2],
                    "mrp": float(row[3]),
                    "selling_price": float(row[4]),
                    "quantity": int(row[5]),
                    "unit": row[6],
                    "sku": row[7],
                    "barcode": row[8],
                    "category": row[9],
                    "hsn_code": row[10],
                    "gst_percent": float(row[11]) if row[11] else 0,
                    "updated_at": row[12]
                })
            
            conn.close()
            logger.info(f"Fetched {len(products)} products from billing system")
            return products
            
        except Exception as e:
            logger.error(f"Failed to fetch products from billing system: {e}")
            return []
    
    def sync_products(self, sync_type: str = "delta") -> bool:
        """
        Sync products to cloud platform
        
        Args:
            sync_type: 'delta' (only changes), 'full' (all products), 'inventory_only'
        
        Returns:
            True if sync successful, False otherwise
        """
        try:
            # Fetch products from billing system
            products = self.fetch_products_from_billing()
            
            if not products:
                logger.info("No products to sync")
                return True
            
            # Split into batches (max 1000 per batch)
            batch_size = 1000
            batches = [products[i:i + batch_size] for i in range(0, len(products), batch_size)]
            
            total_created = 0
            total_updated = 0
            total_failed = 0
            
            for batch_num, batch in enumerate(batches, 1):
                logger.info(f"Syncing batch {batch_num}/{len(batches)} ({len(batch)} products)")
                
                # Prepare sync request
                payload = {
                    "store_id": self.store_id,
                    "sync_type": sync_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "products": batch
                }
                
                # Send to API
                response = self.session.post(
                    f"{self.api_url}/sync/products/batch",
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        data = result.get("data", {})
                        total_created += data.get("created", 0)
                        total_updated += data.get("updated", 0)
                        total_failed += data.get("failed", 0)
                        
                        logger.info(
                            f"Batch {batch_num} synced: "
                            f"{data.get('created', 0)} created, "
                            f"{data.get('updated', 0)} updated, "
                            f"{data.get('failed', 0)} failed"
                        )
                    else:
                        logger.error(f"Sync failed: {result.get('error')}")
                        return False
                else:
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    return False
                
                # Small delay between batches to avoid overwhelming server
                time.sleep(1)
            
            # Update last sync timestamp
            self.save_last_sync_timestamp(datetime.utcnow())
            
            logger.info(
                f"Sync complete: "
                f"{total_created} created, "
                f"{total_updated} updated, "
                f"{total_failed} failed"
            )
            return True
            
        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            return False
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status from API"""
        try:
            response = self.session.get(
                f"{self.api_url}/sync/status",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return result.get("data", {})
            
            return {}
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {}
    
    def run_continuous_sync(self, interval_seconds: int = SYNC_INTERVAL_SECONDS):
        """
        Run continuous sync in loop
        
        Args:
            interval_seconds: Time between sync attempts
        """
        logger.info(f"Starting continuous sync (interval: {interval_seconds}s)")
        
        while True:
            try:
                # Get current sync status
                status = self.get_sync_status()
                logger.info(f"Sync status: {status}")
                
                # Determine sync type
                # Use 'inventory_only' during business hours for faster updates
                current_hour = datetime.now().hour
                if 9 <= current_hour <= 21:  # Business hours
                    sync_type = "delta"
                else:
                    sync_type = "delta"
                
                # Perform sync
                success = self.sync_products(sync_type=sync_type)
                
                if success:
                    logger.info("Sync successful")
                else:
                    logger.error("Sync failed")
                
                # Wait before next sync
                logger.info(f"Waiting {interval_seconds} seconds until next sync...")
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Sync agent stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying


def main():
    """Main entry point"""
    print("=" * 60)
    print("E-Commerce Platform - Sync Agent")
    print("=" * 60)
    print(f"API URL: {API_BASE_URL}")
    print(f"Store ID: {STORE_ID}")
    print(f"Sync Interval: {SYNC_INTERVAL_SECONDS} seconds")
    print("=" * 60)
    
    # Validate configuration
    if STORE_ID == "YOUR_STORE_ID_HERE" or API_KEY == "YOUR_API_KEY_HERE":
        print("\nERROR: Please configure STORE_ID and API_KEY in the script!")
        print("Contact platform administrator to get your credentials.")
        return
    
    # Create sync agent
    agent = SyncAgent(
        api_url=API_BASE_URL,
        store_id=STORE_ID,
        api_key=API_KEY
    )
    
    # Run continuous sync
    agent.run_continuous_sync()


if __name__ == "__main__":
    main()
