import sys
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Store, Product, Category, StoreStatus, StoreTier
from app.models.auth_models import User, UserRole, Address
from app.core.security import get_password_hash
import uuid
import secrets

SAMPLE_PRODUCTS = [
    {"name": "Samsung Galaxy S24 Ultra", "category": "Electronics", "mrp": 89999, "selling_price": 89999, "description": "Latest flagship smartphone", "sku": "ELEC-001"},
    {"name": "iPhone 15 Pro Max", "category": "Electronics", "mrp": 159900, "selling_price": 159900, "description": "Apple premium smartphone", "sku": "ELEC-002"},
    {"name": "OnePlus 12", "category": "Electronics", "mrp": 64999, "selling_price": 64999, "description": "High-performance Android phone", "sku": "ELEC-003"},
    {"name": "Sony WH-1000XM5", "category": "Electronics", "mrp": 29990, "selling_price": 29990, "description": "Noise cancellation headphones", "sku": "ELEC-004"},
    {"name": "Apple AirPods Pro 2", "category": "Electronics", "mrp": 24900, "selling_price": 24900, "description": "Premium wireless earbuds", "sku": "ELEC-005"},
    {"name": "Dell XPS 15 Laptop", "category": "Electronics", "mrp": 145000, "selling_price": 145000, "description": "Premium laptop", "sku": "ELEC-006"},
    {"name": "MacBook Air M3", "category": "Electronics", "mrp": 114900, "selling_price": 114900, "description": "Apple Silicon laptop", "sku": "ELEC-007"},
    {"name": "iPad Pro 12.9", "category": "Electronics", "mrp": 112900, "selling_price": 112900, "description": "Professional tablet", "sku": "ELEC-008"},
    {"name": "Samsung Galaxy Tab S9", "category": "Electronics", "mrp": 76999, "selling_price": 76999, "description": "Android tablet", "sku": "ELEC-009"},
    {"name": "Apple Watch Series 9", "category": "Electronics", "mrp": 41900, "selling_price": 41900, "description": "Fitness smartwatch", "sku": "ELEC-010"},
    {"name": "Levi's 501 Jeans", "category": "Fashion", "mrp": 3999, "selling_price": 3999, "description": "Classic denim jeans", "sku": "FASH-011"},
    {"name": "Nike Air Max 270", "category": "Fashion", "mrp": 12795, "selling_price": 12795, "description": "Running shoes", "sku": "FASH-012"},
    {"name": "Adidas Ultraboost 23", "category": "Fashion", "mrp": 16999, "selling_price": 16999, "description": "Premium running shoes", "sku": "FASH-013"},
    {"name": "Van Heusen Shirt", "category": "Fashion", "mrp": 1499, "selling_price": 1499, "description": "Formal shirt", "sku": "FASH-014"},
    {"name": "Peter England Blazer", "category": "Fashion", "mrp": 4999, "selling_price": 4999, "description": "Formal blazer", "sku": "FASH-015"},
    {"name": "Allen Solly Chinos", "category": "Fashion", "mrp": 2499, "selling_price": 2499, "description": "Casual pants", "sku": "FASH-016"},
    {"name": "Puma T-Shirt Pack", "category": "Fashion", "mrp": 1299, "selling_price": 1299, "description": "3 casual t-shirts", "sku": "FASH-017"},
    {"name": "Woodland Leather Shoes", "category": "Fashion", "mrp": 3495, "selling_price": 3495, "description": "Leather formal shoes", "sku": "FASH-018"},
    {"name": "Fossil Analog Watch", "category": "Fashion", "mrp": 8995, "selling_price": 8995, "description": "Men's wristwatch", "sku": "FASH-019"},
    {"name": "Ray-Ban Aviator", "category": "Fashion", "mrp": 6990, "selling_price": 6990, "description": "Aviator sunglasses", "sku": "FASH-020"},
]

# Add 80 more products with similar structure
for i in range(21, 101):
    cat = ["Fashion", "Home & Kitchen", "Groceries", "Books", "Sports", "Beauty", "Toys", "Automotive"][i % 8]
    SAMPLE_PRODUCTS.append({
        "name": f"Product {i}",
        "category": cat,
        "mrp": 500 + (i * 100),
        "selling_price": 500 + (i * 100),
        "description": f"Sample product {i}",
        "sku": f"PROD-{i:03d}"
    })

