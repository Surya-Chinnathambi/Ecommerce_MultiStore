"""
Security — JWT authentication, token blacklisting, account lockout, API key auth
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import hashlib
import secrets
import uuid as _uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.orm import Session
import logging

from app.core.config import settings
from app.core.database import get_db
from app.models.auth_models import User, UserRole, APIKey

logger = logging.getLogger(__name__)

# ── Password hashing ──────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── HTTP bearer scheme ────────────────────────────────────────────────────────
security = HTTPBearer(auto_error=False)

# ── API Key header scheme ─────────────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# ── Token type constants ──────────────────────────────────────────────────────
ACCESS_TOKEN_TYPE  = "access"
REFRESH_TOKEN_TYPE = "refresh"

# ── Account lockout policy ────────────────────────────────────────────────────
MAX_FAILED_ATTEMPTS       = 5
LOCKOUT_DURATION_SECONDS  = 15 * 60   # 15 minutes
LOCKOUT_COUNTER_TTL       = 20 * 60   # failure counter TTL

# ── API key full-access scope ─────────────────────────────────────────────────
SCOPE_FULL_ACCESS = "*"


# ──────────────────────────────────────────────────────────────────────────────
# Password helpers
# ──────────────────────────────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ──────────────────────────────────────────────────────────────────────────────
# JWT — create / decode
# ──────────────────────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a short-lived JWT access token with a unique JTI for blacklisting."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": ACCESS_TOKEN_TYPE,
        "jti": str(_uuid.uuid4()),
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> Tuple[str, str]:
    """
    Create a long-lived refresh token.
    Returns (encoded_token, jti) — callers store the jti for rotation tracking.
    """
    jti = str(_uuid.uuid4())
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": REFRESH_TOKEN_TYPE,
        "jti": jti,
    })
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def create_token_pair(user_id: str, role: str, extra: dict | None = None) -> Tuple[str, str]:
    """Return (access_token, refresh_token)."""
    data = {"sub": user_id, "role": role, **(extra or {})}
    access_token = create_access_token(data)
    refresh_token, _ = create_refresh_token(data)
    return access_token, refresh_token


def decode_token(token: str) -> dict:
    """Decode and validate a JWT, raising 401 on any failure."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_refresh_token(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return payload


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(32)


# ──────────────────────────────────────────────────────────────────────────────
# Token blacklisting (Redis)
# ──────────────────────────────────────────────────────────────────────────────

def _blacklist_key(jti: str) -> str:
    return f"token:blacklist:{jti}"


async def blacklist_token(jti: str, expires_at: datetime) -> None:
    """Write JTI to Redis blacklist with TTL = remaining token lifetime."""
    from app.core.redis import redis_client
    ttl = int((expires_at - datetime.utcnow()).total_seconds())
    if ttl > 0:
        await redis_client.setex(_blacklist_key(jti), ttl, "1")


async def is_token_blacklisted(jti: str) -> bool:
    from app.core.redis import redis_client
    return await redis_client.exists(_blacklist_key(jti)) > 0


# ──────────────────────────────────────────────────────────────────────────────
# Account lockout (Redis)
# ──────────────────────────────────────────────────────────────────────────────

async def check_account_locked(email: str) -> None:
    """Raise 429 if the account is locked after too many failed attempts."""
    from app.core.redis import redis_client
    key = f"login:locked:{email.lower()}"
    if await redis_client.exists(key):
        ttl = await redis_client.ttl(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked. Try again in {ttl} seconds.",
            headers={"Retry-After": str(ttl)},
        )


async def record_failed_login(email: str) -> None:
    """Increment failure counter; lock account after MAX_FAILED_ATTEMPTS."""
    from app.core.redis import redis_client
    fails_key = f"login:fails:{email.lower()}"
    count = await redis_client.incr(fails_key)
    await redis_client.expire(fails_key, LOCKOUT_COUNTER_TTL)
    if count >= MAX_FAILED_ATTEMPTS:
        await redis_client.setex(f"login:locked:{email.lower()}", LOCKOUT_DURATION_SECONDS, "1")
        await redis_client.delete(fails_key)
        logger.warning("Account locked", extra={"email": email})


async def clear_failed_logins(email: str) -> None:
    from app.core.redis import redis_client
    await redis_client.delete(f"login:fails:{email.lower()}")


# ──────────────────────────────────────────────────────────────────────────────
# API Key helpers
# ──────────────────────────────────────────────────────────────────────────────

def generate_api_key(is_test: bool = False) -> Tuple[str, str]:
    """
    Returns (raw_key, key_hash).
    raw_key shown once; key_hash stored in DB.
    Format: ec_live_<64-hex>  or  ec_test_<64-hex>
    """
    prefix     = "ec_test_" if is_test else "ec_live_"
    raw_key    = prefix + secrets.token_hex(32)
    key_hash   = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_hash


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI dependencies
# ──────────────────────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate Bearer JWT, check blacklist, return User.
    Raises 401 if missing, invalid, expired, or blacklisted.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def get_current_customer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer access required.")
    return current_user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return current_user


async def get_current_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required.")
    return current_user


async def get_api_key_record(
    raw_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db),
) -> APIKey:
    """
    Validate X-API-Key header, bump usage counters, return APIKey record.
    Use on endpoints that accept machine-to-machine authentication.
    """
    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required (X-API-Key header)",
        )

    key_hash = hash_api_key(raw_key)
    api_key = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True,
    ).first()

    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    if api_key.is_expired():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key expired")

    try:
        api_key.last_used_at  = datetime.utcnow()
        api_key.request_count += 1
        db.commit()
    except Exception:
        db.rollback()

    return api_key


def require_scope(scope: str):
    """
    Dependency factory that checks an API key has the required scope.
    Usage:  api_key: APIKey = Depends(require_scope("sync:write"))
    """
    async def _check(api_key: APIKey = Depends(get_api_key_record)) -> APIKey:
        if SCOPE_FULL_ACCESS not in api_key.scopes and scope not in api_key.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key missing required scope: {scope}",
            )
        return api_key
    return _check


def verify_admin_store_access(user: User, store_id: str) -> bool:
    if user.role == UserRole.SUPER_ADMIN:
        return True
    return user.role == UserRole.ADMIN and str(user.store_id) == store_id



