# database.py

from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from app.settings import settings

# Set up the declarative base class for ORM models
Base = declarative_base()

# Async engine using database URL from settings (environment or .env for secrets)
engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,  # Turn off in prod
    pool_pre_ping=True,
    pool_recycle=1800,
    future=True,
)

# Async session factory for dependency injection
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)

# Dependency function for FastAPI endpoints and services
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a fresh SQLAlchemy async session per request; closes session automatically."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Database initialization helper
async def init_db() -> None:
    """Initialize DB schema (to be called on startup if needed)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

