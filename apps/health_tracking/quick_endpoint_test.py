#!/usr/bin/env python3
"""
Quick Health Tracking Service Endpoint Test
Tests specific endpoints against a running service.
"""

import asyncio
import json
import time
from typing import Dict, Any
import aiohttp
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuickEndpointTester:
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.session = None
        self.auth_token = "test_token_12345"  # Mock token for testing
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, method: str, endpoint: str, expected_status: int = 200, 
                          data: Dict[str, Any] = None, description: str = "") -> bool:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=headers) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=headers) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = response.status == expected_status
            
            if success:
                logger.info(f"✅ {method} {endpoint} - {response.status} - {description}")
            else:
                logger.error(f"❌ {method} {endpoint} - Expected {expected_status}, got {response.status} - {description}")
                if isinstance(response_data, dict) and "detail" in response_data:
                    logger.error(f"   Error: {response_data['detail']}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ {method} {endpoint} - Exception: {e} - {description}")
            return False

    async def test_core_endpoints(self):
        """Test core service endpoints"""
        logger.info("🔍 Testing Core Endpoints...")
        
        endpoints = [
            ("GET", "/health", 200, "Health check"),
            ("GET", "/ready", 200, "Readiness check"),
            ("GET", "/metrics", 200, "Prometheus metrics"),
            ("GET", "/docs", 200, "API documentation"),
        ]
        
        results = []
        for method, endpoint, expected_status, description in endpoints:
            result = await self.test_endpoint(method, endpoint, expected_status, description=description)
            results.append(result)
        
        return all(results)

    async def test_api_endpoints(self):
        """Test API endpoints"""
        logger.info("🔍 Testing API Endpoints...")
        
        endpoints = [
            ("GET", "/api/v1/health-tracking/metrics", 200, "Get metrics"),
            ("GET", "/api/v1/health-tracking/goals", 200, "Get goals"),
            ("GET", "/api/v1/health-tracking/symptoms", 200, "Get symptoms"),
            ("GET", "/api/v1/health-tracking/vital-signs", 200, "Get vital signs"),
            ("GET", "/api/v1/health-tracking/insights", 200, "Get insights"),
            ("GET", "/api/v1/health-tracking/analytics", 200, "Get analytics"),
            ("GET", "/api/v1/health-tracking/devices", 200, "Get devices"),
            ("GET", "/api/v1/health-tracking/alerts", 200, "Get alerts"),
        ]
        
        results = []
        for method, endpoint, expected_status, description in endpoints:
            result = await self.test_endpoint(method, endpoint, expected_status, description=description)
            results.append(result)
        
        return all(results)

    async def test_agent_endpoints(self):
        """Test AI agent endpoints"""
        logger.info("🤖 Testing AI Agent Endpoints...")
        
        test_data = {"user_id": "test_user", "data": {"test": "data"}}
        
        endpoints = [
            ("GET", "/agents/health", 200, "Agent health check"),
            ("POST", "/agents/anomaly-detection", 200, "Anomaly detection", test_data),
            ("POST", "/agents/trend-analysis", 200, "Trend analysis", test_data),
            ("POST", "/agents/goal-suggestions", 200, "Goal suggestions", test_data),
            ("POST", "/agents/health-coaching", 200, "Health coaching", test_data),
            ("POST", "/agents/risk-assessment", 200, "Risk assessment", test_data),
            ("POST", "/agents/pattern-recognition", 200, "Pattern recognition", test_data),
        ]
        
        results = []
        for endpoint_info in endpoints:
            if len(endpoint_info) == 4:
                method, endpoint, expected_status, description = endpoint_info
                data = None
            else:
                method, endpoint, expected_status, description, data = endpoint_info
            
            result = await self.test_endpoint(method, endpoint, expected_status, data, description=description)
            results.append(result)
        
        return all(results)

    async def test_dashboard_endpoints(self):
        """Test dashboard endpoints"""
        logger.info("📊 Testing Dashboard Endpoints...")
        
        endpoints = [
            ("GET", "/dashboard/summary", 200, "Dashboard summary"),
        ]
        
        results = []
        for method, endpoint, expected_status, description in endpoints:
            result = await self.test_endpoint(method, endpoint, expected_status, description=description)
            results.append(result)
        
        return all(results)

    async def run_quick_test(self):
        """Run all quick tests"""
        logger.info("🚀 Starting Quick Health Tracking Service Test")
        logger.info(f"Testing service at: {self.base_url}")
        
        start_time = time.time()
        
        try:
            # Test core endpoints
            core_success = await self.test_core_endpoints()
            
            # Test API endpoints
            api_success = await self.test_api_endpoints()
            
            # Test agent endpoints
            agent_success = await self.test_agent_endpoints()
            
            # Test dashboard endpoints
            dashboard_success = await self.test_dashboard_endpoints()
            
        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            return False
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Generate summary
        all_success = core_success and api_success and agent_success and dashboard_success
        
        logger.info("=" * 60)
        logger.info("📋 QUICK TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Test Duration: {total_duration:.2f} seconds")
        logger.info(f"Core Endpoints: {'✅ PASS' if core_success else '❌ FAIL'}")
        logger.info(f"API Endpoints: {'✅ PASS' if api_success else '❌ FAIL'}")
        logger.info(f"Agent Endpoints: {'✅ PASS' if agent_success else '❌ FAIL'}")
        logger.info(f"Dashboard Endpoints: {'✅ PASS' if dashboard_success else '❌ FAIL'}")
        logger.info("=" * 60)
        
        if all_success:
            logger.info("🎉 All quick tests passed!")
        else:
            logger.error("💥 Some quick tests failed!")
        
        return all_success

async def main():
    """Main test runner"""
    # Get base URL from command line argument or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8002"
    
    async with QuickEndpointTester(base_url) as tester:
        success = await tester.run_quick_test()
        
        if success:
            logger.info("✅ Health Tracking Service is responding correctly!")
            sys.exit(0)
        else:
            logger.error("❌ Health Tracking Service has issues!")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 