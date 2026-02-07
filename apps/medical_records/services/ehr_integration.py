"""
EHR Integration Service

This module provides comprehensive EHR integration capabilities including:
- FHIR client management for modern EHR systems
- HL7 message parsing for legacy systems
- Data synchronization and ingestion
- Patient data correlation
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from uuid import UUID
import json

from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from common.utils.logging import get_logger
from common.database.connection import get_db_session
from .fhir_client import FHIRClient, FHIRClientConfig, FHIRClientManager, FHIRResourceType
from .hl7_parser import HL7Parser, HL7ToFHIRConverter, HL7Message
from .data_service import DataService

logger = get_logger(__name__)


class EHRSystemType(str, Enum):
    """Supported EHR system types."""
    EPIC = "epic"
    CERNER = "cerner"
    ATHENA = "athena"
    MEDITECH = "meditech"
    ALLSCRIPTS = "allscripts"
    CUSTOM = "custom"


class IntegrationStatus(str, Enum):
    """Integration status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONFIGURING = "configuring"


class SyncSchedule(str, Enum):
    """Sync schedule types."""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"


class EHRIntegrationConfig(BaseModel):
    """EHR integration configuration."""
    system_name: str
    system_type: EHRSystemType
    fhir_base_url: str
    fhir_client_id: str
    fhir_client_secret: str
    fhir_scope: str = "launch/patient patient/*.read patient/*.write"
    hl7_endpoint: Optional[str] = None
    sync_schedule: SyncSchedule = SyncSchedule.DAILY
    sync_interval_minutes: int = 1440  # 24 hours
    last_sync: Optional[datetime] = None
    status: IntegrationStatus = IntegrationStatus.INACTIVE
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PatientMapping(BaseModel):
    """Patient mapping between EHR and internal system."""
    internal_patient_id: UUID
    ehr_patient_id: str
    ehr_system: str
    mapping_type: str = "primary"  # primary, secondary, historical
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DataIngestionResult(BaseModel):
    """Result of data ingestion operation."""
    operation_id: str
    ehr_system: str
    patient_id: str
    resource_type: str
    resource_count: int
    success_count: int
    error_count: int
    errors: List[str] = Field(default_factory=list)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EHRIntegrationService:
    """EHR integration service for data ingestion."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fhir_manager = FHIRClientManager()
        self.hl7_parser = HL7Parser()
        self.hl7_converter = HL7ToFHIRConverter()
        self.data_service = DataService()
        self.integrations: Dict[str, EHRIntegrationConfig] = {}
        
    def add_ehr_integration(self, config: EHRIntegrationConfig) -> None:
        """Add an EHR integration configuration."""
        try:
            # Create FHIR client configuration
            fhir_config = FHIRClientConfig(
                base_url=config.fhir_base_url,
                client_id=config.fhir_client_id,
                client_secret=config.fhir_client_secret,
                scope=config.fhir_scope
            )
            
            # Add to FHIR client manager
            self.fhir_manager.add_client(config.system_name, fhir_config)
            
            # Store integration config
            self.integrations[config.system_name] = config
            
            self.logger.info(f"Added EHR integration for {config.system_name}")
            
        except Exception as e:
            self.logger.error(f"Error adding EHR integration: {e}")
            raise
    
    async def test_ehr_connection(self, system_name: str) -> Dict[str, Any]:
        """Test connection to an EHR system."""
        try:
            config = self.integrations.get(system_name)
            if not config:
                raise ValueError(f"EHR integration '{system_name}' not found")
            
            client = self.fhir_manager.get_client(system_name)
            
            # Test authentication
            token = await client.authenticate()
            
            # Test basic FHIR operation (get server metadata)
            metadata = await client._make_request("GET", "/metadata")
            
            return {
                "system_name": system_name,
                "status": "connected",
                "fhir_version": metadata.get("fhirVersion"),
                "server_name": metadata.get("software", {}).get("name"),
                "tested_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error testing EHR connection: {e}")
            return {
                "system_name": system_name,
                "status": "error",
                "error": str(e),
                "tested_at": datetime.utcnow().isoformat()
            }
    
    async def sync_patient_data(
        self, 
        system_name: str, 
        patient_id: str,
        last_sync: Optional[datetime] = None
    ) -> DataIngestionResult:
        """Sync patient data from EHR system."""
        try:
            config = self.integrations.get(system_name)
            if not config:
                raise ValueError(f"EHR integration '{system_name}' not found")
            
            client = self.fhir_manager.get_client(system_name)
            operation_id = f"sync_{system_name}_{patient_id}_{datetime.utcnow().timestamp()}"
            
            result = DataIngestionResult(
                operation_id=operation_id,
                ehr_system=system_name,
                patient_id=patient_id,
                resource_type="mixed",
                resource_count=0,
                success_count=0,
                error_count=0
            )
            
            # Sync different resource types
            resource_types = [
                (FHIRResourceType.OBSERVATION, "observations"),
                (FHIRResourceType.DIAGNOSTIC_REPORT, "diagnostic_reports"),
                (FHIRResourceType.DOCUMENT_REFERENCE, "documents"),
                (FHIRResourceType.IMAGING_STUDY, "imaging_studies")
            ]
            
            for resource_type, resource_name in resource_types:
                try:
                    # Search for resources
                    search_params = [
                        FHIRSearchParam("patient", FHIRSearchParamType.REFERENCE, f"Patient/{patient_id}")
                    ]
                    
                    if last_sync:
                        search_params.append(
                            FHIRSearchParam("_lastUpdated", FHIRSearchParamType.DATE, last_sync, "gt")
                        )
                    
                    bundle = await client.search_resources(resource_type, search_params)
                    
                    if bundle.get("entry"):
                        result.resource_count += len(bundle["entry"])
                        
                        # Process each resource
                        for entry in bundle["entry"]:
                            try:
                                resource = entry.get("resource", {})
                                await self._process_fhir_resource(resource, system_name, patient_id)
                                result.success_count += 1
                            except Exception as e:
                                result.error_count += 1
                                result.errors.append(f"Error processing {resource_name}: {str(e)}")
                    
                except Exception as e:
                    result.error_count += 1
                    result.errors.append(f"Error syncing {resource_name}: {str(e)}")
            
            # Update last sync timestamp
            config.last_sync = datetime.utcnow()
            
            self.logger.info(f"Sync completed for patient {patient_id}: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error syncing patient data: {e}")
            raise
    
    async def process_hl7_message(
        self, 
        system_name: str, 
        raw_message: str
    ) -> DataIngestionResult:
        """Process an HL7 message from legacy EHR systems."""
        try:
            config = self.integrations.get(system_name)
            if not config:
                raise ValueError(f"EHR integration '{system_name}' not found")
            
            operation_id = f"hl7_{system_name}_{datetime.utcnow().timestamp()}"
            
            result = DataIngestionResult(
                operation_id=operation_id,
                ehr_system=system_name,
                patient_id="unknown",
                resource_type="hl7",
                resource_count=1,
                success_count=0,
                error_count=0
            )
            
            # Parse HL7 message
            hl7_message = self.hl7_parser.parse_message(raw_message)
            
            # Convert to FHIR
            fhir_bundle = self.hl7_converter.convert_message(hl7_message)
            
            if fhir_bundle.get("entry"):
                result.resource_count = len(fhir_bundle["entry"])
                
                # Extract patient ID
                for entry in fhir_bundle["entry"]:
                    resource = entry.get("resource", {})
                    if resource.get("resourceType") == "Patient":
                        result.patient_id = resource.get("id", "unknown")
                        break
                
                # Process each FHIR resource
                for entry in fhir_bundle["entry"]:
                    try:
                        resource = entry.get("resource", {})
                        await self._process_fhir_resource(resource, system_name, result.patient_id)
                        result.success_count += 1
                    except Exception as e:
                        result.error_count += 1
                        result.errors.append(f"Error processing FHIR resource: {str(e)}")
            
            self.logger.info(f"HL7 message processed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing HL7 message: {e}")
            raise
    
    async def _process_fhir_resource(
        self, 
        resource: Dict[str, Any], 
        system_name: str, 
        patient_id: str
    ) -> None:
        """Process a single FHIR resource and store it."""
        try:
            resource_type = resource.get("resourceType")
            
            if resource_type == "Observation":
                await self._process_observation(resource, system_name, patient_id)
            elif resource_type == "DiagnosticReport":
                await self._process_diagnostic_report(resource, system_name, patient_id)
            elif resource_type == "DocumentReference":
                await self._process_document_reference(resource, system_name, patient_id)
            elif resource_type == "ImagingStudy":
                await self._process_imaging_study(resource, system_name, patient_id)
            elif resource_type == "Patient":
                await self._process_patient(resource, system_name)
            else:
                self.logger.warning(f"Unsupported resource type: {resource_type}")
                
        except Exception as e:
            self.logger.error(f"Error processing FHIR resource: {e}")
            raise
    
    async def _process_observation(
        self, 
        resource: Dict[str, Any], 
        system_name: str, 
        patient_id: str
    ) -> None:
        """Process FHIR Observation resource."""
        try:
            # Extract observation data
            code = resource.get("code", {})
            coding = code.get("coding", [{}])[0] if code.get("coding") else {}
            
            value_quantity = resource.get("valueQuantity", {})
            
            observation_data = {
                "patient_id": patient_id,
                "test_name": code.get("text", ""),
                "test_code": coding.get("code", ""),
                "value": value_quantity.get("value"),
                "unit": value_quantity.get("unit"),
                "reference_range_low": None,
                "reference_range_high": None,
                "abnormal": False,
                "critical": False,
                "test_date": resource.get("effectiveDateTime"),
                "result_date": resource.get("issued"),
                "status": resource.get("status", "unknown"),
                "source": system_name,
                "external_id": resource.get("id"),
                "fhir_resource_id": resource.get("id"),
                "record_metadata": {
                    "fhir_resource": resource,
                    "ingested_at": datetime.utcnow().isoformat()
                }
            }
            
            # Process reference ranges
            reference_ranges = resource.get("referenceRange", [])
            if reference_ranges:
                ref_range = reference_ranges[0]
                observation_data["reference_range_low"] = ref_range.get("low", {}).get("value")
                observation_data["reference_range_high"] = ref_range.get("high", {}).get("value")
            
            # Store in database
            async with get_db_session() as db:
                await self.data_service.create_lab_result(db, observation_data)
            
        except Exception as e:
            self.logger.error(f"Error processing observation: {e}")
            raise
    
    async def _process_diagnostic_report(
        self, 
        resource: Dict[str, Any], 
        system_name: str, 
        patient_id: str
    ) -> None:
        """Process FHIR DiagnosticReport resource."""
        try:
            # Extract report data
            code = resource.get("code", {})
            coding = code.get("coding", [{}])[0] if code.get("coding") else {}
            
            report_data = {
                "patient_id": patient_id,
                "title": code.get("text", ""),
                "report_type": "diagnostic_report",
                "category": "laboratory",
                "content": f"Diagnostic report from {system_name}",
                "summary": f"Report for {code.get('text', '')}",
                "status": resource.get("status", "unknown"),
                "priority": "normal",
                "effective_date": resource.get("effectiveDateTime"),
                "source": system_name,
                "external_id": resource.get("id"),
                "fhir_resource_id": resource.get("id"),
                "report_metadata": {
                    "fhir_resource": resource,
                    "ingested_at": datetime.utcnow().isoformat()
                }
            }
            
            # Store in database
            async with get_db_session() as db:
                await self.data_service.create_clinical_report(db, report_data)
            
        except Exception as e:
            self.logger.error(f"Error processing diagnostic report: {e}")
            raise
    
    async def _process_document_reference(
        self, 
        resource: Dict[str, Any], 
        system_name: str, 
        patient_id: str
    ) -> None:
        """Process FHIR DocumentReference resource."""
        try:
            # Extract document data
            doc_type = resource.get("type", {})
            coding = doc_type.get("coding", [{}])[0] if doc_type.get("coding") else {}
            
            document_data = {
                "patient_id": patient_id,
                "document_type": "clinical_document",
                "title": coding.get("display", "Clinical Document"),
                "content": f"Document from {system_name}",
                "source": system_name,
                "external_id": resource.get("id"),
                "fhir_resource_id": resource.get("id"),
                "document_metadata": {
                    "fhir_resource": resource,
                    "ingested_at": datetime.utcnow().isoformat()
                }
            }
            
            # Store in database
            async with get_db_session() as db:
                await self.data_service.create_document(db, document_data)
            
        except Exception as e:
            self.logger.error(f"Error processing document reference: {e}")
            raise
    
    async def _process_imaging_study(
        self, 
        resource: Dict[str, Any], 
        system_name: str, 
        patient_id: str
    ) -> None:
        """Process FHIR ImagingStudy resource."""
        try:
            # Extract imaging study data
            modalities = resource.get("modality", [])
            modality_text = ", ".join([m.get("display", "") for m in modalities]) if modalities else "Unknown"
            
            imaging_data = {
                "patient_id": patient_id,
                "modality": modality_text,
                "body_part": "Unknown",
                "study_date": resource.get("started"),
                "description": f"Imaging study from {system_name}",
                "source": system_name,
                "external_id": resource.get("id"),
                "fhir_resource_id": resource.get("id"),
                "imaging_metadata": {
                    "fhir_resource": resource,
                    "ingested_at": datetime.utcnow().isoformat()
                }
            }
            
            # Store in database
            async with get_db_session() as db:
                await self.data_service.create_imaging_study(db, imaging_data)
            
        except Exception as e:
            self.logger.error(f"Error processing imaging study: {e}")
            raise
    
    async def _process_patient(
        self, 
        resource: Dict[str, Any], 
        system_name: str
    ) -> None:
        """Process FHIR Patient resource."""
        try:
            # Extract patient data
            patient_id = resource.get("id")
            names = resource.get("name", [{}])
            name = names[0] if names else {}
            
            patient_data = {
                "ehr_patient_id": patient_id,
                "ehr_system": system_name,
                "first_name": name.get("given", [""])[0] if name.get("given") else "",
                "last_name": name.get("family", ""),
                "gender": resource.get("gender", "unknown"),
                "birth_date": resource.get("birthDate"),
                "metadata": {
                    "fhir_resource": resource,
                    "ingested_at": datetime.utcnow().isoformat()
                }
            }
            
            # Store patient mapping
            # TODO: Implement patient mapping storage
            
        except Exception as e:
            self.logger.error(f"Error processing patient: {e}")
            raise
    
    async def get_integration_status(self, system_name: str) -> Dict[str, Any]:
        """Get integration status for an EHR system."""
        try:
            config = self.integrations.get(system_name)
            if not config:
                return {"status": "not_found"}
            
            # Test connection
            connection_test = await self.test_ehr_connection(system_name)
            
            return {
                "system_name": system_name,
                "system_type": config.system_type,
                "status": config.status,
                "sync_schedule": config.sync_schedule,
                "last_sync": config.last_sync.isoformat() if config.last_sync else None,
                "connection_status": connection_test.get("status"),
                "fhir_version": connection_test.get("fhir_version"),
                "server_name": connection_test.get("server_name")
            }
            
        except Exception as e:
            self.logger.error(f"Error getting integration status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def list_integrations(self) -> List[Dict[str, Any]]:
        """List all configured EHR integrations."""
        try:
            integrations = []
            for system_name, config in self.integrations.items():
                status = await self.get_integration_status(system_name)
                integrations.append(status)
            
            return integrations
            
        except Exception as e:
            self.logger.error(f"Error listing integrations: {e}")
            raise


# Global EHR integration service instance
ehr_integration_service = EHRIntegrationService() 