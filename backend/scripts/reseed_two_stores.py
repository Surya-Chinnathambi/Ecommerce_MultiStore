"""
Reseed script: Clears ALL data and creates 2 stores with 100 products each.

Store 1: CMS Store     – suryag.chinnathambi@gmail.com / Surya@123
Store 2: SS_Stores     – gstb6505@gmail.com            / Surya@123
Each store also gets 5 customers.
"""
import sys
import uuid
import secrets
import re
from datetime import datetime

sys.path.insert(0, "/app")

from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.models import Store, Product, Category, StoreStatus, StoreTier
from app.models.auth_models import User, UserRole, Address
from app.core.security import get_password_hash

# ---------------------------------------------------------------------------
# Product catalogue – 100 unique SKUs across 10 categories
# ---------------------------------------------------------------------------

PRODUCTS = [
    # Electronics (10)
    {"name": "Samsung Galaxy S24 Ultra", "cat": "Electronics", "price": 89999, "desc": "200MP flagship smartphone", "sku": "ELEC-001"},
    {"name": "iPhone 15 Pro Max", "cat": "Electronics", "price": 159900, "desc": "Apple A17 Pro chip smartphone", "sku": "ELEC-002"},
    {"name": "OnePlus 12 5G", "cat": "Electronics", "price": 64999, "desc": "Snapdragon 8 Gen 3 phone", "sku": "ELEC-003"},
    {"name": "Sony WH-1000XM5 Headphones", "cat": "Electronics", "price": 29990, "desc": "Industry-leading ANC headphones", "sku": "ELEC-004"},
    {"name": "Apple AirPods Pro 2", "cat": "Electronics", "price": 24900, "desc": "Active noise cancellation earbuds", "sku": "ELEC-005"},
    {"name": "Dell XPS 15 Laptop", "cat": "Electronics", "price": 145000, "desc": "15-inch professional laptop", "sku": "ELEC-006"},
    {"name": "MacBook Air M3", "cat": "Electronics", "price": 114900, "desc": "Apple Silicon ultra-thin laptop", "sku": "ELEC-007"},
    {"name": "iPad Pro 12.9 M2", "cat": "Electronics", "price": 112900, "desc": "Professional tablet with M2 chip", "sku": "ELEC-008"},
    {"name": "Apple Watch Series 9", "cat": "Electronics", "price": 41900, "desc": "Advanced health smartwatch", "sku": "ELEC-009"},
    {"name": "Bose QuietComfort 45", "cat": "Electronics", "price": 24500, "desc": "Wireless noise-cancelling headphones", "sku": "ELEC-010"},

    # Fashion (10)
    {"name": "Levi's 501 Original Jeans", "cat": "Fashion", "price": 3999, "desc": "Classic straight-fit denim jeans", "sku": "FASH-011"},
    {"name": "Nike Air Max 270", "cat": "Fashion", "price": 12795, "desc": "Men's air-cushioned running shoes", "sku": "FASH-012"},
    {"name": "Adidas Ultraboost 23", "cat": "Fashion", "price": 16999, "desc": "Boost-technology premium runners", "sku": "FASH-013"},
    {"name": "Van Heusen Formal Shirt", "cat": "Fashion", "price": 1499, "desc": "Classic fit office shirt", "sku": "FASH-014"},
    {"name": "Peter England Blazer", "cat": "Fashion", "price": 4999, "desc": "Men's formal business blazer", "sku": "FASH-015"},
    {"name": "Allen Solly Chinos", "cat": "Fashion", "price": 2499, "desc": "Slim fit casual pants", "sku": "FASH-016"},
    {"name": "Puma T-Shirt Pack of 3", "cat": "Fashion", "price": 1299, "desc": "3-pack casual t-shirts", "sku": "FASH-017"},
    {"name": "Woodland Leather Shoes", "cat": "Fashion", "price": 3495, "desc": "Genuine leather formal shoes", "sku": "FASH-018"},
    {"name": "Fossil Analog Watch", "cat": "Fashion", "price": 8995, "desc": "Classic leather-strap wristwatch", "sku": "FASH-019"},
    {"name": "Ray-Ban Aviator Sunglasses", "cat": "Fashion", "price": 6990, "desc": "Iconic aviator style shades", "sku": "FASH-020"},

    # Home & Kitchen (10)
    {"name": "Philips Air Fryer HD9252", "cat": "Home & Kitchen", "price": 8990, "desc": "Rapid-air healthy cooking", "sku": "HOME-021"},
    {"name": "Prestige Induction Cooktop", "cat": "Home & Kitchen", "price": 2499, "desc": "Energy-efficient single burner", "sku": "HOME-022"},
    {"name": "Bajaj Mixer Grinder 750W", "cat": "Home & Kitchen", "price": 3299, "desc": "3-jar mixer grinder", "sku": "HOME-023"},
    {"name": "Borosil Microwave Bowls Set", "cat": "Home & Kitchen", "price": 799, "desc": "Set of 6 glass bowls", "sku": "HOME-024"},
    {"name": "Milton Casserole Set", "cat": "Home & Kitchen", "price": 1999, "desc": "Insulated serving casseroles", "sku": "HOME-025"},
    {"name": "Hawkins Pressure Cooker 5L", "cat": "Home & Kitchen", "price": 2195, "desc": "Aluminium pressure cooker", "sku": "HOME-026"},
    {"name": "Pigeon Non-Stick Cookware Set", "cat": "Home & Kitchen", "price": 1899, "desc": "Set of 3 non-stick pans", "sku": "HOME-027"},
    {"name": "Cello Water Bottle Set", "cat": "Home & Kitchen", "price": 499, "desc": "Set of 4 BPA-free bottles", "sku": "HOME-028"},
    {"name": "AmazonBasics Bed Sheet Queen", "cat": "Home & Kitchen", "price": 1299, "desc": "Queen-size cotton bedsheet set", "sku": "HOME-029"},
    {"name": "IKEA Blackout Curtains", "cat": "Home & Kitchen", "price": 1499, "desc": "Room-darkening bedroom curtains", "sku": "HOME-030"},

    # Groceries (10)
    {"name": "Tata Tea Premium 1kg", "cat": "Groceries", "price": 485, "desc": "Premium tea leaves pack", "sku": "GROC-031"},
    {"name": "Nescafe Classic 200g", "cat": "Groceries", "price": 325, "desc": "Instant coffee powder", "sku": "GROC-032"},
    {"name": "Fortune Sunflower Oil 5L", "cat": "Groceries", "price": 785, "desc": "Refined sunflower cooking oil", "sku": "GROC-033"},
    {"name": "Aashirvaad Whole Wheat Atta 10kg", "cat": "Groceries", "price": 410, "desc": "Chakki fresh atta", "sku": "GROC-034"},
    {"name": "India Gate Basmati Rice 5kg", "cat": "Groceries", "price": 750, "desc": "Premium aged basmati rice", "sku": "GROC-035"},
    {"name": "Amul Butter 100g", "cat": "Groceries", "price": 56, "desc": "Pasteurised salted butter", "sku": "GROC-036"},
    {"name": "Britannia Good Day 200g", "cat": "Groceries", "price": 30, "desc": "Butter cookies pack", "sku": "GROC-037"},
    {"name": "Maggi Noodles 12-Pack", "cat": "Groceries", "price": 144, "desc": "Masala instant noodles", "sku": "GROC-038"},
    {"name": "Lays Classic Chips 50g", "cat": "Groceries", "price": 20, "desc": "Salted potato chips", "sku": "GROC-039"},
    {"name": "Coca-Cola 2L Bottle", "cat": "Groceries", "price": 90, "desc": "Carbonated cola drink", "sku": "GROC-040"},

    # Books (10)
    {"name": "The Alchemist – Paulo Coelho", "cat": "Books", "price": 299, "desc": "Bestselling fiction novel", "sku": "BOOK-041"},
    {"name": "Atomic Habits – James Clear", "cat": "Books", "price": 499, "desc": "Build habits, break bad ones", "sku": "BOOK-042"},
    {"name": "Rich Dad Poor Dad", "cat": "Books", "price": 349, "desc": "Personal finance classic", "sku": "BOOK-043"},
    {"name": "The Psychology of Money", "cat": "Books", "price": 399, "desc": "Timeless lessons on wealth", "sku": "BOOK-044"},
    {"name": "Ikigai", "cat": "Books", "price": 299, "desc": "Japanese secret to long life", "sku": "BOOK-045"},
    {"name": "Harry Potter Box Set (7 Books)", "cat": "Books", "price": 2999, "desc": "Complete magical series", "sku": "BOOK-046"},
    {"name": "Think Like a Monk – Jay Shetty", "cat": "Books", "price": 399, "desc": "Train your mind for peace", "sku": "BOOK-047"},
    {"name": "The 5 AM Club – Robin Sharma", "cat": "Books", "price": 349, "desc": "Own your morning routine", "sku": "BOOK-048"},
    {"name": "Sapiens – Yuval Noah Harari", "cat": "Books", "price": 499, "desc": "Brief history of humankind", "sku": "BOOK-049"},
    {"name": "Deep Work – Cal Newport", "cat": "Books", "price": 399, "desc": "Rules for focused success", "sku": "BOOK-050"},

    # Sports (10)
    {"name": "Nivia Football Size 5", "cat": "Sports", "price": 699, "desc": "Professional match football", "sku": "SPOR-051"},
    {"name": "Yonex Badminton Racket", "cat": "Sports", "price": 1899, "desc": "Carbon fibre badminton racket", "sku": "SPOR-052"},
    {"name": "Cosco Kashmir Willow Bat", "cat": "Sports", "price": 2499, "desc": "Kashmir willow cricket bat", "sku": "SPOR-053"},
    {"name": "Boldfit Resistance Bands Set", "cat": "Sports", "price": 499, "desc": "Set of 5 exercise bands", "sku": "SPOR-054"},
    {"name": "Strauss Anti-Slip Yoga Mat", "cat": "Sports", "price": 699, "desc": "6mm thick exercise mat", "sku": "SPOR-055"},
    {"name": "Boldfit Adjustable Dumbbells", "cat": "Sports", "price": 1999, "desc": "Pair adjustable gym dumbbells", "sku": "SPOR-056"},
    {"name": "Nivia Pro Skipping Rope", "cat": "Sports", "price": 199, "desc": "Ball-bearing jump rope", "sku": "SPOR-057"},
    {"name": "Decathlon BTWIN Cycle 21-Speed", "cat": "Sports", "price": 15999, "desc": "Mountain bike 21-speed", "sku": "SPOR-058"},
    {"name": "Fitbit Charge 6 GPS", "cat": "Sports", "price": 13999, "desc": "Advanced fitness tracker", "sku": "SPOR-059"},
    {"name": "Nivia Gym Duffle Bag", "cat": "Sports", "price": 799, "desc": "Durable sports duffle bag", "sku": "SPOR-060"},

    # Beauty (10)
    {"name": "Lakme Absolute Matte Foundation", "cat": "Beauty", "price": 850, "desc": "Full-coverage matte finish", "sku": "BEAU-061"},
    {"name": "Maybelline Volumising Mascara", "cat": "Beauty", "price": 599, "desc": "Black lash-volumising mascara", "sku": "BEAU-062"},
    {"name": "L'Oreal Hair Fall Shampoo 400ml", "cat": "Beauty", "price": 399, "desc": "Strengthening hair shampoo", "sku": "BEAU-063"},
    {"name": "Dove Beauty Bar Pack of 3", "cat": "Beauty", "price": 199, "desc": "Moisturising soap bars", "sku": "BEAU-064"},
    {"name": "Nivea Moisturising Body Lotion", "cat": "Beauty", "price": 349, "desc": "Deep moisture body lotion", "sku": "BEAU-065"},
    {"name": "Gillette Fusion ProGlide Razor", "cat": "Beauty", "price": 799, "desc": "5-blade precision razor", "sku": "BEAU-066"},
    {"name": "Plum Green Tea Face Wash", "cat": "Beauty", "price": 349, "desc": "Oil-control green tea cleanse", "sku": "BEAU-067"},
    {"name": "Biotique Bio Kelp Shampoo 400ml", "cat": "Beauty", "price": 299, "desc": "Protein-rich hair shampoo", "sku": "BEAU-068"},
    {"name": "The Body Shop Tea Tree Oil", "cat": "Beauty", "price": 895, "desc": "Pure tea tree essential oil", "sku": "BEAU-069"},
    {"name": "Mamaearth Vitamin C Serum 30ml", "cat": "Beauty", "price": 599, "desc": "Brightening vitamin-C face serum", "sku": "BEAU-070"},

    # Toys (10)
    {"name": "LEGO Classic Creative Bricks", "cat": "Toys", "price": 2999, "desc": "480 piece building set", "sku": "TOYS-071"},
    {"name": "Hot Wheels 10-Car Gift Pack", "cat": "Toys", "price": 999, "desc": "1:64 die-cast car set", "sku": "TOYS-072"},
    {"name": "Barbie Fashionista Doll", "cat": "Toys", "price": 1299, "desc": "Poseable fashion doll", "sku": "TOYS-073"},
    {"name": "Nerf Elite Disruptor Blaster", "cat": "Toys", "price": 1999, "desc": "6-dart revolving foam blaster", "sku": "TOYS-074"},
    {"name": "Funskool Ludo Board Game", "cat": "Toys", "price": 799, "desc": "Classic family board game", "sku": "TOYS-075"},
    {"name": "Hamleys XL Plush Teddy Bear", "cat": "Toys", "price": 1499, "desc": "Super-soft 60cm teddy bear", "sku": "TOYS-076"},
    {"name": "Fisher-Price Baby Walker", "cat": "Toys", "price": 2499, "desc": "Interactive activity walker", "sku": "TOYS-077"},
    {"name": "Pampers Pants L 72-Count", "cat": "Toys", "price": 1299, "desc": "Large pant-style diapers", "sku": "TOYS-078"},
    {"name": "Johnson's Baby Care Kit", "cat": "Toys", "price": 699, "desc": "Shampoo, lotion & soap set", "sku": "TOYS-079"},
    {"name": "Mee Mee Feeding Bottles Set", "cat": "Toys", "price": 349, "desc": "Set of 2 BPA-free bottles", "sku": "TOYS-080"},

    # Automotive (10)
    {"name": "Shell Helix Ultra 5W-40 4L", "cat": "Automotive", "price": 1899, "desc": "Full-synthetic engine oil", "sku": "AUTO-081"},
    {"name": "Bosch S5 12V 65Ah Battery", "cat": "Automotive", "price": 6999, "desc": "Start-stop car battery", "sku": "AUTO-082"},
    {"name": "3M Scratch Remover Polish", "cat": "Automotive", "price": 599, "desc": "Fine scratch removal compound", "sku": "AUTO-083"},
    {"name": "Philips H4 LED Headlight Pair", "cat": "Automotive", "price": 1299, "desc": "Bright LED H4 headlight kit", "sku": "AUTO-084"},
    {"name": "Michelin Flat-Blade Wiper Set", "cat": "Automotive", "price": 799, "desc": "Pair of frameless wipers", "sku": "AUTO-085"},
    {"name": "Turtle Wax Car Shampoo 1L", "cat": "Automotive", "price": 449, "desc": "Wash-and-wax car shampoo", "sku": "AUTO-086"},
    {"name": "Wavex Tyre Shine Spray 500ml", "cat": "Automotive", "price": 299, "desc": "Long-lasting tyre dressing", "sku": "AUTO-087"},
    {"name": "Carmate Aqua Fresh Perfume", "cat": "Automotive", "price": 199, "desc": "Dashboard clip air freshener", "sku": "AUTO-088"},
    {"name": "AutoRight Leather Steering Cover", "cat": "Automotive", "price": 399, "desc": "Universal steering-wheel cover", "sku": "AUTO-089"},
    {"name": "ResQ Portable Tyre Inflator", "cat": "Automotive", "price": 1499, "desc": "12V digital air compressor", "sku": "AUTO-090"},

    # Furniture (10)
    {"name": "IKEA KALLAX Shelf Unit", "cat": "Furniture", "price": 8999, "desc": "4-cube storage shelf", "sku": "FURN-091"},
    {"name": "Pepperfry Solid Wood Coffee Table", "cat": "Furniture", "price": 12999, "desc": "Sheesham wood table with shelf", "sku": "FURN-092"},
    {"name": "Urban Ladder Amsterdam Sofa", "cat": "Furniture", "price": 45999, "desc": "3-seater fabric sofa", "sku": "FURN-093"},
    {"name": "Wakefit Orthopaedic Mattress Queen", "cat": "Furniture", "price": 18999, "desc": "6-inch memory foam mattress", "sku": "FURN-094"},
    {"name": "Godrej Interio Study Chair", "cat": "Furniture", "price": 7499, "desc": "Ergonomic mesh office chair", "sku": "FURN-095"},
    {"name": "IKEA HEMNES Wardrobe 3-Door", "cat": "Furniture", "price": 32999, "desc": "Solid pine wardrobe", "sku": "FURN-096"},
    {"name": "Nilkamal Easy Chair Outdoor", "cat": "Furniture", "price": 1499, "desc": "Weather-resistant plastic chair", "sku": "FURN-097"},
    {"name": "Pepperfry Engineered Wood TV Unit", "cat": "Furniture", "price": 9999, "desc": "Wall-mounted TV console", "sku": "FURN-098"},
    {"name": "Kurlon Glamour 8-inch Mattress", "cat": "Furniture", "price": 14999, "desc": "Bonnell spring queen mattress", "sku": "FURN-099"},
    {"name": "Durian L-Shape Sofa Set", "cat": "Furniture", "price": 54999, "desc": "5-seater sectional leather sofa", "sku": "FURN-100"},
]

