"""Create test admin user"""
from app.core.database import SessionLocal
from app.models.auth_models import User, UserRole
from app.models.models import Store
from app.core.security import get_password_hash
from uuid import uuid4

db = SessionLocal()

try:
    # Get first store
    store = db.query(Store).first()
    
    if not store:
        print("No store found. Please run init_db.py first")
        exit(1)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == 'admin@test.com').first()
    
    if existing_user:
        print("User admin@test.com already exists")
        print("Email: admin@test.com")
        print("Password: admin123")
    else:
        # Create admin user
        user = User(
            id=uuid4(),
            email='admin@test.com',
            password_hash=get_password_hash('admin123'),
            full_name='Admin User',
            role=UserRole.ADMIN,
            is_active=True,
            store_id=store.id
        )
        db.add(user)
        db.commit()
        print("✓ Admin user created successfully!")
        print("Email: admin@test.com")
        print("Password: admin123")
        print(f"Store: {store.name}")
        
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
