#!/usr/bin/env python3
"""
Get Supabase Connection Details
Helps users get the correct database connection string from their Supabase project.
"""

import requests
import json
from dotenv import load_dotenv
import os

def get_supabase_connection_info():
    """Get connection info from Supabase project"""
    
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        print("❌ SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        return None
    
    print("🔍 Getting connection info from Supabase...")
    
    # Extract project reference from URL
    # URL format: https://[project-ref].supabase.co
    project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
    
    print(f"📋 Project Reference: {project_ref}")
    print(f"🌐 Supabase URL: {supabase_url}")
    print(f"🔑 Anon Key: {supabase_anon_key[:20]}...")
    
    # Test the connection
    headers = {
        'apikey': supabase_anon_key,
        'Authorization': f'Bearer {supabase_anon_key}'
    }
    
    try:
        response = requests.get(f"{supabase_url}/rest/v1/", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Supabase connection test successful!")
        else:
            print(f"❌ Supabase connection test failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return None
    
    return {
        'project_ref': project_ref,
        'supabase_url': supabase_url,
        'anon_key': supabase_anon_key
    }

def print_connection_instructions():
    """Print instructions for getting the database connection string"""
    
    print("\n" + "="*60)
    print("SUPABASE DATABASE CONNECTION SETUP")
    print("="*60)
    
    print("\n1. Go to your Supabase project dashboard:")
    print("   https://supabase.com/dashboard")
    
    print("\n2. Select your project")
    
    print("\n3. Go to Settings > Database")
    
    print("\n4. Find the 'Connection string' section")
    
    print("\n5. Copy the 'URI' connection string")
    
    print("\n6. Update your .env file with the correct DATABASE_URL:")
    print("   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres")
    
    print("\n7. Replace [YOUR-PASSWORD] with your actual database password")
    print("   (This is the password you set when creating the project)")
    
    print("\n8. Test the connection:")
    print("   python scripts/test_setup.py")

def test_database_connection(db_url):
    """Test the database connection"""
    try:
        import psycopg2
        print(f"\n🔍 Testing database connection...")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ Database connected successfully!")
        print(f"📋 PostgreSQL version: {version.split(',')[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Supabase Connection Helper")
    print("="*40)
    
    # Get connection info
    info = get_supabase_connection_info()
    if not info:
        print("\n❌ Could not get Supabase connection info")
        print("Please check your .env file and ensure your Supabase project exists.")
        return
    
    # Print instructions
    print_connection_instructions()
    
    # Check if DATABASE_URL is set
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')
    
    if db_url and not db_url.endswith('postgres'):
        print(f"\n🔍 Current DATABASE_URL: {db_url}")
        
        # Test the connection
        if test_database_connection(db_url):
            print("\n🎉 Database connection is working!")
        else:
            print("\n❌ Database connection failed. Please check your DATABASE_URL and password.")
    else:
        print("\n⚠️  DATABASE_URL not configured or using placeholder value")
        print("Please update your .env file with the correct database connection string.")

if __name__ == "__main__":
    main() 