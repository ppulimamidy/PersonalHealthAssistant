#!/usr/bin/env python3
"""
Comprehensive Health Tracking Service Endpoint Test Suite
Tests all endpoints and functionality to ensure production readiness.
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, List, Optional
import aiohttp
import logging
from datetime import datetime, timedelta
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthTrackingComprehensiveTester:
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        self.auth_token = None
        self.test_user_id = str(uuid.uuid4())
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, method: str, endpoint: str, expected_status: int = 200, 
                          data: Dict[str, Any] = None, headers: Dict[str, str] = None,
                          description: str = "") -> Dict[str, Any]:
        """Test a single endpoint with detailed logging"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        # Add auth token if available
        if headers is None:
            headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
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
                "description": description,
                "expected_status": expected_status,
                "actual_status": response.status,
                "success": success,
                "duration": duration,
                "response_data": response_data,
                "headers": dict(response.headers),
                "timestamp": datetime.now().isoformat()
            }
            
            if success:
                logger.info(f"✅ {method} {endpoint} - {response.status} ({duration:.3f}s) - {description}")
            else:
                logger.error(f"❌ {method} {endpoint} - Expected {expected_status}, got {response.status} - {description}")
                if isinstance(response_data, dict) and "detail" in response_data:
                    logger.error(f"   Error detail: {response_data['detail']}")
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "method": method,
                "endpoint": endpoint,
                "description": description,
                "expected_status": expected_status,
                "actual_status": None,
                "success": False,
                "duration": duration,
                "error": str(e),
                "response_data": None,
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ {method} {endpoint} - Exception: {e} - {description}")
            self.test_results.append(result)
            return result

    async def setup_test_authentication(self):
        """Setup authentication for testing"""
        logger.info("🔐 Setting up test authentication...")
        
        # For now, we'll use a mock token - in production this would come from auth service
        self.auth_token = "test_token_12345"
        
        # Test authentication with a protected endpoint
        await self.test_endpoint(
            "GET", 
            "/api/v1/health-tracking/metrics", 
            200, 
            description="Test authenticated access"
        )

    async def test_health_endpoints(self):
        """Test health and monitoring endpoints"""
        logger.info("🏥 Testing Health Endpoints...")
        
        endpoints = [
            ("GET", "/health", 200, "Basic health check"),
            ("GET", "/ready", 200, "Service readiness check"),
            ("GET", "/metrics", 200, "Prometheus metrics"),
            ("GET", "/api/v1/health-tracking/metrics", 200, "API metrics"),
        ]
        
        for method, endpoint, expected_status, description in endpoints:
            await self.test_endpoint(method, endpoint, expected_status, description=description)

    async def test_authentication_requirements(self):
        """Test that protected endpoints require authentication"""
        logger.info("🔒 Testing Authentication Requirements...")
        
        # Temporarily remove auth token
        original_token = self.auth_token
        self.auth_token = None
        
        protected_endpoints = [
            ("GET", "/api/v1/health-tracking/metrics", 401, "Metrics without auth"),
            ("GET", "/api/v1/health-tracking/goals", 401, "Goals without auth"),
            ("GET", "/api/v1/health-tracking/symptoms", 401, "Symptoms without auth"),
            ("GET", "/api/v1/health-tracking/vital-signs", 401, "Vital signs without auth"),
            ("GET", "/api/v1/health-tracking/insights", 401, "Insights without auth"),
            ("GET", "/api/v1/health-tracking/analytics", 401, "Analytics without auth"),
            ("GET", "/api/v1/health-tracking/devices", 401, "Devices without auth"),
            ("GET", "/api/v1/health-tracking/alerts", 401, "Alerts without auth"),
            ("GET", "/dashboard/summary", 401, "Dashboard without auth"),
            ("GET", "/agents/health", 401, "Agents health without auth"),
        ]
        
        for method, endpoint, expected_status, description in protected_endpoints:
            await self.test_endpoint(method, endpoint, expected_status, description=description)
        
        # Restore auth token
        self.auth_token = original_token

    async def test_metrics_endpoints(self):
        """Test health metrics endpoints"""
        logger.info("📊 Testing Health Metrics Endpoints...")
        
        # Test GET endpoints
        await self.test_endpoint("GET", "/api/v1/health-tracking/metrics", 200, description="Get all metrics")
        await self.test_endpoint("GET", f"/api/v1/health-tracking/metrics?user_id={self.test_user_id}", 200, description="Get user metrics")
        
        # Test POST endpoint with sample data
        metric_data = {
            "user_id": self.test_user_id,
            "metric_type": "heart_rate",
            "value": 75.0,
            "unit": "bpm",
            "timestamp": datetime.now().isoformat(),
            "source": "test_device",
            "metadata": {"location": "resting"}
        }
        
        await self.test_endpoint("POST", "/api/v1/health-tracking/metrics", 201, data=metric_data, description="Create new metric")

    async def test_goals_endpoints(self):
        """Test health goals endpoints"""
        logger.info("🎯 Testing Health Goals Endpoints...")
        
        # Test GET endpoints
        await self.test_endpoint("GET", "/api/v1/health-tracking/goals", 200, description="Get all goals")
        await self.test_endpoint("GET", f"/api/v1/health-tracking/goals?user_id={self.test_user_id}", 200, description="Get user goals")
        
        # Test POST endpoint with sample data
        goal_data = {
            "user_id": self.test_user_id,
            "goal_type": "weight_loss",
            "target_value": 70.0,
            "current_value": 75.0,
            "unit": "kg",
            "deadline": (datetime.now() + timedelta(days=30)).isoformat(),
            "description": "Lose 5kg in 30 days"
        }
        
        await self.test_endpoint("POST", "/api/v1/health-tracking/goals", 201, data=goal_data, description="Create new goal")

    async def test_symptoms_endpoints(self):
        """Test symptoms endpoints"""
        logger.info("🤒 Testing Symptoms Endpoints...")
        
        # Test GET endpoints
        await self.test_endpoint("GET", "/api/v1/health-tracking/symptoms", 200, description="Get all symptoms")
        await self.test_endpoint("GET", f"/api/v1/health-tracking/symptoms?user_id={self.test_user_id}", 200, description="Get user symptoms")
        
        # Test POST endpoint with sample data
        symptom_data = {
            "user_id": self.test_user_id,
            "symptom_type": "headache",
            "severity": "moderate",
            "duration_hours": 2,
            "description": "Tension headache",
            "timestamp": datetime.now().isoformat(),
            "location": "forehead"
        }
        
        await self.test_endpoint("POST", "/api/v1/health-tracking/symptoms", 201, data=symptom_data, description="Create new symptom")

    async def test_vital_signs_endpoints(self):
        """Test vital signs endpoints"""
        logger.info("💓 Testing Vital Signs Endpoints...")
        
        # Test GET endpoints
        await self.test_endpoint("GET", "/api/v1/health-tracking/vital-signs", 200, description="Get all vital signs")
        await self.test_endpoint("GET", f"/api/v1/health-tracking/vital-signs?user_id={self.test_user_id}", 200, description="Get user vital signs")
        
        # Test POST endpoint with sample data
        vital_data = {
            "user_id": self.test_user_id,
            "vital_type": "blood_pressure",
            "systolic": 120,
            "diastolic": 80,
            "pulse": 72,
            "timestamp": datetime.now().isoformat(),
            "measurement_method": "automatic",
            "notes": "Morning reading"
        }
        
        await self.test_endpoint("POST", "/api/v1/health-tracking/vital-signs", 201, data=vital_data, description="Create new vital sign")

    async def test_insights_endpoints(self):
        """Test health insights endpoints"""
        logger.info("🧠 Testing Health Insights Endpoints...")
        
        # Test GET endpoints
        await self.test_endpoint("GET", "/api/v1/health-tracking/insights", 200, description="Get all insights")
        await self.test_endpoint("GET", f"/api/v1/health-tracking/insights?user_id={self.test_user_id}", 200, description="Get user insights")
        
        # Test POST endpoint with sample data
        insight_data = {
            "user_id": self.test_user_id,
            "insight_type": "trend_analysis",
            "title": "Heart Rate Trend",
            "description": "Your heart rate has been consistently improving over the past week",
            "confidence_score": 0.85,
            "recommendations": ["Continue current exercise routine", "Monitor stress levels"],
            "timestamp": datetime.now().isoformat()
        }
        
        await self.test_endpoint("POST", "/api/v1/health-tracking/insights", 201, data=insight_data, description="Create new insight")

    async def test_analytics_endpoints(self):
        """Test analytics endpoints"""
        logger.info("📈 Testing Analytics Endpoints...")
        
        # Test GET endpoints
        await self.test_endpoint("GET", "/api/v1/health-tracking/analytics", 200, description="Get analytics overview")
        await self.test_endpoint("GET", f"/api/v1/health-tracking/analytics?user_id={self.test_user_id}", 200, description="Get user analytics")
        
        # Test specific analytics endpoints
        await self.test_endpoint("GET", f"/api/v1/health-tracking/analytics/trends?user_id={self.test_user_id}", 200, description="Get trends analysis")
        await self.test_endpoint("GET", f"/api/v1/health-tracking/analytics/correlations?user_id={self.test_user_id}", 200, description="Get correlations analysis")

    async def test_devices_endpoints(self):
        """Test devices endpoints"""
        logger.info("📱 Testing Devices Endpoints...")
        
        # Test GET endpoints
        await self.test_endpoint("GET", "/api/v1/health-tracking/devices", 200, description="Get all devices")
        await self.test_endpoint("GET", f"/api/v1/health-tracking/devices?user_id={self.test_user_id}", 200, description="Get user devices")
        
        # Test POST endpoint with sample data
        device_data = {
            "user_id": self.test_user_id,
            "device_type": "smartwatch",
            "device_name": "Apple Watch Series 7",
            "device_id": "aw_12345",
            "manufacturer": "Apple",
            "model": "Series 7",
            "firmware_version": "8.5",
            "last_sync": datetime.now().isoformat(),
            "is_active": True
        }
        
        await self.test_endpoint("POST", "/api/v1/health-tracking/devices", 201, data=device_data, description="Register new device")

    async def test_alerts_endpoints(self):
        """Test alerts endpoints"""
        logger.info("🚨 Testing Alerts Endpoints...")
        
        # Test GET endpoints
        await self.test_endpoint("GET", "/api/v1/health-tracking/alerts", 200, description="Get all alerts")
        await self.test_endpoint("GET", f"/api/v1/health-tracking/alerts?user_id={self.test_user_id}", 200, description="Get user alerts")
        
        # Test POST endpoint with sample data
        alert_data = {
            "user_id": self.test_user_id,
            "alert_type": "high_heart_rate",
            "severity": "warning",
            "title": "Elevated Heart Rate Detected",
            "message": "Your heart rate is above normal resting levels",
            "metric_value": 95,
            "threshold_value": 90,
            "timestamp": datetime.now().isoformat(),
            "is_acknowledged": False
        }
        
        await self.test_endpoint("POST", "/api/v1/health-tracking/alerts", 201, data=alert_data, description="Create new alert")

    async def test_agent_endpoints(self):
        """Test AI agent endpoints"""
        logger.info("🤖 Testing AI Agent Endpoints...")
        
        # Test agent health
        await self.test_endpoint("GET", "/agents/health", 200, description="Get agents health status")
        
        # Test agent endpoints with sample data
        agent_endpoints = [
            ("POST", "/agents/anomaly-detection", {
                "user_id": self.test_user_id,
                "data": {"heart_rate": [75, 80, 85, 90, 95, 100]}
            }, "Anomaly detection"),
            ("POST", "/agents/trend-analysis", {
                "user_id": self.test_user_id,
                "data": {"metric": "heart_rate", "days": 7}
            }, "Trend analysis"),
            ("POST", "/agents/goal-suggestions", {
                "user_id": self.test_user_id,
                "data": {"current_metrics": {"weight": 75, "activity": "low"}}
            }, "Goal suggestions"),
            ("POST", "/agents/health-coaching", {
                "user_id": self.test_user_id,
                "data": {"goal": "weight_loss", "current_progress": 0.3}
            }, "Health coaching"),
            ("POST", "/agents/risk-assessment", {
                "user_id": self.test_user_id,
                "data": {"age": 30, "bmi": 25, "family_history": ["diabetes"]}
            }, "Risk assessment"),
            ("POST", "/agents/pattern-recognition", {
                "user_id": self.test_user_id,
                "data": {"metrics": ["heart_rate", "sleep", "activity"]}
            }, "Pattern recognition")
        ]
        
        for method, endpoint, data, description in agent_endpoints:
            await self.test_endpoint(method, endpoint, 200, data=data, description=description)

    async def test_dashboard_endpoints(self):
        """Test dashboard endpoints"""
        logger.info("📊 Testing Dashboard Endpoints...")
        
        await self.test_endpoint("GET", "/dashboard/summary", 200, description="Get dashboard summary")

    async def test_error_handling(self):
        """Test error handling and edge cases"""
        logger.info("⚠️ Testing Error Handling...")
        
        # Test non-existent endpoints
        await self.test_endpoint("GET", "/api/v1/health-tracking/non-existent", 404, description="Non-existent endpoint")
        await self.test_endpoint("POST", "/api/v1/health-tracking/non-existent", 404, description="Non-existent POST endpoint")
        
        # Test invalid methods
        await self.test_endpoint("PATCH", "/api/v1/health-tracking/metrics", 405, description="Invalid HTTP method")
        await self.test_endpoint("DELETE", "/health", 405, description="Invalid method on health endpoint")
        
        # Test invalid data
        invalid_metric_data = {
            "user_id": self.test_user_id,
            "metric_type": "invalid_type",
            "value": "not_a_number"
        }
        await self.test_endpoint("POST", "/api/v1/health-tracking/metrics", 422, data=invalid_metric_data, description="Invalid metric data")

    async def test_rate_limiting(self):
        """Test rate limiting functionality"""
        logger.info("⏱️ Testing Rate Limiting...")
        
        # Make multiple rapid requests to test rate limiting
        tasks = []
        for i in range(15):  # Exceed rate limit
            task = self.test_endpoint("GET", "/api/v1/health-tracking/metrics", 200, description=f"Rate limit test {i+1}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check if any requests were rate limited (429 status)
        rate_limited = [r for r in results if isinstance(r, dict) and r.get("actual_status") == 429]
        if rate_limited:
            logger.info(f"Rate limiting working: {len(rate_limited)} requests were rate limited")

    async def test_cors_configuration(self):
        """Test CORS configuration"""
        logger.info("🌐 Testing CORS Configuration...")
        
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        }
        
        await self.test_endpoint("GET", "/health", 200, headers=headers, description="CORS preflight test")

    async def test_performance(self):
        """Test performance under load"""
        logger.info("⚡ Testing Performance...")
        
        # Test concurrent requests
        start_time = time.time()
        tasks = []
        
        for i in range(20):
            task = self.test_endpoint("GET", "/health", 200, description=f"Performance test {i+1}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Calculate performance metrics
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        if successful_results:
            durations = [r["duration"] for r in successful_results]
            avg_duration = statistics.mean(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            total_time = end_time - start_time
            
            logger.info(f"Performance Results:")
            logger.info(f"  Total requests: {len(results)}")
            logger.info(f"  Successful: {len(successful_results)}")
            logger.info(f"  Total time: {total_time:.3f}s")
            logger.info(f"  Average response time: {avg_duration:.3f}s")
            logger.info(f"  Min response time: {min_duration:.3f}s")
            logger.info(f"  Max response time: {max_duration:.3f}s")

    async def test_api_documentation(self):
        """Test API documentation endpoints"""
        logger.info("📚 Testing API Documentation...")
        
        await self.test_endpoint("GET", "/docs", 200, description="OpenAPI documentation")
        await self.test_endpoint("GET", "/redoc", 200, description="ReDoc documentation")
        await self.test_endpoint("GET", "/openapi.json", 200, description="OpenAPI schema")

    async def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        logger.info("🚀 Starting Comprehensive Health Tracking Service Test Suite")
        logger.info(f"Testing service at: {self.base_url}")
        logger.info(f"Test user ID: {self.test_user_id}")
        
        start_time = time.time()
        
        try:
            # Setup
            await self.setup_test_authentication()
            
            # Core functionality tests
            await self.test_health_endpoints()
            await self.test_authentication_requirements()
            await self.test_api_documentation()
            
            # API endpoint tests
            await self.test_metrics_endpoints()
            await self.test_goals_endpoints()
            await self.test_symptoms_endpoints()
            await self.test_vital_signs_endpoints()
            await self.test_insights_endpoints()
            await self.test_analytics_endpoints()
            await self.test_devices_endpoints()
            await self.test_alerts_endpoints()
            await self.test_agent_endpoints()
            await self.test_dashboard_endpoints()
            
            # Quality and security tests
            await self.test_error_handling()
            await self.test_rate_limiting()
            await self.test_cors_configuration()
            await self.test_performance()
            
        except Exception as e:
            logger.error(f"Test suite failed with exception: {e}")
            raise
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Generate test summary
        await self.generate_test_summary(total_duration)

    async def generate_test_summary(self, total_duration: float):
        """Generate comprehensive test summary"""
        logger.info("📋 Generating Test Summary...")
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.get("success")])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Group results by endpoint category
        endpoint_categories = {}
        for result in self.test_results:
            endpoint = result.get("endpoint", "")
            if "/health" in endpoint or "/ready" in endpoint or "/metrics" in endpoint:
                category = "Health & Monitoring"
            elif "/api/v1/health-tracking/metrics" in endpoint:
                category = "Metrics API"
            elif "/api/v1/health-tracking/goals" in endpoint:
                category = "Goals API"
            elif "/api/v1/health-tracking/symptoms" in endpoint:
                category = "Symptoms API"
            elif "/api/v1/health-tracking/vital-signs" in endpoint:
                category = "Vital Signs API"
            elif "/api/v1/health-tracking/insights" in endpoint:
                category = "Insights API"
            elif "/api/v1/health-tracking/analytics" in endpoint:
                category = "Analytics API"
            elif "/api/v1/health-tracking/devices" in endpoint:
                category = "Devices API"
            elif "/api/v1/health-tracking/alerts" in endpoint:
                category = "Alerts API"
            elif "/agents" in endpoint:
                category = "AI Agents"
            elif "/dashboard" in endpoint:
                category = "Dashboard"
            elif "/docs" in endpoint or "/redoc" in endpoint or "/openapi" in endpoint:
                category = "Documentation"
            else:
                category = "Other"
            
            if category not in endpoint_categories:
                endpoint_categories[category] = {"total": 0, "success": 0, "failed": 0}
            
            endpoint_categories[category]["total"] += 1
            if result.get("success"):
                endpoint_categories[category]["success"] += 1
            else:
                endpoint_categories[category]["failed"] += 1
        
        # Calculate performance metrics
        successful_results = [r for r in self.test_results if r.get("success")]
        if successful_results:
            durations = [r["duration"] for r in successful_results]
            avg_duration = statistics.mean(durations)
            min_duration = min(durations)
            max_duration = max(durations)
        else:
            avg_duration = min_duration = max_duration = 0
        
        # Print summary
        logger.info("=" * 80)
        logger.info("🏥 HEALTH TRACKING SERVICE - COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Test Duration: {total_duration:.2f} seconds")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Successful: {successful_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info("")
        
        logger.info("📊 PERFORMANCE METRICS:")
        logger.info(f"  Average Response Time: {avg_duration:.3f}s")
        logger.info(f"  Min Response Time: {min_duration:.3f}s")
        logger.info(f"  Max Response Time: {max_duration:.3f}s")
        logger.info("")
        
        logger.info("📋 ENDPOINT CATEGORY RESULTS:")
        for category, stats in endpoint_categories.items():
            category_success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
            status_icon = "✅" if category_success_rate == 100 else "⚠️" if category_success_rate >= 80 else "❌"
            logger.info(f"  {status_icon} {category}: {stats['success']}/{stats['total']} ({category_success_rate:.1f}%)")
        logger.info("")
        
        # List failed tests
        failed_results = [r for r in self.test_results if not r.get("success")]
        if failed_results:
            logger.info("❌ FAILED TESTS:")
            for result in failed_results:
                logger.info(f"  {result['method']} {result['endpoint']} - Expected {result['expected_status']}, got {result['actual_status']}")
                if result.get('error'):
                    logger.info(f"    Error: {result['error']}")
        else:
            logger.info("✅ ALL TESTS PASSED!")
        
        logger.info("=" * 80)
        
        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"health_tracking_test_results_{timestamp}.json"
        
        summary_data = {
            "test_summary": {
                "total_duration": total_duration,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "performance": {
                    "average_duration": avg_duration,
                    "min_duration": min_duration,
                    "max_duration": max_duration
                }
            },
            "endpoint_categories": endpoint_categories,
            "detailed_results": self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        logger.info(f"📄 Detailed results saved to: {filename}")
        
        # Return success status
        return success_rate >= 95  # Consider 95%+ success rate as passing

async def main():
    """Main test runner"""
    import sys
    
    # Get base URL from command line argument or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8002"
    
    async with HealthTrackingComprehensiveTester(base_url) as tester:
        success = await tester.run_comprehensive_test()
        
        if success:
            logger.info("🎉 Health Tracking Service is PRODUCTION READY!")
            sys.exit(0)
        else:
            logger.error("💥 Health Tracking Service needs attention before production deployment!")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 