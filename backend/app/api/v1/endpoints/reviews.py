"""
Review API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.models.review_models import ProductReview, ReviewResponse, ReviewHelpful
from app.models.models import Product, Order, OrderItem
from app.models.auth_models import User
from app.schemas.review_analytics_schemas import (
    ReviewCreate, ReviewUpdate, ReviewResponse as ReviewResponseSchema,
    StoreReviewResponseCreate, StoreReviewResponse,
    ReviewHelpfulCreate, ReviewStats
)
from app.api.v1.endpoints.auth import get_current_user
from app.middleware.tenant import get_current_store_id

router = APIRouter()


@router.post("/", response_model=ReviewResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db)
):
    """Create a new product review"""
    
    # Verify product exists and belongs to store
    product = db.query(Product).filter(
        Product.id == review_data.product_id,
        Product.store_id == store_id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if user already reviewed this product
    existing_review = db.query(ProductReview).filter(
        ProductReview.product_id == review_data.product_id,
        ProductReview.user_id == current_user.id
    ).first()
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this product"
        )
    
    # Check if verified purchase
    is_verified = False
    if review_data.order_id:
        order = db.query(Order).join(OrderItem).filter(
            Order.id == review_data.order_id,
            Order.user_id == current_user.id,
            OrderItem.product_id == review_data.product_id,
            Order.status.in_(["delivered", "confirmed"])
        ).first()
        is_verified = order is not None
    
    # Create review
    new_review = ProductReview(
        product_id=review_data.product_id,
        store_id=store_id,
        user_id=current_user.id,
        order_id=review_data.order_id,
        rating=review_data.rating,
        title=review_data.title,
        review_text=review_data.review_text,
        images=review_data.images,
        is_verified_purchase=is_verified,
        is_approved=True  # Auto-approve, or set to False for moderation
    )
    
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    
    # Attach user name
    response = ReviewResponseSchema.from_orm(new_review)
    response.user_name = current_user.full_name
    
    return response


@router.get("/product/{product_id}", response_model=List[ReviewResponseSchema])
async def get_product_reviews(
    product_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|rating|helpful_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    verified_only: bool = Query(False),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db)
):
    """Get all reviews for a product"""
    
    # Build query
    query = db.query(ProductReview).filter(
        ProductReview.product_id == product_id,
        ProductReview.store_id == store_id,
        ProductReview.is_approved == True
    )
    
    if verified_only:
        query = query.filter(ProductReview.is_verified_purchase == True)
    
    if min_rating:
        query = query.filter(ProductReview.rating >= min_rating)
    
    # Sorting
    sort_column = getattr(ProductReview, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Pagination
    reviews = query.offset(skip).limit(limit).all()
    
    # Attach user names
    result = []
    for review in reviews:
        review_dict = ReviewResponseSchema.from_orm(review)
        user = db.query(User).filter(User.id == review.user_id).first()
        if user:
            review_dict.user_name = user.full_name
        result.append(review_dict)
    
    return result


@router.get("/product/{product_id}/stats", response_model=ReviewStats)
async def get_product_review_stats(
    product_id: UUID,
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db)
):
    """Get review statistics for a product"""
    
    reviews = db.query(ProductReview).filter(
        ProductReview.product_id == product_id,
        ProductReview.store_id == store_id,
        ProductReview.is_approved == True
    ).all()
    
    if not reviews:
        return ReviewStats(
            total_reviews=0,
            average_rating=0.0,
            rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            verified_purchase_percentage=0.0
        )
    
    total_reviews = len(reviews)
    average_rating = sum(r.rating for r in reviews) / total_reviews
    
    # Rating distribution
    rating_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    verified_count = 0
    
    for review in reviews:
        rating_dist[review.rating] += 1
        if review.is_verified_purchase:
            verified_count += 1
    
    verified_percentage = (verified_count / total_reviews * 100) if total_reviews > 0 else 0
    
    return ReviewStats(
        total_reviews=total_reviews,
        average_rating=round(average_rating, 2),
        rating_distribution=rating_dist,
        verified_purchase_percentage=round(verified_percentage, 2)
    )


@router.put("/{review_id}", response_model=ReviewResponseSchema)
async def update_review(
    review_id: UUID,
    review_data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db)
):
    """Update user's own review"""
    
    review = db.query(ProductReview).filter(
        ProductReview.id == review_id,
        ProductReview.user_id == current_user.id,
        ProductReview.store_id == store_id
    ).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Update fields
    update_data = review_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)
    
    review.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(review)
    
    response = ReviewResponseSchema.from_orm(review)
    response.user_name = current_user.full_name
    
    return response


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: UUID,
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db)
):
    """Delete user's own review"""
    
    review = db.query(ProductReview).filter(
        ProductReview.id == review_id,
        ProductReview.user_id == current_user.id,
        ProductReview.store_id == store_id
    ).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    db.delete(review)
    db.commit()
    
    return None


@router.post("/{review_id}/helpful", status_code=status.HTTP_200_OK)
async def mark_review_helpful(
    review_id: UUID,
    helpful_data: ReviewHelpfulCreate,
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db)
):
    """Mark a review as helpful or not helpful"""
    
    review = db.query(ProductReview).filter(
        ProductReview.id == review_id,
        ProductReview.store_id == store_id
    ).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check if user already marked this review
    existing = db.query(ReviewHelpful).filter(
        ReviewHelpful.review_id == review_id,
        ReviewHelpful.user_id == current_user.id
    ).first()
    
    if existing:
        # Update existing
        old_value = existing.is_helpful
        existing.is_helpful = helpful_data.is_helpful
        
        # Update counts
        if old_value and not helpful_data.is_helpful:
            review.helpful_count = max(0, review.helpful_count - 1)
            review.not_helpful_count += 1
        elif not old_value and helpful_data.is_helpful:
            review.not_helpful_count = max(0, review.not_helpful_count - 1)
            review.helpful_count += 1
    else:
        # Create new
        new_helpful = ReviewHelpful(
            review_id=review_id,
            user_id=current_user.id,
            is_helpful=helpful_data.is_helpful
        )
        db.add(new_helpful)
        
        # Update counts
        if helpful_data.is_helpful:
            review.helpful_count += 1
        else:
            review.not_helpful_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "helpful_count": review.helpful_count,
        "not_helpful_count": review.not_helpful_count
    }


@router.post("/{review_id}/response", response_model=StoreReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review_response(
    review_id: UUID,
    response_data: StoreReviewResponseCreate,
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db)
):
    """Store owner/admin responds to a review"""
    
    # Verify user is admin
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only store admins can respond to reviews"
        )
    
    review = db.query(ProductReview).filter(
        ProductReview.id == review_id,
        ProductReview.store_id == store_id
    ).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Create response
    new_response = ReviewResponse(
        review_id=review_id,
        store_id=store_id,
        responder_name=response_data.responder_name,
        response_text=response_data.response_text
    )
    
    db.add(new_response)
    db.commit()
    db.refresh(new_response)
    
    return StoreReviewResponse.from_orm(new_response)


@router.get("/my-reviews", response_model=List[ReviewResponseSchema])
async def get_my_reviews(
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db)
):
    """Get all reviews by current user"""
    
    reviews = db.query(ProductReview).filter(
        ProductReview.user_id == current_user.id,
        ProductReview.store_id == store_id
    ).order_by(ProductReview.created_at.desc()).all()
    
    result = []
    for review in reviews:
        review_dict = ReviewResponseSchema.from_orm(review)
        review_dict.user_name = current_user.full_name
        result.append(review_dict)
    
    return result
