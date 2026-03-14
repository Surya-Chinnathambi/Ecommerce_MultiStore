"""
Database Configuration and Session Management
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging
import threading

from app.core.config import settings

logger = logging.getLogger(__name__)

# Round-robin counter for read replica selection (avoids random skew)
_replica_counter = [0]
_replica_lock = threading.Lock()

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,          # Verify connections before using
    pool_recycle=settings.DB_POOL_RECYCLE,   # Recycle to avoid stale / timed-out connections
    pool_timeout=settings.DB_POOL_TIMEOUT,   # Raise if pool exhausted instead of hanging
    connect_args={},
    echo=False,                  # Set to True for SQL query debugging
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
class Base(DeclarativeBase):
    pass


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


@contextmanager
def get_db_session():
    """
    Sync context-manager for use in Celery tasks, scripts, and one-off jobs.
    Commits on success, rolls back on any exception, always closes.

    Usage::

        with get_db_session() as db:
            orders = db.query(Order).filter(...).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_read_db():
    """
    Get a read-only database session from a replica.
    Falls back to primary if no replicas are configured.
    Uses strict round-robin (not random) for even load distribution.
    """
    if read_engines:
        with _replica_lock:
            idx = _replica_counter[0] % len(read_engines)
            _replica_counter[0] = (_replica_counter[0] + 1) % (len(read_engines) * 10_000)
        read_engine = read_engines[idx]
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
    """Configure connection-level safety guards and log new DB sessions."""
    logger.debug("Database connection established")
    if settings.DB_STATEMENT_TIMEOUT_MS <= 0:
        return

    # Postgres: ensure runaway queries are terminated so worker throughput
    # remains healthy under burst traffic.
    try:
        timeout_ms = int(settings.DB_STATEMENT_TIMEOUT_MS)
        cursor = dbapi_conn.cursor()
        cursor.execute(f"SET statement_timeout = {timeout_ms}")
        cursor.close()
    except Exception:
        try:
            dbapi_conn.rollback()
        except Exception:
            pass
        # Ignore for non-Postgres drivers or restricted permissions.
        logger.debug("Skipping DB statement timeout setup", exc_info=True)


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
