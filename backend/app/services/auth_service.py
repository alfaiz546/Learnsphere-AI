from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, StudentProfile
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.cache.cache_manager import cache
from app.schemas.auth import RegisterRequest, LoginRequest
import uuid

def register_student(db: Session, request: RegisterRequest) -> dict:
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    
    user = User(
        email=request.email,
        username=request.username,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        role="student"
    )
    db.add(user)
    db.flush()
    
    profile = StudentProfile(user_id=user.id, subjects_of_interest="[]")
    db.add(profile)
    db.commit()
    db.refresh(user)
    
    return _generate_tokens(user)

def authenticate_user(db: Session, request: LoginRequest) -> dict:
    user = db.query(User).filter(User.email == request.email, User.is_active == True).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return _generate_tokens(user)

def refresh_user_token(db: Session, refresh_token: str) -> dict:
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_id_str = payload.get("sub")
    try:
        user_uuid = uuid.UUID(user_id_str)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    user = db.query(User).filter(User.id == user_uuid, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return _generate_tokens(user)

def _generate_tokens(user: User) -> dict:
    access_token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "username": user.username,
        "role": user.role
    }

def logout_user(token: str) -> bool:
    """Extracts expiration from token and blacklists it in Redis until expiry."""
    payload = decode_token(token)
    if not payload:
        return False
    exp = payload.get("exp")
    if exp:
        now = datetime.now(timezone.utc).timestamp()
        ttl = int(exp - now)
        if ttl > 0:
            return cache.blacklist_token(token, ttl)
    return True
