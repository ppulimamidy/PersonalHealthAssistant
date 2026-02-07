#!/usr/bin/env python3
"""
Kubernetes Schema Setup for Personal Health Assistant
Sets up the database schema in the Kubernetes PostgreSQL instance
"""

import os
import sys
import psycopg2
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KubernetesSchemaSetup:
    def __init__(self):
        # Kubernetes database connection details
        self.db_host = "postgres-db"
        self.db_port = 5432
        self.db_name = "health_assistant"
        self.db_user = "postgres"
        self.db_password = "your-super-secret-and-long-postgres-password"
        
        self.connection_string = f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        
    def test_connection(self):
        """Test connection to Kubernetes database"""
        try:
            logger.info("Testing connection to Kubernetes PostgreSQL database...")
            
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            logger.info(f"✅ Connected to database: {version.split(',')[0]}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def execute_schema_file(self, file_path: Path):
        """Execute a schema file"""
        try:
            logger.info(f"Executing schema file: {file_path.name}")
            
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Read and execute SQL file
            with open(file_path, 'r') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
            
            for i, statement in enumerate(statements):
                try:
                    cursor.execute(statement)
                    if i % 10 == 0:  # Log progress every 10 statements
                        logger.info(f"  Executed {i+1}/{len(statements)} statements")
                except Exception as e:
                    logger.warning(f"  Statement {i+1} failed (continuing): {e}")
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"✅ Completed: {file_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to execute {file_path.name}: {e}")
            return False
    
    def setup_schema(self):
        """Set up complete database schema"""
        logger.info("🚀 Starting schema setup for Kubernetes database...")
        
        # Test connection first
        if not self.test_connection():
            return False
        
        # Get schema files in order
        schema_dir = project_root / "scripts" / "setup" / "extensions"
        schema_files = [
            schema_dir / "01_extensions.sql",
            schema_dir / "01_pgvector.sql",
            schema_dir / "02_auth_setup.sql",
            project_root / "schema.sql",
            project_root / "auth_setup.sql",
            project_root / "rls_policies.sql"
        ]
        
        # Execute schema files in order
        for schema_file in schema_files:
            if schema_file.exists():
                if not self.execute_schema_file(schema_file):
                    logger.warning(f"⚠️  Schema file {schema_file.name} had issues, continuing...")
            else:
                logger.warning(f"⚠️  Schema file {schema_file.name} not found, skipping...")
        
        logger.info("✅ Schema setup completed!")
        return True
    
    def verify_schema(self):
        """Verify that schema was set up correctly"""
        try:
            logger.info("🔍 Verifying schema setup...")
            
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            verification_results = {}
            
            # Check if key tables exist
            key_tables = [
                'auth.users', 'public.user_profiles', 'public.health_metrics',
                'public.devices', 'public.medical_conditions', 'public.medications'
            ]
            
            for table in key_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    verification_results[table] = {"exists": True, "count": count}
                except Exception as e:
                    verification_results[table] = {"exists": False, "error": str(e)}
            
            # Check if extensions are enabled
            cursor.execute("SELECT extname FROM pg_extension")
            extensions = cursor.fetchall()
            verification_results["extensions"] = [ext[0] for ext in extensions]
            
            # Check if schemas exist
            cursor.execute("SELECT schema_name FROM information_schema.schemata")
            schemas = cursor.fetchall()
            verification_results["schemas"] = [schema[0] for schema in schemas]
            
            cursor.close()
            conn.close()
            
            logger.info("✅ Schema verification completed!")
            return verification_results
            
        except Exception as e:
            logger.error(f"❌ Schema verification failed: {e}")
            return {"error": str(e)}


def print_verification_results(results):
    """Print verification results in a readable format"""
    print("\n" + "="*60)
    print("SCHEMA VERIFICATION RESULTS")
    print("="*60)
    
    if "error" in results:
        print(f"❌ Verification failed: {results['error']}")
        return
    
    # Check tables
    print("\n📋 Table Status:")
    for table, status in results.items():
        if isinstance(status, dict) and "exists" in status:
            if status["exists"]:
                print(f"  ✅ {table}: {status['count']} records")
            else:
                print(f"  ❌ {table}: {status['error']}")
    
    # Check extensions
    if "extensions" in results:
        print(f"\n🔧 Extensions ({len(results['extensions'])}):")
        for ext in results["extensions"]:
            print(f"  ✅ {ext}")
    
    # Check schemas
    if "schemas" in results:
        print(f"\n🗂️  Schemas ({len(results['schemas'])}):")
        for schema in results["schemas"]:
            print(f"  ✅ {schema}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Kubernetes Schema Setup")
    parser.add_argument("--verify-only", action="store_true", 
                       help="Only verify existing schema")
    
    args = parser.parse_args()
    
    setup = KubernetesSchemaSetup()
    
    if args.verify_only:
        results = setup.verify_schema()
        print_verification_results(results)
    else:
        success = setup.setup_schema()
        if success:
            results = setup.verify_schema()
            print_verification_results(results)


if __name__ == "__main__":
    main() 