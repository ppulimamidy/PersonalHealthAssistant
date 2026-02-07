#!/usr/bin/env python3
"""
Database Setup Script for Personal Health Assistant
Initializes the Supabase database with schema and initial data.
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

class SupabaseDatabaseSetup:
    def __init__(self):
        # Force reload from .env file, ignoring shell environment variables
        self.db_url = None
        self.supabase_url = None
        self.supabase_service_key = None
        
        # Read directly from .env file
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key == 'DATABASE_URL':
                            self.db_url = value
                        elif key == 'SUPABASE_URL':
                            self.supabase_url = value
                        elif key == 'SUPABASE_SERVICE_ROLE_KEY':
                            self.supabase_service_key = value
        
        if not self.db_url:
            logger.error("❌ DATABASE_URL not found in .env file")
            logger.error("Please run: python scripts/setup_env.py")
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Parse database URL to extract connection details
        # Format: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(self.db_url)
            self.db_host = parsed.hostname
            self.db_port = parsed.port or 5432
            self.db_user = parsed.username
            self.db_password = parsed.password
            self.db_name = parsed.path.lstrip('/')
            
            logger.info(f"📋 Database connection details:")
            logger.info(f"   Host: {self.db_host}")
            logger.info(f"   Port: {self.db_port}")
            logger.info(f"   User: {self.db_user}")
            logger.info(f"   Database: {self.db_name}")
            
        except Exception as e:
            logger.error(f"Failed to parse DATABASE_URL: {e}")
            raise
        
    def test_connection(self):
        """Test connection to Supabase database"""
        try:
            logger.info("Testing connection to Supabase database...")
            
            # Test DNS resolution first
            import socket
            try:
                socket.gethostbyname(self.db_host)
                logger.info(f"✅ DNS resolution successful for {self.db_host}")
            except socket.gaierror as e:
                logger.error(f"❌ DNS resolution failed for {self.db_host}: {e}")
                logger.error("This might mean:")
                logger.error("1. The Supabase project doesn't exist")
                logger.error("2. The project reference is incorrect")
                logger.error("3. You need to check your Supabase dashboard")
                return False
            
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            logger.info(f"✓ Connected to Supabase: {version.split(',')[0]}")
            
            cursor.close()
            conn.close()
            return True
            
        except psycopg2.OperationalError as e:
            if "password authentication failed" in str(e):
                logger.error("❌ Password authentication failed")
                logger.error("Please check your database password in the DATABASE_URL")
                logger.error("The password should be the one you set when creating the Supabase project")
            elif "could not connect to server" in str(e):
                logger.error("❌ Could not connect to database server")
                logger.error("Please check:")
                logger.error("1. Your Supabase project is active")
                logger.error("2. The DATABASE_URL is correct")
                logger.error("3. Your IP is not blocked by Supabase")
            else:
                logger.error(f"❌ Database connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
            return False
    
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
                logger.info("✓ Database schema created successfully!")
            else:
                logger.error("schema.sql file not found!")
                raise FileNotFoundError("schema.sql not found")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creating schema: {e}")
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
            logger.info("✓ Initial data created successfully!")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creating initial data: {e}")
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
                logger.info(f"✓ Table {table}: {count} records")
            
            # Check extensions
            cursor.execute("""
                SELECT extname FROM pg_extension 
                WHERE extname IN ('uuid-ossp', 'pgcrypto', 'vector')
            """)
            extensions = [row[0] for row in cursor.fetchall()]
            logger.info(f"✓ Extensions enabled: {', '.join(extensions)}")
            
            cursor.close()
            conn.close()
            
            logger.info("✓ Database setup verification completed!")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying setup: {e}")
            return False
    
    def run_setup(self):
        """Run the complete database setup"""
        logger.info("🚀 Starting Supabase database setup...")
        
        try:
            # Test connection
            if not self.test_connection():
                raise Exception("Failed to connect to Supabase database")
            
            # Create schema
            self.create_schema()
            
            # Create initial data
            self.create_initial_data()
            
            # Verify setup
            if not self.verify_setup():
                raise Exception("Database setup verification failed")
            
            logger.info("🎉 Supabase database setup completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            raise

def main():
    """Main function"""
    try:
        setup = SupabaseDatabaseSetup()
        setup.run_setup()
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 