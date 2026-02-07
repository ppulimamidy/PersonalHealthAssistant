"""
FHIR Client Service for EHR Integration

This module provides a comprehensive FHIR client for integrating with EHR systems
like Epic, Cerner, and other FHIR-compliant healthcare systems.
"""

import httpx
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlencode
import json
import logging
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field

from common.config.settings import get_settings
from common.utils.logging import get_logger
from common.utils.resilience import CircuitBreaker

logger = get_logger(__name__)
settings = get_settings()


class FHIRResourceType(str, Enum):
    """FHIR resource types supported by the system."""
    PATIENT = "Patient"
    OBSERVATION = "Observation"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    DOCUMENT_REFERENCE = "DocumentReference"
    IMAGING_STUDY = "ImagingStudy"
    MEDICATION_REQUEST = "MedicationRequest"
    PROCEDURE = "Procedure"
    CONDITION = "Condition"
    ALLERGY_INTOLERANCE = "AllergyIntolerance"
    IMMUNIZATION = "Immunization"
    ENCOUNTER = "Encounter"
    PRACTITIONER = "Practitioner"
    ORGANIZATION = "Organization"


class FHIRSearchParamType(str, Enum):
    """FHIR search parameter types."""
    STRING = "string"
    TOKEN = "token"
    DATE = "date"
    NUMBER = "number"
    QUANTITY = "quantity"
    URI = "uri"
    REFERENCE = "reference"


@dataclass
class FHIRSearchParam:
    """FHIR search parameter definition."""
    name: str
    type: FHIRSearchParamType
    value: Union[str, int, float, datetime]
    modifier: Optional[str] = None


