"""
Cache Service for GraphQL BFF
Handles caching to improve performance and reduce load on backend services.
"""

import json
import hashlib
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from common.utils.logging import get_logger

logger = get_logger(__name__)

class CacheService:
    """Service for caching GraphQL BFF data"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.logger = logger
        
        # Default cache settings
        self.default_ttl = 3600  # 1 hour
        self.short_ttl = 300     # 5 minutes
        self.long_ttl = 86400    # 24 hours
        
        # Cache key prefixes
        self.prefixes = {
            "reasoning": "reasoning",
            "daily_summary": "daily_summary",
            "health_data": "health_data",
            "insights": "insights",
            "recommendations": "recommendations",
            "doctor_report": "doctor_report",
            "user_profile": "user_profile"
        }
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            cached_value = await self.redis_client.get(key)
            if cached_value:
                return json.loads(cached_value)
            return None
        except Exception as e:
            self.logger.warning(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            await self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            self.logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            self.logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
        
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            self.logger.warning(f"Cache exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for cache key"""
        if not self.redis_client:
            return False
        
        try:
            return await self.redis_client.expire(key, ttl)
        except Exception as e:
            self.logger.warning(f"Cache expire error for key {key}: {e}")
            return False
    
    # Specialized cache methods for different data types
    async def get_reasoning_result(self, user_id: str, query: str) -> Optional[Dict[str, Any]]:
        """Get cached reasoning result"""
        cache_key = self._generate_reasoning_key(user_id, query)
        return await self.get(cache_key)
    
    async def set_reasoning_result(self, user_id: str, query: str, result: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set cached reasoning result"""
        cache_key = self._generate_reasoning_key(user_id, query)
        return await self.set(cache_key, result, ttl or self.default_ttl)
    
    async def get_daily_summary(self, user_id: str, date: str) -> Optional[Dict[str, Any]]:
        """Get cached daily summary"""
        cache_key = self._generate_daily_summary_key(user_id, date)
        return await self.get(cache_key)
    
    async def set_daily_summary(self, user_id: str, date: str, summary: Dict[str, Any]) -> bool:
        """Set cached daily summary"""
        cache_key = self._generate_daily_summary_key(user_id, date)
        return await self.set(cache_key, summary, self.long_ttl)  # Daily summaries cached longer
    
    async def get_health_data(self, user_id: str, time_window: str, data_types: Optional[list] = None) -> Optional[Dict[str, Any]]:
        """Get cached health data"""
        cache_key = self._generate_health_data_key(user_id, time_window, data_types)
        return await self.get(cache_key)
    
    async def set_health_data(self, user_id: str, time_window: str, data: Dict[str, Any], data_types: Optional[list] = None) -> bool:
        """Set cached health data"""
        cache_key = self._generate_health_data_key(user_id, time_window, data_types)
        return await self.set(cache_key, data, self.short_ttl)  # Health data cached for shorter time
    
    async def get_insights(self, user_id: str, insight_type: Optional[str] = None, limit: int = 20, offset: int = 0) -> Optional[list]:
        """Get cached insights"""
        cache_key = self._generate_insights_key(user_id, insight_type, limit, offset)
        return await self.get(cache_key)
    
    async def set_insights(self, user_id: str, insights: list, insight_type: Optional[str] = None, limit: int = 20, offset: int = 0) -> bool:
        """Set cached insights"""
        cache_key = self._generate_insights_key(user_id, insight_type, limit, offset)
        return await self.set(cache_key, insights, self.default_ttl)
    
    async def get_doctor_report(self, user_id: str, time_window: str) -> Optional[Dict[str, Any]]:
        """Get cached doctor report"""
        cache_key = self._generate_doctor_report_key(user_id, time_window)
        return await self.get(cache_key)
    
    async def set_doctor_report(self, user_id: str, time_window: str, report: Dict[str, Any]) -> bool:
        """Set cached doctor report"""
        cache_key = self._generate_doctor_report_key(user_id, time_window)
        return await self.set(cache_key, report, self.long_ttl)  # Reports cached longer
    
    # Cache invalidation methods
    async def invalidate_user_cache(self, user_id: str) -> bool:
        """Invalidate all cache entries for a user"""
        if not self.redis_client:
            return False
        
        try:
            pattern = f"*:{user_id}:*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                self.logger.info(f"Invalidated {len(keys)} cache entries for user {user_id}")
            return True
        except Exception as e:
            self.logger.warning(f"Cache invalidation error for user {user_id}: {e}")
            return False
    
    async def invalidate_reasoning_cache(self, user_id: str) -> bool:
        """Invalidate reasoning cache for a user"""
        if not self.redis_client:
            return False
        
        try:
            pattern = f"{self.prefixes['reasoning']}:{user_id}:*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                self.logger.info(f"Invalidated {len(keys)} reasoning cache entries for user {user_id}")
            return True
        except Exception as e:
            self.logger.warning(f"Reasoning cache invalidation error for user {user_id}: {e}")
            return False
    
    async def invalidate_health_data_cache(self, user_id: str) -> bool:
        """Invalidate health data cache for a user"""
        if not self.redis_client:
            return False
        
        try:
            pattern = f"{self.prefixes['health_data']}:{user_id}:*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                self.logger.info(f"Invalidated {len(keys)} health data cache entries for user {user_id}")
            return True
        except Exception as e:
            self.logger.warning(f"Health data cache invalidation error for user {user_id}: {e}")
            return False
    
    # Cache key generation methods
    def _generate_reasoning_key(self, user_id: str, query: str) -> str:
        """Generate cache key for reasoning results"""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        return f"{self.prefixes['reasoning']}:{user_id}:{query_hash}"
    
    def _generate_daily_summary_key(self, user_id: str, date: str) -> str:
        """Generate cache key for daily summaries"""
        return f"{self.prefixes['daily_summary']}:{user_id}:{date}"
    
    def _generate_health_data_key(self, user_id: str, time_window: str, data_types: Optional[list] = None) -> str:
        """Generate cache key for health data"""
        data_types_str = ",".join(sorted(data_types)) if data_types else "all"
        return f"{self.prefixes['health_data']}:{user_id}:{time_window}:{data_types_str}"
    
    def _generate_insights_key(self, user_id: str, insight_type: Optional[str], limit: int, offset: int) -> str:
        """Generate cache key for insights"""
        insight_type_str = insight_type or "all"
        return f"{self.prefixes['insights']}:{user_id}:{insight_type_str}:{limit}:{offset}"
    
    def _generate_doctor_report_key(self, user_id: str, time_window: str) -> str:
        """Generate cache key for doctor reports"""
        return f"{self.prefixes['doctor_report']}:{user_id}:{time_window}"
    
    # Cache statistics and monitoring
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {"error": "Redis not available"}
        
        try:
            info = await self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            self.logger.warning(f"Cache stats error: {e}")
            return {"error": str(e)}
    
    async def clear_all_cache(self) -> bool:
        """Clear all cache entries (use with caution)"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.flushdb()
            self.logger.info("All cache entries cleared")
            return True
        except Exception as e:
            self.logger.warning(f"Cache clear error: {e}")
            return False
