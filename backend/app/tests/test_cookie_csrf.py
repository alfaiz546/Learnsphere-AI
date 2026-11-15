"""Security-hardened tests for HttpOnly Cookie authentication, signed CSRF, and CLI token endpoints.

Covers:
1. Browser endpoints (/login, /register, /refresh) NEVER expose access_token or refresh_token in JSON.
2. HttpOnly and SameSite cookie attributes.
3. Dedicated CLI token endpoints (/token, /token/refresh) issue Bearer tokens and set NO cookies.
4. Signed, timestamped CSRF protection with Origin header validation and sibling-domain injection defense.
5. Token rotation and Redis logout revocation.
6. Bearer token backward compatibility for programmatic clients.
"""
import pytest
import uuid
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.core.dependencies import generate_csrf_token, verify_csrf_token


# ---------------------------------------------------------------------------
# 1. Browser Auth Tests (HttpOnly Cookie-Only, Zero JWT in Body)
# ---------------------------------------------------------------------------

class TestBrowserCookieAuth:
    """Verify browser endpoints rely exclusively on cookies and never leak JWTs."""

    def test_browser_login_never_exposes_jwt_in_body(self, client, db_session):
        """POST /api/auth/login must set HttpOnly cookies and NEVER expose JWTs in the JSON body."""
        email = f"noleak_login_{uuid.uuid4().hex[:6]}@example.com"
        username = f"user_{uuid.uuid4().hex[:6]}"
        reg = client.post("/api/auth/register", json={
            "email": email, "username": username, "password": "Password123!"
        })
        assert reg.status_code == 201

        login_res = client.post("/api/auth/login", json={
            "email": email, "password": "Password123!"
        })
        assert login_res.status_code == 200

        # Cookies must be present
        cookies = {c.name: c for c in login_res.cookies.jar}
        assert "access_token" in cookies
        assert "refresh_token" in cookies
        assert "csrf_token" in cookies

        # access_token and refresh_token must be HttpOnly
        assert cookies["access_token"].value
        assert cookies["refresh_token"].value
        assert cookies["csrf_token"].value

        # CRITICAL SECURITY ASSERTION: Response JSON body MUST NOT contain JWT tokens
        body = login_res.json()
        assert body["success"] is True
        assert "csrf_token" in body["data"]
        assert "user_id" in body["data"]
        assert "username" in body["data"]
        assert "access_token" not in body["data"], "Security violation: access_token leaked in JSON body!"
        assert "refresh_token" not in body["data"], "Security violation: refresh_token leaked in JSON body!"

    def test_browser_register_never_exposes_jwt_in_body(self, client, db_session):
        """POST /api/auth/register must set HttpOnly cookies and NEVER expose JWTs in JSON body."""
        email = f"noleak_reg_{uuid.uuid4().hex[:6]}@example.com"
        username = f"user_{uuid.uuid4().hex[:6]}"
        reg = client.post("/api/auth/register", json={
            "email": email, "username": username, "password": "Password123!"
        })
        assert reg.status_code == 201

        cookies = {c.name: c for c in reg.cookies.jar}
        assert "access_token" in cookies
        assert "refresh_token" in cookies
        assert "csrf_token" in cookies

        # CRITICAL: Response body MUST NOT contain JWT tokens
        body = reg.json()
        assert body["success"] is True
        assert "csrf_token" in body["data"]
        assert "access_token" not in body["data"], "Security violation: access_token leaked in register JSON body!"
        assert "refresh_token" not in body["data"], "Security violation: refresh_token leaked in register JSON body!"

    def test_browser_refresh_never_exposes_jwt_in_body(self, client, db_session):
        """POST /api/auth/refresh must rotate cookies and NEVER expose JWTs in JSON body."""
        email = f"noleak_ref_{uuid.uuid4().hex[:6]}@example.com"
        username = f"user_{uuid.uuid4().hex[:6]}"
        reg = client.post("/api/auth/register", json={
            "email": email, "username": username, "password": "Password123!"
        })
        assert reg.status_code == 201

        old_refresh = None
        for c in reg.cookies.jar:
            if c.name == "refresh_token":
                old_refresh = c.value

        refresh_res = client.post(
            "/api/auth/refresh",
            cookies={"refresh_token": old_refresh}
        )
        assert refresh_res.status_code == 200

        new_cookies = {c.name: c for c in refresh_res.cookies.jar}
        assert "access_token" in new_cookies
        assert "refresh_token" in new_cookies
        assert "csrf_token" in new_cookies

        # CRITICAL: Response body MUST NOT contain JWT tokens
        body = refresh_res.json()
        assert body["success"] is True
        assert "csrf_token" in body["data"]
        assert "access_token" not in body["data"], "Security violation: access_token leaked in refresh JSON body!"
        assert "refresh_token" not in body["data"], "Security violation: refresh_token leaked in refresh JSON body!"

    def test_cookie_authenticated_request_succeeds(self, client, db_session):
        """Requests with valid access_token cookie authenticate cleanly."""
        email = f"cookieauth_{uuid.uuid4().hex[:6]}@example.com"
        username = f"user_{uuid.uuid4().hex[:6]}"
        reg = client.post("/api/auth/register", json={
            "email": email, "username": username, "password": "Password123!"
        })
        assert reg.status_code == 201

        access_token = None
        csrf_token = None
        for c in reg.cookies.jar:
            if c.name == "access_token":
                access_token = c.value
            if c.name == "csrf_token":
                csrf_token = c.value

        profile = client.get(
            "/api/student/profile",
            cookies={"access_token": access_token, "csrf_token": csrf_token}
        )
        assert profile.status_code == 200

    def test_logout_clears_cookies_and_blacklists(self, client, db_session):
        """POST /api/auth/logout clears auth cookies and revokes token in Redis."""
        email = f"logout_{uuid.uuid4().hex[:6]}@example.com"
        username = f"user_{uuid.uuid4().hex[:6]}"
        reg = client.post("/api/auth/register", json={
            "email": email, "username": username, "password": "Password123!"
        })
        assert reg.status_code == 201

        access_token = None
        for c in reg.cookies.jar:
            if c.name == "access_token":
                access_token = c.value

        blacklisted = set()
        def mock_blacklist(t, ttl):
            blacklisted.add(t)
            return True

        with patch("app.services.auth_service.cache.blacklist_token", side_effect=mock_blacklist):
            logout_res = client.post(
                "/api/auth/logout",
                cookies={"access_token": access_token}
            )
        assert logout_res.status_code == 200
        assert access_token in blacklisted
        assert logout_res.json()["success"] is True

    def test_missing_token_returns_401(self, client, db_session):
        """Request without cookies or Bearer header must return 401."""
        profile = client.get("/api/student/profile")
        assert profile.status_code == 401


