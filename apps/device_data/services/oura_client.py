"""
Oura API Client
Dedicated client for interacting with Oura Ring API.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import aiohttp
from aiohttp import ClientTimeout, ClientSession
import time

from common.utils.logging import get_logger
from common.utils.resilience import with_resilience
from ..config.oura_config import oura_config

logger = get_logger(__name__)


class OuraAPIError(Exception):
    """Base exception for Oura API errors"""
    pass


class OuraAuthenticationError(OuraAPIError):
    """Authentication error with Oura API"""
    pass


class OuraRateLimitError(OuraAPIError):
    """Rate limit exceeded error"""
    pass


class OuraAPIResponseError(OuraAPIError):
    """API response error"""
    pass


class OuraAPIClient:
    """Client for interacting with Oura Ring API"""
    
    def __init__(self, access_token: str = None, use_sandbox: bool = None, user_id: str = None):
        # Use sandbox if explicitly requested or if no token provided
        if use_sandbox is None:
            use_sandbox = oura_config.use_sandbox or access_token is None
        
        self.use_sandbox = use_sandbox
        self.access_token = access_token
        self.user_id = user_id
        
        if self.use_sandbox:
            # Use mock sandbox client with user-specific data
            from .oura_sandbox_client import OuraSandboxClient
            self._sandbox_client = OuraSandboxClient(user_id=user_id)
            print(f"🔧 Using Oura Sandbox Mode - Mock data for user {user_id}")
        else:
            # Use real API client
            self.api_base_url = oura_config.api_base_url
            if not access_token:
                raise ValueError("Access token required for production Oura API")
            
            self.endpoints = oura_config.endpoints
            self.timeout = ClientTimeout(total=oura_config.request_timeout)
            self.session: Optional[ClientSession] = None
            self.rate_limit_tracker = {
                "requests": 0,
                "window_start": time.time()
            }
        
    async def __aenter__(self):
        """Async context manager entry"""
        if self.use_sandbox:
            return await self._sandbox_client.__aenter__()
        else:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "PersonalHealthAssistant/1.0"
            }
            
            # Add authorization header only if not in sandbox mode
            if not self.use_sandbox and self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
            
            self.session = ClientSession(
                timeout=self.timeout,
                headers=headers
            )
            return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.use_sandbox:
            await self._sandbox_client.__aexit__(exc_type, exc_val, exc_tb)
        elif self.session:
            await self.session.close()
    
    def _check_rate_limit(self):
        """Check and update rate limiting"""
        current_time = time.time()
        window_duration = 60  # 1 minute window
        
        # Reset window if expired
        if current_time - self.rate_limit_tracker["window_start"] > window_duration:
            self.rate_limit_tracker = {
                "requests": 1,
                "window_start": current_time
            }
        else:
            self.rate_limit_tracker["requests"] += 1
            
        # Check if rate limit exceeded
        if self.rate_limit_tracker["requests"] > oura_config.rate_limit_per_minute:
            raise OuraRateLimitError(
                f"Rate limit exceeded: {self.rate_limit_tracker['requests']} requests in current window"
            )
    
    @with_resilience("oura_api", max_retries=3)
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Oura API with retry logic"""
        if not self.session:
            raise OuraAPIError("Client session not initialized. Use async context manager.")
        
        self._check_rate_limit()
        
        url = f"{self.api_base_url}{endpoint}"
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                params=params,
                json=data
            ) as response:
                
                if response.status == 401 and not self.use_sandbox:
                    raise OuraAuthenticationError("Invalid or expired access token")
                elif response.status == 429:
                    raise OuraRateLimitError("Rate limit exceeded")
                elif response.status >= 400:
                    error_text = await response.text()
                    raise OuraAPIResponseError(
                        f"API request failed: {response.status} - {error_text}"
                    )
                
                return await response.json()
                
        except aiohttp.ClientError as e:
            raise OuraAPIError(f"Network error: {e}")
        except Exception as e:
            if isinstance(e, OuraAPIError):
                raise
            raise OuraAPIError(f"Unexpected error: {e}")
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get user information from Oura API"""
        if self.use_sandbox:
            return await self._sandbox_client.get_user_info()
        
        logger.info("Fetching Oura user info")
        return await self._make_request("GET", self.endpoints["userinfo"])
    
    async def get_daily_sleep(
        self, 
        start_date: Union[str, datetime], 
        end_date: Union[str, datetime]
    ) -> Dict[str, Any]:
        """Get daily sleep data"""
        if self.use_sandbox:
            return await self._sandbox_client.get_daily_sleep(start_date, end_date)
        
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d")
            
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        logger.info(f"Fetching Oura daily sleep data from {start_date} to {end_date}")
        return await self._make_request("GET", self.endpoints["daily_sleep"], params=params)
    
    async def get_daily_activity(
        self, 
        start_date: Union[str, datetime], 
        end_date: Union[str, datetime]
    ) -> Dict[str, Any]:
        """Get daily activity data"""
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d")
            
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        logger.info(f"Fetching Oura daily activity data from {start_date} to {end_date}")
        return await self._make_request("GET", self.endpoints["daily_activity"], params=params)
    
    async def get_daily_readiness(
        self, 
        start_date: Union[str, datetime], 
        end_date: Union[str, datetime]
    ) -> Dict[str, Any]:
        """Get daily readiness data"""
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d")
            
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        logger.info(f"Fetching Oura daily readiness data from {start_date} to {end_date}")
        return await self._make_request("GET", self.endpoints["daily_readiness"], params=params)
    
    async def get_heart_rate(
        self, 
        start_date: Union[str, datetime], 
        end_date: Union[str, datetime]
    ) -> Dict[str, Any]:
        """Get heart rate data"""
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d")
            
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        logger.info(f"Fetching Oura heart rate data from {start_date} to {end_date}")
        return await self._make_request("GET", self.endpoints["heart_rate"], params=params)
    
    async def get_personal_info(self) -> Dict[str, Any]:
        """Get personal information"""
        if self.use_sandbox:
            return await self._sandbox_client.get_personal_info()
        
        logger.info("Fetching Oura personal info")
        return await self._make_request("GET", self.endpoints["personal_info"])
    
    async def get_workout(
        self, 
        start_date: Union[str, datetime], 
        end_date: Union[str, datetime]
    ) -> Dict[str, Any]:
        """Get workout data"""
        if self.use_sandbox:
            return await self._sandbox_client.get_workout(start_date, end_date)
        
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d")
            
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        logger.info(f"Fetching Oura workout data from {start_date} to {end_date}")
        return await self._make_request("GET", self.endpoints["workout"], params=params)
    
    async def get_session(
        self, 
        start_date: Union[str, datetime], 
        end_date: Union[str, datetime]
    ) -> Dict[str, Any]:
        """Get session data"""
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d")
            
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        logger.info(f"Fetching Oura session data from {start_date} to {end_date}")
        return await self._make_request("GET", self.endpoints["session"], params=params)
    
    async def get_sleep(
        self, 
        start_date: Union[str, datetime], 
        end_date: Union[str, datetime]
    ) -> Dict[str, Any]:
        """Get detailed sleep data"""
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d")
            
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        logger.info(f"Fetching Oura detailed sleep data from {start_date} to {end_date}")
        return await self._make_request("GET", self.endpoints["sleep"], params=params)
    
    async def get_activity(
        self, 
        start_date: Union[str, datetime], 
        end_date: Union[str, datetime]
    ) -> Dict[str, Any]:
        """Get detailed activity data"""
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d")
            
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        logger.info(f"Fetching Oura detailed activity data from {start_date} to {end_date}")
        return await self._make_request("GET", self.endpoints["activity"], params=params)
    
    async def get_readiness(
        self, 
        start_date: Union[str, datetime], 
        end_date: Union[str, datetime]
    ) -> Dict[str, Any]:
        """Get detailed readiness data"""
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d")
            
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        logger.info(f"Fetching Oura detailed readiness data from {start_date} to {end_date}")
        return await self._make_request("GET", self.endpoints["readiness"], params=params)
    
    async def test_connection(self) -> bool:
        """Test connection to Oura API"""
        if self.use_sandbox:
            return await self._sandbox_client.test_connection()
        
        try:
            await self.get_user_info()
            logger.info("Oura API connection test successful")
            return True
        except Exception as e:
            logger.error(f"Oura API connection test failed: {e}")
            return False
    
    async def get_all_data(
        self, 
        start_date: Union[str, datetime], 
        end_date: Union[str, datetime]
    ) -> Dict[str, Any]:
        """Get all available data types for the date range"""
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d")
        
        logger.info(f"Fetching all Oura data from {start_date} to {end_date}")
        
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