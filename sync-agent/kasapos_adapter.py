"""
KasaPOS Integration Adapter
Connects to KasaPOS billing software for grocery stores in India

KasaPOS typically stores data in:
1. MySQL database (local or cloud)
2. SQLite database 
3. CSV/Excel exports

This adapter supports all methods with auto-detection.
"""
import os
import csv
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Optional imports for MySQL and Excel
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    
try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

logger = logging.getLogger(__name__)


class KasaPOSConnectionType(Enum):
    """Supported connection types for KasaPOS"""
    MYSQL = "mysql"
    SQLITE = "sqlite"
    CSV = "csv"
    EXCEL = "excel"
    API = "api"


@dataclass
class KasaPOSConfig:
    """Configuration for KasaPOS connection"""
    connection_type: KasaPOSConnectionType
    
    # MySQL settings
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "kasapos"
    
    # SQLite settings
    sqlite_path: str = ""
    
    # CSV/Excel settings
    export_folder: str = ""
    products_file: str = "products.csv"
    inventory_file: str = "inventory.csv"
    orders_file: str = "sales.csv"
    
    # API settings (if KasaPOS has REST API)
    api_url: str = ""
    api_key: str = ""
    
    # Common settings
    store_code: str = ""  # Your store identifier in KasaPOS
    sync_interval_minutes: int = 5
    
    @classmethod
    def from_env(cls) -> 'KasaPOSConfig':
        """Load configuration from environment variables"""
        conn_type = os.getenv("KASAPOS_CONNECTION_TYPE", "mysql").lower()
        
        return cls(
            connection_type=KasaPOSConnectionType(conn_type),
            mysql_host=os.getenv("KASAPOS_MYSQL_HOST", "localhost"),
            mysql_port=int(os.getenv("KASAPOS_MYSQL_PORT", "3306")),
            mysql_user=os.getenv("KASAPOS_MYSQL_USER", "root"),
            mysql_password=os.getenv("KASAPOS_MYSQL_PASSWORD", ""),
            mysql_database=os.getenv("KASAPOS_MYSQL_DATABASE", "kasapos"),
            sqlite_path=os.getenv("KASAPOS_SQLITE_PATH", ""),
            export_folder=os.getenv("KASAPOS_EXPORT_FOLDER", ""),
            products_file=os.getenv("KASAPOS_PRODUCTS_FILE", "products.csv"),
            inventory_file=os.getenv("KASAPOS_INVENTORY_FILE", "inventory.csv"),
            orders_file=os.getenv("KASAPOS_ORDERS_FILE", "sales.csv"),
            api_url=os.getenv("KASAPOS_API_URL", ""),
            api_key=os.getenv("KASAPOS_API_KEY", ""),
            store_code=os.getenv("KASAPOS_STORE_CODE", "STORE001"),
            sync_interval_minutes=int(os.getenv("KASAPOS_SYNC_INTERVAL", "5"))
        )


