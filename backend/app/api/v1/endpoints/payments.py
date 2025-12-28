"""
Payment API Endpoints
Handles payment creation, confirmation, refunds, and webhooks
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.security import get_current_user, get_optional_user
from app.models.auth_models import User
from app.models.payment_models import Payment, Refund, PaymentWebhook
from app.schemas.payment_schemas import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentConfirm,
    PaymentResponse,
    RefundCreate,
    RefundResponse,
    PaymentStats,
    PaymentMethodInfo,
    PaymentGatewayEnum
)
from app.services.payment_service import payment_service
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/intent", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_intent(
    payment_data: PaymentIntentCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Create a payment intent for an order
    
    - **order_id**: UUID of the order to pay for
    - **payment_gateway**: stripe, razorpay, or cod
    - **payment_method**: card, upi, netbanking, wallet, etc.
    """
    try:
        # Get store_id from order
        from app.models.models import Order
        order = db.query(Order).filter(Order.id == payment_data.order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        user_id = current_user.id if current_user else None
        
        result = await payment_service.create_payment_intent(
            db=db,
            store_id=order.store_id,
            user_id=user_id,
            payment_data=payment_data
        )
        
        logger.info(f"Payment intent created: {result.payment_id} for order {payment_data.order_id}")
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment intent"
        )


