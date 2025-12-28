"""
Manual migration script to create marketing tables
Run this once to add marketing features to the database
"""
from app.core.database import engine, Base
import app.models.models  # Import to register all models
import app.models.auth_models
import app.models.marketing_models

def create_marketing_tables():
    """Create all marketing tables in the database"""
    print("Creating all database tables (including marketing)...")
    
    # This will create all tables defined in Base.metadata
    # Existing tables will be skipped
    Base.metadata.create_all(bind=engine)
    
    print(" All tables created successfully!")

if __name__ == "__main__":
    create_marketing_tables()
