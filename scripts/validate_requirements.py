#!/usr/bin/env python3
"""
Personal Health Assistant - Requirements Validation Script
Comprehensive validation of all required tools, frameworks, and software.
"""

import os
import sys
import subprocess
import platform
import importlib
import requests
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Status(Enum):
    """Status enumeration for validation results"""
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARNING = "⚠️  WARNING"
    SKIP = "⏭️  SKIP"

@dataclass
class ValidationResult:
    """Validation result data class"""
    name: str
    status: Status
    version: Optional[str] = None
    message: str = ""
    required: bool = True
    category: str = ""

class RequirementsValidator:
    """Comprehensive requirements validator for Personal Health Assistant"""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.os_type = platform.system().lower()
        self.arch = platform.machine().lower()
        
    def add_result(self, result: ValidationResult):
        """Add validation result"""
        self.results.append(result)
        
    def run_command(self, command: str, capture_output: bool = True) -> Tuple[bool, str]:
        """Run a command and return success status and output"""
        try:
            if capture_output:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                return result.returncode == 0, result.stdout.strip()
            else:
                result = subprocess.run(command, shell=True, timeout=30)
                return result.returncode == 0, ""
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False, ""
    
    def get_package_version(self, package_name: str) -> Optional[str]:
        """Get package version using multiple methods"""
        try:
            # Try importlib first
            module = importlib.import_module(package_name.replace("-", "_"))
            version = getattr(module, "__version__", None)
            if version:
                return version
            
            # Try pkg_resources
            try:
                import pkg_resources
                version = pkg_resources.get_distribution(package_name).version
                return version
            except:
                pass
            
            # Try specific version attributes
            if hasattr(module, "VERSION"):
                return module.VERSION
            elif hasattr(module, "version"):
                return module.version
            
            return "Unknown"
        except ImportError:
            return None
    
    def check_system_requirements(self):
        """Check system-level requirements"""
        logger.info("🔍 Checking System Requirements...")
        
        # Operating System
        supported_os = ["darwin", "linux", "windows"]
        if self.os_type in supported_os:
            self.add_result(ValidationResult(
                name="Operating System",
                status=Status.PASS,
                version=f"{platform.system()} {platform.release()}",
                message=f"Supported OS: {self.os_type}",
                category="System"
            ))
        else:
            self.add_result(ValidationResult(
                name="Operating System",
                status=Status.FAIL,
                message=f"Unsupported OS: {self.os_type}. Supported: {', '.join(supported_os)}",
                category="System"
            ))
        
        # Architecture
        if self.arch in ["x86_64", "amd64", "arm64", "aarch64"]:
            self.add_result(ValidationResult(
                name="Architecture",
                status=Status.PASS,
                version=self.arch,
                message="Supported architecture",
                category="System"
            ))
        else:
            self.add_result(ValidationResult(
                name="Architecture",
                status=Status.WARNING,
                version=self.arch,
                message="Architecture may have compatibility issues",
                category="System"
            ))
        
        # Python Version
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 9:
            self.add_result(ValidationResult(
                name="Python",
                status=Status.PASS,
                version=f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                message="Python 3.9+ required",
                category="System"
            ))
        else:
            self.add_result(ValidationResult(
                name="Python",
                status=Status.FAIL,
                version=f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                message="Python 3.9+ required",
                category="System"
            ))
    
    def check_docker_requirements(self):
        """Check Docker and Docker Compose"""
        logger.info("🐳 Checking Docker Requirements...")
        
        # Docker
        success, output = self.run_command("docker --version")
        if success:
            version = output.split()[2] if output else "Unknown"
            self.add_result(ValidationResult(
                name="Docker",
                status=Status.PASS,
                version=version,
                message="Docker is installed and accessible",
                category="Containerization"
            ))
        else:
            self.add_result(ValidationResult(
                name="Docker",
                status=Status.FAIL,
                message="Docker is not installed or not accessible",
                category="Containerization"
            ))
        
        # Docker Compose
        success, output = self.run_command("docker-compose --version")
        if success:
            version = output.split()[2] if output else "Unknown"
            self.add_result(ValidationResult(
                name="Docker Compose",
                status=Status.PASS,
                version=version,
                message="Docker Compose is installed",
                category="Containerization"
            ))
        else:
            self.add_result(ValidationResult(
                name="Docker Compose",
                status=Status.FAIL,
                message="Docker Compose is not installed",
                category="Containerization"
            ))
        
        # Docker Daemon
        success, _ = self.run_command("docker info")
        if success:
            self.add_result(ValidationResult(
                name="Docker Daemon",
                status=Status.PASS,
                message="Docker daemon is running",
                category="Containerization"
            ))
        else:
            self.add_result(ValidationResult(
                name="Docker Daemon",
                status=Status.FAIL,
                message="Docker daemon is not running",
                category="Containerization"
            ))
    
    def check_python_packages(self):
        """Check required Python packages"""
        logger.info("🐍 Checking Python Packages...")
        
        # Core packages from requirements.txt with their import names
        core_packages = {
            "fastapi": "fastapi",
            "uvicorn": "uvicorn",
            "sqlalchemy": "sqlalchemy",
            "psycopg2-binary": "psycopg2",
            "pydantic": "pydantic",
            "python-dotenv": "dotenv",
            "httpx": "httpx",
            "redis": "redis",
            "kafka-python": "kafka",
            "qdrant-client": "qdrant_client",
            "langchain": "langchain",
            "openai": "openai",
            "anthropic": "anthropic",
            "transformers": "transformers",
            "torch": "torch",
            "numpy": "numpy",
            "pandas": "pandas",
            "scikit-learn": "sklearn",
            "alembic": "alembic",
            "asyncpg": "asyncpg",
            "structlog": "structlog",
            "prometheus-client": "prometheus_client",
            "sentry-sdk": "sentry_sdk",
            "cryptography": "cryptography",
            "bcrypt": "bcrypt",
            "pytest": "pytest",
            "black": "black",
            "flake8": "flake8",
            "mypy": "mypy",
            "isort": "isort",
            "pre-commit": "pre_commit",
            "bandit": "bandit",
            "safety": "safety"
        }
        
        for package_name, import_name in core_packages.items():
            try:
                # Try to import the module
                importlib.import_module(import_name)
                version = self.get_package_version(package_name)
                self.add_result(ValidationResult(
                    name=f"Python: {package_name}",
                    status=Status.PASS,
                    version=version,
                    message=f"Package {package_name} is installed",
                    category="Python Packages"
                ))
            except ImportError:
                self.add_result(ValidationResult(
                    name=f"Python: {package_name}",
                    status=Status.FAIL,
                    message=f"Package {package_name} is not installed",
                    category="Python Packages"
                ))
    
    def check_database_requirements(self):
        """Check database and related tools"""
        logger.info("🗄️  Checking Database Requirements...")
        
        # PostgreSQL Client
        success, output = self.run_command("psql --version")
        if success:
            version = output.split()[2] if output else "Unknown"
            self.add_result(ValidationResult(
                name="PostgreSQL Client",
                status=Status.PASS,
                version=version,
                message="PostgreSQL client is installed",
                category="Database"
            ))
        else:
            self.add_result(ValidationResult(
                name="PostgreSQL Client",
                status=Status.WARNING,
                message="PostgreSQL client not found (Docker will be used)",
                category="Database"
            ))
        
        # Check if virtual environment exists
        venv_path = Path("venv")
        if venv_path.exists():
            self.add_result(ValidationResult(
                name="Python Virtual Environment",
                status=Status.PASS,
                message="Virtual environment exists",
                category="Python Environment"
            ))
        else:
            self.add_result(ValidationResult(
                name="Python Virtual Environment",
                status=Status.WARNING,
                message="Virtual environment not found",
                category="Python Environment"
            ))
    
    def check_development_tools(self):
        """Check development tools"""
        logger.info("🔧 Checking Development Tools...")
        
        # Git
        success, output = self.run_command("git --version")
        if success:
            version = output.split()[2] if output else "Unknown"
            self.add_result(ValidationResult(
                name="Git",
                status=Status.PASS,
                version=version,
                message="Git is installed",
                category="Development Tools"
            ))
        else:
            self.add_result(ValidationResult(
                name="Git",
                status=Status.FAIL,
                message="Git is not installed",
                category="Development Tools"
            ))
        
        # Make
        success, output = self.run_command("make --version")
        if success:
            version = output.split()[2] if output else "Unknown"
            self.add_result(ValidationResult(
                name="Make",
                status=Status.PASS,
                version=version,
                message="Make is installed",
                category="Development Tools"
            ))
        else:
            self.add_result(ValidationResult(
                name="Make",
                status=Status.WARNING,
                message="Make is not installed (optional)",
                required=False,
                category="Development Tools"
            ))
        
        # Curl
        success, output = self.run_command("curl --version")
        if success:
            version = output.split()[1] if output else "Unknown"
            self.add_result(ValidationResult(
                name="Curl",
                status=Status.PASS,
                version=version,
                message="Curl is installed",
                category="Development Tools"
            ))
        else:
            self.add_result(ValidationResult(
                name="Curl",
                status=Status.WARNING,
                message="Curl is not installed",
                required=False,
                category="Development Tools"
            ))
    
    def check_external_services(self):
        """Check external service connectivity"""
        logger.info("🌐 Checking External Services...")
        
        # Check if .env file exists
        env_file = Path(".env")
        if env_file.exists():
            self.add_result(ValidationResult(
                name="Environment File",
                status=Status.PASS,
                message=".env file exists",
                category="Configuration"
            ))
        else:
            self.add_result(ValidationResult(
                name="Environment File",
                status=Status.WARNING,
                message=".env file not found",
                category="Configuration"
            ))
        
        # Check Docker services (if running)
        try:
            success, output = self.run_command("docker-compose ps")
            if success and "Up" in output:
                self.add_result(ValidationResult(
                    name="Docker Services",
                    status=Status.PASS,
                    message="Docker services are running",
                    category="Services"
                ))
            else:
                self.add_result(ValidationResult(
                    name="Docker Services",
                    status=Status.WARNING,
                    message="Docker services are not running",
                    category="Services"
                ))
        except Exception:
            self.add_result(ValidationResult(
                name="Docker Services",
                status=Status.SKIP,
                message="Could not check Docker services",
                category="Services"
            ))
    
    def check_network_connectivity(self):
        """Check network connectivity for external services"""
        logger.info("🌐 Checking Network Connectivity...")
        
        # Test basic internet connectivity
        try:
            response = requests.get("https://httpbin.org/get", timeout=10)
            if response.status_code == 200:
                self.add_result(ValidationResult(
                    name="Internet Connectivity",
                    status=Status.PASS,
                    message="Internet connection is working",
                    category="Network"
                ))
            else:
                self.add_result(ValidationResult(
                    name="Internet Connectivity",
                    status=Status.FAIL,
                    message="Internet connection failed",
                    category="Network"
                ))
        except Exception:
            self.add_result(ValidationResult(
                name="Internet Connectivity",
                status=Status.FAIL,
                message="No internet connection",
                category="Network"
            ))
        
        # Test Docker Hub connectivity
        try:
            response = requests.get("https://registry-1.docker.io/v2/", timeout=10)
            if response.status_code in [200, 401]:  # 401 is expected for unauthenticated
                self.add_result(ValidationResult(
                    name="Docker Hub Connectivity",
                    status=Status.PASS,
                    message="Docker Hub is accessible",
                    category="Network"
                ))
            else:
                self.add_result(ValidationResult(
                    name="Docker Hub Connectivity",
                    status=Status.FAIL,
                    message="Docker Hub is not accessible",
                    category="Network"
                ))
        except Exception:
            self.add_result(ValidationResult(
                name="Docker Hub Connectivity",
                status=Status.FAIL,
                message="Cannot reach Docker Hub",
                category="Network"
            ))
    
    def check_disk_space(self):
        """Check available disk space"""
        logger.info("💾 Checking Disk Space...")
        
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_gb = free // (1024**3)
            
            if free_gb >= 10:
                self.add_result(ValidationResult(
                    name="Disk Space",
                    status=Status.PASS,
                    version=f"{free_gb}GB free",
                    message="Sufficient disk space available",
                    category="System"
                ))
            elif free_gb >= 5:
                self.add_result(ValidationResult(
                    name="Disk Space",
                    status=Status.WARNING,
                    version=f"{free_gb}GB free",
                    message="Limited disk space (recommend 10GB+)",
                    category="System"
                ))
            else:
                self.add_result(ValidationResult(
                    name="Disk Space",
                    status=Status.FAIL,
                    version=f"{free_gb}GB free",
                    message="Insufficient disk space",
                    category="System"
                ))
        except Exception:
            self.add_result(ValidationResult(
                name="Disk Space",
                status=Status.SKIP,
                message="Could not check disk space",
                category="System"
            ))
    
    def check_memory(self):
        """Check available memory"""
        logger.info("🧠 Checking Memory...")
        
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_gb = memory.available // (1024**3)
            
            if available_gb >= 4:
                self.add_result(ValidationResult(
                    name="Available Memory",
                    status=Status.PASS,
                    version=f"{available_gb}GB available",
                    message="Sufficient memory available",
                    category="System"
                ))
            elif available_gb >= 2:
                self.add_result(ValidationResult(
                    name="Available Memory",
                    status=Status.WARNING,
                    version=f"{available_gb}GB available",
                    message="Limited memory (recommend 4GB+)",
                    category="System"
                ))
            else:
                self.add_result(ValidationResult(
                    name="Available Memory",
                    status=Status.FAIL,
                    version=f"{available_gb}GB available",
                    message="Insufficient memory",
                    category="System"
                ))
        except ImportError:
            self.add_result(ValidationResult(
                name="Available Memory",
                status=Status.SKIP,
                message="psutil not available for memory check",
                category="System"
            ))
        except Exception:
            self.add_result(ValidationResult(
                name="Available Memory",
                status=Status.SKIP,
                message="Could not check memory",
                category="System"
            ))
    
    def run_all_checks(self):
        """Run all validation checks"""
        logger.info("🚀 Starting Personal Health Assistant Requirements Validation")
        logger.info("=" * 70)
        
        self.check_system_requirements()
        self.check_docker_requirements()
        self.check_python_packages()
        self.check_database_requirements()
        self.check_development_tools()
        self.check_external_services()
        self.check_network_connectivity()
        self.check_disk_space()
        self.check_memory()
        
        logger.info("=" * 70)
        logger.info("📊 Validation Complete!")
    
    def generate_report(self) -> Dict:
        """Generate a comprehensive report"""
        report = {
            "summary": {
                "total_checks": len(self.results),
                "passed": len([r for r in self.results if r.status == Status.PASS]),
                "failed": len([r for r in self.results if r.status == Status.FAIL]),
                "warnings": len([r for r in self.results if r.status == Status.WARNING]),
                "skipped": len([r for r in self.results if r.status == Status.SKIP])
            },
            "results": []
        }
        
        # Group by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        for category, results in categories.items():
            report["results"].append({
                "category": category,
                "checks": [
                    {
                        "name": r.name,
                        "status": r.status.value,
                        "version": r.version,
                        "message": r.message,
                        "required": r.required
                    }
                    for r in results
                ]
            })
        
        return report
    
    def print_report(self):
        """Print the validation report"""
        report = self.generate_report()
        
        print("\n" + "=" * 80)
        print("📋 PERSONAL HEALTH ASSISTANT - REQUIREMENTS VALIDATION REPORT")
        print("=" * 80)
        
        # Summary
        summary = report["summary"]
        print(f"\n📊 SUMMARY:")
        print(f"   Total Checks: {summary['total_checks']}")
        print(f"   ✅ Passed: {summary['passed']}")
        print(f"   ❌ Failed: {summary['failed']}")
        print(f"   ⚠️  Warnings: {summary['warnings']}")
        print(f"   ⏭️  Skipped: {summary['skipped']}")
        
        # Detailed results by category
        for category_data in report["results"]:
            category = category_data["category"]
            checks = category_data["checks"]
            
            print(f"\n🔍 {category.upper()}:")
            print("-" * 60)
            
            for check in checks:
                status_icon = check["status"]
                name = check["name"]
                version = f" ({check['version']})" if check["version"] else ""
                message = f" - {check['message']}" if check["message"] else ""
                required = " [REQUIRED]" if check["required"] else " [OPTIONAL]"
                
                print(f"   {status_icon} {name}{version}{message}{required}")
        
        # Recommendations
        failed_required = [r for r in self.results if r.status == Status.FAIL and r.required]
        warnings = [r for r in self.results if r.status == Status.WARNING]
        
        if failed_required:
            print(f"\n❌ CRITICAL ISSUES (Must Fix):")
            print("-" * 40)
            for result in failed_required:
                print(f"   • {result.name}: {result.message}")
        
        if warnings:
            print(f"\n⚠️  RECOMMENDATIONS:")
            print("-" * 40)
            for result in warnings:
                print(f"   • {result.name}: {result.message}")
        
        # Overall status
        if failed_required:
            print(f"\n🎯 STATUS: ❌ NOT READY - {len(failed_required)} critical issues found")
            print("   Please fix the critical issues above before proceeding.")
        elif warnings:
            print(f"\n🎯 STATUS: ⚠️  READY WITH WARNINGS - {len(warnings)} recommendations")
            print("   The system should work, but consider addressing the warnings.")
        else:
            print(f"\n🎯 STATUS: ✅ READY - All requirements met!")
            print("   Your development environment is ready for Personal Health Assistant development.")
        
        print("\n" + "=" * 80)
    
    def save_report(self, filename: str = "requirements_validation_report.json"):
        """Save the validation report to a JSON file"""
        report = self.generate_report()
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"📄 Report saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

def main():
    """Main function"""
    try:
        validator = RequirementsValidator()
        validator.run_all_checks()
        validator.print_report()
        validator.save_report()
        
        # Exit with appropriate code
        failed_required = [r for r in validator.results if r.status == Status.FAIL and r.required]
        if failed_required:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()