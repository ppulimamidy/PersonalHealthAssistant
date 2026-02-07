"""
Create Epic FHIR Data Tables

This script creates the database tables for storing Epic FHIR data locally.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from apps.medical_records.models.epic_fhir_data import (
    Base,
    EpicFHIRConnection,
    EpicFHIRObservation,
    EpicFHIRDiagnosticReport,
    EpicFHIRDocument,
    EpicFHIRImagingStudy,
    EpicFHIRSyncLog
)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5432/health_assistant"
)


async def create_tables():
    """Create all Epic FHIR data tables."""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
            print("✅ Epic FHIR data tables created successfully!")
            
            # Verify tables were created
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'epic_fhir_%'
                ORDER BY table_name
            """))
            
            tables = result.fetchall()
            print(f"📋 Created tables: {[table[0] for table in tables]}")
            
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise


async def drop_tables():
    """Drop all Epic FHIR data tables (for testing/cleanup)."""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            # Drop all tables
            await conn.run_sync(Base.metadata.drop_all)
            
            print("🗑️ Epic FHIR data tables dropped successfully!")
            
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        raise


async def check_tables():
    """Check if Epic FHIR data tables exist."""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.begin() as conn:
            # Check if tables exist
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'epic_fhir_%'
                ORDER BY table_name
            """))
            
            tables = result.fetchall()
            
            if tables:
                print(f"✅ Found Epic FHIR tables: {[table[0] for table in tables]}")
            else:
                print("❌ No Epic FHIR tables found")
            
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Epic FHIR Database Management")
    parser.add_argument(
        "action",
        choices=["create", "drop", "check"],
        help="Action to perform"
    )
    
    args = parser.parse_args()
    
    if args.action == "create":
        asyncio.run(create_tables())
    elif args.action == "drop":
        asyncio.run(drop_tables())
    elif args.action == "check":
        asyncio.run(check_tables()) 