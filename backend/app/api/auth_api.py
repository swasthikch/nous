"""User Authentication & RBAC REST API Endpoints for NOUS (Phase 10).

Endpoints:
- POST /api/auth/register: Create user with PBKDF2 hash.
- POST /api/auth/login: Authenticate and issue JWT Bearer token.
- GET  /api/auth/me: Retrieve current authenticated user profile.
- POST /api/auth/logout: Client logout acknowledgement.
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from backend.app.security.auth import (
    User,
    auth_manager,
    create_access_token,
    decode_access_token,
)

router = APIRouter(prefix="/api/auth", tags=["User Authentication & Security"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6)
    role: str = Field(default="user")


class LoginRequest(BaseModel):
    username_or_email: str = Field(...)
    password: str = Field(...)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """FastAPI Dependency for validating JWT Bearer authentication."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[len("Bearer "):].strip()
    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authorization token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject.")

    user = auth_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account no longer exists.")

    return user


def require_role(required_role: str):
    """Enforce specific RBAC role permission."""
    async def _role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role != required_role and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires '{required_role}' role privileges.",
            )
        return user
    return _role_checker


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    """Register a new user account."""
    try:
        user = auth_manager.register_user(
            username=req.username,
            email=req.email,
            password=req.password,
            role=req.role,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    token = create_access_token({"sub": user.id, "username": user.username, "role": user.role})
    return AuthResponse(access_token=token, user=user)


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Authenticate with username/email and password."""
    user = auth_manager.authenticate_user(req.username_or_email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )

    token = create_access_token({"sub": user.id, "username": user.username, "role": user.role})
    return AuthResponse(access_token=token, user=user)


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve current authenticated user."""
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Acknowledge client logout."""
    return {"success": True, "message": f"User '{current_user.username}' signed out successfully."}
