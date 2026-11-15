from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any
import re

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=255)

    model_config = {"str_strip_whitespace": True}

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str

class BrowserAuthData(BaseModel):
    user_id: str
    username: str
    role: str
    csrf_token: str

class BrowserAuthResponse(BaseModel):
    success: bool
    message: str
    data: Optional[BrowserAuthData] = None

class AuthResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
