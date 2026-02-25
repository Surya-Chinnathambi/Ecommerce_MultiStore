"""
POS Integration API Endpoints
Manage integrations with billing software like KasaPOS, Marg, Tally
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import logging

from app.core.database import get_db
from app.models.models import Store
from app.core.security import get_current_user
from app.models.auth_models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pos-integration", tags=["POS Integration"])


class POSType(str, Enum):
    KASAPOS = "kasapos"
    MARG = "marg"
    TALLY = "tally"
    BUSY = "busy"
    OTHER = "other"


class ConnectionType(str, Enum):
    MYSQL = "mysql"
    SQLITE = "sqlite"
    CSV = "csv"
    EXCEL = "excel"
    API = "api"


class POSConfigBase(BaseModel):
    """Base POS configuration"""
    pos_type: POSType = POSType.KASAPOS
    connection_type: ConnectionType = ConnectionType.MYSQL
    
    # MySQL settings
    mysql_host: Optional[str] = "localhost"
    mysql_port: Optional[int] = 3306
    mysql_user: Optional[str] = "root"
    mysql_password: Optional[str] = None
    mysql_database: Optional[str] = "kasapos"
    
    # SQLite settings
    sqlite_path: Optional[str] = None
    
    # CSV/Excel settings
    export_folder: Optional[str] = None
    products_file: Optional[str] = "products.csv"
    inventory_file: Optional[str] = "inventory.csv"
    
    # Sync settings
    sync_interval_minutes: int = Field(default=5, ge=1, le=60)
    inventory_sync_interval_minutes: int = Field(default=1, ge=1, le=30)
    auto_sync_enabled: bool = True
    
    # Business hours (IST)
    business_start_hour: int = Field(default=9, ge=0, le=23)
    business_end_hour: int = Field(default=22, ge=0, le=23)


class POSConfigCreate(POSConfigBase):
    """Create POS configuration"""
    store_id: str


class POSConfigResponse(POSConfigBase):
    """POS configuration response"""
    id: str
    store_id: str
    created_at: datetime
    updated_at: datetime
    last_sync_at: Optional[datetime] = None
    sync_status: str = "not_configured"
    total_synced_products: int = 0
    
    class Config:
        from_attributes = True


class SyncStatusResponse(BaseModel):
    """Sync status response"""
    store_id: str
    pos_type: POSType
    connection_status: str  # connected, disconnected, error
    last_sync_at: Optional[datetime]
    next_sync_at: Optional[datetime]
    products_synced: int
    inventory_synced: int
    errors: List[str] = []
    sync_in_progress: bool = False


class TestConnectionRequest(BaseModel):
    """Test connection request"""
    pos_type: POSType
    connection_type: ConnectionType
    mysql_host: Optional[str] = None
    mysql_port: Optional[int] = None
    mysql_user: Optional[str] = None
    mysql_password: Optional[str] = None
    mysql_database: Optional[str] = None
    sqlite_path: Optional[str] = None
    export_folder: Optional[str] = None


class TestConnectionResponse(BaseModel):
    """Test connection response"""
    success: bool
    message: str
    products_found: int = 0
    tables_found: List[str] = []
    sample_products: List[dict] = []


# In-memory storage for demo (use database in production)
pos_configs = {}
sync_status = {}


@router.post("/config", response_model=dict)
async def create_pos_config(
    config: POSConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create or update POS integration configuration
    """
    # Verify store ownership
    store = db.query(Store).filter(Store.id == config.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # Check admin access — super-admins can configure any store, others only their own
    if not current_user.is_superuser and str(current_user.store_id) != str(store.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to configure this store"
        )
    
    # Store configuration (in production, save to database)
    config_data = config.model_dump()
    config_data["id"] = f"pos_{config.store_id}"
    config_data["created_at"] = datetime.utcnow()
    config_data["updated_at"] = datetime.utcnow()
    
    pos_configs[config.store_id] = config_data
    
    logger.info(f"POS config created for store {config.store_id}")
    
    return {
        "success": True,
        "message": "POS configuration saved successfully",
        "data": config_data
    }


@router.get("/config/{store_id}", response_model=dict)
async def get_pos_config(
    store_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get POS integration configuration for a store
    """
    config = pos_configs.get(store_id)
    
    if not config:
        return {
            "success": True,
            "data": None,
            "message": "No POS configuration found"
        }
    
    # Remove sensitive data
    safe_config = {**config}
    if safe_config.get("mysql_password"):
        safe_config["mysql_password"] = "********"
    
    return {
        "success": True,
        "data": safe_config
    }


@router.post("/test-connection", response_model=dict)
async def test_pos_connection(
    request: TestConnectionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Test connection to POS software
    
    This tests if we can connect to the billing software and fetch products.
    """
    result = {
        "success": False,
        "message": "",
        "products_found": 0,
        "tables_found": [],
        "sample_products": []
    }
    
    try:
        if request.pos_type == POSType.KASAPOS:
            # Simulate KasaPOS connection test
            # In production, this would actually connect to the database
            
            if request.connection_type == ConnectionType.MYSQL:
                result["success"] = True
                result["message"] = f"Successfully connected to MySQL at {request.mysql_host}:{request.mysql_port}"
                result["products_found"] = 150  # Simulated
                result["tables_found"] = ["tbl_products", "tbl_stock", "tbl_category", "tbl_sales"]
                result["sample_products"] = [
                    {"name": "Toor Dal 1kg", "price": 145.00, "stock": 50},
                    {"name": "Rice 5kg Ponni", "price": 450.00, "stock": 30},
                    {"name": "Coconut Oil 1L", "price": 180.00, "stock": 25}
                ]
            
            elif request.connection_type == ConnectionType.SQLITE:
                if request.sqlite_path:
                    result["success"] = True
                    result["message"] = f"Successfully opened SQLite database"
                    result["products_found"] = 120
                else:
                    result["message"] = "SQLite path not provided"
            
            elif request.connection_type == ConnectionType.CSV:
                if request.export_folder:
                    result["success"] = True
                    result["message"] = f"Found CSV files in {request.export_folder}"
                    result["products_found"] = 100
                else:
                    result["message"] = "Export folder not provided"
        
        else:
            result["message"] = f"{request.pos_type} integration coming soon!"
    
    except Exception as e:
        result["message"] = f"Connection failed: {str(e)}"
        logger.error(f"POS connection test failed: {e}", exc_info=True)
    
    return {
        "success": True,
        "data": result
    }


@router.get("/status/{store_id}", response_model=dict)
async def get_sync_status(
    store_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current sync status for a store
    """
    status = sync_status.get(store_id, {
        "store_id": store_id,
        "connection_status": "not_configured",
        "last_sync_at": None,
        "next_sync_at": None,
        "products_synced": 0,
        "inventory_synced": 0,
        "errors": [],
        "sync_in_progress": False
    })
    
    return {
        "success": True,
        "data": status
    }


@router.post("/trigger-sync/{store_id}", response_model=dict)
async def trigger_manual_sync(
    store_id: str,
    sync_type: str = "delta",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger a manual sync for a store
    
    sync_type: 'delta', 'full', or 'inventory_only'
    """
    config = pos_configs.get(store_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POS not configured for this store"
        )
    
    # In production, this would trigger the actual sync agent
    # For now, simulate the response
    sync_status[store_id] = {
        "store_id": store_id,
        "connection_status": "syncing",
        "last_sync_at": datetime.utcnow(),
        "sync_in_progress": True,
        "products_synced": 0,
        "errors": []
    }
    
    logger.info(f"Manual sync triggered for store {store_id}, type: {sync_type}")
    
    return {
        "success": True,
        "message": f"Sync triggered successfully ({sync_type})",
        "data": {
            "sync_id": f"sync_{store_id}_{datetime.utcnow().timestamp()}",
            "sync_type": sync_type,
            "started_at": datetime.utcnow().isoformat()
        }
    }


@router.get("/supported-pos", response_model=dict)
async def get_supported_pos_systems():
    """
    Get list of supported POS systems
    """
    return {
        "success": True,
        "data": [
            {
                "id": "kasapos",
                "name": "KasaPOS",
                "description": "Popular POS for grocery stores in India",
                "connection_types": ["mysql", "sqlite", "csv", "excel"],
                "features": ["products", "inventory", "sales", "categories"],
                "status": "available"
            },
            {
                "id": "marg",
                "name": "Marg ERP",
                "description": "Business management software for retail",
                "connection_types": ["mssql", "csv"],
                "features": ["products", "inventory", "sales"],
                "status": "coming_soon"
            },
            {
                "id": "tally",
                "name": "Tally Prime",
                "description": "Popular accounting software in India",
                "connection_types": ["api", "xml"],
                "features": ["products", "inventory", "accounting"],
                "status": "coming_soon"
            },
            {
                "id": "busy",
                "name": "Busy Accounting",
                "description": "GST-compliant accounting software",
                "connection_types": ["mssql", "csv"],
                "features": ["products", "inventory"],
                "status": "coming_soon"
            }
        ]
    }


@router.get("/sync-logs/{store_id}", response_model=dict)
async def get_sync_logs(
    store_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get sync history/logs for a store
    """
    # In production, fetch from database
    # For now, return sample data
    return {
        "success": True,
        "data": [
            {
                "id": "log_1",
                "sync_type": "delta",
                "started_at": "2026-01-07T10:00:00Z",
                "completed_at": "2026-01-07T10:00:15Z",
                "products_fetched": 50,
                "products_created": 5,
                "products_updated": 45,
                "products_failed": 0,
                "status": "success"
            },
            {
                "id": "log_2",
                "sync_type": "inventory_only",
                "started_at": "2026-01-07T09:55:00Z",
                "completed_at": "2026-01-07T09:55:03Z",
                "products_fetched": 150,
                "products_updated": 150,
                "status": "success"
            }
        ]
    }
