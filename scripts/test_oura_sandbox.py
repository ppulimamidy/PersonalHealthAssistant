#!/usr/bin/env python3
"""
Oura Sandbox Test Script
Quick test script for Oura sandbox mode.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.device_data.services.oura_client import OuraAPIClient


async def test_sandbox():
    """Test Oura sandbox mode"""
    print("🔧 Testing Oura Sandbox Mode")
    print("=" * 40)
    
    try:
        # Create client in sandbox mode (no token needed)
        async with OuraAPIClient(use_sandbox=True) as client:
            print("✅ Sandbox client created successfully")
            
            # Test connection
            print("\n📡 Testing connection...")
            if await client.test_connection():
                print("✅ Connection successful")
            else:
                print("❌ Connection failed")
                return False
            
            # Test user info
            print("\n👤 Testing user info...")
            try:
                user_info = await client.get_user_info()
                print(f"✅ User info: {user_info}")
            except Exception as e:
                print(f"❌ User info failed: {e}")
            
            # Test data endpoints
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            print(f"\n📊 Testing data endpoints from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
            
            endpoints_to_test = [
                ("Daily Sleep", client.get_daily_sleep),
                ("Daily Activity", client.get_daily_activity),
                ("Daily Readiness", client.get_daily_readiness),
                ("Heart Rate", client.get_heart_rate),
                ("Workout", client.get_workout),
                ("Session", client.get_session),
                ("Sleep", client.get_sleep),
                ("Activity", client.get_activity),
                ("Readiness", client.get_readiness)
            ]
            
            for name, endpoint_func in endpoints_to_test:
                try:
                    data = await endpoint_func(start_date, end_date)
                    record_count = len(data.get('data', []))
                    print(f"  ✅ {name}: {record_count} records")
                except Exception as e:
                    print(f"  ❌ {name}: {e}")
            
            # Test bulk data fetch
            print("\n🔄 Testing bulk data fetch...")
            try:
                all_data = await client.get_all_data(start_date, end_date)
                print(f"✅ Bulk data fetch successful")
                print(f"   Errors: {len(all_data.get('errors', []))}")
            except Exception as e:
                print(f"❌ Bulk data fetch failed: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Sandbox test failed: {e}")
        return False


async def main():
    """Main function"""
    print("🚀 Oura Sandbox Test")
    print("=" * 50)
    print("This test uses Oura's sandbox environment - no access token required!")
    print()
    
    success = await test_sandbox()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Sandbox test completed successfully!")
        print("✅ Your Oura integration is ready for development and testing")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    print("\n📝 Next Steps:")
    print("   1. Use sandbox mode for development: export OURA_USE_SANDBOX=true")
    print("   2. Test with real data when ready: export OURA_ACCESS_TOKEN='your_token'")
    print("   3. Run full integration tests: python scripts/test_oura_integration.py")


if __name__ == "__main__":
    asyncio.run(main()) 