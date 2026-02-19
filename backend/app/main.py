"""
FastAPI Main Application
Enterprise Multi-Tenant E-Commerce Platform
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from prometheus_client import make_asgi_app as make_prometheus_asgi_app

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.middleware.tenant import TenantMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityHeadersMiddleware, InputSanitizationMiddleware, AuditLogMiddleware
from app.middleware.prometheus import PrometheusMiddleware
from app.middleware.http_cache import HTTPCacheMiddleware
from app.middleware.correlation import CorrelationIdMiddleware
from app.core.redis import redis_client

# ── Structured JSON Logging ───────────────────────────────────────────────────
# Uses python-json-logger so every log line is valid JSON — easy to ingest into
# Loki / CloudWatch / Datadog without extra parsing rules.
import sys
from pythonjsonlogger import jsonlogger

def _configure_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

    # Quieten noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

_configure_logging()
logger = logging.getLogger(__name__)

# ── Sentry Error Tracking ─────────────────────────────────────────────────────
# Initialise before the app is constructed so Sentry wraps all integrations.
# Set SENTRY_DSN in .env.development (leave empty to disable in local dev).
def _init_sentry() -> None:
    from app.core.config import settings as s
    if not s.SENTRY_DSN:
        logger.info("Sentry disabled — SENTRY_DSN not set")
        return
    sentry_sdk.init(
        dsn=s.SENTRY_DSN,
        environment=s.ENVIRONMENT,
        release=f"{s.PROJECT_NAME}@{s.VERSION}",
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            CeleryIntegration(monitor_beat_tasks=True),
            RedisIntegration(),
        ],
        # Only send 10% of transactions in production to stay in free tier;
        # set to 1.0 in staging for full visibility.
        traces_sample_rate=0.1 if s.ENVIRONMENT == "production" else 1.0,
        send_default_pii=False,
    )
    logger.info("Sentry initialised", extra={"environment": s.ENVIRONMENT})

_init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for startup and shutdown events"""
    # Startup
    logger.info("Starting application...")
    
    # Initialize database tables
    # Base.metadata.create_all(bind=engine)  # Use Alembic in production
    
    # Test Redis connection
    try:
        await redis_client.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await redis_client.close()


# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Multi-Tenant E-Commerce & Inventory Sync Platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB

# Correlation ID must be registered FIRST so every downstream middleware and
# handler can access request.state.correlation_id and the response header is set.
app.add_middleware(CorrelationIdMiddleware)

# CORS - Configure based on environment
cors_origins = settings.ALLOWED_ORIGINS
if settings.ENVIRONMENT == "development":
    cors_origins = ["*"]
elif not cors_origins or cors_origins == ["*"]:
    # Production should have explicit origins
    cors_origins = [
        "https://yourdomain.com",
        "https://admin.yourdomain.com",
        "https://api.yourdomain.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "X-Request-ID"]
)
app.add_middleware(TenantMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditLogMiddleware)
# HTTP cache headers (ETag / Cache-Control / 304) for public storefront endpoints
app.add_middleware(HTTPCacheMiddleware)
# Prometheus must be the outermost middleware so it captures total request time
app.add_middleware(
    PrometheusMiddleware,
    app_name=settings.PROJECT_NAME,
    app_version=settings.VERSION,
    environment=settings.ENVIRONMENT,
)

# Input sanitization only in production/staging
if settings.ENVIRONMENT in ["production", "staging"]:
    app.add_middleware(InputSanitizationMiddleware)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time tracking"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s")
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later."
            },
            "timestamp": time.time()
        }
    )


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Mount Prometheus metrics endpoint
# Nginx restricts /metrics to internal Docker subnets (see nginx/nginx.conf)
_prometheus_app = make_prometheus_asgi_app()
app.mount("/metrics", _prometheus_app)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers"""
    try:
        # Check database
        from app.core.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        # Check Redis
        await redis_client.ping()
        
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "documentation": "/api/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1  # Use multiple workers in production
    )
