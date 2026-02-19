"""
API Router - Combines all API endpoints
"""
from fastapi import APIRouter

from app.api.v1.endpoints import sync, storefront, products, orders, stores, auth, reviews, analytics, payments, notifications, billing, pos_integration, websocket, wishlist, seller, returns, coupons, search, recommendations
from app.routers import marketing, invoice_ninja
from app.services import redis_monitor, search_service, performance_metrics

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(sync.router, prefix="/sync", tags=["Sync"])
api_router.include_router(storefront.router, prefix="/storefront", tags=["Storefront"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(stores.router, prefix="/stores", tags=["Stores"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing Integration"])
api_router.include_router(pos_integration.router, tags=["POS Integration"])
api_router.include_router(marketing.router, prefix="/marketing", tags=["Marketing"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(invoice_ninja.router, prefix="/invoice-ninja", tags=["Invoice Ninja"])
api_router.include_router(websocket.router, tags=["WebSocket"])
api_router.include_router(wishlist.router, prefix="/wishlist", tags=["Wishlist"])
api_router.include_router(seller.router, prefix="/sellers", tags=["Sellers"])
api_router.include_router(returns.router, prefix="/returns", tags=["Returns"])
api_router.include_router(coupons.router, prefix="/coupons", tags=["Coupons"])
api_router.include_router(search.router, prefix="/search/typesense", tags=["Typesense Search"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])

# New monitoring and search endpoints
api_router.include_router(redis_monitor.router, prefix="/monitoring", tags=["Monitoring"])
api_router.include_router(search_service.router, prefix="/search", tags=["Search"])
api_router.include_router(performance_metrics.router, prefix="/metrics", tags=["Metrics"])

