from __future__ import annotations
import json
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    AuthResponse,
    BrowserAuthResponse,
)
from app.services.auth_service import (
    register_student,
    authenticate_user,
    refresh_user_token,
    logout_user,
)
from app.core.dependencies import security, generate_csrf_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------
def _is_secure() -> bool:
    """Return True when cookies must carry the Secure flag."""
    return settings.ENVIRONMENT.lower() in ("production", "staging")


def _samesite() -> str:
    """SameSite policy.

    Development: frontend proxy on same origin -> Lax is sufficient.
    Production/staging: Lax is safest when API and SPA share the same registrable domain.
    """
    return "lax"
    """SameSite policy.

    Development: frontend on a different port (e.g., Vite dev server) requires SameSite=None so cookies are sent on cross‑origin XHR/fetch.
    Production/staging: Lax is safest when API and SPA share the same registrable domain.
    """
    # In development we want cross‑origin cookie transmission for API calls.
    return "none" if settings.ENVIRONMENT.lower() == "development" else "lax"

    """SameSite policy.

    Development: frontend proxy on same origin -> Lax is sufficient.
    Production/staging: Lax is safest when API and SPA share the same
    registrable domain.
    """
    return "lax"


def _set_auth_cookies(
    response: Response,
    tokens: dict,
    csrf_token: str,
) -> None:
    """Set access_token, refresh_token (HttpOnly) and csrf_token cookies."""
    secure = _is_secure()
    samesite = _samesite()

    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # Must be readable by JavaScript for double-submit header
        secure=secure,
        samesite=samesite,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    """Delete all auth cookies."""
    for name in ("access_token", "refresh_token", "csrf_token"):
        response.delete_cookie(key=name, path="/")


def _build_json_response(
    body: dict,
    status_code: int = 200,
    tokens: dict | None = None,
    csrf_token: str | None = None,
    clear: bool = False,
) -> Response:
    """Build a Response with JSON body and auth cookies."""
    response = Response(
        content=json.dumps(body),
        status_code=status_code,
        media_type="application/json",
    )
    if tokens and csrf_token:
        _set_auth_cookies(response, tokens, csrf_token)
    if clear:
        _clear_auth_cookies(response)
    return response


# ---------------------------------------------------------------------------
# Browser Endpoints (HttpOnly Cookie-Based, ZERO JWTs in response body)
# ---------------------------------------------------------------------------
@router.post("/register", response_model=BrowserAuthResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Browser registration: Sets HttpOnly auth cookies. Returns user info + CSRF token only."""
    tokens = register_student(db, request)
    csrf_token = generate_csrf_token()
    body = {
        "success": True,
        "message": "Registration successful",
        "data": {
            "user_id": str(tokens["user_id"]),
            "username": tokens["username"],
            "role": tokens["role"],
            "csrf_token": csrf_token,
        },
    }
    return _build_json_response(body, status_code=201, tokens=tokens, csrf_token=csrf_token)


@router.post("/login", response_model=BrowserAuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Browser login: Sets HttpOnly auth cookies. Returns user info + CSRF token only."""
    tokens = authenticate_user(db, request)
    csrf_token = generate_csrf_token()
    body = {
        "success": True,
        "message": "Login successful",
        "data": {
            "user_id": str(tokens["user_id"]),
            "username": tokens["username"],
            "role": tokens["role"],
            "csrf_token": csrf_token,
        },
    }
    return _build_json_response(body, status_code=200, tokens=tokens, csrf_token=csrf_token)


@router.post("/refresh", response_model=BrowserAuthResponse)
def refresh(request: Request, db: Session = Depends(get_db)):
    """Browser refresh: Reads refresh_token from HttpOnly cookie, rotates cookies, returns user info."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token cookie",
        )

    tokens = refresh_user_token(db, refresh_token)
    csrf_token = generate_csrf_token()
    body = {
        "success": True,
        "message": "Token refreshed",
        "data": {
            "user_id": str(tokens["user_id"]),
            "username": tokens["username"],
            "role": tokens["role"],
            "csrf_token": csrf_token,
        },
    }
    return _build_json_response(body, status_code=200, tokens=tokens, csrf_token=csrf_token)


@router.post("/logout")
def logout(request: Request):
    """Logout: Revokes token in Redis and clears all auth cookies."""
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if token:
        logout_user(token)
    response_body = {"success": True, "message": "Logged out successfully"}
    return _build_json_response(response_body, clear=True)


# ---------------------------------------------------------------------------
# Programmatic / CLI Token Endpoints (Pure Bearer, NO Cookies)
# ---------------------------------------------------------------------------
@router.post("/token", response_model=AuthResponse)
def issue_cli_token(request: LoginRequest, db: Session = Depends(get_db)):
    """CLI/API token issuance: Returns JWT tokens in JSON body for scripts, CLI, and SDKs.

    Does NOT set cookies.
    """
    tokens = authenticate_user(db, request)
    return {
        "success": True,
        "message": "Token issued",
        "data": {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
            "user_id": str(tokens["user_id"]),
            "username": tokens["username"],
            "role": tokens["role"],
        },
    }


@router.post("/token/refresh", response_model=AuthResponse)
def refresh_cli_token(request: RefreshRequest, db: Session = Depends(get_db)):
    """CLI/API token refresh: Accepts refresh_token in request body, returns updated tokens in body.

    Does NOT read or set cookies.
    """
    tokens = refresh_user_token(db, request.refresh_token)
    return {
        "success": True,
        "message": "Token refreshed",
        "data": {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
            "user_id": str(tokens["user_id"]),
            "username": tokens["username"],
            "role": tokens["role"],
        },
    }
