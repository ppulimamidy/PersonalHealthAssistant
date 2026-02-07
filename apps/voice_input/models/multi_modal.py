"""
Multi-Modal Input Models
Models for combining multiple input modalities (voice, text, image, sensor data).
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Float, JSON, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from common.models.base import Base


class InputModality(str, Enum):
    """Types of input modalities"""
    VOICE = "voice"
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    SENSOR = "sensor"
    GESTURE = "gesture"
    BIOMETRIC = "biometric"


class VoiceInput(BaseModel):
    """Voice input data"""
    audio_file_path: str = Field(..., description="Path to audio file")
    audio_duration: float = Field(..., description="Audio duration in seconds")
    audio_format: str = Field(..., description="Audio format (wav, mp3, etc.)")
    transcription_text: Optional[str] = Field(None, description="Transcribed text")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Transcription confidence")
    language_detected: Optional[str] = Field(None, description="Detected language")


class TextInput(BaseModel):
    """Text input data"""
    text_content: str = Field(..., description="Text content")
    language: Optional[str] = Field(None, description="Text language")
    source: Optional[str] = Field(None, description="Text source (typing, OCR, etc.)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ImageInput(BaseModel):
    """Image input data"""
    image_file_path: str = Field(..., description="Path to image file")
    image_format: str = Field(..., description="Image format (jpg, png, etc.)")
    image_size: Dict[str, int] = Field(..., description="Image dimensions {width, height}")
    image_analysis: Optional[Dict[str, Any]] = Field(None, description="Image analysis results")
    ocr_text: Optional[str] = Field(None, description="OCR extracted text")


class SensorInput(BaseModel):
    """Sensor data input"""
    sensor_type: str = Field(..., description="Type of sensor (heart_rate, temperature, etc.)")
    sensor_value: Union[float, int, str] = Field(..., description="Sensor reading")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    device_id: Optional[str] = Field(None, description="Device identifier")
    location: Optional[str] = Field(None, description="Sensor location on body")


class FusionStrategy(str, Enum):
    """Fusion strategies for combining modalities"""
    EARLY = "early"
    LATE = "late"
    HYBRID = "hybrid"


class ModalityType(str, Enum):
    """Modality types"""
    VOICE = "voice"
    TEXT = "text"
    IMAGE = "image"
    SENSOR = "sensor"


class ProcessingStatus(str, Enum):
    """Processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ConfidenceScore(BaseModel):
    """Confidence score for a modality"""
    value: float = Field(..., ge=0, le=1)
    modality: ModalityType


class MultiModalRequest(BaseModel):
    """Request for multi-modal processing"""
    modalities: List[ModalityType]
    data: dict
    fusion_strategy: FusionStrategy = FusionStrategy.HYBRID


class MultiModalInput(BaseModel):
    """Input for multi-modal processing"""
    voice_input: Optional[VoiceInput] = Field(None, description="Voice input data")
    text_input: Optional[TextInput] = Field(None, description="Text input data")
    image_input: Optional[ImageInput] = Field(None, description="Image input data")
    sensor_input: Optional[SensorInput] = Field(None, description="Sensor input data")
    fusion_strategy: FusionStrategy = Field(FusionStrategy.HYBRID, description="Fusion strategy")
    user_id: Optional[UUID] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MultiModalResult(BaseModel):
    """Result of multi-modal processing"""
    input_id: UUID = Field(..., description="Input ID")
    processing_successful: bool
    processing_time: float = Field(..., description="Total processing time in seconds")
    
    # Combined analysis results
    combined_text: str = Field(..., description="Combined text from all modalities")
    primary_intent: str = Field(..., description="Primary recognized intent")
    confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence score")
    
    # Modality-specific results
    voice_processing_result: Optional[Dict[str, Any]] = Field(None, description="Voice processing results")
    text_processing_result: Optional[Dict[str, Any]] = Field(None, description="Text processing results")
    image_processing_result: Optional[Dict[str, Any]] = Field(None, description="Image processing results")
    sensor_processing_result: Optional[Dict[str, Any]] = Field(None, description="Sensor processing results")
    
    # Extracted information
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted entities")
    health_indicators: Dict[str, Any] = Field(default_factory=dict, description="Health indicators")
    recommendations: List[str] = Field(default_factory=list, description="Generated recommendations")
    
    # Processing details
    processing_errors: List[str] = Field(default_factory=list, description="Processing errors")
    processing_warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    
    # Timestamps
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class MultiModalFusion(BaseModel):
    """Fusion strategy for combining multiple modalities"""
    fusion_method: str = Field(..., description="Fusion method (early, late, hybrid)")
    modality_weights: Dict[str, float] = Field(default_factory=dict, description="Weights for each modality")
    confidence_threshold: float = Field(0.7, ge=0, le=1, description="Confidence threshold")
    fusion_metadata: Dict[str, Any] = Field(default_factory=dict, description="Fusion metadata") 