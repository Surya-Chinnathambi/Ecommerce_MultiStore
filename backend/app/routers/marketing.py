from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import random
import string

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.auth_models import User
from app.models.models import Store, Product, Order
from app.models.marketing_models import (
    PromotionalBanner, BannerType, BannerStatus,
    FlashSale, SocialProofActivity, ReferralCode, Referral, LoyaltyPoints, LoyaltyTransaction
)
from pydantic import BaseModel, Field

router = APIRouter(tags=["marketing"])


# ================= Pydantic Schemas =================

class BannerCreate(BaseModel):
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    banner_type: str = "promotional"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    display_order: int = 0


class BannerResponse(BaseModel):
    id: str
    title: str
    subtitle: Optional[str]
    description: Optional[str]
    image_url: Optional[str]
    link_url: Optional[str]
    banner_type: str
    status: str
    start_date: datetime
    end_date: Optional[datetime]
    display_order: int
    click_count: int

    class Config:
        from_attributes = True


class FlashSaleCreate(BaseModel):
    product_id: str
    name: str
    description: Optional[str] = None
    sale_price: float
    start_time: datetime
    end_time: datetime
    max_quantity: Optional[int] = None


class FlashSaleResponse(BaseModel):
    id: str
    product_id: str
    name: str
    description: Optional[str]
    original_price: float
    sale_price: float
    discount_percent: float
    start_time: datetime
    end_time: datetime
    max_quantity: Optional[int]
    sold_quantity: int
    is_active: bool
    product: dict = None

    class Config:
        from_attributes = True


class SocialProofResponse(BaseModel):
    id: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReferralCodeCreate(BaseModel):
    referrer_reward: float = 100.0
    referee_reward: float = 100.0
    max_usage: int = 100


class ReferralCodeResponse(BaseModel):
    id: str
    code: str
    referrer_reward: float
    referee_reward: float
    usage_count: int
    max_usage: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ReferralApply(BaseModel):
    referral_code: str


class LoyaltyPointsResponse(BaseModel):
    id: str
    total_points: int
    points_earned: int
    points_redeemed: int
    tier: str

    class Config:
        from_attributes = True


# ================= Helper Functions =================

def get_store_from_header(db: Session, store_id: str) -> Store:
    """Get store from store_id parameter"""
    from uuid import UUID
    try:
        store_uuid = UUID(store_id)
        store = db.query(Store).filter(Store.id == store_uuid).first()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        return store
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid store_id format")


