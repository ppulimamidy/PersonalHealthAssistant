"""
Voice Input Service Main Application
FastAPI application for multi-modal voice input processing and analysis.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
import sys
import os

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from common.config.settings import get_settings
from common.middleware.auth import auth_middleware, get_current_user
from common.middleware.error_handling import setup_error_handlers
from common.utils.logging import get_logger, setup_logging
from common.database.connection import get_async_db

from apps.voice_input.api import (
    voice_input_router, 
    transcription_router, 
    intent_recognition_router, 
    multi_modal_router, 
    audio_enhancement_router,
    text_to_speech_router,
    vision_analysis_router,
    medical_analysis_router
)

# Ensure logging is set up to write to file
setup_logging(enable_console=True, enable_file=True, enable_json=True)

# Global logger
logger = get_logger("voice_input.main")

# Get settings
settings = get_settings()

# Debug: Print ALLOWED_HOSTS at startup
print(f"[DEBUG] ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🎤 Starting Voice Input Service...")
    
    # Initialize services
    try:
        from apps.voice_input.services.service_manager import initialize_services
        await initialize_services()
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
    
    logger.info("✅ Voice Input Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Voice Input Service...")
    
    # Cleanup services
    try:
        from apps.voice_input.services.service_manager import cleanup_services
        await cleanup_services()
    except Exception as e:
        logger.error(f"❌ Error cleaning up services: {e}")


# Create FastAPI application
app = FastAPI(
    title="Voice Input Service",
    description="Multi-modal voice input processing and analysis for VitaSense",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=settings.ALLOWED_HOSTS
# )

# Setup error handlers
setup_error_handlers(app)

# Include routers
app.include_router(voice_input_router, prefix="/api/v1/voice-input")
app.include_router(transcription_router, prefix="/api/v1/voice-input")
app.include_router(intent_recognition_router, prefix="/api/v1/voice-input")
app.include_router(multi_modal_router, prefix="/api/v1/voice-input")
app.include_router(audio_enhancement_router, prefix="/api/v1/voice-input")
app.include_router(text_to_speech_router, prefix="/api/v1/voice-input")
app.include_router(vision_analysis_router, prefix="/api/v1/voice-input")
app.include_router(medical_analysis_router, prefix="/api/v1/voice-input")


@app.middleware("http")
async def log_request_headers(request: Request, call_next):
    print(f"[DEBUG] Incoming request: {request.method} {request.url}")
    for k, v in request.headers.items():
        print(f"[DEBUG] Header: {k}: {v}")
    response = await call_next(request)
    return response


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Voice Input Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Multi-modal voice input processing and analysis",
        "features": [
            "Voice input processing and quality analysis",
            "Speech-to-text transcription",
            "Text-to-speech synthesis",
            "Intent recognition and entity extraction",
            "Multi-modal input fusion",
            "Audio enhancement and noise reduction",
            "Vision-enabled voice analysis with image upload",
            "GROQ and OpenAI vision model integration",
            "Complete vision-to-speech workflow"
        ]
    }


@app.get("/health")
async def health_check(request: Request):
    # Log the Host header for debugging
    host_header = request.headers.get("host")
    print(f"[DEBUG] /health Host header: {host_header}")
    return {
        "service": "voice_input",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "voice_input": "/api/v1/voice-input/voice-input",
            "transcription": "/api/v1/voice-input/transcription",
            "text_to_speech": "/api/v1/voice-input/text-to-speech",
            "intent_recognition": "/api/v1/voice-input/intent",
            "multi_modal": "/api/v1/voice-input/multi-modal",
            "audio_enhancement": "/api/v1/voice-input/audio-enhancement",
            "vision_analysis": "/api/v1/voice-input/vision-analysis"
        }
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {
        "service": "voice_input",
        "status": "ready",
        "version": "1.0.0"
    }


@app.get("/capabilities")
async def get_capabilities():
    """Get service capabilities."""
    return {
        "service": "voice_input",
        "capabilities": {
            "voice_processing": {
                "supported_formats": [".wav", ".mp3", ".m4a", ".flac", ".ogg"],
                "max_duration": "5 minutes",
                "quality_analysis": True,
                "noise_reduction": True
            },
            "transcription": {
                "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"],
                "speaker_diarization": False,
                "enhancement": True,
                "translation": True
            },
            "text_to_speech": {
                "languages": ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR", "ru-RU", "zh-CN", "ja-JP", "ko-KR"],
                "voice_types": ["neural", "concatenative", "hmm", "dnn", "wavenet", "tacotron"],
                "emotions": ["neutral", "happy", "sad", "angry", "excited", "calm", "concerned", "professional"],
                "ssml_support": True,
                "prosody_control": True
            },
            "intent_recognition": {
                "health_domain": True,
                "entity_extraction": True,
                "sentiment_analysis": True,
                "urgency_detection": True
            },
            "multi_modal": {
                "voice": True,
                "text": True,
                "image": True,
                "sensor_data": True,
                "fusion_strategies": ["early", "late", "hybrid"]
            },
            "audio_enhancement": {
                "normalization": True,
                "noise_reduction": True,
                "filtering": True,
                "compression": True,
                "format_conversion": True
            },
            "vision_analysis": {
                "image_upload": True,
                "supported_formats": ["jpeg", "jpg", "png", "webp", "tiff", "bmp"],
                "max_image_size": "10MB",
                "vision_providers": ["groq", "openai"],
                "vision_models": {
                    "groq": ["llava-3.1-8b-instant", "llava-3.1-8b", "llava-3.1-70b"],
                    "openai": ["gpt-4-vision-preview", "gpt-4o", "gpt-4o-mini"]
                },
                "medical_focus": True,
                "domain_validation": True
            }
        }
    }


if __name__ == "__main__":
    voice_settings = VoiceInputSettings()
    uvicorn.run(
        "main:app",
        host=voice_settings.HOST,
        port=voice_settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 