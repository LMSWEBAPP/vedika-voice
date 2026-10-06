from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
from app.core.logging import logger

# Create async engine with pool settings suitable for SQLite or Postgres
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for yielding an async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables if they do not exist."""
    async with engine.begin() as conn:
        # Import all models before create_all
        import app.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)

        # SQLite safe check for domain column on leads table
        if "sqlite" in settings.DATABASE_URL:
            from sqlalchemy import text
            try:
                await conn.execute(text("ALTER TABLE leads ADD COLUMN domain VARCHAR(255)"))
            except Exception:
                pass  # column already exists
    logger.info("Database tables initialized successfully.")
