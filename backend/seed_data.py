import sys
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Store, Product, Category, StoreStatus, StoreTier
from app.models.auth_models import User, UserRole, Address
from app.core.security import get_password_hash
import uuid
import secrets

# Sample product data
SAMPLE_PRODUCTS = [
    # Electronics
    {"name": "Samsung Galaxy S24 Ultra", "category": "Electronics", "price": 89999, "description": "Latest flagship smartphone with 200MP camera", "sku": "ELEC-001"},
    {"name": "iPhone 15 Pro Max", "category": "Electronics", "price": 159900, "description": "Apple''s premium smartphone with A17 Pro chip", "sku": "ELEC-002"},
    {"name": "OnePlus 12", "category": "Electronics", "price": 64999, "description": "High-performance Android phone with flagship specs", "sku": "ELEC-003"},
    {"name": "Sony WH-1000XM5 Headphones", "category": "Electronics", "price": 29990, "description": "Industry-leading noise cancellation headphones", "sku": "ELEC-004"},
    {"name": "Apple AirPods Pro 2", "category": "Electronics", "price": 24900, "description": "Premium wireless earbuds with active noise cancellation", "sku": "ELEC-005"},
    {"name": "Dell XPS 15 Laptop", "category": "Electronics", "price": 145000, "description": "15-inch premium laptop for professionals", "sku": "ELEC-006"},
    {"name": "MacBook Air M3", "category": "Electronics", "price": 114900, "description": "Thin and light laptop with Apple Silicon", "sku": "ELEC-007"},
    {"name": "iPad Pro 12.9", "category": "Electronics", "price": 112900, "description": "Professional tablet with M2 chip", "sku": "ELEC-008"},
    {"name": "Samsung Galaxy Tab S9", "category": "Electronics", "price": 76999, "description": "Premium Android tablet with S Pen", "sku": "ELEC-009"},
    {"name": "Apple Watch Series 9", "category": "Electronics", "price": 41900, "description": "Advanced health and fitness smartwatch", "sku": "ELEC-010"},
    
    # Fashion - Men
    {"name": "Levi''s 501 Original Jeans", "category": "Fashion", "price": 3999, "description": "Classic straight fit denim jeans", "sku": "FASH-011"},
    {"name": "Nike Air Max 270", "category": "Fashion", "price": 12795, "description": "Men''s running shoes with air cushioning", "sku": "FASH-012"},
    {"name": "Adidas Ultraboost 23", "category": "Fashion", "price": 16999, "description": "Premium running shoes with boost technology", "sku": "FASH-013"},
    {"name": "Van Heusen Formal Shirt", "category": "Fashion", "price": 1499, "description": "Classic fit formal shirt for office wear", "sku": "FASH-014"},
    {"name": "Peter England Blazer", "category": "Fashion", "price": 4999, "description": "Men''s formal blazer for business occasions", "sku": "FASH-015"},
    {"name": "Allen Solly Chinos", "category": "Fashion", "price": 2499, "description": "Comfortable slim fit casual pants", "sku": "FASH-016"},
    {"name": "Puma T-Shirt Pack", "category": "Fashion", "price": 1299, "description": "Set of 3 casual t-shirts", "sku": "FASH-017"},
    {"name": "Woodland Leather Shoes", "category": "Fashion", "price": 3495, "description": "Genuine leather formal shoes", "sku": "FASH-018"},
    {"name": "Fossil Analog Watch", "category": "Fashion", "price": 8995, "description": "Classic men''s wristwatch with leather strap", "sku": "FASH-019"},
    {"name": "Ray-Ban Aviator Sunglasses", "category": "Fashion", "price": 6990, "description": "Classic aviator style sunglasses", "sku": "FASH-020"},
    
    # Fashion - Women
    {"name": "Zara Floral Dress", "category": "Fashion", "price": 2990, "description": "Elegant floral print summer dress", "sku": "FASH-021"},
    {"name": "H&M Casual Top", "category": "Fashion", "price": 999, "description": "Women''s casual cotton top", "sku": "FASH-022"},
    {"name": "Forever 21 Denim Jacket", "category": "Fashion", "price": 2499, "description": "Classic blue denim jacket", "sku": "FASH-023"},
    {"name": "Biba Kurti Set", "category": "Fashion", "price": 1899, "description": "Traditional Indian ethnic wear", "sku": "FASH-024"},
    {"name": "W for Woman Palazzo", "category": "Fashion", "price": 1599, "description": "Comfortable wide-leg pants", "sku": "FASH-025"},
    {"name": "Fabindia Cotton Saree", "category": "Fashion", "price": 3499, "description": "Handwoven cotton saree", "sku": "FASH-026"},
    {"name": "Nike Women''s Sports Bra", "category": "Fashion", "price": 1895, "description": "High support sports bra", "sku": "FASH-027"},
    {"name": "Sketchers Go Walk", "category": "Fashion", "price": 4999, "description": "Women''s comfortable walking shoes", "sku": "FASH-028"},
    {"name": "Michael Kors Handbag", "category": "Fashion", "price": 15999, "description": "Designer leather handbag", "sku": "FASH-029"},
    {"name": "Accessorize Jewelry Set", "category": "Fashion", "price": 1299, "description": "Fashion jewelry necklace and earrings", "sku": "FASH-030"},
    
    # Home & Kitchen
    {"name": "Philips Air Fryer", "category": "Home & Kitchen", "price": 8990, "description": "Healthy cooking with rapid air technology", "sku": "HOME-031"},
    {"name": "Prestige Induction Cooktop", "category": "Home & Kitchen", "price": 2499, "description": "Energy efficient cooking appliance", "sku": "HOME-032"},
    {"name": "Bajaj Mixer Grinder", "category": "Home & Kitchen", "price": 3299, "description": "3 jar mixer grinder for kitchen", "sku": "HOME-033"},
    {"name": "Borosil Microwave Safe Bowls", "category": "Home & Kitchen", "price": 799, "description": "Set of 6 glass bowls", "sku": "HOME-034"},
    {"name": "Cello Water Bottle Set", "category": "Home & Kitchen", "price": 499, "description": "Set of 4 plastic water bottles", "sku": "HOME-035"},
    {"name": "Milton Casserole Set", "category": "Home & Kitchen", "price": 1999, "description": "Insulated food serving casseroles", "sku": "HOME-036"},
    {"name": "Hawkins Pressure Cooker", "category": "Home & Kitchen", "price": 2195, "description": "5 liter aluminum pressure cooker", "sku": "HOME-037"},
    {"name": "Pigeon Non-Stick Cookware", "category": "Home & Kitchen", "price": 1899, "description": "Set of 3 non-stick pans", "sku": "HOME-038"},
    {"name": "Amazon Basics Bed Sheet", "category": "Home & Kitchen", "price": 1299, "description": "Queen size cotton bed sheet set", "sku": "HOME-039"},
    {"name": "IKEA Curtains", "category": "Home & Kitchen", "price": 1499, "description": "Blackout curtains for bedroom", "sku": "HOME-040"},
    
    # Groceries
    {"name": "Tata Tea Premium", "category": "Groceries", "price": 485, "description": "1kg pack of premium tea leaves", "sku": "GROC-041"},
    {"name": "Nescafe Classic Coffee", "category": "Groceries", "price": 325, "description": "200g instant coffee powder", "sku": "GROC-042"},
    {"name": "Fortune Sunflower Oil", "category": "Groceries", "price": 785, "description": "5 liter refined cooking oil", "sku": "GROC-043"},
    {"name": "Aashirvaad Whole Wheat Atta", "category": "Groceries", "price": 410, "description": "10kg chakki fresh atta", "sku": "GROC-044"},
    {"name": "India Gate Basmati Rice", "category": "Groceries", "price": 750, "description": "5kg premium basmati rice", "sku": "GROC-045"},
    {"name": "Amul Butter", "category": "Groceries", "price": 56, "description": "100g salted butter", "sku": "GROC-046"},
    {"name": "Britannia Good Day Biscuits", "category": "Groceries", "price": 30, "description": "Pack of cookies", "sku": "GROC-047"},
    {"name": "Maggi Noodles Pack", "category": "Groceries", "price": 144, "description": "12 pack of instant noodles", "sku": "GROC-048"},
    {"name": "Lays Chips", "category": "Groceries", "price": 20, "description": "50g pack of potato chips", "sku": "GROC-049"},
    {"name": "Coca Cola 2L", "category": "Groceries", "price": 90, "description": "2 liter cold drink bottle", "sku": "GROC-050"},
    
    # Books
    {"name": "The Alchemist - Paulo Coelho", "category": "Books", "price": 299, "description": "Bestselling fiction novel", "sku": "BOOK-051"},
    {"name": "Atomic Habits - James Clear", "category": "Books", "price": 499, "description": "Self-help book on building habits", "sku": "BOOK-052"},
    {"name": "Rich Dad Poor Dad", "category": "Books", "price": 349, "description": "Personal finance classic", "sku": "BOOK-053"},
    {"name": "The Psychology of Money", "category": "Books", "price": 399, "description": "Understanding wealth and happiness", "sku": "BOOK-054"},
    {"name": "Ikigai", "category": "Books", "price": 299, "description": "Japanese secret to long life", "sku": "BOOK-055"},
    {"name": "Harry Potter Collection", "category": "Books", "price": 2999, "description": "Complete 7 book set", "sku": "BOOK-056"},
    {"name": "Think Like a Monk", "category": "Books", "price": 399, "description": "Jay Shetty''s guide to peace", "sku": "BOOK-057"},
    {"name": "The 5 AM Club", "category": "Books", "price": 349, "description": "Robin Sharma''s productivity guide", "sku": "BOOK-058"},
    {"name": "Sapiens", "category": "Books", "price": 499, "description": "Brief history of humankind", "sku": "BOOK-059"},
    {"name": "Deep Work", "category": "Books", "price": 399, "description": "Cal Newport on focused success", "sku": "BOOK-060"},
    
    # Sports & Fitness
    {"name": "Nivia Football", "category": "Sports", "price": 699, "description": "Size 5 professional football", "sku": "SPOR-061"},
    {"name": "Yonex Badminton Racket", "category": "Sports", "price": 1899, "description": "Professional badminton racket", "sku": "SPOR-062"},
    {"name": "Cosco Cricket Bat", "category": "Sports", "price": 2499, "description": "Kashmir willow cricket bat", "sku": "SPOR-063"},
    {"name": "Nivia Gym Bag", "category": "Sports", "price": 799, "description": "Durable sports duffle bag", "sku": "SPOR-064"},
    {"name": "Boldfit Resistance Bands", "category": "Sports", "price": 499, "description": "Set of 5 exercise bands", "sku": "SPOR-065"},
    {"name": "Strauss Yoga Mat", "category": "Sports", "price": 699, "description": "Anti-slip exercise mat", "sku": "SPOR-066"},
    {"name": "Boldfit Dumbbells Set", "category": "Sports", "price": 1999, "description": "Pair of adjustable dumbbells", "sku": "SPOR-067"},
    {"name": "Nivia Skipping Rope", "category": "Sports", "price": 199, "description": "Professional jump rope", "sku": "SPOR-068"},
    {"name": "Decathlon Bicycle", "category": "Sports", "price": 15999, "description": "Mountain bike 21 speed", "sku": "SPOR-069"},
    {"name": "Fitbit Charge 6", "category": "Sports", "price": 13999, "description": "Fitness tracker with GPS", "sku": "SPOR-070"},
    
    # Beauty & Personal Care
    {"name": "Lakme Absolute Foundation", "category": "Beauty", "price": 850, "description": "Matte finish foundation", "sku": "BEAU-071"},
    {"name": "Maybelline Mascara", "category": "Beauty", "price": 599, "description": "Volumizing black mascara", "sku": "BEAU-072"},
    {"name": "LOreal Paris Shampoo", "category": "Beauty", "price": 399, "description": "Hair fall defense shampoo", "sku": "BEAU-073"},
    {"name": "Dove Soap Pack", "category": "Beauty", "price": 199, "description": "Pack of 3 beauty bars", "sku": "BEAU-074"},
    {"name": "Nivea Body Lotion", "category": "Beauty", "price": 349, "description": "Moisturizing body lotion", "sku": "BEAU-075"},
    {"name": "Gillette Fusion Razor", "category": "Beauty", "price": 799, "description": "5 blade razor for men", "sku": "BEAU-076"},
    {"name": "Plum Face Wash", "category": "Beauty", "price": 349, "description": "Green tea face wash", "sku": "BEAU-077"},
    {"name": "Biotique Bio Kelp Shampoo", "category": "Beauty", "price": 299, "description": "Protein shampoo for hair", "sku": "BEAU-078"},
    {"name": "The Body Shop Tea Tree Oil", "category": "Beauty", "price": 895, "description": "Natural tea tree essential oil", "sku": "BEAU-079"},
    {"name": "Mamaearth Vitamin C Serum", "category": "Beauty", "price": 599, "description": "Face serum with vitamin C", "sku": "BEAU-080"},
    
    # Toys & Baby Products
    {"name": "LEGO Classic Set", "category": "Toys", "price": 2999, "description": "Creative building blocks set", "sku": "TOYS-081"},
    {"name": "Hot Wheels Car Pack", "category": "Toys", "price": 999, "description": "Set of 10 die-cast cars", "sku": "TOYS-082"},
    {"name": "Barbie Doll", "category": "Toys", "price": 1299, "description": "Fashion doll with accessories", "sku": "TOYS-083"},
    {"name": "Nerf Gun Blaster", "category": "Toys", "price": 1999, "description": "Toy foam dart blaster", "sku": "TOYS-084"},
    {"name": "Funskool Board Games", "category": "Toys", "price": 799, "description": "Classic family board game", "sku": "TOYS-085"},
    {"name": "Hamleys Soft Toy", "category": "Toys", "price": 1499, "description": "Plush teddy bear", "sku": "TOYS-086"},
    {"name": "Fisher Price Baby Walker", "category": "Toys", "price": 2499, "description": "Interactive baby walker", "sku": "TOYS-087"},
    {"name": "Pampers Diaper Pack", "category": "Toys", "price": 1299, "description": "Pack of 72 baby diapers", "sku": "TOYS-088"},
    {"name": "Johnson Baby Care Set", "category": "Toys", "price": 699, "description": "Shampoo, lotion and soap", "sku": "TOYS-089"},
    {"name": "Mee Mee Baby Bottle", "category": "Toys", "price": 349, "description": "Set of 2 feeding bottles", "sku": "TOYS-090"},
    
    # Automotive
    {"name": "Shell Engine Oil", "category": "Automotive", "price": 1899, "description": "4 liter synthetic engine oil", "sku": "AUTO-091"},
    {"name": "Bosch Car Battery", "category": "Automotive", "price": 6999, "description": "12V 65Ah car battery", "sku": "AUTO-092"},
    {"name": "3M Car Polish", "category": "Automotive", "price": 599, "description": "Scratch remover polish", "sku": "AUTO-093"},
    {"name": "Philips LED Headlight Bulb", "category": "Automotive", "price": 1299, "description": "H4 LED car headlight", "sku": "AUTO-094"},
    {"name": "Michelin Car Wiper Blades", "category": "Automotive", "price": 799, "description": "Pair of windshield wipers", "sku": "AUTO-095"},
    {"name": "Turtle Wax Car Shampoo", "category": "Automotive", "price": 449, "description": "Car wash and wax shampoo", "sku": "AUTO-096"},
    {"name": "Wavex Tyre Shine Spray", "category": "Automotive", "price": 299, "description": "Tire dressing spray", "sku": "AUTO-097"},
    {"name": "Carmate Car Perfume", "category": "Automotive", "price": 199, "description": "Dashboard air freshener", "sku": "AUTO-098"},
    {"name": "AutoRight Steering Cover", "category": "Automotive", "price": 399, "description": "Leather steering wheel cover", "sku": "AUTO-099"},
    {"name": "ResQ Tire Inflator", "category": "Automotive", "price": 1499, "description": "Portable air compressor", "sku": "AUTO-100"},
]

