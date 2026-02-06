"""
Feature Flags System
Implements feature flags for canary releases and feature toggles as per Implementation Guide.
"""

import os
import json
import time
import asyncio
import hashlib
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
from enum import Enum
import redis.asyncio as redis
from pydantic import BaseModel, Field
from fastapi import HTTPException, Depends

from common.config.settings import get_settings
from common.utils.logging import get_logger


logger = get_logger(__name__)
settings = get_settings()


class FeatureFlagType(str, Enum):
    """Feature flag types"""
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    ENVIRONMENT = "environment"
    TIME_BASED = "time_based"


class FeatureFlagRule(BaseModel):
    """Feature flag rule configuration"""
    type: FeatureFlagType
    value: Any
    conditions: Optional[Dict[str, Any]] = None


class FeatureFlag(BaseModel):
    """Feature flag configuration"""
    name: str
    description: str
    enabled: bool = False
    rules: Optional[List[FeatureFlagRule]] = None
    default_value: Any = False
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    created_by: Optional[str] = None
    environment: str = "development"


class FeatureFlagManager:
    """Feature flag manager with Redis backend"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.external_services.redis_url
        self.redis_client: Optional[redis.Redis] = None
        self._flags: Dict[str, FeatureFlag] = {}
        self._cache_ttl = 300  # 5 minutes cache
        
        # Initialize default feature flags
        self._initialize_default_flags()
    
    def _initialize_default_flags(self):
        """Initialize default feature flags"""
        default_flags = {
            "new_dashboard_layout": FeatureFlag(
                name="new_dashboard_layout",
                description="Enable new dashboard layout",
                enabled=True,
                default_value=True
            ),
            "ai_lab_report_summary": FeatureFlag(
                name="ai_lab_report_summary",
                description="Enable AI-powered lab report summaries",
                enabled=False,
                default_value=False,
                rules=[
                    FeatureFlagRule(
                        type=FeatureFlagType.USER_LIST,
                        value=["user1@example.com", "user2@example.com"]
                    )
                ]
            ),
            "beta_user_group": FeatureFlag(
                name="beta_user_group",
                description="Beta user group access",
                enabled=True,
                default_value=False,
                rules=[
                    FeatureFlagRule(
                        type=FeatureFlagType.USER_LIST,
                        value=["beta_user1@example.com", "beta_user2@example.com"]
                    )
                ]
            ),
            "enhanced_analytics": FeatureFlag(
                name="enhanced_analytics",
                description="Enable enhanced analytics features",
                enabled=True,
                default_value=True,
                rules=[
                    FeatureFlagRule(
                        type=FeatureFlagType.PERCENTAGE,
                        value=50  # 50% of users
                    )
                ]
            ),
            "voice_input_beta": FeatureFlag(
                name="voice_input_beta",
                description="Enable voice input beta features",
                enabled=False,
                default_value=False,
                rules=[
                    FeatureFlagRule(
                        type=FeatureFlagType.USER_LIST,
                        value=["voice_beta_user@example.com"]
                    )
                ]
            ),
            "genomics_analysis": FeatureFlag(
                name="genomics_analysis",
                description="Enable genomics analysis features",
                enabled=True,
                default_value=True,
                rules=[
                    FeatureFlagRule(
                        type=FeatureFlagType.ENVIRONMENT,
                        value=["production", "staging"]
                    )
                ]
            ),
            "real_time_notifications": FeatureFlag(
                name="real_time_notifications",
                description="Enable real-time notifications",
                enabled=False,
                default_value=False,
                rules=[
                    FeatureFlagRule(
                        type=FeatureFlagType.PERCENTAGE,
                        value=25  # 25% of users
                    )
                ]
            )
        }
        
        for flag_name, flag in default_flags.items():
            self._flags[flag_name] = flag
    
    async def get_redis_client(self) -> redis.Redis:
        """Get Redis client"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf8",
                decode_responses=True
            )
        return self.redis_client
    
    async def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get feature flag from cache or Redis"""
        # Check local cache first
        if flag_name in self._flags:
            return self._flags[flag_name]
        
        # Try Redis
        try:
            redis_client = await self.get_redis_client()
            flag_data = await redis_client.get(f"feature_flag:{flag_name}")
            if flag_data:
                flag_dict = json.loads(flag_data)
                flag = FeatureFlag(**flag_dict)
                self._flags[flag_name] = flag
                return flag
        except Exception as e:
            logger.error(f"Failed to get feature flag from Redis: {e}")
        
        return None
    
    async def set_flag(self, flag: FeatureFlag):
        """Set feature flag in cache and Redis"""
        flag.updated_at = time.time()
        self._flags[flag.name] = flag
        
        try:
            redis_client = await self.get_redis_client()
            await redis_client.setex(
                f"feature_flag:{flag.name}",
                self._cache_ttl,
                flag.model_dump_json()
            )
        except Exception as e:
            logger.error(f"Failed to set feature flag in Redis: {e}")
    
    async def delete_flag(self, flag_name: str):
        """Delete feature flag"""
        if flag_name in self._flags:
            del self._flags[flag_name]
        
        try:
            redis_client = await self.get_redis_client()
            await redis_client.delete(f"feature_flag:{flag_name}")
        except Exception as e:
            logger.error(f"Failed to delete feature flag from Redis: {e}")
    
    def _evaluate_boolean_rule(self, rule: FeatureFlagRule, context: Dict[str, Any]) -> bool:
        """Evaluate boolean rule"""
        return bool(rule.value)
    
    def _evaluate_percentage_rule(self, rule: FeatureFlagRule, context: Dict[str, Any]) -> bool:
        """Evaluate percentage rule"""
        user_id = context.get("user_id")
        if not user_id:
            return False
        
        # Use user ID hash to determine percentage
        hash_value = hash(str(user_id)) % 100
        return hash_value < rule.value
    
    def _evaluate_user_list_rule(self, rule: FeatureFlagRule, context: Dict[str, Any]) -> bool:
        """Evaluate user list rule"""
        user_email = context.get("user_email")
        if not user_email:
            return False
        
        return user_email in rule.value
    
    def _evaluate_environment_rule(self, rule: FeatureFlagRule, context: Dict[str, Any]) -> bool:
        """Evaluate environment rule"""
        environment = context.get("environment", settings.development.environment)
        return environment in rule.value
    
    def _evaluate_time_based_rule(self, rule: FeatureFlagRule, context: Dict[str, Any]) -> bool:
        """Evaluate time-based rule"""
        current_time = time.time()
        start_time = rule.conditions.get("start_time", 0)
        end_time = rule.conditions.get("end_time", float('inf'))
        
        return start_time <= current_time <= end_time
    
    async def is_feature_enabled(
        self,
        feature_name: str,
        user: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if a feature is enabled for the given user and context"""
        flag = await self.get_flag(feature_name)
        if not flag:
            return False
        
        if not flag.enabled:
            return False
        
        # If no rules, return default value
        if not flag.rules:
            return bool(flag.default_value)
        
        # Build context
        context = context or {}
        if user:
            context.update({
                "user_id": user.get("id"),
                "user_email": user.get("email"),
                "user_roles": user.get("roles", [])
            })
        context["environment"] = settings.development.environment
        
        # Evaluate rules
        for rule in flag.rules:
            try:
                if rule.type == FeatureFlagType.BOOLEAN:
                    if self._evaluate_boolean_rule(rule, context):
                        return True
                elif rule.type == FeatureFlagType.PERCENTAGE:
                    if self._evaluate_percentage_rule(rule, context):
                        return True
                elif rule.type == FeatureFlagType.USER_LIST:
                    if self._evaluate_user_list_rule(rule, context):
                        return True
                elif rule.type == FeatureFlagType.ENVIRONMENT:
                    if self._evaluate_environment_rule(rule, context):
                        return True
                elif rule.type == FeatureFlagType.TIME_BASED:
                    if self._evaluate_time_based_rule(rule, context):
                        return True
            except Exception as e:
                logger.error(f"Error evaluating feature flag rule: {e}")
                continue
        
        return bool(flag.default_value)
    
    async def get_feature_value(
        self,
        feature_name: str,
        user: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Get feature flag value (for non-boolean flags)"""
        is_enabled = await self.is_feature_enabled(feature_name, user, context)
        if is_enabled:
            flag = await self.get_flag(feature_name)
            return flag.default_value if flag else None
        return None
    
    async def list_flags(self) -> List[FeatureFlag]:
        """List all feature flags"""
        return list(self._flags.values())
    
    async def create_flag(self, flag: FeatureFlag):
        """Create a new feature flag"""
        await self.set_flag(flag)
        logger.info(f"Created feature flag: {flag.name}")
    
    async def update_flag(self, flag_name: str, updates: Dict[str, Any]):
        """Update an existing feature flag"""
        flag = await self.get_flag(flag_name)
        if not flag:
            raise ValueError(f"Feature flag {flag_name} not found")
        
        # Update fields
        for field, value in updates.items():
            if hasattr(flag, field):
                setattr(flag, field, value)
        
        await self.set_flag(flag)
        logger.info(f"Updated feature flag: {flag_name}")


# Global feature flag manager
feature_flag_manager = FeatureFlagManager()


def feature_flag(
    feature_name: str,
    default_value: Any = False,
    user_dependency: Optional[Callable] = None
):
    """Decorator for feature flag protection"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get user from dependency or context
            user = None
            if user_dependency:
                user = await user_dependency()
            
            # Check if feature is enabled
            is_enabled = await feature_flag_manager.is_feature_enabled(
                feature_name, user
            )
            
            if not is_enabled:
                # Return default value or raise exception
                if default_value is not None:
                    return default_value
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Feature {feature_name} is not available"
                    )
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't easily get user context
            # This is a simplified version
            is_enabled = asyncio.run(
                feature_flag_manager.is_feature_enabled(feature_name)
            )
            
            if not is_enabled:
                if default_value is not None:
                    return default_value
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Feature {feature_name} is not available"
                    )
            
            return func(*args, **kwargs)
        
        # Check if function is async
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def require_feature_flag(feature_name: str):
    """Dependency for requiring a feature flag"""
    async def dependency(user: Optional[Dict[str, Any]] = None):
        is_enabled = await feature_flag_manager.is_feature_enabled(
            feature_name, user
        )
        if not is_enabled:
            raise HTTPException(
                status_code=404,
                detail=f"Feature {feature_name} is not available"
            )
        return is_enabled
    return dependency