class FHIRToken(BaseModel):
    """FHIR OAuth2 token model."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    expires_at: Optional[datetime] = None


class FHIRClientConfig(BaseModel):
    """FHIR client configuration."""
    base_url: str
    client_id: str
    client_secret: str
    scope: str = "launch/patient patient/*.read patient/*.write"
    redirect_uri: Optional[str] = None
    token_endpoint: Optional[str] = None
    authorize_endpoint: Optional[str] = None
    fhir_version: str = "R4"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


class FHIRResource(BaseModel):
    """Base FHIR resource model."""
    resourceType: str
    id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class FHIRPatient(FHIRResource):
    """FHIR Patient resource."""
    resourceType: str = "Patient"
    identifier: Optional[List[Dict[str, Any]]] = None
    active: Optional[bool] = None
    name: Optional[List[Dict[str, Any]]] = None
    telecom: Optional[List[Dict[str, Any]]] = None
    gender: Optional[str] = None
    birthDate: Optional[str] = None
    address: Optional[List[Dict[str, Any]]] = None


class FHIRObservation(FHIRResource):
    """FHIR Observation resource."""
    resourceType: str = "Observation"
    status: Optional[str] = None
    category: Optional[List[Dict[str, Any]]] = None
    code: Optional[Dict[str, Any]] = None
    subject: Optional[Dict[str, Any]] = None
    effectiveDateTime: Optional[str] = None
    issued: Optional[str] = None
    performer: Optional[List[Dict[str, Any]]] = None
    valueQuantity: Optional[Dict[str, Any]] = None
    valueCodeableConcept: Optional[Dict[str, Any]] = None
    valueString: Optional[str] = None
    referenceRange: Optional[List[Dict[str, Any]]] = None
    interpretation: Optional[List[Dict[str, Any]]] = None


class FHIRDiagnosticReport(FHIRResource):
    """FHIR DiagnosticReport resource."""
    resourceType: str = "DiagnosticReport"
    status: Optional[str] = None
    category: Optional[List[Dict[str, Any]]] = None
    code: Optional[Dict[str, Any]] = None
    subject: Optional[Dict[str, Any]] = None
    encounter: Optional[Dict[str, Any]] = None
    effectiveDateTime: Optional[str] = None
    issued: Optional[str] = None
    performer: Optional[List[Dict[str, Any]]] = None
    result: Optional[List[Dict[str, Any]]] = None
    presentedForm: Optional[List[Dict[str, Any]]] = None


class FHIRDocumentReference(FHIRResource):
    """FHIR DocumentReference resource."""
    resourceType: str = "DocumentReference"
    status: Optional[str] = None
    type: Optional[Dict[str, Any]] = None
    category: Optional[List[Dict[str, Any]]] = None
    subject: Optional[Dict[str, Any]] = None
    date: Optional[str] = None
    author: Optional[List[Dict[str, Any]]] = None
    custodian: Optional[Dict[str, Any]] = None
    content: Optional[List[Dict[str, Any]]] = None
    context: Optional[Dict[str, Any]] = None


class FHIRImagingStudy(FHIRResource):
    """FHIR ImagingStudy resource."""
    resourceType: str = "ImagingStudy"
    status: Optional[str] = None
    modality: Optional[List[Dict[str, Any]]] = None
    subject: Optional[Dict[str, Any]] = None
    encounter: Optional[Dict[str, Any]] = None
    started: Optional[str] = None
    procedureCode: Optional[List[Dict[str, Any]]] = None
    location: Optional[Dict[str, Any]] = None
    numberOfSeries: Optional[int] = None
    numberOfInstances: Optional[int] = None
    series: Optional[List[Dict[str, Any]]] = None


class FHIRBundle(BaseModel):
    """FHIR Bundle resource for search results."""
    resourceType: str = "Bundle"
    type: str
    total: Optional[int] = None
    link: Optional[List[Dict[str, Any]]] = None
    entry: Optional[List[Dict[str, Any]]] = None


class FHIRClientError(Exception):
    """Base exception for FHIR client errors."""
    pass


class FHIRAuthenticationError(FHIRClientError):
    """Authentication error."""
    pass


class FHIRResourceNotFoundError(FHIRClientError):
    """Resource not found error."""
    pass


class FHIRValidationError(FHIRClientError):
    """Validation error."""
    pass


class FHIRClient:
    """FHIR client for EHR integration."""
    
    def __init__(self, config: FHIRClientConfig):
        self.config = config
        self.token: Optional[FHIRToken] = None
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
        # self.retry_policy = RetryPolicy(
        #     max_retries=config.max_retries,
        #     base_delay=config.retry_delay
        # )
        
        # Set up endpoints
        if not config.token_endpoint:
            config.token_endpoint = urljoin(config.base_url, "/oauth2/token")
        if not config.authorize_endpoint:
            config.authorize_endpoint = urljoin(config.base_url, "/oauth2/authorize")
    
    async def authenticate(self) -> FHIRToken:
        """Authenticate with the FHIR server using client credentials."""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    self.config.token_endpoint,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        "scope": self.config.scope
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    raise FHIRAuthenticationError(
                        f"Authentication failed: {response.status_code} - {response.text}"
                    )
                
                token_data = response.json()
                self.token = FHIRToken(
                    access_token=token_data["access_token"],
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_in=token_data.get("expires_in"),
                    refresh_token=token_data.get("refresh_token"),
                    scope=token_data.get("scope")
                )
                
                if self.token.expires_in:
                    self.token.expires_at = datetime.utcnow() + timedelta(
                        seconds=self.token.expires_in
                    )
                
                logger.info("FHIR authentication successful")
                return self.token
                
        except Exception as e:
            logger.error(f"FHIR authentication error: {e}")
            raise FHIRAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def _ensure_token(self) -> str:
        """Ensure we have a valid token."""
        if not self.token or (
            self.token.expires_at and 
            datetime.utcnow() >= self.token.expires_at
        ):
            await self.authenticate()
        
        return self.token.access_token
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to the FHIR server."""
        
        @self.circuit_breaker
        async def _request():
            token = await self._ensure_token()
            
            url = urljoin(self.config.base_url, endpoint)
            request_headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/fhir+json",
                "Accept": "application/fhir+json"
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
                
                if response.status_code == 401:
                    # Token expired, try to re-authenticate
                    await self.authenticate()
                    token = await self._ensure_token()
                    request_headers["Authorization"] = f"Bearer {token}"
                    
                    response = await client.request(
                        method=method,
                        url=url,
                        params=params,
                        json=data,
                        headers=request_headers
                    )
                
                if response.status_code == 404:
                    raise FHIRResourceNotFoundError(f"Resource not found: {endpoint}")
                
                if response.status_code >= 400:
                    raise FHIRClientError(
                        f"FHIR request failed: {response.status_code} - {response.text}"
                    )
                
                return response.json()
        
        # TODO: Add retry logic here if needed. For now, just call _request directly.
        return await _request()
    
    async def search_resources(
        self,
        resource_type: FHIRResourceType,
        search_params: Optional[List[FHIRSearchParam]] = None,
        count: Optional[int] = None,
        page_token: Optional[str] = None
    ) -> FHIRBundle:
        """Search for FHIR resources."""
        try:
            endpoint = f"/{resource_type.value}"
            params = {}
            
            if search_params:
                for param in search_params:
                    param_value = param.value
                    if isinstance(param_value, datetime):
                        param_value = param_value.isoformat()
                    
                    param_name = param.name
                    if param.modifier:
                        param_name = f"{param_name}:{param.modifier}"
                    
                    params[param_name] = str(param_value)
            
            if count:
                params["_count"] = count
            
            if page_token:
                params["_getpages"] = page_token
            
            response_data = await self._make_request("GET", endpoint, params=params)
            return FHIRBundle(**response_data)
            
        except Exception as e:
            logger.error(f"Error searching {resource_type.value}: {e}")
            raise
    
    async def get_resource(
        self, 
        resource_type: FHIRResourceType, 
        resource_id: str
    ) -> Dict[str, Any]:
        """Get a specific FHIR resource by ID."""
        try:
            endpoint = f"/{resource_type.value}/{resource_id}"
            return await self._make_request("GET", endpoint)
            
        except Exception as e:
            logger.error(f"Error getting {resource_type.value}/{resource_id}: {e}")
            raise
    
    async def create_resource(
        self, 
        resource_type: FHIRResourceType, 
        resource_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new FHIR resource."""
        try:
            endpoint = f"/{resource_type.value}"
            return await self._make_request("POST", endpoint, data=resource_data)
            
        except Exception as e:
            logger.error(f"Error creating {resource_type.value}: {e}")
            raise
    
    async def update_resource(
        self, 
        resource_type: FHIRResourceType, 
        resource_id: str, 
        resource_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing FHIR resource."""
        try:
            endpoint = f"/{resource_type.value}/{resource_id}"
            return await self._make_request("PUT", endpoint, data=resource_data)
            
        except Exception as e:
            logger.error(f"Error updating {resource_type.value}/{resource_id}: {e}")
            raise
    
    async def delete_resource(
        self, 
        resource_type: FHIRResourceType, 
        resource_id: str
    ) -> bool:
        """Delete a FHIR resource."""
        try:
            endpoint = f"/{resource_type.value}/{resource_id}"
            await self._make_request("DELETE", endpoint)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting {resource_type.value}/{resource_id}: {e}")
            raise
    
    async def get_patient_observations(
        self, 
        patient_id: str, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        category: Optional[str] = None
    ) -> FHIRBundle:
        """Get observations for a specific patient."""
        search_params = [
            FHIRSearchParam("patient", FHIRSearchParamType.REFERENCE, f"Patient/{patient_id}")
        ]
        
        if date_from:
            search_params.append(
                FHIRSearchParam("date", FHIRSearchParamType.DATE, date_from, "ge")
            )
        
        if date_to:
            search_params.append(
                FHIRSearchParam("date", FHIRSearchParamType.DATE, date_to, "le")
            )
        
        if category:
            search_params.append(
                FHIRSearchParam("category", FHIRSearchParamType.TOKEN, category)
            )
        
        return await self.search_resources(
            FHIRResourceType.OBSERVATION,
            search_params=search_params
        )
    
    async def get_patient_diagnostic_reports(
        self, 
        patient_id: str, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        category: Optional[str] = None
    ) -> FHIRBundle:
        """Get diagnostic reports for a specific patient."""
        search_params = [
            FHIRSearchParam("patient", FHIRSearchParamType.REFERENCE, f"Patient/{patient_id}")
        ]
        
        if date_from:
            search_params.append(
                FHIRSearchParam("date", FHIRSearchParamType.DATE, date_from, "ge")
            )
        
        if date_to:
            search_params.append(
                FHIRSearchParam("date", FHIRSearchParamType.DATE, date_to, "le")
            )
        
        if category:
            search_params.append(
                FHIRSearchParam("category", FHIRSearchParamType.TOKEN, category)
            )
        
        return await self.search_resources(
            FHIRResourceType.DIAGNOSTIC_REPORT,
            search_params=search_params
        )
    
    async def get_patient_documents(
        self, 
        patient_id: str, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        type: Optional[str] = None
    ) -> FHIRBundle:
        """Get document references for a specific patient."""
        search_params = [
            FHIRSearchParam("patient", FHIRSearchParamType.REFERENCE, f"Patient/{patient_id}")
        ]
        
        if date_from:
            search_params.append(
                FHIRSearchParam("date", FHIRSearchParamType.DATE, date_from, "ge")
            )
        
        if date_to:
            search_params.append(
                FHIRSearchParam("date", FHIRSearchParamType.DATE, date_to, "le")
            )
        
        if type:
            search_params.append(
                FHIRSearchParam("type", FHIRSearchParamType.TOKEN, type)
            )
        
        return await self.search_resources(
            FHIRResourceType.DOCUMENT_REFERENCE,
            search_params=search_params
        )
    
    async def get_patient_imaging_studies(
        self, 
        patient_id: str, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        modality: Optional[str] = None
    ) -> FHIRBundle:
        """Get imaging studies for a specific patient."""
        search_params = [
            FHIRSearchParam("patient", FHIRSearchParamType.REFERENCE, f"Patient/{patient_id}")
        ]
        
        if date_from:
            search_params.append(
                FHIRSearchParam("date", FHIRSearchParamType.DATE, date_from, "ge")
            )
        
        if date_to:
            search_params.append(
                FHIRSearchParam("date", FHIRSearchParamType.DATE, date_to, "le")
            )
        
        if modality:
            search_params.append(
                FHIRSearchParam("modality", FHIRSearchParamType.TOKEN, modality)
            )
        
        return await self.search_resources(
            FHIRResourceType.IMAGING_STUDY,
            search_params=search_params
        )
    
    async def sync_patient_data(
        self, 
        patient_id: str, 
        last_sync: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Sync all patient data since last sync."""
        try:
            sync_results = {
                "patient_id": patient_id,
                "sync_timestamp": datetime.utcnow().isoformat(),
                "resources": {}
            }
            
            # Get observations
            observations = await self.get_patient_observations(
                patient_id, 
                date_from=last_sync
            )
            sync_results["resources"]["observations"] = {
                "count": observations.total or 0,
                "bundle": observations.dict()
            }
            
            # Get diagnostic reports
            diagnostic_reports = await self.get_patient_diagnostic_reports(
                patient_id, 
                date_from=last_sync
            )
            sync_results["resources"]["diagnostic_reports"] = {
                "count": diagnostic_reports.total or 0,
                "bundle": diagnostic_reports.dict()
            }
            
            # Get document references
            documents = await self.get_patient_documents(
                patient_id, 
                date_from=last_sync
            )
            sync_results["resources"]["documents"] = {
                "count": documents.total or 0,
                "bundle": documents.dict()
            }
            
            # Get imaging studies
            imaging_studies = await self.get_patient_imaging_studies(
                patient_id, 
                date_from=last_sync
            )
            sync_results["resources"]["imaging_studies"] = {
                "count": imaging_studies.total or 0,
                "bundle": imaging_studies.dict()
            }
            
            logger.info(f"Sync completed for patient {patient_id}: {sync_results}")
            return sync_results
            
        except Exception as e:
            logger.error(f"Error syncing patient {patient_id}: {e}")
            raise


class FHIRClientManager:
    """Manager for multiple FHIR clients (different EHR systems)."""
    
    def __init__(self):
        self.clients: Dict[str, FHIRClient] = {}
        self.logger = logging.getLogger(__name__)
    
    def add_client(self, name: str, config: FHIRClientConfig) -> None:
        """Add a FHIR client for a specific EHR system."""
        self.clients[name] = FHIRClient(config)
        self.logger.info(f"Added FHIR client for {name}")
    
    def get_client(self, name: str) -> FHIRClient:
        """Get a FHIR client by name."""
        if name not in self.clients:
            raise FHIRClientError(f"FHIR client '{name}' not found")
        return self.clients[name]
    
    async def sync_all_patients(
        self, 
        patient_ids: List[str], 
        ehr_system: str,
        last_sync: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Sync data for multiple patients from a specific EHR system."""
        try:
            client = self.get_client(ehr_system)
            sync_results = {
                "ehr_system": ehr_system,
                "sync_timestamp": datetime.utcnow().isoformat(),
                "patients": {}
            }
            
            for patient_id in patient_ids:
                try:
                    patient_sync = await client.sync_patient_data(patient_id, last_sync)
                    sync_results["patients"][patient_id] = patient_sync
                except Exception as e:
                    self.logger.error(f"Error syncing patient {patient_id}: {e}")
                    sync_results["patients"][patient_id] = {"error": str(e)}
            
            return sync_results
            
        except Exception as e:
            self.logger.error(f"Error in bulk sync: {e}")
            raise


# Global FHIR client manager instance
fhir_client_manager = FHIRClientManager() 