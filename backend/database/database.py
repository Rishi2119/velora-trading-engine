"""
Velora Database — Async SQLAlchemy Engine & Session Factory
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from backend.config.settings import settings
from backend.database.models import Base
import logging

logger = logging.getLogger(__name__)

# Build engine — StaticPool for SQLite in-process dev
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=(
        {"check_same_thread": False}
        if "sqlite" in settings.DATABASE_URL else {}
    ),
    poolclass=StaticPool if "sqlite" in settings.DATABASE_URL else None,
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Create all tables on first launch."""
    logger.info(f"Connecting to database: {settings.DATABASE_URL}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized.")


async def get_db():
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