# Sample user data
SAMPLE_USERS = [
    {
        "email": "priya.sharma@example.com",
        "full_name": "Priya Sharma",
        "phone": "9876543210",
        "password": "Customer@123",
        "address": {
            "full_name": "Priya Sharma",
            "phone": "9876543210",
            "address_line1": "123 MG Road",
            "address_line2": "Near City Mall",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "address_type": "home",
            "is_default": True
        }
    },
    {
        "email": "rajesh.kumar@example.com",
        "full_name": "Rajesh Kumar",
        "phone": "9123456789",
        "password": "Customer@123",
        "address": {
            "full_name": "Rajesh Kumar",
            "phone": "9123456789",
            "address_line1": "456 Park Street",
            "address_line2": "Opposite Metro Station",
            "city": "Bangalore",
            "state": "Karnataka",
            "pincode": "560001",
            "address_type": "home",
            "is_default": True
        }
    },
    {
        "email": "anita.verma@example.com",
        "full_name": "Anita Verma",
        "phone": "9988776655",
        "password": "Customer@123",
        "address": {
            "full_name": "Anita Verma",
            "phone": "9988776655",
            "address_line1": "789 Anna Salai",
            "address_line2": "T Nagar",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "pincode": "600017",
            "address_type": "home",
            "is_default": True
        }
    },
    {
        "email": "amit.patel@example.com",
        "full_name": "Amit Patel",
        "phone": "9845123678",
        "password": "Customer@123",
        "address": {
            "full_name": "Amit Patel",
            "phone": "9845123678",
            "address_line1": "321 SG Highway",
            "address_line2": "Satellite Area",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "pincode": "380015",
            "address_type": "home",
            "is_default": True
        }
    },
    {
        "email": "neha.reddy@example.com",
        "full_name": "Neha Reddy",
        "phone": "9712345678",
        "password": "Customer@123",
        "address": {
            "full_name": "Neha Reddy",
            "phone": "9712345678",
            "address_line1": "555 Banjara Hills",
            "address_line2": "Road No 12",
            "city": "Hyderabad",
            "state": "Telangana",
            "pincode": "500034",
            "address_type": "home",
            "is_default": True
        }
    }
]

