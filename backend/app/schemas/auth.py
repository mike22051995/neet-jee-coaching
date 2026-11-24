"""Schemas for authentication endpoints."""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class AdminUserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
