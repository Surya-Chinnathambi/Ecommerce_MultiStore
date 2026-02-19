"""
Wishlist API Endpoints
Persistent per-user wishlist with add / remove / list / move-to-cart.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.auth_models import User
from app.models.models import Product
from app.models.marketplace_models import WishlistItem
from app.schemas.schemas import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _serialize_wishlist_item(item: WishlistItem) -> dict:
    p = item.product
    return {
        "id": str(item.id),
        "product_id": str(item.product_id),
        "added_at": item.added_at.isoformat(),
        "variant_id": str(item.variant_id) if item.variant_id else None,
        "product": {
            "id": str(p.id),
            "name": p.name,
            "slug": p.slug,
            "thumbnail": p.thumbnail,
            "images": p.images or [],
            "selling_price": p.selling_price,
            "mrp": p.mrp,
            "discount_percent": p.discount_percent,
            "is_in_stock": p.is_in_stock,
            "quantity": p.quantity,
        } if p else None,
    }


# ────────────────────────────────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────────────────────────────────

@router.get("/", response_model=APIResponse, summary="Get user's wishlist")
async def get_wishlist(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    store_id = request.state.store_id

    items = (
        db.query(WishlistItem)
        .options(joinedload(WishlistItem.product))
        .filter(
            WishlistItem.user_id == current_user.id,
            WishlistItem.store_id == store_id,
        )
        .order_by(WishlistItem.added_at.desc())
        .all()
    )

    return APIResponse(
        success=True,
        data=[_serialize_wishlist_item(i) for i in items],
        meta={"total": len(items)},
    )


@router.post("/{product_id}", response_model=APIResponse, status_code=status.HTTP_201_CREATED,
             summary="Add product to wishlist")
async def add_to_wishlist(
    product_id: UUID,
    request: Request,
    variant_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    store_id = request.state.store_id

    # Verify product belongs to this store
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.store_id == store_id,
        Product.is_active == True,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Idempotent: already wishlisted?
    existing = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id,
        WishlistItem.product_id == product_id,
    ).first()
    if existing:
        return APIResponse(success=True, data=_serialize_wishlist_item(existing),
                           meta={"already_in_wishlist": True})

    item = WishlistItem(
        user_id=current_user.id,
        product_id=product_id,
        store_id=store_id,
        variant_id=variant_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    # Eager-load product for serialisation
    item = (
        db.query(WishlistItem)
        .options(joinedload(WishlistItem.product))
        .filter(WishlistItem.id == item.id)
        .first()
    )

    logger.info(f"Wishlist add: user={current_user.id} product={product_id}")
    return APIResponse(success=True, data=_serialize_wishlist_item(item),
                       meta={"already_in_wishlist": False})


@router.delete("/{product_id}", response_model=APIResponse, summary="Remove product from wishlist")
async def remove_from_wishlist(
    product_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id,
        WishlistItem.product_id == product_id,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not in wishlist")

    db.delete(item)
    db.commit()

    logger.info(f"Wishlist remove: user={current_user.id} product={product_id}")
    return APIResponse(success=True, data={"removed": True})


@router.get("/check/{product_id}", response_model=APIResponse,
            summary="Check if a product is wishlisted")
async def check_wishlist(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exists = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id,
        WishlistItem.product_id == product_id,
    ).first() is not None

    return APIResponse(success=True, data={"is_wishlisted": exists})


@router.delete("/", response_model=APIResponse, summary="Clear entire wishlist")
async def clear_wishlist(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    store_id = request.state.store_id
    deleted = (
        db.query(WishlistItem)
        .filter(
            WishlistItem.user_id == current_user.id,
            WishlistItem.store_id == store_id,
        )
        .delete()
    )
    db.commit()
    return APIResponse(success=True, data={"deleted_count": deleted})