@router.post("/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payment_confirm: PaymentConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirm a payment after customer completes checkout
    
    - **payment_id**: UUID of the payment to confirm
    - **gateway_payment_id**: Payment ID from Stripe/Razorpay
    - **gateway_signature**: Signature for verification (Razorpay only)
    """
    try:
        result = await payment_service.confirm_payment(
            db=db,
            payment_id=payment_confirm.payment_id,
            gateway_payment_id=payment_confirm.gateway_payment_id,
            gateway_signature=payment_confirm.gateway_signature
        )
        
        logger.info(f"Payment confirmed: {payment_confirm.payment_id}")
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error confirming payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm payment"
        )


@router.get("/methods", response_model=List[PaymentMethodInfo])
async def get_payment_methods(
    db: Session = Depends(get_db)
):
    """
    Get available payment methods
    """
    methods = []
    
    # Stripe
    if settings.STRIPE_SECRET_KEY:
        methods.append(PaymentMethodInfo(
            gateway=PaymentGatewayEnum.STRIPE,
            name="Stripe",
            enabled=True,
            supported_methods=["card"],
            min_amount=1.0,
            max_amount=100000.0,
            transaction_fee_percent=2.9
        ))
    
    # Razorpay
    if settings.RAZORPAY_KEY_ID:
        methods.append(PaymentMethodInfo(
            gateway=PaymentGatewayEnum.RAZORPAY,
            name="Razorpay",
            enabled=True,
            supported_methods=["card", "upi", "netbanking", "wallet"],
            min_amount=1.0,
            max_amount=100000.0,
            transaction_fee_percent=2.0
        ))
    
    # COD always available
    methods.append(PaymentMethodInfo(
        gateway=PaymentGatewayEnum.COD,
        name="Cash on Delivery",
        enabled=True,
        supported_methods=["cod"],
        min_amount=1.0,
        max_amount=10000.0,
        transaction_fee_percent=0.0
    ))
    
    return methods


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get payment details by ID
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check authorization - only store owner or customer can view
    if current_user:
        if current_user.store_id != payment.store_id and current_user.id != payment.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this payment"
            )
    
    return PaymentResponse.from_orm(payment)


@router.get("/order/{order_id}", response_model=List[PaymentResponse])
async def get_order_payments(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all payments for an order
    """
    from app.models.models import Order
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check authorization
    if current_user:
        if current_user.store_id != order.store_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
    
    payments = db.query(Payment).filter(Payment.order_id == order_id).all()
    return [PaymentResponse.from_orm(p) for p in payments]


@router.post("/refund", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
async def create_refund(
    refund_data: RefundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a refund for a payment (Admin only)
    
    - **payment_id**: UUID of the payment to refund
    - **amount**: Refund amount (optional, full refund if not specified)
    - **reason**: Reason for refund
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can process refunds"
        )
    
    try:
        result = await payment_service.create_refund(
            db=db,
            store_id=current_user.store_id,
            user_id=current_user.id,
            refund_data=refund_data
        )
        
        logger.info(f"Refund created: {result['refund_id']} for payment {refund_data.payment_id}")
        
        # Fetch and return the refund
        refund = db.query(Refund).filter(Refund.id == result['refund_id']).first()
        return RefundResponse.from_orm(refund)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating refund: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create refund"
        )


@router.get("/refunds/payment/{payment_id}", response_model=List[RefundResponse])
async def get_payment_refunds(
    payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all refunds for a payment
    """
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.store_id == current_user.store_id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    refunds = db.query(Refund).filter(Refund.payment_id == payment_id).all()
    return [RefundResponse.from_orm(r) for r in refunds]


@router.get("/stats", response_model=PaymentStats)
async def get_payment_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get payment statistics for the store (Admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        stats = await payment_service.get_payment_stats(
            db=db,
            store_id=current_user.store_id
        )
        return stats
        
    except Exception as e:
        logger.error(f"Error getting payment stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment stats"
        )


@router.post("/webhook/stripe", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events
    """
    payload = await request.body()
    
    # Verify signature
    if not payment_service.verify_webhook_signature("stripe", payload, stripe_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    
    import json
    event_data = json.loads(payload)
    
    # Save webhook event
    webhook = PaymentWebhook(
        gateway="stripe",
        event_type=event_data.get("type"),
        event_id=event_data.get("id"),
        payload=event_data,
        signature=stripe_signature
    )
    
    try:
        # Process the event
        event_type = event_data.get("type")
        
        if event_type == "payment_intent.succeeded":
            # Payment successful
            payment_intent = event_data["data"]["object"]
            payment_id = payment_intent["metadata"].get("payment_id")
            
            if payment_id:
                payment = db.query(Payment).filter(Payment.id == payment_id).first()
                if payment:
                    await payment_service.confirm_payment(
                        db=db,
                        payment_id=UUID(payment_id),
                        gateway_payment_id=payment_intent["id"]
                    )
        
        elif event_type == "payment_intent.payment_failed":
            # Payment failed
            payment_intent = event_data["data"]["object"]
            payment_id = payment_intent["metadata"].get("payment_id")
            
            if payment_id:
                payment = db.query(Payment).filter(Payment.id == payment_id).first()
                if payment:
                    payment.status = "failed"
                    payment.error_message = payment_intent.get("last_payment_error", {}).get("message")
                    db.commit()
        
        webhook.processed = True
        webhook.processed_at = datetime.utcnow()
        
    except Exception as e:
        webhook.processing_error = str(e)
        logger.error(f"Error processing Stripe webhook: {str(e)}")
    
    db.add(webhook)
    db.commit()
    
    return {"status": "success"}


@router.post("/webhook/razorpay", include_in_schema=False)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Handle Razorpay webhook events
    """
    payload = await request.body()
    
    # Verify signature
    if not payment_service.verify_webhook_signature("razorpay", payload, x_razorpay_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    
    import json
    event_data = json.loads(payload)
    
    # Save webhook event
    webhook = PaymentWebhook(
        gateway="razorpay",
        event_type=event_data.get("event"),
        event_id=event_data.get("event_id", str(UUID())),
        payload=event_data,
        signature=x_razorpay_signature
    )
    
    try:
        # Process the event
        event_type = event_data.get("event")
        
        if event_type == "payment.captured":
            # Payment successful
            payment_entity = event_data["payload"]["payment"]["entity"]
            notes = payment_entity.get("notes", {})
            payment_id = notes.get("payment_id")
            
            if payment_id:
                await payment_service.confirm_payment(
                    db=db,
                    payment_id=UUID(payment_id),
                    gateway_payment_id=payment_entity["id"]
                )
        
        elif event_type == "payment.failed":
            # Payment failed
            payment_entity = event_data["payload"]["payment"]["entity"]
            notes = payment_entity.get("notes", {})
            payment_id = notes.get("payment_id")
            
            if payment_id:
                payment = db.query(Payment).filter(Payment.id == payment_id).first()
                if payment:
                    payment.status = "failed"
                    payment.error_message = payment_entity.get("error_description")
                    payment.error_code = payment_entity.get("error_code")
                    db.commit()
        
        webhook.processed = True
        webhook.processed_at = datetime.utcnow()
        
    except Exception as e:
        webhook.processing_error = str(e)
        logger.error(f"Error processing Razorpay webhook: {str(e)}")
    
    db.add(webhook)
    db.commit()
    
    return {"status": "success"}
