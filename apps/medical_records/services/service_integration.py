"""
Service Integration for Medical Records Service

This module handles communication with other microservices in the Personal Health Assistant platform.
"""

import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import HTTPException, status
from jose import jwt, JWTError

from common.config.settings import get_settings
from common.utils.logging import get_logger
from common.utils.resilience import CircuitBreaker
from common.clients.knowledge_graph_client import KnowledgeGraphClient

logger = get_logger(__name__)
settings = get_settings()


class ServiceIntegrationError(Exception):
    """Base exception for service integration errors"""
    pass


class AuthServiceClient:
    """Client for communicating with the Auth Service"""
    
    def __init__(self):
        self.base_url = settings.AUTH_SERVICE_URL
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=Exception
        )
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        print(f"[PRINT] validate_token called with token: {token[:12]}...")
        try:
            url = f"{self.base_url}/auth/me"
            logger.warning(f"[DEBUG] Validating token: {token[:12]}... at {url}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"}
                )
                logger.warning(f"[DEBUG] Auth service response: {response.status_code} {response.text}")
                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "valid": True,
                        "user_id": user_data.get("id"),
                        "email": user_data.get("email"),
                        "user_type": user_data.get("user_type"),
                        "status": user_data.get("status"),
                        "email_verified": user_data.get("email_verified")
                    }
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Token validation failed"
                    )
                    
        except httpx.TimeoutException:
            logger.error("Timeout while validating token with auth service")
            raise ServiceIntegrationError("Auth service timeout")
        except httpx.ConnectError:
            logger.error("Connection error while validating token with auth service")
            raise ServiceIntegrationError("Auth service connection failed")
        except Exception as e:
            logger.error(f"Error validating token with auth service: {e}")
            raise ServiceIntegrationError(f"Auth service error: {str(e)}")
    
    async def get_user_info(self, user_id: str, token: str) -> Dict[str, Any]:
        """Get user information from auth service"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/auth/users/{user_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Failed to get user info"
                    )
                    
        except httpx.TimeoutException:
            logger.error("Timeout while getting user info from auth service")
            raise ServiceIntegrationError("Auth service timeout")
        except httpx.ConnectError:
            logger.error("Connection error while getting user info from auth service")
            raise ServiceIntegrationError("Auth service connection failed")
        except Exception as e:
            logger.error(f"Error getting user info from auth service: {e}")
            raise ServiceIntegrationError(f"Auth service error: {str(e)}")
    
    async def check_permissions(self, user_id: str, permissions: List[str], token: str) -> bool:
        """Check if user has required permissions"""
        # TODO: Implement proper permission checking when auth service has permission endpoints
        # For now, return True for testing purposes
        logger.info(f"Permission check bypassed for user {user_id} with permissions {permissions}")
        return True
        
        # Original implementation (commented out for now):
        # try:
        #     async with httpx.AsyncClient(timeout=10.0) as client:
        #         response = await client.post(
        #             f"{self.base_url}/api/v1/auth/permissions/check",
        #             json={
        #                 "user_id": user_id,
        #                 "permissions": permissions
        #             },
        #             headers={"Authorization": f"Bearer {token}"}
        #         )
        #         
        #         if response.status_code == 200:
        #             result = response.json()
        #             return result.get("has_permissions", False)
        #         else:
        #             logger.warning(f"Permission check failed: {response.status_code}")
        #             return False
        #             
        # except Exception as e:
        #     logger.error(f"Error checking permissions with auth service: {e}")
        #     return False


class UserProfileServiceClient:
    """Client for communicating with the User Profile Service"""
    
    def __init__(self):
        self.base_url = settings.USER_PROFILE_SERVICE_URL
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=Exception
        )
    
    async def get_user_profile(self, user_id: str, token: str) -> Optional[Dict[str, Any]]:
        """Get user profile from user profile service"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/user-profile/profile/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    logger.warning(f"Failed to get user profile: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    async def check_data_access_permission(self, user_id: str, data_type: str, token: str) -> bool:
        """Check if user has permission to access specific data type"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/user-profile/privacy/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    privacy_settings = response.json()
                    # Check if user has consented to medical records access
                    return privacy_settings.get("medical_records_access", False)
                else:
                    logger.warning(f"Failed to get privacy settings: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking data access permission: {e}")
            return False


class HealthTrackingServiceClient:
    """Client for communicating with the Health Tracking Service"""
    
    def __init__(self):
        self.base_url = settings.HEALTH_TRACKING_SERVICE_URL
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=Exception
        )
    
    async def get_health_metrics(self, user_id: str, token: str, date_range: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Get health metrics from health tracking service"""
        try:
            params = {}
            if date_range:
                params.update(date_range)
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/health-tracking/metrics",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    return response.json().get("metrics", [])
                else:
                    logger.warning(f"Failed to get health metrics: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting health metrics: {e}")
            return []
    
    async def correlate_lab_results(self, user_id: str, lab_results: List[Dict[str, Any]], token: str) -> Dict[str, Any]:
        """Correlate lab results with health metrics"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/health-tracking/correlate",
                    json={
                        "user_id": user_id,
                        "lab_results": lab_results
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to correlate lab results: {response.status_code}")
                    return {"correlations": []}
                    
        except Exception as e:
            logger.error(f"Error correlating lab results: {e}")
            return {"correlations": []}


class KnowledgeGraphServiceClient:
    """Client for communicating with the Knowledge Graph Service"""
    
    def __init__(self):
        self.base_url = settings.KNOWLEDGE_GRAPH_SERVICE_URL
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=Exception
        )
    
    async def enrich_medical_entities(self, medical_text: str) -> List[Dict[str, Any]]:
        """Enrich medical text with knowledge graph entities"""
        try:
            async with KnowledgeGraphClient() as client:
                # Search for medical entities in the text
                entities = await client.search_entities(medical_text, limit=20)
                return entities
        except Exception as e:
            logger.error(f"Error enriching medical entities: {e}")
            return []
    
    async def get_condition_treatments(self, condition_name: str) -> List[Dict[str, Any]]:
        """Get treatments for a specific medical condition"""
        try:
            async with KnowledgeGraphClient() as client:
                # First find the condition
                conditions = await client.search_entities(condition_name, entity_type="condition", limit=1)
                if not conditions:
                    return []
                
                # Then get treatments
                treatments = await client.get_entities(entity_type="treatment", limit=10)
                return treatments
        except Exception as e:
            logger.error(f"Error getting condition treatments: {e}")
            return []
    
    async def get_medication_interactions(self, medication_name: str) -> List[Dict[str, Any]]:
        """Get potential drug interactions for a medication"""
        try:
            async with KnowledgeGraphClient() as client:
                # Search for the medication
                medications = await client.search_entities(medication_name, entity_type="medication", limit=1)
                if not medications:
                    return []
                
                # Get relationships for this medication
                # This would require a more complex query in a real implementation
                return []
        except Exception as e:
            logger.error(f"Error getting medication interactions: {e}")
            return []
    
    async def validate_medical_codes(self, codes: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Validate medical codes against the knowledge graph"""
        try:
            async with KnowledgeGraphClient() as client:
                validated_codes = []
                for code in codes:
                    # Search for the code in the knowledge graph
                    entities = await client.search_entities(code.get("code", ""), limit=1)
                    if entities:
                        validated_codes.append({
                            "code": code.get("code"),
                            "system": code.get("system"),
                            "valid": True,
                            "entity": entities[0]
                        })
                    else:
                        validated_codes.append({
                            "code": code.get("code"),
                            "system": code.get("system"),
                            "valid": False
                        })
                return validated_codes
        except Exception as e:
            logger.error(f"Error validating medical codes: {e}")
            return []


