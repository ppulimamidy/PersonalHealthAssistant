"""
Supabase integration service for authentication and database operations.

This service handles:
- Supabase client initialization
- Authentication operations
- Database operations
- Real-time subscriptions
- Storage operations
"""

import os
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from common.utils.logging import get_logger
from common.config.settings import get_settings

logger = get_logger(__name__)


class SupabaseService:
    """Service for Supabase integration."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Supabase client."""
        try:
            supabase_url = self.settings.supabase.supabase_url
            supabase_key = self.settings.supabase.supabase_anon_key
            
            if not supabase_url or not supabase_key:
                logger.warning("Supabase credentials not configured, using mock client")
                self.client = None
                return
            
            # Configure client options
            options = ClientOptions(
                schema="public",
                headers={
                    "X-Client-Info": "personal-health-assistant/1.0.0"
                }
            )
            
            self.client = create_client(supabase_url, supabase_key, options)
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
    
    async def create_user(self, email: str, password: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user in Supabase Auth."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            # Create user in Supabase Auth
            auth_response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_data
                }
            })
            
            if auth_response.user:
                logger.info(f"Created Supabase user: {auth_response.user.id}")
                return {
                    "user_id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "created_at": auth_response.user.created_at,
                    "email_confirmed_at": auth_response.user.email_confirmed_at
                }
            else:
                raise Exception("Failed to create user in Supabase Auth")
                
        except Exception as e:
            logger.error(f"Failed to create Supabase user: {e}")
            raise
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in user with email and password."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            auth_response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user and auth_response.session:
                logger.info(f"User signed in: {auth_response.user.id}")
                return {
                    "user": auth_response.user,
                    "session": auth_response.session,
                    "access_token": auth_response.session.access_token,
                    "refresh_token": auth_response.session.refresh_token
                }
            else:
                raise Exception("Invalid credentials")
                
        except Exception as e:
            logger.error(f"Failed to sign in user: {e}")
            raise
    
    async def sign_out(self, access_token: str) -> bool:
        """Sign out user."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            self.client.auth.sign_out()
            logger.info("User signed out successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sign out user: {e}")
            raise
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            auth_response = self.client.auth.refresh_session(refresh_token)
            
            if auth_response.session:
                logger.info("Token refreshed successfully")
                return {
                    "access_token": auth_response.session.access_token,
                    "refresh_token": auth_response.session.refresh_token,
                    "expires_at": auth_response.session.expires_at
                }
            else:
                raise Exception("Failed to refresh token")
                
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            raise
    
    async def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            # Set the access token
            self.client.auth.set_session(access_token, access_token)
            
            # Get user
            user = self.client.auth.get_user()
            
            if user.user:
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "email_confirmed_at": user.user.email_confirmed_at,
                    "created_at": user.user.created_at,
                    "updated_at": user.user.updated_at,
                    "user_metadata": user.user.user_metadata
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
    
    async def update_user(self, access_token: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            # Set the access token
            self.client.auth.set_session(access_token, access_token)
            
            # Update user
            auth_response = self.client.auth.update_user(user_data)
            
            if auth_response.user:
                logger.info(f"Updated user: {auth_response.user.id}")
                return {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "user_metadata": auth_response.user.user_metadata,
                    "updated_at": auth_response.user.updated_at
                }
            else:
                raise Exception("Failed to update user")
                
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            raise
    
    async def reset_password(self, email: str) -> bool:
        """Send password reset email."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            self.client.auth.reset_password_email(email)
            logger.info(f"Password reset email sent to: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            raise
    
    async def verify_otp(self, email: str, token: str, type: str = "email") -> Dict[str, Any]:
        """Verify OTP for email confirmation or password reset."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            auth_response = self.client.auth.verify_otp({
                "email": email,
                "token": token,
                "type": type
            })
            
            if auth_response.user:
                logger.info(f"OTP verified for user: {auth_response.user.id}")
                return {
                    "user_id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "email_confirmed_at": auth_response.user.email_confirmed_at
                }
            else:
                raise Exception("Invalid OTP")
                
        except Exception as e:
            logger.error(f"Failed to verify OTP: {e}")
            raise
    
    async def insert_data(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert data into Supabase table."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            response = self.client.table(table).insert(data).execute()
            
            if response.data:
                logger.info(f"Data inserted into {table}: {len(response.data)} records")
                return response.data[0] if len(response.data) == 1 else response.data
            else:
                raise Exception(f"Failed to insert data into {table}")
                
        except Exception as e:
            logger.error(f"Failed to insert data into {table}: {e}")
            raise
    
    async def get_data(self, table: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get data from Supabase table."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            query = self.client.table(table).select("*")
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.execute()
            
            if response.data is not None:
                logger.info(f"Retrieved {len(response.data)} records from {table}")
                return response.data
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to get data from {table}: {e}")
            raise
    
    async def update_data(self, table: str, data: Dict[str, Any], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Update data in Supabase table."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            query = self.client.table(table).update(data)
            
            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            
            if response.data is not None:
                logger.info(f"Updated {len(response.data)} records in {table}")
                return response.data
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to update data in {table}: {e}")
            raise
    
    async def delete_data(self, table: str, filters: Dict[str, Any]) -> bool:
        """Delete data from Supabase table."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            query = self.client.table(table).delete()
            
            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            
            logger.info(f"Deleted data from {table}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete data from {table}: {e}")
            raise
    
    async def subscribe_to_changes(self, table: str, callback) -> str:
        """Subscribe to real-time changes in a table."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            subscription = self.client.table(table).on("*", callback).subscribe()
            logger.info(f"Subscribed to changes in {table}")
            return subscription
            
        except Exception as e:
            logger.error(f"Failed to subscribe to changes in {table}: {e}")
            raise
    
    async def upload_file(self, bucket: str, path: str, file_data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload file to Supabase Storage."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            response = self.client.storage.from_(bucket).upload(
                path=path,
                file=file_data,
                file_options={"content-type": content_type}
            )
            
            # Get public URL
            url = self.client.storage.from_(bucket).get_public_url(path)
            
            logger.info(f"File uploaded to {bucket}/{path}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to upload file to {bucket}/{path}: {e}")
            raise
    
    async def download_file(self, bucket: str, path: str) -> bytes:
        """Download file from Supabase Storage."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            response = self.client.storage.from_(bucket).download(path)
            
            logger.info(f"File downloaded from {bucket}/{path}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to download file from {bucket}/{path}: {e}")
            raise
    
    async def delete_file(self, bucket: str, path: str) -> bool:
        """Delete file from Supabase Storage."""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            self.client.storage.from_(bucket).remove([path])
            
            logger.info(f"File deleted from {bucket}/{path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from {bucket}/{path}: {e}")
            raise
    
    def is_connected(self) -> bool:
        """Check if Supabase client is connected."""
        return self.client is not None
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Supabase connection."""
        try:
            if not self.client:
                return {
                    "status": "disconnected",
                    "message": "Supabase client not initialized"
                }
            
            # Try a simple query to test connection
            response = self.client.table("users").select("count", count="exact").limit(1).execute()
            
            return {
                "status": "connected",
                "message": "Supabase connection is healthy",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Supabase health check failed: {e}",
                "timestamp": datetime.utcnow().isoformat()
            } 