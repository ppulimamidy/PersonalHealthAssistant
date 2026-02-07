#!/usr/bin/env python3
"""
Database Migration Script for Nutrition Service

This script creates all necessary tables for the nutrition service in the existing database.
"""

import os
import sys
import logging
from pathlib import Path
from sqlalchemy import text

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.database.connection import get_db_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_nutrition_tables():
    """Create nutrition tables in the existing database."""
    try:
        logger.info("Starting nutrition service database migration...")
        
        # Get database connection
        db_manager = get_db_manager()
        
        # Convert async URL to sync URL for migration
        async_url = db_manager.get_database_url()
        sync_url = async_url.replace('postgresql+asyncpg://', 'postgresql://')
        
        # Create sync engine for migration
        from sqlalchemy import create_engine
        engine = create_engine(sync_url)
        
        # Read migration SQL file
        migration_file = Path(__file__).parent / "migrations" / "create_nutrition_tables.sql"
        
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        logger.info("Executing nutrition schema migration...")
        with engine.connect() as connection:
            # Create schema if it doesn't exist
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS nutrition"))
            connection.commit()
            
            # Execute the migration SQL
            connection.execute(text(migration_sql))
            connection.commit()
        
        logger.info("Nutrition schema migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

def verify_nutrition_tables():
    """Verify that all nutrition tables were created successfully."""
    try:
        logger.info("Verifying nutrition tables...")
        
        db_manager = get_db_manager()
        engine = db_manager.create_engine()
        
        # List of expected tables
        expected_tables = [
            "food_recognition_results",
            "user_corrections", 
            "meal_logs",
            "nutrition_goals",
            "food_database",
            "model_performance",
            "user_preferences"
        ]
        
        # Check each table
        with engine.connect() as connection:
            for table_name in expected_tables:
                result = connection.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'nutrition' 
                        AND table_name = '{table_name}'
                    );
                """))
                
                exists = result.fetchone()[0]
                if exists:
                    logger.info(f"✓ Table 'nutrition.{table_name}' exists")
                else:
                    logger.error(f"✗ Table 'nutrition.{table_name}' missing")
                    return False
        
        # Check views
        expected_views = [
            "daily_nutrition_summary",
            "model_performance_summary", 
            "user_recognition_stats"
        ]
        
        for view_name in expected_views:
            result = connection.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.views 
                    WHERE table_schema = 'nutrition' 
                    AND table_name = '{view_name}'
                );
            """))
            
            exists = result.fetchone()[0]
            if exists:
                logger.info(f"✓ View 'nutrition.{view_name}' exists")
            else:
                logger.error(f"✗ View 'nutrition.{view_name}' missing")
                return False
        
        logger.info("✅ All nutrition tables and views verified successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False

def main():
    """Main migration function."""
    logger.info("🚀 Starting Nutrition Service Database Migration")
    
    # Create tables
    if not create_nutrition_tables():
        logger.error("❌ Failed to create nutrition tables")
        sys.exit(1)
    
    # Verify tables
    if not verify_nutrition_tables():
        logger.error("❌ Failed to verify nutrition tables")
        sys.exit(1)
    
    logger.info("🎉 Nutrition Service Database Migration Completed Successfully!")

if __name__ == "__main__":
    print("🚀 Starting Nutrition Service Database Migration")
    success = create_nutrition_tables()
    if success:
        print("✅ Nutrition tables created successfully!")
    else:
        print("❌ Failed to create nutrition tables")
        sys.exit(1) 