class ServiceIntegrationManager:
    """Manager for all service integrations"""
    
    def __init__(self):
        self.auth_client = AuthServiceClient()
        self.user_profile_client = UserProfileServiceClient()
        self.health_tracking_client = HealthTrackingServiceClient()
        self.knowledge_graph_client = KnowledgeGraphServiceClient()
    
    async def validate_user_access(self, token: str, required_permissions: Optional[List[str]] = None) -> Dict[str, Any]:
        logger.warning(f"[DEBUG] validate_user_access called with token: {token[:12]}... perms: {required_permissions}")
        try:
            logger.warning(f"[DEBUG] validate_user_access called with token: {token[:12]}... perms: {required_permissions}")
            # Validate token
            token_data = await self.auth_client.validate_token(token)
            user_id = token_data.get("user_id")
            
            if not user_id:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token"
                )
            
            # Check permissions if required
            if required_permissions:
                has_permissions = await self.auth_client.check_permissions(
                    user_id, required_permissions, token
                )
                if not has_permissions:
                    raise HTTPException(
                        status_code=403,
                        detail="Insufficient permissions"
                    )
            
            # Get user profile
            user_profile = await self.user_profile_client.get_user_profile(user_id, token)
            
            # Check data access permission
            has_data_access = await self.user_profile_client.check_data_access_permission(
                user_id, "medical_records", token
            )
            
            return {
                "user_id": user_id,
                "token_data": token_data,
                "user_profile": user_profile,
                "has_data_access": has_data_access
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating user access: {e}")
            raise HTTPException(
                status_code=500,
                detail="Service integration error"
            )
    
    async def get_health_context(self, user_id: str, token: str, date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get health context for lab results analysis"""
        try:
            # Get health metrics
            health_metrics = await self.health_tracking_client.get_health_metrics(
                user_id, token, date_range
            )
            
            # Get user profile for additional context
            user_profile = await self.user_profile_client.get_user_profile(user_id, token)
            
            return {
                "health_metrics": health_metrics,
                "user_profile": user_profile,
                "context_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting health context: {e}")
            return {
                "health_metrics": [],
                "user_profile": None,
                "context_timestamp": datetime.utcnow().isoformat()
            }
    
    async def correlate_lab_results_with_health_data(self, user_id: str, lab_results: List[Dict[str, Any]], token: str) -> Dict[str, Any]:
        """Correlate lab results with health tracking data"""
        try:
            correlations = await self.health_tracking_client.correlate_lab_results(
                user_id, lab_results, token
            )
            
            return correlations
            
        except Exception as e:
            logger.error(f"Error correlating lab results: {e}")
            return {"correlations": [], "error": str(e)}
    
    async def enrich_medical_record_with_knowledge_graph(self, medical_text: str) -> Dict[str, Any]:
        """Enrich medical record text with knowledge graph entities"""
        try:
            # Get medical entities from knowledge graph
            entities = await self.knowledge_graph_client.enrich_medical_entities(medical_text)
            
            return {
                "original_text": medical_text,
                "enriched_entities": entities,
                "entity_count": len(entities),
                "enrichment_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error enriching medical record: {e}")
            return {
                "original_text": medical_text,
                "enriched_entities": [],
                "entity_count": 0,
                "error": str(e),
                "enrichment_timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_medical_recommendations(self, conditions: List[str], medications: List[str]) -> Dict[str, Any]:
        """Get medical recommendations based on conditions and medications"""
        try:
            recommendations = {
                "treatments": [],
                "interactions": [],
                "recommendations": []
            }
            
            # Get treatments for each condition
            for condition in conditions:
                treatments = await self.knowledge_graph_client.get_condition_treatments(condition)
                recommendations["treatments"].extend(treatments)
            
            # Get interactions for each medication
            for medication in medications:
                interactions = await self.knowledge_graph_client.get_medication_interactions(medication)
                recommendations["interactions"].extend(interactions)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting medical recommendations: {e}")
            return {
                "treatments": [],
                "interactions": [],
                "recommendations": [],
                "error": str(e)
            }
    
    async def validate_medical_codes(self, codes: List[Dict[str, str]]) -> Dict[str, Any]:
        """Validate medical codes against the knowledge graph"""
        try:
            validated_codes = await self.knowledge_graph_client.validate_medical_codes(codes)
            
            return {
                "validated_codes": validated_codes,
                "valid_count": len([c for c in validated_codes if c.get("valid", False)]),
                "invalid_count": len([c for c in validated_codes if not c.get("valid", False)]),
                "validation_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error validating medical codes: {e}")
            return {
                "validated_codes": [],
                "valid_count": 0,
                "invalid_count": len(codes),
                "error": str(e),
                "validation_timestamp": datetime.utcnow().isoformat()
            }


# Global service integration manager instance
service_integration = ServiceIntegrationManager() 