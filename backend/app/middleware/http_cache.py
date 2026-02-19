"""
HTTP Cache Middleware
=====================
Adds ``ETag``, ``Cache-Control``, and ``Vary`` headers to cacheable GET
responses and short-circuits with **304 Not Modified** when the client
already holds a valid copy.

Only applied to:
- GET requests
- Unauthenticated requests (no ``Authorization`` header)
- A curated allow-list of public storefront paths

This gives CDNs and browsers accurate hints so they can cache responses
locally, reducing origin load for the most-read endpoints (store info,
category tree, product listings).
"""
import hashlib
import logging
from typing import Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Maps URL path *prefix* → max-age in seconds.
# Stale-while-revalidate is set to 2× max-age so the browser can serve the
# stale copy while fetching a fresh one in the background.
_CACHEABLE_PREFIXES: Dict[str, int] = {
    "/api/v1/storefront/store-info":        3600,   # 1 h
    "/api/v1/storefront/categories":        1800,   # 30 min
    "/api/v1/storefront/products":          300,    # 5 min
    "/api/v1/storefront/featured-products": 600,    # 10 min
    "/api/v1/storefront/banners":           1800,   # 30 min
}


class HTTPCacheMiddleware(BaseHTTPMiddleware):
    """
    Adds ETag and Cache-Control headers to eligible GET responses.

    Flow::

        Request (GET, no Auth, cacheable path)
            │
            ▼
        Call next handler
            │
            ▼
        Read full response body → compute MD5 ETag
            │
            ├─ If-None-Match == ETag  ──►  304 Not Modified (no body)
            │
            └─ Otherwise  ──►  200 with ETag + Cache-Control + Vary headers
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Only cache eligible requests ------------------------------------
        if request.method != "GET":
            return await call_next(request)

        # Never cache authenticated requests (personalised data may leak)
        if request.headers.get("authorization"):
            return await call_next(request)

        max_age: int | None = None
        for prefix, ttl in _CACHEABLE_PREFIXES.items():
            if request.url.path.startswith(prefix):
                max_age = ttl
                break

        if max_age is None:
            return await call_next(request)

        # Execute the actual handler --------------------------------------
        resp = await call_next(request)

        # Only attach cache headers to successful responses
        if resp.status_code != 200:
            return resp

        # Consume the async body iterator so we can hash it
        body = b"".join([chunk async for chunk in resp.body_iterator])
        etag = f'"{hashlib.md5(body).hexdigest()}"'

        # 304 short-circuit if the client already has this version --------
        if request.headers.get("if-none-match") == etag:
            logger.debug("304 Not Modified: %s", request.url.path)
            return Response(
                status_code=304,
                headers={
                    "ETag": etag,
                    "Cache-Control": (
                        f"public, max-age={max_age}, "
                        f"stale-while-revalidate={max_age * 2}"
                    ),
                },
            )

        # Attach cache-control metadata to the response -------------------
        headers = dict(resp.headers)
        headers["ETag"] = etag
        headers["Cache-Control"] = (
            f"public, max-age={max_age}, stale-while-revalidate={max_age * 2}"
        )
        # Vary on the tenant domain so CDN nodes are partitioned per store
        headers["Vary"] = "Accept-Encoding, X-Store-Domain"

        return Response(
            content=body,
            status_code=resp.status_code,
            headers=headers,
            media_type=resp.media_type,
        )
