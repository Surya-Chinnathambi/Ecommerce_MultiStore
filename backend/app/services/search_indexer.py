"""
Typesense Search Indexer
Indexes product data for ultra-fast search and autocomplete.
Uses typesense-python client.
"""
from __future__ import annotations
import logging
from typing import Any, Optional, List, Dict

from app.core.config import settings

logger = logging.getLogger(__name__)

# Lazy-import typesense so the app still starts if library is missing
try:
    import typesense
    _TYPESENSE_AVAILABLE = True
except ImportError:
    typesense = None  # type: ignore
    _TYPESENSE_AVAILABLE = False
    logger.warning("typesense package not installed — search indexing disabled")


PRODUCT_SCHEMA = {
    "name": settings.TYPESENSE_COLLECTION,
    "fields": [
        {"name": "id",              "type": "string"},
        {"name": "name",            "type": "string"},
        {"name": "description",     "type": "string", "optional": True},
        {"name": "sku",             "type": "string", "optional": True},
        {"name": "store_id",        "type": "string", "facet": True},
        {"name": "category_id",     "type": "string", "facet": True, "optional": True},
        {"name": "category_name",   "type": "string", "facet": True, "optional": True},
        {"name": "selling_price",   "type": "float"},
        {"name": "mrp",             "type": "float"},
        {"name": "discount_percent","type": "int32"},
        {"name": "is_in_stock",     "type": "bool"},
        {"name": "quantity",        "type": "int32"},
        {"name": "thumbnail",       "type": "string", "optional": True, "index": False},
        {"name": "tags",            "type": "string[]", "optional": True, "facet": True},
        {"name": "rating",            "type": "float",  "optional": True},
        {"name": "review_count",      "type": "int32",  "optional": True},
        {"name": "popularity_score",  "type": "float",  "optional": True},
    ],
    "default_sorting_field": "selling_price",
    "enable_nested_fields": False,
}


def _get_client() -> Optional[Any]:
    if not _TYPESENSE_AVAILABLE:
        return None
    try:
        return typesense.Client({
            "nodes": [{"host": settings.TYPESENSE_HOST,
                       "port": str(settings.TYPESENSE_PORT),
                       "protocol": "http"}],
            "api_key": settings.TYPESENSE_API_KEY,
            "connection_timeout_seconds": 2,
        })
    except Exception as exc:
        logger.error(f"[Typesense] Failed to build client: {exc}")
        return None


def ensure_collection() -> bool:
    """Create the products collection if it doesn't exist."""
    client = _get_client()
    if not client:
        return False
    try:
        client.collections[settings.TYPESENSE_COLLECTION].retrieve()
        return True  # already exists
    except Exception:
        pass
    try:
        client.collections.create(PRODUCT_SCHEMA)
        logger.info("[Typesense] Collection created")
        return True
    except Exception as exc:
        logger.error(f"[Typesense] Failed to create collection: {exc}")
        return False


def index_product(product: Any, category_name: str = "") -> bool:
    """Upsert a single product document."""
    client = _get_client()
    if not client:
        return False
    try:
        doc = {
            "id":               str(product.id),
            "name":             product.name or "",
            "description":      product.description or "",
            "sku":              product.sku or "",
            "store_id":         str(product.store_id),
            "category_id":      str(product.category_id) if product.category_id else "",
            "category_name":    category_name,
            "selling_price":    float(product.selling_price or 0),
            "mrp":              float(product.mrp or 0),
            "discount_percent": int(product.discount_percent or 0),
            "is_in_stock":      bool(product.is_in_stock),
            "quantity":         int(product.quantity or 0),
            "thumbnail":        product.thumbnail or "",
            "tags":             product.tags if isinstance(product.tags, list) else [],
            "rating":            float(product.average_rating) if hasattr(product, "average_rating") and product.average_rating else 0.0,
            "review_count":      0,
            "popularity_score":  0.0,
        }
        client.collections[settings.TYPESENSE_COLLECTION].documents.upsert(doc)
        return True
    except Exception as exc:
        logger.error(f"[Typesense] Index product {product.id} failed: {exc}")
        return False


def remove_product(product_id: str) -> bool:
    """Remove a product document from the index."""
    client = _get_client()
    if not client:
        return False
    try:
        client.collections[settings.TYPESENSE_COLLECTION].documents[product_id].delete()
        return True
    except Exception as exc:
        logger.warning(f"[Typesense] Remove product {product_id} failed: {exc}")
        return False


