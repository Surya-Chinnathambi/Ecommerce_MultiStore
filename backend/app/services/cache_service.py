"""
Cache Service
=============
Centralised high-level cache operations for domain entities.

All methods are thin wrappers over redis_client that:
  - enforce consistent key naming (via CacheKeys)
  - apply platform-wide TTL defaults (from settings)
  - provide a single place to change invalidation logic

Usage::

    from app.services.cache_service import cache_service

    # Read
    data = await cache_service.get_product_list(store_id, page=1, per_page=50)

    # Write
    await cache_service.set_product_list(store_id, data, page=1, per_page=50)

    # Invalidate single product
    await cache_service.invalidate_product(store_id, product_id)

    # Invalidate everything for a store after a full sync
    await cache_service.invalidate_store_products(store_id)
"""
import asyncio
import logging
from typing import Any, Optional

from app.core.config import settings
from app.core.redis import CacheKeys, redis_client

logger = logging.getLogger(__name__)


class CacheService:
    """High-level cache operations for domain entities."""

    # ── Products ──────────────────────────────────────────────────────────────

    @staticmethod
    async def get_product_list(store_id: str, **params) -> Optional[Any]:
        """Return a cached product listing, or None on miss."""
        if not settings.CACHE_ENABLED:
            return None
        key = CacheKeys.product_list(store_id, **params)
        return await redis_client.get_json(key)

    @staticmethod
    async def set_product_list(store_id: str, data: Any, **params) -> None:
        """Cache a product listing result."""
        if not settings.CACHE_ENABLED:
            return
        key = CacheKeys.product_list(store_id, **params)
        await redis_client.set_json(key, data, ttl=settings.CACHE_TTL_PRODUCT_LIST)

    @staticmethod
    async def invalidate_product(store_id: str, product_id: str) -> None:
        """
        Remove single-product and inventory caches for one product.
        Called when a product is created, updated, or deleted.
        """
        if not settings.CACHE_ENABLED:
            return
        await redis_client.delete(
            CacheKeys.product(store_id, product_id),
            CacheKeys.inventory(store_id, product_id),
        )
        logger.debug(f"Invalidated product cache: store={store_id} product={product_id}")

    @staticmethod
    async def invalidate_store_products(store_id: str) -> int:
        """
        Remove ALL product caches (list pages + single-product + inventory)
        for a store.  Call this after a sync completes so stale data is
        never served.
        """
        if not settings.CACHE_ENABLED:
            return 0
        count = await redis_client.delete_pattern(f"store:{store_id}:product*")
        logger.info(
            "Invalidated product cache",
            extra={"store_id": store_id, "keys_deleted": count},
        )
        return count

    # ── Search ────────────────────────────────────────────────────────────────

    @staticmethod
    async def get_search_results(store_id: str, query: str, page: int = 1) -> Optional[Any]:
        if not settings.CACHE_ENABLED:
            return None
        key = CacheKeys.search_results(store_id, query, page)
        return await redis_client.get_json(key)

    @staticmethod
    async def set_search_results(store_id: str, query: str, data: Any, page: int = 1) -> None:
        if not settings.CACHE_ENABLED:
            return
        key = CacheKeys.search_results(store_id, query, page)
        await redis_client.set_json(key, data, ttl=settings.CACHE_TTL_SEARCH_RESULTS)

    # ── Store config ──────────────────────────────────────────────────────────

    @staticmethod
    async def invalidate_store_config(store_id: str) -> None:
        """
        Remove store-info and category caches.
        Call when store settings or categories are updated.
        """
        if not settings.CACHE_ENABLED:
            return
        await redis_client.delete(
            CacheKeys.store_config(store_id),
            CacheKeys.categories(store_id),
        )
        logger.debug(f"Invalidated store config cache: store={store_id}")

    # ── Convenience sync wrapper (for Celery tasks) ───────────────────────────

    @staticmethod
    def invalidate_store_products_sync(store_id: str) -> int:
        """
        Synchronous wrapper for use inside Celery tasks (which have no
        running event loop).  Creates a temporary event loop, runs the
        coroutine, and tears it down cleanly.
        """
        try:
            return asyncio.run(CacheService.invalidate_store_products(store_id))
        except RuntimeError:
            # A loop is already running (e.g. pytest-asyncio or nested call)
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    CacheService.invalidate_store_products(store_id)
                )
            finally:
                loop.close()
        except Exception as exc:
            logger.warning(f"Sync cache invalidation failed for store {store_id}: {exc}")
            return 0


# Module-level singleton — import and use directly
cache_service = CacheService()
