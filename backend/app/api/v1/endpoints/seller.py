"""
Seller Marketplace API
Registration, dashboard, product management, payouts.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile, File, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, desc
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.auth_models import User, UserRole
from app.models.marketplace_models import (
    Seller, SellerProduct, SellerPayout,
    SellerStatus, PayoutStatus
)
from app.models.models import Product, Order, OrderItem
from app.schemas.schemas import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── guards ────────────────────────────────────────────────────────────────

def _require_seller(current_user: User, db: Session) -> Seller:
    seller = db.query(Seller).filter(Seller.user_id == current_user.id).first()
    if not seller:
        raise HTTPException(status_code=403, detail="Seller profile not found")
    return seller


def _require_approved_seller(current_user: User, db: Session) -> Seller:
    seller = _require_seller(current_user, db)
    if seller.status != SellerStatus.APPROVED:
        raise HTTPException(status_code=403,
                            detail=f"Seller account is {seller.status}. "
                                   "Please wait for admin approval.")
    return seller


# ─── registration ───────────────────────────────────────────────────────────

@router.post("/register", response_model=APIResponse, status_code=status.HTTP_201_CREATED,
             summary="Register as a seller")
async def register_seller(
    request: Request,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Any authenticated customer can apply to be a seller.
    Account starts in PENDING status — admin must approve.
    """
    store_id = request.state.store_id

    if db.query(Seller).filter(Seller.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="You already have a seller account")

    required = ["business_name"]
    for field in required:
        if not payload.get(field):
            raise HTTPException(status_code=422, detail=f"'{field}' is required")

    seller = Seller(
        user_id=current_user.id,
        store_id=store_id,
        business_name=payload["business_name"],
        business_type=payload.get("business_type"),
        gstin=payload.get("gstin"),
        pan=payload.get("pan"),
        address_line1=payload.get("address_line1"),
        address_line2=payload.get("address_line2"),
        city=payload.get("city"),
        state=payload.get("state"),
        pincode=payload.get("pincode"),
        bank_account_number=payload.get("bank_account_number"),
        bank_ifsc=payload.get("bank_ifsc"),
        bank_account_name=payload.get("bank_account_name"),
        upi_id=payload.get("upi_id"),
        status=SellerStatus.PENDING,
        is_active=False,
    )
    db.add(seller)
    db.commit()
    db.refresh(seller)

    logger.info(f"Seller registered: {seller.id} by user {current_user.id}")
    return APIResponse(success=True, data={"seller_id": str(seller.id),
                                           "status": seller.status.value},
                       meta={"message": "Application submitted. You'll be notified after review."})


@router.get("/me", response_model=APIResponse, summary="Get my seller profile")
async def get_seller_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seller = _require_seller(current_user, db)
    return APIResponse(success=True, data=_serialize_seller(seller))


