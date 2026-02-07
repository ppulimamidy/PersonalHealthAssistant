"""
Transcription Models
Models for speech-to-text transcription results and segments.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Float, JSON, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from common.models.base import Base


class TranscriptionSegment(BaseModel):
    """Individual segment of transcribed speech"""
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Transcribed text for this segment")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score for this segment")
    speaker_id: Optional[str] = Field(None, description="Speaker identification")
    language: Optional[str] = Field(None, description="Language for this segment")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Segment metadata")


class TranscriptionResult(BaseModel):
    """Complete transcription result"""
    voice_input_id: UUID
    transcription_successful: bool
    processing_time: float = Field(..., description="Transcription processing time in seconds")
    
    # Transcription content
    full_text: str = Field(..., description="Complete transcribed text")
    segments: List[TranscriptionSegment] = Field(default_factory=list, description="Individual segments")
    
    # Language and confidence
    detected_language: str = Field(..., description="Primary detected language")
    language_confidence: float = Field(..., ge=0, le=1, description="Language detection confidence")
    overall_confidence: float = Field(..., ge=0, le=1, description="Overall transcription confidence")
    
    # Speaker information
    speaker_count: int = Field(1, description="Number of speakers detected")
    speaker_confidence: Optional[float] = Field(None, ge=0, le=1, description="Speaker identification confidence")
    
    # Processing details
    transcription_model: str = Field(..., description="Model used for transcription")
    transcription_errors: List[str] = Field(default_factory=list, description="Transcription errors")
    transcription_warnings: List[str] = Field(default_factory=list, description="Transcription warnings")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    
    # Timestamps
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class TranscriptionEnhancement(BaseModel):
    """Enhanced transcription with corrections"""
    original_transcription: str
    enhanced_transcription: str
    corrections_applied: List[Dict[str, Any]] = Field(..., description="List of corrections applied")
    enhancement_score: float = Field(..., ge=0, le=1, description="Enhancement quality score")
    processing_time: float = Field(..., description="Enhancement processing time")
    enhancement_metadata: Dict[str, Any] = Field(default_factory=dict, description="Enhancement metadata") 