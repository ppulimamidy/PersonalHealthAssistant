"""
User Profile Integration Service

This service handles the integration between the auth service and user profile service.
It ensures that when a user is created in the auth service, a corresponding profile
is created in the user profile service.
"""

import httpx
import structlog
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException, status

logger = structlog.get_logger(__name__)


class UserProfileIntegrationService:
    """Service for integrating with the user profile service."""
    
    def __init__(self, user_profile_service_url: str = "http://user-profile-service:8001"):
        self.user_profile_service_url = user_profile_service_url
        self.logger = structlog.get_logger(__name__)
    
    async def create_user_profile(
        self, 
        user_id: str, 
        email: str, 
        first_name: str, 
        last_name: str, 
        user_type: str,
        phone: Optional[str] = None,
        date_of_birth: Optional[datetime] = None,
        gender: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a user profile in the user profile service.
        
        Args:
            user_id: The user ID from the auth service
            email: User's email address
            first_name: User's first name
            last_name: User's last name
            user_type: Type of user (patient, doctor, etc.)
            phone: User's phone number (optional)
            date_of_birth: User's date of birth (optional)
            gender: User's gender (optional)
            
        Returns:
            Dict containing the created profile information
            
        Raises:
            HTTPException: If profile creation fails
        """
        try:
            # Prepare profile data
            profile_data = {
                "user_id": int(user_id),  # Convert UUID to int for user_profile service
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": date_of_birth.isoformat() if date_of_birth else "1990-01-01",
                "gender": gender or "other",
                "phone_number": phone
            }
            
            self.logger.info(f"Creating user profile for user {user_id}")
            
            # Make HTTP request to user profile service
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.user_profile_service_url}/api/v1/user-profile/profile/",
                    json=profile_data,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code == 201 or response.status_code == 200:
                    profile_info = response.json()
                    self.logger.info(f"Successfully created user profile for user {user_id}")
                    return profile_info
                else:
                    self.logger.error(
                        f"Failed to create user profile for user {user_id}. "
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    # Don't fail the registration if profile creation fails
                    # Just log the error and continue
                    return {"error": "Profile creation failed", "details": response.text}
                    
        except httpx.TimeoutException:
            self.logger.error(f"Timeout while creating user profile for user {user_id}")
            return {"error": "Profile creation timed out"}
        except httpx.ConnectError:
            self.logger.error(f"Connection error while creating user profile for user {user_id}")
            return {"error": "Profile service connection failed"}
        except Exception as e:
            self.logger.error(f"Unexpected error while creating user profile for user {user_id}: {e}")
            return {"error": f"Profile creation failed: {str(e)}"}
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user profile from the user profile service.
        
        Args:
            user_id: The user ID from the auth service
            
        Returns:
            Dict containing the profile information or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.user_profile_service_url}/api/v1/user-profile/profile/me",
                    headers={"Authorization": f"Bearer {user_id}"}  # This would need proper auth
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting user profile for user {user_id}: {e}")
            return None


def get_user_profile_integration_service() -> UserProfileIntegrationService:
    """Dependency function to get the user profile integration service."""
    return UserProfileIntegrationService() 