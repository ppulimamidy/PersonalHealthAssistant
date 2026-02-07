#!/usr/bin/env python3
"""
Epic FHIR Integration Test Script

This script tests the Epic FHIR integration to ensure it's working correctly.
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.medical_records.config.epic_fhir_config import epic_fhir_config, EpicEnvironment
from apps.medical_records.services.epic_fhir_client import EpicFHIRClient, EpicFHIRClientConfig


class EpicFHIRTester:
    """Epic FHIR integration tester."""
    
    def __init__(self):
        self.test_results = {}
    
    def print_banner(self):
        """Print test banner."""
        print("=" * 80)
        print("🧪 Epic FHIR Integration Test")
        print("=" * 80)
        print()
    
    def check_configuration(self) -> bool:
        """Check if Epic FHIR is configured."""
        print("📋 Checking Configuration")
        print("-" * 40)
        
        required_vars = [
            "EPIC_FHIR_CLIENT_ID",
            "EPIC_FHIR_CLIENT_SECRET"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print("❌ Missing required environment variables:")
            for var in missing_vars:
                print(f"   - {var}")
            print()
            print("💡 Run the setup script first:")
            print("   python scripts/setup_epic_fhir.py")
            return False
        
        print("✅ Configuration check passed")
        print(f"   Environment: {epic_fhir_config.environment.value}")
        print(f"   Base URL: {epic_fhir_config.base_url}")
        print(f"   FHIR Version: {epic_fhir_config.fhir_version}")
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to Epic FHIR server."""
        print("\n🔍 Testing Connection")
        print("-" * 40)
        
        try:
            # Create client configuration
            config = EpicFHIRClientConfig(
                client_id=epic_fhir_config.client_id,
                client_secret=epic_fhir_config.client_secret,
                epic_environment=epic_fhir_config.environment,
                scope=epic_fhir_config.scope
            )
            
            # Create client
            client = EpicFHIRClient(config)
            
            # Test connection
            print("Connecting to Epic FHIR server...")
            result = await client.test_connection()
            
            if result["status"] == "connected":
                print("✅ Connection successful!")
                print(f"   FHIR Version: {result.get('fhir_version', 'Unknown')}")
                print(f"   Server: {result.get('server_name', 'Unknown')}")
                print(f"   Environment: {result['environment']}")
                self.test_results["connection"] = True
                return True
            else:
                print("❌ Connection failed!")
                print(f"   Error: {result.get('error', 'Unknown error')}")
                self.test_results["connection"] = False
                return False
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            self.test_results["connection"] = False
            return False
    
    async def test_metadata_access(self) -> bool:
        """Test access to FHIR metadata."""
        print("\n📊 Testing Metadata Access")
        print("-" * 40)
        
        try:
            # Create client configuration
            config = EpicFHIRClientConfig(
                client_id=epic_fhir_config.client_id,
                client_secret=epic_fhir_config.client_secret,
                epic_environment=epic_fhir_config.environment,
                scope=epic_fhir_config.scope
            )
            
            # Create client
            client = EpicFHIRClient(config)
            
            # Get metadata
            print("Fetching FHIR metadata...")
            metadata = await client._make_epic_request("GET", "/metadata")
            
            if metadata:
                print("✅ Metadata access successful!")
                print(f"   FHIR Version: {metadata.get('fhirVersion', 'Unknown')}")
                print(f"   Software: {metadata.get('software', {}).get('name', 'Unknown')}")
                print(f"   Implementation: {metadata.get('implementation', {}).get('description', 'Unknown')}")
                self.test_results["metadata"] = True
                return True
            else:
                print("❌ Metadata access failed!")
                self.test_results["metadata"] = False
                return False
                
        except Exception as e:
            print(f"❌ Metadata test failed: {e}")
            self.test_results["metadata"] = False
            return False
    
    async def test_patient_access(self) -> bool:
        """Test access to test patients."""
        print("\n👥 Testing Patient Access")
        print("-" * 40)
        
        try:
            # Create client configuration
            config = EpicFHIRClientConfig(
                client_id=epic_fhir_config.client_id,
                client_secret=epic_fhir_config.client_secret,
                epic_environment=epic_fhir_config.environment,
                scope=epic_fhir_config.scope
            )
            
            # Create client
            client = EpicFHIRClient(config)
            
            # Test with Anna (the main test patient)
            print("Testing access to test patient 'anna'...")
            patient_data = await client.get_test_patient("anna")
            
            if patient_data:
                print("✅ Patient access successful!")
                patient_name = patient_data.get("name", [{}])[0].get("text", "Unknown")
                print(f"   Patient: {patient_name}")
                print(f"   Gender: {patient_data.get('gender', 'Unknown')}")
                print(f"   Birth Date: {patient_data.get('birthDate', 'Unknown')}")
                self.test_results["patient_access"] = True
                return True
            else:
                print("❌ Patient access failed!")
                self.test_results["patient_access"] = False
                return False
                
        except Exception as e:
            print(f"❌ Patient access test failed: {e}")
            self.test_results["patient_access"] = False
            return False
    
    async def test_available_patients(self) -> bool:
        """Test getting available test patients."""
        print("\n📋 Testing Available Patients")
        print("-" * 40)
        
        try:
            # Create client configuration
            config = EpicFHIRClientConfig(
                client_id=epic_fhir_config.client_id,
                client_secret=epic_fhir_config.client_secret,
                epic_environment=epic_fhir_config.environment,
                scope=epic_fhir_config.scope
            )
            
            # Create client
            client = EpicFHIRClient(config)
            
            # Get available patients
            print("Fetching available test patients...")
            patients = await client.get_available_test_patients()
            
            if patients:
                print("✅ Available patients test successful!")
                print(f"   Found {len(patients)} test patients:")
                for patient in patients:
                    if "error" not in patient:
                        print(f"   - {patient['name']}: {patient.get('display_name', 'Unknown')}")
                    else:
                        print(f"   - {patient['name']}: Error - {patient['error']}")
                self.test_results["available_patients"] = True
                return True
            else:
                print("❌ Available patients test failed!")
                self.test_results["available_patients"] = False
                return False
                
        except Exception as e:
            print(f"❌ Available patients test failed: {e}")
            self.test_results["available_patients"] = False
            return False
    
    def print_summary(self):
        """Print test summary."""
        print("\n📊 Test Summary")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print()
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print()
        
        if failed_tests == 0:
            print("🎉 All tests passed! Epic FHIR integration is working correctly.")
            print()
            print("📋 Next Steps:")
            print("1. Start the medical records service:")
            print("   cd apps/medical_records")
            print("   python main.py")
            print()
            print("2. Test the API endpoints:")
            print("   GET  /api/v1/medical-records/epic-fhir/test-connection")
            print("   GET  /api/v1/medical-records/epic-fhir/test-patients")
            print("   GET  /api/v1/medical-records/epic-fhir/test-patients/anna")
        else:
            print("⚠️  Some tests failed. Please check the configuration and try again.")
            print()
            print("🔧 Troubleshooting:")
            print("- Verify your Epic FHIR credentials")
            print("- Check network connectivity")
            print("- Ensure your app is approved in the Epic developer portal")
            print("- Review the error messages above")
    
    async def run_tests(self):
        """Run all tests."""
        self.print_banner()
        
        # Check configuration
        if not self.check_configuration():
            return
        
        # Run tests
        await self.test_connection()
        await self.test_metadata_access()
        await self.test_patient_access()
        await self.test_available_patients()
        
        # Print summary
        self.print_summary()


async def main():
    """Main function."""
    tester = EpicFHIRTester()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main()) 