def generate_referral_code() -> str:
    """Generate unique 8-character referral code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


# ================= Promotional Banners =================

@router.get("/banners", response_model=List[BannerResponse])
def get_active_banners(
    banner_type: Optional[str] = None,
    store_id: str = None,
    db: Session = Depends(get_db)
):
    """Get all active promotional banners"""
    if not store_id:
        return []  # Return empty list if no store_id provided
    
    store = get_store_from_header(db, store_id)
    now = datetime.utcnow()
    
    query = db.query(PromotionalBanner).filter(
        and_(
            PromotionalBanner.store_id == store.id,
            PromotionalBanner.status == BannerStatus.ACTIVE,
            PromotionalBanner.start_date <= now,
            (PromotionalBanner.end_date.is_(None)) | (PromotionalBanner.end_date >= now)
        )
    )
    
    if banner_type:
        query = query.filter(PromotionalBanner.banner_type == banner_type)
    
    banners = query.order_by(PromotionalBanner.display_order).all()
    return banners


@router.post("/banners", response_model=BannerResponse)
def create_banner(
    banner: BannerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create promotional banner (Admin only)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not current_user.store_id:
        raise HTTPException(status_code=400, detail="User not associated with a store")
    
    new_banner = PromotionalBanner(
        **banner.dict(),
        store_id=current_user.store_id,
        start_date=banner.start_date or datetime.utcnow()
    )
    
    db.add(new_banner)
    db.commit()
    db.refresh(new_banner)
    return new_banner


@router.post("/banners/{banner_id}/click")
def track_banner_click(
    banner_id: str,
    db: Session = Depends(get_db)
):
    """Track banner click"""
    banner = db.query(PromotionalBanner).filter(PromotionalBanner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    banner.click_count += 1
    db.commit()
    return {"message": "Click tracked"}


# ================= Flash Sales =================

@router.get("/flash-sales", response_model=List[FlashSaleResponse])
def get_flash_sales(
    active_only: bool = True,
    store_id: str = None,
    db: Session = Depends(get_db)
):
    """Get all flash sales"""
    if not store_id:
        return []  # Return empty list if no store_id provided
    
    store = get_store_from_header(db, store_id)
    now = datetime.utcnow()
    
    query = db.query(FlashSale).filter(
        FlashSale.store_id == store.id
    )
    
    if active_only:
        query = query.filter(
            and_(
                FlashSale.is_active == True,
                FlashSale.start_time <= now,
                FlashSale.end_time >= now
            )
        )
    
    flash_sales = query.all()
    
    # Enrich with product data
    result = []
    for sale in flash_sales:
        sale_dict = {
            "id": str(sale.id),
            "product_id": str(sale.product_id),
            "name": sale.name,
            "description": sale.description,
            "original_price": sale.original_price,
            "sale_price": sale.sale_price,
            "discount_percent": sale.discount_percent,
            "start_time": sale.start_time,
            "end_time": sale.end_time,
            "max_quantity": sale.max_quantity,
            "sold_quantity": sale.sold_quantity,
            "is_active": sale.is_active,
            "product": {
                "id": str(sale.product.id),
                "name": sale.product.name,
                "thumbnail": sale.product.thumbnail,
                "sku": sale.product.sku
            } if sale.product else None
        }
        result.append(sale_dict)
    
    return result


@router.post("/flash-sales", response_model=FlashSaleResponse)
def create_flash_sale(
    flash_sale: FlashSaleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create flash sale (Admin only)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get product to set original price
    product = db.query(Product).filter(Product.id == flash_sale.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    discount_percent = round(((product.selling_price - flash_sale.sale_price) / product.selling_price) * 100, 2)
    
    new_flash_sale = FlashSale(
        **flash_sale.dict(),
        store_id=current_user.store_id,
        original_price=product.selling_price,
        discount_percent=discount_percent
    )
    
    db.add(new_flash_sale)
    db.commit()
    db.refresh(new_flash_sale)
    return new_flash_sale


# ================= Social Proof =================

@router.get("/social-proof/recent", response_model=List[SocialProofResponse])
def get_recent_activities(
    limit: int = 10,
    store_id: str = None,
    db: Session = Depends(get_db)
):
    """Get recent social proof activities"""
    if not store_id:
        return []  # Return empty list if no store_id provided
    
    store = get_store_from_header(db, store_id)
    
    activities = db.query(SocialProofActivity).filter(
        SocialProofActivity.store_id == store.id
    ).order_by(
        SocialProofActivity.created_at.desc()
    ).limit(limit).all()
    
    return activities


@router.post("/social-proof/activity")
def create_social_activity(
    product_id: Optional[str] = None,
    activity_type: str = "viewing",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create social proof activity"""
    store = get_store_from_header(db)
    
    # Anonymize user name
    first_name = current_user.full_name.split()[0] if current_user.full_name else "Someone"
    
    messages = {
        "viewing": f"{first_name} is viewing this product",
        "purchase": f"{first_name} just purchased this!",
        "added_to_cart": f"{first_name} added this to cart"
    }
    
    activity = SocialProofActivity(
        store_id=store.id,
        product_id=product_id,
        user_name=first_name,
        activity_type=activity_type,
        message=messages.get(activity_type, f"{first_name} interacted with this product")
    )
    
    db.add(activity)
    db.commit()
    return {"message": "Activity tracked"}


# ================= Referral Program =================

