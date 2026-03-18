"""
Seed script: creates/resets the admin user in velora.db with a known password.
Run from d:\trading_engins:
    python scripts/seed_admin.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.pool import StaticPool
from backend.database.models import Base, User
from backend.utils.security import hash_password

DATABASE_URL = "sqlite+aiosqlite:///./velora.db"
ADMIN_EMAIL = "admin@velora.com"
ADMIN_PASSWORD = "velora123"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def seed():
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionFactory() as db:
        result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        user = result.scalar_one_or_none()

        if user:
            user.hashed_password = hash_password(ADMIN_PASSWORD)
            user.is_active = True
            user.is_admin = True
            print(f"[UPDATED] {ADMIN_EMAIL} password reset to: {ADMIN_PASSWORD}")
        else:
            user = User(
                email=ADMIN_EMAIL,
                hashed_password=hash_password(ADMIN_PASSWORD),
                full_name="Admin",
                is_active=True,
                is_admin=True,
            )
            db.add(user)
            print(f"[CREATED] {ADMIN_EMAIL} with password: {ADMIN_PASSWORD}")

        await db.commit()
    print(" Login at http://localhost:3000/login")
    print(f"  Email:    {ADMIN_EMAIL}")
    print(f"  Password: {ADMIN_PASSWORD}")


asyncio.run(seed())
