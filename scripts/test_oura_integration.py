#!/usr/bin/env python3
"""
Oura Integration Test Script
Tests the complete Oura Ring integration with the device data service.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any
import json
from uuid import uuid4

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.device_data.services.oura_client import OuraAPIClient, OuraAPIError
from apps.device_data.config.oura_config import oura_config
from apps.device_data.models.device import Device, DeviceType, DeviceStatus
from apps.device_data.services.device_integrations import OuraRingIntegration


async def test_oura_api_client():
    """Test the Oura API client directly"""
    print("🔍 Testing Oura API Client...")
    
    # Check if sandbox mode is enabled
    use_sandbox = os.getenv("OURA_USE_SANDBOX", "false").lower() == "true"
    
    if use_sandbox:
        print("🔧 Using Oura Sandbox Mode - No access token required")
        access_token = None
    else:
        # Get access token from environment
        access_token = os.getenv("OURA_ACCESS_TOKEN")
        if not access_token:
            print("❌ OURA_ACCESS_TOKEN environment variable not set")
            print("   Please set it with: export OURA_ACCESS_TOKEN='your_token_here'")
            print("   Or enable sandbox mode with: export OURA_USE_SANDBOX=true")
            return False
    
    try:
        async with OuraAPIClient(access_token, use_sandbox=use_sandbox) as client:
            # Test connection
            print("  📡 Testing connection...")
            if await client.test_connection():
                print("  ✅ Connection successful")
            else:
                print("  ❌ Connection failed")
                return False
            
            # Get user info
            print("  👤 Fetching user info...")
            user_info = await client.get_user_info()
            print(f"  ✅ User info: {user_info.get('email', 'N/A')}")
            
            # Get personal info
            print("  📋 Fetching personal info...")
            personal_info = await client.get_personal_info()
            print(f"  ✅ Personal info retrieved")
            
            # Test data fetching for last 7 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            print(f"  📊 Fetching data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
            
            # Test individual endpoints
            print("    💤 Testing sleep data...")
            sleep_data = await client.get_daily_sleep(start_date, end_date)
            print(f"    ✅ Sleep data: {len(sleep_data.get('data', []))} records")
            
            print("    🏃 Testing activity data...")
            activity_data = await client.get_daily_activity(start_date, end_date)
            print(f"    ✅ Activity data: {len(activity_data.get('data', []))} records")
            
            print("    ⚡ Testing readiness data...")
            readiness_data = await client.get_daily_readiness(start_date, end_date)
            print(f"    ✅ Readiness data: {len(readiness_data.get('data', []))} records")
            
            print("    ❤️ Testing heart rate data...")
            heart_rate_data = await client.get_heart_rate(start_date, end_date)
            print(f"    ✅ Heart rate data: {len(heart_rate_data.get('data', []))} records")
            
            # Test getting all data at once
            print("    🔄 Testing bulk data fetch...")
            all_data = await client.get_all_data(start_date, end_date)
            print(f"    ✅ All data fetched successfully")
            print(f"       Errors: {len(all_data.get('errors', []))}")
            
            return True
            
    except OuraAPIError as e:
        print(f"  ❌ Oura API Error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False


async def test_oura_integration():
    """Test the Oura integration with device data service"""
    print("\n🔧 Testing Oura Integration with Device Data Service...")
    
    # Check if sandbox mode is enabled
    use_sandbox = os.getenv("OURA_USE_SANDBOX", "false").lower() == "true"
    access_token = os.getenv("OURA_ACCESS_TOKEN", "") if not use_sandbox else ""
    
    # Create a mock device
    device = Device(
        id=uuid4(),
        user_id=uuid4(),
        name="Oura Ring Test",
        device_type=DeviceType.SMART_RING,
        manufacturer="Oura",
        model="Oura Ring Gen 3",
        serial_number="TEST123456",
        api_key=access_token,
        status=DeviceStatus.ACTIVE,
        connection_type="api",
        last_sync_at=datetime.now(),
        device_metadata={"source": "oura_ring", "test": True, "sandbox": use_sandbox}
    )
    
    try:
        # Create integration instance
        integration = OuraRingIntegration(device)
        
        # Test authentication
        print("  🔐 Testing authentication...")
        if await integration.authenticate():
            print("  ✅ Authentication successful")
        else:
            print("  ❌ Authentication failed")
            return False
        
        # Test device info
        print("  📱 Testing device info...")
        device_info = await integration.get_device_info()
        print(f"  ✅ Device info: {device_info.get('device_type', 'N/A')}")
        print(f"     Status: {device_info.get('status', 'N/A')}")
        print(f"     Supported data types: {len(device_info.get('supported_data_types', []))}")
        
        # Test connection
        print("  🔗 Testing connection...")
        if await integration.test_connection():
            print("  ✅ Connection test successful")
        else:
            print("  ❌ Connection test failed")
            return False
        
        # Test data sync for last 3 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        print(f"  📊 Testing data sync from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
        data_points = await integration.sync_data(start_date, end_date)
        
        print(f"  ✅ Data sync completed: {len(data_points)} data points")
        
        # Analyze data points by type
        data_by_type = {}
        for point in data_points:
            data_type = point.data_type.value
            if data_type not in data_by_type:
                data_by_type[data_type] = 0
            data_by_type[data_type] += 1
        
        print("  📈 Data points by type:")
        for data_type, count in data_by_type.items():
            print(f"     {data_type}: {count}")
        
        # Show sample data points
        if data_points:
            print("  📋 Sample data points:")
            for i, point in enumerate(data_points[:3]):
                print(f"     {i+1}. {point.data_type.value}: {point.value} {point.unit} at {point.timestamp}")
                print(f"        Metadata: {point.metadata}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False


async def test_oura_config():
    """Test Oura configuration"""
    print("\n⚙️ Testing Oura Configuration...")
    
    print(f"  📡 API Base URL: {oura_config.api_base_url}")
    print(f"  ⏱️ Request Timeout: {oura_config.request_timeout}s")
    print(f"  🔄 Max Retries: {oura_config.max_retries}")
    print(f"  📊 Default Sync Days: {oura_config.default_sync_days}")
    print(f"  📈 Max Sync Days: {oura_config.max_sync_days}")
    
    print("  📋 Supported Data Types:")
    for category, types in oura_config.supported_data_types.items():
        print(f"     {category}: {len(types)} types")
    
    print("  ✅ Configuration loaded successfully")
    return True


async def test_oura_endpoints():
    """Test Oura API endpoints"""
    print("\n🌐 Testing Oura API Endpoints...")
    
    # Check if sandbox mode is enabled
    use_sandbox = os.getenv("OURA_USE_SANDBOX", "false").lower() == "true"
    
    if use_sandbox:
        print("  🔧 Using Oura Sandbox Mode - No access token required")
        access_token = None
    else:
        access_token = os.getenv("OURA_ACCESS_TOKEN")
        if not access_token:
            print("  ❌ OURA_ACCESS_TOKEN not set")
            return False
    
    try:
        async with OuraAPIClient(access_token, use_sandbox=use_sandbox) as client:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            
            endpoints_to_test = [
                ("daily_sleep", client.get_daily_sleep),
                ("daily_activity", client.get_daily_activity),
                ("daily_readiness", client.get_daily_readiness),
                ("heart_rate", client.get_heart_rate),
                ("workout", client.get_workout),
                ("session", client.get_session),
                ("sleep", client.get_sleep),
                ("activity", client.get_activity),
                ("readiness", client.get_readiness)
            ]
            
            for endpoint_name, endpoint_func in endpoints_to_test:
                print(f"  🔍 Testing {endpoint_name}...")
                try:
                    data = await endpoint_func(start_date, end_date)
                    record_count = len(data.get('data', []))
                    print(f"    ✅ {endpoint_name}: {record_count} records")
                except Exception as e:
                    print(f"    ❌ {endpoint_name}: {e}")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Endpoint testing failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Starting Oura Integration Tests...")
    print("=" * 50)
    
    # Check environment
    use_sandbox = os.getenv("OURA_USE_SANDBOX", "false").lower() == "true"
    access_token = os.getenv("OURA_ACCESS_TOKEN")
    
    if not use_sandbox and not access_token:
        print("❌ OURA_ACCESS_TOKEN environment variable not set")
        print("   Please set it with: export OURA_ACCESS_TOKEN='your_token_here'")
        print("   Or enable sandbox mode with: export OURA_USE_SANDBOX=true")
        print("\n📖 To get an Oura access token:")
        print("   1. Go to https://cloud.ouraring.com/personal-access-tokens")
        print("   2. Create a new personal access token")
        print("   3. Copy the token and set it as an environment variable")
        print("\n🔧 Or use sandbox mode for testing:")
        print("   export OURA_USE_SANDBOX=true")
        return
    
    # Run tests
    tests = [
        ("Configuration", test_oura_config),
        ("API Client", test_oura_api_client),
        ("API Endpoints", test_oura_endpoints),
        ("Integration", test_oura_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Oura integration is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the output above for details.")
    
    print("\n📝 Next Steps:")
    print("   1. If all tests passed, your Oura integration is ready to use")
    print("   2. You can now use the device data service to sync Oura data")
    print("   3. Check the API documentation for available endpoints")
    print("   4. Consider setting up automated data syncing")


if __name__ == "__main__":
    asyncio.run(main()) 