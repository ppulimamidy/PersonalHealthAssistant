"""
Voice Input Service Models
Data models for multi-modal voice input processing.
"""

from .voice_input import VoiceInput, VoiceInputCreate, VoiceInputUpdate, VoiceInputResponse
from .audio_processing import AudioProcessingResult, AudioQualityMetrics
from .transcription import TranscriptionResult, TranscriptionSegment
from .intent_recognition import IntentRecognitionResult, Intent, Entity
from .multi_modal import MultiModalInput, MultiModalResult, InputModality
from .text_to_speech import (
    TextToSpeechRequest, 
    TextToSpeechResult, 
    VoiceProfile, 
    SpeechSegment,
    VoiceType, 
    EmotionType, 
    SpeechRate, 
    PitchLevel
)

__all__ = [
    # Voice Input Models
    "VoiceInput",
    "VoiceInputCreate", 
    "VoiceInputUpdate",
    "VoiceInputResponse",
    
    # Audio Processing Models
    "AudioProcessingResult",
    "AudioQualityMetrics",
    
    # Transcription Models
    "TranscriptionResult",
    "TranscriptionSegment",
    
    # Intent Recognition Models
    "IntentRecognitionResult",
    "Intent",
    "Entity",
    
    # Multi-Modal Models
    "MultiModalInput",
    "MultiModalResult",
    "InputModality",
    
    # Text-to-Speech Models
    "TextToSpeechRequest",
    "TextToSpeechResult",
    "VoiceProfile",
    "SpeechSegment",
    "VoiceType",
    "EmotionType",
    "SpeechRate",
    "PitchLevel"
] 