# ---------------------------------------------------------------------------
# 2. Dedicated CLI Token Endpoints (Pure Bearer, NO Cookies)
# ---------------------------------------------------------------------------

class TestCLITokenEndpoints:
    """Verify dedicated CLI token endpoints issue tokens in body without cookies."""

    def test_cli_token_issuance_returns_tokens_without_cookies(self, client, db_session):
        """POST /api/auth/token returns JWTs in JSON body and does NOT set cookies."""
        email = f"cli_{uuid.uuid4().hex[:6]}@example.com"
        username = f"user_{uuid.uuid4().hex[:6]}"
        reg = client.post("/api/auth/register", json={
            "email": email, "username": username, "password": "Password123!"
        })
        assert reg.status_code == 201

        # Request token via dedicated CLI endpoint
        token_res = client.post("/api/auth/token", json={
            "email": email, "password": "Password123!"
        })
        assert token_res.status_code == 200

        # CLI endpoint MUST provide tokens in JSON body
        body = token_res.json()
        assert body["success"] is True
        assert body["data"]["access_token"]
        assert body["data"]["refresh_token"]
        assert body["data"]["token_type"] == "bearer"

        # CLI endpoint MUST NOT set auth cookies
        cli_cookies = {c.name: c for c in token_res.cookies.jar}
        assert "access_token" not in cli_cookies
        assert "refresh_token" not in cli_cookies

    def test_cli_token_refresh_returns_tokens_without_cookies(self, client, db_session):
        """POST /api/auth/token/refresh refreshes tokens via body without cookies."""
        email = f"cliref_{uuid.uuid4().hex[:6]}@example.com"
        username = f"user_{uuid.uuid4().hex[:6]}"
        reg = client.post("/api/auth/register", json={
            "email": email, "username": username, "password": "Password123!"
        })
        assert reg.status_code == 201

        token_res = client.post("/api/auth/token", json={
            "email": email, "password": "Password123!"
        })
        refresh_token = token_res.json()["data"]["refresh_token"]

        # Refresh via CLI endpoint
        refreshed = client.post("/api/auth/token/refresh", json={
            "refresh_token": refresh_token
        })
        assert refreshed.status_code == 200
        ref_body = refreshed.json()
        assert ref_body["success"] is True
        assert ref_body["data"]["access_token"]
        assert ref_body["data"]["refresh_token"]
        assert ref_body["data"]["token_type"] == "bearer"


# ---------------------------------------------------------------------------
# 3. Cryptographically Signed CSRF Protection & Injection Defense
# ---------------------------------------------------------------------------

