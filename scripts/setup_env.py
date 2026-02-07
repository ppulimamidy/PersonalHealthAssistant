#!/usr/bin/env python3
"""
Environment Setup Script for Personal Health Assistant
Helps users configure their environment variables for Supabase.
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with Supabase configuration template"""
    
    env_content = """# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Database URL for Supabase
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

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
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return False
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print("\n📝 Next steps:")
        print("1. Go to your Supabase project dashboard")
        print("2. Copy your project URL and API keys")
        print("3. Update the .env file with your actual values")
        print("4. Run: python scripts/setup/db_setup.py")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def print_supabase_instructions():
    """Print instructions for setting up Supabase"""
    
    print("\n" + "="*60)
    print("SUPABASE SETUP INSTRUCTIONS")
    print("="*60)
    
    print("\n1. Create a Supabase Project:")
    print("   - Go to https://supabase.com")
    print("   - Sign up or log in")
    print("   - Click 'New Project'")
    print("   - Choose your organization")
    print("   - Enter project name and database password")
    print("   - Select a region close to you")
    print("   - Click 'Create new project'")
    
    print("\n2. Get Your Project Credentials:")
    print("   - In your project dashboard, go to Settings > API")
    print("   - Copy the following values:")
    print("     * Project URL")
    print("     * anon/public key")
    print("     * service_role key (keep this secret!)")
    
    print("\n3. Get Your Database URL:")
    print("   - In your project dashboard, go to Settings > Database")
    print("   - Copy the connection string")
    print("   - Replace [YOUR-PASSWORD] with your database password")
    
    print("\n4. Update Your .env File:")
    print("   - Replace the placeholder values with your actual credentials")
    print("   - Never commit the .env file to version control")
    
    print("\n5. Test Your Setup:")
    print("   - Run: python scripts/test_setup.py")
    print("   - Run: python scripts/setup/db_setup.py")

def main():
    """Main function"""
    print("🚀 Personal Health Assistant - Environment Setup")
    print("="*50)
    
    # Check if we're in the right directory
    if not Path('schema.sql').exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Create .env file
    if create_env_file():
        print_supabase_instructions()
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 