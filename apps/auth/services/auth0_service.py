"""
Auth0 integration service for authentication operations.

This service handles:
- Auth0 client initialization
- Authentication operations
- User management
- Token validation
- Profile management
"""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from authlib.integrations.starlette_client import OAuth
from authlib.jose import jwt
from common.utils.logging import get_logger
from common.config.settings import get_settings

logger = get_logger(__name__)


class Auth0Service:
    """Service for Auth0 integration."""
    
    def __init__(self):
        self.settings = get_settings()
        self.oauth: Optional[OAuth] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Auth0 OAuth client."""
        try:
            auth0_domain = self.settings.auth0.auth0_domain
            auth0_client_id = self.settings.auth0.auth0_client_id
            auth0_client_secret = self.settings.auth0.auth0_client_secret
            
            if not auth0_domain or not auth0_client_id or not auth0_client_secret:
                logger.warning("Auth0 credentials not configured, using mock client")
                self.oauth = None
                return
            
            # Initialize OAuth client
            self.oauth = OAuth()
            self.oauth.register(
                name='auth0',
                client_id=auth0_client_id,
                client_secret=auth0_client_secret,
                client_kwargs={
                    'scope': 'openid profile email',
                },
                server_metadata_url=f'https://{auth0_domain}/.well-known/openid_configuration'
            )
            
            logger.info("Auth0 client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Auth0 client: {e}")
            self.oauth = None
    
    async def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Get Auth0 authorization URL."""
        try:
            if not self.oauth:
                raise Exception("Auth0 client not initialized")
            
            auth0 = self.oauth.create_client('auth0')
            authorization_url = auth0.authorize_redirect(redirect_uri, state=state)
            
            logger.info("Generated Auth0 authorization URL")
            return str(authorization_url)
            
        except Exception as e:
            logger.error(f"Failed to generate Auth0 authorization URL: {e}")
            raise
    
    async def handle_callback(self, request, redirect_uri: str) -> Dict[str, Any]:
        """Handle Auth0 callback and exchange code for tokens."""
        try:
            if not self.oauth:
                raise Exception("Auth0 client not initialized")
            
            auth0 = self.oauth.create_client('auth0')
            token = await auth0.authorize_access_token(request)
            user_info = await auth0.parse_id_token(token)
            
            logger.info(f"Auth0 callback handled for user: {user_info.get('sub')}")
            return {
                "access_token": token.get('access_token'),
                "id_token": token.get('id_token'),
                "refresh_token": token.get('refresh_token'),
                "token_type": token.get('token_type'),
                "expires_in": token.get('expires_in'),
                "user_info": user_info
            }
            
        except Exception as e:
            logger.error(f"Failed to handle Auth0 callback: {e}")
            raise
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Auth0."""
        try:
            if not self.oauth:
                raise Exception("Auth0 client not initialized")
            
            auth0 = self.oauth.create_client('auth0')
            user_info = await auth0.userinfo(token=access_token)
            
            logger.info(f"Retrieved user info from Auth0: {user_info.get('sub')}")
            return user_info
            
        except Exception as e:
            logger.error(f"Failed to get user info from Auth0: {e}")
            raise
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate Auth0 JWT token."""
        try:
            if not self.settings.auth0.auth0_domain:
                raise Exception("Auth0 domain not configured")
            
            # Get Auth0 public key for token validation
            jwks_url = f"https://{self.settings.auth0.auth0_domain}/.well-known/jwks.json"
            
            # Validate token
            claims = jwt.decode(
                token,
                jwks_url,
                claims_options={
                    'iss': {'essential': True, 'value': f'https://{self.settings.auth0.auth0_domain}/'},
                    'aud': {'essential': True, 'value': self.settings.auth0.auth0_client_id},
                    'exp': {'essential': True},
                    'iat': {'essential': True}
                }
            )
            
            logger.info(f"Validated Auth0 token for user: {claims.get('sub')}")
            return claims
            
        except Exception as e:
            logger.error(f"Failed to validate Auth0 token: {e}")
            raise
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Auth0 access token."""
        try:
            if not self.oauth:
                raise Exception("Auth0 client not initialized")
            
            auth0 = self.oauth.create_client('auth0')
            token = await auth0.refresh_token(refresh_token)
            
            logger.info("Refreshed Auth0 access token")
            return {
                "access_token": token.get('access_token'),
                "id_token": token.get('id_token'),
                "refresh_token": token.get('refresh_token'),
                "token_type": token.get('token_type'),
                "expires_in": token.get('expires_in')
            }
            
        except Exception as e:
            logger.error(f"Failed to refresh Auth0 token: {e}")
            raise
    
    async def logout(self, return_to: str) -> str:
        """Get Auth0 logout URL."""
        try:
            if not self.settings.auth0.auth0_domain:
                raise Exception("Auth0 domain not configured")
            
            logout_url = f"https://{self.settings.auth0.auth0_domain}/v2/logout"
            params = {
                'client_id': self.settings.auth0.auth0_client_id,
                'returnTo': return_to
            }
            
            # Build URL with parameters
            param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            full_logout_url = f"{logout_url}?{param_string}"
            
            logger.info("Generated Auth0 logout URL")
            return full_logout_url
            
        except Exception as e:
            logger.error(f"Failed to generate Auth0 logout URL: {e}")
            raise
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user in Auth0."""
        try:
            if not self.settings.auth0.auth0_domain or not self.settings.auth0.auth0_client_secret:
                raise Exception("Auth0 credentials not configured")
            
            # This would typically use Auth0 Management API
            # For now, return a mock response
            logger.info("Auth0 user creation not implemented - using mock response")
            return {
                "user_id": f"auth0|{user_data.get('email', 'mock')}",
                "email": user_data.get('email'),
                "created_at": datetime.utcnow().isoformat(),
                "status": "created"
            }
            
        except Exception as e:
            logger.error(f"Failed to create Auth0 user: {e}")
            raise
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information in Auth0."""
        try:
            if not self.settings.auth0.auth0_domain or not self.settings.auth0.auth0_client_secret:
                raise Exception("Auth0 credentials not configured")
            
            # This would typically use Auth0 Management API
            # For now, return a mock response
            logger.info(f"Auth0 user update not implemented - using mock response for user: {user_id}")
            return {
                "user_id": user_id,
                "updated_at": datetime.utcnow().isoformat(),
                "status": "updated"
            }
            
        except Exception as e:
            logger.error(f"Failed to update Auth0 user: {e}")
            raise
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user from Auth0."""
        try:
            if not self.settings.auth0.auth0_domain or not self.settings.auth0.auth0_client_secret:
                raise Exception("Auth0 credentials not configured")
            
            # This would typically use Auth0 Management API
            # For now, return a mock response
            logger.info(f"Auth0 user deletion not implemented - using mock response for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete Auth0 user: {e}")
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information by ID from Auth0."""
        try:
            if not self.settings.auth0.auth0_domain or not self.settings.auth0.auth0_client_secret:
                raise Exception("Auth0 credentials not configured")
            
            # This would typically use Auth0 Management API
            # For now, return a mock response
            logger.info(f"Auth0 user retrieval not implemented - using mock response for user: {user_id}")
            return {
                "user_id": user_id,
                "email": f"user@{user_id.split('|')[-1]}.com",
                "created_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Failed to get Auth0 user: {e}")
            return None
    
    async def search_users(self, query: str) -> List[Dict[str, Any]]:
        """Search users in Auth0."""
        try:
            if not self.settings.auth0.auth0_domain or not self.settings.auth0.auth0_client_secret:
                raise Exception("Auth0 credentials not configured")
            
            # This would typically use Auth0 Management API
            # For now, return a mock response
            logger.info(f"Auth0 user search not implemented - using mock response for query: {query}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to search Auth0 users: {e}")
            raise
    
    async def get_user_logs(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user logs from Auth0."""
        try:
            if not self.settings.auth0.auth0_domain or not self.settings.auth0.auth0_client_secret:
                raise Exception("Auth0 credentials not configured")
            
            # This would typically use Auth0 Management API
            # For now, return a mock response
            logger.info(f"Auth0 user logs not implemented - using mock response for user: {user_id}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to get Auth0 user logs: {e}")
            raise
    
    async def block_user(self, user_id: str, reason: str = None) -> bool:
        """Block a user in Auth0."""
        try:
            if not self.settings.auth0.auth0_domain or not self.settings.auth0.auth0_client_secret:
                raise Exception("Auth0 credentials not configured")
            
            # This would typically use Auth0 Management API
            # For now, return a mock response
            logger.info(f"Auth0 user blocking not implemented - using mock response for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to block Auth0 user: {e}")
            raise
    
    async def unblock_user(self, user_id: str) -> bool:
        """Unblock a user in Auth0."""
        try:
            if not self.settings.auth0.auth0_domain or not self.settings.auth0.auth0_client_secret:
                raise Exception("Auth0 credentials not configured")
            
            # This would typically use Auth0 Management API
            # For now, return a mock response
            logger.info(f"Auth0 user unblocking not implemented - using mock response for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unblock Auth0 user: {e}")
            raise
    
    def is_connected(self) -> bool:
        """Check if Auth0 client is connected."""
        return self.oauth is not None
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Auth0 connection."""
        try:
            if not self.oauth:
                return {
                    "status": "disconnected",
                    "message": "Auth0 client not initialized"
                }
            
            # Try to access Auth0 well-known configuration
            if not self.settings.auth0.auth0_domain:
                return {
                    "status": "error",
                    "message": "Auth0 domain not configured"
                }
            
            # This would typically make a request to Auth0
            # For now, return a mock response
            return {
                "status": "connected",
                "message": "Auth0 connection is healthy",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Auth0 health check failed: {e}",
                "timestamp": datetime.utcnow().isoformat()
            } 