def search_products(
    query: str,
    store_id: str,
    page: int = 1,
    per_page: int = 20,
    category_id: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: bool = False,
    sort_by: str = "selling_price:asc",
) -> Dict[str, Any]:
    """Full-text search with filters."""
    client = _get_client()
    if not client:
        return {"results": [], "total": 0, "page": page, "source": "fallback"}

    filter_parts = [f"store_id:={store_id}"]
    if category_id:
        filter_parts.append(f"category_id:={category_id}")
    if in_stock_only:
        filter_parts.append("is_in_stock:=true")
    if min_price is not None:
        filter_parts.append(f"selling_price:>={min_price}")
    if max_price is not None:
        filter_parts.append(f"selling_price:<={max_price}")

    search_params = {
        "q":              query or "*",
        "query_by":       "name,description,sku,category_name,tags",
        "filter_by":      " && ".join(filter_parts),
        "sort_by":        sort_by,
        "page":           page,
        "per_page":       per_page,
        "highlight_full_fields": "name",
    }

    try:
        results = client.collections[settings.TYPESENSE_COLLECTION].documents.search(search_params)
        hits = results.get("hits", [])
        return {
            "results": [
                {
                    **h["document"],
                    "_highlight": h.get("highlight", {}),
                }
                for h in hits
            ],
            "total":   results.get("found", 0),
            "page":    page,
            "source":  "typesense",
        }
    except Exception as exc:
        logger.error(f"[Typesense] Search failed: {exc}")
        return {"results": [], "total": 0, "page": page, "source": "fallback"}


def autocomplete(query: str, store_id: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Fast prefix autocomplete suggestions."""
    client = _get_client()
    if not client:
        return []
    try:
        results = client.collections[settings.TYPESENSE_COLLECTION].documents.search({
            "q":          query,
            "query_by":   "name",
            "filter_by":  f"store_id:={store_id}",
            "per_page":   limit,
            "prefix":     True,
        })
        return [
            {
                "id":        h["document"]["id"],
                "name":      h["document"]["name"],
                "price":     h["document"]["selling_price"],
                "thumbnail": h["document"].get("thumbnail"),
            }
            for h in results.get("hits", [])
        ]
    except Exception as exc:
        logger.error(f"[Typesense] Autocomplete failed: {exc}")
        return []


def bulk_index_products(products: list, category_map: dict = {}) -> int:
    """Bulk import products into Typesense. Returns count indexed."""
    client = _get_client()
    if not client:
        return 0

    docs = []
    for product in products:
        cat_name = category_map.get(str(product.category_id), "")
        docs.append({
            "id":               str(product.id),
            "name":             product.name or "",
            "description":      product.description or "",
            "sku":              product.sku or "",
            "store_id":         str(product.store_id),
            "category_id":      str(product.category_id) if product.category_id else "",
            "category_name":    cat_name,
            "selling_price":    float(product.selling_price or 0),
            "mrp":              float(product.mrp or 0),
            "discount_percent": int(product.discount_percent or 0),
            "is_in_stock":      bool(product.is_in_stock),
            "quantity":         int(product.quantity or 0),
            "thumbnail":        product.thumbnail or "",
            "tags":             product.tags if isinstance(product.tags, list) else [],
            "rating":           0.0,
            "review_count":     0,
            "popularity_score": 0.0,
        })

    try:
        resp = client.collections[settings.TYPESENSE_COLLECTION].documents.import_(
            docs, {"action": "upsert"}
        )
        success = sum(1 for r in resp if r.get("success"))
        logger.info(f"[Typesense] Bulk indexed {success}/{len(docs)} products")
        return success
    except Exception as exc:
        logger.error(f"[Typesense] Bulk index failed: {exc}")
        return 0


def update_popularity(product_id: str, score: float) -> bool:
    """
    Patch only the *popularity_score* field for a single document.
    Called by the Celery popularity-update task.
    """
    client = _get_client()
    if not client:
        return False
    try:
        client.collections[settings.TYPESENSE_COLLECTION].documents[product_id].update(
            {"popularity_score": round(score, 6)}
        )
        return True
    except Exception as exc:
        logger.debug(f"[Typesense] update_popularity {product_id} failed: {exc}")
        return False
