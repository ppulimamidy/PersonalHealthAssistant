#!/usr/bin/env python3
"""
Comprehensive Health Tracking Service Test
Tests all endpoints and functionality to ensure production readiness.
"""

import asyncio
import json
import time
from typing import Dict, Any
import aiohttp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthTrackingServiceTester:
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, method: str, endpoint: str, expected_status: int = 200, 
                          data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=headers) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=headers) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data, headers=headers) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
            elif method.upper() == "DELETE":
                async with self.session.delete(url, headers=headers) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            duration = time.time() - start_time
            success = response.status == expected_status
            
            result = {
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": response.status,
                "success": success,
                "duration": duration,
                "response_data": response_data,
                "headers": dict(response.headers)
            }
            
            if success:
                logger.info(f"✅ {method} {endpoint} - {response.status} ({duration:.3f}s)")
            else:
                logger.error(f"❌ {method} {endpoint} - Expected {expected_status}, got {response.status}")
                logger.error(f"   Response: {response_data}")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": None,
                "success": False,
                "duration": duration,
                "error": str(e),
                "response_data": None
            }
            logger.error(f"❌ {method} {endpoint} - Exception: {e}")
            return result
    
    async def run_health_checks(self):
        """Run basic health checks"""
        logger.info("🔍 Running Health Checks...")
        
        # Health endpoint
        await self.test_endpoint("GET", "/health", 200)
        
        # Readiness endpoint
        await self.test_endpoint("GET", "/ready", 200)
        
        # Metrics endpoint (Prometheus format)
        await self.test_endpoint("GET", "/metrics", 200)
        
        # API metrics endpoint (JSON format)
        await self.test_endpoint("GET", "/api/v1/health-tracking/metrics", 200)
    
    async def run_authentication_tests(self):
        """Test authentication requirements"""
        logger.info("🔐 Testing Authentication Requirements...")
        
        # Test endpoints that should return 401 without authentication
        endpoints_to_test = [
            "/api/v1/health-tracking/metrics",
            "/api/v1/health-tracking/goals",
            "/api/v1/health-tracking/symptoms",
            "/api/v1/health-tracking/vital-signs",
            "/api/v1/health-tracking/insights",
            "/api/v1/health-tracking/analytics",
            "/api/v1/health-tracking/devices",
            "/api/v1/health-tracking/alerts",
            "/dashboard/summary",
            "/agents/health"
        ]
        
        for endpoint in endpoints_to_test:
            await self.test_endpoint("GET", endpoint, 401)
    
    async def run_api_structure_tests(self):
        """Test API structure and documentation"""
        logger.info("📚 Testing API Structure...")
        
        # OpenAPI documentation
        await self.test_endpoint("GET", "/docs", 200)
        await self.test_endpoint("GET", "/redoc", 200)
        await self.test_endpoint("GET", "/openapi.json", 200)
    
    async def run_agent_endpoints_tests(self):
        """Test agent endpoints"""
        logger.info("🤖 Testing Agent Endpoints...")
        
        # Test agent endpoints (should require authentication)
        agent_endpoints = [
            ("POST", "/agents/anomaly-detection", {"user_id": "test", "data": {}}),
            ("POST", "/agents/trend-analysis", {"user_id": "test", "data": {}}),
            ("POST", "/agents/goal-suggestions", {"user_id": "test", "data": {}}),
            ("POST", "/agents/health-coaching", {"user_id": "test", "data": {}}),
            ("POST", "/agents/risk-assessment", {"user_id": "test", "data": {}}),
            ("POST", "/agents/pattern-recognition", {"user_id": "test", "data": {}})
        ]
        
        for method, endpoint, data in agent_endpoints:
            await self.test_endpoint(method, endpoint, 401, data)
    
    async def run_cors_tests(self):
        """Test CORS configuration"""
        logger.info("🌐 Testing CORS Configuration...")
        
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        }
        
        await self.test_endpoint("GET", "/health", 200, headers=headers)
    
    async def run_error_handling_tests(self):
        """Test error handling"""
        logger.info("⚠️ Testing Error Handling...")
        
        # Test non-existent endpoints
        await self.test_endpoint("GET", "/non-existent", 404)
        await self.test_endpoint("POST", "/api/v1/health-tracking/non-existent", 404)
        
        # Test invalid methods
        await self.test_endpoint("PATCH", "/health", 405)
    
    async def run_performance_tests(self):
        """Test basic performance"""
        logger.info("⚡ Testing Performance...")
        
        # Test multiple concurrent health checks
        tasks = []
        for i in range(10):
            task = self.test_endpoint("GET", "/health", 200)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate average response time
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        if successful_results:
            avg_duration = sum(r["duration"] for r in successful_results) / len(successful_results)
            logger.info(f"Average response time: {avg_duration:.3f}s")
    
    async def run_comprehensive_test(self):
        """Run all tests"""
        logger.info("🚀 Starting Comprehensive Health Tracking Service Test")
        logger.info(f"Testing service at: {self.base_url}")
        
        start_time = time.time()
        
        # Run all test suites
        await self.run_health_checks()
        await self.run_authentication_tests()
        await self.run_api_structure_tests()
        await self.run_agent_endpoints_tests()
        await self.run_cors_tests()
        await self.run_error_handling_tests()
        await self.run_performance_tests()
        
        total_time = time.time() - start_time
        logger.info(f"✅ All tests completed in {total_time:.2f}s")
        
        # Generate summary
        await self.generate_test_summary()
    
    async def generate_test_summary(self):
        """Generate a summary of test results"""
        logger.info("📊 Generating Test Summary...")
        
        summary = {
            "service_url": self.base_url,
            "test_timestamp": time.time(),
            "total_tests": len(self.test_results),
            "successful_tests": len([r for r in self.test_results if r.get("success")]),
            "failed_tests": len([r for r in self.test_results if not r.get("success")]),
            "test_results": self.test_results
        }
        
        # Save results to file
        timestamp = int(time.time())
        filename = f"health_tracking_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"📄 Test results saved to: {filename}")
        
        # Print summary
        success_rate = (summary["successful_tests"] / summary["total_tests"]) * 100 if summary["total_tests"] > 0 else 0
        logger.info(f"📈 Success Rate: {success_rate:.1f}% ({summary['successful_tests']}/{summary['total_tests']})")
        
        if summary["failed_tests"] > 0:
            logger.warning(f"⚠️ {summary['failed_tests']} tests failed. Check the results file for details.")

async def main():
    """Main test runner"""
    async with HealthTrackingServiceTester() as tester:
        await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main()) 