"""
Search API
Provides:
  GET /search/autocomplete   — fast prefix suggestions
  GET /search/               — full product search with facets
  POST /search/admin/reindex — trigger full re-index from DB
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.auth_models import User, UserRole
from app.models.models import Product, Category
from app.services import search_indexer
from app.schemas.schemas import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/autocomplete", response_model=APIResponse,
            summary="Fast autocomplete suggestions")
async def autocomplete(
    request: Request,
    q: str = "",
    limit: int = 8,
):
    store_id = request.state.store_id
    if not store_id:
        return APIResponse(success=True, data=[])
    if len(q.strip()) < 2:
        return APIResponse(success=True, data=[])

    results = search_indexer.autocomplete(q.strip(), store_id, limit=limit)
    return APIResponse(success=True, data=results)


@router.get("/", response_model=APIResponse, summary="Full product search")
async def search_products(
    request: Request,
    q: str = "",
    page: int = 1,
    per_page: int = 20,
    category_id: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: bool = False,
    sort: str = "relevance",
    db: Session = Depends(get_db),
):
    store_id = request.state.store_id
    if not store_id:
        return APIResponse(success=True, data=[], meta={"total": 0})

    sort_map = {
        "relevance":  "_text_match:desc",
        "price_asc":  "selling_price:asc",
        "price_desc": "selling_price:desc",
        "newest":     "id:desc",
        "discount":   "discount_percent:desc",
    }
    sort_by = sort_map.get(sort, "_text_match:desc")

    result = search_indexer.search_products(
        query=q.strip() or "*",
        store_id=store_id,
        page=page,
        per_page=per_page,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock,
        sort_by=sort_by,
    )

    return APIResponse(
        success=True,
        data=result["results"],
        meta={
            "total": result["total"],
            "page":  result["page"],
            "source": result["source"],
        },
    )


@router.post("/admin/reindex", response_model=APIResponse,
             summary="[Admin] Re-index all products into Typesense")
async def reindex_all(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Admin only")

    store_id = request.state.store_id

    # Ensure collection exists
    search_indexer.ensure_collection()

    # Load products + categories
    products = db.query(Product).filter(Product.store_id == store_id).all()
    categories = db.query(Category).filter(Category.store_id == store_id).all()
    category_map = {str(c.id): c.name for c in categories}

    count = search_indexer.bulk_index_products(products, category_map)

    return APIResponse(success=True, data={
        "indexed": count,
        "total_products": len(products),
        "store_id": store_id,
    })
