"""
Dexcom Sandbox Client
Mock client that provides realistic Dexcom CGM data for testing without API calls.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import json

from common.utils.logging import get_logger

logger = get_logger(__name__)


class DexcomSandboxClient:
    """Mock Dexcom client for sandbox/testing environment"""
    
    def __init__(self, user_id: str = None):
        self.logger = get_logger(__name__)
        self.user_id = user_id or "sandbox-user-123"
        self.logger.info(f"🔧 Initialized Dexcom Sandbox Client for user {self.user_id} - No API calls required")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass
    
    async def test_connection(self) -> bool:
        """Test connection - always succeeds in sandbox"""
        await asyncio.sleep(0.1)  # Simulate network delay
        return True
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get mock user information"""
        await asyncio.sleep(0.1)
        return {
            "id": self.user_id,
            "email": f"user-{self.user_id}@dexcom-sandbox.com",
            "first_name": f"Sandbox",
            "last_name": f"User-{self.user_id[-4:]}",
            "timezone": "UTC"
        }
    
    async def get_data_range(self) -> Dict[str, Any]:
        """Get mock data range information"""
        await asyncio.sleep(0.1)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        return {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "egvs": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "calibrations": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "events": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "alerts": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    def _generate_date_range(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> List[str]:
        """Generate list of dates between start and end"""
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)
        return dates
    
    async def get_egvs(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get mock Estimated Glucose Values (EGVs)"""
        await asyncio.sleep(0.2)
        dates = self._generate_date_range(start_date, end_date)
        
        egvs = []
        for date in dates:
            # Generate 24 hours of glucose readings (every 5 minutes)
            base_time = datetime.fromisoformat(date)
            for hour in range(24):
                for minute in range(0, 60, 5):  # Every 5 minutes
                    timestamp = base_time + timedelta(hours=hour, minutes=minute)
                    
                    # Generate realistic glucose values (70-200 mg/dL)
                    glucose_value = random.uniform(70, 200)
                    
                    # Add some variation for meals, exercise, etc.
                    if 6 <= hour <= 8:  # Breakfast time
                        glucose_value += random.uniform(20, 50)
                    elif 12 <= hour <= 14:  # Lunch time
                        glucose_value += random.uniform(20, 50)
                    elif 18 <= hour <= 20:  # Dinner time
                        glucose_value += random.uniform(20, 50)
                    
                    egv = {
                        "systemTime": timestamp.isoformat(),
                        "displayTime": timestamp.isoformat(),
                        "value": round(glucose_value, 1),
                        "unit": "mg/dL",
                        "trend": random.choice(["DoubleUp", "SingleUp", "FortyFiveUp", "Flat", "FortyFiveDown", "SingleDown", "DoubleDown", "NotComputable", "RateOutOfRange"]),
                        "trendRate": random.uniform(-2.0, 2.0),
                        "status": random.choice(["OK", "Low", "High", "OutOfRange"]),
                        "glucoseChangeRate": random.uniform(-5.0, 5.0)
                    }
                    egvs.append(egv)
        
        return {"egvs": egvs}
    
    async def get_calibrations(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get mock calibration data"""
        await asyncio.sleep(0.1)
        dates = self._generate_date_range(start_date, end_date)
        
        calibrations = []
        for date in dates:
            # Generate 1-2 calibrations per day
            num_calibrations = random.randint(1, 2)
            for i in range(num_calibrations):
                base_time = datetime.fromisoformat(date)
                hour = random.randint(6, 22)  # Between 6 AM and 10 PM
                minute = random.randint(0, 59)
                timestamp = base_time + timedelta(hours=hour, minutes=minute)
                
                calibration = {
                    "systemTime": timestamp.isoformat(),
                    "displayTime": timestamp.isoformat(),
                    "value": random.uniform(70, 200),
                    "unit": "mg/dL",
                    "type": "Finger",
                    "transmitterId": f"TX{random.randint(100000, 999999)}",
                    "transmitterTicks": random.randint(1000, 9999)
                }
                calibrations.append(calibration)
        
        return {"calibrations": calibrations}
    
    async def get_events(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get mock events (insulin, carbs, etc.)"""
        await asyncio.sleep(0.1)
        dates = self._generate_date_range(start_date, end_date)
        
        events = []
        for date in dates:
            base_time = datetime.fromisoformat(date)
            
            # Breakfast events
            breakfast_time = base_time + timedelta(hours=7, minutes=random.randint(0, 30))
            events.append({
                "systemTime": breakfast_time.isoformat(),
                "displayTime": breakfast_time.isoformat(),
                "eventType": "Carbs",
                "value": random.randint(30, 80),
                "unit": "grams",
                "eventSubType": "Breakfast"
            })
            
            # Lunch events
            lunch_time = base_time + timedelta(hours=12, minutes=random.randint(0, 30))
            events.append({
                "systemTime": lunch_time.isoformat(),
                "displayTime": lunch_time.isoformat(),
                "eventType": "Carbs",
                "value": random.randint(40, 100),
                "unit": "grams",
                "eventSubType": "Lunch"
            })
            
            # Dinner events
            dinner_time = base_time + timedelta(hours=18, minutes=random.randint(0, 30))
            events.append({
                "systemTime": dinner_time.isoformat(),
                "displayTime": dinner_time.isoformat(),
                "eventType": "Carbs",
                "value": random.randint(30, 90),
                "unit": "grams",
                "eventSubType": "Dinner"
            })
            
            # Insulin events (1-3 per day)
            num_insulin_events = random.randint(1, 3)
            for i in range(num_insulin_events):
                hour = random.randint(6, 22)
                minute = random.randint(0, 59)
                insulin_time = base_time + timedelta(hours=hour, minutes=minute)
                
                events.append({
                    "systemTime": insulin_time.isoformat(),
                    "displayTime": insulin_time.isoformat(),
                    "eventType": "Insulin",
                    "value": random.uniform(2.0, 15.0),
                    "unit": "units",
                    "eventSubType": random.choice(["Rapid-Acting", "Long-Acting"])
                })
        
        return {"events": events}
    
    async def get_alerts(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get mock alert data"""
        await asyncio.sleep(0.1)
        dates = self._generate_date_range(start_date, end_date)
        
        alerts = []
        for date in dates:
            # Generate 0-2 alerts per day
            num_alerts = random.randint(0, 2)
            for i in range(num_alerts):
                base_time = datetime.fromisoformat(date)
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                alert_time = base_time + timedelta(hours=hour, minutes=minute)
                
                alert = {
                    "systemTime": alert_time.isoformat(),
                    "displayTime": alert_time.isoformat(),
                    "alertType": random.choice(["LowGlucose", "HighGlucose", "RisingGlucose", "FallingGlucose", "OutOfRange"]),
                    "value": random.uniform(50, 300),
                    "unit": "mg/dL",
                    "status": random.choice(["Active", "Cleared"])
                }
                alerts.append(alert)
        
        return {"alerts": alerts}
    
    async def get_devices(self) -> Dict[str, Any]:
        """Get mock device information"""
        await asyncio.sleep(0.1)
        return {
            "devices": [
                {
                    "id": f"device-{self.user_id}",
                    "name": "Dexcom G7",
                    "model": "G7",
                    "serialNumber": f"SN{random.randint(100000, 999999)}",
                    "transmitterId": f"TX{random.randint(100000, 999999)}",
                    "lastUploadDate": datetime.utcnow().isoformat(),
                    "status": "Active"
                }
            ]
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get mock statistics"""
        await asyncio.sleep(0.1)
        return {
            "statistics": {
                "averageGlucose": random.uniform(120, 180),
                "glucoseUnit": "mg/dL",
                "timeInRange": random.uniform(60, 90),
                "timeInRangeUnit": "percent",
                "totalDays": random.randint(7, 30),
                "totalReadings": random.randint(1000, 5000)
            }
        }
    
    async def get_all_data(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get all Dexcom data types"""
        egvs = await self.get_egvs(start_date, end_date)
        calibrations = await self.get_calibrations(start_date, end_date)
        events = await self.get_events(start_date, end_date)
        alerts = await self.get_alerts(start_date, end_date)
        devices = await self.get_devices()
        statistics = await self.get_statistics()
        
        return {
            "egvs": egvs.get("egvs", []),
            "calibrations": calibrations.get("calibrations", []),
            "events": events.get("events", []),
            "alerts": alerts.get("alerts", []),
            "devices": devices.get("devices", []),
            "statistics": statistics.get("statistics", {})
        } 