"""
Vision Analysis Models
Models for vision-enabled voice input processing with image analysis.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class ImageFormat(str, Enum):
    """Supported image formats"""
    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    WEBP = "webp"
    TIFF = "tiff"
    BMP = "bmp"


class VisionModelProvider(str, Enum):
    """Supported vision model providers"""
    GROQ = "groq"
    OPENAI = "openai"


class AudioFormat(str, Enum):
    """Supported audio output formats"""
    MP3 = "mp3"
    WAV = "wav"
    M4A = "m4a"
    OGG = "ogg"
    FLAC = "flac"


class TTSProvider(str, Enum):
    """Supported text-to-speech providers"""
    EDGE_TTS = "edge_tts"
    GTTS = "gtts"
    PYTTSX3 = "pyttsx3"
    OPENAI_TTS = "openai_tts"


class ImageUploadRequest(BaseModel):
    """Request model for image upload with voice query"""
    patient_id: UUID = Field(..., description="Patient identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    voice_query_file: Optional[str] = Field(None, description="Voice query file path")
    text_query: Optional[str] = Field(None, description="Text query as alternative to voice")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    priority: int = Field(default=1, description="Processing priority")
    urgency_level: int = Field(default=1, description="Urgency level")


class ImageUploadResponse(BaseModel):
    """Response model for image upload"""
    image_id: UUID = Field(..., description="Unique image identifier")
    patient_id: UUID = Field(..., description="Patient identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    image_path: str = Field(..., description="Path to stored image")
    image_format: ImageFormat = Field(..., description="Image format")
    image_size: int = Field(..., description="Image size in bytes")
    image_dimensions: Dict[str, int] = Field(..., description="Image width and height")
    upload_timestamp: datetime = Field(..., description="Upload timestamp")
    status: str = Field(default="uploaded", description="Upload status")


class SpeechToTextRequest(BaseModel):
    """Request model for speech-to-text conversion"""
    audio_file_path: str = Field(..., description="Path to audio file")
    language: str = Field(default="en", description="Language code")
    model: str = Field(default="whisper-1", description="STT model to use")
    enhance_audio: bool = Field(default=True, description="Whether to enhance audio quality")


class SpeechToTextResponse(BaseModel):
    """Response model for speech-to-text conversion"""
    transcription_id: UUID = Field(..., description="Unique transcription identifier")
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., description="Confidence score")
    language: str = Field(..., description="Detected language")
    duration: float = Field(..., description="Audio duration in seconds")
    word_timestamps: Optional[List[Dict[str, Any]]] = Field(None, description="Word-level timestamps")
    processing_time: float = Field(..., description="Processing time in seconds")
    medical_context: Optional[Dict[str, Any]] = Field(None, description="Medical context information")


class VisionAnalysisRequest(BaseModel):
    """Request model for vision analysis"""
    image_path: str = Field(..., description="Path to image file")
    query: str = Field(..., description="Text query for vision analysis")
    provider: VisionModelProvider = Field(default=VisionModelProvider.GROQ, description="Vision model provider")
    model: str = Field(default="llava-3.1-8b-instant", description="Vision model to use")
    max_tokens: int = Field(default=1000, description="Maximum tokens for response")
    temperature: float = Field(default=0.7, description="Response temperature")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class VisionAnalysisResponse(BaseModel):
    """Response model for vision analysis"""
    analysis_id: UUID = Field(..., description="Unique analysis identifier")
    query: str = Field(..., description="Original query")
    response: str = Field(..., description="Vision model response")
    confidence: float = Field(..., description="Confidence score")
    provider: VisionModelProvider = Field(..., description="Used provider")
    model: str = Field(..., description="Used model")
    processing_time: float = Field(..., description="Processing time in seconds")
    tokens_used: Optional[int] = Field(None, description="Tokens used in request")
    cost: Optional[float] = Field(None, description="API cost in USD")
    medical_domain: Optional[str] = Field(None, description="Detected medical domain")
    medical_confidence: Optional[float] = Field(None, description="Medical domain confidence score")


class TextToSpeechRequest(BaseModel):
    """Request model for text-to-speech conversion"""
    text: str = Field(..., description="Text to convert to speech")
    provider: TTSProvider = Field(default=TTSProvider.EDGE_TTS, description="TTS provider")
    voice: str = Field(default="en-US-JennyNeural", description="Voice to use")
    language: str = Field(default="en-US", description="Language code")
    audio_format: AudioFormat = Field(default=AudioFormat.MP3, description="Output audio format")
    speed: float = Field(default=1.0, description="Speech speed multiplier")
    pitch: float = Field(default=1.0, description="Speech pitch multiplier")
    volume: float = Field(default=1.0, description="Speech volume multiplier")


class TextToSpeechResponse(BaseModel):
    """Response model for text-to-speech conversion"""
    tts_id: UUID = Field(..., description="Unique TTS identifier")
    audio_file_path: str = Field(..., description="Path to generated audio file")
    audio_format: AudioFormat = Field(..., description="Audio format")
    duration: float = Field(..., description="Audio duration in seconds")
    file_size: int = Field(..., description="Audio file size in bytes")
    provider: TTSProvider = Field(..., description="Used provider")
    voice: str = Field(..., description="Used voice")
    processing_time: float = Field(..., description="Processing time in seconds")


class VisionVoiceAnalysisRequest(BaseModel):
    """Complete request model for vision-enabled voice analysis"""
    patient_id: UUID = Field(..., description="Patient identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    image_file: Optional[str] = Field(None, description="Path to image file")
    voice_query_file: Optional[str] = Field(None, description="Path to voice query file")
    text_query: Optional[str] = Field(None, description="Text query as alternative to voice")
    vision_provider: VisionModelProvider = Field(default=VisionModelProvider.GROQ, description="Vision model provider")
    vision_model: str = Field(default="llava-3.1-8b-instant", description="Vision model to use")
    tts_provider: TTSProvider = Field(default=TTSProvider.EDGE_TTS, description="TTS provider")
    tts_voice: str = Field(default="en-US-JennyNeural", description="TTS voice")
    audio_output_format: AudioFormat = Field(default=AudioFormat.MP3, description="Output audio format")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    priority: int = Field(default=1, description="Processing priority")
    urgency_level: int = Field(default=1, description="Urgency level")


class VisionVoiceAnalysisResponse(BaseModel):
    """Complete response model for vision-enabled voice analysis"""
    analysis_id: UUID = Field(..., description="Unique analysis identifier")
    patient_id: UUID = Field(..., description="Patient identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    # Image processing results
    image_upload: Optional[ImageUploadResponse] = Field(None, description="Image upload results")
    
    # Speech-to-text results
    speech_to_text: Optional[SpeechToTextResponse] = Field(None, description="Speech-to-text results")
    
    # Vision analysis results
    vision_analysis: Optional[VisionAnalysisResponse] = Field(None, description="Vision analysis results")
    
    # Text-to-speech results
    text_to_speech: Optional[TextToSpeechResponse] = Field(None, description="Text-to-speech results")
    
    # Processing metadata
    processing_start_time: datetime = Field(..., description="Processing start time")
    processing_end_time: datetime = Field(..., description="Processing end time")
    total_processing_time: float = Field(..., description="Total processing time in seconds")
    status: str = Field(..., description="Overall processing status")
    error_message: Optional[str] = Field(None, description="Error message if any")
    
    # Cost tracking
    total_cost: Optional[float] = Field(None, description="Total API cost in USD")
    cost_breakdown: Optional[Dict[str, float]] = Field(None, description="Cost breakdown by service")


class VisionAnalysisSession(BaseModel):
    """Session model for tracking vision analysis sessions"""
    session_id: UUID = Field(..., description="Session identifier")
    patient_id: UUID = Field(..., description="Patient identifier")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity time")
    total_analyses: int = Field(default=0, description="Total analyses in session")
    total_cost: float = Field(default=0.0, description="Total cost for session")
    status: str = Field(default="active", description="Session status")


class VisionAnalysisHistory(BaseModel):
    """History model for tracking vision analysis history"""
    analysis_id: UUID = Field(..., description="Analysis identifier")
    patient_id: UUID = Field(..., description="Patient identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    query: str = Field(..., description="Original query")
    response: str = Field(..., description="Vision model response")
    image_path: Optional[str] = Field(None, description="Path to analyzed image")
    audio_response_path: Optional[str] = Field(None, description="Path to audio response")
    created_at: datetime = Field(..., description="Analysis creation time")
    processing_time: float = Field(..., description="Processing time")
    cost: float = Field(..., description="Analysis cost")
    provider: VisionModelProvider = Field(..., description="Used provider")
    model: str = Field(..., description="Used model")


class VisionAnalysisStats(BaseModel):
    """Statistics model for vision analysis"""
    total_analyses: int = Field(..., description="Total number of analyses")
    total_cost: float = Field(..., description="Total cost")
    average_processing_time: float = Field(..., description="Average processing time")
    success_rate: float = Field(..., description="Success rate percentage")
    provider_usage: Dict[str, int] = Field(..., description="Usage by provider")
    model_usage: Dict[str, int] = Field(..., description="Usage by model")
    daily_analyses: Dict[str, int] = Field(..., description="Daily analysis counts")
    cost_by_provider: Dict[str, float] = Field(..., description="Cost breakdown by provider") 