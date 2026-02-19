"""
Pytest Configuration
=====================
Shared fixtures for all test modules.

Key design decisions:
  - Each test function gets an isolated DB transaction that rolls back on
    teardown, so tests never pollute each other.
  - Redis calls are mocked via unittest.mock.AsyncMock so tests don't need
    a live Redis instance (CACHE_ENABLED=false is also set in CI env).
  - Both get_db and get_read_db are overridden so endpoints that use
    the read-replica path also hit the test DB.
"""
import pytest
import asyncio
from typing import Generator
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db, get_read_db, Base
from app.core.config import settings
from app.models.models import StoreStatus

# ── Test database ─────────────────────────────────────────────────────────────
# Use a dedicated test DB to avoid touching the dev database.
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    settings.DATABASE_URL.split("/")[-1],
    "test_ecommerce_platform",
)

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    # Disable per-query statement timeout for tests (no PG option needed)
    connect_args={},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _get_test_db():
    """Shared DB override for both get_db and get_read_db."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Session-scoped DB setup ───────────────────────────────────────────────────

@pytest.fixture(scope="session")
def setup_database():
    """Create all tables once per test session; drop them on teardown."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# ── Per-function isolated DB session ─────────────────────────────────────────

@pytest.fixture(scope="function")
def db_session(setup_database) -> Generator:
    """
    Each test gets an isolated DB session wrapped in a transaction that is
    rolled back on teardown — so tests never pollute each other.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# ── Mock Redis ────────────────────────────────────────────────────────────────
# Tests must not require a live Redis connection.
# All redis_client calls return sensible defaults.

@pytest.fixture(autouse=True)
def mock_redis():
    """Auto-use fixture that stubs out all Redis operations."""
    with patch("app.core.redis.redis_client") as mock_rc:
        mock_rc.get = AsyncMock(return_value=None)
        mock_rc.set = AsyncMock(return_value=True)
        mock_rc.get_json = AsyncMock(return_value=None)
        mock_rc.set_json = AsyncMock(return_value=True)
        mock_rc.delete = AsyncMock(return_value=1)
        mock_rc.delete_pattern = AsyncMock(return_value=0)
        mock_rc.increment = AsyncMock(return_value=1)
        mock_rc.exists = AsyncMock(return_value=False)
        mock_rc.ping = AsyncMock(return_value=True)
        yield mock_rc


# ── FastAPI test client ───────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """Test client with both DB dependencies overridden."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_read_db] = lambda: db_session
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ── Domain fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def test_store(db_session):
    """Active store for multi-tenant tests."""
    from app.models.models import Store
    import uuid

    store = Store(
        id=uuid.uuid4(),
        external_id="test-store-001",
        name="Test Store",
        slug="test-store",
        sync_api_key=f"test-api-key-{uuid.uuid4().hex[:8]}",
        status=StoreStatus.ACTIVE,
        is_active=True,
    )
    db_session.add(store)
    db_session.commit()
    db_session.refresh(store)
    return store


@pytest.fixture
def test_user(db_session):
    """Regular customer user."""
    from app.models.auth_models import User, UserRole
    from app.core.security import get_password_hash
    import uuid

    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        phone="1234567890",
        password_hash=get_password_hash("testpassword123"),
        full_name="Test User",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session, test_store):
    """Admin user attached to test_store."""
    from app.models.auth_models import User, UserRole
    from app.core.security import get_password_hash
    import uuid

    admin = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        phone="9876543210",
        password_hash=get_password_hash("adminpassword123"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        store_id=test_store.id,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def auth_token(test_user):
    """Bearer token for test_user (access token only — no JTI needed in tests)."""
    from app.core.security import create_access_token

    return create_access_token(
        data={"sub": str(test_user.id), "role": test_user.role.value}
    )


@pytest.fixture
def admin_token(test_admin):
    """Bearer token for test_admin."""
    from app.core.security import create_access_token

    return create_access_token(
        data={"sub": str(test_admin.id), "role": test_admin.role.value}
    )


@pytest.fixture
def auth_headers(auth_token):
    """Authorization headers for test_user."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_headers(admin_token, test_store):
    """Authorization headers for test_admin, including store context."""
    return {
        "Authorization": f"Bearer {admin_token}",
        "X-Store-ID": str(test_store.id),
    }
