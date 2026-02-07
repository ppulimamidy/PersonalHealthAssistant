"""
Intent Recognition Models
Models for understanding user intentions and extracting entities from voice input.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Float, JSON, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from enum import Enum

from common.models.base import Base


class Entity(BaseModel):
    """Extracted entity from voice input"""
    entity_type: str = Field(..., description="Type of entity (symptom, medication, date, etc.)")
    entity_value: str = Field(..., description="Extracted entity value")
    confidence: float = Field(..., ge=0, le=1, description="Entity extraction confidence")
    start_position: int = Field(..., description="Start position in text")
    end_position: int = Field(..., description="End position in text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Entity metadata")


class Intent(BaseModel):
    """Recognized intent from voice input"""
    intent_name: str = Field(..., description="Name of the recognized intent")
    confidence: float = Field(..., ge=0, le=1, description="Intent recognition confidence")
    category: str = Field(..., description="Intent category (health, appointment, medication, etc.)")
    priority: int = Field(1, ge=1, le=5, description="Intent priority (1-5)")
    requires_action: bool = Field(True, description="Whether intent requires immediate action")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Intent metadata")


class IntentRecognitionResult(BaseModel):
    """Complete intent recognition result"""
    voice_input_id: UUID
    transcription_text: str = Field(..., description="Input text for intent recognition")
    recognition_successful: bool
    processing_time: float = Field(..., description="Processing time in seconds")
    
    # Recognized intents (multiple intents possible)
    primary_intent: Intent = Field(..., description="Primary recognized intent")
    secondary_intents: List[Intent] = Field(default_factory=list, description="Secondary intents")
    
    # Extracted entities
    entities: List[Entity] = Field(default_factory=list, description="Extracted entities")
    
    # Context and sentiment
    context: Dict[str, Any] = Field(default_factory=dict, description="Recognized context")
    sentiment: Optional[str] = Field(None, description="Detected sentiment (positive, negative, neutral)")
    urgency_level: int = Field(1, ge=1, le=5, description="Urgency level (1-5)")
    
    # Processing details
    recognition_model: str = Field(..., description="Model used for intent recognition")
    recognition_errors: List[str] = Field(default_factory=list, description="Recognition errors")
    recognition_warnings: List[str] = Field(default_factory=list, description="Recognition warnings")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    
    # Timestamps
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class HealthIntent(BaseModel):
    """Health-specific intent recognition"""
    symptom_intent: Optional[Dict[str, Any]] = Field(None, description="Symptom-related intent")
    medication_intent: Optional[Dict[str, Any]] = Field(None, description="Medication-related intent")
    appointment_intent: Optional[Dict[str, Any]] = Field(None, description="Appointment-related intent")
    emergency_intent: Optional[Dict[str, Any]] = Field(None, description="Emergency-related intent")
    wellness_intent: Optional[Dict[str, Any]] = Field(None, description="Wellness-related intent")
    
    # Health-specific entities
    symptoms: List[str] = Field(default_factory=list, description="Detected symptoms")
    medications: List[str] = Field(default_factory=list, description="Mentioned medications")
    body_parts: List[str] = Field(default_factory=list, description="Mentioned body parts")
    severity_level: Optional[str] = Field(None, description="Severity level (mild, moderate, severe)")
    duration: Optional[str] = Field(None, description="Duration of symptoms")


class IntentType(str, Enum):
    SYMPTOM_REPORT = "symptom_report"
    MEDICATION_QUERY = "medication_query"
    APPOINTMENT_REQUEST = "appointment_request"
    EMERGENCY_ALERT = "emergency_alert"
    WELLNESS_QUERY = "wellness_query"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    SYMPTOM = "symptom"
    MEDICATION = "medication"
    DATE = "date"
    BODY_PART = "body_part"
    SEVERITY = "severity"
    DURATION = "duration"
    TIME = "time"
    OTHER = "other"


class IntentConfidence(BaseModel):
    value: float = Field(..., ge=0, le=1)


class EntityConfidence(BaseModel):
    value: float = Field(..., ge=0, le=1)


class IntentRecognitionRequest(BaseModel):
    voice_input_id: UUID
    transcription_text: str
    context: Optional[Dict[str, Any]] = None 