SAMPLE_USERS = [
    {"email": "priya.sharma@example.com", "full_name": "Priya Sharma", "phone": "9876543211", "password": "Customer@123",
     "address": {"full_name": "Priya Sharma", "phone": "9876543211", "address_line1": "123 MG Road", "address_line2": "Near City Mall", "city": "Mumbai", "state": "Maharashtra", "pincode": "400001", "address_type": "home", "is_default": True}},
    {"email": "rajesh.kumar@example.com", "full_name": "Rajesh Kumar", "phone": "9123456780", "password": "Customer@123",
     "address": {"full_name": "Rajesh Kumar", "phone": "9123456780", "address_line1": "456 Park Street", "address_line2": "Metro Station", "city": "Bangalore", "state": "Karnataka", "pincode": "560001", "address_type": "home", "is_default": True}},
    {"email": "anita.verma@example.com", "full_name": "Anita Verma", "phone": "9988776656", "password": "Customer@123",
     "address": {"full_name": "Anita Verma", "phone": "9988776656", "address_line1": "789 Anna Salai", "address_line2": "T Nagar", "city": "Chennai", "state": "Tamil Nadu", "pincode": "600017", "address_type": "home", "is_default": True}},
    {"email": "amit.patel@example.com", "full_name": "Amit Patel", "phone": "9845123679", "password": "Customer@123",
     "address": {"full_name": "Amit Patel", "phone": "9845123679", "address_line1": "321 SG Highway", "address_line2": "Satellite", "city": "Ahmedabad", "state": "Gujarat", "pincode": "380015", "address_type": "home", "is_default": True}},
    {"email": "neha.reddy@example.com", "full_name": "Neha Reddy", "phone": "9712345679", "password": "Customer@123",
     "address": {"full_name": "Neha Reddy", "phone": "9712345679", "address_line1": "555 Banjara Hills", "address_line2": "Road 12", "city": "Hyderabad", "state": "Telangana", "pincode": "500034", "address_type": "home", "is_default": True}}
]

def seed_database():
    db = next(get_db())
    try:
        print("Starting database seeding...")
        
        admin_user = db.query(User).filter(User.email == "suryag.chinnathambi@gmail.com").first()
        if not admin_user:
            admin_user = User(email="suryag.chinnathambi@gmail.com", full_name="Surya Chinnathambi", phone="9876543210",
                password_hash=get_password_hash("Surya@123"), role=UserRole.ADMIN, is_active=True, created_at=datetime.utcnow())
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"Admin created: {admin_user.email}")
        else:
            print(f"Admin exists: {admin_user.email}")
        
        store = db.query(Store).filter(Store.name == "CMS Store").first()
        if not store:
            store = Store(id=uuid.uuid4(), external_id="CMS-" + str(uuid.uuid4())[:8], name="CMS Store", slug="cms-store",
                owner_name="Surya Chinnathambi", owner_email="suryag.chinnathambi@gmail.com", owner_phone="9876543210",
                address="123 Main Street", city="Mumbai", state="Maharashtra", pincode="400001",
                sync_api_key=secrets.token_urlsafe(32), status=StoreStatus.ACTIVE, sync_tier=StoreTier.TIER1,
                created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            db.add(store)
            db.commit()
            db.refresh(store)
            print(f"Store created: {store.id}")
        else:
            print(f"Store exists: {store.id}")
        
        if not admin_user.store_id:
            admin_user.store_id = store.id
            db.commit()
            print("Admin linked to store")
        
        categories = {}
        for cat_name in set([p["category"] for p in SAMPLE_PRODUCTS]):
            cat = db.query(Category).filter(Category.store_id == store.id, Category.name == cat_name).first()
            if not cat:
                cat = Category(id=uuid.uuid4(), store_id=store.id, name=cat_name,
                    slug=cat_name.lower().replace(" ", "-").replace("&", "and"), description=f"{cat_name} products",
                    is_active=True, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
                db.add(cat)
                db.commit()
                db.refresh(cat)
            categories[cat_name] = cat.id
        print(f"Categories: {len(categories)}")
        
        products_created = 0
        for p in SAMPLE_PRODUCTS:
            if not db.query(Product).filter(Product.store_id == store.id, Product.sku == p["sku"]).first():
                prod = Product(id=uuid.uuid4(), external_id=p["sku"], store_id=store.id, category_id=categories[p["category"]], sku=p["sku"],
                    name=p["name"], slug=p["name"].lower().replace(" ", "-"), description=p["description"],
                    mrp=p["mrp"], selling_price=p["selling_price"], quantity=100, is_active=True,
                    created_at=datetime.utcnow(), updated_at=datetime.utcnow())
                db.add(prod)
                products_created += 1
        db.commit()
        print(f"Products created: {products_created}")
        
        users_created = 0
        for u in SAMPLE_USERS:
            if not db.query(User).filter(User.email == u["email"]).first():
                user = User(email=u["email"], full_name=u["full_name"], phone=u["phone"],
                    password_hash=get_password_hash(u["password"]), role=UserRole.CUSTOMER,
                    is_active=True, created_at=datetime.utcnow())
                db.add(user)
                db.commit()
                db.refresh(user)
                addr = Address(user_id=user.id, full_name=u["address"]["full_name"], phone=u["address"]["phone"],
                    address_line1=u["address"]["address_line1"], address_line2=u["address"]["address_line2"],
                    city=u["address"]["city"], state=u["address"]["state"], pincode=u["address"]["pincode"],
                    address_type=u["address"]["address_type"], is_default=u["address"]["is_default"],
                    created_at=datetime.utcnow())
                db.add(addr)
                db.commit()
                users_created += 1
                print(f"User created: {user.email}")
        
        print("\n" + "="*60)
        print("SEEDING COMPLETED!")
        print("="*60)
        print(f"Store: CMS Store")
        print(f"Store ID: {store.id}")
        print(f"Admin: suryag.chinnathambi@gmail.com / Surya@123")
        print(f"Products: {db.query(Product).filter(Product.store_id == store.id).count()}")
        print(f"Categories: {len(categories)}")
        print(f"Customers: 5 (Password: Customer@123)")
        for u in SAMPLE_USERS:
            print(f"  - {u['email']}")
        print(f"\nAccess: http://localhost:3000?store_id={store.id}")
        print("="*60)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
