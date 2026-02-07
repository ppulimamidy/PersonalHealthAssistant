#!/usr/bin/env python3
"""
Local Database Setup Script
Sets up a local PostgreSQL database for development while Supabase connection is being resolved.
"""

import os
import sys
import time
import psycopg2
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LocalDatabaseSetup:
    def __init__(self):
        self.db_url = "postgresql://postgres:postgres@localhost:5432/health_assistant"
        self.db_host = "localhost"
        self.db_port = "5432"
        self.db_user = "postgres"
        self.db_password = "postgres"
        self.db_name = "health_assistant"
        
    def wait_for_database(self, max_retries=30):
        """Wait for database to be ready"""
        logger.info("Waiting for local database to be ready...")
        
        for attempt in range(max_retries):
            try:
                conn = psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port,
                    user=self.db_user,
                    password=self.db_password,
                    database='postgres'
                )
                conn.close()
                logger.info("✅ Local database is ready!")
                return True
            except psycopg2.OperationalError as e:
                logger.info(f"Database not ready yet (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2)
        
        logger.error("❌ Local database failed to start within expected time")
        return False
    
    def create_database(self):
        """Create the health_assistant database if it doesn't exist"""
        try:
            # Connect to default postgres database
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database='postgres'
            )
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (self.db_name,))
            exists = cursor.fetchone()
            
            if not exists:
                logger.info(f"Creating database '{self.db_name}'...")
                cursor.execute(f"CREATE DATABASE {self.db_name}")
                logger.info(f"✅ Database '{self.db_name}' created successfully!")
            else:
                logger.info(f"✅ Database '{self.db_name}' already exists")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error creating database: {e}")
            raise
    
    def create_schema(self):
        """Create database schema from schema.sql"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Read and execute schema.sql
            schema_file = project_root / "schema.sql"
            if schema_file.exists():
                logger.info("Creating database schema...")
                with open(schema_file, 'r') as f:
                    schema_sql = f.read()
                
                # Split by semicolon and execute each statement
                statements = schema_sql.split(';')
                for statement in statements:
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            cursor.execute(statement)
                        except Exception as e:
                            logger.warning(f"Statement failed (continuing): {e}")
                
                conn.commit()
                logger.info("✅ Database schema created successfully!")
            else:
                logger.error("❌ schema.sql file not found!")
                raise FileNotFoundError("schema.sql not found")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error creating schema: {e}")
            raise
    
    def create_initial_data(self):
        """Create initial data and seed the database"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            logger.info("Creating initial data...")
            
            # Create default device data types
            device_data_types = [
                ("HEART_RATE", "VITALS", "BPM", "Heart rate measurements"),
                ("BLOOD_PRESSURE", "VITALS", "mmHg", "Blood pressure readings"),
                ("BLOOD_OXYGEN", "VITALS", "%", "Blood oxygen saturation"),
                ("TEMPERATURE", "VITALS", "°C", "Body temperature"),
                ("STEPS", "ACTIVITY", "count", "Step count"),
                ("CALORIES", "ACTIVITY", "kcal", "Calories burned"),
                ("DISTANCE", "ACTIVITY", "m", "Distance traveled"),
                ("SLEEP_DURATION", "SLEEP", "minutes", "Sleep duration"),
                ("SLEEP_QUALITY", "SLEEP", "score", "Sleep quality score"),
                ("WEIGHT", "BODY", "kg", "Body weight"),
                ("BODY_FAT", "BODY", "%", "Body fat percentage"),
                ("MUSCLE_MASS", "BODY", "kg", "Muscle mass"),
                ("WATER_INTAKE", "NUTRITION", "ml", "Water intake"),
                ("GLUCOSE", "METABOLIC", "mg/dL", "Blood glucose level"),
                ("CHOLESTEROL", "METABOLIC", "mg/dL", "Cholesterol level"),
            ]
            
            for name, category, unit, description in device_data_types:
                cursor.execute("""
                    INSERT INTO public.device_data_types (name, category, unit, description)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (name) DO NOTHING
                """, (name, category, unit, description))
            
            # Create default healthcare facilities
            facilities = [
                ("General Hospital", "HOSPITAL", "123 Main St, City, State", "555-0123"),
                ("City Clinic", "CLINIC", "456 Oak Ave, City, State", "555-0456"),
                ("Specialty Medical Center", "SPECIALTY", "789 Pine Rd, City, State", "555-0789"),
            ]
            
            for name, type, address, contact in facilities:
                cursor.execute("""
                    INSERT INTO public.healthcare_facilities (name, type, address, contact_info)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (name, type, address, contact))
            
            # Create default insurance companies
            insurance_companies = [
                ("HealthFirst Insurance", "555-1000"),
                ("WellCare Insurance", "555-2000"),
                ("MediShield Insurance", "555-3000"),
            ]
            
            for name, contact in insurance_companies:
                cursor.execute("""
                    INSERT INTO public.insurance_companies (name, contact_info)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (name, contact))
            
            conn.commit()
            logger.info("✅ Initial data created successfully!")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error creating initial data: {e}")
            raise
    
    def verify_setup(self):
        """Verify that the setup was successful"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            logger.info("Verifying database setup...")
            
            # Check if key tables exist
            tables_to_check = [
                "auth.users",
                "public.user_profiles",
                "public.health_metrics",
                "public.device_data_types",
                "public.healthcare_facilities",
                "public.insurance_companies"
            ]
            
            for table in tables_to_check:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"✅ Table {table}: {count} records")
            
            # Check extensions
            cursor.execute("""
                SELECT extname FROM pg_extension 
                WHERE extname IN ('uuid-ossp', 'pgcrypto', 'vector')
            """)
            extensions = [row[0] for row in cursor.fetchall()]
            logger.info(f"✅ Extensions enabled: {', '.join(extensions)}")
            
            cursor.close()
            conn.close()
            
            logger.info("✅ Database setup verification completed!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verifying setup: {e}")
            return False
    
    def run_setup(self):
        """Run the complete database setup"""
        logger.info("🚀 Starting local database setup...")
        
        try:
            # Wait for database to be ready
            if not self.wait_for_database():
                raise Exception("Local database failed to start")
            
            # Create database
            self.create_database()
            
            # Create schema
            self.create_schema()
            
            # Create initial data
            self.create_initial_data()
            
            # Verify setup
            if not self.verify_setup():
                raise Exception("Database setup verification failed")
            
            logger.info("🎉 Local database setup completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            raise

def main():
    """Main function"""
    try:
        setup = LocalDatabaseSetup()
        setup.run_setup()
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 