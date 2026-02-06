#!/usr/bin/env python3
"""
Comprehensive Test Script for User Profile Service

This script tests all endpoints of the user profile service including:
- Profile management
- Preferences management  
- Privacy settings
- Health attributes

Run with: python test_endpoints.py
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any
import httpx
from datetime import datetime, date

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Test configuration
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/v1/user-profile"

# Test data
TEST_PROFILE_DATA = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "phone_number": "+1234567890"
}

TEST_PREFERENCES_DATA = {
    "email_notifications": True,
    "sms_notifications": False,
    "push_notifications": True,
    "theme": "dark",
    "language": "en",
    "units": "metric"
}

TEST_PRIVACY_DATA = {
    "profile_visibility": "private",
    "share_health_data": False,
    "share_medical_records": False,
    "notify_data_access": True
}

TEST_HEALTH_ATTRIBUTES_DATA = {
    "height_cm": 175.0,
    "weight_kg": 70.0,
    "primary_health_goal": "weight_loss",
    "target_weight_kg": 65.0,
    "daily_step_goal": 10000
}

# Updated endpoint paths based on actual routes
ENDPOINTS = {
    "profile": {
        "create": f"{API_PREFIX}/profile/",
        "get": f"{API_PREFIX}/profile/me",
        "update": f"{API_PREFIX}/profile/me",
        "delete": f"{API_PREFIX}/profile/me",
        "validate": f"{API_PREFIX}/profile/me/validate",
        "export": f"{API_PREFIX}/profile/me/export",
        "import": f"{API_PREFIX}/profile/me/import",
        "completion": f"{API_PREFIX}/profile/me/completion",
        "summary": f"{API_PREFIX}/profile/me/summary"
    },
    "preferences": {
        "create": f"{API_PREFIX}/preferences/preferences/",
        "get": f"{API_PREFIX}/preferences/preferences/me",
        "update": f"{API_PREFIX}/preferences/preferences/me",
        "delete": f"{API_PREFIX}/preferences/preferences/me",
        "validate": f"{API_PREFIX}/preferences/preferences/me/validate",
        "export": f"{API_PREFIX}/preferences/preferences/me/export",
        "import": f"{API_PREFIX}/preferences/preferences/me/import",
        "summary": f"{API_PREFIX}/preferences/preferences/me/summary"
    },
    "privacy": {
        "create": f"{API_PREFIX}/privacy/privacy/",
        "get": f"{API_PREFIX}/privacy/privacy/me",
        "update": f"{API_PREFIX}/privacy/privacy/me",
        "delete": f"{API_PREFIX}/privacy/privacy/me",
        "validate": f"{API_PREFIX}/privacy/privacy/me/validate",
        "export": f"{API_PREFIX}/privacy/privacy/me/export",
        "import": f"{API_PREFIX}/privacy/privacy/me/import",
        "summary": f"{API_PREFIX}/privacy/privacy/me/summary"
    },
    "health_attributes": {
        "create": f"{API_PREFIX}/health-attributes/health-attributes/",
        "get": f"{API_PREFIX}/health-attributes/health-attributes/me",
        "update": f"{API_PREFIX}/health-attributes/health-attributes/me",
        "delete": f"{API_PREFIX}/health-attributes/health-attributes/me",
        "validate": f"{API_PREFIX}/health-attributes/health-attributes/me/validate",
        "export": f"{API_PREFIX}/health-attributes/health-attributes/me/export",
        "import": f"{API_PREFIX}/health-attributes/health-attributes/me/import",
        "summary": f"{API_PREFIX}/health-attributes/health-attributes/me/summary"
    }
}

class UserProfileTester:
    """Test class for user profile service endpoints."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_user_id = 1  # Mock user ID for testing
        self.results = []
    
    async def test_health_endpoint(self) -> bool:
        """Test the health endpoint."""
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ Health endpoint working")
                return True
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
            return False
    
    async def test_root_endpoint(self) -> bool:
        """Test the root endpoint."""
        try:
            response = await self.client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                print("✅ Root endpoint working")
                return True
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
            return False
    
    async def test_profile_endpoints(self) -> bool:
        """Test profile management endpoints."""
        print("\n🔍 Testing Profile Endpoints...")
        
        try:
            # Test profile creation
            response = await self.client.post(
                f"{BASE_URL}{API_PREFIX}/profile/",
                json=TEST_PROFILE_DATA
            )
            if response.status_code == 201:
                print("✅ Profile creation working")
                profile_data = response.json()
            else:
                print(f"❌ Profile creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            # Test get profile
            response = await self.client.get(f"{BASE_URL}{API_PREFIX}/profile/me")
            if response.status_code == 200:
                print("✅ Profile retrieval working")
            else:
                print(f"❌ Profile retrieval failed: {response.status_code}")
                return False
            
            # Test profile validation
            response = await self.client.post(
                f"{BASE_URL}{API_PREFIX}/profile/me/validate",
                json=TEST_PROFILE_DATA
            )
            if response.status_code == 200:
                print("✅ Profile validation working")
            else:
                print(f"❌ Profile validation failed: {response.status_code}")
            
            # Test profile export
            response = await self.client.get(f"{BASE_URL}{API_PREFIX}/profile/me/export")
            if response.status_code == 200:
                print("✅ Profile export working")
            else:
                print(f"❌ Profile export failed: {response.status_code}")
            
            # Test profile summary
            response = await self.client.get(f"{BASE_URL}{API_PREFIX}/profile/me/summary")
            if response.status_code == 200:
                print("✅ Profile summary working")
            else:
                print(f"❌ Profile summary failed: {response.status_code}")
            
            # Test profile completion
            response = await self.client.get(f"{BASE_URL}{API_PREFIX}/profile/me/completion")
            if response.status_code == 200:
                print("✅ Profile completion working")
            else:
                print(f"❌ Profile completion failed: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ Profile endpoints error: {e}")
            return False
    
    async def test_preferences_endpoints(self) -> bool:
        """Test preferences management endpoints."""
        print("\n🔍 Testing Preferences Endpoints...")
        
        try:
            # Test preferences creation
            response = await self.client.post(
                f"{BASE_URL}{API_PREFIX}/preferences/preferences/",
                json=TEST_PREFERENCES_DATA
            )
            if response.status_code == 201:
                print("✅ Preferences creation working")
            else:
                print(f"❌ Preferences creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            # Test get preferences
            response = await self.client.get(f"{BASE_URL}{API_PREFIX}/preferences/preferences/me")
            if response.status_code == 200:
                print("✅ Preferences retrieval working")
            else:
                print(f"❌ Preferences retrieval failed: {response.status_code}")
                return False
            
            # Test preferences validation
            response = await self.client.post(
                f"{BASE_URL}{API_PREFIX}/preferences/preferences/me/validate",
                json=TEST_PREFERENCES_DATA
            )
            if response.status_code == 200:
                print("✅ Preferences validation working")
            else:
                print(f"❌ Preferences validation failed: {response.status_code}")
            
            # Test preferences export
            response = await self.client.get(f"{BASE_URL}{API_PREFIX}/preferences/preferences/me/export")
            if response.status_code == 200:
                print("✅ Preferences export working")
            else:
                print(f"❌ Preferences export failed: {response.status_code}")
            
            # Test preferences summary
            response = await self.client.get(f"{BASE_URL}{API_PREFIX}/preferences/preferences/me/summary")
            if response.status_code == 200:
                print("✅ Preferences summary working")
            else:
                print(f"❌ Preferences summary failed: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ Preferences endpoints error: {e}")
            return False
    
    async def test_privacy_endpoints(self) -> bool:
        """Test privacy settings endpoints."""
        print("\n🔍 Testing Privacy Endpoints...")
        
        try:
            # Test privacy settings creation
            response = await self.client.post(
                f"{BASE_URL}{API_PREFIX}/privacy/privacy/",
                json=TEST_PRIVACY_DATA
            )
            if response.status_code == 201:
                print("✅ Privacy settings creation working")
            else:
                print(f"❌ Privacy settings creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            # Test get privacy settings
            response = await self.client.get(f"{BASE_URL}{API_PREFIX}/privacy/privacy/me")
            if response.status_code == 200:
                print("✅ Privacy settings retrieval working")
            else:
                print(f"❌ Privacy settings retrieval failed: {response.status_code}")
                return False
            
            # Test privacy settings validation
            response = await self.client.post(
                f"{BASE_URL}{API_PREFIX}/privacy/privacy/me/validate",
                json=TEST_PRIVACY_DATA
            )
            if response.status_code == 200:
                print("✅ Privacy settings validation working")
            else:
                print(f"❌ Privacy settings validation failed: {response.status_code}")
            
            # Test privacy settings export
            response = await self.client.get(f"{BASE_URL}{API_PREFIX}/privacy/privacy/me/export")
            if response.status_code == 200:
                print("✅ Privacy settings export working")
            else:
                print(f"❌ Privacy settings export failed: {response.status_code}")
            
            # Test privacy settings summary
            response = await self.client.get(f"{BASE_URL}{API_PREFIX}/privacy/privacy/me/summary")
            if response.status_code == 200:
                print("✅ Privacy settings summary working")
            else:
                print(f"❌ Privacy settings summary failed: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ Privacy endpoints error: {e}")
            return False
    
    async def test_health_attributes_endpoints(self) -> bool:
        """Test health attributes endpoints."""
        print("\n🔍 Testing Health Attributes Endpoints...")
        
        try:
            # Test health attributes creation
            response = await self.client.post(
                f"{BASE_URL}{API_PREFIX}/health-attributes/health-attributes/",
                json=TEST_HEALTH_ATTRIBUTES_DATA
            )
            if response.status_code == 201:
                print("✅ Health attributes creation working")
            else:
                print(f"❌ Health attributes creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            # Test get health attributes
            response = await self.client.get(f"{BASE_URL}{API_PREFIX}/health-attributes/health-attributes/me")
            if response.status_code == 200:
                print("✅ Health attributes retrieval working")
            else:
                print(f"❌ Health attributes retrieval failed: {response.status_code}")
                return False
            
            # Test health attributes validation
            response = await self.client.post(
                f"{BASE_URL}{API_PREFIX}/health-attributes/health-attributes/me/validate",
                json=TEST_HEALTH_ATTRIBUTES_DATA
            )
            if response.status_code == 200:
                print("✅ Health attributes validation working")
            else:
                print(f"❌ Health attributes validation failed: {response.status_code}")
            
            # Test health attributes export
            response = await self.client.get(f"{BASE_URL}{API_PREFIX}/health-attributes/health-attributes/me/export")
            if response.status_code == 200:
                print("✅ Health attributes export working")
            else:
                print(f"❌ Health attributes export failed: {response.status_code}")
            
            # Test health attributes summary
            response = await self.client.get(f"{BASE_URL}{API_PREFIX}/health-attributes/health-attributes/me/summary")
            if response.status_code == 200:
                print("✅ Health attributes summary working")
            else:
                print(f"❌ Health attributes summary failed: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ Health attributes endpoints error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting User Profile Service End-to-End Tests")
        print("=" * 60)
        
        # Test basic endpoints
        health_ok = await self.test_health_endpoint()
        root_ok = await self.test_root_endpoint()
        
        if not health_ok or not root_ok:
            print("❌ Basic endpoints failed. Service may not be running.")
            return
        
        # Test all service endpoints
        profile_ok = await self.test_profile_endpoints()
        preferences_ok = await self.test_preferences_endpoints()
        privacy_ok = await self.test_privacy_endpoints()
        health_attrs_ok = await self.test_health_attributes_endpoints()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Health Endpoint: {'✅ PASS' if health_ok else '❌ FAIL'}")
        print(f"Root Endpoint: {'✅ PASS' if root_ok else '❌ FAIL'}")
        print(f"Profile Endpoints: {'✅ PASS' if profile_ok else '❌ FAIL'}")
        print(f"Preferences Endpoints: {'✅ PASS' if preferences_ok else '❌ FAIL'}")
        print(f"Privacy Endpoints: {'✅ PASS' if privacy_ok else '❌ FAIL'}")
        print(f"Health Attributes Endpoints: {'✅ PASS' if health_attrs_ok else '❌ FAIL'}")
        
        all_passed = all([health_ok, root_ok, profile_ok, preferences_ok, privacy_ok, health_attrs_ok])
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED! User Profile Service is working correctly.")
        else:
            print("\n⚠️  SOME TESTS FAILED. Please check the service configuration.")
        
        await self.client.aclose()


async def main():
    """Main test function."""
    tester = UserProfileTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 