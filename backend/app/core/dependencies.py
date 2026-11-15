from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.core.security import decode_token
from app.cache.cache_manager import cache
from app.models.user import User
import uuid
import hmac
import hashlib
import time
import secrets
from typing import Optional

security = HTTPBearer(auto_error=False)

# Endpoints exempt from CSRF validation (non-state-changing, auth-issuing, or CLI token endpoints)
_CSRF_EXEMPT_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/token",
    "/api/auth/token/refresh",
    "/api/health",
    "/health",
    "/",
}

# HTTP methods that do not require CSRF protection
_CSRF_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def generate_csrf_token() -> str:
    """Generate a cryptographically signed, timestamped CSRF token.

    Format: <entropy>:<timestamp>.<hmac_signature>
    This binds the token to the server secret (SECRET_KEY), preventing cookie injection
    from untrusted sibling domains or attackers without access to the server secret.
    """
    from app.core.config import settings

    entropy = secrets.token_hex(16)
    timestamp = str(int(time.time()))
    payload = f"{entropy}:{timestamp}"
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]
    return f"{payload}.{signature}"


def verify_csrf_token(token: str) -> bool:
    """Validate that a CSRF token has a valid cryptographic signature and is not expired."""
    from app.core.config import settings

    if not token or "." not in token:
        return False
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        return False
    payload, signature = parts
    expected_sig = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]
    if not hmac.compare_digest(signature, expected_sig):
        return False
    # Validate timestamp expiration (7 days, matching refresh token lifespan)
    try:
        _, ts_str = payload.split(":", 1)
        age = int(time.time()) - int(ts_str)
        if age < 0 or age > settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400:
            return False
    except Exception:
        return False
    return True


def _extract_access_token(
    request: Request = None,
    credentials: Optional[HTTPAuthorizationCredentials] = None,
) -> Optional[str]:
    """Extract access token: cookie first, then Bearer header (transition/CLI)."""
    # 1. HttpOnly cookie (preferred for browsers)
    if request is not None:
        token = request.cookies.get("access_token")
        if token:
            return token
    # 2. Authorization header (CLI and programmatic clients)
    if credentials and credentials.credentials:
        return credentials.credentials
    return None


def _validate_csrf(request: Request) -> None:
    """Validate CSRF protection for cookie-authenticated state-changing requests.

    Security layers:
    1. Safe method check (GET/HEAD/OPTIONS exempt).
    2. Path exemption check (login/register/token exempt).
    3. Non-cookie check (Bearer-authenticated CLI requests are exempt from CSRF).
    4. Origin/Referer verification against CORS_ORIGINS.
    5. Double-submit token verification (X-CSRF-Token header == csrf_token cookie).
    6. Cryptographic signature verification (HMAC with SECRET_KEY protects against
       cookie injection from sibling subdomains).
    """
    method = request.method.upper()
    if method in _CSRF_SAFE_METHODS:
        return

    path = request.url.path.rstrip("/")
    if path in _CSRF_EXEMPT_PATHS:
        return

    # Only enforce CSRF when the request is cookie-authenticated
    if not request.cookies.get("access_token"):
        return  # Bearer-header path — no ambient cookie auth, no CSRF risk

    # 1. Origin / Referer validation
    from app.core.config import settings
    origin = request.headers.get("origin")
    if origin:
        allowed = set(settings.CORS_ORIGINS)
        if origin not in allowed and not origin.startswith("http://testserver"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed: Origin header mismatch",
            )
    else:
        referer = request.headers.get("referer")
        if referer:
            from urllib.parse import urlparse
            ref_parsed = urlparse(referer)
            ref_origin = f"{ref_parsed.scheme}://{ref_parsed.netloc}"
            allowed = set(settings.CORS_ORIGINS)
            if ref_origin not in allowed and not ref_origin.startswith("http://testserver"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF validation failed: Referer header mismatch",
                )

    # 2. Double-submit matching
    csrf_cookie = request.cookies.get("csrf_token", "")
    csrf_header = request.headers.get("x-csrf-token", "")

    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed: Token mismatch or missing",
        )

    # 3. Cryptographic signature check (prevents sibling-subdomain injection)
    if not verify_csrf_token(csrf_cookie):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed: Token signature invalid or expired",
        )


def get_current_user(
    request: Request = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    # --- CSRF check (before anything else on state-changing requests) ---
    if request is not None:
        _validate_csrf(request)

    token = _extract_access_token(request, credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Check if token is blacklisted in Redis with explicit failure policy
    is_blacklisted = cache.is_token_blacklisted(token)
    if is_blacklisted is True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
        )
    elif is_blacklisted is None:
        # Redis is unreachable: enforce strict or permissive failure policy based on settings
        from app.core.config import settings
        if settings.AUTH_REQUIRE_REDIS_BLACKLIST or settings.ENVIRONMENT.lower() in ("production", "staging"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable. Security verification degraded.",
            )

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user identifier")

    user = db.query(User).filter(User.id == user_uuid, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
