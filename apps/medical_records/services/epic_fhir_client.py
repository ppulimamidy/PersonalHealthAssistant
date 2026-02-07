"""
Epic FHIR Client Service

This module provides a specialized FHIR client for Epic EHR integration,
including test sandbox support and Epic-specific functionality.
"""

import httpx
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlencode, parse_qs, urlparse
import json
import logging
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field

from common.utils.logging import get_logger
from common.utils.resilience import CircuitBreaker
from .fhir_client import FHIRClient, FHIRClientConfig, FHIRResourceType, FHIRSearchParam, FHIRSearchParamType
from ..config.epic_fhir_config import epic_fhir_config, EpicEnvironment, EPIC_FHIR_RESOURCES, EPIC_FHIR_HEADERS

logger = get_logger(__name__)


class EpicFHIRLaunchType(str, Enum):
    """Epic FHIR launch types."""
    SMART_ON_FHIR = "smart_on_fhir"
    CLIENT_CREDENTIALS = "client_credentials"
    AUTHORIZATION_CODE = "authorization_code"


class EpicFHIRLaunchContext(BaseModel):
    """Epic FHIR launch context."""
    launch_type: EpicFHIRLaunchType
    patient_id: Optional[str] = None
    encounter_id: Optional[str] = None
    user_id: Optional[str] = None
    app_context: Optional[str] = None
    launch_url: Optional[str] = None
    redirect_uri: Optional[str] = None
    state: Optional[str] = None
    scope: Optional[str] = None


