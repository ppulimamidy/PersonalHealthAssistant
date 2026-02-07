#!/usr/bin/env python3
"""
Wake Up Supabase Database
Helps wake up a sleeping Supabase database and get the correct connection string.
"""

import requests
import json
from dotenv import load_dotenv
import os
import time

def wake_up_database():
    """Try to wake up the database by making API calls"""
    
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        print("❌ SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        return False
    
    print("🔍 Attempting to wake up the database...")
    
    headers = {
        'apikey': supabase_anon_key,
        'Authorization': f'Bearer {supabase_anon_key}',
        'Content-Type': 'application/json'
    }
    
    # Try different API endpoints to wake up the database
    endpoints = [
        "/rest/v1/",
        "/rest/v1/rpc/",
        "/auth/v1/",
        "/storage/v1/",
    ]
    
    for endpoint in endpoints:
        try:
            print(f"   Trying {endpoint}...")
            response = requests.get(f"{supabase_url}{endpoint}", headers=headers, timeout=10)
            print(f"   Response: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ {endpoint} is responding")
            elif response.status_code == 404:
                print(f"   ⚠️  {endpoint} not found (this is normal)")
            else:
                print(f"   ❌ {endpoint} failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {endpoint} error: {e}")
    
    return True

def test_database_connection_with_retry():
    """Test database connection with multiple retries"""
    
    print("\n🔄 Testing database connection with retries...")
    
    for attempt in range(5):
        print(f"\n   Attempt {attempt + 1}/5...")
        
        try:
            import psycopg2
            
            load_dotenv()
            db_url = None
            
            # Read DATABASE_URL directly from .env file
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        db_url = line.split('=', 1)[1].strip()
                        break
            
            if not db_url:
                print("   ❌ DATABASE_URL not found in .env file")
                return False
            
            print(f"   Connecting to: {db_url.split('@')[1] if '@' in db_url else 'unknown'}")
            
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"   ✅ Connected successfully!")
            print(f"   📋 PostgreSQL version: {version.split(',')[0]}")
            
            cursor.close()
            conn.close()
            return True
            
        except psycopg2.OperationalError as e:
            error_msg = str(e)
            print(f"   ❌ Connection failed: {error_msg}")
            
            if "could not connect to server" in error_msg:
                print("   💡 Database might be sleeping or initializing...")
            elif "password authentication failed" in error_msg:
                print("   💡 Check your database password")
            elif "Tenant or user not found" in error_msg:
                print("   💡 Project might not be set up correctly")
            
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
        
        if attempt < 4:
            print(f"   ⏳ Waiting 10 seconds before retry...")
            time.sleep(10)
    
    return False

def print_manual_setup_instructions():
    """Print manual setup instructions"""
    
    load_dotenv()
    supabase_url = os.getenv('SUPABASE_URL')
    
    if supabase_url:
        project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
    else:
        project_ref = "YOUR_PROJECT_REF"
    
    print("\n" + "="*70)
    print("MANUAL SETUP INSTRUCTIONS")
    print("="*70)
    
    print(f"\n1. Open your Supabase dashboard:")
    print(f"   https://supabase.com/dashboard/project/{project_ref}")
    
    print(f"\n2. Go to the SQL Editor (left sidebar)")
    
    print(f"\n3. Run a simple query to wake up the database:")
    print(f"   SELECT 1;")
    
    print(f"\n4. Wait for the query to complete")
    
    print(f"\n5. Go to Settings > Database")
    
    print(f"\n6. Copy the exact connection string from 'Connection string' section")
    
    print(f"\n7. Update your .env file with the exact string")
    
    print(f"\n8. Test the connection:")
    print(f"   python scripts/test_setup.py")

def main():
    """Main function"""
    print("🌅 Supabase Database Wake-Up Script")
    print("="*45)
    
    # Wake up the database
    if not wake_up_database():
        print("\n❌ Failed to wake up database")
        return
    
    # Wait a moment
    print("\n⏳ Waiting 5 seconds for database to wake up...")
    time.sleep(5)
    
    # Test connection with retries
    if test_database_connection_with_retry():
        print("\n🎉 Database connection successful!")
        print("You can now run: python scripts/setup/db_setup.py")
    else:
        print("\n❌ Database connection failed after all retries")
        print_manual_setup_instructions()

if __name__ == "__main__":
    main() 