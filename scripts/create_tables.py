#!/usr/bin/env python3
"""
Script to create all database tables for the Personal Health Assistant platform.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from common.database.connection import get_database_url
from apps.auth.models import Base as AuthBase
from apps.user_profile.models import Base as UserProfileBase
from apps.health_tracking.models import Base as HealthTrackingBase

async def create_tables():
    """Create all database tables."""
    try:
        # Get database URL
        db_url = get_database_url()
        print(f"Connecting to database: {db_url}")
        
        # Create async engine
        engine = create_async_engine(db_url, echo=True)
        
        # Create all tables
        print("Creating database tables...")
        
        # Create auth tables
        print("Creating auth tables...")
        async with engine.begin() as conn:
            await conn.run_sync(AuthBase.metadata.create_all)
        
        # Create user profile tables
        print("Creating user profile tables...")
        async with engine.begin() as conn:
            await conn.run_sync(UserProfileBase.metadata.create_all)
        
        # Create health tracking tables
        print("Creating health tracking tables...")
        async with engine.begin() as conn:
            await conn.run_sync(HealthTrackingBase.metadata.create_all)
        
        print("All tables created successfully!")
        
        # Close engine
        await engine.dispose()
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(create_tables()) 