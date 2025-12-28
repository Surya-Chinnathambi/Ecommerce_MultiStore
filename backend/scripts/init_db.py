"""
Database initialization script
Creates initial database tables and sample data
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import engine, Base, SessionLocal
from app.models.models import Store, Category, Product, StoreTier, StoreStatus
from app.models.review_models import ProductReview, ReviewResponse, ReviewHelpful
from app.models.analytics_models import DailyAnalytics, ProductAnalytics, InventoryAlert
from datetime import datetime
from uuid import uuid4
import secrets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")


def create_sample_store():
    """Create a sample store for testing"""
    db = SessionLocal()
    
    try:
        # Check if store already exists
        existing = db.query(Store).filter(Store.slug == "demo-store").first()
        if existing:
            logger.info(f"Demo store already exists: {existing.name}")
            logger.info(f"Store ID: {existing.id}")
            logger.info(f"API Key: {existing.sync_api_key}")
            return
        
        # Generate API key
        api_key = f"sk_test_{secrets.token_urlsafe(32)}"
        
        # Create store
        store = Store(
            id=uuid4(),
            external_id="DEMO001",
            name="Demo Grocery Store",
            slug="demo-store",
            domain="demo-store.localhost",
            owner_name="Store Owner",
            owner_phone="+919876543210",
            owner_email="owner@demostore.com",
            address="123 Main Street",
            city="Mumbai",
            state="Maharashtra",
            pincode="400001",
            currency="INR",
            timezone="Asia/Kolkata",
            language="en",
            sync_tier=StoreTier.TIER3,
            sync_interval_minutes=30,
            sync_api_key=api_key,
            status=StoreStatus.ACTIVE,
            is_active=True,
            logo_url="https://via.placeholder.com/150",
            primary_color="#2563eb",
            secondary_color="#ffffff"
        )
        
        db.add(store)
        db.commit()
        db.refresh(store)
        
        logger.info("=" * 60)
        logger.info("Demo store created successfully!")
        logger.info("=" * 60)
        logger.info(f"Store Name: {store.name}")
        logger.info(f"Store ID: {store.id}")
        logger.info(f"Slug: {store.slug}")
        logger.info(f"Domain: {store.domain}")
        logger.info(f"API Key: {api_key}")
        logger.info("=" * 60)
        logger.info("\nUse this API key in the sync agent configuration!")
        logger.info("=" * 60)
        
        # Create sample categories
        categories = [
            {"name": "Groceries", "slug": "groceries"},
            {"name": "Fruits & Vegetables", "slug": "fruits-vegetables"},
            {"name": "Dairy", "slug": "dairy"},
            {"name": "Snacks", "slug": "snacks"},
            {"name": "Beverages", "slug": "beverages"},
        ]
        
        for idx, cat_data in enumerate(categories):
            category = Category(
                id=uuid4(),
                store_id=store.id,
                name=cat_data["name"],
                slug=cat_data["slug"],
                description=f"{cat_data['name']} products",
                display_order=idx,
                is_active=True
            )
            db.add(category)
        
        db.commit()
        logger.info(f"Created {len(categories)} sample categories")
        
        # Create sample products
        category = db.query(Category).filter(Category.store_id == store.id).first()
        
        products = [
            {
                "name": "Organic Milk 1L",
                "mrp": 60.0,
                "selling_price": 55.0,
                "quantity": 100,
                "sku": "MILK001"
            },
            {
                "name": "Fresh Bread",
                "mrp": 40.0,
                "selling_price": 38.0,
                "quantity": 50,
                "sku": "BREAD001"
            },
            {
                "name": "Rice 1kg",
                "mrp": 70.0,
                "selling_price": 65.0,
                "quantity": 200,
                "sku": "RICE001"
            }
        ]
        
        for prod_data in products:
            product = Product(
                id=uuid4(),
                store_id=store.id,
                external_id=prod_data["sku"],
                name=prod_data["name"],
                slug=prod_data["name"].lower().replace(" ", "-"),
                description=f"High quality {prod_data['name']}",
                mrp=prod_data["mrp"],
                selling_price=prod_data["selling_price"],
                quantity=prod_data["quantity"],
                unit="piece",
                sku=prod_data["sku"],
                category_id=category.id if category else None,
                is_active=True,
                is_in_stock=True,
                discount_percent=round(((prod_data["mrp"] - prod_data["selling_price"]) / prod_data["mrp"]) * 100, 2)
            )
            db.add(product)
        
        db.commit()
        logger.info(f"Created {len(products)} sample products")
        
    except Exception as e:
        logger.error(f"Error creating sample store: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("E-Commerce Platform - Database Initialization")
    print("=" * 60 + "\n")
    
    # Initialize database
    init_database()
    
    # Create sample store
    create_sample_store()
    
    print("\n" + "=" * 60)
    print("Initialization complete!")
    print("=" * 60 + "\n")
