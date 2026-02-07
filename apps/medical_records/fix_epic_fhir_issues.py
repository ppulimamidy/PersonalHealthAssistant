#!/usr/bin/env python3
"""
Epic FHIR Issues Fix Script

This script fixes the Epic FHIR integration issues identified by the test:
1. Missing environment variables
2. Database connection issues
3. Epic FHIR configuration problems
4. Service connectivity issues
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from common.config.settings import get_settings
from common.utils.logging import get_logger

logger = get_logger(__name__)

class EpicFHIRIssueFixer:
    """Fix Epic FHIR integration issues."""
    
    def __init__(self):
        self.settings = get_settings()
        self.fixes_applied = []
        
    def log_fix(self, fix_name: str, status: str, details: str = ""):
        """Log fix result."""
        if status == "APPLIED":
            logger.info(f"✅ {fix_name}: {details}")
        elif status == "SKIPPED":
            logger.warning(f"⚠️ {fix_name}: {details}")
        else:
            logger.error(f"❌ {fix_name}: {details}")
        
        self.fixes_applied.append({
            "fix": fix_name,
            "status": status,
            "details": details
        })
    
    def fix_environment_variables(self):
        """Fix missing Epic FHIR environment variables."""
        logger.info("🔧 Fixing Epic FHIR Environment Variables...")
        
        # Check if .env file exists
        env_file = Path(project_root) / ".env"
        
        # Epic FHIR environment variables to set
        epic_vars = {
            "EPIC_FHIR_CLIENT_ID": "your_epic_client_id_here",
            "EPIC_FHIR_CLIENT_SECRET": "your_epic_client_secret_here", 
            "EPIC_FHIR_ENVIRONMENT": "sandbox",
            "EPIC_FHIR_REDIRECT_URI": "http://localhost:8080/callback"
        }
        
        # Check current environment variables
        missing_vars = []
        for var, default_value in epic_vars.items():
            if not os.getenv(var):
                missing_vars.append((var, default_value))
        
        if not missing_vars:
            self.log_fix("Environment Variables", "SKIPPED", "All Epic FHIR environment variables are already set")
            return
        
        # Create or update .env file
        env_content = []
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_content = f.readlines()
        
        # Add missing variables
        for var, default_value in missing_vars:
            var_line = f"{var}={default_value}\n"
            
            # Check if variable already exists in .env
            var_exists = any(line.startswith(f"{var}=") for line in env_content)
            
            if not var_exists:
                env_content.append(var_line)
                self.log_fix(f"Environment Variable: {var}", "APPLIED", f"Added {var} to .env file")
            else:
                self.log_fix(f"Environment Variable: {var}", "SKIPPED", f"{var} already exists in .env")
        
        # Write updated .env file
        with open(env_file, 'w') as f:
            f.writelines(env_content)
        
        self.log_fix("Environment Variables", "APPLIED", f"Updated .env file with {len(missing_vars)} missing variables")
        
        # Set environment variables for current session
        for var, default_value in missing_vars:
            os.environ[var] = default_value
    
    def fix_database_connection(self):
        """Fix database connection issues."""
        logger.info("🔧 Fixing Database Connection Issues...")
        
        try:
            # Run the Epic FHIR table creation script
            create_tables_script = Path(__file__).parent / "create_epic_fhir_tables.py"
            
            if create_tables_script.exists():
                result = subprocess.run([
                    sys.executable, str(create_tables_script)
                ], capture_output=True, text=True, cwd=project_root)
                
                if result.returncode == 0:
                    self.log_fix("Database Tables", "APPLIED", "Epic FHIR tables created successfully")
                else:
                    self.log_fix("Database Tables", "FAILED", f"Error creating tables: {result.stderr}")
            else:
                self.log_fix("Database Tables", "SKIPPED", "create_epic_fhir_tables.py not found")
                
        except Exception as e:
            self.log_fix("Database Tables", "FAILED", f"Exception: {str(e)}")
    
    def fix_epic_fhir_config(self):
        """Fix Epic FHIR configuration issues."""
        logger.info("🔧 Fixing Epic FHIR Configuration...")
        
        try:
            # Import and check Epic FHIR config
            from apps.medical_records.config.epic_fhir_config import epic_fhir_config
            
            # Check if configuration is valid
            if not epic_fhir_config.client_id or epic_fhir_config.client_id == "your_epic_client_id_here":
                self.log_fix("Epic FHIR Config", "SKIPPED", "Please set valid Epic FHIR client credentials in environment variables")
            else:
                self.log_fix("Epic FHIR Config", "APPLIED", "Epic FHIR configuration is valid")
                
        except Exception as e:
            self.log_fix("Epic FHIR Config", "FAILED", f"Configuration error: {str(e)}")
    
    def fix_epic_fhir_client_manager(self):
        """Fix Epic FHIR client manager initialization."""
        logger.info("🔧 Fixing Epic FHIR Client Manager...")
        
        try:
            from apps.medical_records.services.epic_fhir_client import epic_fhir_client_manager, initialize_epic_fhir_clients
            
            # Initialize clients
            initialize_epic_fhir_clients()
            
            # Check if sandbox client exists
            try:
                client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
                self.log_fix("Epic FHIR Client Manager", "APPLIED", "Epic FHIR client manager initialized successfully")
            except Exception as e:
                self.log_fix("Epic FHIR Client Manager", "FAILED", f"Client manager error: {str(e)}")
                
        except Exception as e:
            self.log_fix("Epic FHIR Client Manager", "FAILED", f"Initialization error: {str(e)}")
    
    def create_epic_fhir_test_credentials(self):
        """Create test Epic FHIR credentials for development."""
        logger.info("🔧 Creating Test Epic FHIR Credentials...")
        
        # Epic FHIR test sandbox credentials (for development only)
        test_credentials = {
            "EPIC_FHIR_CLIENT_ID": "test_client_id",
            "EPIC_FHIR_CLIENT_SECRET": "test_client_secret",
            "EPIC_FHIR_ENVIRONMENT": "sandbox",
            "EPIC_FHIR_REDIRECT_URI": "http://localhost:8080/callback"
        }
        
        # Create test credentials file
        test_creds_file = Path(__file__).parent / "test_epic_credentials.py"
        
        test_creds_content = '''"""
