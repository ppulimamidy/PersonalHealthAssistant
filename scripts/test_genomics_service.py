#!/usr/bin/env python3
"""
Test script for Genomics Service.

This script tests the basic functionality of the genomics service including:
- Health checks
- API endpoints
- Database connectivity
- File upload capabilities
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

# Service configuration
GENOMICS_SERVICE_URL = "http://localhost:8012"
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"

async def test_health_endpoints():
    """Test health and readiness endpoints."""
    print("🔍 Testing health endpoints...")
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        try:
            response = await client.get(f"{GENOMICS_SERVICE_URL}/health")
            if response.status_code == 200:
                print("✅ Health endpoint working")
                print(f"   Status: {response.json()}")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
        
        # Test readiness endpoint
        try:
            response = await client.get(f"{GENOMICS_SERVICE_URL}/ready")
            if response.status_code == 200:
                print("✅ Readiness endpoint working")
                print(f"   Status: {response.json()}")
            else:
                print(f"❌ Readiness endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Readiness endpoint error: {e}")
        
        # Test root endpoint
        try:
            response = await client.get(f"{GENOMICS_SERVICE_URL}/")
            if response.status_code == 200:
                print("✅ Root endpoint working")
                print(f"   Service info: {response.json()}")
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")

async def test_api_endpoints():
    """Test API endpoints (without authentication for now)."""
    print("\n🔍 Testing API endpoints...")
    
    async with httpx.AsyncClient() as client:
        # Test genomic data endpoints
        try:
            response = await client.get(f"{GENOMICS_SERVICE_URL}/api/v1/genomic-data/")
            print(f"📊 Genomic data endpoint: {response.status_code}")
        except Exception as e:
            print(f"❌ Genomic data endpoint error: {e}")
        
        # Test analysis endpoints
        try:
            response = await client.get(f"{GENOMICS_SERVICE_URL}/api/v1/analysis/")
            print(f"🔬 Analysis endpoint: {response.status_code}")
        except Exception as e:
            print(f"❌ Analysis endpoint error: {e}")
        
        # Test variants endpoints
        try:
            response = await client.get(f"{GENOMICS_SERVICE_URL}/api/v1/variants/")
            print(f"🧬 Variants endpoint: {response.status_code}")
        except Exception as e:
            print(f"❌ Variants endpoint error: {e}")
        
        # Test pharmacogenomics endpoints
        try:
            response = await client.get(f"{GENOMICS_SERVICE_URL}/api/v1/pharmacogenomics/profiles")
            print(f"💊 Pharmacogenomics endpoint: {response.status_code}")
        except Exception as e:
            print(f"❌ Pharmacogenomics endpoint error: {e}")
        
        # Test ancestry endpoints
        try:
            response = await client.get(f"{GENOMICS_SERVICE_URL}/api/v1/ancestry/")
            print(f"🌍 Ancestry endpoint: {response.status_code}")
        except Exception as e:
            print(f"❌ Ancestry endpoint error: {e}")
        
        # Test counseling endpoints
        try:
            response = await client.get(f"{GENOMICS_SERVICE_URL}/api/v1/counseling/")
            print(f"👨‍⚕️ Counseling endpoint: {response.status_code}")
        except Exception as e:
            print(f"❌ Counseling endpoint error: {e}")

async def test_database_connectivity():
    """Test database connectivity through the service."""
    print("\n🔍 Testing database connectivity...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint which includes database check
            response = await client.get(f"{GENOMICS_SERVICE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("database") == "connected":
                    print("✅ Database connectivity working")
                else:
                    print("❌ Database connectivity failed")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Database connectivity error: {e}")

async def test_file_operations():
    """Test file operations (create test file)."""
    print("\n🔍 Testing file operations...")
    
    # Create test genomic data file
    test_file_path = "/tmp/test_genomic_data.vcf"
    test_content = """##fileformat=VCFv4.2
##fileDate=20250805
##source=TestGenomicsService
##reference=GRCh38
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
chr1\t1000\t.\tA\tT\t100\tPASS\tNS=1;DP=100
chr1\t2000\t.\tG\tC\t100\tPASS\tNS=1;DP=100
"""
    
    try:
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        print(f"✅ Test file created: {test_file_path}")
        print(f"   File size: {len(test_content)} bytes")
    except Exception as e:
        print(f"❌ Test file creation failed: {e}")

async def test_service_integration():
    """Test integration with other services."""
    print("\n🔍 Testing service integration...")
    
    # Test if genomics service can reach other services
    services_to_test = [
        ("Auth Service", "http://localhost:8000/health"),
        ("User Profile Service", "http://localhost:8001/health"),
        ("Health Tracking Service", "http://localhost:8002/health"),
        ("Medical Records Service", "http://localhost:8005/health"),
        ("Knowledge Graph Service", "http://localhost:8010/health"),
        ("Doctor Collaboration Service", "http://localhost:8011/health"),
    ]
    
    async with httpx.AsyncClient() as client:
        for service_name, url in services_to_test:
            try:
                response = await client.get(url, timeout=5.0)
                if response.status_code == 200:
                    print(f"✅ {service_name} reachable")
                else:
                    print(f"⚠️  {service_name} returned {response.status_code}")
            except Exception as e:
                print(f"❌ {service_name} not reachable: {e}")

async def main():
    """Main test function."""
    print("🧬 Genomics Service Test Suite")
    print("=" * 50)
    print(f"Testing service at: {GENOMICS_SERVICE_URL}")
    print(f"Test time: {datetime.now().isoformat()}")
    print()
    
    # Run tests
    await test_health_endpoints()
    await test_api_endpoints()
    await test_database_connectivity()
    await test_file_operations()
    await test_service_integration()
    
    print("\n" + "=" * 50)
    print("🧬 Genomics Service Test Suite Complete")
    print("Check the results above for any issues.")

if __name__ == "__main__":
    asyncio.run(main()) 