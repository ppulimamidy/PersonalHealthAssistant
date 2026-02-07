#!/usr/bin/env python3
"""
Test Setup Script for Personal Health Assistant
Verifies that all components are working correctly with Supabase.
"""

import os
import sys
import time
import requests
import psycopg2
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
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

class SystemTester:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.db_url = os.getenv('DATABASE_URL')
        self.qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
        self.kafka_bootstrap = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.test_results = {}
        
    def test_supabase_connection(self) -> bool:
        """Test Supabase connection and basic operations"""
        try:
            logger.info("Testing Supabase connection...")
            
            if not self.supabase_url or not self.supabase_anon_key:
                logger.error("❌ Supabase URL or Anon Key not configured")
                self.test_results['supabase'] = False
                return False
            
            # Test Supabase health check
            headers = {
                'apikey': self.supabase_anon_key,
                'Authorization': f'Bearer {self.supabase_anon_key}'
            }
            
            # Test basic health check
            response = requests.get(f"{self.supabase_url}/rest/v1/", headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info("✓ Supabase REST API is responding")
                
                # Test if we can query the database
                response = requests.get(
                    f"{self.supabase_url}/rest/v1/user_profiles?select=count",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code in [200, 404]:  # 404 is ok if table doesn't exist yet
                    logger.info("✓ Supabase database queries work")
                    self.test_results['supabase'] = True
                    return True
                else:
                    logger.error(f"❌ Supabase database query failed: {response.status_code}")
                    self.test_results['supabase'] = False
                    return False
            else:
                logger.error(f"❌ Supabase health check failed: {response.status_code}")
                self.test_results['supabase'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Supabase test failed: {e}")
            self.test_results['supabase'] = False
            return False
    
    def test_database_connection(self) -> bool:
        """Test direct database connection and basic operations"""
        try:
            logger.info("Testing direct database connection...")
            
            if not self.db_url:
                logger.error("❌ DATABASE_URL not configured")
                self.test_results['database'] = False
                return False
            
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            logger.info(f"✓ Database connected: {version.split(',')[0]}")
            
            # Test if key tables exist
            tables_to_check = [
                "auth.users",
                "public.user_profiles",
                "public.health_metrics",
                "public.device_data_types"
            ]
            
            for table in tables_to_check:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    logger.info(f"✓ Table {table}: {count} records")
                except psycopg2.Error as e:
                    logger.warning(f"⚠ Table {table} not found or not accessible: {e}")
            
            # Test extensions
            cursor.execute("""
                SELECT extname FROM pg_extension 
                WHERE extname IN ('uuid-ossp', 'pgcrypto', 'vector')
            """)
            extensions = [row[0] for row in cursor.fetchall()]
            logger.info(f"✓ Extensions enabled: {', '.join(extensions)}")
            
            cursor.close()
            conn.close()
            
            self.test_results['database'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Database test failed: {e}")
            self.test_results['database'] = False
            return False
    
    def test_qdrant_connection(self) -> bool:
        """Test Qdrant vector database connection"""
        try:
            logger.info("Testing Qdrant connection...")
            
            # Test basic health check
            response = requests.get(f"{self.qdrant_url}/collections", timeout=5)
            if response.status_code == 200:
                logger.info("✓ Qdrant is responding")
                
                # Test collection creation
                test_collection = {
                    "name": "test_collection",
                    "vectors": {
                        "size": 1536,
                        "distance": "Cosine"
                    }
                }
                
                response = requests.put(
                    f"{self.qdrant_url}/collections/test_collection",
                    json=test_collection,
                    timeout=5
                )
                
                if response.status_code in [200, 201]:
                    logger.info("✓ Qdrant collection creation works")
                    
                    # Clean up test collection
                    requests.delete(f"{self.qdrant_url}/collections/test_collection", timeout=5)
                    
                    self.test_results['qdrant'] = True
                    return True
                else:
                    logger.error(f"❌ Qdrant collection creation failed: {response.status_code}")
                    self.test_results['qdrant'] = False
                    return False
            else:
                logger.error(f"❌ Qdrant health check failed: {response.status_code}")
                self.test_results['qdrant'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Qdrant test failed: {e}")
            self.test_results['qdrant'] = False
            return False
    
    def test_kafka_connection(self) -> bool:
        """Test Kafka connection and basic operations"""
        try:
            logger.info("Testing Kafka connection...")
            
            # Import kafka modules
            from kafka import KafkaProducer, KafkaConsumer
            from kafka.errors import KafkaError
            
            # Test producer
            producer = KafkaProducer(
                bootstrap_servers=[self.kafka_bootstrap],
                value_serializer=lambda x: x.encode('utf-8'),
                request_timeout_ms=5000
            )
            
            # Send test message
            future = producer.send('test_topic', value='test_message')
            producer.flush()
            
            # Check if message was sent successfully
            try:
                record_metadata = future.get(timeout=10)
                logger.info(f"✓ Kafka producer works: {record_metadata}")
            except KafkaError as e:
                logger.error(f"❌ Kafka producer failed: {e}")
                self.test_results['kafka'] = False
                return False
            
            # Test consumer
            consumer = KafkaConsumer(
                'test_topic',
                bootstrap_servers=[self.kafka_bootstrap],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='test_group',
                value_deserializer=lambda x: x.decode('utf-8'),
                request_timeout_ms=5000
            )
            
            # Wait for message
            message_count = 0
            start_time = time.time()
            while message_count == 0 and time.time() - start_time < 10:
                messages = consumer.poll(timeout_ms=1000)
                for tp, records in messages.items():
                    for record in records:
                        message_count += 1
                        logger.info(f"✓ Kafka consumer received: {record.value}")
            
            consumer.close()
            producer.close()
            
            if message_count > 0:
                self.test_results['kafka'] = True
                return True
            else:
                logger.error("❌ Kafka consumer didn't receive message")
                self.test_results['kafka'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Kafka test failed: {e}")
            self.test_results['kafka'] = False
            return False
    
    def test_docker_services(self) -> bool:
        """Test if Docker services are running"""
        try:
            logger.info("Testing Docker services...")
            
            import subprocess
            
            # Check if docker-compose services are running
            result = subprocess.run(
                ['docker-compose', 'ps'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                services = ['postgres', 'qdrant', 'kafka', 'zookeeper']
                running_services = []
                
                for line in result.stdout.split('\n'):
                    for service in services:
                        if service in line and 'Up' in line:
                            running_services.append(service)
                
                logger.info(f"✓ Running services: {', '.join(running_services)}")
                
                if len(running_services) >= 3:  # At least postgres, qdrant, and kafka
                    self.test_results['docker'] = True
                    return True
                else:
                    logger.error(f"❌ Not all services are running. Found: {running_services}")
                    self.test_results['docker'] = False
                    return False
            else:
                logger.error(f"❌ Docker-compose check failed: {result.stderr}")
                self.test_results['docker'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Docker services test failed: {e}")
            self.test_results['docker'] = False
            return False
    
    def test_python_environment(self) -> bool:
        """Test Python environment and dependencies"""
        try:
            logger.info("Testing Python environment...")
            
            # Test key imports
            import fastapi
            import uvicorn
            import sqlalchemy
            import psycopg2
            import redis
            import duckdb
            import qdrant_client
            import langchain
            
            logger.info("✓ All key dependencies imported successfully")
            
            # Test Python version
            import sys
            python_version = sys.version_info
            if python_version.major == 3 and python_version.minor >= 9:
                logger.info(f"✓ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
                self.test_results['python'] = True
                return True
            else:
                logger.error(f"❌ Python version too old: {python_version}")
                self.test_results['python'] = False
                return False
                
        except ImportError as e:
            logger.error(f"❌ Missing dependency: {e}")
            self.test_results['python'] = False
            return False
        except Exception as e:
            logger.error(f"❌ Python environment test failed: {e}")
            self.test_results['python'] = False
            return False
    
    def test_file_structure(self) -> bool:
        """Test if required files and directories exist"""
        try:
            logger.info("Testing file structure...")
            
            required_files = [
                "schema.sql",
                "requirements.txt",
                "docker-compose.yml",
                ".env"
            ]
            
            required_dirs = [
                "apps",
                "common",
                "tests",
                "docs",
                "scripts"
            ]
            
            missing_files = []
            missing_dirs = []
            
            for file in required_files:
                if not Path(file).exists():
                    missing_files.append(file)
                else:
                    logger.info(f"✓ File exists: {file}")
            
            for dir in required_dirs:
                if not Path(dir).exists():
                    missing_dirs.append(dir)
                else:
                    logger.info(f"✓ Directory exists: {dir}")
            
            if missing_files or missing_dirs:
                logger.error(f"❌ Missing files: {missing_files}")
                logger.error(f"❌ Missing directories: {missing_dirs}")
                self.test_results['files'] = False
                return False
            else:
                self.test_results['files'] = True
                return True
                
        except Exception as e:
            logger.error(f"❌ File structure test failed: {e}")
            self.test_results['files'] = False
            return False
    
    def test_environment_variables(self) -> bool:
        """Test if required environment variables are set"""
        try:
            logger.info("Testing environment variables...")
            
            required_vars = [
                "SUPABASE_URL",
                "SUPABASE_ANON_KEY",
                "DATABASE_URL",
                "QDRANT_URL",
                "KAFKA_BOOTSTRAP_SERVERS"
            ]
            
            optional_vars = [
                "SUPABASE_SERVICE_ROLE_KEY",
                "JWT_SECRET_KEY",
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY"
            ]
            
            missing_required = []
            missing_optional = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_required.append(var)
                else:
                    logger.info(f"✓ Required env var: {var}")
            
            for var in optional_vars:
                if not os.getenv(var):
                    missing_optional.append(var)
                else:
                    logger.info(f"✓ Optional env var: {var}")
            
            if missing_required:
                logger.error(f"❌ Missing required env vars: {missing_required}")
                self.test_results['env'] = False
                return False
            
            if missing_optional:
                logger.warning(f"⚠ Missing optional env vars: {missing_optional}")
            
            self.test_results['env'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Environment variables test failed: {e}")
            self.test_results['env'] = False
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        logger.info("🚀 Starting comprehensive system test...")
        
        tests = [
            ("Python Environment", self.test_python_environment),
            ("File Structure", self.test_file_structure),
            ("Environment Variables", self.test_environment_variables),
            ("Docker Services", self.test_docker_services),
            ("Supabase Connection", self.test_supabase_connection),
            ("Database Connection", self.test_database_connection),
            ("Qdrant Connection", self.test_qdrant_connection),
            ("Kafka Connection", self.test_kafka_connection),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                test_func()
            except Exception as e:
                logger.error(f"❌ {test_name} test crashed: {e}")
                self.test_results[test_name.lower().replace(' ', '_')] = False
        
        return self.test_results
    
    def print_summary(self):
        """Print test results summary"""
        logger.info(f"\n{'='*60}")
        logger.info("TEST RESULTS SUMMARY")
        logger.info(f"{'='*60}")
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name.replace('_', ' ').title():<25} {status}")
            if result:
                passed += 1
        
        logger.info(f"\n{'='*60}")
        logger.info(f"OVERALL: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! System is ready for development.")
        else:
            logger.info("⚠️  Some tests failed. Please check the errors above.")
        
        logger.info(f"{'='*60}")
        
        return passed == total

def main():
    """Main function"""
    try:
        tester = SystemTester()
        tester.run_all_tests()
        success = tester.print_summary()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 