@router.get("/referral/my-code", response_model=ReferralCodeResponse)
def get_my_referral_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's referral code (create if doesn't exist)"""
    store = get_store_from_header(db)
    
    # Check if user already has a code
    referral_code = db.query(ReferralCode).filter(
        and_(
            ReferralCode.user_id == current_user.id,
            ReferralCode.store_id == store.id,
            ReferralCode.is_active == True
        )
    ).first()
    
    # Create new code if doesn't exist
    if not referral_code:
        code = generate_referral_code()
        # Ensure uniqueness
        while db.query(ReferralCode).filter(ReferralCode.code == code).first():
            code = generate_referral_code()
        
        referral_code = ReferralCode(
            code=code,
            user_id=current_user.id,
            store_id=store.id
        )
        db.add(referral_code)
        db.commit()
        db.refresh(referral_code)
    
    return referral_code


@router.post("/referral/apply")
def apply_referral_code(
    referral_data: ReferralApply,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply referral code for new user"""
    store = get_store_from_header(db)
    
    # Check if user already used a referral
    existing_referral = db.query(Referral).filter(
        and_(
            Referral.referee_id == current_user.id,
            Referral.store_id == store.id
        )
    ).first()
    
    if existing_referral:
        raise HTTPException(status_code=400, detail="You have already used a referral code")
    
    # Find referral code
    referral_code = db.query(ReferralCode).filter(
        and_(
            ReferralCode.code == referral_data.referral_code,
            ReferralCode.store_id == store.id,
            ReferralCode.is_active == True
        )
    ).first()
    
    if not referral_code:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    
    if referral_code.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot use your own referral code")
    
    if referral_code.usage_count >= referral_code.max_usage:
        raise HTTPException(status_code=400, detail="Referral code usage limit reached")
    
    # Create referral record
    referral = Referral(
        referral_code_id=referral_code.id,
        referrer_id=referral_code.user_id,
        referee_id=current_user.id,
        store_id=store.id,
        referrer_reward_amount=referral_code.referrer_reward,
        referee_reward_amount=referral_code.referee_reward
    )
    
    db.add(referral)
    referral_code.usage_count += 1
    db.commit()
    
    return {
        "message": "Referral code applied successfully",
        "reward": referral_code.referee_reward
    }


@router.get("/referral/stats")
def get_referral_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's referral statistics"""
    store = get_store_from_header(db)
    
    referral_code = db.query(ReferralCode).filter(
        and_(
            ReferralCode.user_id == current_user.id,
            ReferralCode.store_id == store.id
        )
    ).first()
    
    if not referral_code:
        return {
            "code": None,
            "total_referrals": 0,
            "total_rewards": 0,
            "pending_referrals": 0
        }
    
    total_referrals = db.query(func.count(Referral.id)).filter(
        Referral.referral_code_id == referral_code.id
    ).scalar()
    
    total_rewards = db.query(func.sum(Referral.referrer_reward_amount)).filter(
        and_(
            Referral.referral_code_id == referral_code.id,
            Referral.referrer_reward_given == True
        )
    ).scalar() or 0
    
    pending_referrals = db.query(func.count(Referral.id)).filter(
        and_(
            Referral.referral_code_id == referral_code.id,
            Referral.status == "pending"
        )
    ).scalar()
    
    return {
        "code": referral_code.code,
        "total_referrals": total_referrals,
        "total_rewards": float(total_rewards),
        "pending_referrals": pending_referrals
    }


# ================= Loyalty Points =================

@router.get("/loyalty/points", response_model=LoyaltyPointsResponse)
def get_loyalty_points(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's loyalty points"""
    store = get_store_from_header(db)
    
    loyalty = db.query(LoyaltyPoints).filter(
        and_(
            LoyaltyPoints.user_id == current_user.id,
            LoyaltyPoints.store_id == store.id
        )
    ).first()
    
    if not loyalty:
        # Create loyalty account
        loyalty = LoyaltyPoints(
            user_id=current_user.id,
            store_id=store.id
        )
        db.add(loyalty)
        db.commit()
        db.refresh(loyalty)
    
    return loyalty


@router.post("/loyalty/earn")
def earn_loyalty_points(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Earn loyalty points from order (auto-called after order completion)"""
    store = get_store_from_header(db)
    
    # Get loyalty account
    loyalty = db.query(LoyaltyPoints).filter(
        and_(
            LoyaltyPoints.user_id == current_user.id,
            LoyaltyPoints.store_id == store.id
        )
    ).first()
    
    if not loyalty:
        loyalty = LoyaltyPoints(
            user_id=current_user.id,
            store_id=store.id
        )
        db.add(loyalty)
    
    # Get order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Calculate points (1 point per ₹10 spent)
    points = int(order.total_amount / 10)
    
    loyalty.total_points += points
    loyalty.points_earned += points
    
    # Update tier based on total points
    if loyalty.total_points >= 10000:
        loyalty.tier = "platinum"
    elif loyalty.total_points >= 5000:
        loyalty.tier = "gold"
    elif loyalty.total_points >= 1000:
        loyalty.tier = "silver"
    
    # Create transaction
    transaction = LoyaltyTransaction(
        loyalty_account_id=loyalty.id,
        order_id=order_id,
        points=points,
        transaction_type="earned",
        description=f"Earned from order {order.order_number}"
    )
    
    db.add(transaction)
    db.commit()
    
    return {
        "message": "Points earned successfully",
        "points_earned": points,
        "total_points": loyalty.total_points,
        "tier": loyalty.tier
    }
