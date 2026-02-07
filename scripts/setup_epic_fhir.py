#!/usr/bin/env python3
"""
Epic FHIR Integration Setup Script

This script helps set up Epic FHIR integration with the test sandbox.
It guides users through the configuration process and validates the setup.
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.medical_records.config.epic_fhir_config import epic_fhir_config, EpicEnvironment
from apps.medical_records.services.epic_fhir_client import EpicFHIRClient, EpicFHIRClientConfig


class EpicFHIRSetup:
    """Epic FHIR setup helper."""
    
    def __init__(self):
        self.config_file = project_root / ".env"
        self.setup_complete = False
    
    def print_banner(self):
        """Print setup banner."""
        print("=" * 80)
        print("🏥 Epic FHIR Integration Setup")
        print("=" * 80)
        print()
        print("This script will help you set up Epic FHIR integration with the test sandbox.")
        print("You'll need to obtain client credentials from Epic's developer portal.")
        print()
        print("📋 Prerequisites:")
        print("1. Epic developer account (https://fhir.epic.com/)")
        print("2. Epic FHIR app registration")
        print("3. Client ID and Client Secret from Epic")
        print()
    
    def get_user_input(self, prompt: str, default: Optional[str] = None) -> str:
        """Get user input with optional default."""
        if default:
            prompt = f"{prompt} (default: {default}): "
        else:
            prompt = f"{prompt}: "
        
        while True:
            value = input(prompt).strip()
            if value:
                return value
            elif default:
                return default
            else:
                print("This field is required. Please enter a value.")
    
    def get_environment_choice(self) -> EpicEnvironment:
        """Get environment choice from user."""
        print("\n🌍 Select Epic Environment:")
        print("1. Sandbox (Recommended for testing)")
        print("2. Production")
        print("3. Staging")
        
        while True:
            choice = input("Enter your choice (1-3, default: 1): ").strip()
            if not choice:
                choice = "1"
            
            if choice == "1":
                return EpicEnvironment.SANDBOX
            elif choice == "2":
                return EpicEnvironment.PRODUCTION
            elif choice == "3":
                return EpicEnvironment.STAGING
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    
    def get_scope_choice(self) -> str:
        """Get scope choice from user."""
        print("\n🔐 Select FHIR Scope:")
        print("1. Patient Read Only (launch/patient patient/*.read)")
        print("2. Patient Read/Write (launch/patient patient/*.read patient/*.write)")
        print("3. System Read Only (system/*.read)")
        print("4. System Read/Write (system/*.read system/*.write)")
        print("5. Custom scope")
        
        while True:
            choice = input("Enter your choice (1-5, default: 1): ").strip()
            if not choice:
                choice = "1"
            
            if choice == "1":
                return "launch/patient patient/*.read"
            elif choice == "2":
                return "launch/patient patient/*.read patient/*.write"
            elif choice == "3":
                return "system/*.read"
            elif choice == "4":
                return "system/*.read system/*.write"
            elif choice == "5":
                return self.get_user_input("Enter custom scope")
            else:
                print("Invalid choice. Please enter 1-5.")
    
    def collect_configuration(self) -> Dict[str, Any]:
        """Collect configuration from user."""
        print("\n📝 Configuration Setup")
        print("-" * 40)
        
        config = {}
        
        # Environment
        config["environment"] = self.get_environment_choice()
        
        # Client credentials
        print(f"\n🔑 Epic FHIR Client Credentials")
        print("You can find these in your Epic developer portal.")
        config["client_id"] = self.get_user_input("Enter your Epic FHIR Client ID")
        config["client_secret"] = self.get_user_input("Enter your Epic FHIR Client Secret")
        
        # Scope
        config["scope"] = self.get_scope_choice()
        
        # Launch URL (optional)
        print(f"\n🚀 SMART on FHIR Launch URL (Optional)")
        print("Leave blank if you don't have a launch URL yet.")
        config["launch_url"] = self.get_user_input("Enter your launch URL", "")
        
        # Redirect URI (optional)
        print(f"\n🔄 OAuth2 Redirect URI (Optional)")
        print("Leave blank to use default: http://localhost:8080/callback")
        config["redirect_uri"] = self.get_user_input("Enter your redirect URI", "http://localhost:8080/callback")
        
        return config
    
    def save_environment_variables(self, config: Dict[str, Any]):
        """Save configuration as environment variables."""
        print("\n💾 Saving Configuration")
        print("-" * 40)
        
        env_vars = {
            "EPIC_FHIR_ENVIRONMENT": config["environment"].value,
            "EPIC_FHIR_CLIENT_ID": config["client_id"],
            "EPIC_FHIR_CLIENT_SECRET": config["client_secret"],
            "EPIC_FHIR_LAUNCH_URL": config["launch_url"],
            "EPIC_FHIR_REDIRECT_URI": config["redirect_uri"]
        }
        
        # Read existing .env file
        env_content = ""
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                env_content = f.read()
        
        # Add or update Epic FHIR variables
        lines = env_content.split("\n") if env_content else []
        existing_vars = {line.split("=")[0]: line for line in lines if "=" in line}
        
        # Update with new values
        for key, value in env_vars.items():
            if value:  # Only add non-empty values
                existing_vars[key] = f"{key}={value}"
        
        # Write back to .env file
        new_content = "\n".join(existing_vars.values())
        with open(self.config_file, "w") as f:
            f.write(new_content)
        
        print(f"✅ Configuration saved to {self.config_file}")
        print("📋 Environment variables set:")
        for key, value in env_vars.items():
            if value:
                print(f"   {key}={value}")
    
    async def test_connection(self, config: Dict[str, Any]) -> bool:
        """Test connection to Epic FHIR server."""
        print("\n🔍 Testing Connection")
        print("-" * 40)
        
        try:
            # Create client configuration
            client_config = EpicFHIRClientConfig(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                epic_environment=config["environment"],
                scope=config["scope"]
            )
            
            # Create client
            client = EpicFHIRClient(client_config)
            
            # Test connection
            print("Connecting to Epic FHIR server...")
            result = await client.test_connection()
            
            if result["status"] == "connected":
                print("✅ Connection successful!")
                print(f"   FHIR Version: {result.get('fhir_version', 'Unknown')}")
                print(f"   Server: {result.get('server_name', 'Unknown')}")
                print(f"   Environment: {result['environment']}")
                return True
            else:
                print("❌ Connection failed!")
                print(f"   Error: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    async def test_patient_access(self, config: Dict[str, Any]) -> bool:
        """Test access to test patients."""
        print("\n👥 Testing Patient Access")
        print("-" * 40)
        
        try:
            # Create client configuration
            client_config = EpicFHIRClientConfig(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                epic_environment=config["environment"],
                scope=config["scope"]
            )
            
            # Create client
            client = EpicFHIRClient(client_config)
            
            # Test with Anna (the main test patient)
            print("Testing access to test patient 'anna'...")
            patient_data = await client.get_test_patient("anna")
            
            if patient_data:
                print("✅ Patient access successful!")
                patient_name = patient_data.get("name", [{}])[0].get("text", "Unknown")
                print(f"   Patient: {patient_name}")
                return True
            else:
                print("❌ Patient access failed!")
                return False
                
        except Exception as e:
            print(f"❌ Patient access test failed: {e}")
            return False
    
    def print_next_steps(self):
        """Print next steps for the user."""
        print("\n🎉 Setup Complete!")
        print("=" * 80)
        print()
        print("📋 Next Steps:")
        print("1. Start the medical records service:")
        print("   cd apps/medical_records")
        print("   python main.py")
        print()
        print("2. Test the Epic FHIR endpoints:")
        print("   GET  /api/v1/medical-records/epic-fhir/test-connection")
        print("   GET  /api/v1/medical-records/epic-fhir/test-patients")
        print("   GET  /api/v1/medical-records/epic-fhir/test-patients/anna")
        print()
        print("3. Available test patients:")
        for name in ["anna", "henry", "john", "omar", "kyle"]:
            print(f"   - {name}")
        print()
        print("4. Documentation:")
        print("   - Epic FHIR: https://fhir.epic.com/")
        print("   - Test Sandbox: https://fhir.epic.com/Documentation?docId=testpatients")
        print()
        print("🔧 Troubleshooting:")
        print("- Check your client credentials in the Epic developer portal")
        print("- Ensure your app has the correct scopes configured")
        print("- Verify your redirect URI matches your app configuration")
        print("- Check the logs for detailed error messages")
        print()
    
    async def run_setup(self):
        """Run the complete setup process."""
        self.print_banner()
        
        # Collect configuration
        config = self.collect_configuration()
        
        # Save configuration
        self.save_environment_variables(config)
        
        # Test connection
        connection_ok = await self.test_connection(config)
        
        if connection_ok:
            # Test patient access
            patient_ok = await self.test_patient_access(config)
            
            if patient_ok:
                self.setup_complete = True
                self.print_next_steps()
            else:
                print("\n⚠️  Setup completed with warnings:")
                print("   - Connection to Epic FHIR server successful")
                print("   - Patient access failed (check scopes)")
                print("\n   You may need to adjust your app's scopes in the Epic developer portal.")
        else:
            print("\n❌ Setup failed!")
            print("   Please check your configuration and try again.")
            print("   Common issues:")
            print("   - Invalid client credentials")
            print("   - Incorrect environment selection")
            print("   - Network connectivity issues")


async def main():
    """Main function."""
    setup = EpicFHIRSetup()
    await setup.run_setup()


if __name__ == "__main__":
    asyncio.run(main()) 