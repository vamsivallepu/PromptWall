"""Database configuration and connection pool management"""
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Base class for SQLAlchemy models (defined first to avoid circular imports)
Base = declarative_base()

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:vamsi@localhost:5432/ai_firewall"
)

# Only create async engine if we're using an async driver
# Alembic uses sync drivers, so we skip engine creation during migrations
if "+asyncpg" in DATABASE_URL or "+asyncio" in DATABASE_URL:
    # Create async engine
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
    )

    # Create async session factory
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
else:
    # For Alembic migrations with sync drivers, these won't be used
    engine = None
    AsyncSessionLocal = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    if engine is None:
        raise RuntimeError(
            f"Database engine is None. DATABASE_URL: {DATABASE_URL}. "
            f"Make sure DATABASE_URL contains '+asyncpg' or '+asyncio' driver."
        )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connection pool"""
    if engine is not None:
        await engine.dispose()
