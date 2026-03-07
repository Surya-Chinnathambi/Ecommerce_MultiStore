"""
Coupons & Promotions API
Supports: PERCENT, FLAT, FREE_SHIPPING, BUY_X_GET_Y
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin, verify_admin_store_access
from app.models.auth_models import User, UserRole
from app.models.marketplace_models import Coupon, CouponUsage, CouponType
from app.schemas.schemas import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _serialize_coupon(c: Coupon, include_usage: bool = False) -> dict:
    d = {
        "id": str(c.id),
        "code": c.code,
        "type": c.type.value if hasattr(c.type, "value") else c.type,
        "value": c.value,
        "min_order_amount": c.min_order_amount,
        "max_discount_amount": c.max_discount_amount,
        "buy_quantity": c.buy_quantity,
        "get_quantity": c.get_quantity,
        "applicable_product_ids": c.applicable_product_ids or [],
        "applicable_category_ids": c.applicable_category_ids or [],
        "usage_limit": c.usage_limit,
        "per_user_limit": c.per_user_limit,
        "used_count": c.used_count,
        "valid_from": c.valid_from.isoformat() if c.valid_from else None,
        "valid_until": c.valid_until.isoformat() if c.valid_until else None,
        "is_active": c.is_active,
        "description": c.description,
    }
    return d


def _compute_discount(coupon: Coupon, order_amount: float, item_count: int) -> dict:
    """Returns {discount: float, free_shipping: bool, message: str}"""
    discount = 0.0
    free_shipping = False

    if coupon.type == CouponType.PERCENT:
        discount = order_amount * (coupon.value / 100.0)
        if coupon.max_discount_amount:
            discount = min(discount, coupon.max_discount_amount)
    elif coupon.type == CouponType.FLAT:
        discount = min(coupon.value, order_amount)
    elif coupon.type == CouponType.FREE_SHIPPING:
        free_shipping = True
        discount = 0.0
    elif coupon.type == CouponType.BUY_X_GET_Y:
        buy_x = coupon.buy_quantity or 1
        get_y = coupon.get_quantity or 1
        eligible_sets = item_count // (buy_x + get_y) if (buy_x + get_y) else 0
        # Approximate: discount = (get_y / total_qty_in_set) * pro-rata amount
        if (buy_x + get_y) > 0 and eligible_sets > 0:
            per_item = order_amount / item_count if item_count else 0
            discount = per_item * get_y * eligible_sets

    return {"discount": round(discount, 2), "free_shipping": free_shipping}


# ─── public routes ─────────────────────────────────────────────────────────────

@router.post("/validate", response_model=APIResponse, summary="Validate coupon at checkout")
async def validate_coupon(
    request: Request,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Payload:
    {
      "code": "SAVE200",
      "order_amount": 1500.0,
      "item_count": 3,
      "product_ids": ["uuid1", ...],   optional
      "category_ids": ["uuid1", ...]   optional
    }
    """
    store_id = request.state.store_id
    code = (payload.get("code") or "").upper().strip()
    if not code:
        raise HTTPException(status_code=422, detail="Coupon code is required")

    coupon = db.query(Coupon).filter(
        and_(
            func.upper(Coupon.code) == code,
            Coupon.store_id == store_id,
            Coupon.is_active == True,
        )
    ).first()

    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found or inactive")

    now = datetime.utcnow()
    if coupon.valid_from and coupon.valid_from > now:
        raise HTTPException(status_code=400, detail="Coupon is not yet active")
    if coupon.valid_until and coupon.valid_until < now:
        raise HTTPException(status_code=400, detail="Coupon has expired")

    order_amount = float(payload.get("order_amount", 0))
    if coupon.min_order_amount and order_amount < coupon.min_order_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum order amount of ₹{coupon.min_order_amount:.0f} required"
        )

    if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
        raise HTTPException(status_code=400, detail="Coupon usage limit reached")

    # Per-user check
    if coupon.per_user_limit:
        user_usage = db.query(func.count(CouponUsage.id)).filter(
            CouponUsage.coupon_id == coupon.id,
            CouponUsage.user_id == current_user.id,
        ).scalar()
        if user_usage >= coupon.per_user_limit:
            raise HTTPException(status_code=400,
                                detail="You have already used this coupon the maximum number of times")

    item_count = int(payload.get("item_count", 1))
    result = _compute_discount(coupon, order_amount, item_count)
    final_amount = order_amount - result["discount"]

    return APIResponse(success=True, data={
        "coupon_id": str(coupon.id),
        "code": coupon.code,
        "type": coupon.type.value,
        "discount_amount": result["discount"],
        "free_shipping": result["free_shipping"],
        "final_amount": round(max(final_amount, 0), 2),
        "description": coupon.description,
    })


