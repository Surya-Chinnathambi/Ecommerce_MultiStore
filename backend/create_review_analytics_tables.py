"""
Database migration script to create review and analytics tables
Run this script to add new tables to your database
"""
from app.core.database import engine, Base
from app.models.review_models import ProductReview, ReviewResponse, ReviewHelpful
from app.models.analytics_models import DailyAnalytics, ProductAnalytics, InventoryAlert
from app.models.models import Store, Product, Category, Order, OrderItem, SyncLog
from app.models.auth_models import User, Address
from app.models.marketing_models import (
    PromotionalBanner, FlashSale, SocialProofActivity, 
    ReferralCode, Referral, LoyaltyPoints, LoyaltyTransaction
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_all_tables():
    """Create all database tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Successfully created all tables!")
        
        # List created tables
        tables = Base.metadata.tables.keys()
        logger.info(f"Created tables: {', '.join(tables)}")
        
        # New tables
        new_tables = [
            'product_reviews',
            'review_responses',
            'review_helpful',
            'daily_analytics',
            'product_analytics',
            'inventory_alerts'
        ]
        
        logger.info("\n📊 New tables for Reviews & Analytics:")
        for table in new_tables:
            if table in tables:
                logger.info(f"  ✓ {table}")
            else:
                logger.warning(f"  ✗ {table} - NOT CREATED")
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        raise

if __name__ == "__main__":
    create_all_tables()
