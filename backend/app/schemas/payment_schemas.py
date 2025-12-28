"""
Payment Pydantic Schemas
Request/Response models for payment operations
"""
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum


# Enums
class PaymentGatewayEnum(str, Enum):
    STRIPE = "stripe"
    RAZORPAY = "razorpay"
    COD = "cod"
    MANUAL = "manual"


class PaymentStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class RefundStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


# Request Schemas
class PaymentIntentCreate(BaseModel):
    """Create a payment intent for an order"""
    order_id: UUID
    payment_gateway: PaymentGatewayEnum
    payment_method: Optional[str] = "card"  # card, upi, netbanking, wallet
    save_payment_method: Optional[bool] = False
    return_url: Optional[str] = None  # Redirect URL after payment
    meta_data: Optional[Dict[str, Any]] = {}
    
    class Config:
        schema_extra = {
            "example": {
                "order_id": "550e8400-e29b-41d4-a716-446655440000",
                "payment_gateway": "stripe",
                "payment_method": "card",
                "return_url": "https://mystore.com/order-success"
            }
        }


class PaymentConfirm(BaseModel):
    """Confirm a payment after customer completes checkout"""
    payment_id: UUID
    gateway_payment_id: str
    gateway_signature: Optional[str] = None  # For Razorpay signature verification
    
    class Config:
        schema_extra = {
            "example": {
                "payment_id": "550e8400-e29b-41d4-a716-446655440000",
                "gateway_payment_id": "pi_1234567890",
                "gateway_signature": "abc123def456"
            }
        }


class RefundCreate(BaseModel):
    """Create a refund request"""
    payment_id: UUID
    amount: Optional[float] = None  # If None, full refund
    reason: str = Field(..., min_length=10, max_length=500)
    meta_data: Optional[Dict[str, Any]] = {}
    
    @validator('amount')
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Amount must be positive')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "payment_id": "550e8400-e29b-41d4-a716-446655440000",
                "amount": 299.99,
                "reason": "Customer requested cancellation"
            }
        }


class WebhookPayload(BaseModel):
    """Webhook event payload from payment gateway"""
    gateway: PaymentGatewayEnum
    event_type: str
    event_id: str
    signature: Optional[str] = None
    payload: Dict[str, Any]


# Response Schemas
class PaymentResponse(BaseModel):
    """Payment details response"""
    id: UUID
    store_id: UUID
    order_id: UUID
    user_id: Optional[UUID]
    
    payment_gateway: PaymentGatewayEnum
    status: PaymentStatusEnum
    
    amount: float
    currency: str
    
    gateway_payment_id: Optional[str]
    gateway_order_id: Optional[str]
    
    payment_method: Optional[str]
    card_last4: Optional[str]
    card_brand: Optional[str]
    
    transaction_fee: float
    net_amount: Optional[float]
    
    customer_email: Optional[str]
    customer_phone: Optional[str]
    customer_name: Optional[str]
    
    error_message: Optional[str]
    error_code: Optional[str]
    
    metadata: Dict[str, Any]
    notes: Optional[str]
    
    initiated_at: datetime
    completed_at: Optional[datetime]
    failed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PaymentIntentResponse(BaseModel):
    """Response after creating payment intent"""
    payment_id: UUID
    client_secret: Optional[str] = None  # For Stripe
    razorpay_order_id: Optional[str] = None  # For Razorpay
    razorpay_key_id: Optional[str] = None  # Public key for Razorpay
    amount: float
    currency: str
    payment_gateway: PaymentGatewayEnum
    
    # Additional data needed by frontend
    order_number: str
    customer_name: str
    customer_email: Optional[str]
    customer_phone: str
    
    class Config:
        schema_extra = {
            "example": {
                "payment_id": "550e8400-e29b-41d4-a716-446655440000",
                "client_secret": "pi_1234567890_secret_abc123",
                "amount": 1299.99,
                "currency": "INR",
                "payment_gateway": "stripe",
                "order_number": "ORD-2025-001",
                "customer_name": "John Doe",
                "customer_email": "john@example.com",
                "customer_phone": "+919876543210"
            }
        }


class RefundResponse(BaseModel):
    """Refund details response"""
    id: UUID
    payment_id: UUID
    store_id: UUID
    order_id: UUID
    
    status: RefundStatusEnum
    amount: float
    currency: str
    reason: str
    
    gateway_refund_id: Optional[str]
    
    initiated_by: str
    approved_by: Optional[UUID]
    
    error_message: Optional[str]
    error_code: Optional[str]
    
    metadata: Dict[str, Any]
    notes: Optional[str]
    
    initiated_at: datetime
    completed_at: Optional[datetime]
    failed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PaymentSummary(BaseModel):
    """Summary of payment for order confirmation"""
    payment_id: UUID
    status: PaymentStatusEnum
    amount: float
    currency: str
    payment_gateway: PaymentGatewayEnum
    payment_method: Optional[str]
    transaction_fee: float
    completed_at: Optional[datetime]


class PaymentMethodInfo(BaseModel):
    """Available payment methods for a store"""
    gateway: PaymentGatewayEnum
    name: str
    enabled: bool
    supported_methods: List[str]  # card, upi, netbanking, wallet, cod
    min_amount: Optional[float]
    max_amount: Optional[float]
    transaction_fee_percent: Optional[float]
    
    class Config:
        schema_extra = {
            "example": {
                "gateway": "razorpay",
                "name": "Razorpay",
                "enabled": True,
                "supported_methods": ["card", "upi", "netbanking", "wallet"],
                "min_amount": 1.0,
                "max_amount": 100000.0,
                "transaction_fee_percent": 2.0
            }
        }


class PaymentStats(BaseModel):
    """Payment statistics for store dashboard"""
    total_payments: int
    total_amount: float
    successful_payments: int
    failed_payments: int
    pending_payments: int
    refunded_amount: float
    transaction_fees: float
    net_revenue: float
    
    # Breakdown by gateway
    stripe_count: int
    razorpay_count: int
    cod_count: int
    
    # Average metrics
    average_transaction_value: float
    success_rate: float  # Percentage
    
    class Config:
        schema_extra = {
            "example": {
                "total_payments": 150,
                "total_amount": 125000.50,
                "successful_payments": 142,
                "failed_payments": 5,
                "pending_payments": 3,
                "refunded_amount": 2500.00,
                "transaction_fees": 2500.01,
                "net_revenue": 120000.49,
                "stripe_count": 80,
                "razorpay_count": 60,
                "cod_count": 10,
                "average_transaction_value": 833.34,
                "success_rate": 94.67
            }
        }
