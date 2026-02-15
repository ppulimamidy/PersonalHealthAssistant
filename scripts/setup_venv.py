#!/usr/bin/env python3
"""
Virtual Environment Setup Script for Personal Health Assistant
This script handles the creation, activation, and validation of the Python virtual environment.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Optional

class VirtualEnvironmentManager:
    """Manages Python virtual environment setup and validation"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / "venv"
        self.requirements_file = self.project_root / "requirements.txt"
        
    def is_venv_active(self) -> bool:
        """Check if virtual environment is currently active"""
        return (hasattr(sys, 'real_prefix') or 
                (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
    
    def venv_exists(self) -> bool:
        """Check if virtual environment directory exists"""
        return self.venv_path.exists()
    
    def create_venv(self) -> bool:
        """Create a new virtual environment"""
        print("🐍 Creating virtual environment...")
        
        try:
            # Use python3 -m venv for better compatibility
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(self.venv_path)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ Virtual environment created successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr}")
            return False
    
    def activate_venv(self) -> bool:
        """Activate the virtual environment (for informational purposes)"""
        if not self.venv_exists():
            print("❌ Virtual environment does not exist")
            return False
        
        if self.is_venv_active():
            print("✅ Virtual environment is already active")
            return True
        
        # Show activation instructions
        if platform.system() == "Windows":
            activate_script = self.venv_path / "Scripts" / "activate"
            print(f"⚠️  Please activate the virtual environment manually:")
            print(f"   {activate_script}")
        else:
            activate_script = self.venv_path / "bin" / "activate"
            print(f"⚠️  Please activate the virtual environment manually:")
            print(f"   source {activate_script}")
        
        return False
    
    def upgrade_pip(self) -> bool:
        """Upgrade pip in the virtual environment"""
        if not self.is_venv_active():
            print("❌ Virtual environment is not active")
            return False
        
        print("🔄 Upgrading pip...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ Pip upgraded successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Failed to upgrade pip: {e}")
            return False
    
    def install_requirements(self) -> bool:
        """Install requirements from requirements.txt"""
        if not self.is_venv_active():
            print("❌ Virtual environment is not active")
            return False
        
        if not self.requirements_file.exists():
            print("⚠️  requirements.txt not found, skipping dependency installation")
            return True
        
        print("📦 Installing Python dependencies...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)],
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr}")
            return False
    
    def validate_venv(self) -> bool:
        """Validate the virtual environment setup"""
        print("🔍 Validating virtual environment...")
        
        checks = []
        
        # Check if venv exists
        if self.venv_exists():
            checks.append(("Virtual environment exists", True))
        else:
            checks.append(("Virtual environment exists", False))
        
        # Check if venv is active
        if self.is_venv_active():
            checks.append(("Virtual environment is active", True))
        else:
            checks.append(("Virtual environment is active", False))
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 9:
            checks.append(("Python version >= 3.9", True))
        else:
            checks.append(("Python version >= 3.9", False))
        
        # Check pip
        try:
            import pip
            checks.append(("Pip is available", True))
        except ImportError:
            checks.append(("Pip is available", False))
        
        # Display results
        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
            if not passed:
                all_passed = False
        
        return all_passed
    
    def setup_complete_venv(self) -> bool:
        """Complete virtual environment setup process"""
        print("🚀 Setting up Python Virtual Environment")
        print("=" * 40)
        
        # Step 1: Create venv if it doesn't exist
        if not self.venv_exists():
            if not self.create_venv():
                return False
        else:
            print("✅ Virtual environment already exists")
        
        # Step 2: Check activation
        if not self.is_venv_active():
            print("\n⚠️  IMPORTANT: Virtual environment is not active!")
            print("Please activate it manually and run this script again:")
            if platform.system() == "Windows":
                print(f"   {self.venv_path}\\Scripts\\activate")
            else:
                print(f"   source {self.venv_path}/bin/activate")
            return False
        
        # Step 3: Upgrade pip
        self.upgrade_pip()
        
        # Step 4: Install requirements
        if not self.install_requirements():
            return False
        
        # Step 5: Validate setup
        if not self.validate_venv():
            print("❌ Virtual environment validation failed")
            return False
        
        print("\n🎉 Virtual environment setup completed successfully!")
        print(f"📍 Virtual environment: {self.venv_path}")
        print(f"🐍 Python executable: {sys.executable}")
        pip_show = subprocess.check_output([sys.executable, "-m", "pip", "show", "pip"], text=True)
        pip_location = ""
        if "Location: " in pip_show:
            pip_location = pip_show.split("Location: ", 1)[1].splitlines()[0].strip()
        print(f"📦 Pip location: {pip_location}")
        
        return True

def main():
    """Main function"""
    manager = VirtualEnvironmentManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "create":
            success = manager.create_venv()
        elif command == "activate":
            success = manager.activate_venv()
        elif command == "validate":
            success = manager.validate_venv()
        elif command == "install":
            success = manager.install_requirements()
        elif command == "upgrade-pip":
            success = manager.upgrade_pip()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: create, activate, validate, install, upgrade-pip")
            sys.exit(1)
    else:
        # Default: complete setup
        success = manager.setup_complete_venv()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 