# Convenience functions for common feature flags
async def is_new_dashboard_enabled(user: Optional[Dict[str, Any]] = None) -> bool:
    """Check if new dashboard is enabled"""
    return await feature_flag_manager.is_feature_enabled("new_dashboard_layout", user)


async def is_ai_lab_summary_enabled(user: Optional[Dict[str, Any]] = None) -> bool:
    """Check if AI lab summary is enabled"""
    return await feature_flag_manager.is_feature_enabled("ai_lab_report_summary", user)


async def is_beta_user(user: Optional[Dict[str, Any]] = None) -> bool:
    """Check if user is in beta group"""
    return await feature_flag_manager.is_feature_enabled("beta_user_group", user)


async def is_enhanced_analytics_enabled(user: Optional[Dict[str, Any]] = None) -> bool:
    """Check if enhanced analytics is enabled"""
    return await feature_flag_manager.is_feature_enabled("enhanced_analytics", user)


async def is_voice_input_enabled(user: Optional[Dict[str, Any]] = None) -> bool:
    """Check if voice input is enabled"""
    return await feature_flag_manager.is_feature_enabled("voice_input_beta", user)


async def is_genomics_enabled(user: Optional[Dict[str, Any]] = None) -> bool:
    """Check if genomics analysis is enabled"""
    return await feature_flag_manager.is_feature_enabled("genomics_analysis", user)


async def is_real_time_notifications_enabled(user: Optional[Dict[str, Any]] = None) -> bool:
    """Check if real-time notifications are enabled"""
    return await feature_flag_manager.is_feature_enabled("real_time_notifications", user)


# Example usage in FastAPI
"""
from fastapi import Depends

@app.get("/api/dashboard")
async def get_dashboard(
    user: Dict = Depends(get_current_user),
    new_layout: bool = Depends(require_feature_flag("new_dashboard_layout"))
):
    if new_layout:
        return {"dashboard": "new_layout"}
    else:
        return {"dashboard": "old_layout"}

@app.get("/api/lab-reports/{report_id}/summary")
async def get_lab_summary(
    report_id: str,
    user: Dict = Depends(get_current_user),
    ai_summary: bool = Depends(require_feature_flag("ai_lab_report_summary"))
):
    if ai_summary:
        return {"summary": "AI-generated summary"}
    else:
        return {"summary": "Standard summary"}
""" 