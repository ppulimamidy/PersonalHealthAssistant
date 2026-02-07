#!/usr/bin/env python3
"""
Fix Supabase Database Connection
Helps users get the correct database connection string from their Supabase project.
"""

import requests
import json
from dotenv import load_dotenv
import os
import re
from pathlib import Path

def get_supabase_project_info():
    """Get project info from Supabase"""
    
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        print("❌ SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        return None
    
    print("🔍 Getting Supabase project info...")
    
    # Extract project reference from URL
    project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
    
    print(f"📋 Project Reference: {project_ref}")
    print(f"🌐 Supabase URL: {supabase_url}")
    
    # Test the connection
    headers = {
        'apikey': supabase_anon_key,
        'Authorization': f'Bearer {supabase_anon_key}'
    }
    
    try:
        response = requests.get(f"{supabase_url}/rest/v1/", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Supabase REST API is working!")
            return project_ref
        else:
            print(f"❌ Supabase connection failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return None

def print_database_setup_instructions(project_ref):
    """Print instructions for setting up the database connection"""
    
    print("\n" + "="*60)
    print("SUPABASE DATABASE CONNECTION SETUP")
    print("="*60)
    
    print(f"\n1. Go to your Supabase project dashboard:")
    print(f"   https://supabase.com/dashboard/project/{project_ref}")
    
    print(f"\n2. Go to Settings > Database")
    
    print(f"\n3. Find the 'Connection string' section")
    
    print(f"\n4. Copy the 'URI' connection string")
    print(f"   It should look like:")
    print(f"   postgresql://postgres:[YOUR-PASSWORD]@db.{project_ref}.supabase.co:5432/postgres")
    
    print(f"\n5. Update your .env file with the correct DATABASE_URL")
    print(f"   Replace the current DATABASE_URL line with the copied string")
    
    print(f"\n6. Make sure to replace [YOUR-PASSWORD] with your actual database password")
    print(f"   (This is the password you set when creating the project)")
    
    print(f"\n7. Test the connection:")
    print(f"   python scripts/test_setup.py")

def check_current_env_file():
    """Check the current .env file and suggest fixes"""
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        return
    
    print(f"\n📋 Current .env file contents:")
    print("-" * 40)
    
    with open(env_file, 'r') as f:
        content = f.read()
        print(content)
    
    # Check for common issues
    lines = content.split('\n')
    issues = []
    
    for line in lines:
        if line.startswith('DATABASE_URL='):
            if 'postgres' in line and 'supabase.co' in line:
                if '[YOUR-PASSWORD]' in line or 'postgres' in line.split('@')[0]:
                    issues.append("DATABASE_URL contains placeholder password")
            elif 'localhost' in line:
                issues.append("DATABASE_URL points to localhost instead of Supabase")
    
    if issues:
        print(f"\n⚠️  Issues found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print(f"\n✅ .env file looks correct")

def update_env_file_with_correct_url(project_ref):
    """Update the .env file with the correct database URL format"""
    
    print(f"\n🔧 Updating .env file...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    # Read current content
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Update DATABASE_URL line
    new_content = []
    updated = False
    
    for line in content.split('\n'):
        if line.startswith('DATABASE_URL='):
            # Keep the current password if it's not a placeholder
            current_url = line.split('=', 1)[1]
            if 'postgres' in current_url and 'supabase.co' in current_url:
                # Extract password from current URL
                password_match = re.search(r'://postgres:([^@]+)@', current_url)
                if password_match and password_match.group(1) != 'postgres':
                    password = password_match.group(1)
                    new_url = f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres"
                else:
                    new_url = f"postgresql://postgres:[YOUR-PASSWORD]@db.{project_ref}.supabase.co:5432/postgres"
            else:
                new_url = f"postgresql://postgres:[YOUR-PASSWORD]@db.{project_ref}.supabase.co:5432/postgres"
            
            new_content.append(f"DATABASE_URL={new_url}")
            updated = True
            print(f"✅ Updated DATABASE_URL to: {new_url}")
        else:
            new_content.append(line)
    
    if not updated:
        print("❌ DATABASE_URL line not found in .env file")
        return False
    
    # Write back to file
    with open(env_file, 'w') as f:
        f.write('\n'.join(new_content))
    
    print("✅ .env file updated successfully!")
    return True

def main():
    """Main function"""
    print("🔧 Supabase Database Connection Fixer")
    print("="*50)
    
    # Get project info
    project_ref = get_supabase_project_info()
    if not project_ref:
        print("\n❌ Could not get Supabase project info")
        return
    
    # Check current .env file
    check_current_env_file()
    
    # Print instructions
    print_database_setup_instructions(project_ref)
    
    # Ask if user wants to update the .env file
    print(f"\n" + "="*60)
    response = input("Would you like me to update your .env file with the correct format? (y/N): ")
    
    if response.lower() == 'y':
        if update_env_file_with_correct_url(project_ref):
            print(f"\n🎉 .env file updated!")
            print(f"Next steps:")
            print(f"1. Update the password in your .env file")
            print(f"2. Run: python scripts/test_setup.py")
        else:
            print(f"\n❌ Failed to update .env file")
    else:
        print(f"\n📝 Please manually update your .env file with the correct DATABASE_URL")

if __name__ == "__main__":
    main() 