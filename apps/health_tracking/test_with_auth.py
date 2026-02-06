#!/usr/bin/env python3
"""
Test Health Tracking Service with JWT Authentication
Tests all endpoints with proper authentication headers.
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any, List
from datetime import datetime

# JWT token from generate_jwt.py
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIiwiZXhwIjoxNzM1NjgwMDAwLCJpYXQiOjE3MzU2NzY0MDAsImlzcyI6ImhlYWx0aC1hc3Npc3RhbnQiLCJhdWQiOiJoZWFsdGgtdHJhY2tpbmcifQ.Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8"

class HealthTrackingTester:
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers with JWT authentication"""
        return {
            "Authorization": f"Bearer {JWT_TOKEN}",
            "Content-Type": "application/json"
        }
    
    async def test_endpoint(self, method: str, endpoint: str, expected_status: int = 200, 
                          data: Dict[str, Any] = None, description: str = "") -> Dict[str, Any]:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        headers = self.get_auth_headers()
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await self.client.post(url, headers=headers, json=data or {})
            elif method.upper() == "PUT":
                response = await self.client.put(url, headers=headers, json=data or {})
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = response.status_code == expected_status
            result = {
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "success": success,
                "description": description,
                "response_time": response.elapsed.total_seconds(),
                "response_size": len(response.content) if response.content else 0
            }
            
            # Try to parse JSON response
            try:
                result["response_data"] = response.json() if response.content else None
            except:
                result["response_text"] = response.text[:500] if response.text else None
            
            if not success:
                result["error"] = f"Expected {expected_status}, got {response.status_code}"
                if response.text:
                    result["error_details"] = response.text[:200]
            
            return result
            
        except Exception as e:
            return {
                "method": method,
                "endpoint": endpoint,
                "status_code": None,
                "expected_status": expected_status,
                "success": False,
                "description": description,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_core_endpoints(self):
        """Test core service endpoints"""
        print("🔍 Testing Core Endpoints...")
        
        core_tests = [
            ("GET", "/health", 200, None, "Health check"),
            ("GET", "/ready", 200, None, "Readiness check"),
            ("GET", "/metrics", 200, None, "Prometheus metrics"),
            ("GET", "/docs", 200, None, "API documentation"),
        ]
        
        for method, endpoint, expected_status, data, description in core_tests:
            result = await self.test_endpoint(method, endpoint, expected_status, data, description)
            self.results.append(result)
            
            if result["success"]:
                print(f"✅ {method} {endpoint} - {result['status_code']} - {description}")
            else:
                print(f"❌ {method} {endpoint} - Expected {expected_status}, got {result.get('status_code', 'ERROR')} - {description}")
                if result.get("error"):
                    print(f"   Error: {result['error']}")
    
    async def test_api_endpoints(self):
        """Test API endpoints with authentication"""
        print("\n🔍 Testing API Endpoints with Authentication...")
        
        api_tests = [
            ("GET", "/api/v1/health-tracking/metrics", 200, None, "Get metrics"),
            ("GET", "/api/v1/health-tracking/goals", 200, None, "Get goals"),
            ("GET", "/api/v1/health-tracking/symptoms", 200, None, "Get symptoms"),
            ("GET", "/api/v1/health-tracking/vital-signs", 200, None, "Get vital signs"),
            ("GET", "/api/v1/health-tracking/insights", 200, None, "Get insights"),
            ("GET", "/api/v1/health-tracking/analytics", 200, None, "Get analytics"),
            ("GET", "/api/v1/health-tracking/devices", 200, None, "Get devices"),
            ("GET", "/api/v1/health-tracking/alerts", 200, None, "Get alerts"),
            
            # Test POST endpoints with sample data
            ("POST", "/api/v1/health-tracking/metrics", 201, {
                "metric_type": "heart_rate",
                "value": 75.0,
                "unit": "bpm",
                "source": "test",
                "notes": "Test metric"
            }, "Create metric"),
            
            ("POST", "/api/v1/health-tracking/goals", 201, {
                "title": "Test Goal",
                "description": "Test goal description",
                "metric_type": "heart_rate",
                "goal_type": "improvement",
                "target_value": 70.0,
                "unit": "bpm"
            }, "Create goal"),
        ]
        
        for method, endpoint, expected_status, data, description in api_tests:
            result = await self.test_endpoint(method, endpoint, expected_status, data, description)
            self.results.append(result)
            
            if result["success"]:
                print(f"✅ {method} {endpoint} - {result['status_code']} - {description}")
                if result.get("response_data") and isinstance(result["response_data"], dict):
                    if "data" in result["response_data"]:
                        count = len(result["response_data"]["data"]) if isinstance(result["response_data"]["data"], list) else 1
                        print(f"   📊 Found {count} items")
            else:
                print(f"❌ {method} {endpoint} - Expected {expected_status}, got {result.get('status_code', 'ERROR')} - {description}")
                if result.get("error"):
                    print(f"   Error: {result['error']}")
                if result.get("error_details"):
                    print(f"   Details: {result['error_details']}")
    
    async def test_agent_endpoints(self):
        """Test AI agent endpoints"""
        print("\n🤖 Testing AI Agent Endpoints...")
        
        agent_tests = [
            ("GET", "/agents/health", 200, None, "Agent health check"),
            ("POST", "/agents/anomaly-detection", 200, {
                "metric_type": "heart_rate",
                "data": [72, 75, 78, 120, 76, 74]  # Anomaly at 120
            }, "Anomaly detection"),
            ("POST", "/agents/trend-analysis", 200, {
                "metric_type": "heart_rate",
                "time_range": "7d"
            }, "Trend analysis"),
            ("POST", "/agents/goal-suggestions", 200, {
                "user_id": "123e4567-e89b-12d3-a456-426614174000"
            }, "Goal suggestions"),
            ("POST", "/agents/health-coaching", 200, {
                "topic": "exercise",
                "user_context": "beginner"
            }, "Health coaching"),
            ("POST", "/agents/risk-assessment", 200, {
                "metrics": ["heart_rate", "blood_pressure"],
                "time_range": "30d"
            }, "Risk assessment"),
            ("POST", "/agents/pattern-recognition", 200, {
                "metric_type": "heart_rate",
                "time_range": "7d"
            }, "Pattern recognition"),
        ]
        
        for method, endpoint, expected_status, data, description in agent_tests:
            result = await self.test_endpoint(method, endpoint, expected_status, data, description)
            self.results.append(result)
            
            if result["success"]:
                print(f"✅ {method} {endpoint} - {result['status_code']} - {description}")
            else:
                print(f"❌ {method} {endpoint} - Expected {expected_status}, got {result.get('status_code', 'ERROR')} - {description}")
                if result.get("error"):
                    print(f"   Error: {result['error']}")
    
    async def test_dashboard_endpoints(self):
        """Test dashboard endpoints"""
        print("\n📊 Testing Dashboard Endpoints...")
        
        dashboard_tests = [
            ("GET", "/dashboard/summary", 200, None, "Dashboard summary"),
        ]
        
        for method, endpoint, expected_status, data, description in dashboard_tests:
            result = await self.test_endpoint(method, endpoint, expected_status, data, description)
            self.results.append(result)
            
            if result["success"]:
                print(f"✅ {method} {endpoint} - {result['status_code']} - {description}")
            else:
                print(f"❌ {method} {endpoint} - Expected {expected_status}, got {result.get('status_code', 'ERROR')} - {description}")
                if result.get("error"):
                    print(f"   Error: {result['error']}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 AUTHENTICATED TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['method']} {result['endpoint']}: {result.get('error', 'Unknown error')}")
        
        print("=" * 60)
        
        if failed_tests == 0:
            print("🎉 All tests passed! Health Tracking Service is working correctly.")
        else:
            print(f"💥 {failed_tests} tests failed. Health Tracking Service has issues.")
        
        return successful_tests == total_tests

async def main():
    """Main test function"""
    print("🚀 Starting Authenticated Health Tracking Service Test")
    print("Testing service at: http://localhost:8002")
    print(f"Using JWT token: {JWT_TOKEN[:20]}...")
    
    start_time = time.time()
    
    async with HealthTrackingTester() as tester:
        await tester.test_core_endpoints()
        await tester.test_api_endpoints()
        await tester.test_agent_endpoints()
        await tester.test_dashboard_endpoints()
        
        test_duration = time.time() - start_time
        print(f"\nTest Duration: {test_duration:.2f} seconds")
        
        success = tester.print_summary()
        
        # Save detailed results to file
        with open("apps/health_tracking/test_results_auth.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "test_duration": test_duration,
                "results": tester.results
            }, f, indent=2, default=str)
        
        return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 