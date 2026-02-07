#!/usr/bin/env python3
"""
Epic FHIR Integration Test Script

This script performs comprehensive testing of the Epic FHIR integration
to identify and resolve configuration issues.
"""

import os
import sys
import asyncio
import json
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from common.config.settings import get_settings
from common.utils.logging import get_logger
from apps.medical_records.config.epic_fhir_config import epic_fhir_config, EpicEnvironment
from apps.medical_records.services.epic_fhir_client import EpicFHIRClient, EpicFHIRClientConfig, epic_fhir_client_manager
from apps.medical_records.models.epic_fhir_data import EpicFHIRConnection, EpicFHIRSyncLog
from apps.medical_records.services.epic_fhir_data_service import EpicFHIRDataService

logger = get_logger(__name__)

class EpicFHIRIntegrationTester:
    """Comprehensive Epic FHIR integration tester."""
    
    def __init__(self):
        self.settings = get_settings()
        self.test_results = []
        self.errors = []
        
    def log_test_result(self, test_name: str, status: str, details: str = "", error: str = ""):
        """Log test result."""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if status == "PASS":
            logger.info(f"✅ {test_name}: {details}")
        elif status == "FAIL":
            logger.error(f"❌ {test_name}: {error}")
            self.errors.append(f"{test_name}: {error}")
        else:
            logger.warning(f"⚠️ {test_name}: {details}")
    
    def test_environment_variables(self) -> bool:
        """Test environment variable configuration."""
        logger.info("🔍 Testing Environment Variables...")
        
        # Check Epic FHIR environment variables
        epic_vars = [
            "EPIC_FHIR_CLIENT_ID",
            "EPIC_FHIR_CLIENT_SECRET", 
            "EPIC_FHIR_ENVIRONMENT",
            "EPIC_FHIR_REDIRECT_URI"
        ]
        
        missing_vars = []
        for var in epic_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.log_test_result(
                "Environment Variables",
                "FAIL",
                f"Missing environment variables: {', '.join(missing_vars)}"
            )
            return False
        
        # Check if client credentials are properly set
        client_id = os.getenv("EPIC_FHIR_CLIENT_ID")
        client_secret = os.getenv("EPIC_FHIR_CLIENT_SECRET")
        
        if not client_id or client_id.strip() == "":
            self.log_test_result(
                "Client ID Configuration",
                "FAIL",
                "EPIC_FHIR_CLIENT_ID is empty or not set"
            )
            return False
        
        if not client_secret or client_secret.strip() == "":
            self.log_test_result(
                "Client Secret Configuration", 
                "FAIL",
                "EPIC_FHIR_CLIENT_SECRET is empty or not set"
            )
            return False
        
        self.log_test_result(
            "Environment Variables",
            "PASS",
            f"All Epic FHIR environment variables configured: {', '.join(epic_vars)}"
        )
        return True
    
    def test_epic_fhir_config(self) -> bool:
        """Test Epic FHIR configuration object."""
        logger.info("🔍 Testing Epic FHIR Configuration...")
        
        try:
            # Test configuration object
            if not epic_fhir_config.client_id:
                self.log_test_result(
                    "Epic FHIR Config - Client ID",
                    "FAIL",
                    "Client ID not configured in epic_fhir_config"
                )
                return False
            
            if not epic_fhir_config.client_secret:
                self.log_test_result(
                    "Epic FHIR Config - Client Secret",
                    "FAIL", 
                    "Client secret not configured in epic_fhir_config"
                )
                return False
            
            # Test environment configuration
            if not epic_fhir_config.environment:
                self.log_test_result(
                    "Epic FHIR Config - Environment",
                    "FAIL",
                    "Environment not configured in epic_fhir_config"
                )
                return False
            
            # Test base URLs
            if not epic_fhir_config.base_url:
                self.log_test_result(
                    "Epic FHIR Config - Base URL",
                    "FAIL",
                    "Base URL not configured in epic_fhir_config"
                )
                return False
            
            self.log_test_result(
                "Epic FHIR Configuration",
                "PASS",
                f"Configuration valid - Environment: {epic_fhir_config.environment.value}, "
                f"Base URL: {epic_fhir_config.base_url}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Epic FHIR Configuration",
                "FAIL",
                f"Error testing configuration: {str(e)}"
            )
            return False
    
    async def test_epic_fhir_client_creation(self) -> bool:
        """Test Epic FHIR client creation."""
        logger.info("🔍 Testing Epic FHIR Client Creation...")
        
        try:
            # Create client configuration
            config = EpicFHIRClientConfig(
                client_id=epic_fhir_config.client_id,
                client_secret=epic_fhir_config.client_secret,
                base_url=epic_fhir_config.base_url,
                scope=epic_fhir_config.scope,
                epic_environment=epic_fhir_config.environment
            )
            
            # Create client
            client = EpicFHIRClient(config)
            
            if not client:
                self.log_test_result(
                    "Epic FHIR Client Creation",
                    "FAIL",
                    "Failed to create Epic FHIR client"
                )
                return False
            
            self.log_test_result(
                "Epic FHIR Client Creation",
                "PASS",
                f"Client created successfully with config: {config.client_id[:10]}..."
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Epic FHIR Client Creation",
                "FAIL",
                f"Error creating client: {str(e)}"
            )
            return False
    
    async def test_epic_fhir_connection(self) -> bool:
        """Test connection to Epic FHIR server."""
        logger.info("🔍 Testing Epic FHIR Server Connection...")
        
        try:
            # Get client from manager
            client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
            
            # Test connection
            result = await client.test_connection()
            
            if not result or "error" in result:
                error_msg = result.get("error", "Unknown connection error") if result else "No response from server"
                self.log_test_result(
                    "Epic FHIR Server Connection",
                    "FAIL",
                    f"Connection failed: {error_msg}"
                )
                return False
            
            self.log_test_result(
                "Epic FHIR Server Connection",
                "PASS",
                f"Connection successful - Server: {result.get('server_name', 'Unknown')}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Epic FHIR Server Connection",
                "FAIL",
                f"Connection error: {str(e)}"
            )
            return False
    
    async def test_epic_fhir_authentication(self) -> bool:
        """Test Epic FHIR authentication."""
        logger.info("🔍 Testing Epic FHIR Authentication...")
        
        try:
            # Get client from manager
            client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
            
            # Test client credentials authentication
            token = await client._authenticate_client_credentials()
            
            if not token or not token.access_token:
                self.log_test_result(
                    "Epic FHIR Authentication",
                    "FAIL",
                    "Failed to obtain access token"
                )
                return False
            
            self.log_test_result(
                "Epic FHIR Authentication",
                "PASS",
                f"Authentication successful - Token type: {token.token_type}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Epic FHIR Authentication",
                "FAIL",
                f"Authentication error: {str(e)}"
            )
            return False
    
    async def test_epic_fhir_test_patients(self) -> bool:
        """Test Epic FHIR test patient data retrieval."""
        logger.info("🔍 Testing Epic FHIR Test Patients...")
        
        try:
            # Get client from manager
            client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
            
            # Test getting available patients
            patients = await client.get_available_test_patients()
            
            if not patients:
                self.log_test_result(
                    "Epic FHIR Test Patients",
                    "FAIL",
                    "No test patients available"
                )
                return False
            
            # Test getting specific patient data
            test_patient = "anna"
            patient_data = await client.get_test_patient(test_patient)
            
            if not patient_data or "error" in patient_data:
                error_msg = patient_data.get("error", "Unknown error") if patient_data else "No patient data"
                self.log_test_result(
                    "Epic FHIR Test Patient Data",
                    "FAIL",
                    f"Failed to get patient data for {test_patient}: {error_msg}"
                )
                return False
            
            self.log_test_result(
                "Epic FHIR Test Patients",
                "PASS",
                f"Test patients available: {len(patients)}, Patient data retrieved for {test_patient}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Epic FHIR Test Patients",
                "FAIL",
                f"Test patient error: {str(e)}"
            )
            return False
    
    async def test_epic_fhir_observations(self) -> bool:
        """Test Epic FHIR observations retrieval."""
        logger.info("🔍 Testing Epic FHIR Observations...")
        
        try:
            # Get client from manager
            client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
            
            # Test getting observations for a test patient
            test_patient = "anna"
            observations = await client.get_test_patient_observations(test_patient)
            
            if not observations or "error" in observations:
                error_msg = observations.get("error", "Unknown error") if observations else "No observations data"
                self.log_test_result(
                    "Epic FHIR Observations",
                    "FAIL",
                    f"Failed to get observations for {test_patient}: {error_msg}"
                )
                return False
            
            self.log_test_result(
                "Epic FHIR Observations",
                "PASS",
                f"Observations retrieved successfully for {test_patient}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Epic FHIR Observations",
                "FAIL",
                f"Observations error: {str(e)}"
            )
            return False
    
    def test_database_connection(self) -> bool:
        """Test database connection for Epic FHIR tables."""
        logger.info("🔍 Testing Database Connection...")
        
        try:
            from common.database.connection import get_db
            from sqlalchemy import text
            
            # Test database connection
            db = next(get_db())
            
            # Test if Epic FHIR tables exist
            result = db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'epic_fhir_%'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                self.log_test_result(
                    "Database - Epic FHIR Tables",
                    "FAIL",
                    "No Epic FHIR tables found in database"
                )
                return False
            
            self.log_test_result(
                "Database - Epic FHIR Tables",
                "PASS",
                f"Epic FHIR tables found: {', '.join(tables)}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Database Connection",
                "FAIL",
                f"Database connection error: {str(e)}"
            )
            return False
    
    async def test_epic_fhir_api_endpoints(self) -> bool:
        """Test Epic FHIR API endpoints."""
        logger.info("🔍 Testing Epic FHIR API Endpoints...")
        
        try:
            # Test if the service is running
            base_url = "http://localhost:8005"  # Medical records service port
            
            async with httpx.AsyncClient() as client:
                # Test health endpoint
                response = await client.get(f"{base_url}/health")
                if response.status_code != 200:
                    self.log_test_result(
                        "API - Service Health",
                        "FAIL",
                        f"Service not responding: {response.status_code}"
                    )
                    return False
                
                # Test Epic FHIR config endpoint
                response = await client.get(f"{base_url}/api/v1/medical-records/epic-fhir/config")
                if response.status_code != 401:  # Should require authentication
                    self.log_test_result(
                        "API - Epic FHIR Config Endpoint",
                        "WARNING",
                        f"Unexpected response: {response.status_code}"
                    )
                else:
                    self.log_test_result(
                        "API - Epic FHIR Config Endpoint",
                        "PASS",
                        "Endpoint requires authentication (expected)"
                    )
            
            return True
            
        except Exception as e:
            self.log_test_result(
                "API Endpoints",
                "FAIL",
                f"API test error: {str(e)}"
            )
            return False
    
    def generate_test_report(self) -> str:
        """Generate comprehensive test report."""
        report = []
        report.append("=" * 80)
        report.append("EPIC FHIR INTEGRATION TEST REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        warning_tests = len([r for r in self.test_results if r["status"] == "WARNING"])
        
        report.append("SUMMARY:")
        report.append(f"  Total Tests: {total_tests}")
        report.append(f"  Passed: {passed_tests}")
        report.append(f"  Failed: {failed_tests}")
        report.append(f"  Warnings: {warning_tests}")
        report.append("")
        
        # Detailed results
        report.append("DETAILED RESULTS:")
        report.append("-" * 80)
        
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            report.append(f"{status_icon} {result['test']}")
            report.append(f"   Status: {result['status']}")
            if result["details"]:
                report.append(f"   Details: {result['details']}")
            if result["error"]:
                report.append(f"   Error: {result['error']}")
            report.append("")
        
        # Recommendations
        if self.errors:
            report.append("RECOMMENDATIONS:")
            report.append("-" * 80)
            report.append("Based on the test results, here are the recommended actions:")
            report.append("")
            
            for error in self.errors:
                if "Environment Variables" in error:
                    report.append("1. Set missing Epic FHIR environment variables:")
                    report.append("   export EPIC_FHIR_CLIENT_ID='your_client_id'")
                    report.append("   export EPIC_FHIR_CLIENT_SECRET='your_client_secret'")
                    report.append("   export EPIC_FHIR_ENVIRONMENT='sandbox'")
                    report.append("   export EPIC_FHIR_REDIRECT_URI='http://localhost:8080/callback'")
                    report.append("")
                
                elif "Client ID" in error or "Client Secret" in error:
                    report.append("2. Verify Epic FHIR client credentials:")
                    report.append("   - Check if credentials are valid")
                    report.append("   - Ensure credentials are properly formatted")
                    report.append("   - Contact Epic support if credentials are expired")
                    report.append("")
                
                elif "Connection" in error:
                    report.append("3. Check Epic FHIR server connectivity:")
                    report.append("   - Verify network connectivity to Epic servers")
                    report.append("   - Check if Epic FHIR service is available")
                    report.append("   - Verify firewall settings")
                    report.append("")
                
                elif "Database" in error:
                    report.append("4. Fix database issues:")
                    report.append("   - Run database migrations: python create_epic_fhir_tables.py")
                    report.append("   - Check database connection settings")
                    report.append("   - Verify database permissions")
                    report.append("")
        
        report.append("=" * 80)
        return "\n".join(report)
    
    async def run_all_tests(self) -> bool:
        """Run all Epic FHIR integration tests."""
        logger.info("🚀 Starting Epic FHIR Integration Tests...")
        
        # Run synchronous tests
        self.test_environment_variables()
        self.test_epic_fhir_config()
        self.test_database_connection()
        
        # Run asynchronous tests
        await self.test_epic_fhir_client_creation()
        await self.test_epic_fhir_connection()
        await self.test_epic_fhir_authentication()
        await self.test_epic_fhir_test_patients()
        await self.test_epic_fhir_observations()
        await self.test_epic_fhir_api_endpoints()
        
        # Generate and display report
        report = self.generate_test_report()
        print(report)
        
        # Save report to file
        report_file = "epic_fhir_test_report.txt"
        with open(report_file, "w") as f:
            f.write(report)
        
        logger.info(f"📄 Test report saved to: {report_file}")
        
        # Return overall success
        return len(self.errors) == 0

async def main():
    """Main test function."""
    tester = EpicFHIRIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("🎉 All Epic FHIR integration tests passed!")
        sys.exit(0)
    else:
        logger.error("💥 Some Epic FHIR integration tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 