@router.get("/active", response_model=APIResponse, summary="List active coupons for store")
async def list_active_coupons(
    request: Request,
    db: Session = Depends(get_db),
):
    store_id = request.state.store_id
    now = datetime.utcnow()
    coupons = db.query(Coupon).filter(
        Coupon.store_id == store_id,
        Coupon.is_active == True,
    ).all()
    # Filter by validity window if set
    coupons = [c for c in coupons if
               (not c.valid_from or c.valid_from <= now) and
               (not c.valid_until or c.valid_until >= now) and
               (not c.usage_limit or c.used_count < c.usage_limit)]

    return APIResponse(success=True, data=[_serialize_coupon(c) for c in coupons])


# ─── admin routes ──────────────────────────────────────────────────────────────

@router.get("/", response_model=APIResponse, summary="[Admin] List all coupons")
async def admin_list_coupons(
    request: Request,
    active_only: bool = False,
    page: int = 1,
    per_page: int = 20,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Admin only")

    store_id = request.state.store_id
    if not verify_admin_store_access(current_user, str(store_id)):
        raise HTTPException(status_code=403, detail="Not authorized for this store")
    
    query = db.query(Coupon).filter(Coupon.store_id == store_id)
    if active_only:
        query = query.filter(Coupon.is_active == True)

    total = query.count()
    coupons = query.order_by(Coupon.created_at.desc()) \
                   .offset((page - 1) * per_page).limit(per_page).all()

    return APIResponse(success=True, data=[_serialize_coupon(c) for c in coupons],
                       meta={"total": total, "page": page})


@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED,
             summary="[Admin] Create coupon")
async def create_coupon(
    request: Request,
    payload: dict,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    store_id = request.state.store_id
    if not verify_admin_store_access(current_user, str(store_id)):
        raise HTTPException(status_code=403, detail="Not authorized for this store")
    code = (payload.get("code") or "").upper().strip()
    if not code:
        raise HTTPException(status_code=422, detail="code is required")

    existing = db.query(Coupon).filter(
        func.upper(Coupon.code) == code,
        Coupon.store_id == store_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Coupon code '{code}' already exists")

    try:
        coupon_type = CouponType(payload.get("type", "percent"))
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid coupon type")

    valid_from = None
    valid_until = None
    if payload.get("valid_from"):
        valid_from = datetime.fromisoformat(payload["valid_from"])
    if payload.get("valid_until"):
        valid_until = datetime.fromisoformat(payload["valid_until"])

    coupon = Coupon(
        id=uuid4(),
        store_id=store_id,
        code=code,
        type=coupon_type,
        value=float(payload.get("value", 0)),
        min_order_amount=payload.get("min_order_amount"),
        max_discount_amount=payload.get("max_discount_amount"),
        buy_quantity=payload.get("buy_quantity"),
        get_quantity=payload.get("get_quantity"),
        applicable_product_ids=payload.get("applicable_product_ids", []),
        applicable_category_ids=payload.get("applicable_category_ids", []),
        usage_limit=payload.get("usage_limit"),
        per_user_limit=payload.get("per_user_limit", 1),
        valid_from=valid_from,
        valid_until=valid_until,
        is_active=payload.get("is_active", True),
        description=payload.get("description"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    return APIResponse(success=True, data=_serialize_coupon(coupon))


@router.put("/{coupon_id}", response_model=APIResponse, summary="[Admin] Update coupon")
async def update_coupon(
    coupon_id: UUID,
    payload: dict,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Admin only")

    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    editable_fields = [
        "value", "min_order_amount", "max_discount_amount", "buy_quantity",
        "get_quantity", "usage_limit", "per_user_limit", "is_active", "description",
        "applicable_product_ids", "applicable_category_ids",
    ]
    for field in editable_fields:
        if field in payload:
            setattr(coupon, field, payload[field])

    if "valid_from" in payload:
        coupon.valid_from = datetime.fromisoformat(payload["valid_from"]) if payload["valid_from"] else None
    if "valid_until" in payload:
        coupon.valid_until = datetime.fromisoformat(payload["valid_until"]) if payload["valid_until"] else None

    coupon.updated_at = datetime.utcnow()
    db.commit()
    return APIResponse(success=True, data=_serialize_coupon(coupon))


@router.delete("/{coupon_id}", response_model=APIResponse, summary="[Admin] Deactivate coupon")
async def deactivate_coupon(
    coupon_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Admin only")

    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    coupon.is_active = False
    coupon.updated_at = datetime.utcnow()
    db.commit()
    return APIResponse(success=True, data={"message": f"Coupon '{coupon.code}' deactivated"})
