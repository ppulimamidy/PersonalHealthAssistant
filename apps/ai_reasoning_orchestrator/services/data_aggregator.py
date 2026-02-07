"""
Data Aggregator Service
Aggregates data from all microservices to provide unified view for AI reasoning.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx
from common.utils.logging import get_logger
from common.utils.resilience import CircuitBreaker, RetryHandler, TimeoutHandler

logger = get_logger(__name__)

class DataAggregator:
    """Aggregates health data from multiple microservices"""
    
    def __init__(self, service_registry: Dict[str, Any]):
        self.service_registry = service_registry
        self.logger = logger
    
    async def aggregate_user_data(
        self, 
        user_id: str, 
        time_window: str = "24h",
        data_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Aggregate user data from all relevant microservices.
        
        Args:
            user_id: User ID
            time_window: Time window for data collection
            data_types: Types of data to collect
            
        Returns:
            Aggregated user data
        """
        if data_types is None:
            data_types = ["vitals", "symptoms", "medications", "nutrition"]
        
        self.logger.info(f"🔄 Aggregating data for user {user_id} over {time_window}")
        
        # Collect data from all services in parallel
        tasks = []
        
        if "vitals" in data_types:
            tasks.append(self._get_vitals_data(user_id, time_window))
        
        if "symptoms" in data_types:
            tasks.append(self._get_symptoms_data(user_id, time_window))
        
        if "medications" in data_types:
            tasks.append(self._get_medications_data(user_id, time_window))
        
        if "nutrition" in data_types:
            tasks.append(self._get_nutrition_data(user_id, time_window))
        
        if "sleep" in data_types:
            tasks.append(self._get_sleep_data(user_id, time_window))
        
        if "activity" in data_types:
            tasks.append(self._get_activity_data(user_id, time_window))
        
        if "lab_results" in data_types:
            tasks.append(self._get_lab_results_data(user_id, time_window))
        
        if "medical_records" in data_types:
            tasks.append(self._get_medical_records_data(user_id, time_window))
        
        if "device_data" in data_types:
            tasks.append(self._get_device_data(user_id, time_window))
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        aggregated_data = {
            "user_id": user_id,
            "time_window": time_window,
            "timestamp": datetime.utcnow().isoformat(),
            "data_sources": data_types,
            "vitals": {},
            "symptoms": [],
            "medications": [],
            "nutrition": [],
            "sleep": [],
            "activity": [],
            "lab_results": [],
            "medical_records": [],
            "device_data": [],
            "summary": {}
        }
        
        # Process results and handle exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.warning(f"⚠️ Failed to fetch {data_types[i]} data: {result}")
                continue
            
            if result and isinstance(result, dict):
                data_type = data_types[i]
                aggregated_data[data_type] = result.get("data", [])
        
        # Generate summary statistics
        aggregated_data["summary"] = self._generate_summary(aggregated_data)
        
        self.logger.info(f"✅ Data aggregation completed for user {user_id}")
        return aggregated_data
    
    async def _get_vitals_data(self, user_id: str, time_window: str) -> Dict[str, Any]:
        """Get vital signs data from health tracking service"""
        try:
            service_config = self.service_registry.get("health_tracking")
            if not service_config:
                return {"data": []}
            
            url = f"{service_config['url']}/api/v1/health-tracking/vitals"
            params = {
                "user_id": user_id,
                "time_window": time_window,
                "limit": 100
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to fetch vitals data: {response.status_code}")
                    return {"data": []}
        except Exception as e:
            self.logger.error(f"Error fetching vitals data: {e}")
            return {"data": []}
    
    async def _get_symptoms_data(self, user_id: str, time_window: str) -> Dict[str, Any]:
        """Get symptoms data from health tracking service"""
        try:
            service_config = self.service_registry.get("health_tracking")
            if not service_config:
                return {"data": []}
            
            url = f"{service_config['url']}/api/v1/health-tracking/symptoms"
            params = {
                "user_id": user_id,
                "time_window": time_window,
                "limit": 50
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to fetch symptoms data: {response.status_code}")
                    return {"data": []}
        except Exception as e:
            self.logger.error(f"Error fetching symptoms data: {e}")
            return {"data": []}
    
    async def _get_medications_data(self, user_id: str, time_window: str) -> Dict[str, Any]:
        """Get medications data from medical records service"""
        try:
            service_config = self.service_registry.get("medical_records")
            if not service_config:
                return {"data": []}
            
            url = f"{service_config['url']}/api/v1/medical-records/medications"
            params = {
                "user_id": user_id,
                "time_window": time_window,
                "limit": 50
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to fetch medications data: {response.status_code}")
                    return {"data": []}
        except Exception as e:
            self.logger.error(f"Error fetching medications data: {e}")
            return {"data": []}
    
    async def _get_nutrition_data(self, user_id: str, time_window: str) -> Dict[str, Any]:
        """Get nutrition data from nutrition service"""
        try:
            service_config = self.service_registry.get("nutrition")
            if not service_config:
                return {"data": []}
            
            url = f"{service_config['url']}/api/v1/nutrition/meals"
            params = {
                "user_id": user_id,
                "time_window": time_window,
                "limit": 50
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to fetch nutrition data: {response.status_code}")
                    return {"data": []}
        except Exception as e:
            self.logger.error(f"Error fetching nutrition data: {e}")
            return {"data": []}
    
    async def _get_sleep_data(self, user_id: str, time_window: str) -> Dict[str, Any]:
        """Get sleep data from health tracking service"""
        try:
            service_config = self.service_registry.get("health_tracking")
            if not service_config:
                return {"data": []}
            
            url = f"{service_config['url']}/api/v1/health-tracking/sleep"
            params = {
                "user_id": user_id,
                "time_window": time_window,
                "limit": 30
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to fetch sleep data: {response.status_code}")
                    return {"data": []}
        except Exception as e:
            self.logger.error(f"Error fetching sleep data: {e}")
            return {"data": []}
    
    async def _get_activity_data(self, user_id: str, time_window: str) -> Dict[str, Any]:
        """Get activity data from health tracking service"""
        try:
            service_config = self.service_registry.get("health_tracking")
            if not service_config:
                return {"data": []}
            
            url = f"{service_config['url']}/api/v1/health-tracking/activity"
            params = {
                "user_id": user_id,
                "time_window": time_window,
                "limit": 50
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to fetch activity data: {response.status_code}")
                    return {"data": []}
        except Exception as e:
            self.logger.error(f"Error fetching activity data: {e}")
            return {"data": []}
    
    async def _get_lab_results_data(self, user_id: str, time_window: str) -> Dict[str, Any]:
        """Get lab results data from medical records service"""
        try:
            service_config = self.service_registry.get("medical_records")
            if not service_config:
                return {"data": []}
            
            url = f"{service_config['url']}/api/v1/medical-records/lab-results"
            params = {
                "user_id": user_id,
                "time_window": time_window,
                "limit": 20
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to fetch lab results data: {response.status_code}")
                    return {"data": []}
        except Exception as e:
            self.logger.error(f"Error fetching lab results data: {e}")
            return {"data": []}
    
    async def _get_medical_records_data(self, user_id: str, time_window: str) -> Dict[str, Any]:
        """Get medical records data from medical records service"""
        try:
            service_config = self.service_registry.get("medical_records")
            if not service_config:
                return {"data": []}
            
            url = f"{service_config['url']}/api/v1/medical-records/documents"
            params = {
                "user_id": user_id,
                "time_window": time_window,
                "limit": 20
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to fetch medical records data: {response.status_code}")
                    return {"data": []}
        except Exception as e:
            self.logger.error(f"Error fetching medical records data: {e}")
            return {"data": []}
    
    async def _get_device_data(self, user_id: str, time_window: str) -> Dict[str, Any]:
        """Get device data from device data service"""
        try:
            service_config = self.service_registry.get("device_data")
            if not service_config:
                return {"data": []}
            
            url = f"{service_config['url']}/api/v1/device-data/summary"
            params = {
                "user_id": user_id,
                "time_window": time_window,
                "limit": 50
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to fetch device data: {response.status_code}")
                    return {"data": []}
        except Exception as e:
            self.logger.error(f"Error fetching device data: {e}")
            return {"data": []}
    
    def _generate_summary(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from aggregated data"""
        summary = {
            "total_records": 0,
            "data_quality_score": 0.0,
            "last_updated": datetime.utcnow().isoformat(),
            "data_types_available": [],
            "anomalies_detected": [],
            "trends_identified": []
        }
        
        # Count records by type
        for data_type in ["vitals", "symptoms", "medications", "nutrition", "sleep", "activity", "lab_results", "medical_records", "device_data"]:
            data = aggregated_data.get(data_type, [])
            if isinstance(data, list):
                count = len(data)
                summary["total_records"] += count
                if count > 0:
                    summary["data_types_available"].append(data_type)
        
        # Calculate data quality score (simplified)
        data_types_count = len(summary["data_types_available"])
        max_data_types = 8  # Total possible data types
        summary["data_quality_score"] = min(1.0, data_types_count / max_data_types)
        
        return summary
