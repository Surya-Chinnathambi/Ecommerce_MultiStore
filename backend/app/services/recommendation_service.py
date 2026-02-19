"""
Recommendation Service
Provides three complementary recommendation strategies:

  1. co_purchased   – collaborative: "customers also bought" via SQL order co-occurrence
  2. similar        – content-based: same-category products with comparable price
  3. recently_viewed – session/user history stored in Redis ZSETs
  4. trending       – order-velocity in last 24 h, cached in Redis
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, and_, Integer, cast
from sqlalchemy.orm import Session, joinedload

from app.core.redis import redis_client
from app.models.models import Order, OrderItem, Product
from app.models.analytics_models import UserProductView

logger = logging.getLogger(__name__)

# ── TTLs ─────────────────────────────────────────────────────────────────────
_TTL_CO_PURCHASED = 3600        # 1 h
_TTL_SIMILAR = 1800             # 30 min
_TTL_TRENDING = 900             # 15 min
_TTL_RECENTLY_VIEWED = 86400    # 24 h  (ZSET kept for 24 h)
_MAX_RECENTLY_VIEWED = 30       # items kept per user

# ── helpers ───────────────────────────────────────────────────────────────────


def _product_dict(p: Product) -> Dict[str, Any]:
    return {
        "id": str(p.id),
        "name": p.name,
        "slug": p.slug,
        "selling_price": p.selling_price,
        "mrp": p.mrp,
        "discount_percent": p.discount_percent,
        "thumbnail": p.thumbnail,
        "is_in_stock": p.is_in_stock,
        "category_id": str(p.category_id) if p.category_id else None,
    }


class RecommendationService:
    """High-level recommendations API for the storefront."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── 1. Collaborative: Co-purchased ───────────────────────────────────────

    async def get_co_purchased(
        self,
        product_id: str,
        store_id: str,
        limit: int = 8,
    ) -> List[Dict]:
        """
        "Customers who bought this also bought…"
        Finds products that appear most often in the same order as *product_id*.
        Result is cached in Redis.
        """
        cache_key = f"rec:co:{store_id}:{product_id}"
        cached = await redis_client.get_json(cache_key)
        if cached is not None:
            return cached

        since = datetime.utcnow() - timedelta(days=90)

        # Sub-query: orders that contain the target product
        orders_with_product = (
            self.db.query(OrderItem.order_id)
            .filter(OrderItem.product_id == product_id)
            .subquery()
        )

        # Co-purchased products
        rows = (
            self.db.query(
                OrderItem.product_id,
                func.count(OrderItem.id).label("freq"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .filter(
                Order.store_id == store_id,
                Order.created_at >= since,
                OrderItem.order_id.in_(orders_with_product),
                OrderItem.product_id != product_id,
            )
            .group_by(OrderItem.product_id)
            .order_by(func.count(OrderItem.id).desc())
            .limit(limit * 2)  # over-fetch to account for inactive
            .all()
        )

        product_ids = [str(r.product_id) for r in rows]
        if not product_ids:
            return []

        products = (
            self.db.query(Product)
            .options(joinedload(Product.category))
            .filter(
                Product.id.in_(product_ids),
                Product.is_active == True,
            )
            .limit(limit)
            .all()
        )

        # Preserve frequency order
        id_order = {pid: idx for idx, pid in enumerate(product_ids)}
        products.sort(key=lambda p: id_order.get(str(p.id), 999))

        result = [_product_dict(p) for p in products]
        await redis_client.set_json(cache_key, result, ttl=_TTL_CO_PURCHASED)
        return result

    # ── 2. Content-based: Similar products ───────────────────────────────────

    async def get_similar(
        self,
        product_id: str,
        store_id: str,
        limit: int = 8,
    ) -> List[Dict]:
        """
        Products in the same category within ±40 % of the source product's price.
        Falls back to same-category-only when no price match is found.
        Result is cached in Redis.
        """
        cache_key = f"rec:sim:{store_id}:{product_id}"
        cached = await redis_client.get_json(cache_key)
        if cached is not None:
            return cached

        source = (
            self.db.query(Product)
            .filter(Product.id == product_id, Product.store_id == store_id)
            .first()
        )
        if not source:
            return []

        base_price = source.selling_price or 0
        lo = base_price * 0.60
        hi = base_price * 1.40

        query = (
            self.db.query(Product)
            .options(joinedload(Product.category))
            .filter(
                Product.store_id == store_id,
                Product.is_active == True,
                Product.id != source.id,
            )
        )

        # Same category + price band
        if source.category_id:
            products = (
                query.filter(
                    Product.category_id == source.category_id,
                    Product.selling_price.between(lo, hi),
                )
                .order_by(
                    func.abs(Product.selling_price - base_price)
                )
                .limit(limit)
                .all()
            )
        else:
            products = []

        # Fallback: same category without price constraint
        if len(products) < limit and source.category_id:
            already = {str(p.id) for p in products}
            extra = (
                query.filter(
                    Product.category_id == source.category_id,
                    ~Product.id.in_(already | {product_id}),
                )
                .order_by(Product.is_featured.desc(), Product.selling_price)
                .limit(limit - len(products))
                .all()
            )
            products.extend(extra)

        result = [_product_dict(p) for p in products[:limit]]
        await redis_client.set_json(cache_key, result, ttl=_TTL_SIMILAR)
        return result

    # ── 3. Trending products ──────────────────────────────────────────────────

    async def get_trending(
        self,
        store_id: str,
        limit: int = 12,
        window_hours: int = 24,
    ) -> List[Dict]:
        """
        Products with the highest order frequency in the last *window_hours* hours.
        Cached because the query is relatively expensive.
        """
        cache_key = f"rec:trending:{store_id}:{window_hours}"
        cached = await redis_client.get_json(cache_key)
        if cached is not None:
            return cached

        since = datetime.utcnow() - timedelta(hours=window_hours)

        rows = (
            self.db.query(
                OrderItem.product_id,
                func.sum(OrderItem.quantity).label("units_sold"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .filter(
                Order.store_id == store_id,
                Order.created_at >= since,
            )
            .group_by(OrderItem.product_id)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(limit * 2)
            .all()
        )

        product_ids = [str(r.product_id) for r in rows]
        if not product_ids:
            # Fallback: featured products
            products = (
                self.db.query(Product)
                .filter(Product.store_id == store_id, Product.is_active == True, Product.is_featured == True)
                .order_by(Product.created_at.desc())
                .limit(limit)
                .all()
            )
        else:
            id_order = {pid: idx for idx, pid in enumerate(product_ids)}
            products = (
                self.db.query(Product)
                .filter(Product.id.in_(product_ids), Product.is_active == True)
                .limit(limit)
                .all()
            )
            products.sort(key=lambda p: id_order.get(str(p.id), 999))

        result = [_product_dict(p) for p in products[:limit]]
        await redis_client.set_json(cache_key, result, ttl=_TTL_TRENDING)
        return result

    # ── 4. Recently viewed ────────────────────────────────────────────────────

    async def track_view(
        self,
        product_id: str,
        store_id: str,
        user_id: Optional[str],
        session_id: Optional[str],
    ) -> None:
        """
        Record a product view in Redis ZSET (score = unix timestamp).
        Also upserts a row in user_product_views for logged-in users.
        """
        # Redis: store up to _MAX_RECENTLY_VIEWED items per viewer
        viewer_key = user_id or session_id
        if viewer_key:
            redis_key = f"rec:viewed:{store_id}:{viewer_key}"
            try:
                if redis_client.redis:
                    ts = datetime.utcnow().timestamp()
                    await redis_client.redis.zadd(redis_key, {product_id: ts})
                    # trim to keep only the most recent N items
                    await redis_client.redis.zremrangebyrank(redis_key, 0, -((_MAX_RECENTLY_VIEWED + 1)))
                    await redis_client.redis.expire(redis_key, _TTL_RECENTLY_VIEWED)
            except Exception as exc:
                logger.warning(f"[Rec] track_view Redis error: {exc}")

        # Postgres: increment view count (authenticated users only)
        if user_id:
            try:
                existing = (
                    self.db.query(UserProductView)
                    .filter(
                        UserProductView.user_id == user_id,
                        UserProductView.product_id == product_id,
                        UserProductView.store_id == store_id,
                    )
                    .first()
                )
                if existing:
                    existing.view_count += 1
                    existing.last_viewed_at = datetime.utcnow()
                else:
                    self.db.add(
                        UserProductView(
                            user_id=user_id,
                            product_id=product_id,
                            store_id=store_id,
                        )
                    )
                self.db.commit()
            except Exception as exc:
                self.db.rollback()
                logger.warning(f"[Rec] track_view DB error: {exc}")

    async def get_recently_viewed(
        self,
        store_id: str,
        user_id: Optional[str],
        session_id: Optional[str],
        limit: int = 10,
    ) -> List[Dict]:
        """Return recently-viewed products for a user/session (newest first)."""
        viewer_key = user_id or session_id
        if not viewer_key:
            return []

        redis_key = f"rec:viewed:{store_id}:{viewer_key}"
        try:
            if not redis_client.redis:
                return []
            # zrevrange returns members sorted by score desc (newest first)
            product_ids: List[str] = await redis_client.redis.zrevrange(redis_key, 0, limit - 1)
        except Exception as exc:
            logger.warning(f"[Rec] get_recently_viewed Redis error: {exc}")
            return []

        if not product_ids:
            return []

        products = (
            self.db.query(Product)
            .filter(Product.id.in_(product_ids), Product.is_active == True)
            .all()
        )
        id_order = {pid: idx for idx, pid in enumerate(product_ids)}
        products.sort(key=lambda p: id_order.get(str(p.id), 999))
        return [_product_dict(p) for p in products]

    # ── 5. "For you" – personalised for authenticated users ──────────────────

    async def get_for_you(
        self,
        store_id: str,
        user_id: str,
        limit: int = 12,
    ) -> List[Dict]:
        """
        Personalised picks: products from the user's most-purchased categories
        that they have NOT ordered before.  Cached per user for 30 minutes.
        """
        cache_key = f"rec:foryou:{store_id}:{user_id}"
        cached = await redis_client.get_json(cache_key)
        if cached is not None:
            return cached

        since = datetime.utcnow() - timedelta(days=60)

        # Categories the user buys from most
        top_categories = (
            self.db.query(
                Product.category_id,
                func.count(OrderItem.id).label("cnt"),
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(
                Order.user_id == user_id,
                Order.store_id == store_id,
                Order.created_at >= since,
                Product.category_id.isnot(None),
            )
            .group_by(Product.category_id)
            .order_by(func.count(OrderItem.id).desc())
            .limit(5)
            .all()
        )

        if not top_categories:
            # cold-start: fall back to trending
            return await self.get_trending(store_id, limit=limit)

        category_ids = [str(r.category_id) for r in top_categories]

        # Products the user has already ordered
        already_ordered = (
            self.db.query(OrderItem.product_id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.user_id == user_id, Order.store_id == store_id)
            .subquery()
        )

        products = (
            self.db.query(Product)
            .options(joinedload(Product.category))
            .filter(
                Product.store_id == store_id,
                Product.is_active == True,
                Product.is_in_stock == True,
                Product.category_id.in_(category_ids),
                ~Product.id.in_(already_ordered),
            )
            .order_by(Product.is_featured.desc(), Product.updated_at.desc())
            .limit(limit)
            .all()
        )

        result = [_product_dict(p) for p in products]
        # shorter cache for personalised results
        await redis_client.set_json(cache_key, result, ttl=1800)
        return result
