"""
Epic FHIR API

This module provides API endpoints for Epic FHIR integration including:
- Test sandbox connectivity
- Test patient data retrieval
- SMART on FHIR launch
- Connection testing
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from common.utils.logging import get_logger
from ..services.epic_fhir_client import (
    EpicFHIRClient, 
    EpicFHIRClientConfig, 
    EpicFHIRLaunchContext,
    EpicFHIRLaunchType,
    epic_fhir_client_manager
)
from ..config.epic_fhir_config import epic_fhir_config, EpicEnvironment
from ..services.service_integration import service_integration
from ..services.jwt_service import jwk_service

logger = get_logger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/epic-fhir", tags=["Epic FHIR"], dependencies=[])


# Request/Response Models
class EpicFHIRConnectionRequest(BaseModel):
    """Request model for Epic FHIR connection."""
    client_id: str = Field(..., description="Epic FHIR client ID")
    client_secret: str = Field(..., description="Epic FHIR client secret")
    environment: EpicEnvironment = Field(EpicEnvironment.SANDBOX, description="Epic environment")
    scope: str = Field("launch/patient patient/*.read", description="FHIR scope")
    launch_type: EpicFHIRLaunchType = Field(EpicFHIRLaunchType.CLIENT_CREDENTIALS, description="Launch type")


class EpicFHIRLaunchRequest(BaseModel):
    """Request model for SMART on FHIR launch."""
    patient_name: str = Field(..., description="Test patient name (anna, henry, john, omar, kyle)")
    encounter_id: Optional[str] = Field(None, description="Encounter ID")
    user_id: Optional[str] = Field(None, description="User ID")
    app_context: Optional[str] = Field(None, description="App context")
    redirect_uri: str = Field("http://localhost:8080/callback", description="Redirect URI")


class EpicFHIRTestPatientRequest(BaseModel):
    """Request model for test patient data retrieval."""
    patient_name: str = Field(..., description="Test patient name")
    resource_type: Optional[str] = Field(None, description="FHIR resource type")
    date_from: Optional[datetime] = Field(None, description="Start date")
    date_to: Optional[datetime] = Field(None, description="End date")
    category: Optional[str] = Field(None, description="Resource category")


class EpicFHIRConnectionResponse(BaseModel):
    """Response model for Epic FHIR connection."""
    status: str
    environment: str
    fhir_version: Optional[str]
    server_name: Optional[str]
    server_version: Optional[str]
    timestamp: str
    error: Optional[str] = None


class EpicFHIRTestPatientResponse(BaseModel):
    """Response model for test patient data."""
    patient_name: str
    patient_id: str
    resource_type: str
    data: Dict[str, Any]
    timestamp: str


class EpicFHIRLaunchResponse(BaseModel):
    """Response model for SMART on FHIR launch."""
    launch_url: str
    patient_id: str
    state: str
    scope: str
    timestamp: str


class EpicFHIRCallbackRequest(BaseModel):
    """Request model for Epic FHIR OAuth2 callback processing."""
    code: str = Field(..., description="Authorization code from Epic")
    state: str = Field(..., description="State parameter")
    error: Optional[str] = Field(None, description="Error from Epic")
    error_description: Optional[str] = Field(None, description="Error description from Epic")
    patient_name: Optional[str] = Field(None, description="Patient name for data sync")


# API Endpoints
@router.post("/connect", response_model=EpicFHIRConnectionResponse)
async def connect_to_epic_fhir(
    connection_request: EpicFHIRConnectionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Connect to Epic FHIR server."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token, 
            required_permissions=["admin", "ehr_management"]
        )
        
        # Create Epic FHIR client configuration
        config = EpicFHIRClientConfig(
            client_id=connection_request.client_id,
            client_secret=connection_request.client_secret,
            epic_environment=connection_request.environment,
            scope=connection_request.scope,
            launch_type=connection_request.launch_type
        )
        
        # Create Epic FHIR client
        client = EpicFHIRClient(config)
        
        # Test connection
        connection_result = await client.test_connection()
        
        # Add client to manager if connection successful
        if connection_result["status"] == "connected":
            epic_fhir_client_manager.add_epic_client("epic_sandbox", config)
        
        return EpicFHIRConnectionResponse(
            status=connection_result["status"],
            environment=connection_result["environment"],
            fhir_version=connection_result.get("fhir_version"),
            server_name=connection_result.get("server_name"),
            server_version=connection_result.get("server_version"),
            timestamp=connection_result["timestamp"],
            error=connection_result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Epic FHIR connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Epic FHIR connection failed: {str(e)}"
        )


@router.get("/test-connection", response_model=EpicFHIRConnectionResponse)
async def test_epic_fhir_connection(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Test connection to Epic FHIR server."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token, 
            required_permissions=["admin", "ehr_management"]
        )
        
        # Get Epic FHIR client
        client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
        
        # Test connection
        connection_result = await client.test_connection()
        
        return EpicFHIRConnectionResponse(
            status=connection_result["status"],
            environment=connection_result["environment"],
            fhir_version=connection_result.get("fhir_version"),
            server_name=connection_result.get("server_name"),
            server_version=connection_result.get("server_version"),
            timestamp=connection_result["timestamp"],
            error=connection_result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Epic FHIR connection test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Epic FHIR connection test failed: {str(e)}"
        )


@router.get("/test-patients", response_model=List[Dict[str, Any]])
async def get_available_test_patients(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get available test patients from Epic sandbox."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token, 
            required_permissions=["admin", "ehr_management", "patient_read"]
        )
        
        # Return configured test patients
        test_patients = epic_fhir_config.test_patients
        patients = []
        
        for name, patient_id in test_patients.items():
            patients.append({
                "name": name,
                "patient_id": patient_id,
                "full_name": {
                    "camila": "Camila Lopez",
                    "derrick": "Derrick Lin", 
                    "desiree": "Desiree Powell",
                    "elijah": "Elijah Davis",
                    "linda": "Linda Ross",
                    "olivia": "Olivia Roberts"
                }.get(name, name.title())
            })
        
        return patients
        
    except Exception as e:
        logger.error(f"Failed to get test patients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test patients: {str(e)}"
        )


@router.get("/test-patients/{patient_name}", response_model=EpicFHIRTestPatientResponse)
async def get_test_patient(
    patient_name: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific test patient from Epic sandbox."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token, 
            required_permissions=["admin", "ehr_management", "patient_read"]
        )
        
        # Get Epic FHIR client
        client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
        
        # Get test patient
        patient_data = await client.get_test_patient(patient_name)
        
        # Get patient ID
        patient_id = epic_fhir_config.get_test_patient_id(patient_name)
        
        return EpicFHIRTestPatientResponse(
            patient_name=patient_name,
            patient_id=patient_id,
            resource_type="Patient",
            data=patient_data,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get test patient {patient_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test patient {patient_name}: {str(e)}"
        )


@router.get("/test-patients/{patient_name}/observations", response_model=EpicFHIRTestPatientResponse)
async def get_test_patient_observations(
    patient_name: str,
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    category: Optional[str] = Query(None, description="Observation category"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get observations for a test patient."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token, 
            required_permissions=["admin", "ehr_management", "patient_read"]
        )
        
        # Get Epic FHIR client
        client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
        
        # Get test patient observations
        observations = await client.get_test_patient_observations(
            patient_name, date_from, date_to, category
        )
        
        # Get patient ID
        patient_id = epic_fhir_config.get_test_patient_id(patient_name)
        
        return EpicFHIRTestPatientResponse(
            patient_name=patient_name,
            patient_id=patient_id,
            resource_type="Observation",
            data=observations,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get observations for test patient {patient_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get observations for test patient {patient_name}: {str(e)}"
        )

@router.get("/sandbox-test-patients/{patient_name}/observations", response_model=EpicFHIRTestPatientResponse)
async def get_sandbox_test_patient_observations(
    patient_name: str,
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    category: Optional[str] = Query(None, description="Observation category"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get observations for a test patient using sandbox (no authentication required)."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token, 
            required_permissions=["admin", "ehr_management", "patient_read"]
        )
        
        # Get Epic FHIR client
        client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
        
        # Get test patient observations using sandbox method
        observations = await client.get_sandbox_test_patient_observations(
            patient_name, date_from, date_to, category
        )
        
        # Get patient ID
        patient_id = epic_fhir_config.get_test_patient_id(patient_name)
        
        return EpicFHIRTestPatientResponse(
            patient_name=patient_name,
            patient_id=patient_id,
            resource_type="Observation",
            data=observations,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get sandbox observations for test patient {patient_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sandbox observations for test patient {patient_name}: {str(e)}"
        )


@router.get("/test-patients/{patient_name}/diagnostic-reports", response_model=EpicFHIRTestPatientResponse)
async def get_test_patient_diagnostic_reports(
    patient_name: str,
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    category: Optional[str] = Query(None, description="Report category"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get diagnostic reports for a test patient."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token, 
            required_permissions=["admin", "ehr_management", "patient_read"]
        )
        
        # Get Epic FHIR client
        client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
        
        # Get test patient diagnostic reports
        reports = await client.get_test_patient_diagnostic_reports(
            patient_name, date_from, date_to, category
        )
        
        # Get patient ID
        patient_id = epic_fhir_config.get_test_patient_id(patient_name)
        
        return EpicFHIRTestPatientResponse(
            patient_name=patient_name,
            patient_id=patient_id,
            resource_type="DiagnosticReport",
            data=reports,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get diagnostic reports for test patient {patient_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get diagnostic reports for test patient {patient_name}: {str(e)}"
        )


@router.get("/test-patients/{patient_name}/documents", response_model=EpicFHIRTestPatientResponse)
async def get_test_patient_documents(
    patient_name: str,
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    doc_type: Optional[str] = Query(None, description="Document type"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get document references for a test patient."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token, 
            required_permissions=["admin", "ehr_management", "patient_read"]
        )
        
        # Get Epic FHIR client
        client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
        
        # Get test patient documents
        documents = await client.get_test_patient_documents(
            patient_name, date_from, date_to, doc_type
        )
        
        # Get patient ID
        patient_id = epic_fhir_config.get_test_patient_id(patient_name)
        
        return EpicFHIRTestPatientResponse(
            patient_name=patient_name,
            patient_id=patient_id,
            resource_type="DocumentReference",
            data=documents,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get documents for test patient {patient_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents for test patient {patient_name}: {str(e)}"
        )


@router.get("/test-patients/{patient_name}/imaging-studies", response_model=EpicFHIRTestPatientResponse)
async def get_test_patient_imaging_studies(
    patient_name: str,
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    modality: Optional[str] = Query(None, description="Imaging modality"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get imaging studies for a test patient."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token, 
            required_permissions=["admin", "ehr_management", "patient_read"]
        )
        
        # Get Epic FHIR client
        client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
        
        # Get test patient imaging studies
        studies = await client.get_test_patient_imaging_studies(
            patient_name, date_from, date_to, modality
        )
        
        # Get patient ID
        patient_id = epic_fhir_config.get_test_patient_id(patient_name)
        
        return EpicFHIRTestPatientResponse(
            patient_name=patient_name,
            patient_id=patient_id,
            resource_type="ImagingStudy",
            data=studies,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get imaging studies for test patient {patient_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get imaging studies for test patient {patient_name}: {str(e)}"
        )


@router.post("/launch", response_model=EpicFHIRLaunchResponse)
async def create_smart_on_fhir_launch(
    launch_request: EpicFHIRLaunchRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a SMART on FHIR launch URL."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token, 
            required_permissions=["admin", "ehr_management"]
        )
        
        # Get patient ID
        patient_id = epic_fhir_config.get_test_patient_id(launch_request.patient_name)
        if not patient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Test patient '{launch_request.patient_name}' not found"
            )
        
        # Get Epic FHIR client
        client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
        
        # Create launch context
        launch_context = EpicFHIRLaunchContext(
            launch_type=EpicFHIRLaunchType.SMART_ON_FHIR,
            patient_id=patient_id,
            encounter_id=launch_request.encounter_id,
            user_id=launch_request.user_id,
            app_context=launch_request.app_context,
            redirect_uri=launch_request.redirect_uri,
            state="random_state_123",
            scope="launch/patient patient/*.read"
        )
        
        # Generate launch URL
        launch_url = client._generate_authorization_url(launch_context)
        
        return EpicFHIRLaunchResponse(
            launch_url=launch_url,
            patient_id=patient_id,
            state=launch_context.state,
            scope=launch_context.scope,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to create SMART on FHIR launch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create SMART on FHIR launch: {str(e)}"
        )


@router.get("/authorize")
async def authorize_epic_fhir(
    patient_name: Optional[str] = Query(None, description="Patient name for launch context"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Start Epic FHIR OAuth2 authorization code flow with optional patient context."""
    try:
        token = credentials.credentials
        user_info = await service_integration.validate_user_access(
            token,
            required_permissions=["admin", "ehr_management", "patient_read"]
        )

        # Get Epic FHIR client
        client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
        
        # Generate authorization URL for Epic FHIR sandbox with patient context
        auth_url = client.get_authorization_url(patient_name=patient_name)
        
        return {
            "authorization_url": auth_url,
            "client_id": epic_fhir_config.client_id,
            "redirect_uri": epic_fhir_config.redirect_uri,
            "scope": epic_fhir_config.scope,
            "state": "epic_fhir_auth",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to generate authorization URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )

