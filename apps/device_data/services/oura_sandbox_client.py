"""
Oura Sandbox Client
Mock client that provides realistic Oura data for testing without API calls.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import json

from common.utils.logging import get_logger

logger = get_logger(__name__)


class OuraSandboxClient:
    """Mock Oura client for sandbox/testing environment"""
    
    def __init__(self, user_id: str = None):
        self.logger = get_logger(__name__)
        self.user_id = user_id or "sandbox-user-123"
        self.logger.info(f"🔧 Initialized Oura Sandbox Client for user {self.user_id} - No API calls required")
    
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
            "email": f"user-{self.user_id}@oura-sandbox.com",
            "first_name": f"Sandbox",
            "last_name": f"User-{self.user_id[-4:]}",
            "age": 30,
            "weight": 70.0,
            "height": 175.0,
            "gender": "other",
            "timezone": "UTC"
        }
    
    async def get_personal_info(self) -> Dict[str, Any]:
        """Get mock personal information"""
        await asyncio.sleep(0.1)
        return {
            "id": self.user_id,
            "weight": 70.0,
            "height": 175.0,
            "age": 30,
            "gender": "other",
            "timezone": "UTC"
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
    
    async def get_daily_sleep(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get mock daily sleep data"""
        await asyncio.sleep(0.2)
        dates = self._generate_date_range(start_date, end_date)
        
        data = []
        for date in dates:
            # Generate realistic sleep data
            total_sleep = random.uniform(6.5, 8.5) * 3600  # 6.5-8.5 hours in seconds
            efficiency = random.uniform(75, 95)
            latency = random.uniform(5, 30)
            
            sleep_data = {
                "day": date,
                "sleep": {
                    "total_sleep_duration": total_sleep,
                    "sleep_efficiency": efficiency,
                    "sleep_latency": latency,
                    "rem_sleep_duration": random.uniform(1.5, 2.5) * 3600,
                    "deep_sleep_duration": random.uniform(1.0, 2.0) * 3600,
                    "light_sleep_duration": random.uniform(3.0, 5.0) * 3600,
                    "awake_time": random.uniform(0.1, 0.5) * 3600,
                    "sleep_score": random.uniform(70, 95),
                    "temperature_deviation": random.uniform(-0.5, 0.5),
                    "respiratory_rate": random.uniform(14, 18),
                    "hr_lowest": random.uniform(45, 55),
                    "hr_average": random.uniform(55, 65),
                    "rmssd": random.uniform(20, 40),
                    "hr_5min_lowest": random.uniform(45, 55)
                }
            }
            data.append(sleep_data)
        
        return {"data": data}
    
    async def get_daily_activity(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get mock daily activity data"""
        await asyncio.sleep(0.2)
        dates = self._generate_date_range(start_date, end_date)
        
        data = []
        for date in dates:
            activity_data = {
                "day": date,
                "activity": {
                    "steps": random.randint(8000, 15000),
                    "calories_total": random.randint(1800, 2500),
                    "calories_active": random.randint(200, 800),
                    "score": random.uniform(60, 95),
                    "daily_movement": random.uniform(60, 95),
                    "non_wear_time": random.uniform(0, 2) * 3600,
                    "rest_mode": random.choice([True, False]),
                    "active_calories": random.randint(200, 800),
                    "met_min_inactive": random.uniform(0, 60),
                    "met_min_low": random.uniform(30, 120),
                    "met_min_medium": random.uniform(10, 60),
                    "met_min_high": random.uniform(0, 30),
                    "average_met": random.uniform(1.2, 1.8),
                    "class_5min": json.dumps([random.randint(0, 4) for _ in range(288)]),  # 24 hours * 12 (5-min intervals)
                    "steps_previous_day": random.randint(8000, 15000),
                    "met_1min": json.dumps([random.uniform(1.0, 2.0) for _ in range(1440)])  # 24 hours * 60 minutes
                }
            }
            data.append(activity_data)
        
        return {"data": data}
    
    async def get_daily_readiness(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get mock daily readiness data"""
        await asyncio.sleep(0.2)
        dates = self._generate_date_range(start_date, end_date)
        
        data = []
        for date in dates:
            readiness_data = {
                "day": date,
                "readiness": {
                    "score": random.uniform(60, 95),
                    "score_previous_night": random.uniform(60, 95),
                    "score_sleep_balance": random.uniform(60, 95),
                    "score_previous_day_activity": random.uniform(60, 95),
                    "score_activity_balance": random.uniform(60, 95),
                    "score_resting_hr": random.uniform(60, 95),
                    "score_hrv_balance": random.uniform(60, 95),
                    "score_recovery_index": random.uniform(60, 95),
                    "score_temperature": random.uniform(60, 95),
                    "resting_hr": random.uniform(45, 65),
                    "hrv_balance": random.uniform(60, 95)
                }
            }
            data.append(readiness_data)
        
        return {"data": data}
    
    async def get_heart_rate(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get mock heart rate data"""
        await asyncio.sleep(0.2)
        dates = self._generate_date_range(start_date, end_date)
        
        data = []
        for date in dates:
            # Generate 24 hours of heart rate data (one reading per hour)
            for hour in range(24):
                timestamp = f"{date}T{hour:02d}:00:00"
                hr_data = {
                    "timestamp": timestamp,
                    "heart_rate": random.randint(50, 100)
                }
                data.append(hr_data)
        
        return {"data": data}
    
    async def get_workout(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get mock workout data"""
        await asyncio.sleep(0.2)
        dates = self._generate_date_range(start_date, end_date)
        
        data = []
        for date in dates:
            # 30% chance of having a workout on any given day
            if random.random() < 0.3:
                workout_data = {
                    "day": date,
                    "workout": {
                        "duration": random.randint(30, 120) * 60,  # 30-120 minutes in seconds
                        "calories": random.randint(200, 800),
                        "type": random.choice(["running", "cycling", "swimming", "strength", "yoga"])
                    }
                }
                data.append(workout_data)
        
        return {"data": data}
    
    async def get_session(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get mock session data"""
        await asyncio.sleep(0.2)
        dates = self._generate_date_range(start_date, end_date)
        
        data = []
        for date in dates:
            # 20% chance of having a session on any given day
            if random.random() < 0.2:
                session_data = {
                    "day": date,
                    "session": {
                        "duration": random.randint(10, 60) * 60,  # 10-60 minutes in seconds
                        "type": random.choice(["meditation", "breathing", "relaxation"])
                    }
                }
                data.append(session_data)
        
        return {"data": data}
    
    async def get_sleep(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get mock detailed sleep data (same as daily_sleep for sandbox)"""
        return await self.get_daily_sleep(start_date, end_date)
    
    async def get_activity(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get mock detailed activity data (same as daily_activity for sandbox)"""
        return await self.get_daily_activity(start_date, end_date)
    
    async def get_readiness(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get mock detailed readiness data (same as daily_readiness for sandbox)"""
        return await self.get_daily_readiness(start_date, end_date)
    
    async def get_all_data(self, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> Dict[str, Any]:
        """Get all mock data types"""
        await asyncio.sleep(0.5)
        
        # Fetch all data types concurrently
        tasks = [
            self.get_daily_sleep(start_date, end_date),
            self.get_daily_activity(start_date, end_date),
            self.get_daily_readiness(start_date, end_date),
            self.get_heart_rate(start_date, end_date),
            self.get_workout(start_date, end_date),
            self.get_session(start_date, end_date),
            self.get_sleep(start_date, end_date),
            self.get_activity(start_date, end_date),
            self.get_readiness(start_date, end_date)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "daily_sleep": results[0] if not isinstance(results[0], Exception) else None,
            "daily_activity": results[1] if not isinstance(results[1], Exception) else None,
            "daily_readiness": results[2] if not isinstance(results[2], Exception) else None,
            "heart_rate": results[3] if not isinstance(results[3], Exception) else None,
            "workout": results[4] if not isinstance(results[4], Exception) else None,
            "session": results[5] if not isinstance(results[5], Exception) else None,
            "sleep": results[6] if not isinstance(results[6], Exception) else None,
            "activity": results[7] if not isinstance(results[7], Exception) else None,
            "readiness": results[8] if not isinstance(results[8], Exception) else None,
            "errors": [str(r) for r in results if isinstance(r, Exception)]
        } 