#!/usr/bin/env python3
"""
Comprehensive Health Tracking Service Endpoint Test with Authentication
Tests all endpoints with proper JWT authentication
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8002"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyMjIyMjIyMi0yMjIyLTIyMjItMjIyMi0yMjIyMjIyMjIyMjIiLCJ1c2VyX2lkIjoiMjIyMjIyMjItMjIyMi0yMjIyLTIyMjItMjIyMjIyMjIyMjIyIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwidXNlcl90eXBlIjoidXNlciIsInBlcm1pc3Npb25zIjpbIm1lZGljYWxfcmVjb3JkczpyZWFkIiwibWVkaWNhbF9yZWNvcmRzOndyaXRlIl0sImV4cCI6MTc1MjAxMjI3NiwiaWF0IjoxNzUyMDA4Njc2LCJpc3MiOiJtZWRpY2FsLXJlY29yZHMtc2VydmljZSJ9.yJrnGKU2H1Ol7pfaZDitVY6GBfsE1CjVGAXeDz9qecU"

# Headers with authentication
HEADERS = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Test data
SAMPLE_METRIC = {
    "user_id": "22222222-2222-2222-2222-222222222222",
    "metric_type": "heart_rate",
    "value": 75.5,
    "unit": "bpm",
    "timestamp": datetime.utcnow().isoformat(),
    "source": "apple_watch",
    "metadata": {"location": "home", "activity": "resting"}
}

SAMPLE_GOAL = {
    "user_id": "22222222-2222-2222-2222-222222222222",
    "title": "Improve Heart Health",
    "description": "Maintain heart rate below 80 bpm during rest",
    "goal_type": "heart_rate",
    "target_value": 80.0,
    "current_value": 75.5,
    "unit": "bpm",
    "deadline": (datetime.utcnow() + timedelta(days=30)).isoformat(),
    "status": "active"
}

SAMPLE_SYMPTOM = {
    "user_id": "22222222-2222-2222-2222-222222222222",
    "symptom": "headache",
    "category": "neurological",
    "severity": "mild",
    "description": "Mild headache in the morning",
    "timestamp": datetime.utcnow().isoformat(),
    "duration_hours": 2,
    "triggers": ["stress", "lack of sleep"]
}

SAMPLE_VITAL_SIGN = {
    "user_id": "22222222-2222-2222-2222-222222222222",
    "vital_type": "blood_pressure",
    "systolic": 120,
    "diastolic": 80,
    "pulse": 72,
    "measurement_method": "automatic",
    "timestamp": datetime.utcnow().isoformat(),
    "location": "home",
    "notes": "Normal reading"
}

class EndpointTester:
    def __init__(self):
        self.results = []
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, method: str, endpoint: str, data: Dict[str, Any] = None, expected_status: int = 200) -> Dict[str, Any]:
        """Test a single endpoint"""
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=HEADERS) as response:
                    response_text = await response.text()
                    duration = time.time() - start_time
                    
                    result = {
                        "method": method,
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "duration": round(duration, 3),
                        "success": response.status_code == expected_status,
                        "response_size": len(response_text),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    if response.status_code != expected_status:
                        result["error"] = response_text[:200]
                    else:
                        try:
                            result["data"] = json.loads(response_text)
                        except:
                            result["data"] = response_text[:200]
                    
                    return result
                    
            elif method.upper() == "POST":
                async with self.session.post(url, headers=HEADERS, json=data) as response:
                    response_text = await response.text()
                    duration = time.time() - start_time
                    
                    result = {
                        "method": method,
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "duration": round(duration, 3),
                        "success": response.status_code == expected_status,
                        "response_size": len(response_text),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    if response.status_code != expected_status:
                        result["error"] = response_text[:200]
                    else:
                        try:
                            result["data"] = json.loads(response_text)
                        except:
                            result["data"] = response_text[:200]
                    
                    return result
                    
            elif method.upper() == "PUT":
                async with self.session.put(url, headers=HEADERS, json=data) as response:
                    response_text = await response.text()
                    duration = time.time() - start_time
                    
                    result = {
                        "method": method,
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "duration": round(duration, 3),
                        "success": response.status_code == expected_status,
                        "response_size": len(response_text),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    if response.status_code != expected_status:
                        result["error"] = response_text[:200]
                    else:
                        try:
                            result["data"] = json.loads(response_text)
                        except:
                            result["data"] = response_text[:200]
                    
                    return result
                    
            elif method.upper() == "DELETE":
                async with self.session.delete(url, headers=HEADERS) as response:
                    response_text = await response.text()
                    duration = time.time() - start_time
                    
                    result = {
                        "method": method,
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "duration": round(duration, 3),
                        "success": response.status_code == expected_status,
                        "response_size": len(response_text),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    if response.status_code != expected_status:
                        result["error"] = response_text[:200]
                    else:
                        try:
                            result["data"] = json.loads(response_text)
                        except:
                            result["data"] = response_text[:200]
                    
                    return result
                    
        except Exception as e:
            duration = time.time() - start_time
            return {
                "method": method,
                "endpoint": endpoint,
                "status_code": 0,
                "duration": round(duration, 3),
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def run_all_tests(self):
        """Run comprehensive endpoint tests"""
        print("🚀 Starting Comprehensive Health Tracking Service Endpoint Tests")
        print(f"📍 Base URL: {BASE_URL}")
        print(f"🔑 Using JWT Token: {JWT_TOKEN[:50]}...")
        print("=" * 80)
        
        # Core service endpoints
        print("\n📋 Testing Core Service Endpoints...")
        core_tests = [
            ("GET", "/health"),
            ("GET", "/ready"),
            ("GET", "/metrics"),
            ("GET", "/docs"),
            ("GET", "/redoc")
        ]
        
        for method, endpoint in core_tests:
            result = await self.test_endpoint(method, endpoint)
            self.results.append(result)
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {method} {endpoint} - {result['status_code']} ({result['duration']}s)")
        
        # API v1 endpoints
        print("\n🔌 Testing API v1 Endpoints...")
        
        # Health Metrics endpoints
        print("\n📊 Health Metrics Endpoints:")
        metrics_tests = [
            ("GET", "/api/v1/health-tracking/metrics"),
            ("POST", "/api/v1/health-tracking/metrics", SAMPLE_METRIC),
            ("GET", "/api/v1/health-tracking/metrics/22222222-2222-2222-2222-222222222222"),
            ("GET", "/api/v1/health-tracking/metrics/22222222-2222-2222-2222-222222222222/heart_rate"),
            ("GET", "/api/v1/health-tracking/metrics/22222222-2222-2222-2222-222222222222/summary"),
            ("GET", "/api/v1/health-tracking/metrics/22222222-2222-2222-2222-222222222222/trends"),
            ("DELETE", "/api/v1/health-tracking/metrics/1")
        ]
        
        for test in metrics_tests:
            if len(test) == 2:
                method, endpoint = test
                result = await self.test_endpoint(method, endpoint)
            else:
                method, endpoint, data = test
                result = await self.test_endpoint(method, endpoint, data)
            
            self.results.append(result)
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {method} {endpoint} - {result['status_code']} ({result['duration']}s)")
        
        # Health Goals endpoints
        print("\n🎯 Health Goals Endpoints:")
        goals_tests = [
            ("GET", "/api/v1/health-tracking/goals"),
            ("POST", "/api/v1/health-tracking/goals", SAMPLE_GOAL),
            ("GET", "/api/v1/health-tracking/goals/22222222-2222-2222-2222-222222222222"),
            ("PUT", "/api/v1/health-tracking/goals/1", SAMPLE_GOAL),
            ("DELETE", "/api/v1/health-tracking/goals/1")
        ]
        
        for test in goals_tests:
            if len(test) == 2:
                method, endpoint = test
                result = await self.test_endpoint(method, endpoint)
            else:
                method, endpoint, data = test
                result = await self.test_endpoint(method, endpoint, data)
            
            self.results.append(result)
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {method} {endpoint} - {result['status_code']} ({result['duration']}s)")
        
        # Symptoms endpoints
        print("\n🤒 Symptoms Endpoints:")
        symptoms_tests = [
            ("GET", "/api/v1/health-tracking/symptoms"),
            ("POST", "/api/v1/health-tracking/symptoms", SAMPLE_SYMPTOM),
            ("GET", "/api/v1/health-tracking/symptoms/22222222-2222-2222-2222-222222222222"),
            ("PUT", "/api/v1/health-tracking/symptoms/1", SAMPLE_SYMPTOM),
            ("DELETE", "/api/v1/health-tracking/symptoms/1")
        ]
        
        for test in symptoms_tests:
            if len(test) == 2:
                method, endpoint = test
                result = await self.test_endpoint(method, endpoint)
            else:
                method, endpoint, data = test
                result = await self.test_endpoint(method, endpoint, data)
            
            self.results.append(result)
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {method} {endpoint} - {result['status_code']} ({result['duration']}s)")
        
        # Vital Signs endpoints
        print("\n💓 Vital Signs Endpoints:")
        vitals_tests = [
            ("GET", "/api/v1/health-tracking/vitals"),
            ("POST", "/api/v1/health-tracking/vitals", SAMPLE_VITAL_SIGN),
            ("GET", "/api/v1/health-tracking/vitals/22222222-2222-2222-2222-222222222222"),
            ("PUT", "/api/v1/health-tracking/vitals/1", SAMPLE_VITAL_SIGN),
            ("DELETE", "/api/v1/health-tracking/vitals/1")
        ]
        
        for test in vitals_tests:
            if len(test) == 2:
                method, endpoint = test
                result = await self.test_endpoint(method, endpoint)
            else:
                method, endpoint, data = test
                result = await self.test_endpoint(method, endpoint, data)
            
            self.results.append(result)
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {method} {endpoint} - {result['status_code']} ({result['duration']}s)")
        
        # Analytics endpoints
        print("\n📈 Analytics Endpoints:")
        analytics_tests = [
            ("GET", "/api/v1/health-tracking/analytics/22222222-2222-2222-2222-222222222222/summary"),
            ("GET", "/api/v1/health-tracking/analytics/22222222-2222-2222-2222-222222222222/trends"),
            ("GET", "/api/v1/health-tracking/analytics/22222222-2222-2222-2222-222222222222/correlations"),
            ("POST", "/api/v1/health-tracking/analytics/22222222-2222-2222-2222-222222222222/anomaly-detection", {"metric_type": "heart_rate"}),
            ("POST", "/api/v1/health-tracking/analytics/22222222-2222-2222-2222-222222222222/pattern-recognition", {"metric_type": "heart_rate"})
        ]
        
        for test in analytics_tests:
            if len(test) == 2:
                method, endpoint = test
                result = await self.test_endpoint(method, endpoint)
            else:
                method, endpoint, data = test
                result = await self.test_endpoint(method, endpoint, data)
            
            self.results.append(result)
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {method} {endpoint} - {result['status_code']} ({result['duration']}s)")
        
        # Insights endpoints
        print("\n🧠 Insights Endpoints:")
        insights_tests = [
            ("GET", "/api/v1/health-tracking/insights"),
            ("GET", "/api/v1/health-tracking/insights/22222222-2222-2222-2222-222222222222"),
            ("POST", "/api/v1/health-tracking/insights/generate", {"user_id": "22222222-2222-2222-2222-222222222222"}),
            ("PUT", "/api/v1/health-tracking/insights/1", {"status": "read"}),
            ("DELETE", "/api/v1/health-tracking/insights/1")
        ]
        
        for test in insights_tests:
            if len(test) == 2:
                method, endpoint = test
                result = await self.test_endpoint(method, endpoint)
            else:
                method, endpoint, data = test
                result = await self.test_endpoint(method, endpoint, data)
            
            self.results.append(result)
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {method} {endpoint} - {result['status_code']} ({result['duration']}s)")
        
        # Devices endpoints
        print("\n📱 Devices Endpoints:")
        devices_tests = [
            ("GET", "/api/v1/health-tracking/devices"),
            ("GET", "/api/v1/health-tracking/devices/22222222-2222-2222-2222-222222222222"),
            ("POST", "/api/v1/health-tracking/devices", {"user_id": "22222222-2222-2222-2222-222222222222", "device_type": "apple_watch", "device_id": "watch123"}),
            ("PUT", "/api/v1/health-tracking/devices/1", {"status": "active"}),
            ("DELETE", "/api/v1/health-tracking/devices/1")
        ]
        
        for test in devices_tests:
            if len(test) == 2:
                method, endpoint = test
                result = await self.test_endpoint(method, endpoint)
            else:
                method, endpoint, data = test
                result = await self.test_endpoint(method, endpoint, data)
            
            self.results.append(result)
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {method} {endpoint} - {result['status_code']} ({result['duration']}s)")
        
        # Alerts endpoints
        print("\n🚨 Alerts Endpoints:")
        alerts_tests = [
            ("GET", "/api/v1/health-tracking/alerts"),
            ("GET", "/api/v1/health-tracking/alerts/22222222-2222-2222-2222-222222222222"),
            ("POST", "/api/v1/health-tracking/alerts", {"user_id": "22222222-2222-2222-2222-222222222222", "alert_type": "high_heart_rate", "message": "Heart rate elevated"}),
            ("PUT", "/api/v1/health-tracking/alerts/1", {"status": "acknowledged"}),
            ("DELETE", "/api/v1/health-tracking/alerts/1")
        ]
        
        for test in alerts_tests:
            if len(test) == 2:
                method, endpoint = test
                result = await self.test_endpoint(method, endpoint)
            else:
                method, endpoint, data = test
                result = await self.test_endpoint(method, endpoint, data)
            
            self.results.append(result)
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {method} {endpoint} - {result['status_code']} ({result['duration']}s)")
        
        # Agent endpoints
        print("\n🤖 Agent Endpoints:")
        agent_tests = [
            ("GET", "/agents/health"),
            ("POST", "/agents/anomaly-detection", {"user_id": "22222222-2222-2222-2222-222222222222", "metric_type": "heart_rate"}),
            ("POST", "/agents/trend-analysis", {"user_id": "22222222-2222-2222-2222-222222222222", "metric_type": "heart_rate"}),
            ("POST", "/agents/goal-suggestions", {"user_id": "22222222-2222-2222-2222-222222222222"}),
            ("POST", "/agents/health-coaching", {"user_id": "22222222-2222-2222-2222-222222222222"}),
            ("POST", "/agents/risk-assessment", {"user_id": "22222222-2222-2222-2222-222222222222"}),
            ("POST", "/agents/pattern-recognition", {"user_id": "22222222-2222-2222-2222-222222222222", "metric_type": "heart_rate"})
        ]
        
        for test in agent_tests:
            if len(test) == 2:
                method, endpoint = test
                result = await self.test_endpoint(method, endpoint)
            else:
                method, endpoint, data = test
                result = await self.test_endpoint(method, endpoint, data)
            
            self.results.append(result)
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {method} {endpoint} - {result['status_code']} ({result['duration']}s)")
        
        # Dashboard endpoints
        print("\n📊 Dashboard Endpoints:")
        dashboard_tests = [
            ("GET", "/dashboard/summary")
        ]
        
        for method, endpoint in dashboard_tests:
            result = await self.test_endpoint(method, endpoint)
            self.results.append(result)
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {method} {endpoint} - {result['status_code']} ({result['duration']}s)")
        
        # Test endpoints
        print("\n🧪 Test Endpoints:")
        test_tests = [
            ("POST", "/test/create-goal", SAMPLE_GOAL),
            ("POST", "/test/create-symptom", SAMPLE_SYMPTOM),
            ("POST", "/test/create-vital-sign", SAMPLE_VITAL_SIGN)
        ]
        
        for method, endpoint, data in test_tests:
            result = await self.test_endpoint(method, endpoint, data)
            self.results.append(result)
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {method} {endpoint} - {result['status_code']} ({result['duration']}s)")
        
        # Generate summary report
        await self.generate_report()
    
    async def generate_report(self):
        """Generate a comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Performance metrics
        durations = [r["duration"] for r in self.results if "duration" in r]
        if durations:
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            print(f"⏱️  Average Response Time: {avg_duration:.3f}s")
            print(f"⏱️  Fastest Response: {min_duration:.3f}s")
            print(f"⏱️  Slowest Response: {max_duration:.3f}s")
        
        # Status code breakdown
        status_codes = {}
        for result in self.results:
            status = result["status_code"]
            status_codes[status] = status_codes.get(status, 0) + 1
        
        print("\n📋 Status Code Breakdown:")
        for status, count in sorted(status_codes.items()):
            print(f"   {status}: {count} requests")
        
        # Failed tests details
        if failed_tests > 0:
            print(f"\n❌ Failed Tests Details:")
            for result in self.results:
                if not result["success"]:
                    print(f"   {result['method']} {result['endpoint']} - {result['status_code']}")
                    if "error" in result:
                        print(f"      Error: {result['error'][:100]}...")
        
        # Save detailed results to file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_test_results_{timestamp}.json"
        
        report_data = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": (successful_tests/total_tests)*100,
                "timestamp": datetime.utcnow().isoformat(),
                "base_url": BASE_URL
            },
            "performance": {
                "average_duration": avg_duration if durations else 0,
                "max_duration": max_duration if durations else 0,
                "min_duration": min_duration if durations else 0
            },
            "status_codes": status_codes,
            "detailed_results": self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {filename}")
        
        # Production readiness assessment
        print(f"\n🏭 PRODUCTION READINESS ASSESSMENT")
        print("=" * 50)
        
        critical_issues = []
        warnings = []
        
        if failed_tests > 0:
            critical_issues.append(f"{failed_tests} endpoints are failing")
        
        if avg_duration > 1.0:
            warnings.append("Average response time is above 1 second")
        
        if max_duration > 5.0:
            warnings.append("Some endpoints are very slow (>5s)")
        
        auth_failures = sum(1 for r in self.results if r["status_code"] == 401)
        if auth_failures > 0:
            critical_issues.append(f"{auth_failures} authentication failures")
        
        server_errors = sum(1 for r in self.results if r["status_code"] >= 500)
        if server_errors > 0:
            critical_issues.append(f"{server_errors} server errors (5xx)")
        
        if critical_issues:
            print("🚨 CRITICAL ISSUES:")
            for issue in critical_issues:
                print(f"   • {issue}")
            print("\n❌ NOT PRODUCTION READY")
        else:
            print("✅ No critical issues found")
        
        if warnings:
            print("\n⚠️  WARNINGS:")
            for warning in warnings:
                print(f"   • {warning}")
        
        if not critical_issues:
            print("\n✅ PRODUCTION READY")
        
        print("\n🎉 Test completed!")

async def main():
    """Main test runner"""
    async with EndpointTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 