class EpicFHIRToken(BaseModel):
    """Epic FHIR token model."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    expires_at: Optional[datetime] = None
    patient_id: Optional[str] = None
    encounter_id: Optional[str] = None
    user_id: Optional[str] = None


class EpicFHIRClientConfig(FHIRClientConfig):
    """Epic FHIR client configuration."""
    epic_environment: EpicEnvironment = EpicEnvironment.SANDBOX
    launch_type: EpicFHIRLaunchType = EpicFHIRLaunchType.CLIENT_CREDENTIALS
    enable_smart_on_fhir: bool = True
    enable_test_patients: bool = True
    enable_launch_context: bool = True
    
    def __init__(self, **data):
        # Set Epic-specific defaults
        if "base_url" not in data:
            data["base_url"] = epic_fhir_config.base_url
        if "client_id" not in data:
            data["client_id"] = epic_fhir_config.client_id
        if "client_secret" not in data:
            data["client_secret"] = epic_fhir_config.client_secret
        if "scope" not in data:
            data["scope"] = epic_fhir_config.scope
        
        super().__init__(**data)
    
    @property
    def oauth_url(self) -> str:
        """Get the OAuth URL for the current environment."""
        return epic_fhir_config.oauth_url
    
    # Redirect URI is handled directly in the client methods


class EpicFHIRClient(FHIRClient):
    """Epic FHIR client with Epic-specific functionality."""
    
    def __init__(self, config: EpicFHIRClientConfig):
        super().__init__(config)
        self.epic_config = config
        self.launch_context: Optional[EpicFHIRLaunchContext] = None
        self.epic_token: Optional[EpicFHIRToken] = None
        
        # Epic-specific headers
        self.epic_headers = EPIC_FHIR_HEADERS.copy()
    
    async def authenticate_with_launch_context(
        self, 
        launch_context: EpicFHIRLaunchContext
    ) -> EpicFHIRToken:
        """Authenticate using SMART on FHIR launch context."""
        try:
            self.launch_context = launch_context
            
            if launch_context.launch_type == EpicFHIRLaunchType.SMART_ON_FHIR:
                return await self._authenticate_smart_on_fhir(launch_context)
            elif launch_context.launch_type == EpicFHIRLaunchType.CLIENT_CREDENTIALS:
                return await self._authenticate_client_credentials()
            elif launch_context.launch_type == EpicFHIRLaunchType.AUTHORIZATION_CODE:
                return await self._authenticate_authorization_code(launch_context)
            else:
                raise ValueError(f"Unsupported launch type: {launch_context.launch_type}")
                
        except Exception as e:
            logger.error(f"Epic FHIR authentication error: {e}")
            raise
    
    async def _authenticate_smart_on_fhir(
        self, 
        launch_context: EpicFHIRLaunchContext
    ) -> EpicFHIRToken:
        """Authenticate using SMART on FHIR launch."""
        try:
            # Parse launch URL to extract parameters
            parsed_url = urlparse(launch_context.launch_url)
            query_params = parse_qs(parsed_url.query)
            
            # Extract launch parameters
            launch_token = query_params.get("launch", [None])[0]
            iss = query_params.get("iss", [None])[0]
            
            if not launch_token:
                raise ValueError("Launch token not found in launch URL")
            
            # Exchange launch token for access token
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    self.config.token_endpoint,
                    data={
                        "grant_type": "authorization_code",
                        "code": launch_token,
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        "redirect_uri": launch_context.redirect_uri or "http://localhost:8080/callback"
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")
                
                token_data = response.json()
                
                # Create Epic FHIR token
                self.epic_token = EpicFHIRToken(
                    access_token=token_data["access_token"],
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_in=token_data.get("expires_in"),
                    refresh_token=token_data.get("refresh_token"),
                    scope=token_data.get("scope"),
                    patient_id=token_data.get("patient"),
                    encounter_id=token_data.get("encounter"),
                    user_id=token_data.get("user")
                )
                
                if self.epic_token.expires_in:
                    self.epic_token.expires_at = datetime.utcnow() + timedelta(
                        seconds=self.epic_token.expires_in
                    )
                
                logger.info("Epic FHIR SMART on FHIR authentication successful")
                return self.epic_token
                
        except Exception as e:
            logger.error(f"SMART on FHIR authentication error: {e}")
            raise
    
    async def _authenticate_client_credentials(self) -> EpicFHIRToken:
        """Authenticate using client credentials flow."""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                # For Epic FHIR sandbox, we need OAuth2 with client ID and blank client secret
                auth_data = {
                    "grant_type": "client_credentials",
                    "client_id": self.config.client_id,
                    "scope": self.config.scope
                }
                
                # Add client secret (can be blank for sandbox)
                if self.config.client_secret is not None:
                    auth_data["client_secret"] = self.config.client_secret
                else:
                    # For sandbox, use empty string as client secret
                    auth_data["client_secret"] = ""
                
                response = await client.post(
                    self.config.token_endpoint,
                    data=auth_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Client credentials authentication failed: {response.status_code} - {response.text}")
                
                token_data = response.json()
                
                # Create Epic FHIR token
                self.epic_token = EpicFHIRToken(
                    access_token=token_data["access_token"],
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_in=token_data.get("expires_in"),
                    refresh_token=token_data.get("refresh_token"),
                    scope=token_data.get("scope")
                )
                
                if self.epic_token.expires_in:
                    self.epic_token.expires_at = datetime.utcnow() + timedelta(
                        seconds=self.epic_token.expires_in
                    )
                
                logger.info("Epic FHIR client credentials authentication successful")
                return self.epic_token
                
        except Exception as e:
            logger.error(f"Client credentials authentication error: {e}")
            raise
    
    async def _authenticate_authorization_code(
        self, 
        launch_context: EpicFHIRLaunchContext
    ) -> EpicFHIRToken:
        """Authenticate using authorization code flow."""
        try:
            # Generate authorization URL
            auth_url = self._generate_authorization_url(launch_context)
            logger.info(f"Authorization URL: {auth_url}")
            
            # For now, we'll use client credentials as fallback
            # In a real implementation, you would redirect the user to the auth URL
            # and handle the callback with the authorization code
            return await self._authenticate_client_credentials()
            
        except Exception as e:
            logger.error(f"Authorization code authentication error: {e}")
            raise
    
    async def _exchange_authorization_code(self, code: str) -> EpicFHIRToken:
        """Exchange authorization code for access token."""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    self.config.token_endpoint,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        "redirect_uri": epic_fhir_config.redirect_uri or "http://localhost:8080/api/v1/medical-records/epic-fhir/callback"
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")
                
                token_data = response.json()
                
                # Create Epic FHIR token
                self.epic_token = EpicFHIRToken(
                    access_token=token_data["access_token"],
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_in=token_data.get("expires_in"),
                    refresh_token=token_data.get("refresh_token"),
                    scope=token_data.get("scope"),
                    patient_id=token_data.get("patient"),
                    encounter_id=token_data.get("encounter"),
                    user_id=token_data.get("user")
                )
                
                if self.epic_token.expires_in:
                    self.epic_token.expires_at = datetime.utcnow() + timedelta(
                        seconds=self.epic_token.expires_in
                    )
                
                logger.info("Epic FHIR authorization code exchange successful")
                return self.epic_token
                
        except Exception as e:
            logger.error(f"Authorization code exchange error: {e}")
            raise
    
    def _generate_authorization_url(self, launch_context: EpicFHIRLaunchContext) -> str:
        """Generate authorization URL for OAuth2 flow."""
        params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": launch_context.redirect_uri or "http://localhost:8080/callback",
            "scope": launch_context.scope or self.config.scope,
            "state": launch_context.state or "random_state"
        }
        
        if launch_context.patient_id:
            params["launch"] = launch_context.patient_id
        
        return f"{self.config.authorize_endpoint}?{urlencode(params)}"
    
    async def _ensure_epic_token(self) -> str:
        """Ensure we have a valid Epic FHIR token."""
        if not self.epic_token or (
            self.epic_token.expires_at and 
            datetime.utcnow() >= self.epic_token.expires_at
        ):
            if self.launch_context:
                await self.authenticate_with_launch_context(self.launch_context)
            else:
                await self._authenticate_client_credentials()
        
        return self.epic_token.access_token
    
    async def _make_epic_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to Epic FHIR server."""
        
        @self.circuit_breaker
        async def _request():
            token = await self._ensure_epic_token()
            
            url = urljoin(self.config.base_url, endpoint)
            request_headers = self.epic_headers.copy()
            request_headers["Authorization"] = f"Bearer {token}"
            
            if headers:
                request_headers.update(headers)
            
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers
                )
                
                if response.status_code == 401:
                    # Token expired, try to re-authenticate
                    if self.launch_context:
                        await self.authenticate_with_launch_context(self.launch_context)
                    else:
                        await self._authenticate_client_credentials()
                    
                    token = await self._ensure_epic_token()
                    request_headers["Authorization"] = f"Bearer {token}"
                    
                    response = await client.request(
                        method=method,
                        url=url,
                        params=params,
                        json=data,
                        headers=request_headers
                    )
                
                if response.status_code == 404:
                    raise Exception(f"Resource not found: {endpoint}")
                
                if response.status_code >= 400:
                    raise Exception(f"Epic FHIR request failed: {response.status_code} - {response.text}")
                
                return response.json()
        
        # TODO: Add retry logic here if needed. For now, just call _request directly.
        return await _request()

    async def _make_sandbox_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an unauthenticated request to Epic FHIR sandbox for testing."""
        
        @self.circuit_breaker
        async def _request():
            url = urljoin(self.config.base_url, endpoint)
            request_headers = {
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json"
            }
            
            if headers:
                request_headers.update(headers)
            
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers
                )
                
                if response.status_code == 404:
                    raise Exception(f"Resource not found: {endpoint}")
                
                if response.status_code >= 400:
                    raise Exception(f"Epic FHIR sandbox request failed: {response.status_code} - {response.text}")
                
                return response.json()
        
        return await _request()
    
    async def get_test_patient(self, patient_name: str) -> Dict[str, Any]:
        """Get a test patient from Epic sandbox."""
        try:
            patient_id = epic_fhir_config.get_test_patient_id(patient_name)
            if not patient_id:
                raise ValueError(f"Test patient '{patient_name}' not found")
            
            return await self.get_resource(FHIRResourceType.PATIENT, patient_id)
            
        except Exception as e:
            logger.error(f"Error getting test patient {patient_name}: {e}")
            raise
    
    async def get_test_patient_observations(
        self, 
        patient_name: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get observations for a test patient."""
        try:
            patient_id = epic_fhir_config.get_test_patient_id(patient_name)
            if not patient_id:
                raise ValueError(f"Test patient '{patient_name}' not found")
            
            return await self.get_patient_observations(patient_id, date_from, date_to, category)
            
        except Exception as e:
            logger.error(f"Error getting observations for test patient {patient_name}: {e}")
            raise

    async def get_sandbox_test_patient_observations(
        self, 
        patient_name: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get observations for a test patient using sandbox (no authentication)."""
        try:
            patient_id = epic_fhir_config.get_test_patient_id(patient_name)
            if not patient_id:
                raise ValueError(f"Test patient '{patient_name}' not found")
            
            # Build query parameters
            params = {"patient": patient_id}
            
            if date_from:
                params["date"] = f"ge{date_from.strftime('%Y-%m-%d')}"
            
            if date_to:
                if "date" in params:
                    params["date"] += f"&date=le{date_to.strftime('%Y-%m-%d')}"
                else:
                    params["date"] = f"le{date_to.strftime('%Y-%m-%d')}"
            
            if category:
                params["category"] = category
            
            # Make sandbox request
            return await self._make_sandbox_request("GET", "/Observation", params=params)
            
        except Exception as e:
            logger.error(f"Error getting sandbox observations for test patient {patient_name}: {e}")
            raise
    
    async def get_test_patient_diagnostic_reports(
        self, 
        patient_name: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get diagnostic reports for a test patient."""
        try:
            patient_id = epic_fhir_config.get_test_patient_id(patient_name)
            if not patient_id:
                raise ValueError(f"Test patient '{patient_name}' not found")
            
            return await self.get_patient_diagnostic_reports(patient_id, date_from, date_to, category)
            
        except Exception as e:
            logger.error(f"Error getting diagnostic reports for test patient {patient_name}: {e}")
            raise
    
    async def get_test_patient_documents(
        self, 
        patient_name: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        doc_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get document references for a test patient."""
        try:
            patient_id = epic_fhir_config.get_test_patient_id(patient_name)
            if not patient_id:
                raise ValueError(f"Test patient '{patient_name}' not found")
            
            return await self.get_patient_documents(patient_id, date_from, date_to, doc_type)
            
        except Exception as e:
            logger.error(f"Error getting documents for test patient {patient_name}: {e}")
            raise
    
    async def get_test_patient_imaging_studies(
        self, 
        patient_name: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        modality: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get imaging studies for a test patient."""
        try:
            patient_id = epic_fhir_config.get_test_patient_id(patient_name)
            if not patient_id:
                raise ValueError(f"Test patient '{patient_name}' not found")
            
            return await self.get_patient_imaging_studies(patient_id, date_from, date_to, modality)
            
        except Exception as e:
            logger.error(f"Error getting imaging studies for test patient {patient_name}: {e}")
            raise
    
    async def get_patient_info(self, patient_id: str) -> Dict[str, Any]:
        """Get patient information using the access token."""
        try:
            if not self.epic_token or self.epic_token.is_expired():
                raise Exception("No valid OAuth2 token available")
            
            endpoint = f"/Patient/{patient_id}"
            response = await self._make_epic_request("GET", endpoint)
            
            logger.info(f"Successfully fetched patient info for {patient_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching patient info: {e}")
            raise

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Epic FHIR server."""
        try:
            # Try to get the FHIR server metadata
            response = await self._make_epic_request("GET", "/metadata")
            
            return {
                "status": "connected",
                "fhir_version": response.get("fhirVersion"),
                "server_name": response.get("software", {}).get("name"),
                "server_version": response.get("software", {}).get("version"),
                "environment": self.epic_config.epic_environment.value,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Epic FHIR connection test failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "environment": self.epic_config.epic_environment.value,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_available_test_patients(self) -> List[Dict[str, Any]]:
        """Get list of available test patients."""
        try:
            patients = []
            for name, patient_id in epic_fhir_config.test_patients.items():
                # Return basic patient info without requiring authentication
                # This allows the frontend to see available patients for OAuth2 flow
                patients.append({
                    "name": name,
                    "patient_id": patient_id,
                    "display_name": name.title(),  # Capitalize first letter
                    "gender": "unknown",  # Will be populated after OAuth2 authentication
                    "birth_date": None,   # Will be populated after OAuth2 authentication
                    "status": "requires_oauth2"  # Indicate that OAuth2 is needed
                })
            
            return patients
            
        except Exception as e:
            logger.error(f"Error getting available test patients: {e}")
            raise

    def get_authorization_url(self, patient_name: Optional[str] = None) -> str:
        """Generate Epic FHIR OAuth2 authorization URL with SMART on FHIR launch context."""
        import secrets
        from urllib.parse import urlencode
        
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Get redirect URI directly from epic_fhir_config
        redirect_uri = epic_fhir_config.redirect_uri or "http://localhost:8005/api/v1/medical-records/epic-fhir/callback"
        
        # Build authorization URL with proper URL encoding
        auth_params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": redirect_uri,
            "scope": self.config.scope,
            "state": state,
            "aud": self.config.base_url
        }
        
        # Note: For standalone OAuth flow, we don't include launch parameter
        # Launch parameters are only used in SMART on FHIR launch flows from within the EHR
        # In standalone OAuth, we'll get patient context after authentication
        if patient_name:
            logger.info(f"Patient context will be set after OAuth for patient: {patient_name}")
        
        # Properly encode the query parameters using urlencode
        query_string = urlencode(auth_params)
        
        return f"{self.config.oauth_url}/authorize?{query_string}"

    async def exchange_authorization_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                token_data = {
                    "grant_type": "authorization_code",
                    "client_id": self.config.client_id,
                    "code": code,
                    "redirect_uri": epic_fhir_config.redirect_uri or "http://localhost:8005/api/v1/medical-records/epic-fhir/callback"
                }
                
                # Add client secret if provided
                if self.config.client_secret:
                    token_data["client_secret"] = self.config.client_secret
                
                response = await client.post(
                    f"{self.config.oauth_url}/token",
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")
                
                token_response = response.json()
                
                # Extract patient information from token response
                patient_id = token_response.get("patient")
                encounter_id = token_response.get("encounter")
                user_id = token_response.get("user")
                
                logger.info(f"Token response includes - Patient: {patient_id}, Encounter: {encounter_id}, User: {user_id}")
                
                # Store the token with patient context
                self.epic_token = EpicFHIRToken(
                    access_token=token_response["access_token"],
                    token_type=token_response.get("token_type", "Bearer"),
                    expires_in=token_response.get("expires_in"),
                    refresh_token=token_response.get("refresh_token"),
                    scope=token_response.get("scope"),
                    patient_id=patient_id,
                    encounter_id=encounter_id,
                    user_id=user_id
                )
                
                if self.epic_token.expires_in:
                    self.epic_token.expires_at = datetime.utcnow() + timedelta(
                        seconds=self.epic_token.expires_in
                    )
                
                logger.info("Epic FHIR authorization code exchange successful")
                
                # If we have a patient ID from the token response, fetch patient details
                if patient_id:
                    try:
                        patient_info = await self.get_patient_info(patient_id)
                        logger.info(f"Fetched patient info: {patient_info.get('name', 'Unknown')}")
                        token_response["patient_info"] = patient_info
                    except Exception as e:
                        logger.warning(f"Failed to fetch patient info: {e}")
                
                return token_response
                
        except Exception as e:
            logger.error(f"Authorization code exchange error: {e}")
            raise

    async def get_patient_observations_with_auth(
        self,
        patient_name: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get observations for a test patient using OAuth2 authentication."""
        try:
            # Ensure we have a valid token
            if not self.epic_token or self.epic_token.is_expired():
                raise Exception("No valid OAuth2 token available. Please complete authorization flow first.")
            
            patient_id = epic_fhir_config.get_test_patient_id(patient_name)
            if not patient_id:
                raise ValueError(f"Test patient '{patient_name}' not found")

            # Build query parameters
            params = {"patient": patient_id}

            if date_from:
                params["date"] = f"ge{date_from.strftime('%Y-%m-%d')}"

            if date_to:
                if "date" in params:
                    params["date"] += f"&date=le{date_to.strftime('%Y-%m-%d')}"
                else:
                    params["date"] = f"le{date_to.strftime('%Y-%m-%d')}"

            if category:
                params["category"] = category

            # Make authenticated request
            return await self._make_epic_request("GET", "/Observation", params=params)

        except Exception as e:
            logger.error(f"Error getting observations for test patient {patient_name}: {e}")
            raise


class EpicFHIRClientManager:
    """Manager for Epic FHIR clients."""
    
    def __init__(self):
        self.clients: Dict[str, EpicFHIRClient] = {}
        self.logger = logging.getLogger(__name__)
    
    def add_epic_client(
        self, 
        name: str, 
        config: EpicFHIRClientConfig,
        launch_context: Optional[EpicFHIRLaunchContext] = None
    ) -> None:
        """Add an Epic FHIR client."""
        client = EpicFHIRClient(config)
        if launch_context:
            client.launch_context = launch_context
        
        self.clients[name] = client
        self.logger.info(f"Added Epic FHIR client for {name}")
    
    def get_epic_client(self, name: str) -> EpicFHIRClient:
        """Get an Epic FHIR client by name."""
        if name not in self.clients:
            raise Exception(f"Epic FHIR client '{name}' not found")
        return self.clients[name]
    
    async def test_all_connections(self) -> Dict[str, Any]:
        """Test connections for all Epic FHIR clients."""
        results = {}
        for name, client in self.clients.items():
            try:
                results[name] = await client.test_connection()
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        return results


# Global Epic FHIR client manager instance
epic_fhir_client_manager = EpicFHIRClientManager()

def initialize_epic_fhir_clients():
    """Initialize default Epic FHIR clients."""
    try:
        # Create default sandbox client
        sandbox_config = EpicFHIRClientConfig(
            epic_environment=EpicEnvironment.SANDBOX,
            launch_type=EpicFHIRLaunchType.CLIENT_CREDENTIALS,
            enable_smart_on_fhir=True,
            enable_test_patients=True,
            enable_launch_context=True
        )
        
        epic_fhir_client_manager.add_epic_client("epic_sandbox", sandbox_config)
        logger.info("✅ Initialized Epic FHIR sandbox client")
        
        # Create default production client (if credentials are available)
        if epic_fhir_config.client_id and epic_fhir_config.client_secret:
            production_config = EpicFHIRClientConfig(
                epic_environment=EpicEnvironment.PRODUCTION,
                launch_type=EpicFHIRLaunchType.CLIENT_CREDENTIALS,
                enable_smart_on_fhir=True,
                enable_test_patients=False,
                enable_launch_context=True
            )
            
            epic_fhir_client_manager.add_epic_client("epic_production", production_config)
            logger.info("✅ Initialized Epic FHIR production client")
        
    except Exception as e:
        logger.error(f"Failed to initialize Epic FHIR clients: {e}")

# Initialize default clients
initialize_epic_fhir_clients() 