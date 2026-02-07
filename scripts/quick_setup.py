#!/usr/bin/env python3
"""
Quick Setup Script for Personal Health Assistant
Automates the complete setup process for Supabase.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_prerequisites():
    """Check if prerequisites are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required")
        return False
    
    # Check if Docker is running
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker and Docker Compose are required")
        return False
    
    print("✅ Prerequisites check passed")
    return True

def setup_environment():
    """Set up environment variables"""
    print("\n📝 Setting up environment variables...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  .env file not found. Please run: python scripts/setup_env.py")
        print("Then update the .env file with your Supabase credentials.")
        return False
    
    # Check if Supabase variables are configured
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var).startswith('your_') or '[YOUR-' in os.getenv(var, ''):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Please configure these environment variables: {', '.join(missing_vars)}")
        print("Update your .env file with actual Supabase credentials.")
        return False
    
    print("✅ Environment variables configured")
    return True

def setup_python_environment():
    """Set up Python virtual environment and install dependencies"""
    print("\n🐍 Setting up Python environment...")
    
    # Create virtual environment if it doesn't exist
    venv_path = Path('venv')
    if not venv_path.exists():
        if not run_command("python3 -m venv venv", "Creating virtual environment"):
            return False
    
    # Determine the correct pip path
    if os.name == 'nt':  # Windows
        pip_path = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_path = "venv/bin/pip"
    
    # Install dependencies
    if not run_command(f"{pip_path} install -r requirements.txt", "Installing dependencies"):
        return False
    
    return True

def start_services():
    """Start Docker services"""
    print("\n🐳 Starting Docker services...")
    
    if not run_command("docker-compose up -d", "Starting Docker services"):
        return False
    
    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    time.sleep(30)
    
    return True

def setup_database():
    """Set up the database"""
    print("\n🗄️  Setting up database...")
    
    # Determine the correct python path
    if os.name == 'nt':  # Windows
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        python_path = "venv/bin/python"
    
    if not run_command(f"{python_path} scripts/setup/db_setup.py", "Setting up database schema"):
        return False
    
    return True

def run_tests():
    """Run the test suite"""
    print("\n🧪 Running tests...")
    
    # Determine the correct python path
    if os.name == 'nt':  # Windows
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        python_path = "venv/bin/python"
    
    if not run_command(f"{python_path} scripts/test_setup.py", "Running test suite"):
        return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 Personal Health Assistant - Quick Setup")
    print("="*50)
    
    # Check if we're in the right directory
    if not Path('schema.sql').exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    steps = [
        ("Prerequisites Check", check_prerequisites),
        ("Environment Setup", setup_environment),
        ("Python Environment", setup_python_environment),
        ("Docker Services", start_services),
        ("Database Setup", setup_database),
        ("Test Suite", run_tests),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{'='*60}")
        print(f"STEP: {step_name}")
        print(f"{'='*60}")
        
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}")
            print("\nTroubleshooting:")
            print("1. Check the error messages above")
            print("2. Ensure you have configured your .env file with Supabase credentials")
            print("3. Make sure Docker is running")
            print("4. Try running individual steps manually")
            sys.exit(1)
    
    print(f"\n{'='*60}")
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print(f"{'='*60}")
    print("\nYour Personal Health Assistant is now ready!")
    print("\nNext steps:")
    print("1. Start developing your application")
    print("2. Check the documentation in docs/")
    print("3. Run tests: python scripts/test_setup.py")
    print("4. Start the application: python main.py")

if __name__ == "__main__":
    main() 