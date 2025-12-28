"""
Payment Service
Handles Stripe and Razorpay payment processing
"""
import stripe
import razorpay
import hashlib
import hmac
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.models.payment_models import (
    Payment,
    Refund,
    PaymentWebhook,
    PaymentGateway,
    PaymentStatus,
    RefundStatus
)
from app.models.models import Order, OrderStatus
from app.schemas.payment_schemas import (
    PaymentIntentCreate,
    PaymentResponse,
    PaymentIntentResponse,
    RefundCreate,
    PaymentStats
)


class PaymentService:
    """Service for handling payments across multiple gateways"""
    
    def __init__(self):
        # Initialize Stripe
        if settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Initialize Razorpay
        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            self.razorpay_client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
        else:
            self.razorpay_client = None
    
    async def create_payment_intent(
        self,
        db: Session,
        store_id: UUID,
        user_id: Optional[UUID],
        payment_data: PaymentIntentCreate
    ) -> PaymentIntentResponse:
        """Create a payment intent for an order"""
        
        # Get the order
        order = db.query(Order).filter(
            Order.id == payment_data.order_id,
            Order.store_id == store_id
        ).first()
        
        if not order:
            raise ValueError("Order not found")
        
        # Check if order already has a completed payment
        existing_payment = db.query(Payment).filter(
            Payment.order_id == order.id,
            Payment.status == PaymentStatus.COMPLETED
        ).first()
        
        if existing_payment:
            raise ValueError("Order already has a completed payment")
        
        # Create payment record
        payment = Payment(
            store_id=store_id,
            order_id=order.id,
            user_id=user_id,
            payment_gateway=PaymentGateway(payment_data.payment_gateway.value),
            status=PaymentStatus.PENDING,
            amount=order.total_amount,
            currency=order.store.currency if hasattr(order.store, 'currency') else "INR",
            payment_method=payment_data.payment_method,
            customer_email=order.customer_email,
            customer_phone=order.customer_phone,
            customer_name=order.customer_name,
            meta_data=payment_data.meta_data
        )
        
        db.add(payment)
        db.flush()  # Get the payment ID
        
        response_data = {
            "payment_id": payment.id,
            "amount": payment.amount,
            "currency": payment.currency,
            "payment_gateway": payment_data.payment_gateway,
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "customer_phone": order.customer_phone
        }
        
        # Handle different payment gateways
        if payment_data.payment_gateway == PaymentGateway.STRIPE:
            # Create Stripe PaymentIntent
            try:
                intent = stripe.PaymentIntent.create(
                    amount=int(payment.amount * 100),  # Convert to cents
                    currency=payment.currency.lower(),
                    metadata={
                        "payment_id": str(payment.id),
                        "order_id": str(order.id),
                        "store_id": str(store_id)
                    },
                    description=f"Order {order.order_number}",
                    receipt_email=order.customer_email
                )
                
                payment.gateway_payment_id = intent.id
                payment.gateway_response = intent.to_dict()
                
                response_data["client_secret"] = intent.client_secret
                
            except stripe.error.StripeError as e:
                payment.status = PaymentStatus.FAILED
                payment.error_message = str(e)
                db.commit()
                raise ValueError(f"Stripe error: {str(e)}")
        
        elif payment_data.payment_gateway == PaymentGateway.RAZORPAY:
            # Create Razorpay Order
            if not self.razorpay_client:
                raise ValueError("Razorpay is not configured")
            
            try:
                razorpay_order = self.razorpay_client.order.create({
                    "amount": int(payment.amount * 100),  # Convert to paise
                    "currency": payment.currency,
                    "receipt": order.order_number,
                    "notes": {
                        "payment_id": str(payment.id),
                        "order_id": str(order.id),
                        "store_id": str(store_id)
                    }
                })
                
                payment.gateway_order_id = razorpay_order['id']
                payment.gateway_response = razorpay_order
                
                response_data["razorpay_order_id"] = razorpay_order['id']
                response_data["razorpay_key_id"] = settings.RAZORPAY_KEY_ID
                
            except razorpay.errors.BadRequestError as e:
                payment.status = PaymentStatus.FAILED
                payment.error_message = str(e)
                db.commit()
                raise ValueError(f"Razorpay error: {str(e)}")
        
        elif payment_data.payment_gateway == PaymentGateway.COD:
            # Cash on Delivery - no gateway processing needed
            payment.status = PaymentStatus.PENDING
            payment.gateway_payment_id = f"COD-{order.order_number}"
        
        db.commit()
        db.refresh(payment)
        
        return PaymentIntentResponse(**response_data)
    
    async def confirm_payment(
        self,
        db: Session,
        payment_id: UUID,
        gateway_payment_id: str,
        gateway_signature: Optional[str] = None
    ) -> PaymentResponse:
        """Confirm a payment after customer completes checkout"""
        
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if not payment:
            raise ValueError("Payment not found")
        
        if payment.status == PaymentStatus.COMPLETED:
            return PaymentResponse.from_orm(payment)
        
        # Verify payment based on gateway
        if payment.payment_gateway == PaymentGateway.STRIPE:
            try:
                intent = stripe.PaymentIntent.retrieve(gateway_payment_id)
                
                if intent.status == "succeeded":
                    payment.status = PaymentStatus.COMPLETED
                    payment.gateway_payment_id = intent.id
                    payment.completed_at = datetime.utcnow()
                    payment.gateway_response = intent.to_dict()
                    
                    # Calculate fees (Stripe typically charges 2.9% + $0.30)
                    payment.transaction_fee = (payment.amount * 0.029) + 0.30
                    payment.net_amount = payment.amount - payment.transaction_fee
                    
                    # Update order status
                    order = payment.order
                    order.payment_status = payment.status.value
                    order.order_status = OrderStatus.CONFIRMED
                    
                else:
                    payment.status = PaymentStatus.FAILED
                    payment.failed_at = datetime.utcnow()
                    payment.error_message = f"Payment status: {intent.status}"
                
            except stripe.error.StripeError as e:
                payment.status = PaymentStatus.FAILED
                payment.failed_at = datetime.utcnow()
                payment.error_message = str(e)
                raise ValueError(f"Stripe verification failed: {str(e)}")
        
        elif payment.payment_gateway == PaymentGateway.RAZORPAY:
            if not gateway_signature:
                raise ValueError("Razorpay signature is required")
            
            # Verify Razorpay signature
            try:
                params_dict = {
                    'razorpay_order_id': payment.gateway_order_id,
                    'razorpay_payment_id': gateway_payment_id,
                    'razorpay_signature': gateway_signature
                }
                
                self.razorpay_client.utility.verify_payment_signature(params_dict)
                
                # Fetch payment details
                razorpay_payment = self.razorpay_client.payment.fetch(gateway_payment_id)
                
                if razorpay_payment['status'] == 'captured' or razorpay_payment['status'] == 'authorized':
                    payment.status = PaymentStatus.COMPLETED
                    payment.gateway_payment_id = gateway_payment_id
                    payment.gateway_signature = gateway_signature
                    payment.completed_at = datetime.utcnow()
                    payment.gateway_response = razorpay_payment
                    
                    # Extract payment method details
                    if 'method' in razorpay_payment:
                        payment.payment_method = razorpay_payment['method']
                    if 'card' in razorpay_payment:
                        payment.card_last4 = razorpay_payment['card'].get('last4')
                        payment.card_brand = razorpay_payment['card'].get('network')
                    
                    # Calculate fees (Razorpay typically charges 2%)
                    payment.transaction_fee = payment.amount * 0.02
                    payment.net_amount = payment.amount - payment.transaction_fee
                    
                    # Update order status
                    order = payment.order
                    order.payment_status = payment.status.value
                    order.order_status = OrderStatus.CONFIRMED
                    
                else:
                    payment.status = PaymentStatus.FAILED
                    payment.failed_at = datetime.utcnow()
                    payment.error_message = f"Payment status: {razorpay_payment['status']}"
                
            except razorpay.errors.SignatureVerificationError:
                payment.status = PaymentStatus.FAILED
                payment.failed_at = datetime.utcnow()
                payment.error_message = "Signature verification failed"
                raise ValueError("Razorpay signature verification failed")
        
        elif payment.payment_gateway == PaymentGateway.COD:
            # COD payments are marked as pending until delivery
            payment.status = PaymentStatus.PENDING
            payment.gateway_payment_id = gateway_payment_id
            
            # Update order status
            order = payment.order
            order.payment_status = "cod"
            order.order_status = OrderStatus.CONFIRMED
        
        db.commit()
        db.refresh(payment)
        
        return PaymentResponse.from_orm(payment)
    
    async def create_refund(
        self,
        db: Session,
        store_id: UUID,
        user_id: Optional[UUID],
        refund_data: RefundCreate
    ) -> Dict[str, Any]:
        """Create a refund for a payment"""
        
        payment = db.query(Payment).filter(
            Payment.id == refund_data.payment_id,
            Payment.store_id == store_id,
            Payment.status == PaymentStatus.COMPLETED
        ).first()
        
        if not payment:
            raise ValueError("Payment not found or not eligible for refund")
        
        # Determine refund amount
        refund_amount = refund_data.amount if refund_data.amount else payment.amount
        
        if refund_amount > payment.amount:
            raise ValueError("Refund amount cannot exceed payment amount")
        
        # Check if already refunded
        total_refunded = db.query(func.sum(Refund.amount)).filter(
            Refund.payment_id == payment.id,
            Refund.status == RefundStatus.COMPLETED
        ).scalar() or 0
        
        if total_refunded + refund_amount > payment.amount:
            raise ValueError("Total refund amount would exceed payment amount")
        
        # Create refund record
        refund = Refund(
            payment_id=payment.id,
            store_id=store_id,
            order_id=payment.order_id,
            amount=refund_amount,
            currency=payment.currency,
            reason=refund_data.reason,
            status=RefundStatus.PENDING,
            initiated_by="admin" if user_id else "customer",
            approved_by=user_id,
            meta_data=refund_data.meta_data
        )
        
        db.add(refund)
        db.flush()
        
        # Process refund based on gateway
        if payment.payment_gateway == PaymentGateway.STRIPE:
            try:
                stripe_refund = stripe.Refund.create(
                    payment_intent=payment.gateway_payment_id,
                    amount=int(refund_amount * 100),  # Convert to cents
                    reason='requested_by_customer',
                    metadata={
                        "refund_id": str(refund.id),
                        "payment_id": str(payment.id)
                    }
                )
                
                refund.gateway_refund_id = stripe_refund.id
                refund.gateway_response = stripe_refund.to_dict()
                refund.status = RefundStatus.PROCESSING
                
                if stripe_refund.status == 'succeeded':
                    refund.status = RefundStatus.COMPLETED
                    refund.completed_at = datetime.utcnow()
                
            except stripe.error.StripeError as e:
                refund.status = RefundStatus.FAILED
                refund.failed_at = datetime.utcnow()
                refund.error_message = str(e)
                db.commit()
                raise ValueError(f"Stripe refund failed: {str(e)}")
        
        elif payment.payment_gateway == PaymentGateway.RAZORPAY:
            try:
                razorpay_refund = self.razorpay_client.payment.refund(
                    payment.gateway_payment_id,
                    {
                        "amount": int(refund_amount * 100),  # Convert to paise
                        "notes": {
                            "refund_id": str(refund.id),
                            "reason": refund_data.reason
                        }
                    }
                )
                
                refund.gateway_refund_id = razorpay_refund['id']
                refund.gateway_response = razorpay_refund
                refund.status = RefundStatus.PROCESSING
                
                if razorpay_refund['status'] == 'processed':
                    refund.status = RefundStatus.COMPLETED
                    refund.completed_at = datetime.utcnow()
                
            except razorpay.errors.BadRequestError as e:
                refund.status = RefundStatus.FAILED
                refund.failed_at = datetime.utcnow()
                refund.error_message = str(e)
                db.commit()
                raise ValueError(f"Razorpay refund failed: {str(e)}")
        
        elif payment.payment_gateway == PaymentGateway.COD:
            # COD refunds need manual processing
            refund.status = RefundStatus.PENDING
            refund.notes = "Manual refund required for COD payment"
        
        # Update payment status
        if refund_amount >= payment.amount:
            payment.status = PaymentStatus.REFUNDED
        else:
            payment.status = PaymentStatus.PARTIALLY_REFUNDED
        
        db.commit()
        db.refresh(refund)
        
        return {
            "refund_id": refund.id,
            "status": refund.status.value,
            "amount": refund.amount,
            "currency": refund.currency,
            "gateway_refund_id": refund.gateway_refund_id
        }
    
    async def get_payment_stats(self, db: Session, store_id: UUID) -> PaymentStats:
        """Get payment statistics for a store"""
        
        # Get all payments for the store
        payments = db.query(Payment).filter(Payment.store_id == store_id).all()
        
        total_payments = len(payments)
        total_amount = sum(p.amount for p in payments)
        successful_payments = len([p for p in payments if p.status == PaymentStatus.COMPLETED])
        failed_payments = len([p for p in payments if p.status == PaymentStatus.FAILED])
        pending_payments = len([p for p in payments if p.status == PaymentStatus.PENDING])
        
        # Get refund stats
        refunds = db.query(Refund).filter(
            Refund.store_id == store_id,
            Refund.status == RefundStatus.COMPLETED
        ).all()
        refunded_amount = sum(r.amount for r in refunds)
        
        # Calculate fees and net revenue
        transaction_fees = sum(p.transaction_fee or 0 for p in payments if p.status == PaymentStatus.COMPLETED)
        net_revenue = total_amount - refunded_amount - transaction_fees
        
        # Count by gateway
        stripe_count = len([p for p in payments if p.payment_gateway == PaymentGateway.STRIPE])
        razorpay_count = len([p for p in payments if p.payment_gateway == PaymentGateway.RAZORPAY])
        cod_count = len([p for p in payments if p.payment_gateway == PaymentGateway.COD])
        
        # Calculate averages
        average_transaction_value = total_amount / total_payments if total_payments > 0 else 0
        success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
        
        return PaymentStats(
            total_payments=total_payments,
            total_amount=total_amount,
            successful_payments=successful_payments,
            failed_payments=failed_payments,
            pending_payments=pending_payments,
            refunded_amount=refunded_amount,
            transaction_fees=transaction_fees,
            net_revenue=net_revenue,
            stripe_count=stripe_count,
            razorpay_count=razorpay_count,
            cod_count=cod_count,
            average_transaction_value=average_transaction_value,
            success_rate=success_rate
        )
    
    def verify_webhook_signature(self, gateway: str, payload: bytes, signature: str) -> bool:
        """Verify webhook signature from payment gateway"""
        
        if gateway == "stripe":
            try:
                stripe.Webhook.construct_event(
                    payload, signature, settings.STRIPE_WEBHOOK_SECRET
                )
                return True
            except stripe.error.SignatureVerificationError:
                return False
        
        elif gateway == "razorpay":
            # Razorpay webhook verification
            secret = settings.RAZORPAY_WEBHOOK_SECRET
            expected_signature = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        
        return False


# Singleton instance
payment_service = PaymentService()