# ---------------------------------------------------------------------------
# 5 customers per store
# ---------------------------------------------------------------------------

STORE1_CUSTOMERS = [
    {"email": "priya.sharma@cms.example.com", "full_name": "Priya Sharma", "phone": "9100000011",
     "city": "Mumbai", "state": "Maharashtra", "pincode": "400001"},
    {"email": "rajesh.kumar@cms.example.com", "full_name": "Rajesh Kumar", "phone": "9100000012",
     "city": "Bangalore", "state": "Karnataka", "pincode": "560001"},
    {"email": "anita.verma@cms.example.com", "full_name": "Anita Verma", "phone": "9100000013",
     "city": "Chennai", "state": "Tamil Nadu", "pincode": "600017"},
    {"email": "amit.patel@cms.example.com", "full_name": "Amit Patel", "phone": "9100000014",
     "city": "Ahmedabad", "state": "Gujarat", "pincode": "380015"},
    {"email": "neha.reddy@cms.example.com", "full_name": "Neha Reddy", "phone": "9100000015",
     "city": "Hyderabad", "state": "Telangana", "pincode": "500034"},
]

STORE2_CUSTOMERS = [
    {"email": "ravi.ss@ss.example.com", "full_name": "Ravi Kumar", "phone": "9200000021",
     "city": "Delhi", "state": "Delhi", "pincode": "110001"},
    {"email": "sunita.ss@ss.example.com", "full_name": "Sunita Singh", "phone": "9200000022",
     "city": "Pune", "state": "Maharashtra", "pincode": "411001"},
    {"email": "kiran.ss@ss.example.com", "full_name": "Kiran Bose", "phone": "9200000023",
     "city": "Kolkata", "state": "West Bengal", "pincode": "700001"},
    {"email": "dilip.ss@ss.example.com", "full_name": "Dilip Nair", "phone": "9200000024",
     "city": "Kochi", "state": "Kerala", "pincode": "682001"},
    {"email": "meena.ss@ss.example.com", "full_name": "Meena Joshi", "phone": "9200000025",
     "city": "Jaipur", "state": "Rajasthan", "pincode": "302001"},
]

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[''\"–—]", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def image_url(seed: str, w: int = 400, h: int = 400) -> str:
    return f"https://picsum.photos/seed/{seed}/{w}/{h}"


# ---------------------------------------------------------------------------
# Core seeding functions
# ---------------------------------------------------------------------------

def clear_all_data(db) -> None:
    """Truncate every user-data table in reverse-dependency order."""
    print("  Clearing all existing data …")
    db.execute(text("SET session_replication_role = 'replica'"))
    tables = [
        "order_items", "orders", "payments",
        "wishlist_items", "cart_items",
        "product_images", "product_reviews",
        "user_product_views", "user_sessions",
        "api_keys", "addresses", "users",
        "seller_listings", "products", "categories",
        "stores",
    ]
    for tbl in tables:
        try:
            db.execute(text(f"TRUNCATE TABLE {tbl} CASCADE"))
        except Exception:
            db.rollback()
    db.execute(text("SET session_replication_role = 'origin'"))
    db.commit()
    print("  All data cleared.")


def create_store(db, name: str, slug: str, owner_name: str, owner_email: str,
                 owner_phone: str, city: str, state: str) -> Store:
    store = Store(
        id=uuid.uuid4(),
        external_id=slug.upper() + "-" + str(uuid.uuid4())[:8],
        name=name,
        slug=slug,
        owner_name=owner_name,
        owner_email=owner_email,
        owner_phone=owner_phone,
        address="123 Main Road",
        city=city,
        state=state,
        pincode="600001",
        sync_api_key=secrets.token_urlsafe(32),
        status=StoreStatus.ACTIVE,
        sync_tier=StoreTier.TIER1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(store)
    db.flush()
    return store


def create_admin(db, email: str, full_name: str, phone: str,
                 password: str, store_id) -> User:
    admin = User(
        id=uuid.uuid4(),
        email=email,
        full_name=full_name,
        phone=phone,
        password_hash=get_password_hash(password),
        role=UserRole.ADMIN,
        store_id=store_id,
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(admin)
    db.flush()
    return admin


def create_categories(db, store_id) -> dict:
    """Create one category per unique `cat` value in PRODUCTS."""
    cat_names = sorted(set(p["cat"] for p in PRODUCTS))
    cats = {}
    for name in cat_names:
        cat = Category(
            id=uuid.uuid4(),
            store_id=store_id,
            name=name,
            slug=slugify(name),
            description=f"{name} products",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(cat)
        db.flush()
        cats[name] = cat.id
    return cats


def create_products(db, store_id, categories: dict, sku_prefix: str) -> int:
    """Seed all 100 products for a store; `sku_prefix` differentiates stores."""
    for p in PRODUCTS:
        slug = slugify(p["name"])
        img_seed = slug[:20]  # deterministic picsum seed
        sku = f"{sku_prefix}-{p['sku']}"

        product = Product(
            id=uuid.uuid4(),
            store_id=store_id,
            category_id=categories[p["cat"]],
            sku=sku,
            external_id=sku,
            name=p["name"],
            slug=slug + "-" + sku_prefix.lower(),
            description=p["desc"],
            mrp=float(p["price"]),
            selling_price=float(p["price"]),
            quantity=100,
            images=[image_url(img_seed), image_url(img_seed + "-2")],
            thumbnail=image_url(img_seed, 200, 200),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(product)
    db.flush()
    return len(PRODUCTS)


def create_customers(db, customers_data: list, store_id) -> int:
    count = 0
    for c in customers_data:
        user = User(
            id=uuid.uuid4(),
            email=c["email"],
            full_name=c["full_name"],
            phone=c["phone"],
            password_hash=get_password_hash("Customer@123"),
            role=UserRole.CUSTOMER,
            store_id=store_id,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db.add(user)
        db.flush()

        addr = Address(
            id=uuid.uuid4(),
            user_id=user.id,
            full_name=c["full_name"],
            phone=c["phone"],
            address_line1="1 Sample Street",
            address_line2="",
            city=c["city"],
            state=c["state"],
            pincode=c["pincode"],
            address_type="home",
            is_default=True,
            created_at=datetime.utcnow(),
        )
        db.add(addr)
        db.flush()
        count += 1
        print(f"    Customer: {c['email']}")
    return count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    db = SessionLocal()
    try:
        print("\n" + "=" * 60)
        print(" RESEED: 2-STORE DATABASE SETUP")
        print("=" * 60)

        # ── 0. Clear ────────────────────────────────────────────────
        clear_all_data(db)

        # ── STORE 1: CMS Store ──────────────────────────────────────
        print("\n[Store 1] Creating CMS Store …")
        store1 = create_store(
            db,
            name="CMS Store",
            slug="cms-store",
            owner_name="Surya Chinnathambi",
            owner_email="suryag.chinnathambi@gmail.com",
            owner_phone="9000000001",
            city="Chennai",
            state="Tamil Nadu",
        )
        print(f"  Store ID : {store1.id}")

        admin1 = create_admin(
            db,
            email="suryag.chinnathambi@gmail.com",
            full_name="Surya Chinnathambi",
            phone="9000000001",
            password="Surya@123",
            store_id=store1.id,
        )
        print(f"  Admin    : {admin1.email}")

        cats1 = create_categories(db, store1.id)
        n1 = create_products(db, store1.id, cats1, "S1")
        print(f"  Products : {n1}")

        print("  Customers:")
        nc1 = create_customers(db, STORE1_CUSTOMERS, store1.id)

        db.commit()
        print(f"  Store 1 committed. ({nc1} customers)")

        # ── STORE 2: SS_Stores ──────────────────────────────────────
        print("\n[Store 2] Creating SS_Stores …")
        store2 = create_store(
            db,
            name="SS_Stores",
            slug="ss-stores",
            owner_name="GSTB Admin",
            owner_email="gstb6505@gmail.com",
            owner_phone="9000000002",
            city="Bangalore",
            state="Karnataka",
        )
        print(f"  Store ID : {store2.id}")

        admin2 = create_admin(
            db,
            email="gstb6505@gmail.com",
            full_name="GSTB Admin",
            phone="9000000002",
            password="Surya@123",
            store_id=store2.id,
        )
        print(f"  Admin    : {admin2.email}")

        cats2 = create_categories(db, store2.id)
        n2 = create_products(db, store2.id, cats2, "S2")
        print(f"  Products : {n2}")

        print("  Customers:")
        nc2 = create_customers(db, STORE2_CUSTOMERS, store2.id)

        db.commit()
        print(f"  Store 2 committed. ({nc2} customers)")

        # ── Summary ─────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print(" SEEDING COMPLETE")
        print("=" * 60)
        print(f"""
  Store 1 – CMS Store
    Store ID : {store1.id}
    Admin    : suryag.chinnathambi@gmail.com / Surya@123
    Products : {n1}
    Customers: {nc1}

  Store 2 – SS_Stores
    Store ID : {store2.id}
    Admin    : gstb6505@gmail.com / Surya@123
    Products : {n2}
    Customers: {nc2}

  Customer password (all): Customer@123
""")

    except Exception as exc:
        db.rollback()
        print(f"\n ERROR: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
