#!/usr/bin/env python3
"""
Debug script for metrics endpoint
"""

import asyncio
import httpx
import json
from datetime import datetime

async def debug_metrics_endpoint():
    """Debug the metrics endpoint step by step"""
    
    # Test 1: Check if service is running
    print("1. Testing service health...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8002/health")
            print(f"   Health check: {response.status_code}")
            if response.status_code == 200:
                print("   ✓ Service is running")
            else:
                print("   ✗ Service is not responding properly")
                return
        except Exception as e:
            print(f"   ✗ Service connection failed: {e}")
            return
    
    # Test 2: Test metrics endpoint without auth
    print("\n2. Testing metrics endpoint without auth...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8002/api/v1/health-tracking/metrics")
            print(f"   Metrics without auth: {response.status_code}")
            if response.status_code == 401:
                print("   ✓ Authentication required (expected)")
            else:
                print(f"   ✗ Unexpected status: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ✗ Request failed: {e}")
    
    # Test 3: Test metrics endpoint with auth
    print("\n3. Testing metrics endpoint with auth...")
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIiwiZXhwIjoxNzM1NjgwMDAwLCJpYXQiOjE3MzU2NzY0MDAsImlzcyI6ImhlYWx0aC1hc3Npc3RhbnQiLCJhdWQiOiJoZWFsdGgtdHJhY2tpbmcifQ.Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8"
    
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {jwt_token}"}
            response = await client.get(
                "http://localhost:8002/api/v1/health-tracking/metrics",
                headers=headers
            )
            print(f"   Metrics with auth: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                print("   ✓ Metrics endpoint working!")
                data = response.json()
                print(f"   Data: {json.dumps(data, indent=2)}")
            elif response.status_code == 500:
                print("   ✗ Internal server error")
                print(f"   Full response: {response.text}")
            else:
                print(f"   ✗ Unexpected status: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ✗ Request failed: {e}")
    
    # Test 4: Test with query parameters
    print("\n4. Testing metrics endpoint with query parameters...")
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {jwt_token}"}
            params = {"limit": 10, "offset": 0}
            response = await client.get(
                "http://localhost:8002/api/v1/health-tracking/metrics",
                headers=headers,
                params=params
            )
            print(f"   Metrics with params: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
        except Exception as e:
            print(f"   ✗ Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_metrics_endpoint()) 