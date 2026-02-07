#!/usr/bin/env python3
"""
Get Exact Supabase Connection String
Helps users get the exact database connection string from their Supabase dashboard.
"""

import requests
import json
from dotenv import load_dotenv
import os
from pathlib import Path

def test_supabase_api():
    """Test if Supabase API is working"""
    
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        print("❌ SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        return False
    
    print("🔍 Testing Supabase API connection...")
    
    headers = {
        'apikey': supabase_anon_key,
        'Authorization': f'Bearer {supabase_anon_key}'
    }
    
    try:
        response = requests.get(f"{supabase_url}/rest/v1/", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Supabase API is working!")
            return True
        else:
            print(f"❌ Supabase API test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to Supabase API: {e}")
        return False

def print_dashboard_instructions():
    """Print instructions for getting the exact connection string"""
    
    load_dotenv()
    supabase_url = os.getenv('SUPABASE_URL')
    
    if supabase_url:
        project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
    else:
        project_ref = "YOUR_PROJECT_REF"
    
    print("\n" + "="*70)
    print("GETTING THE EXACT DATABASE CONNECTION STRING")
    print("="*70)
    
    print(f"\n1. Open your Supabase dashboard:")
    print(f"   https://supabase.com/dashboard/project/{project_ref}")
    
    print(f"\n2. Click on 'Settings' in the left sidebar")
    
    print(f"\n3. Click on 'Database' in the settings menu")
    
    print(f"\n4. Scroll down to 'Connection string' section")
    
    print(f"\n5. Look for 'URI' connection string")
    print(f"   It should look like one of these formats:")
    print(f"   - postgresql://postgres:[YOUR-PASSWORD]@db.{project_ref}.supabase.co:5432/postgres")
    print(f"   - postgresql://postgres:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres")
    print(f"   - postgresql://postgres:[YOUR-PASSWORD]@aws-0-[region].supabase.com:5432/postgres")
    
    print(f"\n6. Copy the EXACT connection string")
    
    print(f"\n7. Update your .env file with the exact string")
    print(f"   Replace the current DATABASE_URL line")
    
    print(f"\n8. Make sure to replace [YOUR-PASSWORD] with your actual password")
    
    print(f"\n9. Test the connection:")
    print(f"   python scripts/test_setup.py")

def check_current_connection():
    """Check the current connection string and suggest improvements"""
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        return
    
    print(f"\n📋 Current DATABASE_URL in .env file:")
    print("-" * 50)
    
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                print(line.strip())
                break
    
    print(f"\n🔍 Analysis:")
    
    # Read the DATABASE_URL
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL not found in .env file")
        return
    
    # Parse the URL
    try:
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        
        print(f"   Host: {parsed.hostname}")
        print(f"   Port: {parsed.port}")
        print(f"   User: {parsed.username}")
        print(f"   Database: {parsed.path.lstrip('/')}")
        
        # Check for common issues
        if parsed.hostname and 'supabase.co' in parsed.hostname:
            if parsed.hostname.startswith('db.'):
                print(f"   ✅ Using direct database hostname")
            elif 'pooler' in parsed.hostname:
                print(f"   ✅ Using connection pooler")
            else:
                print(f"   ✅ Using standard Supabase hostname")
        else:
            print(f"   ❌ Hostname doesn't look like Supabase")
            
    except Exception as e:
        print(f"   ❌ Error parsing DATABASE_URL: {e}")

def try_alternative_hostnames():
    """Try alternative hostname formats"""
    
    load_dotenv()
    supabase_url = os.getenv('SUPABASE_URL')
    
    if not supabase_url:
        print("❌ SUPABASE_URL not found")
        return
    
    project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
    
    print(f"\n🔍 Trying alternative hostname formats...")
    
    # Common Supabase hostname patterns
    hostname_patterns = [
        f"db.{project_ref}.supabase.co",
        f"aws-0-us-east-1.pooler.supabase.com",
        f"aws-0-us-west-1.pooler.supabase.com",
        f"aws-0-eu-west-1.pooler.supabase.com",
        f"aws-0-ap-southeast-1.pooler.supabase.com",
        f"aws-0-us-east-1.supabase.com",
        f"aws-0-us-west-1.supabase.com",
        f"aws-0-eu-west-1.supabase.com",
        f"aws-0-ap-southeast-1.supabase.com",
    ]
    
    import socket
    
    for hostname in hostname_patterns:
        try:
            socket.gethostbyname(hostname)
            print(f"   ✅ {hostname} - RESOLVES")
        except socket.gaierror:
            print(f"   ❌ {hostname} - FAILS")

def main():
    """Main function"""
    print("🔧 Supabase Database Connection Troubleshooter")
    print("="*55)
    
    # Test API connection
    if not test_supabase_api():
        print("\n❌ Cannot connect to Supabase API")
        print("Please check your SUPABASE_URL and SUPABASE_ANON_KEY")
        return
    
    # Check current connection
    check_current_connection()
    
    # Try alternative hostnames
    try_alternative_hostnames()
    
    # Print instructions
    print_dashboard_instructions()
    
    print(f"\n" + "="*70)
    print("TROUBLESHOOTING TIPS:")
    print("="*70)
    print(f"\n1. If DNS resolution fails, try:")
    print(f"   - Wait 5-10 minutes for DNS propagation")
    print(f"   - Try from a different network")
    print(f"   - Use a VPN or mobile hotspot")
    
    print(f"\n2. If the project is new:")
    print(f"   - The database might be initializing")
    print(f"   - Try again in a few minutes")
    
    print(f"\n3. If you're on free tier:")
    print(f"   - The database might be sleeping")
    print(f"   - Visit the dashboard to wake it up")
    
    print(f"\n4. Alternative connection methods:")
    print(f"   - Use the connection pooler (port 6543)")
    print(f"   - Use the direct connection (port 5432)")
    print(f"   - Check if your region has a different hostname")

if __name__ == "__main__":
    main() 