@router.put("/me", response_model=APIResponse, summary="Update seller profile")
async def update_seller_profile(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seller = _require_seller(current_user, db)

    updatable = [
        "business_name", "business_type", "gstin", "pan",
        "address_line1", "address_line2", "city", "state", "pincode",
        "bank_account_number", "bank_ifsc", "bank_account_name", "upi_id",
    ]
    for field in updatable:
        if field in payload:
            setattr(seller, field, payload[field])

    seller.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(seller)
    return APIResponse(success=True, data=_serialize_seller(seller))


# ─── seller dashboard ───────────────────────────────────────────────────────

@router.get("/me/dashboard", response_model=APIResponse, summary="Seller performance dashboard")
async def seller_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seller = _require_approved_seller(current_user, db)

    # Revenue this month
    from datetime import date
    month_start = date.today().replace(day=1)

    monthly_revenue = (
        db.query(func.sum(OrderItem.total))
        .join(Order, Order.id == OrderItem.order_id)
        .join(SellerProduct,
              and_(SellerProduct.product_id == OrderItem.product_id,
                   SellerProduct.seller_id == seller.id))
        .filter(func.date(Order.created_at) >= month_start)
        .scalar() or 0.0
    )

    monthly_orders = (
        db.query(func.count(Order.id.distinct()))
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(SellerProduct,
              and_(SellerProduct.product_id == OrderItem.product_id,
                   SellerProduct.seller_id == seller.id))
        .filter(func.date(Order.created_at) >= month_start)
        .scalar() or 0
    )

    active_listings = (
        db.query(func.count(SellerProduct.id))
        .filter(SellerProduct.seller_id == seller.id,
                SellerProduct.is_active == True)
        .scalar() or 0
    )

    pending_payout = (
        db.query(func.sum(SellerPayout.net_amount))
        .filter(SellerPayout.seller_id == seller.id,
                SellerPayout.status == PayoutStatus.PENDING)
        .scalar() or 0.0
    )

    return APIResponse(success=True, data={
        "seller_id": str(seller.id),
        "status": seller.status.value,
        "business_name": seller.business_name,
        "avg_rating": seller.avg_rating,
        "total_orders": seller.total_orders,
        "stats": {
            "monthly_revenue": round(monthly_revenue, 2),
            "monthly_orders": monthly_orders,
            "active_listings": active_listings,
            "pending_payout": round(pending_payout, 2),
        }
    })


# ─── seller products ────────────────────────────────────────────────────────

@router.get("/me/products", response_model=APIResponse, summary="My product listings")
async def list_seller_products(
    page: int = 1,
    per_page: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seller = _require_approved_seller(current_user, db)

    query = (
        db.query(SellerProduct)
        .options(joinedload(SellerProduct.product))
        .filter(SellerProduct.seller_id == seller.id)
    )
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return APIResponse(success=True, data=[_serialize_seller_product(sp) for sp in items],
                       meta={"total": total, "page": page, "per_page": per_page})


@router.post("/me/products", response_model=APIResponse,
             status_code=status.HTTP_201_CREATED, summary="List a new product")
async def add_seller_product(
    request: Request,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seller = _require_approved_seller(current_user, db)
    store_id = request.state.store_id

    product_id = payload.get("product_id")
    if not product_id:
        raise HTTPException(status_code=422, detail="product_id is required")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.store_id == store_id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in this store")

    existing = db.query(SellerProduct).filter(
        SellerProduct.seller_id == seller.id,
        SellerProduct.product_id == product_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already list this product")

    sp = SellerProduct(
        seller_id=seller.id,
        product_id=product_id,
        store_id=store_id,
        selling_price=payload.get("selling_price", product.selling_price),
        mrp=payload.get("mrp", product.mrp),
        quantity=payload.get("quantity", 0),
        dispatch_days=payload.get("dispatch_days", 2),
        return_days=payload.get("return_days", 7),
        warranty_months=payload.get("warranty_months", 0),
    )
    db.add(sp)
    db.commit()
    db.refresh(sp)
    return APIResponse(success=True, data={"seller_product_id": str(sp.id)})


@router.put("/me/products/{sp_id}", response_model=APIResponse,
            summary="Update seller product listing")
async def update_seller_product(
    sp_id: UUID,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seller = _require_approved_seller(current_user, db)

    sp = db.query(SellerProduct).filter(
        SellerProduct.id == sp_id,
        SellerProduct.seller_id == seller.id,
    ).first()
    if not sp:
        raise HTTPException(status_code=404, detail="Listing not found")

    for field in ["selling_price", "mrp", "quantity", "dispatch_days",
                  "return_days", "warranty_months", "is_active"]:
        if field in payload:
            setattr(sp, field, payload[field])

    sp.is_in_stock = (sp.quantity > 0)
    sp.updated_at = datetime.utcnow()
    db.commit()
    return APIResponse(success=True, data={"updated": True})


# ─── seller orders ──────────────────────────────────────────────────────────

@router.get("/me/orders", response_model=APIResponse, summary="Orders containing my products")
async def list_seller_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seller = _require_seller(current_user, db)

    seller_product_ids = [
        sp.product_id
        for sp in db.query(SellerProduct).filter(SellerProduct.seller_id == seller.id).all()
    ]

    if not seller_product_ids:
        return APIResponse(success=True, data=[], meta={"total": 0, "page": page, "per_page": per_page})

    query = (
        db.query(Order)
        .options(joinedload(Order.items))
        .join(OrderItem, Order.id == OrderItem.order_id)
        .filter(OrderItem.product_id.in_(seller_product_ids))
        .distinct()
    )

    if status_filter:
        query = query.filter(Order.order_status == status_filter)

    total = query.count()
    orders = query.order_by(desc(Order.created_at)).offset((page - 1) * per_page).limit(per_page).all()

    result = []
    for order in orders:
        my_items = [item for item in order.items if item.product_id in seller_product_ids]
        my_total = sum(float(item.total) for item in my_items)
        result.append({
            "id": str(order.id),
            "order_number": order.order_number,
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "payment_method": order.payment_method,
            "customer_name": order.customer_name,
            "delivery_city": order.delivery_city,
            "delivery_state": order.delivery_state,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "my_total": my_total,
            "my_items_count": len(my_items),
            "items": [
                {
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total": float(item.total),
                }
                for item in my_items
            ],
        })

    return APIResponse(success=True, data=result, meta={"total": total, "page": page, "per_page": per_page})


# ─── payouts ─────────────────────────────────────────────────────────────────

@router.get("/me/payouts", response_model=APIResponse, summary="Payout history")
async def list_payouts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seller = _require_seller(current_user, db)
    payouts = (
        db.query(SellerPayout)
        .filter(SellerPayout.seller_id == seller.id)
        .order_by(SellerPayout.created_at.desc())
        .limit(24)
        .all()
    )
    return APIResponse(success=True, data=[{
        "id": str(p.id),
        "period": f"{p.period_start.date()} – {p.period_end.date()}",
        "gross": p.gross_amount,
        "commission": p.commission,
        "net": p.net_amount,
        "status": p.status.value,
        "paid_at": p.paid_at.isoformat() if p.paid_at else None,
    } for p in payouts])


# ─── admin: approve/reject ────────────────────────────────────────────────────

@router.get("/admin/list", response_model=APIResponse, summary="[Admin] List all sellers")
async def admin_list_sellers(
    status_filter: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Admin only")

    query = db.query(Seller)
    if status_filter:
        query = query.filter(Seller.status == status_filter)

    total = query.count()
    sellers = query.offset((page - 1) * per_page).limit(per_page).all()
    return APIResponse(success=True, data=[_serialize_seller(s) for s in sellers],
                       meta={"total": total})


@router.post("/admin/{seller_id}/approve", response_model=APIResponse)
async def admin_approve_seller(
    seller_id: UUID,
    payload: dict = {},
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Admin only")

    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    action = payload.get("action", "approve")   # approve | reject | suspend
    if action == "approve":
        seller.status = SellerStatus.APPROVED
        seller.is_active = True
        seller.approved_at = datetime.utcnow()
    elif action == "reject":
        seller.status = SellerStatus.REJECTED
        seller.is_active = False
    elif action == "suspend":
        seller.status = SellerStatus.SUSPENDED
        seller.is_active = False

    db.commit()
    return APIResponse(success=True, data={"seller_id": str(seller_id), "new_status": seller.status.value})


# ─── serialisers ─────────────────────────────────────────────────────────────

def _serialize_seller(s: Seller) -> dict:
    return {
        "id": str(s.id),
        "business_name": s.business_name,
        "business_type": s.business_type,
        "gstin": s.gstin,
        "city": s.city,
        "state": s.state,
        "status": s.status.value,
        "is_active": s.is_active,
        "kyc_verified": s.kyc_verified,
        "avg_rating": s.avg_rating,
        "total_orders": s.total_orders,
        "commission_rate": s.commission_rate,
        "created_at": s.created_at.isoformat(),
    }


def _serialize_seller_product(sp: SellerProduct) -> dict:
    p = sp.product
    return {
        "id": str(sp.id),
        "selling_price": sp.selling_price,
        "mrp": sp.mrp,
        "quantity": sp.quantity,
        "is_in_stock": sp.is_in_stock,
        "is_active": sp.is_active,
        "dispatch_days": sp.dispatch_days,
        "return_days": sp.return_days,
        "product": {
            "id": str(p.id),
            "name": p.name,
            "thumbnail": p.thumbnail,
            "sku": p.sku,
        } if p else None,
    }
