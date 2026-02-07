#!/usr/bin/env python3
"""
Master Setup Script for Personal Health Assistant
This script orchestrates the complete setup process for new developers.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

class SetupMaster:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = self.project_root / "scripts"
        self.setup_dir = self.scripts_dir / "setup"
        
    def run_command(self, command, description, check=True):
        """Run a shell command with error handling"""
        print(f"\n🔄 {description}")
        print(f"Running: {command}")
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=check
            )
            
            if result.stdout:
                print(f"✅ Output: {result.stdout.strip()}")
            
            return result.returncode == 0
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr}")
            return False
    
    def check_prerequisites(self):
        """Check if all prerequisites are installed"""
        print("🔍 Checking prerequisites...")
        
        prerequisites = {
            "docker": "docker --version",
            "docker-compose": "docker-compose --version", 
            "python": "python3 --version",
            "git": "git --version"
        }
        
        missing = []
        for tool, command in prerequisites.items():
            if not self.run_command(command, f"Checking {tool}", check=False):
                missing.append(tool)
        
        if missing:
            print(f"❌ Missing prerequisites: {', '.join(missing)}")
            print("Please install the missing tools and run this script again.")
            return False
        
        print("✅ All prerequisites are installed")
        return True
    
    def setup_python_environment(self):
        """Set up Python virtual environment and install dependencies"""
        print("\n🐍 Setting up Python environment...")
        
        # Check if virtual environment exists
        venv_path = self.project_root / "venv"
        if not venv_path.exists():
            print("Creating virtual environment...")
            if not self.run_command("python3 -m venv venv", "Creating virtual environment"):
                return False
        else:
            print("✅ Virtual environment already exists")
        
        # Check if we're already in a virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("✅ Virtual environment is already active")
        else:
            print("⚠️  Virtual environment is not active")
            print("Please activate it manually: source venv/bin/activate")
            print("Then run this script again.")
            return False
        
        # Upgrade pip
        print("Upgrading pip...")
        if not self.run_command("pip install --upgrade pip", "Upgrading pip"):
            print("⚠️  Failed to upgrade pip, continuing anyway...")
        
        # Install requirements
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            print("Installing Python dependencies...")
            if not self.run_command("pip install -r requirements.txt", "Installing dependencies"):
                return False
        else:
            print("⚠️  requirements.txt not found, skipping dependency installation")
        
        return True
    
    def start_docker_services(self):
        """Start all Docker services"""
        print("\n🐳 Starting Docker services...")
        
        # Stop any existing services
        self.run_command("docker-compose down", "Stopping existing services", check=False)
        
        # Start services
        if not self.run_command("docker-compose up -d", "Starting Docker services"):
            return False
        
        # Wait for services to be ready
        print("⏳ Waiting for services to be ready...")
        time.sleep(30)
        
        return True
    
    def verify_services(self):
        """Verify all services are running correctly"""
        print("\n🔍 Verifying services...")
        
        # Check service status
        if not self.run_command("docker-compose ps", "Checking service status"):
            return False
        
        # Test database connection
        if not self.run_command(
            "docker exec supabase_db psql -U postgres -d postgres -c 'SELECT version();'",
            "Testing database connection"
        ):
            return False
        
        # Test API endpoint
        if not self.run_command(
            "curl -s http://localhost:3000/ > /dev/null",
            "Testing API endpoint",
            check=False
        ):
            print("⚠️  API endpoint test failed (this might be normal during startup)")
        
        return True
    
    def run_tests(self):
        """Run the comprehensive test suite"""
        print("\n🧪 Running tests...")
        
        test_script = self.scripts_dir / "test_setup.py"
        if test_script.exists():
            if not self.run_command("python scripts/test_setup.py", "Running test suite"):
                return False
        
        return True
    
    def display_success_info(self):
        """Display success information and next steps"""
        print("\n" + "="*60)
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        print("\n📊 Your development environment is ready:")
        print("• Database: PostgreSQL with TimescaleDB (port 54323)")
        print("• REST API: PostgREST (port 3000)")
        print("• Studio: Supabase Studio (port 3001)")
        print("• Vector DB: Qdrant (ports 6333-6334)")
        print("• Message Queue: Kafka (port 9092)")
        
        print("\n🔗 Quick Access:")
        print("• API Documentation: http://localhost:3000")
        print("• Database Studio: http://localhost:3001")
        print("• Health Check: curl http://localhost:3000/")
        
        print("\n📁 Project Structure:")
        print("• Application code: apps/")
        print("• Database schema: schema.sql")
        print("• Setup scripts: scripts/")
        print("• Configuration: docker-compose.yml")
        
        print("\n🚀 Next Steps:")
        print("1. Explore the API at http://localhost:3000")
        print("2. Check out the apps/ directory for application modules")
        print("3. Read JUNIOR_DEV_SETUP.md for detailed information")
        print("4. Start coding!")
        
        print("\n📞 Need Help?")
        print("• Check JUNIOR_DEV_SETUP.md for troubleshooting")
        print("• Run: docker-compose logs [service-name] for service logs")
        print("• Run: python scripts/test_setup.py to verify everything")
        
        print("\n" + "="*60)
    
    def run_complete_setup(self):
        """Run the complete setup process"""
        print("🚀 Personal Health Assistant - Complete Setup")
        print("="*50)
        
        steps = [
            ("Checking prerequisites", self.check_prerequisites),
            ("Setting up Python environment", self.setup_python_environment),
            ("Starting Docker services", self.start_docker_services),
            ("Verifying services", self.verify_services),
            ("Running tests", self.run_tests)
        ]
        
        for step_name, step_func in steps:
            print(f"\n{'='*20} {step_name.upper()} {'='*20}")
            if not step_func():
                print(f"\n❌ Setup failed at: {step_name}")
                print("Please check the error messages above and try again.")
                return False
        
        self.display_success_info()
        return True

def main():
    """Main entry point"""
    setup = SetupMaster()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check-only":
        # Only check prerequisites
        return 0 if setup.check_prerequisites() else 1
    
    success = setup.run_complete_setup()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 