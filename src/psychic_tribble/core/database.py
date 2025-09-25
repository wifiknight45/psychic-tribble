"""Database connection pooling and configuration."""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.pool import QueuePool
from sqlalchemy import event

logger = logging.getLogger(__name__)

# Global database components
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


async def init_database_pool(settings) -> None:
    """Initialize database connection pool with optimized settings."""
    global _engine, _session_factory
    
    # Connection pool configuration for better performance and resource management
    pool_config = {
        "poolclass": QueuePool,
        "pool_size": 20,          # Number of connections to maintain
        "max_overflow": 30,       # Additional connections beyond pool_size
        "pool_pre_ping": True,    # Validate connections before use
        "pool_recycle": 3600,     # Recycle connections after 1 hour
        "pool_timeout": 30,       # Timeout when getting connection from pool
    }
    
    # Engine configuration
    engine_config = {
        "echo": settings.DEBUG,   # Log SQL queries in debug mode
        "echo_pool": settings.DEBUG,  # Log pool events in debug mode
        "future": True,           # Use SQLAlchemy 2.0 style
        **pool_config
    }
    
    # Create async engine
    _engine = create_async_engine(
        settings.DATABASE_URL,
        **engine_config
    )
    
    # Create session factory
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
        autocommit=False
    )
    
    # Set up connection event listeners for monitoring
    @event.listens_for(_engine.sync_engine, "connect")
    def on_connect(dbapi_connection, connection_record):
        """Log database connections."""
        logger.debug("Database connection established")
    
    @event.listens_for(_engine.sync_engine, "checkout")
    def on_checkout(dbapi_connection, connection_record, connection_proxy):
        """Log connection checkout from pool."""
        logger.debug("Connection checked out from pool")
    
    @event.listens_for(_engine.sync_engine, "checkin")
    def on_checkin(dbapi_connection, connection_record):
        """Log connection checkin to pool."""
        logger.debug("Connection checked in to pool")
    
    logger.info(
        f"Database connection pool initialized",
        extra={
            "database_url": settings.DATABASE_URL.split("@")[-1],  # Hide credentials
            "pool_size": pool_config["pool_size"],
            "max_overflow": pool_config["max_overflow"]
        }
    )


async def get_db_session() -> AsyncSession:
    """Get database session dependency for FastAPI."""
    if not _session_factory:
        raise RuntimeError("Database not initialized. Call init_database_pool first.")
    
    async with _session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_database_pool() -> None:
    """Close database connection pool."""
    global _engine, _session_factory
    
    if _engine:
        await _engine.dispose()
        logger.info("Database connection pool closed")
    
    _engine = None
    _session_factory = None


def get_engine() -> Optional[AsyncEngine]:
    """Get the database engine."""
    return _engine


def get_session_factory() -> Optional[async_sessionmaker[AsyncSession]]:
    """Get the session factory."""
    return _session_factory


# Connection health check utility
async def check_database_health() -> bool:
    """Check if database is healthy and accessible."""
    if not _engine:
        return False
    
    try:
        async with _engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Database transaction context manager
class DatabaseTransaction:
    """Context manager for database transactions with proper error handling."""
    
    def __init__(self):
        self.session: Optional[AsyncSession] = None
    
    async def __aenter__(self) -> AsyncSession:
        """Enter transaction context."""
        if not _session_factory:
            raise RuntimeError("Database not initialized")
        
        self.session = _session_factory()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context with proper cleanup."""
        if self.session:
            if exc_type:
                await self.session.rollback()
                logger.error(f"Transaction rolled back due to: {exc_val}")
            else:
                await self.session.commit()
            
            await self.session.close()


# Utility function for database operations
async def execute_with_retry(operation, max_retries: int = 3):
    """Execute database operation with retry logic."""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            last_exception = e
            logger.warning(
                f"Database operation failed (attempt {attempt + 1}/{max_retries}): {e}"
            )
            
            if attempt < max_retries - 1:
                # Wait before retry (exponential backoff)
                import asyncio
                await asyncio.sleep(2 ** attempt)
    
    logger.error(f"Database operation failed after {max_retries} attempts")
    raise last_exception