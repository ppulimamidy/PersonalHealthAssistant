#!/usr/bin/env python3
"""
Epic FHIR JWT Setup Script

This script helps set up JWT configuration for Epic FHIR integration,
including generating keys and providing the information needed for Epic registration.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.medical_records.services.jwt_service import jwk_service


class EpicJWTSetup:
    """Epic JWT setup helper."""
    
    def __init__(self):
        self.setup_complete = False
    
    def print_banner(self):
        """Print setup banner."""
        print("=" * 80)
        print("🔐 Epic FHIR JWT Setup")
        print("=" * 80)
        print()
        print("This script will help you set up JWT configuration for Epic FHIR integration.")
        print("You'll need this information to register your app in the Epic developer portal.")
        print()
    
    def display_jwk_set_url(self):
        """Display the JWK Set URL."""
        print("📋 JWK Set URL")
        print("-" * 40)
        jwk_set_url = jwk_service.get_jwk_set_url()
        print(f"JWK Set URL: {jwk_set_url}")
        print()
        print("💡 Use this URL in the Epic developer portal for 'Non-Production JWK Set URL'")
        print()
    
    def display_public_key(self):
        """Display the public key."""
        print("🔑 Public Key")
        print("-" * 40)
        public_key_pem = jwk_service.get_public_key_pem()
        print("Public Key (PEM format):")
        print(public_key_pem)
        print()
        print("💡 Use this public key in the Epic developer portal for 'Public Key'")
        print()
    
    def display_jwk_set(self):
        """Display the JWK Set."""
        print("🔧 JWK Set")
        print("-" * 40)
        jwk_set = jwk_service.get_jwk_set()
        print("JSON Web Key Set:")
        print(json.dumps(jwk_set, indent=2))
        print()
    
    def display_key_information(self):
        """Display key information."""
        print("📊 Key Information")
        print("-" * 40)
        print(f"Key ID: {jwk_service.key_id}")
        print(f"Algorithm: RS256")
        print(f"Key Type: RSA")
        print(f"Key Size: 2048 bits")
        print()
    
    def test_jwk_endpoint(self):
        """Test the JWK endpoint."""
        print("🧪 Testing JWK Endpoint")
        print("-" * 40)
        
        try:
            # Test JWK set generation
            jwk_set = jwk_service.get_jwk_set()
            if jwk_set and "keys" in jwk_set and len(jwk_set["keys"]) > 0:
                print("✅ JWK Set generated successfully")
                print(f"   Number of keys: {len(jwk_set['keys'])}")
                print(f"   Key ID: {jwk_set['keys'][0].get('kid', 'Unknown')}")
            else:
                print("❌ JWK Set generation failed")
                return False
            
            # Test JWT generation
            test_claims = {"sub": "test-user", "scope": "patient/*.read"}
            jwt_token = jwk_service.generate_jwt(test_claims)
            if jwt_token:
                print("✅ JWT generation successful")
                print(f"   Token length: {len(jwt_token)} characters")
            else:
                print("❌ JWT generation failed")
                return False
            
            # Test JWT verification (with a small delay to ensure token is valid)
            import time
            time.sleep(1)  # Small delay to ensure token is valid
            try:
                payload = jwk_service.verify_jwt(jwt_token)
                print("✅ JWT verification successful")
                print(f"   Subject: {payload.get('sub', 'Unknown')}")
            except Exception as e:
                print(f"❌ JWT verification failed: {e}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ JWK endpoint test failed: {e}")
            return False
    
    def save_configuration(self):
        """Save configuration to file."""
        print("💾 Saving Configuration")
        print("-" * 40)
        
        config = {
            "jwk_set_url": jwk_service.get_jwk_set_url(),
            "key_id": jwk_service.key_id,
            "algorithm": "RS256",
            "key_type": "RSA",
            "key_size": 2048,
            "public_key": jwk_service.get_public_key_pem(),
            "jwk_set": jwk_service.get_jwk_set()
        }
        
        config_file = project_root / "epic_fhir_jwt_config.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Configuration saved to: {config_file}")
        print()
    
    def print_epic_registration_instructions(self):
        """Print instructions for Epic registration."""
        print("📝 Epic Developer Portal Registration")
        print("=" * 80)
        print()
        print("Follow these steps to register your app in the Epic developer portal:")
        print()
        print("1. Go to https://fhir.epic.com/")
        print("2. Sign in to your Epic developer account")
        print("3. Create a new app or edit an existing one")
        print("4. In the app configuration, set:")
        print()
        print("   🔗 Non-Production JWK Set URL:")
        print(f"      {jwk_service.get_jwk_set_url()}")
        print()
        print("   🔑 Public Key:")
        print("      (Copy the public key shown above)")
        print()
        print("   🔄 Redirect URI:")
        print("      http://localhost:8080/api/v1/medical-records/epic-fhir/callback")
        print()
        print("5. Save the app configuration")
        print("6. Note down your Client ID and Client Secret")
        print()
        print("💡 After registration, update your .env file with:")
        print("   EPIC_FHIR_CLIENT_ID=your_client_id_here")
        print("   EPIC_FHIR_CLIENT_SECRET=your_client_secret_here")
        print()
    
    def print_next_steps(self):
        """Print next steps."""
        print("🎉 JWT Setup Complete!")
        print("=" * 80)
        print()
        print("📋 Next Steps:")
        print("1. Register your app in the Epic developer portal using the information above")
        print("2. Update your .env file with Epic credentials")
        print("3. Test the Epic FHIR integration:")
        print("   python scripts/test_epic_fhir.py")
        print()
        print("🔧 Testing:")
        print("1. Start the medical records service:")
        print("   cd apps/medical_records")
        print("   python main.py")
        print()
        print("2. Test the JWK endpoint:")
        print("   curl http://localhost:8080/api/v1/medical-records/epic-fhir/.well-known/jwks.json")
        print()
        print("3. Test the public key endpoint:")
        print("   curl -H 'Authorization: Bearer your_jwt_token' \\")
        print("        http://localhost:8080/api/v1/medical-records/epic-fhir/public-key")
        print()
    
    def run_setup(self):
        """Run the complete setup process."""
        self.print_banner()
        
        # Display all the information needed for Epic registration
        self.display_jwk_set_url()
        self.display_public_key()
        self.display_key_information()
        self.display_jwk_set()
        
        # Test the JWK functionality
        if self.test_jwk_endpoint():
            print("✅ All JWT functionality tests passed!")
        else:
            print("❌ Some JWT functionality tests failed!")
            return
        
        # Save configuration
        self.save_configuration()
        
        # Print Epic registration instructions
        self.print_epic_registration_instructions()
        
        # Print next steps
        self.print_next_steps()
        
        self.setup_complete = True


def main():
    """Main function."""
    setup = EpicJWTSetup()
    setup.run_setup()


if __name__ == "__main__":
    main() 