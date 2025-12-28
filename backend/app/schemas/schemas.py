"""
Pydantic Schemas for Request/Response Validation
"""
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# Enums matching database enums
class StoreStatus(str, Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class StoreTier(str, Enum):
    TIER1 = "tier1"
    TIER2 = "tier2"
    TIER3 = "tier3"
    TIER4 = "tier4"


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COD = "cod"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


# Base response wrapper
class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool
    data: Optional[Any] = None
    meta: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Store Schemas
class StoreBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None


class StoreCreate(StoreBase):
    external_id: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=2, max_length=200)
    domain: Optional[str] = None


class StoreResponse(StoreBase):
    id: UUID
    slug: str
    domain: Optional[str]
    status: StoreStatus
    sync_tier: StoreTier
    is_active: bool
    logo_url: Optional[str]
    primary_color: str
    secondary_color: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Product Schemas
class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=500)
    description: Optional[str] = None
    short_description: Optional[str] = None
    mrp: float = Field(..., gt=0)
    selling_price: float = Field(..., gt=0)
    quantity: int = Field(default=0, ge=0)
    unit: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[UUID] = None


class ProductCreate(ProductBase):
    external_id: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=2, max_length=500)
    
    @validator('selling_price')
    def selling_price_not_greater_than_mrp(cls, v, values):
        if 'mrp' in values and v > values['mrp']:
            raise ValueError('Selling price cannot be greater than MRP')
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=500)
    description: Optional[str] = None
    short_description: Optional[str] = None
    mrp: Optional[float] = Field(None, gt=0)
    selling_price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    category_id: Optional[UUID] = None


class ProductResponse(ProductBase):
    id: UUID
    store_id: UUID
    external_id: str
    slug: str
    discount_percent: float
    images: List[str] = []
    thumbnail: Optional[str]
    is_active: bool
    is_featured: bool
    is_in_stock: bool
    last_synced_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Paginated product list"""
    products: List[ProductResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# Sync Schemas
class SyncProductItem(BaseModel):
    """Single product in sync batch"""
    external_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=2)
    description: Optional[str] = None
    mrp: float = Field(..., gt=0)
    selling_price: float = Field(..., gt=0)
    quantity: int = Field(default=0, ge=0)
    unit: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    hsn_code: Optional[str] = None
    gst_percent: Optional[float] = Field(default=0, ge=0, le=100)
    updated_at: Optional[datetime] = None


class SyncBatchRequest(BaseModel):
    """Batch sync request from sync agent"""
    store_id: UUID
    sync_type: str = Field(..., pattern="^(delta|full|inventory_only)$")
    timestamp: datetime
    products: List[SyncProductItem] = Field(..., max_items=1000)
    
    @validator('products')
    def validate_products(cls, v):
        if len(v) == 0:
            raise ValueError('Products list cannot be empty')
        return v


class SyncBatchResponse(BaseModel):
    """Response for batch sync"""
    success: bool
    sync_id: UUID
    processed: int
    created: int
    updated: int
    failed: int
    errors: List[Dict[str, Any]] = []
    next_sync_recommended_at: datetime
    duration_seconds: float


# Order Schemas
class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=200)
    customer_phone: str = Field(..., pattern=r'^\+?[1-9]\d{9,14}$')
    customer_email: Optional[EmailStr] = None
    delivery_address: str = Field(..., min_length=10)
    delivery_city: str
    delivery_state: str
    delivery_pincode: str = Field(..., pattern=r'^\d{6}$')
    delivery_landmark: Optional[str] = None
    payment_method: str = Field(default="COD")
    notes: Optional[str] = None
    items: List[OrderItemCreate] = Field(..., min_items=1, max_items=50)


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str
    product_sku: Optional[str]
    unit_price: float
    quantity: int
    subtotal: float
    tax_amount: float
    total: float
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: UUID
    order_number: str
    store_id: UUID
    customer_name: str
    customer_phone: str
    customer_email: Optional[str]
    delivery_address: str
    order_status: OrderStatus
    payment_status: PaymentStatus
    payment_method: str
    subtotal: float
    tax_amount: float
    discount_amount: float
    delivery_charge: float
    total_amount: float
    items: List[OrderItemResponse]
    created_at: datetime
    expected_delivery_date: Optional[datetime]
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Paginated order list"""
    orders: List[OrderResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# Category Schemas
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None


class CategoryResponse(BaseModel):
    id: UUID
    store_id: UUID
    name: str
    slug: str
    description: Optional[str]
    parent_id: Optional[UUID]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Authentication
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class APIKeyAuth(BaseModel):
    api_key: str = Field(..., min_length=32)
