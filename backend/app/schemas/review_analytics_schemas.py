"""
Pydantic schemas for reviews and analytics
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID


# Review Schemas
class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    title: Optional[str] = Field(None, max_length=200)
    review_text: Optional[str] = None
    images: Optional[str] = None  # JSON array of image URLs


class ReviewCreate(ReviewBase):
    product_id: UUID
    order_id: Optional[UUID] = None


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    review_text: Optional[str] = None
    images: Optional[str] = None


class ReviewResponse(ReviewBase):
    id: UUID
    product_id: UUID
    store_id: UUID
    user_id: UUID
    order_id: Optional[UUID]
    is_verified_purchase: bool
    is_approved: bool
    is_featured: bool
    helpful_count: int
    not_helpful_count: int
    created_at: datetime
    updated_at: datetime
    user_name: Optional[str] = None
    responses: List['StoreReviewResponse'] = []

    class Config:
        from_attributes = True


class StoreReviewResponseCreate(BaseModel):
    response_text: str = Field(..., min_length=10, max_length=1000)
    responder_name: str = Field(..., max_length=200)


class StoreReviewResponse(BaseModel):
    id: UUID
    review_id: UUID
    store_id: UUID
    responder_name: str
    response_text: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewHelpfulCreate(BaseModel):
    is_helpful: bool


class ReviewStats(BaseModel):
    total_reviews: int
    average_rating: float
    rating_distribution: dict  # {1: count, 2: count, ...}
    verified_purchase_percentage: float


# Analytics Schemas
class DailyAnalyticsResponse(BaseModel):
    id: UUID
    store_id: UUID
    date: date
    total_orders: int
    total_revenue: float
    total_items_sold: int
    average_order_value: float
    pending_orders: int
    confirmed_orders: int
    delivered_orders: int
    cancelled_orders: int
    new_customers: int
    returning_customers: int
    total_customers: int
    unique_products_sold: int
    out_of_stock_count: int
    low_stock_count: int
    page_views: int
    unique_visitors: int
    conversion_rate: float
    metrics: dict

    class Config:
        from_attributes = True


class ProductAnalyticsResponse(BaseModel):
    id: UUID
    product_id: UUID
    store_id: UUID
    date: date
    units_sold: int
    revenue: float
    orders_count: int
    views: int
    add_to_cart: int
    conversion_rate: float
    new_reviews: int
    average_rating: float

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    # Today's metrics
    today_orders: int
    today_revenue: float
    today_customers: int
    
    # Comparisons (vs yesterday)
    orders_change: float  # percentage
    revenue_change: float
    customers_change: float
    
    # Week metrics
    week_orders: int
    week_revenue: float
    week_customers: int
    
    # Month metrics
    month_orders: int
    month_revenue: float
    month_customers: int
    
    # Top performers
    top_products: List[dict]
    recent_orders: List[dict]
    
    # Inventory alerts
    low_stock_products: int
    out_of_stock_products: int


class SalesChartData(BaseModel):
    dates: List[str]
    revenue: List[float]
    orders: List[int]
    customers: List[int]


class InventoryAlertResponse(BaseModel):
    id: UUID
    product_id: UUID
    store_id: UUID
    alert_type: str
    current_quantity: int
    threshold_quantity: int
    is_resolved: bool
    is_notified: bool
    notification_sent_at: Optional[datetime]
    resolved_at: Optional[datetime]
    message: Optional[str]
    created_at: datetime
    product_name: Optional[str] = None
    product_sku: Optional[str] = None

    class Config:
        from_attributes = True


class InventoryAlertCreate(BaseModel):
    product_id: UUID
    alert_type: str = Field(..., pattern="^(low_stock|out_of_stock|critical)$")
    current_quantity: int
    threshold_quantity: int
    message: Optional[str] = None


# Search and Filter Schemas
class ProductSearchParams(BaseModel):
    q: Optional[str] = None  # Search query
    category_id: Optional[UUID] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    in_stock: Optional[bool] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    sort_by: Optional[str] = Field("created_at", pattern="^(created_at|price|name|rating|popularity)$")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)

    @validator('max_price')
    def max_price_must_be_greater_than_min(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than or equal to min_price')
        return v


# Resolve forward references after all classes are defined
ReviewResponse.model_rebuild()
