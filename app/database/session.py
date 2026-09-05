import logging
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

# Setup engine arguments depending on DB type
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# Create modern SQLAlchemy async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for SQL queries logging in development
    connect_args=connect_args,
    pool_pre_ping=True,  # Automatically reconnect if remote MySQL connection timed out
    pool_recycle=120,    # Recycle connections every 2 minutes before Hostinger timeout
    pool_size=10,        # Keep 10 active connections always warm in the pool
    max_overflow=20,     # Allow up to 30 concurrent active connections under load
    future=True
)

# Async session maker
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session and ensures it closes correctly.
    """
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
