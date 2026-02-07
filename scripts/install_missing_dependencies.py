#!/usr/bin/env python3
"""
Personal Health Assistant - Install Missing Dependencies Script
Automatically installs all missing Python packages and system dependencies.
"""

import os
import sys
import subprocess
import platform
import logging
from pathlib import Path
from typing import List, Tuple, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DependencyInstaller:
    """Installs missing dependencies for Personal Health Assistant"""
    
    def __init__(self):
        self.os_type = platform.system().lower()
        self.arch = platform.machine().lower()
        self.install_results = []
        
    def run_command(self, command: str, description: str = "") -> bool:
        """Run a command and return success status"""
        try:
            logger.info(f"🔧 {description}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                logger.info(f"✅ {description} - Success")
                return True
            else:
                logger.error(f"❌ {description} - Failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ {description} - Error: {e}")
            return False
    
    def get_missing_packages(self) -> List[str]:
        """Get list of missing Python packages by running validation"""
        try:
            # Import and run validation to get missing packages
            from validate_requirements import RequirementsValidator
            
            validator = RequirementsValidator()
            validator.check_python_packages()
            
            missing_packages = []
            for result in validator.results:
                if result.category == "Python Packages" and result.status.value == "❌ FAIL":
                    # Extract package name from result name
                    package_name = result.name.replace("Python: ", "")
                    missing_packages.append(package_name)
            
            return missing_packages
        except Exception as e:
            logger.error(f"Could not determine missing packages: {e}")
            # Fallback to known missing packages
            return [
                "python-dotenv",
                "torch", 
                "pandas",
                "scikit-learn",
                "alembic",
                "asyncpg",
                "structlog",
                "prometheus-client",
                "sentry-sdk",
                "bcrypt",
                "flake8",
                "bandit",
                "safety"
            ]
    
    def install_python_packages(self, packages: List[str]) -> bool:
        """Install Python packages using pip"""
        if not packages:
            logger.info("✅ All Python packages are already installed")
            return True
        
        logger.info(f"📦 Installing {len(packages)} Python packages...")
        
        # Install packages in batches to avoid timeout
        batch_size = 5
        for i in range(0, len(packages), batch_size):
            batch = packages[i:i + batch_size]
            package_list = " ".join(batch)
            
            success = self.run_command(
                f"pip install {package_list}",
                f"Installing packages: {', '.join(batch)}"
            )
            
            if not success:
                logger.error(f"Failed to install batch: {batch}")
                return False
        
        return True
    
    def install_system_dependencies(self):
        """Install system-level dependencies based on OS"""
        logger.info("🔧 Installing system dependencies...")
        
        if self.os_type == "darwin":  # macOS
            return self.install_macos_dependencies()
        elif self.os_type == "linux":
            return self.install_linux_dependencies()
        elif self.os_type == "windows":
            return self.install_windows_dependencies()
        else:
            logger.error(f"Unsupported OS: {self.os_type}")
            return False
    
    def install_macos_dependencies(self) -> bool:
        """Install dependencies on macOS using Homebrew"""
        logger.info("🍎 Installing macOS dependencies...")
        
        # Check if Homebrew is installed
        if not self.run_command("brew --version", "Checking Homebrew"):
            logger.info("Installing Homebrew...")
            install_script = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            if not self.run_command(install_script, "Installing Homebrew"):
                return False
        
        # Install system packages
        packages = [
            "python@3.11",
            "git",
            "docker",
            "docker-compose",
            "make",
            "jq",
            "curl"
        ]
        
        for package in packages:
            if not self.run_command(f"brew install {package}", f"Installing {package}"):
                logger.warning(f"Failed to install {package}, continuing...")
        
        return True
    
    def install_linux_dependencies(self) -> bool:
        """Install dependencies on Linux"""
        logger.info("🐧 Installing Linux dependencies...")
        
        # Update package list
        if not self.run_command("sudo apt-get update", "Updating package list"):
            return False
        
        # Install packages
        packages = [
            "python3.11",
            "python3.11-venv",
            "python3-pip",
            "git",
            "docker.io",
            "docker-compose",
            "make",
            "jq",
            "curl"
        ]
        
        package_list = " ".join(packages)
        if not self.run_command(f"sudo apt-get install -y {package_list}", "Installing system packages"):
            return False
        
        # Start and enable Docker
        self.run_command("sudo systemctl start docker", "Starting Docker service")
        self.run_command("sudo systemctl enable docker", "Enabling Docker service")
        self.run_command("sudo usermod -aG docker $USER", "Adding user to docker group")
        
        return True
    
    def install_windows_dependencies(self) -> bool:
        """Install dependencies on Windows"""
        logger.info("🪟 Installing Windows dependencies...")
        
        # Check if Chocolatey is installed
        if not self.run_command("choco --version", "Checking Chocolatey"):
            logger.info("Installing Chocolatey...")
            install_script = 'Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString("https://community.chocolatey.org/install.ps1"))'
            if not self.run_command(f'powershell -Command "{install_script}"', "Installing Chocolatey"):
                return False
        
        # Install packages
        packages = [
            "python",
            "git",
            "docker-desktop",
            "make",
            "curl"
        ]
        
        for package in packages:
            if not self.run_command(f"choco install -y {package}", f"Installing {package}"):
                logger.warning(f"Failed to install {package}, continuing...")
        
        return True
    
    def setup_python_environment(self) -> bool:
        """Set up Python virtual environment"""
        logger.info("🐍 Setting up Python environment...")
        
        venv_path = Path("venv")
        
        # Create virtual environment if it doesn't exist
        if not venv_path.exists():
            if not self.run_command("python3 -m venv venv", "Creating virtual environment"):
                return False
        
        # Upgrade pip
        if not self.run_command("pip install --upgrade pip", "Upgrading pip"):
            logger.warning("Failed to upgrade pip, continuing...")
        
        return True
    
    def install_requirements(self) -> bool:
        """Install requirements from requirements.txt"""
        logger.info("📋 Installing requirements from requirements.txt...")
        
        if Path("requirements.txt").exists():
            return self.run_command("pip install -r requirements.txt", "Installing requirements.txt")
        else:
            logger.warning("requirements.txt not found")
            return True
    
    def setup_pre_commit(self) -> bool:
        """Set up pre-commit hooks"""
        logger.info("🔒 Setting up pre-commit hooks...")
        
        # Install pre-commit hooks
        if not self.run_command("pre-commit install", "Installing pre-commit hooks"):
            logger.warning("Failed to install pre-commit hooks")
            return False
        
        return True
    
    def create_env_file(self) -> bool:
        """Create .env file if it doesn't exist"""
        logger.info("📝 Creating .env file...")
        
        env_file = Path(".env")
        if env_file.exists():
            logger.info("✅ .env file already exists")
            return True
        
        # Create basic .env file
        env_content = """# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/health_assistant
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External Services
QDRANT_URL=http://localhost:6333
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_URL=redis://localhost:6379

# AI/ML Services
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# File Storage
STORAGE_BUCKET=health-assistant-storage
STORAGE_REGION=us-east-1

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO

# Development
DEBUG=true
ENVIRONMENT=development
"""
        
        try:
            with open(env_file, 'w') as f:
                f.write(env_content)
            logger.info("✅ Created .env file with default configuration")
            logger.warning("⚠️  Please update .env file with your actual API keys and configuration")
            return True
        except Exception as e:
            logger.error(f"Failed to create .env file: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """Verify that all dependencies are installed"""
        logger.info("🔍 Verifying installation...")
        
        # Run validation script
        if not self.run_command("python scripts/validate_requirements.py", "Running validation"):
            logger.warning("Validation failed, but installation may still be successful")
            return False
        
        return True
    
    def run_installation(self):
        """Run the complete installation process"""
        logger.info("🚀 Starting Personal Health Assistant Dependency Installation")
        logger.info("=" * 70)
        
        steps = [
            ("System Dependencies", self.install_system_dependencies),
            ("Python Environment", self.setup_python_environment),
            ("Requirements", self.install_requirements),
            ("Missing Packages", lambda: self.install_python_packages(self.get_missing_packages())),
            ("Pre-commit Hooks", self.setup_pre_commit),
            ("Environment File", self.create_env_file),
            ("Verification", self.verify_installation),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n{'='*60}")
            logger.info(f"STEP: {step_name}")
            logger.info(f"{'='*60}")
            
            if not step_func():
                logger.error(f"❌ Installation failed at: {step_name}")
                return False
        
        logger.info(f"\n{'='*60}")
        logger.info("🎉 INSTALLATION COMPLETED SUCCESSFULLY!")
        logger.info(f"{'='*60}")
        logger.info("\nYour Personal Health Assistant dependencies are now installed!")
        logger.info("\nNext steps:")
        logger.info("1. Update your .env file with actual API keys")
        logger.info("2. Start Docker services: docker-compose up -d")
        logger.info("3. Run database setup: python scripts/setup/db_setup.py")
        logger.info("4. Verify everything: python scripts/test_setup.py")
        logger.info("5. Start development: python main.py")
        
        return True

def main():
    """Main function"""
    try:
        installer = DependencyInstaller()
        success = installer.run_installation()
        
        if success:
            logger.info("✅ Installation completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Installation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Installation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Installation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 