"""
Velora — Security Utilities
JWT creation/verification and password hashing (bcrypt).
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.config.settings import settings

# ── Password hashing ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(plain.encode('utf-8'), salt)
    return hashed_bytes.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


# ── JWT ───────────────────────────────────────────────────────────────────────
_bearer = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_hours: int = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        hours=expires_hours or settings.JWT_EXPIRY_HOURS
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    """FastAPI dependency: extracts and validates JWT, returns payload dict."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[dict]:
    """Same as get_current_user but returns None instead of raising."""
    if not credentials:
        return None
    try:
        return decode_access_token(credentials.credentials)
    except HTTPException:
        return None