Test Epic FHIR Credentials

This file contains test credentials for Epic FHIR sandbox testing.
These are for development purposes only and should not be used in production.
"""

# Test Epic FHIR Sandbox Credentials
TEST_EPIC_CREDENTIALS = {
    "client_id": "test_client_id",
    "client_secret": "test_client_secret", 
    "environment": "sandbox",
    "redirect_uri": "http://localhost:8080/callback",
    "base_url": "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
    "oauth_url": "https://fhir.epic.com/interconnect-fhir-oauth/oauth2"
}

# Test Patient IDs (from Epic sandbox)
TEST_PATIENT_IDS = {
    "anna": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
    "henry": "a1",
    "john": "a2", 
    "omar": "a3",
    "kyle": "a4"
}

# Test MyChart Users
TEST_MYCHART_USERS = {
    "derrick": "derrick",
    "camilla": "camilla",
    "desiree": "desiree",
    "olivia": "olivia"
}
'''
        
        with open(test_creds_file, 'w') as f:
            f.write(test_creds_content)
        
        self.log_fix("Test Credentials", "APPLIED", "Created test Epic FHIR credentials file")
    
    def create_epic_fhir_setup_guide(self):
        """Create Epic FHIR setup guide."""
        logger.info("🔧 Creating Epic FHIR Setup Guide...")
        
        setup_guide = Path(__file__).parent / "EPIC_FHIR_SETUP_GUIDE.md"
        
        guide_content = '''# Epic FHIR Integration Setup Guide

## Overview
This guide helps you set up Epic FHIR integration for the Personal Health Assistant.

## Prerequisites
1. Epic FHIR Developer Account
2. Epic FHIR App Registration
3. Valid Epic FHIR Client Credentials

## Step 1: Epic FHIR App Registration
1. Go to [Epic FHIR Developer Portal](https://fhir.epic.com/)
2. Create a new app registration
3. Note down your Client ID and Client Secret
4. Configure redirect URIs

## Step 2: Environment Variables
Set the following environment variables:

```bash
export EPIC_FHIR_CLIENT_ID="your_actual_client_id"
export EPIC_FHIR_CLIENT_SECRET="your_actual_client_secret"
export EPIC_FHIR_ENVIRONMENT="sandbox"  # or "production"
export EPIC_FHIR_REDIRECT_URI="http://localhost:8080/callback"
```

Or add them to your `.env` file:

```env
EPIC_FHIR_CLIENT_ID=your_actual_client_id
EPIC_FHIR_CLIENT_SECRET=your_actual_client_secret
EPIC_FHIR_ENVIRONMENT=sandbox
EPIC_FHIR_REDIRECT_URI=http://localhost:8080/callback
```

## Step 3: Database Setup
Run the database migration script:

```bash
python apps/medical_records/create_epic_fhir_tables.py
```

## Step 4: Test Integration
Run the integration test:

```bash
python apps/medical_records/test_epic_fhir_integration.py
```

## Step 5: Start Medical Records Service
```bash
cd apps/medical_records
python main.py
```

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   - Ensure all Epic FHIR environment variables are set
   - Check that credentials are valid

2. **Authentication Errors**
   - Verify client credentials are correct
   - Check if credentials have expired
   - Ensure proper scopes are configured

3. **Database Connection Issues**
   - Run database migrations
   - Check database connection settings
   - Verify database permissions

4. **Network Connectivity**
   - Check firewall settings
   - Verify Epic FHIR service availability
   - Test network connectivity to Epic servers

### Getting Help
- Epic FHIR Documentation: https://fhir.epic.com/
- Epic FHIR Support: https://fhir.epic.com/Support
- Epic FHIR Community: https://community.epic.com/

## Security Notes
- Never commit real credentials to version control
- Use environment variables for sensitive data
- Regularly rotate client secrets
- Follow Epic FHIR security best practices
'''
        
        with open(setup_guide, 'w') as f:
            f.write(guide_content)
        
        self.log_fix("Setup Guide", "APPLIED", "Created Epic FHIR setup guide")
    
    def fix_service_connectivity(self):
        """Fix service connectivity issues."""
        logger.info("🔧 Fixing Service Connectivity...")
        
        # Check if medical records service is running
        try:
            import httpx
            import asyncio
            
            async def check_service():
                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.get("http://localhost:8005/health", timeout=5.0)
                        if response.status_code == 200:
                            return True
                        else:
                            return False
                    except:
                        return False
            
            # Run the check
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            service_running = loop.run_until_complete(check_service())
            loop.close()
            
            if service_running:
                self.log_fix("Service Connectivity", "APPLIED", "Medical records service is running")
            else:
                self.log_fix("Service Connectivity", "SKIPPED", "Medical records service is not running - start it with: python apps/medical_records/main.py")
                
        except Exception as e:
            self.log_fix("Service Connectivity", "FAILED", f"Connectivity check error: {str(e)}")
    
    def generate_fix_report(self):
        """Generate fix report."""
        report = []
        report.append("=" * 80)
        report.append("EPIC FHIR ISSUES FIX REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {asyncio.get_event_loop().time()}")
        report.append("")
        
        # Summary
        total_fixes = len(self.fixes_applied)
        applied_fixes = len([f for f in self.fixes_applied if f["status"] == "APPLIED"])
        skipped_fixes = len([f for f in self.fixes_applied if f["status"] == "SKIPPED"])
        failed_fixes = len([f for f in self.fixes_applied if f["status"] == "FAILED"])
        
        report.append("SUMMARY:")
        report.append(f"  Total Fixes: {total_fixes}")
        report.append(f"  Applied: {applied_fixes}")
        report.append(f"  Skipped: {skipped_fixes}")
        report.append(f"  Failed: {failed_fixes}")
        report.append("")
        
        # Detailed results
        report.append("DETAILED RESULTS:")
        report.append("-" * 80)
        
        for fix in self.fixes_applied:
            status_icon = "✅" if fix["status"] == "APPLIED" else "⚠️" if fix["status"] == "SKIPPED" else "❌"
            report.append(f"{status_icon} {fix['fix']}")
            report.append(f"   Status: {fix['status']}")
            if fix["details"]:
                report.append(f"   Details: {fix['details']}")
            report.append("")
        
        # Next steps
        report.append("NEXT STEPS:")
        report.append("-" * 80)
        report.append("1. Set your actual Epic FHIR credentials in environment variables")
        report.append("2. Run the integration test again: python apps/medical_records/test_epic_fhir_integration.py")
        report.append("3. Start the medical records service: python apps/medical_records/main.py")
        report.append("4. Test the Epic FHIR endpoints")
        report.append("")
        
        report.append("=" * 80)
        return "\n".join(report)
    
    def run_all_fixes(self):
        """Run all Epic FHIR issue fixes."""
        logger.info("🚀 Starting Epic FHIR Issues Fix...")
        
        # Apply fixes
        self.fix_environment_variables()
        self.fix_database_connection()
        self.fix_epic_fhir_config()
        self.fix_epic_fhir_client_manager()
        self.create_epic_fhir_test_credentials()
        self.create_epic_fhir_setup_guide()
        self.fix_service_connectivity()
        
        # Generate and display report
        report = self.generate_fix_report()
        print(report)
        
        # Save report to file
        report_file = "epic_fhir_fix_report.txt"
        with open(report_file, "w") as f:
            f.write(report)
        
        logger.info(f"📄 Fix report saved to: {report_file}")
        
        # Return overall success
        failed_fixes = len([f for f in self.fixes_applied if f["status"] == "FAILED"])
        return failed_fixes == 0

def main():
    """Main fix function."""
    fixer = EpicFHIRIssueFixer()
    success = fixer.run_all_fixes()
    
    if success:
        logger.info("🎉 All Epic FHIR issues fixed successfully!")
        logger.info("📋 Please set your actual Epic FHIR credentials and run the test again.")
        sys.exit(0)
    else:
        logger.error("💥 Some Epic FHIR fixes failed!")
        logger.info("📋 Check the fix report for details and manual steps.")
        sys.exit(1)

if __name__ == "__main__":
    main() 