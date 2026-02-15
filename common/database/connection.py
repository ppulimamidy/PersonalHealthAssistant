"""
Database Connection Management
Handles database connections, connection pooling, and health checks.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, AsyncGenerator
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from contextlib import contextmanager

from common.config.settings import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection manager with connection pooling"""
    
    def __init__(self):
        logger.info("Initializing DatabaseManager")
        self.settings = get_settings()
        logger.info(f"DatabaseManager settings loaded: {self.settings.DATABASE_URL}")
        self._engine: Optional[Engine] = None
        self._async_engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._async_session_factory: Optional[async_sessionmaker] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._is_healthy: bool = False
        logger.info("DatabaseManager initialized successfully")
        
    def get_database_url(self) -> str:
        """Get database URL from settings"""
        url = self.settings.DATABASE_URL
        logger.info(f"Getting database URL: {url}")
        return url
    
    def create_engine(self) -> Engine:
        """Create SQLAlchemy engine with connection pooling"""
        if self._engine is not None:
            logger.info("Returning existing sync engine")
            return self._engine
            
        database_url = self.get_database_url()
        logger.info(f"Creating sync engine with URL: {database_url}")
        
        # Create engine with connection pooling
        self._engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=self.settings.DATABASE_POOL_SIZE,
            max_overflow=self.settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,  # Enable connection health checks
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=False,  # Set to False for production
            connect_args={
                "connect_timeout": 10,
                "application_name": "health_assistant"
            }
        )
        
        logger.info(f"Sync database engine created with pool size: {self.settings.DATABASE_POOL_SIZE}")
        return self._engine
    
    def create_async_engine(self) -> AsyncEngine:
        """Create async SQLAlchemy engine"""
        if self._async_engine is not None:
            logger.info("Returning existing async engine")
            return self._async_engine
            
        database_url = self.get_database_url()
        logger.info(f"Creating async engine with URL: {database_url}")
        
        # Convert to async URL if needed
        if database_url.startswith("postgresql://"):
            async_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        else:
            async_url = database_url

        # Strip ?sslmode=... from URL (asyncpg doesn't support it as a query param)
        # and convert to asyncpg's ssl connect_arg instead.
        import re
        ssl_connect_arg = {}
        match = re.search(r"[?&]sslmode=(\w+)", async_url)
        if match:
            sslmode = match.group(1)
            # Remove sslmode param from URL
            async_url = re.sub(r"[?&]sslmode=\w+", "", async_url)
            # Clean up dangling ? or &
            async_url = async_url.rstrip("?&")
            if sslmode in ("require", "verify-ca", "verify-full"):
                import ssl
                ssl_ctx = ssl.create_default_context()
                if sslmode == "require":
                    ssl_ctx.check_hostname = False
                    ssl_ctx.verify_mode = ssl.CERT_NONE
                ssl_connect_arg = {"ssl": ssl_ctx}

        logger.info(f"Async URL (sanitized): {async_url.split('@')[0]}@***")

        try:
            self._async_engine = create_async_engine(
                async_url,
                pool_pre_ping=True,
                echo=False,
                pool_size=self.settings.DATABASE_POOL_SIZE,
                max_overflow=self.settings.DATABASE_MAX_OVERFLOW,
                pool_recycle=3600,
                connect_args=ssl_connect_arg,
            )
            logger.info("Async database engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create async engine: {e}", exc_info=True)
            raise
            
        return self._async_engine
    
    def get_session_factory(self) -> sessionmaker:
        """Get session factory for synchronous sessions"""
        if self._session_factory is None:
            logger.info("Creating sync session factory")
            engine = self.create_engine()
            self._session_factory = sessionmaker(
                bind=engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            logger.info("Sync session factory created")
        return self._session_factory
    
    def get_async_session_factory(self) -> async_sessionmaker:
        """Get session factory for async sessions"""
        if self._async_session_factory is None:
            logger.info("Creating async session factory")
            engine = self.create_async_engine()
            self._async_session_factory = async_sessionmaker(
                bind=engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            logger.info("Async session factory created")
        return self._async_session_factory
    
    @contextmanager
    def get_session(self) -> Session:
        """Get a database session with automatic cleanup"""
        logger.debug("Getting sync database session")
        session_factory = self.get_session_factory()
        session = session_factory()
        try:
            yield session
            session.commit()
            logger.debug("Sync session committed successfully")
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            session.close()
            logger.debug("Sync session closed")
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session with automatic cleanup"""
        logger.debug("Getting async database session")
        session_factory = self.get_async_session_factory()
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
                logger.debug("Async session committed successfully")
            except Exception as e:
                await session.rollback()
                logger.error(f"Async database session error: {e}", exc_info=True)
                raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        logger.info("Starting database health check")
        try:
            logger.info("Attempting to get async session for health check")
            async with self.get_async_session() as session:
                logger.info("Executing health check query")
                result = await session.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()
                
                if row and row[0] == 1:
                    self._is_healthy = True
                    logger.info("Database health check passed")
                    return {
                        "status": "healthy",
                        "message": "Database connection is working",
                        "timestamp": asyncio.get_event_loop().time()
                    }
                else:
                    self._is_healthy = False
                    logger.error("Database health check failed: unexpected result")
                    return {
                        "status": "unhealthy",
                        "message": "Database health check failed",
                        "timestamp": asyncio.get_event_loop().time()
                    }
        except Exception as e:
            self._is_healthy = False
            logger.error(f"Database health check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "message": f"Database health check error: {str(e)}",
                "timestamp": asyncio.get_event_loop().time()
            }
    
    def is_healthy(self) -> bool:
        """Check if database is healthy"""
        return self._is_healthy
    
    async def start_health_monitoring(self):
        """Start periodic health monitoring"""
        if self._health_check_task is not None:
            logger.info("Health monitoring already started")
            return
            
        async def health_monitor():
            logger.info("Starting health monitoring loop")
            while True:
                try:
                    await self.health_check()
                    await asyncio.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}", exc_info=True)
                    await asyncio.sleep(5)  # Wait before retry
        
        self._health_check_task = asyncio.create_task(health_monitor())
        logger.info("Database health monitoring started")
    
    async def stop_health_monitoring(self):
        """Stop health monitoring"""
        if self._health_check_task:
            logger.info("Stopping health monitoring")
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("Database health monitoring stopped")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        stats = {}
        
        if self._engine:
            pool = self._engine.pool
            stats["sync_pool"] = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
        
        if self._async_engine:
            pool = self._async_engine.pool
            stats["async_pool"] = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
        
        return stats
    
    async def close(self):
        """Close all database connections"""
        logger.info("Closing database connections")
        
        # Stop health monitoring
        await self.stop_health_monitoring()
        
        # Close async engine
        if self._async_engine:
            logger.info("Closing async engine")
            await self._async_engine.dispose()
            self._async_engine = None
        
        # Close sync engine
        if self._engine:
            logger.info("Closing sync engine")
            self._engine.dispose()
            self._engine = None
        
        logger.info("All database connections closed")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get database manager singleton"""
    global _db_manager
    if _db_manager is None:
        logger.info("Creating new DatabaseManager instance")
        _db_manager = DatabaseManager()
        logger.info("DatabaseManager instance created")
    return _db_manager


def get_session() -> Session:
    """Get a database session"""
    return get_db_manager().get_session()


async def get_async_session():
    async with get_db_manager().get_async_session() as session:
        yield session


def get_db():
    """Dependency for FastAPI to get database session"""
    with get_session() as session:
        yield session


async def get_async_db():
    """Dependency for FastAPI to get async database session"""
    async with get_db_manager().get_async_session() as session:
        yield session 