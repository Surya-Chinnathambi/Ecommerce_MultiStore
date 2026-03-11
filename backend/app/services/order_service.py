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
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, desc

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Order, OrderItem, Product, Store, OrderStatus, PaymentStatus
from app.models.marketplace_models import Coupon, CouponUsage, CouponType
from app.models.auth_models import User
from app.services.websocket_manager import notify_new_order
from app.services.cache_service import cache_service
from app.core.redis import redis_client, CacheKeys

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

        # Consolidate duplicate lines for the same product and validate quantity.
        merged_items: Dict[str, int] = {}
        for item in items_data:
            product_id = str(item.get("product_id") or "").strip()
            quantity = int(item.get("quantity") or 0)

            if not product_id:
                raise ValueError("Each order item must include product_id")
            if quantity <= 0:
                raise ValueError("Item quantity must be greater than zero")
            if quantity > 100:
                raise ValueError("Maximum quantity per line item is 100")

            merged_items[product_id] = merged_items.get(product_id, 0) + quantity

        # Recalculate totals and check inventory
        subtotal = 0
        items_to_create = []
        products_to_update = []

        for product_id, quantity in merged_items.items():
            product = self.db.query(Product).filter(
                Product.id == product_id,
                Product.store_id == store_id
            ).with_for_update().first() # Lock the row for inventory safety

            if not product:
                raise ValueError(f"Product {product_id} not found")

            if not product.is_active:
                raise ValueError(f"Product {product.name} is inactive")

            if not product.is_in_stock:
                raise ValueError(f"Product {product.name} is out of stock")

            if product.quantity < quantity:
                raise ValueError(f"Insufficient stock for {product.name}")

            item_price = product.selling_price
            item_subtotal = item_price * quantity
            subtotal += item_subtotal

            items_to_create.append({
                'product_id': product.id,
                'product_name': product.name,
                'quantity': quantity,
                'unit_price': item_price,
                'subtotal': item_subtotal
            })
            
            # Prepare inventory update
            product.quantity -= quantity
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
                is_valid_window = (not coupon.valid_from or coupon.valid_from <= now) and \
                    (not coupon.valid_until or coupon.valid_until >= now)
                has_total_usage = coupon.max_uses_total is None or (coupon.used_count or 0) < coupon.max_uses_total
                meets_min_amount = (not coupon.min_order_amount) or subtotal >= coupon.min_order_amount

                per_user_ok = True
                if user_id and coupon.max_uses_per_user:
                    user_usage_count = self.db.query(func.count(CouponUsage.id)).filter(
                        CouponUsage.coupon_id == coupon.id,
                        CouponUsage.user_id == user_id,
                    ).scalar() or 0
                    per_user_ok = user_usage_count < coupon.max_uses_per_user

                if is_valid_window and has_total_usage and meets_min_amount and per_user_ok:
                    coupon_type = getattr(coupon, "coupon_type", getattr(coupon, "type", None))
                    discount_value = float(getattr(coupon, "discount_value", getattr(coupon, "value", 0)) or 0)

                    if coupon_type == CouponType.PERCENT:
                        discount_amount = subtotal * (discount_value / 100.0)
                        if coupon.max_discount_cap:
                            discount_amount = min(discount_amount, float(coupon.max_discount_cap))
                    elif coupon_type == CouponType.FLAT:
                        discount_amount = min(discount_value, subtotal)
                    elif coupon_type == CouponType.FREE_SHIPPING:
                        discount_amount = shipping_cost

                    discount_amount = round(discount_amount, 2)
                    applied_coupon = coupon

        total = subtotal + tax + shipping_cost - discount_amount
        total = max(total, 0)

        # Order number
        order_number = None
        for _ in range(5):
            candidate = f"ORD-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
            exists = self.db.query(Order.id).filter(Order.order_number == candidate).first()
            if not exists:
                order_number = candidate
                break
        if not order_number:
            raise ValueError("Could not generate a unique order number")

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
            discount_amount=discount_amount,
            total_amount=total,
            coupon_code=applied_coupon.code if applied_coupon else None,
            coupon_id=applied_coupon.id if applied_coupon else None,
            order_status=OrderStatus.PENDING,
            payment_status=PaymentStatus.COD if order_data.get('payment_method', 'COD').upper() == 'COD' else PaymentStatus.PENDING
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

        # Inventory changes affect storefront/product list/search cache immediately.
        await cache_service.invalidate_store_products(str(store_id))
        await redis_client.delete_pattern(f"store:{store_id}:search:*")

        inventory_keys = [
            CacheKeys.inventory(str(store_id), str(item["product_id"]))
            for item in items_to_create
        ]
        if inventory_keys:
            await redis_client.delete(*inventory_keys)

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

    @staticmethod
    def _normalize_phone(phone: Optional[str]) -> str:
        if not phone:
            return ""
        return "".join(ch for ch in phone if ch.isdigit())

    def list_customer_orders(
        self,
        *,
        store_id: UUID,
        current_user: User,
        page: int,
        per_page: int,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return paginated customer orders with robust identity matching and rich payload."""
        normalized_phone = self._normalize_phone(getattr(current_user, "phone", None))

        identity_conditions = [Order.user_id == current_user.id]
        if current_user.email:
            identity_conditions.append(func.lower(Order.customer_email) == current_user.email.lower())
        if normalized_phone:
            identity_conditions.append(
                func.regexp_replace(func.coalesce(Order.customer_phone, ""), r"\\D", "", "g") == normalized_phone
            )

        query = self.db.query(Order).options(
            joinedload(Order.items).joinedload(OrderItem.product)
        ).filter(
            and_(
                Order.store_id == store_id,
                or_(*identity_conditions),
            )
        )

        if status_filter and status_filter != "all":
            query = query.filter(Order.order_status == status_filter)

        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Order.order_number.ilike(pattern),
                    Order.customer_name.ilike(pattern),
                    Order.customer_email.ilike(pattern),
                    Order.items.any(OrderItem.product_name.ilike(pattern)),
                )
            )

        total = query.count()
        orders = query.order_by(desc(Order.created_at))\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()

        orders_data: List[Dict[str, Any]] = []
        for order in orders:
            status_value = order.order_status.value if hasattr(order.order_status, "value") else str(order.order_status)
            payment_value = order.payment_status.value if hasattr(order.payment_status, "value") else str(order.payment_status)
            orders_data.append(
                {
                    "id": str(order.id),
                    "order_number": order.order_number,
                    "order_status": status_value,
                    "payment_status": payment_value,
                    "payment_method": order.payment_method,
                    "subtotal": float(order.subtotal or 0),
                    "tax_amount": float(order.tax_amount or 0),
                    "delivery_charge": float(order.delivery_charge or 0),
                    "total_amount": float(order.total_amount or 0),
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                    "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                    "expected_delivery_date": order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
                    "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
                    "items": [
                        {
                            "id": str(item.id),
                            "product_name": item.product_name,
                            "quantity": item.quantity,
                            "unit_price": float(item.unit_price),
                            "total": float(item.total),
                            "product": {
                                "id": str(item.product.id) if item.product else None,
                                "image_url": (
                                    item.product.images[0]
                                    if item.product and getattr(item.product, "images", None)
                                    else None
                                ),
                            } if item.product else None,
                        }
                        for item in order.items
                    ],
                    "shipping_address": {
                        "address": order.delivery_address,
                        "city": order.delivery_city,
                        "state": order.delivery_state,
                        "postal_code": order.delivery_pincode,
                    },
                }
            )

        return {
            "orders": orders_data,
            "meta": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page,
            },
        }

def get_order_service(db: Session = Depends(get_db)):
    return OrderService(db)
