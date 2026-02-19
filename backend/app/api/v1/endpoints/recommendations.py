"""
Recommendations API
GET /recommendations/trending             – top sellers in the last 24 h
GET /recommendations/product/{id}         – co-purchased + similar
GET /recommendations/for-you              – personalised (auth required)
POST /recommendations/product/{id}/view   – record a product view
GET /recommendations/recently-viewed      – user/session view history
"""
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_read_db
from app.core.security import get_current_user, get_optional_user
from app.models.auth_models import User
from app.schemas.schemas import APIResponse
from app.services.recommendation_service import RecommendationService

router = APIRouter()


def _session_id(request: Request) -> Optional[str]:
    """Extract anonymous session token from cookie or header (best-effort)."""
    return (
        request.cookies.get("session_id")
        or request.headers.get("X-Session-Id")
    )


# ── Trending ──────────────────────────────────────────────────────────────────

@router.get("/trending", response_model=APIResponse, summary="Trending products (last 24 h)")
async def trending(
    request: Request,
    limit: int = Query(12, ge=1, le=40),
    window_hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_read_db),
):
    """Products ordered most frequently in the past *window_hours* hours."""
    store_id = getattr(request.state, "store_id", None)
    if not store_id:
        return APIResponse(success=True, data=[])
    svc = RecommendationService(db)
    data = await svc.get_trending(str(store_id), limit=limit, window_hours=window_hours)
    return APIResponse(success=True, data=data, meta={"count": len(data)})


# ── Product recommendations ───────────────────────────────────────────────────

@router.get(
    "/product/{product_id}",
    response_model=APIResponse,
    summary="Co-purchased + similar recommendations",
)
async def product_recommendations(
    product_id: str,
    request: Request,
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_read_db),
):
    """
    Returns two lists:
    - **co_purchased**: collaborative filtering via order co-occurrence
    - **similar**: content-based (same category, similar price)
    """
    store_id = getattr(request.state, "store_id", None)
    if not store_id:
        return APIResponse(success=True, data={"co_purchased": [], "similar": []})

    svc = RecommendationService(db)
    co_purchased, similar = await _gather(
        svc.get_co_purchased(product_id, str(store_id), limit=limit),
        svc.get_similar(product_id, str(store_id), limit=limit),
    )
    return APIResponse(
        success=True,
        data={"co_purchased": co_purchased, "similar": similar},
        meta={"product_id": product_id},
    )


# ── Record a view ─────────────────────────────────────────────────────────────

@router.post(
    "/product/{product_id}/view",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Record a product view event",
)
async def record_view(
    product_id: str,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_read_db),
):
    """Lightweight view-tracking; returns 200 immediately."""
    store_id = getattr(request.state, "store_id", None)
    if not store_id:
        return APIResponse(success=True, data={})

    svc = RecommendationService(db)
    await svc.track_view(
        product_id=product_id,
        store_id=str(store_id),
        user_id=str(current_user.id) if current_user else None,
        session_id=_session_id(request),
    )
    return APIResponse(success=True, data={"tracked": True})


# ── Recently viewed ───────────────────────────────────────────────────────────

@router.get(
    "/recently-viewed",
    response_model=APIResponse,
    summary="Products the current user/session recently viewed",
)
async def recently_viewed(
    request: Request,
    limit: int = Query(10, ge=1, le=30),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_read_db),
):
    store_id = getattr(request.state, "store_id", None)
    if not store_id:
        return APIResponse(success=True, data=[])

    svc = RecommendationService(db)
    data = await svc.get_recently_viewed(
        store_id=str(store_id),
        user_id=str(current_user.id) if current_user else None,
        session_id=_session_id(request),
        limit=limit,
    )
    return APIResponse(success=True, data=data, meta={"count": len(data)})


# ── Personalised "For You" ───────────────────────────────────────────────────

@router.get(
    "/for-you",
    response_model=APIResponse,
    summary="Personalised picks (authenticated users only)",
)
async def for_you(
    request: Request,
    limit: int = Query(12, ge=1, le=40),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_read_db),
):
    """
    Personalised recommendations based on the user's purchase history.
    Requires authentication; returns trending products as cold-start fallback.
    """
    store_id = getattr(request.state, "store_id", None)
    if not store_id:
        return APIResponse(success=True, data=[])

    svc = RecommendationService(db)
    data = await svc.get_for_you(
        store_id=str(store_id),
        user_id=str(current_user.id),
        limit=limit,
    )
    return APIResponse(success=True, data=data, meta={"count": len(data)})


# ── Internal async gather helper ─────────────────────────────────────────────

async def _gather(*coros):
    import asyncio
    return await asyncio.gather(*coros)
