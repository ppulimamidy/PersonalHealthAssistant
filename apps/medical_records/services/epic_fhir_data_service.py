"""
Epic FHIR Data Service

This service handles the synchronization, storage, and retrieval of Epic FHIR data
in the PersonalHealthAssistant application.
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload

from ..models.epic_fhir_data import (
    EpicFHIRConnection,
    EpicFHIRObservation,
    EpicFHIRDiagnosticReport,
    EpicFHIRDocument,
    EpicFHIRImagingStudy,
    EpicFHIRSyncLog
)
from ..services.epic_fhir_client import epic_fhir_client_manager
from ..config.epic_fhir_config import epic_fhir_config

logger = logging.getLogger(__name__)


class EpicFHIRDataService:
    """Service for managing Epic FHIR data synchronization and storage."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_connection(
        self,
        user_id: UUID,
        token_response: Dict[str, Any],
        patient_id: Optional[str] = None,
        patient_name: Optional[str] = None
    ) -> EpicFHIRConnection:
        """Create a new Epic FHIR connection record."""
        try:
            # Deactivate all existing connections for this user
            await self._deactivate_all_user_connections(user_id)
            
            # Calculate expiration time
            expires_at = None
            if token_response.get("expires_in"):
                expires_at = datetime.utcnow() + timedelta(seconds=token_response["expires_in"])
            
            # Map patient ID to patient name if not provided
            if patient_id and not patient_name:
                patient_name = epic_fhir_config.get_test_patient_name(patient_id)
            
            connection = EpicFHIRConnection(
                user_id=user_id,
                client_id=epic_fhir_config.client_id,
                environment=epic_fhir_config.environment.value,
                scope=token_response.get("scope", epic_fhir_config.default_scope),
                access_token=token_response["access_token"],
                token_type=token_response.get("token_type", "Bearer"),
                expires_in=token_response.get("expires_in"),
                expires_at=expires_at,
                refresh_token=token_response.get("refresh_token"),
                patient_id=patient_id,
                patient_name=patient_name,
                is_active=True
            )
            
            self.db.add(connection)
            await self.db.commit()
            await self.db.refresh(connection)
            
            logger.info(f"Created Epic FHIR connection for user {user_id}")
            return connection
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create Epic FHIR connection: {e}")
            raise
    
    async def _deactivate_all_user_connections(self, user_id: UUID) -> None:
        """Deactivate all existing connections for a user."""
        try:
            stmt = select(EpicFHIRConnection).where(
                and_(
                    EpicFHIRConnection.user_id == user_id,
                    EpicFHIRConnection.is_active == True
                )
            )
            result = await self.db.execute(stmt)
            connections = result.scalars().all()
            
            for connection in connections:
                connection.is_active = False
                connection.updated_at = datetime.utcnow()
            
            if connections:
                await self.db.commit()
                logger.info(f"Deactivated {len(connections)} existing connections for user {user_id}")
                
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to deactivate existing connections for user {user_id}: {e}")
            raise
    
    async def get_active_connection(self, user_id: UUID) -> Optional[EpicFHIRConnection]:
        """Get the active Epic FHIR connection for a user."""
        try:
            stmt = select(EpicFHIRConnection).where(
                and_(
                    EpicFHIRConnection.user_id == user_id,
                    EpicFHIRConnection.is_active == True
                )
            ).order_by(desc(EpicFHIRConnection.created_at))
            
            result = await self.db.execute(stmt)
            return result.scalars().first()
            
        except Exception as e:
            logger.error(f"Failed to get active connection for user {user_id}: {e}")
            raise
    
    async def deactivate_connection(self, connection_id: UUID) -> bool:
        """Deactivate an Epic FHIR connection."""
        try:
            stmt = select(EpicFHIRConnection).where(EpicFHIRConnection.id == connection_id)
            result = await self.db.execute(stmt)
            connection = result.scalar_one_or_none()
            
            if connection:
                connection.is_active = False
                connection.updated_at = datetime.utcnow()
                await self.db.commit()
                logger.info(f"Deactivated Epic FHIR connection {connection_id}")
                return True
            
            return False
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to deactivate connection {connection_id}: {e}")
            raise
    
    async def sync_patient_data(
        self,
        connection_id: UUID,
        resource_types: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Synchronize patient data from Epic FHIR."""
        try:
            # Get connection
            stmt = select(EpicFHIRConnection).where(EpicFHIRConnection.id == connection_id)
            result = await self.db.execute(stmt)
            connection = result.scalar_one_or_none()
            
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")
            
            # Default resource types if not specified
            if not resource_types:
                resource_types = ["Observation", "DiagnosticReport", "DocumentReference", "ImagingStudy"]
            
            sync_results = {}
            
            for resource_type in resource_types:
                sync_log = EpicFHIRSyncLog(
                    connection_id=connection_id,
                    sync_type="full" if not date_from else "incremental",
                    resource_type=resource_type,
                    status="running"
                )
                self.db.add(sync_log)
                await self.db.commit()
                await self.db.refresh(sync_log)
                
                try:
                    # Use a simpler approach - make direct HTTP requests to Epic FHIR
                    # This avoids the complex client async context issues
                    
                    # Map patient ID to patient name for better logging
                    patient_name = epic_fhir_config.get_test_patient_name(connection.patient_id)
                    if not patient_name:
                        patient_name = "unknown"
                    
                    logger.info(f"Starting sync for {resource_type} with patient ID: {connection.patient_id}, mapped name: {patient_name}")
                    
                    # Sync data based on resource type
                    if resource_type == "Observation":
                        result = await self._sync_observations_direct(connection, date_from, date_to)
                    elif resource_type == "DiagnosticReport":
                        result = await self._sync_diagnostic_reports_direct(connection, date_from, date_to)
                    elif resource_type == "DocumentReference":
                        result = await self._sync_documents_direct(connection, date_from, date_to)
                    elif resource_type == "ImagingStudy":
                        result = await self._sync_imaging_studies_direct(connection, date_from, date_to)
                    else:
                        result = {"records_found": 0, "records_synced": 0, "records_failed": 0}
                    
                    # Update sync log
                    sync_log.records_found = result["records_found"]
                    sync_log.records_synced = result["records_synced"]
                    sync_log.records_failed = result["records_failed"]
                    sync_log.status = "completed"
                    sync_log.completed_at = datetime.utcnow()
                    
                    sync_results[resource_type] = result
                    
                except Exception as e:
                    sync_log.status = "failed"
                    sync_log.error_message = str(e)
                    sync_log.completed_at = datetime.utcnow()
                    logger.error(f"Failed to sync {resource_type}: {e}")
                    sync_results[resource_type] = {"error": str(e)}
                
                await self.db.commit()
            
            # Update connection last sync time
            connection.last_sync_at = datetime.utcnow()
            await self.db.commit()
            
            return sync_results
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to sync patient data: {e}")
            raise
    
    async def _sync_observations(
        self,
        client,
        connection: EpicFHIRConnection,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Sync observations from Epic FHIR."""
        try:
            # Get observations from Epic FHIR
            observations_data = await client.get_patient_observations_with_auth(
                connection.patient_name or "anna",  # Default to test patient
                date_from=date_from,
                date_to=date_to
            )
            
            records_found = 0
            records_synced = 0
            records_failed = 0
            
            if observations_data.get("entry"):
                records_found = len(observations_data["entry"])
                
                for entry in observations_data["entry"]:
                    try:
                        resource = entry.get("resource", {})
                        fhir_id = resource.get("id")
                        
                        if not fhir_id:
                            continue
                        
                        # Check if observation already exists
                        existing = await self.db.execute(
                            select(EpicFHIRObservation).where(
                                and_(
                                    EpicFHIRObservation.connection_id == connection.id,
                                    EpicFHIRObservation.fhir_id == fhir_id
                                )
                            )
                        )
                        
                        if existing.scalar_one_or_none():
                            continue  # Skip if already exists
                        
                        # Extract observation data
                        observation = EpicFHIRObservation(
                            connection_id=connection.id,
                            fhir_id=fhir_id,
                            category=self._extract_category(resource),
                            code=self._extract_code(resource),
                            code_display=self._extract_code_display(resource),
                            value_quantity=self._extract_value_quantity(resource),
                            value_unit=self._extract_value_unit(resource),
                            value_code=self._extract_value_code(resource),
                            value_string=self._extract_value_string(resource),
                            effective_datetime=self._parse_datetime(resource.get("effectiveDateTime")),
                            issued=self._parse_datetime(resource.get("issued")),
                            status=resource.get("status"),
                            interpretation=self._extract_interpretation(resource),
                            reference_range_low=self._extract_reference_range_low(resource),
                            reference_range_high=self._extract_reference_range_high(resource),
                            raw_data=resource
                        )
                        
                        self.db.add(observation)
                        records_synced += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to sync observation {fhir_id}: {e}")
                        records_failed += 1
            
            await self.db.commit()
            return {
                "records_found": records_found,
                "records_synced": records_synced,
                "records_failed": records_failed
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to sync observations: {e}")
            raise
    
    async def _sync_diagnostic_reports(
        self,
        client,
        connection: EpicFHIRConnection,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Sync diagnostic reports from Epic FHIR."""
        # Similar implementation to observations
        # This is a placeholder - implement based on your needs
        return {"records_found": 0, "records_synced": 0, "records_failed": 0}
    
    async def _sync_documents(
        self,
        client,
        connection: EpicFHIRConnection,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Sync documents from Epic FHIR."""
        # Similar implementation to observations
        # This is a placeholder - implement based on your needs
        return {"records_found": 0, "records_synced": 0, "records_failed": 0}
    
    async def _sync_imaging_studies(
        self,
        client,
        connection: EpicFHIRConnection,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Sync imaging studies from Epic FHIR."""
        # Similar implementation to observations
        # This is a placeholder - implement based on your needs
        return {"records_found": 0, "records_synced": 0, "records_failed": 0}
    
    async def get_observations(
        self,
        user_id: UUID,
        category: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[EpicFHIRObservation], int]:
        """Get stored observations for a user."""
        try:
            # Build query
            query = select(EpicFHIRObservation).join(EpicFHIRConnection).where(
                EpicFHIRConnection.user_id == user_id
            )
            
            if category:
                query = query.where(EpicFHIRObservation.category == category)
            
            if date_from:
                query = query.where(EpicFHIRObservation.effective_datetime >= date_from)
            
            if date_to:
                query = query.where(EpicFHIRObservation.effective_datetime <= date_to)
            
            # Get total count
            count_query = select(EpicFHIRObservation.id).join(EpicFHIRConnection).where(
                EpicFHIRConnection.user_id == user_id
            )
            if category:
                count_query = count_query.where(EpicFHIRObservation.category == category)
            if date_from:
                count_query = count_query.where(EpicFHIRObservation.effective_datetime >= date_from)
            if date_to:
                count_query = count_query.where(EpicFHIRObservation.effective_datetime <= date_to)
            
            count_result = await self.db.execute(count_query)
            total_count = len(count_result.scalars().all())
            
            # Get paginated results
            query = query.order_by(desc(EpicFHIRObservation.effective_datetime))
            query = query.offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            observations = result.scalars().all()
            
            return observations, total_count
            
        except Exception as e:
            logger.error(f"Failed to get observations for user {user_id}: {e}")
            raise
    
    async def get_diagnostic_reports(
        self,
        user_id: UUID,
        category: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[EpicFHIRDiagnosticReport], int]:
        """Get stored diagnostic reports for a user."""
        try:
            query = select(EpicFHIRDiagnosticReport).join(EpicFHIRConnection).where(
                EpicFHIRConnection.user_id == user_id
            )
            
            if category:
                query = query.where(EpicFHIRDiagnosticReport.category == category)
            
            if date_from:
                query = query.where(EpicFHIRDiagnosticReport.effective_datetime >= date_from)
            
            if date_to:
                query = query.where(EpicFHIRDiagnosticReport.effective_datetime <= date_to)
            
            # Get total count
            count_query = select(EpicFHIRDiagnosticReport.id).join(EpicFHIRConnection).where(
                EpicFHIRConnection.user_id == user_id
            )
            if category:
                count_query = count_query.where(EpicFHIRDiagnosticReport.category == category)
            if date_from:
                count_query = count_query.where(EpicFHIRDiagnosticReport.effective_datetime >= date_from)
            if date_to:
                count_query = count_query.where(EpicFHIRDiagnosticReport.effective_datetime <= date_to)
            
            count_result = await self.db.execute(count_query)
            total_count = len(count_result.scalars().all())
            
            # Get paginated results
            query = query.order_by(desc(EpicFHIRDiagnosticReport.effective_datetime))
            query = query.offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            reports = result.scalars().all()
            
            return reports, total_count
            
        except Exception as e:
            logger.error(f"Failed to get diagnostic reports for user {user_id}: {e}")
            raise
    
    async def get_sync_logs(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[EpicFHIRSyncLog], int]:
        """Get sync logs for a user."""
        try:
            query = select(EpicFHIRSyncLog).join(EpicFHIRConnection).where(
                EpicFHIRConnection.user_id == user_id
            )
            
            # Get total count
            count_query = select(EpicFHIRSyncLog.id).join(EpicFHIRConnection).where(
                EpicFHIRConnection.user_id == user_id
            )
            
            count_result = await self.db.execute(count_query)
            total_count = len(count_result.scalars().all())
            
            # Get paginated results
            query = query.order_by(desc(EpicFHIRSyncLog.started_at))
            query = query.offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            logs = result.scalars().all()
            
            return logs, total_count
            
        except Exception as e:
            logger.error(f"Failed to get sync logs for user {user_id}: {e}")
            raise
    
    # Helper methods for extracting FHIR data
    def _extract_category(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract category from FHIR resource."""
        if resource.get("category") and resource["category"]:
            return resource["category"][0].get("coding", [{}])[0].get("code")
        return None
    
    def _extract_code(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract code from FHIR resource."""
        if resource.get("code") and resource["code"].get("coding"):
            return resource["code"]["coding"][0].get("code")
        return None
    
    def _extract_code_display(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract code display from FHIR resource."""
        if resource.get("code") and resource["code"].get("coding"):
            return resource["code"]["coding"][0].get("display")
        return None
    
    def _extract_value_quantity(self, resource: Dict[str, Any]) -> Optional[float]:
        """Extract value quantity from FHIR resource."""
        if resource.get("valueQuantity"):
            return resource["valueQuantity"].get("value")
        return None
    
    def _extract_value_unit(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract value unit from FHIR resource."""
        if resource.get("valueQuantity"):
            return resource["valueQuantity"].get("unit")
        return None
    
    def _extract_value_code(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract value code from FHIR resource."""
        if resource.get("valueCodeableConcept") and resource["valueCodeableConcept"].get("coding"):
            return resource["valueCodeableConcept"]["coding"][0].get("code")
        return None
    
    def _extract_value_string(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract value string from FHIR resource."""
        return resource.get("valueString")
    
    def _extract_interpretation(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract interpretation from FHIR resource."""
        if resource.get("interpretation") and resource["interpretation"]:
            return resource["interpretation"][0].get("coding", [{}])[0].get("display")
        return None
    
    def _extract_reference_range_low(self, resource: Dict[str, Any]) -> Optional[float]:
        """Extract reference range low from FHIR resource."""
        if resource.get("referenceRange") and resource["referenceRange"]:
            return resource["referenceRange"][0].get("low", {}).get("value")
        return None
    
    def _extract_reference_range_high(self, resource: Dict[str, Any]) -> Optional[float]:
        """Extract reference range high from FHIR resource."""
        if resource.get("referenceRange") and resource["referenceRange"]:
            return resource["referenceRange"][0].get("high", {}).get("value")
        return None
    
    def _parse_datetime(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from FHIR."""
        if not date_string:
            return None
        try:
            # Parse the datetime and convert to timezone-naive UTC
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            if dt.tzinfo:
                dt = dt.replace(tzinfo=None)
            return dt
        except:
            return None

    async def _sync_observations_direct(
        self,
        connection: EpicFHIRConnection,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Sync observations directly from Epic FHIR using HTTP requests."""
        try:
            # Use the patient ID from the connection
            patient_id = connection.patient_id
            if not patient_id:
                logger.warning("No patient ID in connection, skipping observations sync")
                return {"records_found": 0, "records_synced": 0, "records_failed": 0}

            # Build query parameters
            params = {"patient": patient_id}
            
            # Epic FHIR requires either code or category parameter
            # Let's try with a common category first
            params["category"] = "vital-signs"
            
            if date_from:
                params["date"] = f"ge{date_from.strftime('%Y-%m-%d')}"
            
            if date_to:
                if "date" in params:
                    params["date"] += f"&date=le{date_to.strftime('%Y-%m-%d')}"
                else:
                    params["date"] = f"le{date_to.strftime('%Y-%m-%d')}"

            # Make direct HTTP request to Epic FHIR
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{epic_fhir_config.base_url}/Observation",
                    params=params,
                    headers={
                        "Authorization": f"Bearer {connection.access_token}",
                        "Accept": "application/fhir+json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch observations: {response.status_code} - {response.text}")
                    return {"records_found": 0, "records_synced": 0, "records_failed": 1}

                observations_data = response.json()
                records_found = 0
                records_synced = 0
                records_failed = 0

                if observations_data.get("entry"):
                    records_found = len(observations_data["entry"])
                    
                    for entry in observations_data["entry"]:
                        try:
                            resource = entry.get("resource", {})
                            fhir_id = resource.get("id")
                            
                            if not fhir_id:
                                continue
                            
                            # Check if observation already exists
                            existing = await self.db.execute(
                                select(EpicFHIRObservation).where(
                                    and_(
                                        EpicFHIRObservation.connection_id == connection.id,
                                        EpicFHIRObservation.fhir_id == fhir_id
                                    )
                                )
                            )
                            
                            if existing.scalars().first():
                                continue  # Skip if already exists
                            
                            # Extract observation data
                            observation = EpicFHIRObservation(
                                connection_id=connection.id,
                                fhir_id=fhir_id,
                                category=self._extract_category(resource),
                                code=self._extract_code(resource),
                                code_display=self._extract_code_display(resource),
                                value_quantity=self._extract_value_quantity(resource),
                                value_unit=self._extract_value_unit(resource),
                                value_code=self._extract_value_code(resource),
                                value_string=self._extract_value_string(resource),
                                effective_datetime=self._parse_datetime(resource.get("effectiveDateTime")),
                                issued=self._parse_datetime(resource.get("issued")),
                                status=resource.get("status"),
                                interpretation=self._extract_interpretation(resource),
                                reference_range_low=self._extract_reference_range_low(resource),
                                reference_range_high=self._extract_reference_range_high(resource),
                                raw_data=resource
                            )
                            
                            self.db.add(observation)
                            records_synced += 1
                            
                        except Exception as e:
                            logger.error(f"Failed to sync observation {fhir_id}: {e}")
                            records_failed += 1

                await self.db.commit()
                logger.info(f"Synced {records_synced} observations for patient {patient_id}")
                return {"records_found": records_found, "records_synced": records_synced, "records_failed": records_failed}

        except Exception as e:
            logger.error(f"Failed to sync observations: {e}")
            import traceback
            logger.error(f"Observation sync error details: {traceback.format_exc()}")
            return {"records_found": 0, "records_synced": 0, "records_failed": 1}

    async def _sync_diagnostic_reports_direct(
        self,
        connection: EpicFHIRConnection,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Sync diagnostic reports directly from Epic FHIR using HTTP requests."""
        try:
            # Use the patient ID from the connection
            patient_id = connection.patient_id
            if not patient_id:
                logger.warning("No patient ID in connection, skipping diagnostic reports sync")
                return {"records_found": 0, "records_synced": 0, "records_failed": 0}

            # Build query parameters
            params = {"patient": patient_id}
            
            if date_from:
                params["date"] = f"ge{date_from.strftime('%Y-%m-%d')}"
            
            if date_to:
                if "date" in params:
                    params["date"] += f"&date=le{date_to.strftime('%Y-%m-%d')}"
                else:
                    params["date"] = f"le{date_to.strftime('%Y-%m-%d')}"

            # Make direct HTTP request to Epic FHIR
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{epic_fhir_config.base_url}/DiagnosticReport",
                    params=params,
                    headers={
                        "Authorization": f"Bearer {connection.access_token}",
                        "Accept": "application/fhir+json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch diagnostic reports: {response.status_code} - {response.text}")
                    return {"records_found": 0, "records_synced": 0, "records_failed": 1}

                reports_data = response.json()
                records_found = 0
                records_synced = 0
                records_failed = 0

                if reports_data.get("entry"):
                    records_found = len(reports_data["entry"])
                    
                    for entry in reports_data["entry"]:
                        try:
                            resource = entry.get("resource", {})
                            fhir_id = resource.get("id")
                            
                            if not fhir_id:
                                continue
                            
                            # Check if report already exists
                            existing = await self.db.execute(
                                select(EpicFHIRDiagnosticReport).where(
                                    and_(
                                        EpicFHIRDiagnosticReport.connection_id == connection.id,
                                        EpicFHIRDiagnosticReport.fhir_id == fhir_id
                                    )
                                )
                            )
                            
                            if existing.scalars().first():
                                continue  # Skip if already exists
                            
                            # Extract diagnostic report data
                            report = EpicFHIRDiagnosticReport(
                                connection_id=connection.id,
                                fhir_id=fhir_id,
                                category=self._extract_category(resource),
                                code=self._extract_code(resource),
                                code_display=self._extract_code_display(resource),
                                effective_datetime=self._parse_datetime(resource.get("effectiveDateTime")),
                                issued=self._parse_datetime(resource.get("issued")),
                                status=resource.get("status"),
                                conclusion=resource.get("conclusion"),
                                conclusion_code=resource.get("conclusionCode", {}).get("text") if resource.get("conclusionCode") else None,
                                raw_data=resource
                            )
                            
                            self.db.add(report)
                            records_synced += 1
                            
                        except Exception as e:
                            logger.error(f"Failed to sync diagnostic report {fhir_id}: {e}")
                            records_failed += 1

                await self.db.commit()
                logger.info(f"Synced {records_synced} diagnostic reports for patient {patient_id}")
                return {"records_found": records_found, "records_synced": records_synced, "records_failed": records_failed}

        except Exception as e:
            logger.error(f"Failed to sync diagnostic reports: {e}")
            return {"records_found": 0, "records_synced": 0, "records_failed": 1}

    async def _sync_documents_direct(
        self,
        connection: EpicFHIRConnection,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Sync documents directly from Epic FHIR using HTTP requests."""
        # For now, return empty results as documents sync is not implemented
        return {"records_found": 0, "records_synced": 0, "records_failed": 0}

    async def _sync_imaging_studies_direct(
        self,
        connection: EpicFHIRConnection,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Sync imaging studies directly from Epic FHIR using HTTP requests."""
        # For now, return empty results as imaging studies sync is not implemented
        return {"records_found": 0, "records_synced": 0, "records_failed": 0} 