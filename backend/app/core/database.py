"""
Database Configuration and Session Management
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
    echo=False,  # Set to True for SQL query logging
)

# Create read replica engines if configured
read_engines = []
if settings.DATABASE_READ_REPLICAS:
    for replica_url in settings.DATABASE_READ_REPLICAS:
        read_engine = create_engine(
            replica_url,
            poolclass=QueuePool,
            pool_size=settings.DATABASE_POOL_SIZE // 2,
            max_overflow=settings.DATABASE_MAX_OVERFLOW // 2,
            pool_pre_ping=True,
            echo=False,
        )
        read_engines.append(read_engine)
    logger.info(f"Configured {len(read_engines)} read replicas")

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Database session dependency
def get_db():
    """
    Dependency for getting database session
    Automatically closes session after request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_read_db():
    """
    Get read-only database session from replica
    Falls back to primary if no replicas configured
    """
    if read_engines:
        # Simple round-robin selection
        import random
        read_engine = random.choice(read_engines)
        ReadSession = sessionmaker(autocommit=False, autoflush=False, bind=read_engine)
        db = ReadSession()
    else:
        db = SessionLocal()
    
    try:
        yield db
    finally:
        db.close()


# Event listeners for connection pool monitoring
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log new database connections"""
    logger.debug("Database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkout from pool"""
    logger.debug("Connection checked out from pool")


# Utility functions
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


def drop_db():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
    logger.warning("Database tables dropped")
