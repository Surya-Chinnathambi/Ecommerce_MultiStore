"""
Billing Integration Models
Handles connections to external billing/accounting software
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class BillingProvider(str, enum.Enum):
    """Supported billing providers"""
    QUICKBOOKS = "quickbooks"
    XERO = "xero"
    ZOHO_BOOKS = "zoho_books"
    TALLY = "tally"
    SAGE = "sage"
    FRESHBOOKS = "freshbooks"
    WAVE = "wave"
    CUSTOM_API = "custom_api"
    CSV_EXCEL = "csv_excel"
    MANUAL = "manual"


class SyncDirection(str, enum.Enum):
    """Data sync direction"""
    PULL = "pull"  # Import from billing software
    PUSH = "push"  # Export to billing software
    BIDIRECTIONAL = "bidirectional"  # Both ways


class SyncStatus(str, enum.Enum):
    """Sync operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class EntityType(str, enum.Enum):
    """Types of entities to sync"""
    INVOICE = "invoice"
    PRODUCT = "product"
    CUSTOMER = "customer"
    PAYMENT = "payment"
    TAX = "tax"
    EXPENSE = "expense"
    INVENTORY = "inventory"


class BillingIntegration(Base):
    """Billing software integration configuration"""
    __tablename__ = "billing_integrations"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Store
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Integration Details
    name = Column(String(200), nullable=False)  # User-friendly name
    provider = Column(SQLEnum(BillingProvider), nullable=False, index=True)
    
    # Configuration
    config = Column(JSONB, default={})  # API keys, endpoints, credentials (encrypted)
    is_active = Column(Boolean, default=True, index=True)
    auto_sync = Column(Boolean, default=False)  # Enable automatic sync
    sync_direction = Column(SQLEnum(SyncDirection), default=SyncDirection.PUSH)
    sync_frequency_minutes = Column(Integer, default=60)  # How often to sync (if auto_sync)
    
    # Sync Settings
    sync_entities = Column(JSONB, default=[])  # List of entity types to sync
    field_mapping = Column(JSONB, default={})  # Custom field mappings
    
    # Status
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(50), nullable=True)
    last_sync_message = Column(Text, nullable=True)
    total_syncs = Column(Integer, default=0)
    successful_syncs = Column(Integer, default=0)
    failed_syncs = Column(Integer, default=0)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    store = relationship("Store", backref="billing_integrations")
    sync_logs = relationship("BillingSyncLog", back_populates="integration", cascade="all, delete-orphan")


class BillingSyncLog(Base):
    """Log of billing sync operations"""
    __tablename__ = "billing_sync_logs"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign Keys
    integration_id = Column(UUID(as_uuid=True), ForeignKey("billing_integrations.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Sync Details
    sync_type = Column(String(50), nullable=False)  # manual, auto, scheduled
    entity_type = Column(SQLEnum(EntityType), nullable=False, index=True)
    direction = Column(SQLEnum(SyncDirection), nullable=False)
    status = Column(SQLEnum(SyncStatus), nullable=False, index=True)
    
    # Results
    records_processed = Column(Integer, default=0)
    records_succeeded = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    
    # Details
    summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    details = Column(JSONB, default={})  # Detailed results, errors, etc.
    
    # Performance
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Metadata
    triggered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    integration = relationship("BillingIntegration", back_populates="sync_logs")
    store = relationship("Store")


class InvoiceExport(Base):
    """Exported invoice records"""
    __tablename__ = "invoice_exports"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign Keys
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("billing_integrations.id", ondelete="SET NULL"), nullable=True, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Export Details
    invoice_number = Column(String(100), nullable=False, index=True)
    external_id = Column(String(200), nullable=True, index=True)  # ID in external system
    provider = Column(SQLEnum(BillingProvider), nullable=False)
    
    # Data
    invoice_data = Column(JSONB, default={})  # Full invoice data exported
    export_format = Column(String(50), default="json")  # json, xml, csv, etc.
    
    # Status
    status = Column(String(50), default="pending", index=True)
    exported_at = Column(DateTime, nullable=True)
    synced_at = Column(DateTime, nullable=True)  # When acknowledged by external system
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # File exports (for CSV/Excel)
    file_path = Column(String(500), nullable=True)
    file_url = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    order = relationship("Order")
    integration = relationship("BillingIntegration")
    store = relationship("Store")


class ProductImport(Base):
    """Imported product records from billing software"""
    __tablename__ = "product_imports"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign Keys
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("billing_integrations.id", ondelete="SET NULL"), nullable=True, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Import Details
    external_id = Column(String(200), nullable=False, index=True)
    external_sku = Column(String(100), nullable=True)
    provider = Column(SQLEnum(BillingProvider), nullable=False)
    
    # Data
    product_data = Column(JSONB, default={})  # Raw data from external system
    import_format = Column(String(50), default="json")
    
    # Mapping
    field_mappings = Column(JSONB, default={})  # How fields were mapped
    
    # Status
    status = Column(String(50), default="pending", index=True)
    imported_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    product = relationship("Product")
    integration = relationship("BillingIntegration")
    store = relationship("Store")


class CSVTemplate(Base):
    """CSV/Excel templates for import/export"""
    __tablename__ = "csv_templates"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Store
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Template Details
    name = Column(String(200), nullable=False)
    entity_type = Column(SQLEnum(EntityType), nullable=False)
    direction = Column(SQLEnum(SyncDirection), nullable=False)
    
    # Configuration
    column_mappings = Column(JSONB, default={})  # Maps CSV columns to system fields
    delimiter = Column(String(1), default=",")
    has_header = Column(Boolean, default=True)
    encoding = Column(String(20), default="utf-8")
    
    # Template file (for exports)
    template_file = Column(String(500), nullable=True)
    sample_file = Column(String(500), nullable=True)
    
    # Settings
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    store = relationship("Store")
