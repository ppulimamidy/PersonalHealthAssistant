#!/usr/bin/env python3
"""
Oura Integration Setup Script
Interactive setup script for configuring Oura Ring integration.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.device_data.services.oura_client import OuraAPIClient, OuraAPIError


def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("🚀 Oura Ring Integration Setup")
    print("=" * 60)
    print()


def get_user_input(prompt: str, default: str = None) -> str:
    """Get user input with optional default value"""
    if default:
        prompt += f" [{default}]: "
    else:
        prompt += ": "
    
    while True:
        user_input = input(prompt).strip()
        if user_input:
            return user_input
        elif default:
            return default
        else:
            print("Please enter a value.")


def check_environment():
    """Check current environment setup"""
    print("🔍 Checking environment...")
    
    # Check if token is already set
    token = os.getenv("OURA_ACCESS_TOKEN")
    if token:
        print(f"  ✅ OURA_ACCESS_TOKEN is set (length: {len(token)})")
        return token
    else:
        print("  ❌ OURA_ACCESS_TOKEN is not set")
        return None


def get_oura_token() -> str:
    """Get Oura access token from user"""
    print("\n📋 Oura Access Token Setup")
    print("-" * 30)
    print("To get your Oura access token:")
    print("1. Go to https://cloud.ouraring.com/personal-access-tokens")
    print("2. Sign in to your Oura account")
    print("3. Click 'Create new token'")
    print("4. Give it a name (e.g., 'Personal Health Assistant')")
    print("5. Copy the generated token")
    print()
    
    while True:
        token = get_user_input("Enter your Oura access token")
        
        if len(token) < 10:
            print("❌ Token seems too short. Please check and try again.")
            continue
        
        # Test the token
        print("  🔍 Testing token...")
        try:
            asyncio.run(test_token(token))
            print("  ✅ Token is valid!")
            return token
        except Exception as e:
            print(f"  ❌ Token test failed: {e}")
            retry = get_user_input("Try again? (y/n)", "y").lower()
            if retry not in ['y', 'yes']:
                print("Setup cancelled.")
                sys.exit(0)


async def test_token(token: str):
    """Test if the Oura token is valid"""
    async with OuraAPIClient(token) as client:
        await client.test_connection()


def update_env_file(token: str):
    """Update .env file with Oura token"""
    print("\n📝 Updating .env file...")
    
    env_file = Path(".env")
    
    if env_file.exists():
        # Read existing .env file
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Check if OURA_ACCESS_TOKEN already exists
        token_line_index = None
        for i, line in enumerate(lines):
            if line.startswith("OURA_ACCESS_TOKEN="):
                token_line_index = i
                break
        
        if token_line_index is not None:
            # Update existing line
            lines[token_line_index] = f"OURA_ACCESS_TOKEN={token}\n"
            print("  ✅ Updated existing OURA_ACCESS_TOKEN")
        else:
            # Add new line
            lines.append(f"OURA_ACCESS_TOKEN={token}\n")
            print("  ✅ Added OURA_ACCESS_TOKEN")
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(lines)
    else:
        # Create new .env file
        with open(env_file, 'w') as f:
            f.write(f"OURA_ACCESS_TOKEN={token}\n")
        print("  ✅ Created new .env file with OURA_ACCESS_TOKEN")


def set_environment_variable(token: str):
    """Set environment variable for current session"""
    os.environ["OURA_ACCESS_TOKEN"] = token
    print("  ✅ Set OURA_ACCESS_TOKEN for current session")


def run_tests():
    """Run integration tests"""
    print("\n🧪 Running integration tests...")
    
    try:
        # Import and run the test script
        from scripts.test_oura_integration import main as run_oura_tests
        asyncio.run(run_oura_tests())
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        print("You can run tests manually with: python scripts/test_oura_integration.py")


def show_next_steps():
    """Show next steps after setup"""
    print("\n📋 Next Steps")
    print("-" * 20)
    print("1. ✅ Oura integration is now configured")
    print("2. 🔄 Restart your services to pick up the new environment variable")
    print("3. 🧪 Run tests: python scripts/test_oura_integration.py")
    print("4. 📚 Read the guide: docs/OURA_INTEGRATION_GUIDE.md")
    print("5. 🚀 Start using the device data service API")
    print()
    print("📖 API Endpoints:")
    print("   - Connect device: POST /api/v1/device-data/integrations/{device_id}/connect")
    print("   - Sync data: POST /api/v1/device-data/integrations/{device_id}/sync")
    print("   - Get info: GET /api/v1/device-data/integrations/{device_id}/info")
    print("   - Test connection: POST /api/v1/device-data/integrations/{device_id}/test")


def main():
    """Main setup function"""
    print_banner()
    
    # Check current environment
    existing_token = check_environment()
    
    if existing_token:
        print(f"\n✅ Oura integration appears to be already configured.")
        retry = get_user_input("Do you want to reconfigure? (y/n)", "n").lower()
        if retry not in ['y', 'yes']:
            print("Setup skipped. Using existing configuration.")
            show_next_steps()
            return
    
    # Get Oura token
    token = get_oura_token()
    
    # Update .env file
    update_env_file(token)
    
    # Set environment variable for current session
    set_environment_variable(token)
    
    # Run tests
    run_tests()
    
    # Show next steps
    show_next_steps()
    
    print("\n🎉 Setup complete!")


if __name__ == "__main__":
    main() 