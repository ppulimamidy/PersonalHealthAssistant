#!/usr/bin/env python3
"""
Medical Records Database Migration Script
Creates all medical records tables in the database.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from common.config.settings import get_settings
from common.utils.logging import get_logger
from common.models.base import Base

# Import all models to ensure they're registered
from apps.medical_records.models.lab_results_db import LabResultDB
from apps.medical_records.models.documents import DocumentDB, DocumentProcessingLogDB
from apps.medical_records.models.imaging import ImagingStudyDB, MedicalImageDB, DICOMSeriesDB, DICOMInstanceDB
from apps.medical_records.models.clinical_reports import ClinicalReportDB, ReportVersionDB, ReportTemplateDB, ReportCategoryDB, ReportAuditLogDB


logger = get_logger(__name__)
settings = get_settings()


async def create_tables():
    """Create all medical records tables."""
    try:
        logger.info("🏥 Starting Medical Records database migration...")
        
        # Create async engine
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=True,
            pool_pre_ping=True
        )
        
        # Create all tables
        async with engine.begin() as conn:
            logger.info("📋 Creating medical_records schema tables...")
            
            # Create schema if it doesn't exist
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS medical_records"))
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
            logger.info("✅ All medical records tables created successfully!")
        
        # Test connection
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            # Test query
            result = await session.execute(text("SELECT 1"))
            logger.info("✅ Database connection test successful!")
        
        await engine.dispose()
        logger.info("🎉 Medical Records database migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        raise


async def drop_tables():
    """Drop all medical records tables (for testing)."""
    try:
        logger.info("🗑️ Dropping Medical Records tables...")
        
        engine = create_async_engine(settings.DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("✅ All medical records tables dropped successfully!")
        
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Failed to drop tables: {e}")
        raise


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Medical Records Database Migration")
    parser.add_argument("--drop", action="store_true", help="Drop tables instead of creating them")
    args = parser.parse_args()
    
    if args.drop:
        await drop_tables()
    else:
        await create_tables()


if __name__ == "__main__":