# backend/app/db/session.py
# Refactored Database Engine Session Manager.
# Optimized for: Auto-fallback from PostgreSQL (asyncpg) to SQLite (aiosqlite) for laptop execution.

import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

logger = logging.getLogger("spems.db")

# Read database URL, fallback to local SQLite database in virtualenv
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite+aiosqlite:///database/buffer.db"
)

# Architectural correction: If sqlite is specified but driver is missing, convert to async driver aiosqlite
if DATABASE_URL.startswith("sqlite://"):
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
    logger.info("Local environment: Using SQLite with async aiosqlite driver.")

# Connection pool configurations optimized by database type
is_sqlite = "sqlite" in DATABASE_URL
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args=connect_args,
    **({} if is_sqlite else {"pool_size": 20, "max_overflow": 10})
)

# Async session provider factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_async_db():
    """Asynchronous database session dependency injection provider."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session exception: {e}")
            raise
        finally:
            await session.close()
