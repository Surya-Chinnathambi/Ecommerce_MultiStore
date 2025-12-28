"""
Billing integration schemas
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, validator
from app.models.billing_models import BillingProvider, SyncDirection, SyncStatus, EntityType


# ==================== Integration Schemas ====================

class BillingIntegrationBase(BaseModel):
    """Base integration schema"""
    name: str = Field(..., min_length=1, max_length=200)
    provider: BillingProvider
    config: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    auto_sync: bool = False
    sync_direction: SyncDirection = SyncDirection.PUSH
    sync_frequency_minutes: int = Field(60, ge=5, le=1440)
    sync_entities: List[EntityType] = Field(default_factory=list)
    field_mapping: Dict[str, str] = Field(default_factory=dict)


class BillingIntegrationCreate(BillingIntegrationBase):
    """Create integration request"""
    pass


class BillingIntegrationUpdate(BaseModel):
    """Update integration request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    auto_sync: Optional[bool] = None
    sync_direction: Optional[SyncDirection] = None
    sync_frequency_minutes: Optional[int] = Field(None, ge=5, le=1440)
    sync_entities: Optional[List[EntityType]] = None
    field_mapping: Optional[Dict[str, str]] = None


class BillingIntegrationResponse(BillingIntegrationBase):
    """Integration response"""
    id: UUID
    store_id: UUID
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    last_sync_message: Optional[str] = None
    total_syncs: int
    successful_syncs: int
    failed_syncs: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Sync Schemas ====================

class SyncRequest(BaseModel):
    """Manual sync request"""
    entity_types: List[EntityType]
    direction: SyncDirection = SyncDirection.PUSH
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: Optional[int] = Field(None, ge=1, le=10000)


class SyncLogResponse(BaseModel):
    """Sync log response"""
    id: UUID
    integration_id: UUID
    sync_type: str
    entity_type: EntityType
    direction: SyncDirection
    status: SyncStatus
    records_processed: int
    records_succeeded: int
    records_failed: int
    records_skipped: int
    summary: Optional[str] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True


class SyncStats(BaseModel):
    """Sync statistics"""
    total_syncs: int
    successful_syncs: int
    failed_syncs: int
    success_rate: float
    last_sync_at: Optional[datetime] = None
    avg_duration_seconds: Optional[float] = None
    by_entity_type: Dict[str, int]
    recent_logs: List[SyncLogResponse]


# ==================== Invoice Export Schemas ====================

class InvoiceExportRequest(BaseModel):
    """Export invoice request"""
    order_ids: List[UUID] = Field(..., min_items=1)
    integration_id: Optional[UUID] = None
    format: str = Field("json", pattern="^(json|xml|csv|pdf)$")


class InvoiceExportResponse(BaseModel):
    """Invoice export response"""
    id: UUID
    order_id: UUID
    invoice_number: str
    external_id: Optional[str] = None
    provider: BillingProvider
    status: str
    exported_at: Optional[datetime] = None
    file_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceExportBulkResponse(BaseModel):
    """Bulk export response"""
    total: int
    succeeded: int
    failed: int
    exports: List[InvoiceExportResponse]
    errors: List[Dict[str, str]] = Field(default_factory=list)


# ==================== Product Import Schemas ====================

class ProductImportRequest(BaseModel):
    """Import products request"""
    integration_id: Optional[UUID] = None
    source_format: str = Field("json", pattern="^(json|xml|csv)$")
    products: List[Dict[str, Any]] = Field(default_factory=list)
    file_url: Optional[str] = None
    auto_create: bool = True
    update_existing: bool = True


class ProductImportResponse(BaseModel):
    """Product import response"""
    id: UUID
    product_id: Optional[UUID] = None
    external_id: str
    provider: BillingProvider
    status: str
    imported_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProductImportBulkResponse(BaseModel):
    """Bulk import response"""
    total: int
    succeeded: int
    failed: int
    skipped: int
    imports: List[ProductImportResponse]
    errors: List[Dict[str, str]] = Field(default_factory=list)


# ==================== CSV Template Schemas ====================

class CSVTemplateCreate(BaseModel):
    """Create CSV template"""
    name: str = Field(..., min_length=1, max_length=200)
    entity_type: EntityType
    direction: SyncDirection
    column_mappings: Dict[str, str]
    delimiter: str = Field(",", max_length=1)
    has_header: bool = True
    encoding: str = Field("utf-8", pattern="^(utf-8|latin-1|ascii)$")
    is_default: bool = False


class CSVTemplateUpdate(BaseModel):
    """Update CSV template"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    column_mappings: Optional[Dict[str, str]] = None
    delimiter: Optional[str] = Field(None, max_length=1)
    has_header: Optional[bool] = None
    encoding: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class CSVTemplateResponse(BaseModel):
    """CSV template response"""
    id: str
    name: str
    entity_type: EntityType
    direction: SyncDirection
    column_mappings: Dict[str, str]
    delimiter: str
    has_header: bool
    encoding: str
    is_default: bool
    is_active: bool
    template_file: Optional[str] = None
    sample_file: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Export/Import File Schemas ====================

class CSVExportRequest(BaseModel):
    """Export data to CSV"""
    entity_type: EntityType
    template_id: Optional[str] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(1000, ge=1, le=100000)


class CSVImportRequest(BaseModel):
    """Import data from CSV"""
    entity_type: EntityType
    template_id: Optional[str] = None
    file_url: str
    auto_create: bool = True
    update_existing: bool = True
    skip_errors: bool = False


class FileExportResponse(BaseModel):
    """File export response"""
    file_url: str
    file_name: str
    file_size: int
    row_count: int
    format: str
    expires_at: datetime


class FileImportResponse(BaseModel):
    """File import response"""
    total_rows: int
    processed: int
    succeeded: int
    failed: int
    skipped: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    created_ids: List[str] = Field(default_factory=list)
    updated_ids: List[str] = Field(default_factory=list)


# ==================== Provider Config Schemas ====================

class QuickBooksConfig(BaseModel):
    """QuickBooks configuration"""
    client_id: str
    client_secret: str
    realm_id: str
    redirect_uri: str
    environment: str = Field("sandbox", pattern="^(sandbox|production)$")


class XeroConfig(BaseModel):
    """Xero configuration"""
    client_id: str
    client_secret: str
    tenant_id: str
    redirect_uri: str


class TallyConfig(BaseModel):
    """Tally configuration"""
    server_url: str
    port: int = 9000
    company_name: str
    username: Optional[str] = None
    password: Optional[str] = None


class CustomAPIConfig(BaseModel):
    """Custom API configuration"""
    base_url: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    auth_type: str = Field("bearer", pattern="^(bearer|basic|apikey|oauth2)$")
    headers: Dict[str, str] = Field(default_factory=dict)
    endpoints: Dict[str, str] = Field(default_factory=dict)


# ==================== Validation Schemas ====================

class ConnectionTestRequest(BaseModel):
    """Test connection request"""
    provider: BillingProvider
    config: Dict[str, Any]


class ConnectionTestResponse(BaseModel):
    """Test connection response"""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
