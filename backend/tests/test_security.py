"""
Security & Authentication Tests (Sprint 3 features)

Covers:
  - Token refresh rotation
  - Logout / token blacklisting
  - Account lockout after repeated failures
  - core security helper functions
"""
import pytest
from fastapi import status
from unittest.mock import AsyncMock, patch, MagicMock


# ── Token helpers (pure unit tests) ──────────────────────────────────────────

class TestTokenCreation:
    """Unit tests for JWT creation helpers — no DB or HTTP needed."""

    @pytest.mark.unit
    def test_access_token_contains_jti(self):
        """Each access token must contain a 'jti' claim for blacklisting."""
        from app.core.security import create_access_token
        from jose import jwt
        from app.core.config import settings

        token = create_access_token({"sub": "test-user-id", "role": "customer"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "jti" in payload
        assert len(payload["jti"]) > 0

    @pytest.mark.unit
    def test_refresh_token_returns_tuple(self):
        """create_refresh_token must return (token_str, jti_str)."""
        from app.core.security import create_refresh_token

        result = create_refresh_token({"sub": "test-user-id", "role": "customer"})
        assert isinstance(result, tuple)
        assert len(result) == 2
        token, jti = result
        assert isinstance(token, str)
        assert isinstance(jti, str)

    @pytest.mark.unit
    def test_create_token_pair(self):
        """create_token_pair returns two distinct non-empty tokens."""
        from app.core.security import create_token_pair

        access, refresh = create_token_pair("user-123", "customer")
        assert access
        assert refresh
        assert access != refresh

    @pytest.mark.unit
    def test_verify_password(self):
        """Password hashing round-trip."""
        from app.core.security import get_password_hash, verify_password

        plain = "SecurePass!123"
        hashed = get_password_hash(plain)
        assert verify_password(plain, hashed) is True
        assert verify_password("WrongPass", hashed) is False

    @pytest.mark.unit
    def test_hash_api_key_is_deterministic(self):
        """Same raw key always produces the same hash."""
        from app.core.security import hash_api_key

        raw = "sk_live_abc123xyz"
        assert hash_api_key(raw) == hash_api_key(raw)

    @pytest.mark.unit
    def test_generate_api_key_prefix(self):
        """Live keys start with 'sk_live_', test keys with 'sk_test_'."""
        from app.core.security import generate_api_key

        raw_live, _ = generate_api_key(is_test=False)
        raw_test, _ = generate_api_key(is_test=True)
        assert raw_live.startswith("ec_live_")
        assert raw_test.startswith("ec_test_")

    @pytest.mark.unit
    def test_generate_api_key_hash_matches(self):
        """The hash returned by generate_api_key matches hash_api_key(raw)."""
        from app.core.security import generate_api_key, hash_api_key

        raw, key_hash = generate_api_key()
        assert hash_api_key(raw) == key_hash

    @pytest.mark.unit
    def test_decode_token_invalid_raises(self):
        """Decoding a tampered token raises 401."""
        from app.core.security import decode_token
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            decode_token("this.is.not.a.valid.jwt")
        assert exc_info.value.status_code == 401


# ── Token blacklisting (mocked Redis) ────────────────────────────────────────

class TestTokenBlacklisting:
    """Tests for the Redis-backed token blacklist."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_blacklist_token_calls_redis_setex(self):
        """blacklist_token writes the JTI to Redis with a TTL."""
        from datetime import datetime, timedelta
        from app.core import security as sec_module

        mock_redis = MagicMock()
        mock_redis.setex = AsyncMock(return_value=True)

        future = datetime.utcnow() + timedelta(minutes=30)

        with patch("app.core.redis.redis_client", mock_redis):
            await sec_module.blacklist_token("test-jti-123", future)

        mock_redis.setex.assert_called_once()
        call_kwargs = mock_redis.setex.call_args
        # Key should contain the JTI
        assert "test-jti-123" in call_kwargs[0][0]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_is_token_blacklisted_true(self):
        """is_token_blacklisted returns True when Redis reports the key exists."""
        from app.core import security as sec_module

        mock_redis = MagicMock()
        mock_redis.exists = AsyncMock(return_value=True)

        with patch("app.core.redis.redis_client", mock_redis):
            result = await sec_module.is_token_blacklisted("blacklisted-jti")

        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_is_token_blacklisted_false(self):
        """is_token_blacklisted returns False for an unknown JTI."""
        from app.core import security as sec_module

        mock_redis = MagicMock()
        mock_redis.exists = AsyncMock(return_value=False)

        with patch("app.core.redis.redis_client", mock_redis):
            result = await sec_module.is_token_blacklisted("unknown-jti")

        assert result is False


# ── Account lockout (mocked Redis) ───────────────────────────────────────────

class TestAccountLockout:
    """Tests for the Redis-backed login failure / lockout logic."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_account_locked_raises_when_locked(self):
        """check_account_locked raises 429 when the lock key exists."""
        from fastapi import HTTPException
        from app.core import security as sec_module

        mock_redis = MagicMock()
        mock_redis.exists = AsyncMock(return_value=True)
        mock_redis.ttl = AsyncMock(return_value=300)  # 5 min remaining

        with patch("app.core.redis.redis_client", mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                await sec_module.check_account_locked("locked@example.com")

        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_account_not_locked_passes(self):
        """check_account_locked does not raise when account is not locked."""
        from app.core import security as sec_module

        mock_redis = MagicMock()
        mock_redis.exists = AsyncMock(return_value=False)

        with patch("app.core.redis.redis_client", mock_redis):
            # Should not raise
            await sec_module.check_account_locked("ok@example.com")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_record_failed_login_increments_counter(self):
        """record_failed_login calls Redis increment."""
        from app.core import security as sec_module

        mock_redis = MagicMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock(return_value=True)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)

        with patch("app.core.redis.redis_client", mock_redis):
            await sec_module.record_failed_login("fail@example.com")

        mock_redis.incr.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_clear_failed_logins_deletes_keys(self):
        """clear_failed_logins removes both the counter and lock keys."""
        from app.core import security as sec_module

        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock(return_value=2)

        with patch("app.core.redis.redis_client", mock_redis):
            await sec_module.clear_failed_logins("success@example.com")

        mock_redis.delete.assert_called_once()


# ── Auth HTTP endpoints ───────────────────────────────────────────────────────

class TestRefreshTokenEndpoint:
    """HTTP-level tests for POST /api/v1/auth/refresh."""

    def test_refresh_with_invalid_token_fails(self, client, test_store):
        """Submitting a garbage refresh token returns 401."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not.a.real.token"},
            headers={"X-Store-ID": str(test_store.id)},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_with_access_token_fails(self, client, auth_token, test_store):
        """Using an access token as a refresh token must be rejected."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": auth_token},
            headers={"X-Store-ID": str(test_store.id)},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogoutEndpoint:
    """HTTP-level tests for POST /api/v1/auth/logout."""

    def test_logout_requires_auth(self, client, test_store):
        """Logout without a token returns 401 or 403."""
        response = client.post(
            "/api/v1/auth/logout",
            headers={"X-Store-ID": str(test_store.id)},
        )
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_logout_with_valid_token(self, client, auth_headers, test_store):
        """A valid token can be successfully invalidated."""
        response = client.post(
            "/api/v1/auth/logout",
            headers={**auth_headers, "X-Store-ID": str(test_store.id)},
        )
        # 200 OK or 204 No Content
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
