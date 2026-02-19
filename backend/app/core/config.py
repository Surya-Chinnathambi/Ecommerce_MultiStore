"""
Application Configuration
Manages environment variables and settings
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from typing import List, Optional
from functools import lru_cache
import warnings


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Project Info
    PROJECT_NAME: str = "Multi-Tenant E-Commerce Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS - Allow all origins in development
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ecommerce_platform"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Read Replicas (for scaling)
    DATABASE_READ_REPLICAS: List[str] = []
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    
    # Cache TTL (seconds)
    CACHE_TTL_PRODUCTS: int = 900          # 15 minutes — single product
    CACHE_TTL_PRODUCT_LIST: int = 300      # 5 minutes  — filtered product listings
    CACHE_TTL_INVENTORY: int = 60          # 1 minute   — inventory is time-sensitive
    CACHE_TTL_STORE_CONFIG: int = 3600     # 1 hour     — store config rarely changes
    CACHE_TTL_CATEGORIES: int = 1800       # 30 minutes — category structure
    CACHE_TTL_ORDERS: int = 30             # 30 seconds — order status changes fast
    CACHE_TTL_SEARCH_RESULTS: int = 300    # 5 minutes  — search result pages
    CACHE_ENABLED: bool = True             # Master switch — set False to bypass all caching

    # Database Connection Pool Tuning
    DB_POOL_RECYCLE: int = 1800            # Recycle stale connections every 30 min
    DB_POOL_TIMEOUT: int = 30             # Max seconds to wait for a pool connection
    DB_STATEMENT_TIMEOUT_MS: int = 30000  # Hard per-query timeout — prevents runaway queries

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_TIER1_SYNC: int = 1000  # requests per minute
    RATE_LIMIT_TIER2_SYNC: int = 500
    RATE_LIMIT_TIER3_SYNC: int = 200
    RATE_LIMIT_STOREFRONT: int = 100  # per IP
    RATE_LIMIT_DASHBOARD: int = 200
    
    # Sync Engine
    SYNC_BATCH_SIZE_TIER1: int = 200
    SYNC_BATCH_SIZE_TIER2: int = 500
    SYNC_BATCH_SIZE_TIER3: int = 1000
    SYNC_MAX_PARALLEL_BATCHES: int = 5
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Object Storage (S3-compatible)
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "ecommerce-assets"
    S3_REGION: str = "us-east-1"
    
    # Email/SMS
    # Email Settings
    EMAIL_PROVIDER: str = "smtp"  # 'sendgrid' or 'smtp'
    EMAIL_FROM: str = "noreply@example.com"
    EMAIL_FROM_NAME: str = "E-Commerce Platform"
    
    # SendGrid
    SENDGRID_API_KEY: Optional[str] = None
    
    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    # SMS Settings
    SMS_PROVIDER: str = "twilio"  # 'twilio' or 'msg91'
    SMS_FROM_NUMBER: Optional[str] = None
    
    # Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    
    # MSG91 (India)
    MSG91_AUTH_KEY: Optional[str] = None
    MSG91_SENDER_ID: Optional[str] = None
    SMS_API_KEY: Optional[str] = None
    
    # Payment Gateways
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # Razorpay
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 500
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_FORMATS: List[str] = ["jpg", "jpeg", "png", "webp"]
    
    # Business Rules
    CART_EXPIRY_HOURS: int = 24
    ORDER_CANCELLATION_WINDOW_HOURS: int = 1
    LOW_STOCK_THRESHOLD: int = 10

    # Typesense
    TYPESENSE_HOST: str = "localhost"
    TYPESENSE_PORT: int = 8108
    TYPESENSE_API_KEY: str = "typesense-dev-key"
    TYPESENSE_COLLECTION: str = "products"

    # ── Validators ──────────────────────────────────────────────────────
    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        insecure_default = "your-secret-key-change-in-production"
        if v == insecure_default:
            warnings.warn(
                "SECRET_KEY is set to the insecure default value! "
                "Set a cryptographically random SECRET_KEY before going to production.",
                stacklevel=2,
            )
        elif len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @model_validator(mode="after")
    def enforce_production_settings(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            insecure_key = "your-secret-key-change-in-production"
            if self.SECRET_KEY == insecure_key:
                raise ValueError(
                    "[production] SECRET_KEY must not be the default insecure value."
                )
            if self.ALLOWED_ORIGINS == ["*"]:
                raise ValueError(
                    "[production] ALLOWED_ORIGINS must not be '*' — "
                    "set explicit origin domains."
                )
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "[production] SECRET_KEY must be at least 32 characters."
                )
        return self
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
