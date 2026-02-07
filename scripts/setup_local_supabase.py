#!/usr/bin/env python3
"""
Local Supabase Setup Script
Sets up a complete local Supabase development environment.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def create_local_env_file():
    """Create .env file for local Supabase"""
    
    env_content = """# Local Supabase Configuration
SUPABASE_URL=http://localhost:8000
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU

# Database URL for Local Supabase
DATABASE_URL=postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:54323/postgres

# Other Services
QDRANT_URL=http://localhost:6333
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Application Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
"""
    
    env_file = Path('.env')
    
    if env_file.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it for local Supabase? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return False
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created for local Supabase!")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def start_local_supabase():
    """Start the local Supabase services"""
    
    print("🐳 Starting local Supabase services...")
    
    try:
        # Start Supabase services
        result = subprocess.run(
            ["docker-compose", "up", "-d", "supabase-db", "supabase-auth", "supabase-rest", "supabase-realtime", "supabase-storage", "supabase-meta", "supabase-mail"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Local Supabase services started!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Supabase services: {e}")
        print(f"Error output: {e.stderr}")
        return False

def wait_for_services():
    """Wait for services to be ready"""
    
    print("⏳ Waiting for services to be ready...")
    
    services = [
        ("Database", "localhost:54323"),
        ("Auth", "localhost:9999"),
        ("REST API", "localhost:3000"),
        ("Realtime", "localhost:4000"),
        ("Storage", "localhost:5000"),
        ("Meta", "localhost:8080"),
    ]
    
    import socket
    import requests
    
    for service_name, address in services:
        host, port = address.split(':')
        port = int(port)
        
        print(f"   Checking {service_name}...")
        
        # Wait up to 60 seconds for each service
        for attempt in range(60):
            try:
                if service_name == "Database":
                    # Test database connection
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    if result == 0:
                        print(f"   ✅ {service_name} is ready!")
                        break
                else:
                    # Test HTTP endpoints
                    response = requests.get(f"http://{address}/health", timeout=1)
                    if response.status_code == 200:
                        print(f"   ✅ {service_name} is ready!")
                        break
            except:
                pass
            
            if attempt < 59:
                time.sleep(1)
        else:
            print(f"   ❌ {service_name} failed to start")
            return False
    
    return True

def test_local_supabase():
    """Test the local Supabase setup"""
    
    print("🧪 Testing local Supabase setup...")
    
    try:
        import requests
        
        # Test REST API
        response = requests.get("http://localhost:3000/", timeout=5)
        if response.status_code == 200:
            print("✅ REST API is working!")
        else:
            print(f"❌ REST API failed: {response.status_code}")
            return False
        
        # Test database connection
        import psycopg2
        conn = psycopg2.connect("postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:54323/postgres")
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ Database connected: {version.split(',')[0]}")
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def print_local_supabase_info():
    """Print information about the local Supabase setup"""
    
    print("\n" + "="*60)
    print("LOCAL SUPABASE SETUP COMPLETE!")
    print("="*60)
    
    print("\n🌐 Service URLs:")
    print("   Database: localhost:54323")
    print("   REST API: http://localhost:3000")
    print("   Auth: http://localhost:9999")
    print("   Realtime: http://localhost:4000")
    print("   Storage: http://localhost:5000")
    print("   Meta: http://localhost:8080")
    print("   Mail: localhost:2500")
    
    print("\n🔑 API Keys:")
    print("   Anon Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0")
    print("   Service Role Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU")
    
    print("\n📊 Database Connection:")
    print("   URL: postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:54323/postgres")
    
    print("\n🚀 Next Steps:")
    print("   1. Run: python scripts/test_setup.py")
    print("   2. Run: python scripts/setup/db_setup.py")
    print("   3. Start developing your application!")
    
    print("\n🛠️  Management Commands:")
    print("   Start services: docker-compose up -d")
    print("   Stop services: docker-compose down")
    print("   View logs: docker-compose logs -f")
    print("   Reset data: docker-compose down -v && docker-compose up -d")

def main():
    """Main function"""
    print("🚀 Local Supabase Setup")
    print("="*30)
    
    # Check if we're in the right directory
    if not Path('schema.sql').exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Create environment file
    if not create_local_env_file():
        sys.exit(1)
    
    # Start services
    if not start_local_supabase():
        print("\n❌ Failed to start Supabase services")
        print("Please check Docker is running and try again")
        sys.exit(1)
    
    # Wait for services
    if not wait_for_services():
        print("\n❌ Some services failed to start")
        print("Check the logs with: docker-compose logs")
        sys.exit(1)
    
    # Test setup
    if not test_local_supabase():
        print("\n❌ Local Supabase test failed")
        sys.exit(1)
    
    # Print info
    print_local_supabase_info()

if __name__ == "__main__":
    main() 