"""
Voice Input Service Configuration
Configuration settings for the voice input service.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Service Configuration
    SERVICE_NAME: str = "voice-input-service"
    SERVICE_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8004, env="PORT")
    
    # Database Configuration
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION_MINUTES: int = Field(default=60, env="JWT_EXPIRATION_MINUTES")
    
    # CORS Configuration
    ALLOWED_HOSTS: List[str] = Field(default=["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    
    # Audio Processing Configuration
    MAX_AUDIO_DURATION: int = Field(default=300, env="MAX_AUDIO_DURATION")  # 5 minutes
    SUPPORTED_AUDIO_FORMATS: List[str] = Field(
        default=["wav", "mp3", "m4a", "flac", "ogg"], 
        env="SUPPORTED_AUDIO_FORMATS"
    )
    MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    
    # Transcription Configuration
    WHISPER_MODEL: str = Field(default="base", env="WHISPER_MODEL")
    SUPPORTED_LANGUAGES: List[str] = Field(
        default=["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"],
        env="SUPPORTED_LANGUAGES"
    )
    
    # Intent Recognition Configuration
    SPACY_MODEL: str = Field(default="en_core_web_sm", env="SPACY_MODEL")
    CONFIDENCE_THRESHOLD: float = Field(default=0.7, env="CONFIDENCE_THRESHOLD")
    
    # Multi-Modal Configuration
    FUSION_STRATEGY: str = Field(default="late", env="FUSION_STRATEGY")
    MAX_SENSOR_INPUTS: int = Field(default=10, env="MAX_SENSOR_INPUTS")
    
    # Audio Enhancement Configuration
    ENHANCEMENT_METHODS: List[str] = Field(
        default=["normalization", "noise_reduction"],
        env="ENHANCEMENT_METHODS"
    )
    
    # File Storage Configuration
    UPLOAD_DIR: str = Field(default="/app/uploads", env="UPLOAD_DIR")
    TEMP_DIR: str = Field(default="/tmp", env="TEMP_DIR")
    
    # Vision Analysis Configuration
    GROQ_API_KEY: str = Field(..., env="GROQ_API_KEY")
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    VISION_MODEL_DEFAULT: str = Field(default="meta-llama/llama-4-scout-17b-16e-instruct", env="VISION_MODEL_DEFAULT")
    TTS_PROVIDER_DEFAULT: str = Field(default="edge_tts", env="TTS_PROVIDER_DEFAULT")
    TTS_VOICE_DEFAULT: str = Field(default="en-US-JennyNeural", env="TTS_VOICE_DEFAULT")
    
    # Image Processing Configuration
    MAX_IMAGE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_IMAGE_SIZE")  # 10MB
    SUPPORTED_IMAGE_FORMATS: List[str] = Field(
        default=["jpeg", "jpg", "png", "webp", "tiff", "bmp"],
        env="SUPPORTED_IMAGE_FORMATS"
    )
    IMAGE_UPLOAD_DIR: str = Field(default="/app/uploads/images", env="IMAGE_UPLOAD_DIR")
    AUDIO_OUTPUT_DIR: str = Field(default="/app/outputs/vision_analysis", env="AUDIO_OUTPUT_DIR")
    
    # External Service URLs
    AUTH_SERVICE_URL: Optional[str] = Field(default=None, env="AUTH_SERVICE_URL")
    USER_PROFILE_SERVICE_URL: Optional[str] = Field(default=None, env="USER_PROFILE_SERVICE_URL")
    HEALTH_TRACKING_SERVICE_URL: Optional[str] = Field(default=None, env="HEALTH_TRACKING_SERVICE_URL")
    MEDICAL_RECORDS_SERVICE_URL: Optional[str] = Field(default=None, env="MEDICAL_RECORDS_SERVICE_URL")
    AI_INSIGHTS_SERVICE_URL: Optional[str] = Field(default=None, env="AI_INSIGHTS_SERVICE_URL")
    
    # Monitoring Configuration
    PROMETHEUS_ENABLED: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    GRAFANA_ENABLED: bool = Field(default=True, env="GRAFANA_ENABLED")
    
    # Health Check Configuration
    HEALTH_CHECK_INTERVAL: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    HEALTH_CHECK_TIMEOUT: int = Field(default=10, env="HEALTH_CHECK_TIMEOUT")
    HEALTH_CHECK_RETRIES: int = Field(default=3, env="HEALTH_CHECK_RETRIES")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


# Health domain specific configurations
HEALTH_INTENTS = {
    "symptom_report": {
        "priority": 4,
        "requires_action": True,
        "keywords": ["pain", "ache", "hurt", "symptom", "feeling", "unwell"]
    },
    "medication_query": {
        "priority": 2,
        "requires_action": False,
        "keywords": ["medicine", "medication", "pill", "dose", "refill"]
    },
    "appointment_request": {
        "priority": 3,
        "requires_action": True,
        "keywords": ["appointment", "doctor", "visit", "schedule", "see"]
    },
    "emergency_alert": {
        "priority": 5,
        "requires_action": True,
        "keywords": ["emergency", "urgent", "chest pain", "severe", "critical"]
    },
    "wellness_query": {
        "priority": 1,
        "requires_action": False,
        "keywords": ["health", "wellness", "exercise", "diet", "lifestyle"]
    }
}

HEALTH_ENTITIES = {
    "body_part": ["head", "neck", "shoulder", "arm", "chest", "back", "stomach", "leg"],
    "symptom": ["pain", "headache", "fever", "nausea", "fatigue", "cough", "dizziness"],
    "medication": ["aspirin", "ibuprofen", "insulin", "metformin", "antibiotics"],
    "severity": ["mild", "moderate", "severe", "intense", "sharp", "dull"],
    "duration": ["hours", "days", "weeks", "months", "years"],
    "time": ["today", "tomorrow", "morning", "afternoon", "evening", "night"]
}

HEALTH_INDICATORS = {
    "heart_rate": {"normal_range": (60, 100), "unit": "bpm"},
    "blood_pressure": {"normal_range": (90, 140), "unit": "mmHg"},
    "temperature": {"normal_range": (36.1, 37.2), "unit": "°C"},
    "blood_sugar": {"normal_range": (70, 140), "unit": "mg/dL"}
} 