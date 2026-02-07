"""
Text-to-Speech Models
Models for text-to-speech processing and synthesis.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Float, JSON, Text, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from common.models.base import Base


class VoiceType(str, Enum):
    """Types of voice synthesis"""
    NEURAL = "neural"
    CONCATENATIVE = "concatenative"
    HMM = "hmm"
    DNN = "dnn"
    WAVENET = "wavenet"
    TACOTRON = "tacotron"


class EmotionType(str, Enum):
    """Types of emotional expression in speech"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    EXCITED = "excited"
    CALM = "calm"
    CONCERNED = "concerned"
    PROFESSIONAL = "professional"


class SpeechRate(str, Enum):
    """Speech rate options"""
    VERY_SLOW = "very_slow"
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"
    VERY_FAST = "very_fast"


class PitchLevel(str, Enum):
    """Pitch level options"""
    VERY_LOW = "very_low"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    VERY_HIGH = "very_high"


class TextToSpeechRequest(BaseModel):
    """Request model for text-to-speech synthesis"""
    text: str = Field(..., description="Text to synthesize")
    voice_id: Optional[str] = Field(None, description="Voice ID to use")
    language: str = Field("en", description="Language code")
    voice_type: VoiceType = Field(VoiceType.NEURAL, description="Type of voice synthesis")
    emotion: EmotionType = Field(EmotionType.NEUTRAL, description="Emotional expression")
    speech_rate: SpeechRate = Field(SpeechRate.NORMAL, description="Speech rate")
    pitch_level: PitchLevel = Field(PitchLevel.NORMAL, description="Pitch level")
    volume: float = Field(1.0, ge=0.0, le=2.0, description="Volume level (0.0-2.0)")
    sample_rate: int = Field(22050, description="Audio sample rate")
    format: str = Field("wav", description="Output audio format")
    ssml: bool = Field(False, description="Whether text is SSML markup")
    prosody_control: Optional[Dict[str, Any]] = Field(None, description="Prosody control parameters")
    voice_input_id: Optional[UUID] = Field(None, description="Associated voice input ID")


class TextToSpeechResult(BaseModel):
    """Result model for text-to-speech synthesis"""
    synthesis_id: UUID = Field(..., description="Unique synthesis ID")
    text: str = Field(..., description="Original text")
    synthesized_text: str = Field(..., description="Processed text (with SSML if applicable)")
    audio_file_path: str = Field(..., description="Path to generated audio file")
    audio_duration: float = Field(..., description="Duration of generated audio in seconds")
    audio_format: str = Field(..., description="Audio format")
    sample_rate: int = Field(..., description="Audio sample rate")
    bit_rate: Optional[int] = Field(None, description="Audio bit rate")
    file_size: int = Field(..., description="Audio file size in bytes")
    voice_id: str = Field(..., description="Voice ID used")
    voice_name: str = Field(..., description="Voice name")
    language: str = Field(..., description="Language used")
    voice_type: VoiceType = Field(..., description="Voice synthesis type")
    emotion: EmotionType = Field(..., description="Emotional expression")
    speech_rate: SpeechRate = Field(..., description="Speech rate used")
    pitch_level: PitchLevel = Field(..., description="Pitch level used")
    volume: float = Field(..., description="Volume level used")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Synthesis quality score")
    naturalness_score: float = Field(..., ge=0.0, le=1.0, description="Naturalness score")
    intelligibility_score: float = Field(..., ge=0.0, le=1.0, description="Intelligibility score")
    processing_time: float = Field(..., description="Processing time in seconds")
    synthesis_successful: bool = Field(..., description="Whether synthesis was successful")
    processing_errors: Optional[List[str]] = Field(None, description="Processing errors if any")
    synthesis_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class VoiceProfile(BaseModel):
    """Voice profile model"""
    voice_id: str = Field(..., description="Unique voice ID")
    voice_name: str = Field(..., description="Voice name")
    language: str = Field(..., description="Language code")
    gender: str = Field(..., description="Voice gender")
    age_group: str = Field(..., description="Age group")
    accent: Optional[str] = Field(None, description="Accent or dialect")
    voice_type: VoiceType = Field(..., description="Voice synthesis type")
    sample_rate: int = Field(..., description="Sample rate")
    pitch_range: Dict[str, float] = Field(..., description="Pitch range (min, max)")
    speaking_rate_range: Dict[str, float] = Field(..., description="Speaking rate range")
    emotion_support: List[EmotionType] = Field(..., description="Supported emotions")
    quality_metrics: Dict[str, float] = Field(..., description="Quality metrics")
    is_available: bool = Field(True, description="Whether voice is available")
    is_premium: bool = Field(False, description="Whether voice requires premium access")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class SpeechSegment(BaseModel):
    """Individual segment of synthesized speech"""
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Text for this segment")
    emotion: EmotionType = Field(..., description="Emotion for this segment")
    pitch: float = Field(..., description="Pitch value")
    rate: float = Field(..., description="Speech rate")
    volume: float = Field(..., description="Volume level")


