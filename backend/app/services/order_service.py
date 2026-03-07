"""
Order Service
Handles order creation, status updates, and business logic
"""
import random
import string
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.models import Order, OrderItem, Product, Store, OrderStatus, PaymentStatus
from app.models.marketplace_models import Coupon, CouponUsage, CouponType
from app.services.websocket_manager import notify_new_order

logger = logging.getLogger(__name__)

class OrderService:
    def __init__(self, db: Session):
        self.db = db

    async def create_order(
        self,
        store_id: UUID,
        user_id: Optional[UUID],
        order_data: Dict[str, Any]
    ) -> Order:
        """
        Create a new order with atomic operations
        """
        # Validate store
        store = self.db.query(Store).filter(Store.id == store_id).first()
        if not store or not store.is_active:
            raise ValueError("Store not found or inactive")

        items_data = order_data.get('items', [])
        if not items_data:
            raise ValueError("Order must contain at least one item")

        # Recalculate totals and check inventory
        subtotal = 0
        items_to_create = []
        products_to_update = []

        for item_data in items_data:
            product = self.db.query(Product).filter(
                Product.id == item_data['product_id'],
                Product.store_id == store_id
            ).with_for_update().first() # Lock the row for inventory safety

            if not product:
                raise ValueError(f"Product {item_data['product_id']} not found")

            if product.quantity < item_data['quantity']:
                raise ValueError(f"Insufficient stock for {product.name}")

            item_price = product.selling_price
            item_subtotal = item_price * item_data['quantity']
            subtotal += item_subtotal

            items_to_create.append({
                'product_id': product.id,
                'product_name': product.name,
                'quantity': item_data['quantity'],
                'unit_price': item_price,
                'subtotal': item_subtotal
            })
            
            # Prepare inventory update
            product.quantity -= item_data['quantity']
            if product.quantity == 0:
                product.is_in_stock = False
            products_to_update.append(product)

        # Tax and shipping
        tax = subtotal * 0.18
        shipping_cost = 0.0 if subtotal > 500 else 50.0
        discount_amount = 0.0
        applied_coupon = None

        # Coupon handling
        coupon_code = (order_data.get('coupon_code') or '').upper().strip()
        if coupon_code:
            coupon = self.db.query(Coupon).filter(
                func.upper(Coupon.code) == coupon_code,
                Coupon.store_id == store_id,
                Coupon.is_active == True,
            ).first()
            
            if coupon:
                now = datetime.utcnow()
                # Simplified validation for service (can be expanded)
                if (not coupon.valid_until or coupon.valid_until >= now) and \
                   (not coupon.min_order_amount or subtotal >= coupon.min_order_amount):
                    
                    if coupon.type == CouponType.PERCENT:
                        discount_amount = subtotal * (coupon.value / 100.0)
                    elif coupon.type == CouponType.FLAT:
                        discount_amount = min(coupon.value, subtotal)
                    
                    discount_amount = round(discount_amount, 2)
                    applied_coupon = coupon

        total = subtotal + tax + shipping_cost - discount_amount
        total = max(total, 0)

        # Order number
        order_number = f"ORD-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"

        # Create Order record
        order = Order(
            store_id=store_id,
            order_number=order_number,
            user_id=user_id,
            customer_name=order_data.get('customer_name'),
            customer_email=order_data.get('customer_email') or order_data.get('email'),
            customer_phone=order_data.get('customer_phone'),
            delivery_address=order_data.get('delivery_address'),
            delivery_city=order_data.get('delivery_city'),
            delivery_state=order_data.get('delivery_state'),
            delivery_pincode=order_data.get('delivery_pincode'),
            payment_method=order_data.get('payment_method', 'COD').upper(),
            subtotal=subtotal,
            tax_amount=tax,
            delivery_charge=shipping_cost,
            total_amount=total,
            order_status=OrderStatus.PENDING,
            payment_status=PaymentStatus.COD if order_data.get('payment_method') == 'COD' else PaymentStatus.PENDING
        )

        self.db.add(order)
        self.db.flush()

        # Add items
        for item_info in items_to_create:
            order_item = OrderItem(
                order_id=order.id,
                **item_info,
                total=item_info['subtotal']
            )
            self.db.add(order_item)

        # Coupon usage record
        if applied_coupon:
            usage = CouponUsage(
                coupon_id=applied_coupon.id,
                user_id=user_id,
                order_id=order.id,
                store_id=store_id,
                discount_applied=discount_amount,
            )
            self.db.add(usage)
            applied_coupon.used_count = (applied_coupon.used_count or 0) + 1

        self.db.flush() # Ensure everything is ready but don't commit yet

        # Async notifications can be handled by the caller after commit
        return order

    def update_order_status(self, order_id: UUID, new_status: OrderStatus) -> Order:
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
        
        order.order_status = new_status
        order.updated_at = datetime.utcnow()
        self.db.flush()
        return order

def get_order_service(db: Session = Depends(get_db)):
    return OrderService(db)
