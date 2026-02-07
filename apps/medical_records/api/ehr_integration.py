"""
EHR Integration API

This module provides API endpoints for EHR integration including:
- FHIR client management
- HL7 message processing
- Data synchronization
- Integration status monitoring
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

from common.utils.logging import get_logger
from common.middleware.auth import validate_user_access
from ..services.ehr_integration import (
    EHRIntegrationService, 
    EHRIntegrationConfig, 
    EHRSystemType, 
    SyncSchedule,
    IntegrationStatus,
    DataIngestionResult
)
from ..services.service_integration import service_integration

logger = get_logger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/ehr-integration", tags=["EHR Integration"])

# Global service instance
ehr_service = EHRIntegrationService()


# Request/Response Models
class EHRIntegrationCreate(BaseModel):
    """Request model for creating EHR integration."""
    system_name: str = Field(..., description="Name of the EHR system")
    system_type: EHRSystemType = Field(..., description="Type of EHR system")
    fhir_base_url: str = Field(..., description="FHIR base URL")
    fhir_client_id: str = Field(..., description="FHIR client ID")
    fhir_client_secret: str = Field(..., description="FHIR client secret")
    fhir_scope: str = Field("launch/patient patient/*.read patient/*.write", description="FHIR scope")
    hl7_endpoint: Optional[str] = Field(None, description="HL7 endpoint URL")
    sync_schedule: SyncSchedule = Field(SyncSchedule.DAILY, description="Sync schedule")
    sync_interval_minutes: int = Field(1440, description="Sync interval in minutes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class EHRIntegrationUpdate(BaseModel):
    """Request model for updating EHR integration."""
    fhir_base_url: Optional[str] = Field(None, description="FHIR base URL")
    fhir_client_id: Optional[str] = Field(None, description="FHIR client ID")
    fhir_client_secret: Optional[str] = Field(None, description="FHIR client secret")
    fhir_scope: Optional[str] = Field(None, description="FHIR scope")
    hl7_endpoint: Optional[str] = Field(None, description="HL7 endpoint URL")
    sync_schedule: Optional[SyncSchedule] = Field(None, description="Sync schedule")
    sync_interval_minutes: Optional[int] = Field(None, description="Sync interval in minutes")
    status: Optional[IntegrationStatus] = Field(None, description="Integration status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PatientSyncRequest(BaseModel):
    """Request model for patient data sync."""
    patient_id: str = Field(..., description="Patient ID")
    last_sync: Optional[datetime] = Field(None, description="Last sync timestamp")
    resource_types: Optional[List[str]] = Field(None, description="Specific resource types to sync")


class HL7MessageRequest(BaseModel):
    """Request model for HL7 message processing."""
    raw_message: str = Field(..., description="Raw HL7 message")
    system_name: str = Field(..., description="EHR system name")


class EHRIntegrationResponse(BaseModel):
    """Response model for EHR integration."""
    system_name: str
    system_type: EHRSystemType
    status: IntegrationStatus
    sync_schedule: SyncSchedule
    last_sync: Optional[datetime]
    connection_status: str
    fhir_version: Optional[str]
    server_name: Optional[str]
    created_at: datetime
    updated_at: datetime


class SyncResultResponse(BaseModel):
    """Response model for sync operations."""
    operation_id: str
    ehr_system: str
    patient_id: str
    resource_type: str
    resource_count: int
    success_count: int
    error_count: int
    errors: List[str]
    ingested_at: datetime
    metadata: Dict[str, Any]


# API Endpoints
@router.post("/integrations", response_model=EHRIntegrationResponse)
async def create_ehr_integration(
    integration: EHRIntegrationCreate,
    credentials: str = Depends(security)
):
    """Create a new EHR integration."""
    try:
        # Validate user access
        user_info = await service_integration.validate_user_access(
            credentials, 
            required_permissions=["admin", "ehr_management"]
        )
        
        # Create integration config
        config = EHRIntegrationConfig(
            system_name=integration.system_name,
            system_type=integration.system_type,
            fhir_base_url=integration.fhir_base_url,
            fhir_client_id=integration.fhir_client_id,
            fhir_client_secret=integration.fhir_client_secret,
            fhir_scope=integration.fhir_scope,
            hl7_endpoint=integration.hl7_endpoint,
            sync_schedule=integration.sync_schedule,
            sync_interval_minutes=integration.sync_interval_minutes,
            metadata=integration.metadata
        )
        
        # Add integration
        ehr_service.add_ehr_integration(config)
        
        # Get integration status
        status_info = await ehr_service.get_integration_status(integration.system_name)
        
        return EHRIntegrationResponse(
            system_name=integration.system_name,
            system_type=integration.system_type,
            status=config.status,
            sync_schedule=config.sync_schedule,
            last_sync=config.last_sync,
            connection_status=status_info.get("connection_status", "unknown"),
            fhir_version=status_info.get("fhir_version"),
            server_name=status_info.get("server_name"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error creating EHR integration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create EHR integration: {str(e)}"
        )


@router.get("/integrations", response_model=List[EHRIntegrationResponse])
async def list_ehr_integrations(
    credentials: str = Depends(security)
):
    """List all EHR integrations."""
    try:
        # Validate user access
        user_info = await service_integration.validate_user_access(
            credentials, 
            required_permissions=["admin", "ehr_management", "ehr_read"]
        )
        
        # Get integrations
        integrations = await ehr_service.list_integrations()
        
        return [
            EHRIntegrationResponse(
                system_name=integration["system_name"],
                system_type=integration["system_type"],
                status=integration["status"],
                sync_schedule=integration["sync_schedule"],
                last_sync=datetime.fromisoformat(integration["last_sync"]) if integration.get("last_sync") else None,
                connection_status=integration.get("connection_status", "unknown"),
                fhir_version=integration.get("fhir_version"),
                server_name=integration.get("server_name"),
                created_at=datetime.utcnow(),  # TODO: Get from database
                updated_at=datetime.utcnow()   # TODO: Get from database
            )
            for integration in integrations
        ]
        
    except Exception as e:
        logger.error(f"Error listing EHR integrations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list EHR integrations: {str(e)}"
        )


@router.get("/integrations/{system_name}", response_model=EHRIntegrationResponse)
async def get_ehr_integration(
    system_name: str,
    credentials: str = Depends(security)
):
    """Get EHR integration details."""
    try:
        # Validate user access
        user_info = await service_integration.validate_user_access(
            credentials, 
            required_permissions=["admin", "ehr_management", "ehr_read"]
        )
        
        # Get integration status
        status_info = await ehr_service.get_integration_status(system_name)
        
        if status_info.get("status") == "not_found":
            raise HTTPException(
                status_code=404,
                detail=f"EHR integration '{system_name}' not found"
            )
        
        return EHRIntegrationResponse(
            system_name=system_name,
            system_type=status_info.get("system_type"),
            status=status_info.get("status"),
            sync_schedule=status_info.get("sync_schedule"),
            last_sync=datetime.fromisoformat(status_info["last_sync"]) if status_info.get("last_sync") else None,
            connection_status=status_info.get("connection_status", "unknown"),
            fhir_version=status_info.get("fhir_version"),
            server_name=status_info.get("server_name"),
            created_at=datetime.utcnow(),  # TODO: Get from database
            updated_at=datetime.utcnow()   # TODO: Get from database
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting EHR integration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get EHR integration: {str(e)}"
        )


@router.put("/integrations/{system_name}", response_model=EHRIntegrationResponse)
async def update_ehr_integration(
    system_name: str,
    integration_update: EHRIntegrationUpdate,
    credentials: str = Depends(security)
):
    """Update EHR integration configuration."""
    try:
        # Validate user access
        user_info = await service_integration.validate_user_access(
            credentials, 
            required_permissions=["admin", "ehr_management"]
        )
        
        # TODO: Implement update logic
        # For now, return current status
        status_info = await ehr_service.get_integration_status(system_name)
        
        if status_info.get("status") == "not_found":
            raise HTTPException(
                status_code=404,
                detail=f"EHR integration '{system_name}' not found"
            )
        
        return EHRIntegrationResponse(
            system_name=system_name,
            system_type=status_info.get("system_type"),
            status=status_info.get("status"),
            sync_schedule=status_info.get("sync_schedule"),
            last_sync=datetime.fromisoformat(status_info["last_sync"]) if status_info.get("last_sync") else None,
            connection_status=status_info.get("connection_status", "unknown"),
            fhir_version=status_info.get("fhir_version"),
            server_name=status_info.get("server_name"),
            created_at=datetime.utcnow(),  # TODO: Get from database
            updated_at=datetime.utcnow()   # TODO: Get from database
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating EHR integration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update EHR integration: {str(e)}"
        )


@router.delete("/integrations/{system_name}")
async def delete_ehr_integration(
    system_name: str,
    credentials: str = Depends(security)
):
    """Delete EHR integration."""
    try:
        # Validate user access
        user_info = await service_integration.validate_user_access(
            credentials, 
            required_permissions=["admin", "ehr_management"]
        )
        
        # TODO: Implement delete logic
        return {"message": f"EHR integration '{system_name}' deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting EHR integration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete EHR integration: {str(e)}"
        )


@router.post("/integrations/{system_name}/test")
async def test_ehr_connection(
    system_name: str,
    credentials: str = Depends(security)
):
    """Test connection to EHR system."""
    try:
        # Validate user access
        user_info = await service_integration.validate_user_access(
            credentials, 
            required_permissions=["admin", "ehr_management", "ehr_read"]
        )
        
        # Test connection
        result = await ehr_service.test_ehr_connection(system_name)
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing EHR connection: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test EHR connection: {str(e)}"
        )


@router.post("/integrations/{system_name}/sync", response_model=SyncResultResponse)
async def sync_patient_data(
    system_name: str,
    sync_request: PatientSyncRequest,
    background_tasks: BackgroundTasks,
    credentials: str = Depends(security)
):
    """Sync patient data from EHR system."""
    try:
        # Validate user access
        user_info = await service_integration.validate_user_access(
            credentials, 
            required_permissions=["admin", "ehr_management", "data_sync"]
        )
        
        # Perform sync
        result = await ehr_service.sync_patient_data(
            system_name=system_name,
            patient_id=sync_request.patient_id,
            last_sync=sync_request.last_sync
        )
        
        return SyncResultResponse(
            operation_id=result.operation_id,
            ehr_system=result.ehr_system,
            patient_id=result.patient_id,
            resource_type=result.resource_type,
            resource_count=result.resource_count,
            success_count=result.success_count,
            error_count=result.error_count,
            errors=result.errors,
            ingested_at=result.ingested_at,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Error syncing patient data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync patient data: {str(e)}"
        )


@router.post("/integrations/{system_name}/hl7", response_model=SyncResultResponse)
async def process_hl7_message(
    system_name: str,
    hl7_request: HL7MessageRequest,
    credentials: str = Depends(security)
):
    """Process HL7 message from EHR system."""
    try:
        # Validate user access
        user_info = await service_integration.validate_user_access(
            credentials, 
            required_permissions=["admin", "ehr_management", "data_sync"]
        )
        
        # Process HL7 message
        result = await ehr_service.process_hl7_message(
            system_name=system_name,
            raw_message=hl7_request.raw_message
        )
        
        return SyncResultResponse(
            operation_id=result.operation_id,
            ehr_system=result.ehr_system,
            patient_id=result.patient_id,
            resource_type=result.resource_type,
            resource_count=result.resource_count,
            success_count=result.success_count,
            error_count=result.error_count,
            errors=result.errors,
            ingested_at=result.ingested_at,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Error processing HL7 message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process HL7 message: {str(e)}"
        )


@router.get("/integrations/{system_name}/status")
async def get_integration_status(
    system_name: str,
    credentials: str = Depends(security)
):
    """Get detailed integration status."""
    try:
        # Validate user access
        user_info = await service_integration.validate_user_access(
            credentials, 
            required_permissions=["admin", "ehr_management", "ehr_read"]
        )
        
        # Get status
        status_info = await ehr_service.get_integration_status(system_name)
        
        return status_info
        
    except Exception as e:
        logger.error(f"Error getting integration status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get integration status: {str(e)}"
        )


@router.post("/integrations/{system_name}/sync/bulk")
async def bulk_sync_patients(
    system_name: str,
    patient_ids: List[str],
    background_tasks: BackgroundTasks,
    credentials: str = Depends(security)
):
    """Bulk sync multiple patients."""
    try:
        # Validate user access
        user_info = await service_integration.validate_user_access(
            credentials, 
            required_permissions=["admin", "ehr_management", "data_sync"]
        )
        
        # TODO: Implement bulk sync
        results = []
        for patient_id in patient_ids:
            try:
                result = await ehr_service.sync_patient_data(
                    system_name=system_name,
                    patient_id=patient_id
                )
                results.append(result.dict())
            except Exception as e:
                results.append({
                    "patient_id": patient_id,
                    "error": str(e)
                })
        
        return {
            "system_name": system_name,
            "total_patients": len(patient_ids),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in bulk sync: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform bulk sync: {str(e)}"
        ) 