"""
API Router - Combines all API endpoints
"""
from fastapi import APIRouter

from app.api.v1.endpoints import sync, storefront, products, orders, stores, auth, reviews, analytics, payments, notifications, billing
from app.routers import marketing
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
api_router.include_router(marketing.router, prefix="/marketing", tags=["Marketing"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

# New monitoring and search endpoints
api_router.include_router(redis_monitor.router, prefix="/monitoring", tags=["Monitoring"])
api_router.include_router(search_service.router, prefix="/search", tags=["Search"])
api_router.include_router(performance_metrics.router, prefix="/metrics", tags=["Metrics"])

