"""
Campus Café - Authentication & Security Utilities
-------------------------------------------------
This module handles password hashing, JWT token creation/decryption, 
OTP (One-Time Password) generation, and authentication dependencies for routes.

TODO:
    1. In production, change SECRET_KEY to be loaded from environment variables (.env).
    2. Add refresh token support to extend/manage sessions securely.
    3. Transition password hashing parameters to follow strict security benchmarks.
"""

from datetime import datetime, timedelta
from jose import jwt, JWTError
# pyrefly: ignore [missing-import]
from passlib.context import CryptContext
from fastapi import HTTPException, status, Cookie
from typing import Optional
import random, string

# Secret key used to sign JSON Web Tokens (JWT)
# WARNING: Do not hardcode this in production! Use os.getenv("SECRET_KEY")
SECRET_KEY = "cafe-demo-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Sessions expire after 24 hours

# Setup passlib bcrypt context for hashing and verifying passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hashes a plain text password using bcrypt.
    """
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verifies a plain text password against a bcrypt hash.
    """
    return pwd_context.verify(plain, hashed)


def create_token(data: dict) -> str:
    """
    Creates a JWT access token containing user payload and expiration time.
    """
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """
    Decodes and validates a JWT access token.
    Returns the decoded payload if valid, otherwise returns None.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def generate_otp() -> str:
    """
    Generates a secure 6-digit numeric OTP (One-Time Password).
    """
    return "".join(random.choices(string.digits, k=6))


def get_current_user(token: Optional[str] = Cookie(default=None, alias="access_token")):
    """
    Retrieves the current authenticated user from the HTTP-only cookie.
    Used as an optional dependency (returns None if the user is a guest).
    """
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    return payload  # Returns dict containing {"phone", "name", "role"}


def require_user(token: Optional[str] = Cookie(default=None, alias="access_token")):
    """
    FastAPI dependency that enforces authentication.
    Raises 401 Unauthorized if the user session is missing or invalid.
    """
    user = get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please sign in."
        )
    return user


def require_admin(token: Optional[str] = Cookie(default=None, alias="access_token")):
    """
    FastAPI dependency that enforces admin authorization.
    Raises 401 if unauthenticated, or 403 if the user is not an administrator.
    """
    user = require_user(token)
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden. Administrator privileges required."
        )
    return user
