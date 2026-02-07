#!/usr/bin/env python3
"""
Database Migration Script for Nutrition Service

This script creates all necessary tables for the nutrition service.
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

def run_migration():
    """Run the database migration for nutrition service."""
    try:
        logger.info("Starting nutrition service database migration...")
        
        # Get database connection
        db_manager = get_db_manager()
        engine = db_manager.create_engine()
        
        # Read migration SQL file
        migration_file = Path(__file__).parent.parent / "migrations" / "create_nutrition_tables.sql"
        
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        logger.info("Executing migration SQL...")
        with engine.connect() as connection:
            connection.execute(text(migration_sql))
            connection.commit()
        
        logger.info("Migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

def verify_tables():
    """Verify that all tables were created successfully."""
    try:
        logger.info("Verifying tables...")
        
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
                        WHERE table_schema = 'public' 
                        AND table_name = '{table_name}'
                    );
                """))
                
                exists = result.fetchone()[0]
                if exists:
                    logger.info(f"✓ Table '{table_name}' exists")
                else:
                    logger.error(f"✗ Table '{table_name}' missing")
                    return False
        
        # Check views
        expected_views = [
            "daily_nutrition_summary",
            "model_performance_summary", 
            "user_recognition_stats"
        ]
        
        with engine.connect() as connection:
            for view_name in expected_views:
                result = connection.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.views 
                        WHERE table_schema = 'public' 
                        AND table_name = '{view_name}'
                    );
                """))
                
                exists = result.fetchone()[0]
                if exists:
                    logger.info(f"✓ View '{view_name}' exists")
                else:
                    logger.error(f"✗ View '{view_name}' missing")
                    return False
        
        logger.info("All tables and views verified successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Table verification failed: {e}")
        return False

def main():
    """Main function to run migration and verification."""
    logger.info("Nutrition Service Database Setup")
    logger.info("=" * 40)
    
    # Run migration
    migration_success = run_migration()
    if not migration_success:
        logger.error("Migration failed. Exiting.")
        sys.exit(1)
    
    # Verify tables
    verification_success = verify_tables()
    if not verification_success:
        logger.error("Table verification failed. Exiting.")
        sys.exit(1)
    
    logger.info("=" * 40)
    logger.info("Nutrition service database setup completed successfully!")
    logger.info("The service is ready to use.")

if __name__ == "__main__":
    main() 