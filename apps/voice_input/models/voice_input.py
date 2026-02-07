"""
Voice Input Data Models
Core models for voice input processing and storage.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Float, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from common.models.base import Base


class InputStatus(str, Enum):
    """Status of voice input processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InputType(str, Enum):
    """Type of voice input"""
    VOICE_COMMAND = "voice_command"
    VOICE_NOTE = "voice_note"
    VOICE_QUERY = "voice_query"
    VOICE_SYMPTOM = "voice_symptom"
    VOICE_MEDICATION = "voice_medication"
    VOICE_APPOINTMENT = "voice_appointment"
    VOICE_EMERGENCY = "voice_emergency"


class VoiceInput(Base):
    """Database model for voice input records"""
    __tablename__ = "voice_inputs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Input metadata
    input_type = Column(String(50), nullable=False)
    status = Column(String(20), default=InputStatus.PENDING.value)
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high, 4=urgent
    
    # Audio file information
    audio_file_path = Column(String(500), nullable=True)
    audio_duration = Column(Float, nullable=True)  # in seconds
    audio_format = Column(String(20), nullable=True)  # wav, mp3, m4a, etc.
    audio_quality_score = Column(Float, nullable=True)  # 0-1 score
    
    # Processing results
    transcription_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0-1 confidence
    language_detected = Column(String(10), nullable=True)  # en, es, fr, etc.
    
    # Intent and entities
    detected_intent = Column(String(100), nullable=True)
    entities = Column(JSON, nullable=True)  # Extracted entities
    context = Column(JSON, nullable=True)  # Additional context
    
    # Multi-modal data
    text_input = Column(Text, nullable=True)  # Additional text input
    image_data = Column(JSON, nullable=True)  # Image analysis results
    sensor_data = Column(JSON, nullable=True)  # Device sensor data
    
    # Processing metadata
    processing_time = Column(Float, nullable=True)  # in seconds
    processing_errors = Column(JSON, nullable=True)
    processing_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)


class VoiceInputCreate(BaseModel):
    """Model for creating voice input"""
    patient_id: UUID = Field(..., description="Patient ID")
    session_id: Optional[str] = Field(None, description="Session ID for grouping inputs")
    input_type: InputType = Field(..., description="Type of voice input")
    priority: int = Field(1, ge=1, le=4, description="Priority level (1-4)")
    
    # Optional multi-modal data
    text_input: Optional[str] = Field(None, description="Additional text input")
    image_data: Optional[Dict[str, Any]] = Field(None, description="Image analysis data")
    sensor_data: Optional[Dict[str, Any]] = Field(None, description="Device sensor data")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class VoiceInputUpdate(BaseModel):
    """Model for updating voice input"""
    status: Optional[InputStatus] = Field(None, description="Processing status")
    transcription_text: Optional[str] = Field(None, description="Transcribed text")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence score")
    language_detected: Optional[str] = Field(None, description="Detected language")
    detected_intent: Optional[str] = Field(None, description="Detected intent")
    entities: Optional[Dict[str, Any]] = Field(None, description="Extracted entities")
    audio_quality_score: Optional[float] = Field(None, ge=0, le=1, description="Audio quality score")
    processing_time: Optional[float] = Field(None, ge=0, description="Processing time in seconds")
    processing_errors: Optional[List[str]] = Field(None, description="Processing errors")
    processing_metadata: Optional[Dict[str, Any]] = Field(None, description="Processing metadata")


class VoiceInputResponse(BaseModel):
    """Model for voice input response"""
    id: UUID
    patient_id: UUID
    session_id: Optional[str]
    input_type: InputType
    status: InputStatus
    priority: int
    
    # Audio information
    audio_duration: Optional[float]
    audio_format: Optional[str]
    audio_quality_score: Optional[float]
    
    # Processing results
    transcription_text: Optional[str]
    confidence_score: Optional[float]
    language_detected: Optional[str]
    detected_intent: Optional[str]
    entities: Optional[Dict[str, Any]]
    
    # Multi-modal data
    text_input: Optional[str]
    image_data: Optional[Dict[str, Any]]
    sensor_data: Optional[Dict[str, Any]]
    context: Optional[Dict[str, Any]]
    
    # Processing metadata
    processing_time: Optional[float]
    processing_errors: Optional[List[str]]
    processing_metadata: Optional[Dict[str, Any]]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class VoiceQualityMetrics(BaseModel):
    """Model for voice quality metrics"""
    duration: float = Field(..., description="Audio duration in seconds")
    sample_rate: int = Field(..., description="Sample rate in Hz")
    channels: int = Field(..., description="Number of audio channels")
    bit_rate: int = Field(..., description="Bit rate in bits per second")
    format: str = Field(..., description="Audio format")
    file_size: int = Field(..., description="File size in bytes")
    quality_score: float = Field(..., ge=0, le=1, description="Overall quality score")
    noise_level: float = Field(..., ge=0, le=1, description="Noise level (0=clean, 1=noisy)")
    clarity_score: float = Field(..., ge=0, le=1, description="Speech clarity score")
    volume_level: float = Field(..., ge=0, le=1, description="Volume level")
    is_clear: bool = Field(..., description="Whether audio is clear")
    has_background_noise: bool = Field(..., description="Whether background noise is present")
    is_truncated: bool = Field(..., description="Whether audio is truncated")
    analysis_timestamp: datetime = Field(..., description="When analysis was performed")


class AudioMetadata(BaseModel):
    """Model for audio file metadata"""
    duration: float = Field(..., description="Audio duration in seconds")
    sample_rate: int = Field(..., description="Sample rate in Hz")
    channels: int = Field(..., description="Number of audio channels")
    bit_rate: int = Field(..., description="Bit rate in bits per second")
    format: str = Field(..., description="Audio format")
    file_size: int = Field(..., description="File size in bytes")
    encoding: str = Field(..., description="Audio encoding")
    created_at: datetime = Field(..., description="File creation time")
    modified_at: datetime = Field(..., description="File modification time") 