class SSMLProcessor(BaseModel):
    """SSML processing configuration"""
    enable_ssml: bool = Field(True, description="Enable SSML processing")
    supported_tags: List[str] = Field(..., description="Supported SSML tags")
    voice_attributes: Dict[str, Any] = Field(..., description="Voice attributes")
    prosody_controls: Dict[str, Any] = Field(..., description="Prosody control options")
    emotion_mapping: Dict[str, EmotionType] = Field(..., description="SSML emotion mapping")


# SQLAlchemy Models
class TextToSpeechSynthesis(Base):
    """Text-to-speech synthesis database model"""
    __tablename__ = "text_to_speech_syntheses"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    synthesis_id = Column(PGUUID(as_uuid=True), unique=True, nullable=False)
    text = Column(Text, nullable=False)
    synthesized_text = Column(Text, nullable=False)
    audio_file_path = Column(String, nullable=False)
    audio_duration = Column(Float, nullable=False)
    audio_format = Column(String, nullable=False)
    sample_rate = Column(Integer, nullable=False)
    bit_rate = Column(Integer)
    file_size = Column(Integer, nullable=False)
    voice_id = Column(String, nullable=False)
    voice_name = Column(String, nullable=False)
    language = Column(String, nullable=False)
    voice_type = Column(String, nullable=False)
    emotion = Column(String, nullable=False)
    speech_rate = Column(String, nullable=False)
    pitch_level = Column(String, nullable=False)
    volume = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    naturalness_score = Column(Float, nullable=False)
    intelligibility_score = Column(Float, nullable=False)
    processing_time = Column(Float, nullable=False)
    synthesis_successful = Column(String, nullable=False)
    processing_errors = Column(JSON)
    synthesis_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class VoiceProfileDB(Base):
    """Voice profile database model"""
    __tablename__ = "voice_profiles"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    voice_id = Column(String, unique=True, nullable=False)
    voice_name = Column(String, nullable=False)
    language = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    age_group = Column(String, nullable=False)
    accent = Column(String)
    voice_type = Column(String, nullable=False)
    sample_rate = Column(Integer, nullable=False)
    pitch_range = Column(JSON, nullable=False)
    speaking_rate_range = Column(JSON, nullable=False)
    emotion_support = Column(JSON, nullable=False)
    quality_metrics = Column(JSON, nullable=False)
    is_available = Column(String, nullable=False, default="true")
    is_premium = Column(String, nullable=False, default="false")
    created_at = Column(DateTime, default=datetime.utcnow)


class TTSPreviewRequest(BaseModel):
    """Request model for TTS preview"""
    text: str = Field(..., description="Text to preview")
    voice_id: Optional[str] = Field(None, description="Voice ID to use")
    language: str = Field("en", description="Language code")
    emotion: EmotionType = Field(EmotionType.NEUTRAL, description="Emotional expression")
    duration_limit: Optional[float] = Field(None, description="Maximum duration in seconds")


class TTSBatchRequest(BaseModel):
    """Request model for batch TTS synthesis"""
    requests: List[TextToSpeechRequest] = Field(..., description="List of TTS requests")
    batch_id: Optional[UUID] = Field(None, description="Batch identifier")
    priority: int = Field(1, ge=1, le=5, description="Batch priority")


class TTSBatchResult(BaseModel):
    """Result model for batch TTS synthesis"""
    batch_id: UUID = Field(..., description="Batch identifier")
    total_requests: int = Field(..., description="Total number of requests")
    successful_syntheses: int = Field(..., description="Number of successful syntheses")
    failed_syntheses: int = Field(..., description="Number of failed syntheses")
    results: List[TextToSpeechResult] = Field(..., description="Individual synthesis results")
    processing_time: float = Field(..., description="Total processing time")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp") 