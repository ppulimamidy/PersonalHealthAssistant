"""
Service Manager
Manages global service instances to avoid circular imports.
"""

from typing import Optional
from ..services.vision_analysis_service import VisionAnalysisService
from ..services.transcription_service import TranscriptionService
from ..services.voice_processing_service import VoiceProcessingService
from common.utils.logging import get_logger

logger = get_logger(__name__)

# Global service instances
vision_analysis_service: Optional[VisionAnalysisService] = None
transcription_service: Optional[TranscriptionService] = None
voice_processing_service: Optional[VoiceProcessingService] = None


async def initialize_services():
    """Initialize all services"""
    global vision_analysis_service, transcription_service, voice_processing_service
    
    try:
        # Initialize vision analysis service
        vision_analysis_service = VisionAnalysisService()
        await vision_analysis_service.initialize()
        logger.info("✅ Vision Analysis Service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Vision Analysis Service: {e}")
        vision_analysis_service = None
    
    try:
        # Initialize transcription service
        transcription_service = TranscriptionService()
        await transcription_service.initialize_models()
        logger.info("✅ Transcription Service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Transcription Service: {e}")
        transcription_service = None
    
    try:
        # Initialize voice processing service
        voice_processing_service = VoiceProcessingService()
        logger.info("✅ Voice Processing Service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Voice Processing Service: {e}")
        voice_processing_service = None


async def cleanup_services():
    """Cleanup all services"""
    global vision_analysis_service, transcription_service, voice_processing_service
    
    if vision_analysis_service:
        try:
            await vision_analysis_service.cleanup()
            logger.info("✅ Vision Analysis Service cleaned up")
        except Exception as e:
            logger.error(f"❌ Error cleaning up Vision Analysis Service: {e}")
    
    if transcription_service:
        try:
            # Transcription service doesn't have a cleanup method, just set to None
            transcription_service = None
            logger.info("✅ Transcription Service cleaned up")
        except Exception as e:
            logger.error(f"❌ Error cleaning up Transcription Service: {e}")


def get_vision_analysis_service() -> Optional[VisionAnalysisService]:
    """Get the vision analysis service instance"""
    return vision_analysis_service


def get_transcription_service() -> Optional[TranscriptionService]:
    """Get the transcription service instance"""
    return transcription_service


def get_voice_processing_service() -> Optional[VoiceProcessingService]:
    """Get the voice processing service instance"""
    return voice_processing_service 