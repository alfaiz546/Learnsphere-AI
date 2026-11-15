import pytest
import os
import uuid
import time
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.core.config import Settings
from app.core.security import create_access_token, decode_token
from app.cache.cache_manager import CacheManager
from app.core.dependencies import get_current_user
from fastapi.security import HTTPAuthorizationCredentials

def test_secret_key_validation_in_production():
    """Verify that Settings validation raises ValueError in production for weak or default keys."""
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        # Default/insecure key should fail
        with pytest.raises(ValueError, match="CRITICAL SECURITY ERROR"):
            Settings(
                SECRET_KEY="dev-secret-key-change-in-production-use-32-chars-minimum",
                ENVIRONMENT="production"
            )

        # Too short key should fail
        with pytest.raises(ValueError, match="CRITICAL SECURITY ERROR"):
            Settings(
                SECRET_KEY="short_key_123",
                ENVIRONMENT="production"
            )

        # 64-char strong key should succeed
        valid_settings = Settings(
            SECRET_KEY="a" * 64,
            ENVIRONMENT="production"
        )
        assert valid_settings.SECRET_KEY == "a" * 64

def test_redis_blacklisting_behavior_and_ttl():
    """Verify blacklist_token sets appropriate TTL and checks existence correctly."""
    mock_redis = MagicMock()
    cm = CacheManager()

    with patch("app.cache.cache_manager.get_redis_client", return_value=mock_redis):
        # Test blacklist with 300s TTL
        token = "test_jwt_token_sample"
        success = cm.blacklist_token(token, 300)
        assert success is True
        mock_redis.setex.assert_called_once_with("ls:blacklisted_token:test_jwt_token_sample", 300, "1")

        # Test blacklist check returns True
        mock_redis.exists.return_value = 1
        assert cm.is_token_blacklisted(token) is True

        # Test blacklist check returns False
        mock_redis.exists.return_value = 0
        assert cm.is_token_blacklisted(token) is False

def test_redis_blacklisting_graceful_handling_and_fail_policy():
    """Verify behavior when Redis client is unreachable."""
    cm = CacheManager()
    with patch("app.cache.cache_manager.get_redis_client", return_value=None):
        # When Redis is offline, is_token_blacklisted returns None (unknown)
        status = cm.is_token_blacklisted("sample_token")
        assert status is None

        # In permissive mode (AUTH_REQUIRE_REDIS_BLACKLIST=False and dev env), does not block
        # In strict mode, get_current_user raises 503
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dummy_token")
        with patch("app.core.dependencies.cache.is_token_blacklisted", return_value=None):
            with patch("app.core.config.settings.AUTH_REQUIRE_REDIS_BLACKLIST", True):
                with pytest.raises(HTTPException) as exc_info:
                    get_current_user(credentials=credentials, db=MagicMock())
                assert exc_info.value.status_code == 503
                assert "Authentication service temporarily unavailable" in exc_info.value.detail

def test_logout_revokes_token_and_rejects_subsequent_request(client, db_session):
    """Test full login -> logout -> reuse of the same token fails."""
    # 1. Register a test user
    test_email = f"revoke_{uuid.uuid4().hex[:6]}@example.com"
    reg = client.post("/api/auth/register", json={
        "email": test_email,
        "username": f"user_{uuid.uuid4().hex[:6]}",
        "password": "Password123!"
    })
    assert reg.status_code == 201
    token = reg.cookies.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Access protected endpoint succeeds
    profile_res = client.get("/api/student/profile", headers=headers)
    assert profile_res.status_code == 200

    # 3. Mock Redis cache for token blacklist in test environment
    blacklisted_set = set()
    def mock_blacklist(t, ttl):
        blacklisted_set.add(t)
        return True
    def mock_is_blacklisted(t):
        return t in blacklisted_set

    with patch("app.services.auth_service.cache.blacklist_token", side_effect=mock_blacklist):
        with patch("app.core.dependencies.cache.is_token_blacklisted", side_effect=mock_is_blacklisted):
            # 4. Logout
            logout_res = client.post("/api/auth/logout", headers=headers)
            assert logout_res.status_code == 200
            assert token in blacklisted_set

            # 5. Subsequent request with the same token MUST be rejected with 401
            reused_res = client.get("/api/student/profile", headers=headers)
            assert reused_res.status_code == 401
            assert "revoked" in reused_res.json()["detail"].lower()


@pytest.mark.parametrize("env_name", ["staging", "production"])
def test_redis_outage_fail_closed_in_staging_and_production(env_name):
    """Verify that both staging and production strictly fail closed (503) when Redis is unreachable."""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_dummy_token")

    with patch("app.core.dependencies.cache.is_token_blacklisted", return_value=None):
        with patch("app.core.config.settings.ENVIRONMENT", env_name):
            with patch("app.core.config.settings.AUTH_REQUIRE_REDIS_BLACKLIST", False):
                with pytest.raises(HTTPException) as exc_info:
                    get_current_user(credentials=credentials, db=MagicMock())
                assert exc_info.value.status_code == 503
                assert "Authentication service temporarily unavailable" in exc_info.value.detail


def test_redis_outage_fail_closed_when_auth_require_redis_blacklist_is_true():
    """Verify that any environment with AUTH_REQUIRE_REDIS_BLACKLIST=True fails closed (503)."""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_dummy_token")

    with patch("app.core.dependencies.cache.is_token_blacklisted", return_value=None):
        with patch("app.core.config.settings.ENVIRONMENT", "development"):
            with patch("app.core.config.settings.AUTH_REQUIRE_REDIS_BLACKLIST", True):
                with pytest.raises(HTTPException) as exc_info:
                    get_current_user(credentials=credentials, db=MagicMock())
                assert exc_info.value.status_code == 503
                assert "Security verification degraded" in exc_info.value.detail


@pytest.mark.parametrize("env_name", ["development", "staging", "production"])
def test_redis_available_token_revocation_behavior(env_name):
    """Verify normal Redis availability: revoked token returns 401, non-revoked proceeds."""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_dummy_token")

    # 1. When Redis confirms token is blacklisted -> 401 Unauthorized
    with patch("app.core.dependencies.cache.is_token_blacklisted", return_value=True):
        with patch("app.core.config.settings.ENVIRONMENT", env_name):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(credentials=credentials, db=MagicMock())
            assert exc_info.value.status_code == 401
            assert "revoked" in exc_info.value.detail.lower()

    # 2. When Redis confirms token is NOT blacklisted -> blacklist check passes, moves to token decode
    with patch("app.core.dependencies.cache.is_token_blacklisted", return_value=False):
        with patch("app.core.dependencies.decode_token", return_value=None):
            with patch("app.core.config.settings.ENVIRONMENT", env_name):
                with pytest.raises(HTTPException) as exc_info:
                    get_current_user(credentials=credentials, db=MagicMock())
                # Should reach token decode stage (401 invalid/expired token), NOT 503
                assert exc_info.value.status_code == 401
                assert "invalid or expired token" in exc_info.value.detail.lower()

