"""
Epic FHIR Data Models

This module contains SQLAlchemy models for storing Epic FHIR data locally
in the PersonalHealthAssistant application.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from sqlalchemy import (
    Column,
    String,
    DateTime,
    JSON,
    Text,
    Boolean,
    Integer,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from common.models.base import Base


class EpicFHIRConnection(Base):
    """Model for storing Epic FHIR connection information."""

    __tablename__ = "epic_fhir_connections"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )

    # Connection details
    client_id: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str] = mapped_column(
        String(50), nullable=False, default="sandbox"
    )
    scope: Mapped[str] = mapped_column(Text, nullable=False)

    # OAuth2 token information
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Bearer"
    )
    expires_in: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Patient context
    patient_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    patient_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    observations: Mapped[List["EpicFHIRObservation"]] = relationship(
        "EpicFHIRObservation", back_populates="connection"
    )
    diagnostic_reports: Mapped[List["EpicFHIRDiagnosticReport"]] = relationship(
        "EpicFHIRDiagnosticReport", back_populates="connection"
    )
    documents: Mapped[List["EpicFHIRDocument"]] = relationship(
        "EpicFHIRDocument", back_populates="connection"
    )
    imaging_studies: Mapped[List["EpicFHIRImagingStudy"]] = relationship(
        "EpicFHIRImagingStudy", back_populates="connection"
    )

    __table_args__ = (
        Index("idx_epic_fhir_connections_user_active", "user_id", "is_active"),
        Index("idx_epic_fhir_connections_patient", "patient_id"),
    )


class EpicFHIRObservation(Base):
    """Model for storing Epic FHIR Observation data."""

    __tablename__ = "epic_fhir_observations"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    connection_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("epic_fhir_connections.id"), nullable=False
    )

    # FHIR resource information
    fhir_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Observation"
    )

    # Observation details
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    code_display: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Values
    value_quantity: Mapped[Optional[float]] = mapped_column(Integer, nullable=True)
    value_unit: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    value_code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    value_string: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timing
    effective_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    issued: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Status and interpretation
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    interpretation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Reference ranges
    reference_range_low: Mapped[Optional[float]] = mapped_column(Integer, nullable=True)
    reference_range_high: Mapped[Optional[float]] = mapped_column(
        Integer, nullable=True
    )

    # Raw FHIR data
    raw_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    connection: Mapped["EpicFHIRConnection"] = relationship(
        "EpicFHIRConnection", back_populates="observations"
    )

    __table_args__ = (
        Index("idx_epic_fhir_observations_fhir_id", "fhir_id"),
        Index("idx_epic_fhir_observations_category", "category"),
        Index("idx_epic_fhir_observations_effective_date", "effective_datetime"),
        Index("idx_epic_fhir_observations_connection", "connection_id"),
    )


class EpicFHIRDiagnosticReport(Base):
    """Model for storing Epic FHIR DiagnosticReport data."""

    __tablename__ = "epic_fhir_diagnostic_reports"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    connection_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("epic_fhir_connections.id"), nullable=False
    )

    # FHIR resource information
    fhir_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="DiagnosticReport"
    )

    # Report details
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    code_display: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timing
    effective_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    issued: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Status
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Results and conclusions
    conclusion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conclusion_code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Raw FHIR data
    raw_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    connection: Mapped["EpicFHIRConnection"] = relationship(
        "EpicFHIRConnection", back_populates="diagnostic_reports"
    )

    __table_args__ = (
        Index("idx_epic_fhir_diagnostic_reports_fhir_id", "fhir_id"),
        Index("idx_epic_fhir_diagnostic_reports_category", "category"),
        Index("idx_epic_fhir_diagnostic_reports_effective_date", "effective_datetime"),
        Index("idx_epic_fhir_diagnostic_reports_connection", "connection_id"),
    )


class EpicFHIRDocument(Base):
    """Model for storing Epic FHIR DocumentReference data."""

    __tablename__ = "epic_fhir_documents"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    connection_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("epic_fhir_connections.id"), nullable=False
    )

    # FHIR resource information
    fhir_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="DocumentReference"
    )

    # Document details
    type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type_display: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Content
    content_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timing
    date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Status
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Authors and custodians
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    custodian: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Raw FHIR data
    raw_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    connection: Mapped["EpicFHIRConnection"] = relationship(
        "EpicFHIRConnection", back_populates="documents"
    )

    __table_args__ = (
        Index("idx_epic_fhir_documents_fhir_id", "fhir_id"),
        Index("idx_epic_fhir_documents_type", "type"),
        Index("idx_epic_fhir_documents_date", "date"),
        Index("idx_epic_fhir_documents_connection", "connection_id"),
    )


class EpicFHIRImagingStudy(Base):
    """Model for storing Epic FHIR ImagingStudy data."""

    __tablename__ = "epic_fhir_imaging_studies"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    connection_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("epic_fhir_connections.id"), nullable=False
    )

    # FHIR resource information
    fhir_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ImagingStudy"
    )

    # Study details
    modality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    procedure_code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    procedure_display: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timing
    started: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Status
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Study information
    number_of_series: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    number_of_instances: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Location
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Raw FHIR data
    raw_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    connection: Mapped["EpicFHIRConnection"] = relationship(
        "EpicFHIRConnection", back_populates="imaging_studies"
    )

    __table_args__ = (
        Index("idx_epic_fhir_imaging_studies_fhir_id", "fhir_id"),
        Index("idx_epic_fhir_imaging_studies_modality", "modality"),
        Index("idx_epic_fhir_imaging_studies_started", "started"),
        Index("idx_epic_fhir_imaging_studies_connection", "connection_id"),
    )


class EpicFHIRSyncLog(Base):
    """Model for tracking Epic FHIR data synchronization."""

    __tablename__ = "epic_fhir_sync_logs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    connection_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("epic_fhir_connections.id"), nullable=False
    )

    # Sync details
    sync_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'full', 'incremental', 'specific'
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'Observation', 'DiagnosticReport', etc.

    # Results
    records_found: Mapped[int] = mapped_column(Integer, default=0)
    records_synced: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)

    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="running"
    )  # 'running', 'completed', 'failed'
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_epic_fhir_sync_logs_connection", "connection_id"),
        Index("idx_epic_fhir_sync_logs_status", "status"),
        Index("idx_epic_fhir_sync_logs_started", "started_at"),
    )
