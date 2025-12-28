from app.core.database import get_db
from app.models.models import Store, Product, Category
from app.models.auth_models import User, UserRole, Address
from app.core.security import get_password_hash
import uuid
from datetime import datetime

db = next(get_db())

# Get store
store = db.query(Store).filter(Store.name == "CMS Store").first()
print(f"Store: {store.id}")

# Sample categories and products
items = [
    ("Electronics", "Samsung Galaxy S24", "ELEC-001", 89999),
    ("Electronics", "iPhone 15 Pro", "ELEC-002", 139900),
    ("Electronics", "Sony Headphones", "ELEC-003", 29990),
    ("Electronics", "Dell Laptop", "ELEC-004", 75000),
    ("Electronics", "Apple Watch", "ELEC-005", 41900),
    ("Fashion", "Levis Jeans", "FASH-001", 3999),
    ("Fashion", "Nike Shoes", "FASH-002", 12795),
    ("Fashion", "Formal Shirt", "FASH-003", 1499),
    ("Fashion", "Denim Jacket", "FASH-004", 2499),
    ("Fashion", "Sports Watch", "FASH-005", 8995),
    ("Home", "Air Fryer", "HOME-001", 8990),
    ("Home", "Mixer Grinder", "HOME-002", 3299),
    ("Home", "Pressure Cooker", "HOME-003", 2195),
    ("Home", "Bed Sheet Set", "HOME-004", 1299),
    ("Home", "Curtains", "HOME-005", 1499),
    ("Groceries", "Tea 1kg", "GROC-001", 485),
    ("Groceries", "Coffee 200g", "GROC-002", 325),
    ("Groceries", "Cooking Oil 5L", "GROC-003", 785),
    ("Groceries", "Wheat Flour 10kg", "GROC-004", 410),
    ("Groceries", "Rice 5kg", "GROC-005", 750),
]

cats = {}
for cat_name, prod_name, sku, price in items:
    if cat_name not in cats:
        cat = db.query(Category).filter(Category.store_id == store.id, Category.name == cat_name).first()
        if not cat:
            cat = Category(id=uuid.uuid4(), store_id=store.id, name=cat_name, slug=cat_name.lower(), is_active=True)
            db.add(cat)
            db.flush()
        cats[cat_name] = cat.id
    
    existing = db.query(Product).filter(Product.sku == sku, Product.store_id == store.id).first()
    if not existing:
        p = Product(
            id=uuid.uuid4(),
            store_id=store.id,
            category_id=cats[cat_name],
            sku=sku,
            external_id=sku,
            name=prod_name,
            slug=prod_name.lower().replace(" ", "-"),
            mrp=float(price),
            selling_price=float(price),
            quantity=100,
            is_active=True
        )
        db.add(p)
        print(f"Added: {prod_name}")

db.commit()
print(f"\n✅ {len(items)} products created!")

# Create sample users
users_data = [
    ("priya.sharma@example.com", "Priya Sharma", "9876543210"),
    ("rajesh.kumar@example.com", "Rajesh Kumar", "9123456789"),
    ("anita.verma@example.com", "Anita Verma", "9988776655"),
    ("amit.patel@example.com", "Amit Patel", "9845123678"),
    ("neha.reddy@example.com", "Neha Reddy", "9712345678"),
]

for email, name, phone in users_data:
    existing = db.query(User).filter(User.email == email).first()
    if not existing:
        user = User(
            email=email,
            full_name=name,
            phone=phone,
            password_hash=get_password_hash("Customer@123"),
            role=UserRole.CUSTOMER,
            is_active=True
        )
        db.add(user)
        db.flush()
        
        addr = Address(
            user_id=user.id,
            full_name=name,
            phone=phone,
            address_line1="123 Main Street",
            city="Mumbai",
            state="Maharashtra",
            pincode="400001",
            address_type="home",
            is_default=True
        )
        db.add(addr)
        print(f"Added user: {email}")

db.commit()
print(f"\n✅ {len(users_data)} users created!")

print("\n" + "="*60)
print("🎉 SEEDING COMPLETED!")
print("="*60)
print(f"Store ID: {store.id}")
print(f"Admin: suryag.chinnathambi@gmail.com / Surya@123")
print(f"Customer accounts: (all passwords: Customer@123)")
for email, _, _ in users_data:
    print(f"  - {email}")
print(f"\n🌐 Access: http://localhost:3000?store_id={store.id}")
print("="*60)
