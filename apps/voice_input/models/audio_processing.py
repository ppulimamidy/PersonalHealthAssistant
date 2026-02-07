"""
Audio Processing Models
Models for audio quality analysis and processing results.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Float, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from common.models.base import Base


class AudioQualityMetrics(BaseModel):
    """Audio quality metrics"""
    signal_to_noise_ratio: float = Field(..., description="Signal-to-noise ratio in dB")
    background_noise_level: float = Field(..., description="Background noise level in dB")
    speech_clarity: float = Field(..., ge=0, le=1, description="Speech clarity score (0-1)")
    volume_consistency: float = Field(..., ge=0, le=1, description="Volume consistency score (0-1)")
    audio_artifacts: List[str] = Field(default_factory=list, description="Detected audio artifacts")
    overall_quality_score: float = Field(..., ge=0, le=1, description="Overall quality score (0-1)")


class AudioProcessingResult(BaseModel):
    """Result of audio processing"""
    voice_input_id: UUID
    processing_successful: bool
    processing_time: float = Field(..., description="Processing time in seconds")
    
    # Audio analysis results
    audio_duration: float = Field(..., description="Audio duration in seconds")
    sample_rate: int = Field(..., description="Audio sample rate in Hz")
    channels: int = Field(..., description="Number of audio channels")
    bit_depth: int = Field(..., description="Audio bit depth")
    
    # Quality metrics
    quality_metrics: Optional[AudioQualityMetrics] = Field(None, description="Audio quality metrics")
    
    # Processing details
    processing_errors: List[str] = Field(default_factory=list, description="Processing errors")
    processing_warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    
    # Timestamps
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class AudioEnhancementResult(BaseModel):
    """Result of audio enhancement processing"""
    original_file_path: str = Field(..., description="Path to original audio file")
    enhanced_file_path: str = Field(..., description="Path to enhanced audio file")
    enhancement_applied: List[str] = Field(..., description="List of enhancements applied")
    quality_improvement: float = Field(..., ge=0, le=1, description="Quality improvement score (0-1)")
    processing_time: float = Field(..., description="Enhancement processing time")
    success: bool = Field(..., description="Whether enhancement was successful")
    error_message: Optional[str] = Field(None, description="Error message if enhancement failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Enhancement metadata") 