def seed_database():
    db = next(get_db())
    
    try:
        print(" Starting database seeding...")
        
        # 1. Create admin user for CMS Store
        print("\n Step 1: Creating admin user...")
        admin_user = db.query(User).filter(User.email == "suryag.chinnathambi@gmail.com").first()
        if not admin_user:
            admin_user = User(
                email="suryag.chinnathambi@gmail.com",
                full_name="Surya Chinnathambi",
                phone="9876543210",
                password_hash=get_password_hash("Surya@123"),
                role=UserRole.ADMIN,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f" Admin user created: {admin_user.email}")
        else:
            print(f"i Admin user already exists: {admin_user.email}")
        
        # 2. Create CMS Store
        print("\n Step 2: Creating CMS Store...")
        store = db.query(Store).filter(Store.name == "CMS Store").first()
        if not store:
            api_key = secrets.token_urlsafe(32)
            store = Store(
                id=uuid.uuid4(),
                external_id="CMS-" + str(uuid.uuid4())[:8],
                name="CMS Store",
                slug="cms-store",
                owner_name="Surya Chinnathambi",
                owner_email="suryag.chinnathambi@gmail.com",
                owner_phone="9876543210",
                address="123 Main Street, City Center",
                city="Mumbai",
                state="Maharashtra",
                pincode="400001",
                sync_api_key=api_key,
                status=StoreStatus.ACTIVE,
                sync_tier=StoreTier.TIER1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(store)
            db.commit()
            db.refresh(store)
            print(f" CMS Store created with ID: {store.id}")
        else:
            print(f"i CMS Store already exists with ID: {store.id}")
        
        # Update admin user with store reference
        if not admin_user.store_id:
            admin_user.store_id=store.id
            db.commit()
            print(f" Admin user linked to CMS Store")
        
        # 3. Create categories
        print("\n Step 3: Creating product categories...")
        categories = {}
        category_names = list(set([p["category"] for p in SAMPLE_PRODUCTS]))
        
        for cat_name in category_names:
            category = db.query(Category).filter(
                Category.store_id == store.id,
                Category.name == cat_name
            ).first()
            
            if not category:
                category = Category(
                    id=uuid.uuid4(),
                    store_id=store.id,
                    name=cat_name,
                    slug=cat_name.lower().replace(" ", "-").replace("&", "and"),
                    description=f"{cat_name} products",
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(category)
                db.commit()
                db.refresh(category)
            
            categories[cat_name] = category.id
        
        print(f" Created {len(categories)} categories")
        
        # 4. Create 100 products
        print("\n Step 4: Creating 100 products...")
        existing_products = db.query(Product).filter(Product.store_id == store.id).count()
        
        if existing_products < 100:
            products_created = 0
            for product_data in SAMPLE_PRODUCTS:
                # Check if product already exists
                existing = db.query(Product).filter(
                    Product.store_id == store.id,
                    Product.sku == product_data["sku"]
                ).first()
                
                if not existing:
                    product = Product(
                        id=uuid.uuid4(),
                        store_id=store.id,
                        category_id=categories[product_data["category"]],
                        sku=product_data["sku"],
                        name=product_data["name"],
                        slug=product_data["name"].lower().replace(" ", "-").replace("''", ""),
                        description=product_data["description"],
                        mrp=product_data[price],
                        selling_price=product_data[price],
                        quantity=100,
                        external_id=product_data[sku],
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(product)
                    products_created += 1
            
            db.commit()
            print(f" Created {products_created} new products (Total: {existing_products + products_created})")
        else:
            print(f"i Already have {existing_products} products")
        
        # 5. Create 5 sample customer users
        print("\n Step 5: Creating 5 sample customer users...")
        users_created = 0
        
        for user_data in SAMPLE_USERS:
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            
            if not existing_user:
                new_user = User(
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    phone=user_data["phone"],
                    password_hash=get_password_hash(user_data["password"]),
                    role=UserRole.CUSTOMER,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                
                # Create default address
                address = Address(
                    user_id=new_user.id,
                    full_name=user_data["address"]["full_name"],
                    phone=user_data["address"]["phone"],
                    address_line1=user_data["address"]["address_line1"],
                    address_line2=user_data["address"]["address_line2"],
                    city=user_data["address"]["city"],
                    state=user_data["address"]["state"],
                    pincode=user_data["address"]["pincode"],
                    address_type=user_data["address"]["address_type"],
                    is_default=user_data["address"]["is_default"],
                    created_at=datetime.utcnow()
                )
                db.add(address)
                db.commit()
                
                users_created += 1
                print(f" Created user: {new_user.email}")
            else:
                print(f"i User already exists: {user_data['email']}")
        
        print(f"\n Created {users_created} new customer users")
        
        # Print summary
        print("\n" + "="*60)
        print(" DATABASE SEEDING COMPLETED!")
        print("="*60)
        print(f"\n Summary:")
        print(f"  - Store Name: CMS Store")
        print(f"  - Store ID: {store.id}")
        print(f"  - Admin Email: suryag.chinnathambi@gmail.com")
        print(f"  - Admin Password: Surya@123")
        print(f"  - Total Products: {db.query(Product).filter(Product.store_id == store.id).count()}")
        print(f"  - Total Categories: {len(categories)}")
        print(f"  - Total Customer Users: 5")
        print(f"\n Sample Customer Credentials (Password: Customer@123):")
        for user_data in SAMPLE_USERS:
            print(f"  - {user_data['email']}")
        print(f"\n Access the store at:")
        print(f"  http://localhost:3000?store_id={store.id}")
        print("="*60)
        
    except Exception as e:
        print(f"\n Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