@router.get("/authorize-public")
async def authorize_epic_fhir_public(
    patient_name: Optional[str] = Query(None, description="Patient name for launch context")
):
    """Start Epic FHIR OAuth2 authorization code flow (public endpoint for testing)."""
    try:
        # Get Epic FHIR client
        client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
        
        # Generate authorization URL for Epic FHIR sandbox with patient context
        auth_url = client.get_authorization_url(patient_name=patient_name)
        
        logger.info(f"Generated Epic FHIR authorization URL: {auth_url}")
        
        return {
            "authorization_url": auth_url,
            "client_id": epic_fhir_config.client_id,
            "redirect_uri": epic_fhir_config.redirect_uri,
            "scope": epic_fhir_config.scope,
            "state": "epic_fhir_auth",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to generate authorization URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )

@router.get("/callback")
async def epic_fhir_callback(
    code: str = Query(..., description="Authorization code from Epic"),
    state: str = Query(..., description="State parameter"),
    error: Optional[str] = Query(None, description="Error from Epic"),
    error_description: Optional[str] = Query(None, description="Error description from Epic"),
    patient_name: Optional[str] = Query(None, description="Patient name for data sync")
):
    """Handle Epic FHIR OAuth2 callback with authorization code and data sync."""
    try:
        if error:
            logger.error(f"Epic FHIR OAuth2 error: {error} - {error_description}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Epic FHIR OAuth2 error: {error} - {error_description}"
            )

        logger.info(f"Epic FHIR OAuth2 callback received - Code: {code[:20]}..., State: {state[:20]}...")

        # Get Epic FHIR client
        client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
        
        # Exchange authorization code for access token
        token_response = await client.exchange_authorization_code(code)
        
        logger.info(f"Successfully exchanged authorization code for access token")
        
        # Get database session and handle all database operations
        from sqlalchemy.ext.asyncio import AsyncSession
        from common.database.connection import get_db_manager
        from ..services.epic_fhir_data_service import EpicFHIRDataService
        
        db_manager = get_db_manager()
        async with db_manager.get_async_session() as db:
            data_service = EpicFHIRDataService(db)
            
            try:
                # Get patient information
                patient_id = None
                if patient_name:
                    patient_id = epic_fhir_config.get_test_patient_id(patient_name)
                
                # For now, use a default user ID since we don't have authentication in callback
                # In production, you might want to store the user ID in the state parameter
                default_user_id = UUID("00000000-0000-0000-0000-000000000001")  # Default user ID
                
                # Create connection record
                connection = await data_service.create_connection(
                    user_id=default_user_id,
                    token_response=token_response,
                    patient_id=patient_id,
                    patient_name=patient_name
                )
                
                logger.info(f"Created Epic FHIR connection: {connection.id}")
                
                # Sync patient data if patient is specified
                sync_results = {}
                if patient_name:
                    try:
                        sync_results = await data_service.sync_patient_data(
                            connection_id=connection.id,
                            resource_types=["Observation", "DiagnosticReport", "DocumentReference", "ImagingStudy"]
                        )
                        logger.info(f"Successfully synced data for patient: {patient_name}")
                    except Exception as sync_error:
                        logger.warning(f"Data sync failed but connection created: {sync_error}")
                        sync_results = {"error": str(sync_error)}
                
                success_data = {
                    "status": "success",
                    "message": "Epic FHIR OAuth2 authentication successful and data synced",
                    "connection_id": str(connection.id),
                    "patient_name": patient_name,
                    "patient_id": patient_id,
                    "token_type": token_response.get("token_type"),
                    "expires_in": token_response.get("expires_in"),
                    "scope": token_response.get("scope"),
                    "sync_results": sync_results,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Return JSON response since Epic FHIR will redirect to frontend
                logger.info(f"Epic FHIR OAuth2 completed successfully. Connection created: {connection.id}")
                return success_data
                
                # Return JSON response
                return success_data
                
            except Exception as db_error:
                logger.error(f"Database operation failed: {db_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database operation failed: {str(db_error)}"
                )

    except Exception as e:
        logger.error(f"Failed to handle Epic FHIR callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle Epic FHIR callback: {str(e)}"
        )

@router.post("/process-callback")
async def process_epic_fhir_callback(
    callback_request: EpicFHIRCallbackRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Process Epic FHIR OAuth2 callback from frontend."""
    try:
        if callback_request.error:
            logger.error(f"Epic FHIR OAuth2 error: {callback_request.error} - {callback_request.error_description}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Epic FHIR OAuth2 error: {callback_request.error} - {callback_request.error_description}"
            )

        logger.info(f"Processing Epic FHIR OAuth2 callback - Code: {callback_request.code[:20]}..., State: {callback_request.state[:20]}...")

        # Get Epic FHIR client
        client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
        
        # Exchange authorization code for access token
        token_response = await client.exchange_authorization_code(callback_request.code)
        
        logger.info(f"Successfully exchanged authorization code for access token")
        
        # Extract patient information from token response
        patient_id_from_token = token_response.get("patient")
        patient_info = token_response.get("patient_info")
        
        logger.info(f"Token response patient ID: {patient_id_from_token}")
        if patient_info:
            logger.info(f"Patient info from token: {patient_info.get('name', 'Unknown')}")
        
        # Get database session and handle all database operations
        from sqlalchemy.ext.asyncio import AsyncSession
        from common.database.connection import get_db_manager
        from ..services.epic_fhir_data_service import EpicFHIRDataService
        
        db_manager = get_db_manager()
        async with db_manager.get_async_session() as db:
            data_service = EpicFHIRDataService(db)
            
            try:
                # Get patient information - prioritize token response over request parameter
                patient_id = patient_id_from_token
                patient_name = callback_request.patient_name
                
                # If we have patient info from token but no patient_name in request, try to map it
                if patient_id_from_token and not patient_name:
                    # Try to find the patient name by ID
                    for name, pid in epic_fhir_config.test_patients.items():
                        if pid == patient_id_from_token:
                            patient_name = name
                            logger.info(f"Mapped patient ID {patient_id_from_token} to patient name: {patient_name}")
                            break
                
                # Fallback to request parameter if no patient ID from token
                if not patient_id and callback_request.patient_name:
                    patient_id = epic_fhir_config.get_test_patient_id(callback_request.patient_name)
                
                # Get user ID from authenticated user
                token = credentials.credentials
                user_info = await service_integration.validate_user_access(
                    token,
                    required_permissions=["admin", "ehr_management", "patient_read"]
                )
                
                user_id = user_info.get("id") or user_info.get("user_id")
                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid user information. Please authenticate properly."
                    )
                
                # Create connection record
                connection = await data_service.create_connection(
                    user_id=UUID(user_id),
                    token_response=token_response,
                    patient_id=patient_id,
                    patient_name=patient_name
                )
                
                logger.info(f"Created Epic FHIR connection: {connection.id}")
                
                # Sync patient data if patient is specified
                sync_results = {}
                if patient_name:
                    try:
                        sync_results = await data_service.sync_patient_data(
                            connection_id=connection.id,
                            resource_types=["Observation", "DiagnosticReport", "DocumentReference", "ImagingStudy"]
                        )
                        logger.info(f"Successfully synced data for patient: {patient_name}")
                    except Exception as sync_error:
                        logger.warning(f"Data sync failed but connection created: {sync_error}")
                        sync_results = {"error": str(sync_error)}
                
                success_data = {
                    "status": "success",
                    "message": "Epic FHIR OAuth2 authentication successful and data synced",
                    "connection_id": str(connection.id),
                    "patient_name": patient_name,
                    "patient_id": patient_id,
                    "patient_info": patient_info,
                    "token_type": token_response.get("token_type"),
                    "expires_in": token_response.get("expires_in"),
                    "scope": token_response.get("scope"),
                    "sync_results": sync_results,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                return success_data
                
            except Exception as db_error:
                logger.error(f"Database operation failed: {db_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database operation failed: {str(db_error)}"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process Epic FHIR callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Epic FHIR callback: {str(e)}"
        )

@router.get("/test-patients/{patient_name}/observations-with-auth")
async def get_patient_observations_with_auth(
    patient_name: str,
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    category: Optional[str] = Query(None, description="Observation category"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get observations for a test patient using OAuth2 authentication."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token,
            required_permissions=["admin", "ehr_management", "patient_read"]
        )

        # Get Epic FHIR client
        client = epic_fhir_client_manager.get_epic_client("epic_sandbox")

        # Get patient observations using OAuth2 authentication
        observations = await client.get_patient_observations_with_auth(
            patient_name, date_from, date_to, category
        )

        # Get patient ID
        patient_id = epic_fhir_config.get_test_patient_id(patient_name)

        return EpicFHIRTestPatientResponse(
            patient_name=patient_name,
            patient_id=patient_id,
            resource_type="Observation",
            data=observations,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Failed to get observations for test patient {patient_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get observations for test patient {patient_name}: {str(e)}"
        )


@router.get("/metadata", response_model=Dict[str, Any])
async def get_epic_fhir_metadata(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get Epic FHIR server metadata."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token, 
            required_permissions=["admin", "ehr_management"]
        )
        
        # Get Epic FHIR client
        client = epic_fhir_client_manager.get_epic_client("epic_sandbox")
        
        # Get metadata
        metadata = await client._make_epic_request("GET", "/metadata")
        
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to get Epic FHIR metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Epic FHIR metadata: {str(e)}"
        )


@router.get("/config", response_model=Dict[str, Any])
async def get_epic_fhir_config(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get Epic FHIR configuration."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token, 
            required_permissions=["admin", "ehr_management"]
        )
        
        return {
            "environment": epic_fhir_config.environment.value,
            "base_url": epic_fhir_config.base_url,
            "oauth_url": epic_fhir_config.oauth_url,
            "client_id": epic_fhir_config.client_id,
            "redirect_uri": epic_fhir_config.redirect_uri,
            "fhir_version": epic_fhir_config.fhir_version,
            "test_patients": list(epic_fhir_config.test_patients.keys()),
            "test_mychart_users": list(epic_fhir_config.test_mychart_users.keys()),
            "scopes": epic_fhir_config.scopes,
            "jwk_set_url": jwk_service.get_jwk_set_url(),
            "key_id": jwk_service.key_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get Epic FHIR config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Epic FHIR config: {str(e)}"
        )


@router.get("/.well-known/jwks.json")
async def get_jwk_set():
    """Get JSON Web Key Set for Epic FHIR JWT validation."""
    try:
        jwk_set = jwk_service.get_jwk_set()
        return jwk_set
        
    except Exception as e:
        logger.error(f"Failed to get JWK set: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get JWK set: {str(e)}"
        )


@router.get("/public-key")
async def get_public_key():
    logger.warning("[DEBUG] Entered /epic-fhir/public-key endpoint (open)")
    public_key_pem = jwk_service.get_public_key_pem()
    return {
        "key_id": jwk_service.key_id,
        "public_key": public_key_pem,
        "algorithm": "RS256",
        "key_type": "RSA"
    }


@router.post("/generate-jwt")
async def generate_jwt_for_epic(
    claims: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Generate a JWT token for Epic FHIR authentication."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token, 
            required_permissions=["admin", "ehr_management"]
        )
        
        # Generate JWT
        jwt_token = jwk_service.generate_jwt(claims)
        
        return {
            "jwt": jwt_token,
            "key_id": jwk_service.key_id,
            "algorithm": "RS256",
            "expires_in": 3600,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate JWT: {str(e)}"
        ) 

@router.get("/test-alive")
async def test_alive():
    return {"status": "epic router alive"}

@router.get("/client-info")
async def get_client_info(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get Epic FHIR client information (without secrets)."""
    try:
        token = credentials.credentials
        # Validate user access
        user_info = await service_integration.validate_user_access(
            token, 
            required_permissions=["admin", "ehr_management"]
        )
        
        return {
            "client_id": epic_fhir_config.client_id,
            "environment": epic_fhir_config.environment.value,
            "has_client_secret": bool(epic_fhir_config.client_secret),
            "redirect_uri": epic_fhir_config.redirect_uri,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get client info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client info: {str(e)}"
        ) 

@router.get("/my/observations")
async def get_my_observations(
    category: Optional[str] = Query(None, description="Observation category"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(100, description="Number of records to return"),
    offset: int = Query(0, description="Number of records to skip"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get stored observations for the authenticated user."""
    try:
        token = credentials.credentials
        user_info = await service_integration.validate_user_access(
            token,
            required_permissions=["admin", "ehr_management", "patient_read"]
        )

        # Validate that user_info contains the required fields
        if not user_info:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )
        
        # Extract user_id from user_info (it can be either 'id' or 'user_id')
        user_id = user_info.get("id") or user_info.get("user_id")
        if not user_id:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )

        from sqlalchemy.ext.asyncio import AsyncSession
        from common.database.connection import get_db_manager
        from ..services.epic_fhir_data_service import EpicFHIRDataService
        
        db_manager = get_db_manager()
        async with db_manager.get_async_session() as db:
            data_service = EpicFHIRDataService(db)
            
            observations, total_count = await data_service.get_observations(
                user_id=UUID(user_id),
                category=category,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
                offset=offset
            )
            
            return {
                "observations": [
                    {
                        "id": str(obs.id),
                        "fhir_id": obs.fhir_id,
                        "category": obs.category,
                        "code": obs.code,
                        "code_display": obs.code_display,
                        "value_quantity": obs.value_quantity,
                        "value_unit": obs.value_unit,
                        "value_code": obs.value_code,
                        "value_string": obs.value_string,
                        "effective_datetime": obs.effective_datetime.isoformat() if obs.effective_datetime else None,
                        "issued": obs.issued.isoformat() if obs.issued else None,
                        "status": obs.status,
                        "interpretation": obs.interpretation,
                        "reference_range_low": obs.reference_range_low,
                        "reference_range_high": obs.reference_range_high,
                        "created_at": obs.created_at.isoformat()
                    }
                    for obs in observations
                ],
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get observations for user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get observations: {str(e)}"
        )


@router.get("/my/diagnostic-reports")
async def get_my_diagnostic_reports(
    category: Optional[str] = Query(None, description="Report category"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(100, description="Number of records to return"),
    offset: int = Query(0, description="Number of records to skip"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get stored diagnostic reports for the authenticated user."""
    try:
        token = credentials.credentials
        user_info = await service_integration.validate_user_access(
            token,
            required_permissions=["admin", "ehr_management", "patient_read"]
        )

        # Validate that user_info contains the required fields
        if not user_info:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )
        
        # Extract user_id from user_info (it can be either 'id' or 'user_id')
        user_id = user_info.get("id") or user_info.get("user_id")
        if not user_id:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )

        from sqlalchemy.ext.asyncio import AsyncSession
        from common.database.connection import get_db_manager
        from ..services.epic_fhir_data_service import EpicFHIRDataService
        
        db_manager = get_db_manager()
        async with db_manager.get_async_session() as db:
            data_service = EpicFHIRDataService(db)
            
            reports, total_count = await data_service.get_diagnostic_reports(
                user_id=UUID(user_id),
                category=category,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
                offset=offset
            )
            
            return {
                "diagnostic_reports": [
                    {
                        "id": str(report.id),
                        "fhir_id": report.fhir_id,
                        "category": report.category,
                        "code": report.code,
                        "code_display": report.code_display,
                        "effective_datetime": report.effective_datetime.isoformat() if report.effective_datetime else None,
                        "issued": report.issued.isoformat() if report.issued else None,
                        "status": report.status,
                        "conclusion": report.conclusion,
                        "conclusion_code": report.conclusion_code,
                        "created_at": report.created_at.isoformat()
                    }
                    for report in reports
                ],
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get diagnostic reports for user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get diagnostic reports: {str(e)}"
        )


@router.get("/my/documents")
async def get_my_documents(
    category: Optional[str] = Query(None, description="Document category"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(100, description="Number of records to return"),
    offset: int = Query(0, description="Number of records to skip"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get document references for the authenticated user."""
    try:
        token = credentials.credentials
        user_info = await service_integration.validate_user_access(
            token,
            required_permissions=["admin", "ehr_management", "patient_read"]
        )

        # Validate that user_info contains the required fields
        if not user_info:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )
        
        # Extract user_id from user_info (it can be either 'id' or 'user_id')
        user_id = user_info.get("id") or user_info.get("user_id")
        if not user_id:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )

        from sqlalchemy.ext.asyncio import AsyncSession
        from common.database.connection import get_db_manager
        from ..services.epic_fhir_data_service import EpicFHIRDataService
        
        db_manager = get_db_manager()
        async with db_manager.get_async_session() as db:
            data_service = EpicFHIRDataService(db)
            
            # For now, return empty results as documents sync is not fully implemented
            return {
                "documents": [],
                "total_count": 0,
                "limit": limit,
                "offset": offset,
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get documents for user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents: {str(e)}"
        )


@router.get("/my/imaging-studies")
async def get_my_imaging_studies(
    modality: Optional[str] = Query(None, description="Imaging modality"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(100, description="Number of records to return"),
    offset: int = Query(0, description="Number of records to skip"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get imaging studies for the authenticated user."""
    try:
        token = credentials.credentials
        user_info = await service_integration.validate_user_access(
            token,
            required_permissions=["admin", "ehr_management", "patient_read"]
        )

        # Validate that user_info contains the required fields
        if not user_info:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )
        
        # Extract user_id from user_info (it can be either 'id' or 'user_id')
        user_id = user_info.get("id") or user_info.get("user_id")
        if not user_id:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )

        from sqlalchemy.ext.asyncio import AsyncSession
        from common.database.connection import get_db_manager
        from ..services.epic_fhir_data_service import EpicFHIRDataService
        
        db_manager = get_db_manager()
        async with db_manager.get_async_session() as db:
            data_service = EpicFHIRDataService(db)
            
            # For now, return empty results as imaging studies sync is not fully implemented
            return {
                "imaging_studies": [],
                "total_count": 0,
                "limit": limit,
                "offset": offset,
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get imaging studies for user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get imaging studies: {str(e)}"
        )


@router.get("/my/sync-logs")
async def get_my_sync_logs(
    limit: int = Query(50, description="Number of records to return"),
    offset: int = Query(0, description="Number of records to skip"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get sync logs for the authenticated user."""
    try:
        token = credentials.credentials
        user_info = await service_integration.validate_user_access(
            token,
            required_permissions=["admin", "ehr_management", "patient_read"]
        )

        # Validate that user_info contains the required fields
        if not user_info:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )
        
        # Extract user_id from user_info (it can be either 'id' or 'user_id')
        user_id = user_info.get("id") or user_info.get("user_id")
        if not user_id:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )

        from sqlalchemy.ext.asyncio import AsyncSession
        from common.database.connection import get_db_manager
        from ..services.epic_fhir_data_service import EpicFHIRDataService
        
        db_manager = get_db_manager()
        async with db_manager.get_async_session() as db:
            data_service = EpicFHIRDataService(db)
            
            logs, total_count = await data_service.get_sync_logs(
                user_id=UUID(user_id),
                limit=limit,
                offset=offset
            )
            
            return {
                "sync_logs": [
                    {
                        "id": str(log.id),
                        "sync_type": log.sync_type,
                        "resource_type": log.resource_type,
                        "records_found": log.records_found,
                        "records_synced": log.records_synced,
                        "records_failed": log.records_failed,
                        "started_at": log.started_at.isoformat(),
                        "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                        "status": log.status,
                        "error_message": log.error_message,
                        "created_at": log.created_at.isoformat()
                    }
                    for log in logs
                ],
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sync logs for user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync logs: {str(e)}"
        )


@router.post("/my/sync")
async def sync_my_data(
    resource_types: Optional[List[str]] = Query(None, description="Resource types to sync"),
    date_from: Optional[datetime] = Query(None, description="Start date for incremental sync"),
    date_to: Optional[datetime] = Query(None, description="End date for incremental sync"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Sync Epic FHIR data for the authenticated user."""
    try:
        token = credentials.credentials
        user_info = await service_integration.validate_user_access(
            token,
            required_permissions=["admin", "ehr_management", "patient_read"]
        )

        # Validate that user_info contains the required fields
        if not user_info:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )
        
        # Extract user_id from user_info (it can be either 'id' or 'user_id')
        user_id = user_info.get("id") or user_info.get("user_id")
        if not user_id:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )

        from sqlalchemy.ext.asyncio import AsyncSession
        from common.database.connection import get_db_manager
        from ..services.epic_fhir_data_service import EpicFHIRDataService
        
        db_manager = get_db_manager()
        async with db_manager.get_async_session() as db:
            data_service = EpicFHIRDataService(db)
            
            # Get active connection
            connection = await data_service.get_active_connection(UUID(user_id))
            
            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active Epic FHIR connection found. Please complete OAuth2 flow first."
                )
            
            # Default resource types if not specified
            if not resource_types:
                resource_types = ["Observation", "DiagnosticReport", "DocumentReference", "ImagingStudy"]
            
            # Sync data
            sync_results = await data_service.sync_patient_data(
                connection_id=connection.id,
                resource_types=resource_types,
                date_from=date_from,
                date_to=date_to
            )
            
            return {
                "status": "success",
                "message": "Data sync completed",
                "connection_id": str(connection.id),
                "patient_name": connection.patient_name,
                "patient_id": connection.patient_id,
                "sync_results": sync_results,
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync data for user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync data: {str(e)}"
        )


@router.get("/my/connection")
async def get_my_connection(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get the active Epic FHIR connection for the authenticated user."""
    try:
        token = credentials.credentials
        user_info = await service_integration.validate_user_access(
            token,
            required_permissions=["admin", "ehr_management", "patient_read"]
        )

        # Validate that user_info contains the required fields
        if not user_info:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )
        
        # Extract user_id from user_info (it can be either 'id' or 'user_id')
        user_id = user_info.get("id") or user_info.get("user_id")
        if not user_id:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )

        from sqlalchemy.ext.asyncio import AsyncSession
        from common.database.connection import get_db_manager
        from ..services.epic_fhir_data_service import EpicFHIRDataService
        
        db_manager = get_db_manager()
        async with db_manager.get_async_session() as db:
            data_service = EpicFHIRDataService(db)
            
            connection = await data_service.get_active_connection(UUID(user_id))
            
            if not connection:
                return {
                    "status": "no_connection",
                    "message": "No active Epic FHIR connection found",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return {
                "status": "connected",
                "connection_id": str(connection.id),
                "environment": connection.environment,
                "patient_name": connection.patient_name,
                "patient_id": connection.patient_id,
                "scope": connection.scope,
                "expires_at": connection.expires_at.isoformat() if connection.expires_at else None,
                "last_sync_at": connection.last_sync_at.isoformat() if connection.last_sync_at else None,
                "created_at": connection.created_at.isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get connection for user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get connection: {str(e)}"
        )


@router.delete("/my/connection")
async def disconnect_my_connection(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Disconnect the active Epic FHIR connection for the authenticated user."""
    try:
        token = credentials.credentials
        user_info = await service_integration.validate_user_access(
            token,
            required_permissions=["admin", "ehr_management", "patient_read"]
        )

        # Validate that user_info contains the required fields
        if not user_info:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )
        
        # Extract user_id from user_info (it can be either 'id' or 'user_id')
        user_id = user_info.get("id") or user_info.get("user_id")
        if not user_id:
            logger.error(f"Invalid user_info structure: {user_info}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information. Please authenticate properly."
            )

        from sqlalchemy.ext.asyncio import AsyncSession
        from common.database.connection import get_db_manager
        from ..services.epic_fhir_data_service import EpicFHIRDataService
        
        db_manager = get_db_manager()
        async with db_manager.get_async_session() as db:
            data_service = EpicFHIRDataService(db)
            
            connection = await data_service.get_active_connection(UUID(user_id))
            
            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active Epic FHIR connection found"
                )
            
            success = await data_service.deactivate_connection(connection.id)
            
            if success:
                return {
                    "status": "success",
                    "message": "Epic FHIR connection disconnected",
                    "connection_id": str(connection.id),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to disconnect connection"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect: {str(e)}"
        ) 