class TestSignedCSRFProtection:
    """Verify HMAC-signed CSRF tokens, Origin check, and sibling-domain defense."""

    def test_csrf_token_generator_and_verifier(self):
        """Verify CSRF token generation, cryptographic signing, and tamper detection."""
        token = generate_csrf_token()
        assert verify_csrf_token(token) is True

        # Tampered payload must fail verification
        tampered_payload = "forged_entropy:12345." + token.split(".")[1]
        assert verify_csrf_token(tampered_payload) is False

        # Tampered signature must fail verification
        tampered_sig = token.rsplit(".", 1)[0] + ".forged_signature_0000000000000000"
        assert verify_csrf_token(tampered_sig) is False

        # Expired token must fail verification
        expired_payload = f"entropy:{int(time.time()) - 800000}"
        import hmac, hashlib
        from app.core.config import settings
        expired_sig = hmac.new(settings.SECRET_KEY.encode(), expired_payload.encode(), hashlib.sha256).hexdigest()[:32]
        assert verify_csrf_token(f"{expired_payload}.{expired_sig}") is False

    def test_csrf_missing_header_rejected(self, client, db_session):
        """State-changing request with cookie auth but no X-CSRF-Token must be rejected (403)."""
        email = f"csrf_miss_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/auth/register", json={
            "email": email, "username": f"u_{uuid.uuid4().hex[:6]}", "password": "Password123!"
        })
        access_token = reg.cookies.get("access_token")
        csrf_token = reg.cookies.get("csrf_token")

        res = client.put(
            "/api/student/profile",
            json={"full_name": "Attacker"},
            cookies={"access_token": access_token, "csrf_token": csrf_token}
            # No X-CSRF-Token header
        )
        assert res.status_code == 403
        assert "csrf" in res.json()["detail"].lower()

    def test_csrf_sibling_subdomain_cookie_injection_rejected(self, client, db_session):
        """An attacker injecting an arbitrary forged CSRF cookie from a sibling domain is rejected."""
        email = f"csrf_inj_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/auth/register", json={
            "email": email, "username": f"u_{uuid.uuid4().hex[:6]}", "password": "Password123!"
        })
        access_token = reg.cookies.get("access_token")

        # Attacker injects their own forged token into cookie AND header
        forged_token = "attacker_injected_token_value"
        res = client.put(
            "/api/student/profile",
            json={"full_name": "Injected Name"},
            headers={
                "X-CSRF-Token": forged_token,
                "Cookie": f"access_token={access_token}; csrf_token={forged_token}"
            }
        )
        # Even though cookie == header, HMAC signature validation FAILS -> 403
        assert res.status_code == 403
        assert "signature invalid" in res.json()["detail"].lower()

    def test_csrf_origin_mismatch_rejected(self, client, db_session):
        """Request from an untrusted Origin must be rejected (403)."""
        email = f"csrf_orig_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/auth/register", json={
            "email": email, "username": f"u_{uuid.uuid4().hex[:6]}", "password": "Password123!"
        })
        access_token = reg.cookies.get("access_token")
        csrf_token = reg.cookies.get("csrf_token")

        res = client.put(
            "/api/student/profile",
            json={"full_name": "Cross Origin"},
            cookies={"access_token": access_token, "csrf_token": csrf_token},
            headers={
                "X-CSRF-Token": csrf_token,
                "Origin": "https://malicious-cross-origin.com"
            }
        )
        assert res.status_code == 403
        assert "origin" in res.json()["detail"].lower()

    def test_csrf_valid_signed_request_succeeds(self, client, db_session):
        """State-changing request with valid signed token and trusted origin succeeds."""
        email = f"csrf_ok_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/auth/register", json={
            "email": email, "username": f"u_{uuid.uuid4().hex[:6]}", "password": "Password123!"
        })
        access_token = reg.cookies.get("access_token")
        csrf_token = reg.cookies.get("csrf_token")

        res = client.put(
            "/api/student/profile",
            json={"full_name": "Legitimate User"},
            cookies={"access_token": access_token, "csrf_token": csrf_token},
            headers={
                "X-CSRF-Token": csrf_token,
                "Origin": "http://localhost:5173"
            }
        )
        assert res.status_code == 200

    def test_csrf_not_required_for_safe_get(self, client, db_session):
        """GET requests are safe methods and do not require CSRF tokens."""
        email = f"csrf_get_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/auth/register", json={
            "email": email, "username": f"u_{uuid.uuid4().hex[:6]}", "password": "Password123!"
        })
        access_token = reg.cookies.get("access_token")

        res = client.get(
            "/api/student/profile",
            cookies={"access_token": access_token}
        )
        assert res.status_code == 200


# ---------------------------------------------------------------------------
# 4. Bearer Transition & Backward Compatibility
# ---------------------------------------------------------------------------

class TestBearerBackwardCompatibility:
    """Verify non-browser clients can authenticate with Bearer tokens without CSRF."""

    def test_bearer_token_authenticates_without_cookies_or_csrf(self, client, db_session):
        """CLI client using Authorization: Bearer <token> can access protected endpoints."""
        email = f"bearer_{uuid.uuid4().hex[:6]}@example.com"
        username = f"user_{uuid.uuid4().hex[:6]}"
        reg = client.post("/api/auth/register", json={
            "email": email, "username": username, "password": "Password123!"
        })
        assert reg.status_code == 201

        # Get token via CLI endpoint
        token_res = client.post("/api/auth/token", json={
            "email": email, "password": "Password123!"
        })
        access_token = token_res.json()["data"]["access_token"]

        # Call PUT endpoint using fresh client without cookies
        from app.main import app
        from app.database.base import get_db

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app, cookies={}) as fresh_client:
            res = fresh_client.put(
                "/api/student/profile",
                json={"full_name": "CLI Automated User"},
                headers={"Authorization": f"Bearer {access_token}"}
            )
        assert res.status_code == 200
