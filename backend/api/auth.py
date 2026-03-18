"""
Velora API — Authentication
POST /auth/register  — create new user
POST /auth/login     — returns JWT
GET  /auth/me        — current user profile
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.database import get_db
from backend.database.models import User
from backend.utils.security import hash_password, verify_password, create_access_token, get_current_user
from backend.app.core.firebase_auth import verify_firebase_token
from backend.app.core.supabase_auth import verify_supabase_token

from backend.utils.limiter import limiter
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str

class FirebaseLoginRequest(BaseModel):
    id_token: str

class SupabaseLoginRequest(BaseModel):
    id_token: str


class UserProfile(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    is_admin: bool


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user account and return a JWT."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == body.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email})
    logger.info(f"New user registered: {user.email}")
    return TokenResponse(access_token=token, user_id=user.id, email=user.email)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and return JWT."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token({"sub": str(user.id), "email": user.email})
    logger.info(f"User logged in: {user.email}")
    return TokenResponse(access_token=token, user_id=user.id, email=user.email)


@router.post("/firebase-login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def firebase_login(request: Request, body: FirebaseLoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate via Firebase ID token and return local JWT."""
    try:
        decoded_token = verify_firebase_token(body.id_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    email = decoded_token.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Firebase token missing email")

    # Check if user exists, if not create one
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        # Auto-register Firebase user
        user = User(
            email=email,
            hashed_password="firebase_unusable_password",
            full_name=decoded_token.get("name", ""),
            provider="google",
            is_active=True,
            last_login=datetime.utcnow()
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"New user registered via Firebase: {email}")
    else:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is disabled")
        user.last_login = datetime.utcnow()
        await db.commit()
        logger.info(f"User logged in via Firebase: {email}")

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenResponse(access_token=token, user_id=user.id, email=user.email)


@router.post("/supabase-login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def supabase_login(request: Request, body: SupabaseLoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate via Supabase ID token and return local JWT."""
    try:
        decoded_token = await verify_supabase_token(body.id_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    email = decoded_token.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Supabase token missing email")

    # Check if user exists, if not create one
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            hashed_password="supabase_unusable_password",
            full_name=decoded_token.get("full_name", ""),
            provider="supabase",
            is_active=True,
            last_login=datetime.utcnow()
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"New user registered via Supabase: {email}")
    else:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is disabled")
        user.last_login = datetime.utcnow()
        await db.commit()
        logger.info(f"User logged in via Supabase: {email}")

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenResponse(access_token=token, user_id=user.id, email=user.email)


@router.get("/me", response_model=UserProfile)
async def get_me(
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the currently authenticated user's profile."""
    user_id = int(current["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name or "",
        is_active=user.is_active,
        is_admin=user.is_admin,
    )