class KasaPOSAdapter:
    """
    Adapter for KasaPOS Billing Software
    
    Supports multiple connection methods:
    - MySQL database (most common)
    - SQLite database
    - CSV file exports
    - Excel file exports
    - REST API (if available)
    """
    
    # Common KasaPOS table/column mappings
    # Adjust these based on your actual KasaPOS version
    PRODUCT_TABLE = "tbl_products"
    INVENTORY_TABLE = "tbl_stock"
    SALES_TABLE = "tbl_sales"
    CATEGORY_TABLE = "tbl_category"
    
    # Column mappings (KasaPOS column -> our standard field)
    PRODUCT_COLUMNS = {
        "product_id": "external_id",
        "product_code": "sku",
        "product_name": "name",
        "description": "description",
        "mrp": "mrp",
        "selling_price": "price",
        "cost_price": "cost_price",
        "quantity": "quantity",
        "unit": "unit",
        "barcode": "barcode",
        "category_id": "category_id",
        "hsn_code": "hsn_code",
        "gst_rate": "gst_percent",
        "is_active": "is_active",
        "created_at": "created_at",
        "updated_at": "updated_at",
        "min_stock": "min_stock",
        "max_stock": "max_stock",
        "reorder_level": "reorder_level"
    }
    
    def __init__(self, config: KasaPOSConfig):
        self.config = config
        self.connection = None
        self.last_sync_time = self._load_last_sync_time()
        
    def _load_last_sync_time(self) -> datetime:
        """Load last successful sync timestamp"""
        try:
            sync_file = Path("kasapos_last_sync.txt")
            if sync_file.exists():
                with open(sync_file, "r") as f:
                    return datetime.fromisoformat(f.read().strip())
        except Exception as e:
            logger.warning(f"Could not load last sync time: {e}")
        return datetime(2020, 1, 1)
    
    def _save_last_sync_time(self):
        """Save last sync timestamp"""
        with open("kasapos_last_sync.txt", "w") as f:
            f.write(datetime.utcnow().isoformat())
    
    def connect(self) -> bool:
        """Establish connection to KasaPOS data source"""
        try:
            if self.config.connection_type == KasaPOSConnectionType.MYSQL:
                return self._connect_mysql()
            elif self.config.connection_type == KasaPOSConnectionType.SQLITE:
                return self._connect_sqlite()
            elif self.config.connection_type in [KasaPOSConnectionType.CSV, KasaPOSConnectionType.EXCEL]:
                return self._verify_export_folder()
            elif self.config.connection_type == KasaPOSConnectionType.API:
                return self._connect_api()
            else:
                logger.error(f"Unknown connection type: {self.config.connection_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to KasaPOS: {e}")
            return False
    
    def _connect_mysql(self) -> bool:
        """Connect to KasaPOS MySQL database"""
        if not MYSQL_AVAILABLE:
            logger.error("mysql-connector-python not installed. Run: pip install mysql-connector-python")
            return False
        
        try:
            self.connection = mysql.connector.connect(
                host=self.config.mysql_host,
                port=self.config.mysql_port,
                user=self.config.mysql_user,
                password=self.config.mysql_password,
                database=self.config.mysql_database
            )
            logger.info(f"Connected to KasaPOS MySQL at {self.config.mysql_host}")
            return True
        except Exception as e:
            logger.error(f"MySQL connection failed: {e}")
            return False
    
    def _connect_sqlite(self) -> bool:
        """Connect to KasaPOS SQLite database"""
        try:
            if not os.path.exists(self.config.sqlite_path):
                logger.error(f"SQLite database not found: {self.config.sqlite_path}")
                return False
            
            self.connection = sqlite3.connect(self.config.sqlite_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to KasaPOS SQLite at {self.config.sqlite_path}")
            return True
        except Exception as e:
            logger.error(f"SQLite connection failed: {e}")
            return False
    
    def _verify_export_folder(self) -> bool:
        """Verify export folder exists for CSV/Excel mode"""
        if not os.path.exists(self.config.export_folder):
            logger.error(f"Export folder not found: {self.config.export_folder}")
            return False
        logger.info(f"Using export folder: {self.config.export_folder}")
        return True
    
    def _connect_api(self) -> bool:
        """Verify API connection (if KasaPOS has REST API)"""
        try:
            import requests
            response = requests.get(
                f"{self.config.api_url}/health",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"Connected to KasaPOS API at {self.config.api_url}")
                return True
            else:
                logger.error(f"KasaPOS API returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"API connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from KasaPOS")
    
    def fetch_products(self, since: Optional[datetime] = None, full_sync: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch products from KasaPOS
        
        Args:
            since: Only fetch products modified after this time
            full_sync: If True, fetch all products ignoring 'since'
        
        Returns:
            List of product dictionaries
        """
        if full_sync:
            since = None
        elif since is None:
            since = self.last_sync_time
        
        if self.config.connection_type == KasaPOSConnectionType.MYSQL:
            return self._fetch_products_mysql(since)
        elif self.config.connection_type == KasaPOSConnectionType.SQLITE:
            return self._fetch_products_sqlite(since)
        elif self.config.connection_type == KasaPOSConnectionType.CSV:
            return self._fetch_products_csv()
        elif self.config.connection_type == KasaPOSConnectionType.EXCEL:
            return self._fetch_products_excel()
        elif self.config.connection_type == KasaPOSConnectionType.API:
            return self._fetch_products_api(since)
        
        return []
    
    def _fetch_products_mysql(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch products from MySQL database"""
        products = []
        cursor = self.connection.cursor(dictionary=True)
        
        try:
            # Build query - adjust table/column names for your KasaPOS version
            query = f"""
                SELECT 
                    p.product_id,
                    p.product_code,
                    p.product_name,
                    p.description,
                    p.mrp,
                    p.selling_price,
                    COALESCE(p.cost_price, 0) as cost_price,
                    COALESCE(s.quantity, 0) as quantity,
                    p.unit,
                    p.barcode,
                    c.category_name,
                    p.hsn_code,
                    COALESCE(p.gst_rate, 0) as gst_rate,
                    p.is_active,
                    p.created_at,
                    p.updated_at,
                    COALESCE(p.min_stock, 5) as min_stock,
                    p.image_url
                FROM {self.PRODUCT_TABLE} p
                LEFT JOIN {self.INVENTORY_TABLE} s ON p.product_id = s.product_id
                LEFT JOIN {self.CATEGORY_TABLE} c ON p.category_id = c.category_id
                WHERE p.is_active = 1
            """
            
            params = []
            if since:
                query += " AND p.updated_at > %s"
                params.append(since)
            
            query += " ORDER BY p.updated_at ASC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            for row in rows:
                products.append(self._map_product(row))
            
            logger.info(f"Fetched {len(products)} products from KasaPOS MySQL")
            
        except Exception as e:
            logger.error(f"Failed to fetch products from MySQL: {e}")
        finally:
            cursor.close()
        
        return products
    
    def _fetch_products_sqlite(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch products from SQLite database"""
        products = []
        cursor = self.connection.cursor()
        
        try:
            query = f"""
                SELECT 
                    p.product_id,
                    p.product_code,
                    p.product_name,
                    p.description,
                    p.mrp,
                    p.selling_price,
                    COALESCE(p.cost_price, 0) as cost_price,
                    COALESCE(s.quantity, 0) as quantity,
                    p.unit,
                    p.barcode,
                    c.category_name,
                    p.hsn_code,
                    COALESCE(p.gst_rate, 0) as gst_rate,
                    p.is_active,
                    p.created_at,
                    p.updated_at,
                    COALESCE(p.min_stock, 5) as min_stock,
                    p.image_url
                FROM {self.PRODUCT_TABLE} p
                LEFT JOIN {self.INVENTORY_TABLE} s ON p.product_id = s.product_id
                LEFT JOIN {self.CATEGORY_TABLE} c ON p.category_id = c.category_id
                WHERE p.is_active = 1
            """
            
            params = []
            if since:
                query += " AND p.updated_at > ?"
                params.append(since.isoformat())
            
            query += " ORDER BY p.updated_at ASC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            for row in rows:
                products.append(self._map_product(dict(row)))
            
            logger.info(f"Fetched {len(products)} products from KasaPOS SQLite")
            
        except Exception as e:
            logger.error(f"Failed to fetch products from SQLite: {e}")
        finally:
            cursor.close()
        
        return products
    
    def _fetch_products_csv(self) -> List[Dict[str, Any]]:
        """Fetch products from CSV export file"""
        products = []
        csv_path = Path(self.config.export_folder) / self.config.products_file
        
        try:
            if not csv_path.exists():
                logger.error(f"Products CSV not found: {csv_path}")
                return []
            
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    products.append(self._map_csv_product(row))
            
            logger.info(f"Fetched {len(products)} products from CSV")
            
        except Exception as e:
            logger.error(f"Failed to fetch products from CSV: {e}")
        
        return products
    
    def _fetch_products_excel(self) -> List[Dict[str, Any]]:
        """Fetch products from Excel export file"""
        if not EXCEL_AVAILABLE:
            logger.error("openpyxl not installed. Run: pip install openpyxl")
            return []
        
        products = []
        excel_path = Path(self.config.export_folder) / self.config.products_file.replace('.csv', '.xlsx')
        
        try:
            if not excel_path.exists():
                logger.error(f"Products Excel not found: {excel_path}")
                return []
            
            workbook = openpyxl.load_workbook(excel_path)
            sheet = workbook.active
            
            # Get headers from first row
            headers = [cell.value for cell in sheet[1]]
            
            for row in sheet.iter_rows(min_row=2, values_only=True):
                row_dict = dict(zip(headers, row))
                products.append(self._map_csv_product(row_dict))
            
            logger.info(f"Fetched {len(products)} products from Excel")
            
        except Exception as e:
            logger.error(f"Failed to fetch products from Excel: {e}")
        
        return products
    
    def _fetch_products_api(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch products from KasaPOS REST API (if available)"""
        import requests
        products = []
        
        try:
            params = {}
            if since:
                params["modified_after"] = since.isoformat()
            
            response = requests.get(
                f"{self.config.api_url}/products",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("products", []):
                    products.append(self._map_product(item))
                logger.info(f"Fetched {len(products)} products from API")
            else:
                logger.error(f"API returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to fetch products from API: {e}")
        
        return products
    
    def _map_product(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map KasaPOS product to our standard format"""
        return {
            "external_id": str(row.get("product_id", "")),
            "sku": row.get("product_code") or row.get("barcode") or str(row.get("product_id")),
            "name": row.get("product_name", ""),
            "description": row.get("description") or "",
            "mrp": float(row.get("mrp", 0) or 0),
            "price": float(row.get("selling_price", 0) or 0),
            "cost_price": float(row.get("cost_price", 0) or 0),
            "quantity": int(row.get("quantity", 0) or 0),
            "unit": row.get("unit") or "pcs",
            "barcode": row.get("barcode") or "",
            "category": row.get("category_name") or "General",
            "hsn_code": row.get("hsn_code") or "",
            "gst_percent": float(row.get("gst_rate", 0) or 0),
            "is_active": bool(row.get("is_active", True)),
            "min_stock": int(row.get("min_stock", 5) or 5),
            "image_url": row.get("image_url") or "",
            "updated_at": str(row.get("updated_at") or datetime.utcnow().isoformat())
        }
    
    def _map_csv_product(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map CSV row to standard format (column names may vary)"""
        # Common CSV column name variations
        name_cols = ["product_name", "name", "item_name", "product", "item"]
        price_cols = ["selling_price", "price", "rate", "sp"]
        mrp_cols = ["mrp", "max_retail_price", "retail_price"]
        qty_cols = ["quantity", "qty", "stock", "available_qty"]
        sku_cols = ["sku", "product_code", "code", "item_code"]
        barcode_cols = ["barcode", "ean", "upc"]
        
        def get_first_match(cols):
            for col in cols:
                if col in row and row[col]:
                    return row[col]
            return None
        
        return {
            "external_id": str(row.get("product_id", row.get("id", ""))),
            "sku": get_first_match(sku_cols) or str(row.get("product_id", "")),
            "name": get_first_match(name_cols) or "",
            "description": row.get("description", ""),
            "mrp": float(get_first_match(mrp_cols) or 0),
            "price": float(get_first_match(price_cols) or 0),
            "cost_price": float(row.get("cost_price", row.get("purchase_price", 0)) or 0),
            "quantity": int(get_first_match(qty_cols) or 0),
            "unit": row.get("unit", "pcs"),
            "barcode": get_first_match(barcode_cols) or "",
            "category": row.get("category", row.get("category_name", "General")),
            "hsn_code": row.get("hsn_code", row.get("hsn", "")),
            "gst_percent": float(row.get("gst_rate", row.get("gst", row.get("tax", 0))) or 0),
            "is_active": True,
            "min_stock": int(row.get("min_stock", row.get("reorder_level", 5)) or 5),
            "image_url": row.get("image_url", row.get("image", "")),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    def fetch_inventory(self) -> List[Dict[str, Any]]:
        """Fetch current inventory/stock levels"""
        if self.config.connection_type == KasaPOSConnectionType.MYSQL:
            return self._fetch_inventory_mysql()
        elif self.config.connection_type == KasaPOSConnectionType.SQLITE:
            return self._fetch_inventory_sqlite()
        elif self.config.connection_type == KasaPOSConnectionType.CSV:
            return self._fetch_inventory_csv()
        return []
    
    def _fetch_inventory_mysql(self) -> List[Dict[str, Any]]:
        """Fetch inventory from MySQL"""
        inventory = []
        cursor = self.connection.cursor(dictionary=True)
        
        try:
            query = f"""
                SELECT 
                    s.product_id,
                    p.product_code as sku,
                    p.barcode,
                    s.quantity,
                    s.updated_at
                FROM {self.INVENTORY_TABLE} s
                JOIN {self.PRODUCT_TABLE} p ON s.product_id = p.product_id
                WHERE p.is_active = 1
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                inventory.append({
                    "external_id": str(row["product_id"]),
                    "sku": row.get("sku") or row.get("barcode"),
                    "quantity": int(row["quantity"])
                })
            
            logger.info(f"Fetched {len(inventory)} inventory records from KasaPOS")
            
        except Exception as e:
            logger.error(f"Failed to fetch inventory: {e}")
        finally:
            cursor.close()
        
        return inventory
    
    def _fetch_inventory_sqlite(self) -> List[Dict[str, Any]]:
        """Fetch inventory from SQLite"""
        inventory = []
        cursor = self.connection.cursor()
        
        try:
            query = f"""
                SELECT 
                    s.product_id,
                    p.product_code as sku,
                    p.barcode,
                    s.quantity
                FROM {self.INVENTORY_TABLE} s
                JOIN {self.PRODUCT_TABLE} p ON s.product_id = p.product_id
                WHERE p.is_active = 1
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                row_dict = dict(row)
                inventory.append({
                    "external_id": str(row_dict["product_id"]),
                    "sku": row_dict.get("sku") or row_dict.get("barcode"),
                    "quantity": int(row_dict["quantity"])
                })
            
            logger.info(f"Fetched {len(inventory)} inventory records from KasaPOS")
            
        except Exception as e:
            logger.error(f"Failed to fetch inventory: {e}")
        finally:
            cursor.close()
        
        return inventory
    
    def _fetch_inventory_csv(self) -> List[Dict[str, Any]]:
        """Fetch inventory from CSV"""
        inventory = []
        csv_path = Path(self.config.export_folder) / self.config.inventory_file
        
        try:
            if not csv_path.exists():
                logger.warning(f"Inventory CSV not found: {csv_path}")
                return []
            
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    inventory.append({
                        "external_id": str(row.get("product_id", row.get("id", ""))),
                        "sku": row.get("sku", row.get("product_code", row.get("barcode", ""))),
                        "quantity": int(row.get("quantity", row.get("qty", row.get("stock", 0))) or 0)
                    })
            
            logger.info(f"Fetched {len(inventory)} inventory records from CSV")
            
        except Exception as e:
            logger.error(f"Failed to fetch inventory from CSV: {e}")
        
        return inventory
    
    def fetch_recent_sales(self, days: int = 1) -> List[Dict[str, Any]]:
        """Fetch recent sales/orders for analytics"""
        if self.config.connection_type == KasaPOSConnectionType.MYSQL:
            return self._fetch_sales_mysql(days)
        elif self.config.connection_type == KasaPOSConnectionType.CSV:
            return self._fetch_sales_csv()
        return []
    
    def _fetch_sales_mysql(self, days: int = 1) -> List[Dict[str, Any]]:
        """Fetch sales from MySQL"""
        sales = []
        cursor = self.connection.cursor(dictionary=True)
        
        try:
            since_date = datetime.now() - timedelta(days=days)
            
            query = f"""
                SELECT 
                    s.sale_id,
                    s.invoice_number,
                    s.sale_date,
                    s.total_amount,
                    s.discount_amount,
                    s.tax_amount,
                    s.net_amount,
                    s.payment_mode,
                    s.customer_name,
                    s.customer_phone
                FROM {self.SALES_TABLE} s
                WHERE s.sale_date >= %s
                ORDER BY s.sale_date DESC
            """
            
            cursor.execute(query, (since_date,))
            rows = cursor.fetchall()
            
            for row in rows:
                sales.append({
                    "order_id": str(row["sale_id"]),
                    "invoice_number": row.get("invoice_number"),
                    "order_date": str(row["sale_date"]),
                    "total": float(row.get("total_amount", 0)),
                    "discount": float(row.get("discount_amount", 0) or 0),
                    "tax": float(row.get("tax_amount", 0) or 0),
                    "net_total": float(row.get("net_amount", 0)),
                    "payment_method": row.get("payment_mode", "cash"),
                    "customer_name": row.get("customer_name"),
                    "customer_phone": row.get("customer_phone")
                })
            
            logger.info(f"Fetched {len(sales)} recent sales from KasaPOS")
            
        except Exception as e:
            logger.error(f"Failed to fetch sales: {e}")
        finally:
            cursor.close()
        
        return sales
    
    def _fetch_sales_csv(self) -> List[Dict[str, Any]]:
        """Fetch sales from CSV export"""
        sales = []
        csv_path = Path(self.config.export_folder) / self.config.orders_file
        
        try:
            if not csv_path.exists():
                logger.warning(f"Sales CSV not found: {csv_path}")
                return []
            
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sales.append({
                        "order_id": str(row.get("sale_id", row.get("id", ""))),
                        "invoice_number": row.get("invoice_number", row.get("invoice_no", "")),
                        "order_date": row.get("sale_date", row.get("date", "")),
                        "total": float(row.get("total_amount", row.get("total", 0)) or 0),
                        "discount": float(row.get("discount", 0) or 0),
                        "tax": float(row.get("tax", row.get("gst", 0)) or 0),
                        "net_total": float(row.get("net_amount", row.get("net_total", 0)) or 0),
                        "payment_method": row.get("payment_mode", row.get("payment", "cash")),
                        "customer_name": row.get("customer_name", row.get("customer", "")),
                        "customer_phone": row.get("customer_phone", row.get("phone", ""))
                    })
            
            logger.info(f"Fetched {len(sales)} sales from CSV")
            
        except Exception as e:
            logger.error(f"Failed to fetch sales from CSV: {e}")
        
        return sales
    
    def mark_sync_complete(self):
        """Mark sync as complete and update timestamp"""
        self._save_last_sync_time()
        logger.info("Sync marked complete")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection and return diagnostic info"""
        result = {
            "connected": False,
            "connection_type": self.config.connection_type.value,
            "message": "",
            "product_count": 0,
            "tables_found": []
        }
        
        try:
            if self.connect():
                result["connected"] = True
                result["message"] = "Connection successful"
                
                # Try to count products
                products = self.fetch_products(full_sync=True)
                result["product_count"] = len(products)
                
                # List tables (for database connections)
                if self.config.connection_type == KasaPOSConnectionType.MYSQL:
                    cursor = self.connection.cursor()
                    cursor.execute("SHOW TABLES")
                    result["tables_found"] = [row[0] for row in cursor.fetchall()]
                    cursor.close()
                elif self.config.connection_type == KasaPOSConnectionType.SQLITE:
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    result["tables_found"] = [row[0] for row in cursor.fetchall()]
                    cursor.close()
                
                self.disconnect()
            else:
                result["message"] = "Connection failed"
                
        except Exception as e:
            result["message"] = f"Error: {str(e)}"
        
        return result


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="KasaPOS Integration Adapter")
    parser.add_argument("--test", action="store_true", help="Test connection")
    parser.add_argument("--type", choices=["mysql", "sqlite", "csv", "excel"], 
                       default="mysql", help="Connection type")
    parser.add_argument("--host", default="localhost", help="MySQL host")
    parser.add_argument("--port", type=int, default=3306, help="MySQL port")
    parser.add_argument("--user", default="root", help="MySQL user")
    parser.add_argument("--password", default="", help="MySQL password")
    parser.add_argument("--database", default="kasapos", help="MySQL database")
    parser.add_argument("--sqlite-path", help="SQLite database path")
    parser.add_argument("--export-folder", help="CSV/Excel export folder")
    
    args = parser.parse_args()
    
    config = KasaPOSConfig(
        connection_type=KasaPOSConnectionType(args.type),
        mysql_host=args.host,
        mysql_port=args.port,
        mysql_user=args.user,
        mysql_password=args.password,
        mysql_database=args.database,
        sqlite_path=args.sqlite_path or "",
        export_folder=args.export_folder or ""
    )
    
    adapter = KasaPOSAdapter(config)
    
    if args.test:
        print("Testing KasaPOS connection...")
        result = adapter.test_connection()
        print(json.dumps(result, indent=2))
    else:
        print("Use --test to test connection")
        print("Example: python kasapos_adapter.py --test --type mysql --host localhost --database kasapos")
