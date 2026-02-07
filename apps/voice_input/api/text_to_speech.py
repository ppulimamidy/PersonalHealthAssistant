"""
Text-to-Speech API
API endpoints for text-to-speech synthesis.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Form, Body, BackgroundTasks
from fastapi.responses import FileResponse
import os
import uuid

from ..models.text_to_speech import (
    TextToSpeechRequest,
    TextToSpeechResult,
    VoiceProfile,
    VoiceType,
    EmotionType,
    SpeechRate,
    PitchLevel,
    TTSPreviewRequest,
    TTSBatchRequest,
    TTSBatchResult
)
from ..services.text_to_speech_service import TextToSpeechService
from common.utils.logging import get_logger

logger = get_logger(__name__)

text_to_speech_router = APIRouter(prefix="/text-to-speech", tags=["Text-to-Speech"])

# Initialize service
tts_service = TextToSpeechService()


@text_to_speech_router.post("/synthesize", response_model=TextToSpeechResult)
async def synthesize_speech(
    background_tasks: BackgroundTasks,
    request: TextToSpeechRequest
):
    """
    Synthesize speech from text
    
    - **text**: Text to synthesize
    - **voice_id**: Voice ID to use (optional)
    - **language**: Language code (default: en)
    - **voice_type**: Type of voice synthesis
    - **emotion**: Emotional expression
    - **speech_rate**: Speech rate
    - **pitch_level**: Pitch level
    - **volume**: Volume level (0.0-2.0)
    - **sample_rate**: Audio sample rate
    - **format**: Output audio format
    - **ssml**: Whether text is SSML markup
    """
    try:
        logger.info(f"Synthesizing speech for text: {request.text[:50]}...")
        
        # Synthesize speech
        result = await tts_service.synthesize_speech(request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error synthesizing speech: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error synthesizing speech: {str(e)}")


@text_to_speech_router.post("/synthesize-simple")
async def synthesize_speech_simple(
    text: str = Form(...),
    voice_id: Optional[str] = Form(None),
    language: str = Form("en"),
    emotion: EmotionType = Form(EmotionType.NEUTRAL),
    speech_rate: SpeechRate = Form(SpeechRate.NORMAL),
    pitch_level: PitchLevel = Form(PitchLevel.NORMAL),
    volume: float = Form(1.0)
):
    """
    Simple text-to-speech synthesis with form data
    
    - **text**: Text to synthesize
    - **voice_id**: Voice ID to use (optional)
    - **language**: Language code
    - **emotion**: Emotional expression
    - **speech_rate**: Speech rate
    - **pitch_level**: Pitch level
    - **volume**: Volume level
    """
    try:
        logger.info(f"Simple synthesis for text: {text[:50]}...")
        
        # Create request
        request = TextToSpeechRequest(
            text=text,
            voice_id=voice_id,
            language=language,
            emotion=emotion,
            speech_rate=speech_rate,
            pitch_level=pitch_level,
            volume=volume
        )
        
        # Synthesize speech
        result = await tts_service.synthesize_speech(request)
        
        # Return audio file
        if result.synthesis_successful and os.path.exists(result.audio_file_path):
            return FileResponse(
                result.audio_file_path,
                media_type=f"audio/{result.audio_format}",
                filename=f"speech_{result.synthesis_id}.{result.audio_format}"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate audio file")
        
    except Exception as e:
        logger.error(f"Error in simple synthesis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error synthesizing speech: {str(e)}")


@text_to_speech_router.get("/audio/{synthesis_id}")
async def get_synthesized_audio(synthesis_id: str):
    """
    Get synthesized audio file
    
    - **synthesis_id**: Synthesis result identifier
    """
    try:
        # This would fetch from database in production
        # For now, return a mock file
        mock_audio_path = "/tmp/mock_tts_audio.wav"
        
        if not os.path.exists(mock_audio_path):
            # Create a mock audio file for testing
            import wave
            import struct
            import math
            
            with wave.open(mock_audio_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(22050)
                
                # Generate 2 seconds of speech-like audio
                frames = []
                for i in range(44100):  # 2 seconds at 22050 Hz
                    # Create a more speech-like waveform
                    t = i / 22050.0
                    freq = 150 + 50 * math.sin(2 * math.pi * 0.5 * t)  # Varying frequency
                    sample = int(16384 * math.sin(2 * math.pi * freq * t))
                    frames.append(sample)
                
                frame_data = struct.pack('h' * len(frames), *frames)
                wav_file.writeframes(frame_data)
        
        return FileResponse(
            mock_audio_path,
            media_type="audio/wav",
            filename=f"speech_{synthesis_id}.wav"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving audio {synthesis_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="Audio file not found")


@text_to_speech_router.get("/voices", response_model=List[VoiceProfile])
async def get_available_voices():
    """
    Get list of available voices
    """
    try:
        logger.info("Retrieving available voices")
        
        voices = await tts_service.get_available_voices()
        return voices
        
    except Exception as e:
        logger.error(f"Error retrieving voices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving voices: {str(e)}")


@text_to_speech_router.get("/voices/{voice_id}", response_model=VoiceProfile)
async def get_voice_profile(voice_id: str):
    """
    Get specific voice profile
    
    - **voice_id**: Voice identifier
    """
    try:
        logger.info(f"Retrieving voice profile for {voice_id}")
        
        voice_profile = await tts_service.get_voice_profile(voice_id)
        
        if not voice_profile:
            raise HTTPException(status_code=404, detail="Voice not found")
        
        return voice_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving voice profile {voice_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving voice profile: {str(e)}")


@text_to_speech_router.post("/batch-synthesize")
async def batch_synthesize_speech(
    requests: List[TextToSpeechRequest] = Body(...)
):
    """
    Synthesize multiple texts in batch
    
    - **requests**: List of text-to-speech requests
    """
    try:
        logger.info(f"Batch synthesizing {len(requests)} texts")
        
        results = await tts_service.batch_synthesize(requests)
        
        return {
            "batch_id": str(uuid.uuid4()),
            "total_requests": len(requests),
            "successful_syntheses": len([r for r in results if r.synthesis_successful]),
            "failed_syntheses": len([r for r in results if not r.synthesis_successful]),
            "results": [
                {
                    "synthesis_id": str(r.synthesis_id),
                    "text": r.text[:100] + "..." if len(r.text) > 100 else r.text,
                    "voice_id": r.voice_id,
                    "language": r.language,
                    "emotion": r.emotion,
                    "audio_duration": r.audio_duration,
                    "quality_score": r.quality_score,
                    "success": r.synthesis_successful
                }
                for r in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in batch synthesis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in batch synthesis: {str(e)}")


@text_to_speech_router.post("/preview")
async def preview_speech(
    text: str = Form(...),
    voice_id: Optional[str] = Form(None),
    language: str = Form("en"),
    emotion: EmotionType = Form(EmotionType.NEUTRAL)
):
    """
    Generate a short preview of speech synthesis
    
    - **text**: Text to preview (will be truncated if too long)
    - **voice_id**: Voice ID to use (optional)
    - **language**: Language code
    - **emotion**: Emotional expression
    """
    try:
        logger.info("Generating speech preview")
        
        # Truncate text for preview (max 100 characters)
        preview_text = text[:100] + "..." if len(text) > 100 else text
        
        # Create request
        request = TextToSpeechRequest(
            text=preview_text,
            voice_id=voice_id,
            language=language,
            emotion=emotion,
            speech_rate=SpeechRate.NORMAL,
            pitch_level=PitchLevel.NORMAL,
            volume=1.0,
            format="wav"
        )
        
        # Synthesize speech
        result = await tts_service.synthesize_speech(request)
        
        # Return audio file
        if result.synthesis_successful and os.path.exists(result.audio_file_path):
            return FileResponse(
                result.audio_file_path,
                media_type="audio/wav",
                filename=f"preview_{result.synthesis_id}.wav"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate preview")
        
    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")


@text_to_speech_router.get("/capabilities")
async def get_tts_capabilities():
    """
    Get text-to-speech service capabilities
    """
    try:
        logger.info("Retrieving TTS capabilities")
        
        capabilities = {
            "service": "text-to-speech",
            "engines": {
                "edge_tts": {
                    "available": "edge_tts" in tts_service.engines,
                    "description": "Microsoft Edge TTS with neural voices",
                    "languages": ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR", "ru-RU", "zh-CN", "ja-JP", "ko-KR"],
                    "voice_types": ["neural"]
                },
                "gtts": {
                    "available": "gtts" in tts_service.engines,
                    "description": "Google Text-to-Speech",
                    "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"],
                    "voice_types": ["concatenative"]
                },
                "pyttsx3": {
                    "available": "pyttsx3" in tts_service.engines,
                    "description": "Offline text-to-speech",
                    "languages": ["en", "es", "fr", "de", "it", "pt"],
                    "voice_types": ["concatenative"]
                }
            },
            "features": {
                "ssml_support": True,
                "emotion_control": True,
                "prosody_control": True,
                "batch_processing": True,
                "preview_generation": True
            },
            "supported_formats": ["wav", "mp3", "ogg", "flac"],
            "quality_metrics": ["naturalness", "intelligibility", "expressiveness"],
            "voice_profiles": len(tts_service.voice_profiles)
        }
        
        return capabilities
        
    except Exception as e:
        logger.error(f"Error retrieving capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving capabilities: {str(e)}")


@text_to_speech_router.post("/test-voice")
async def test_voice(
    voice_id: str = Form(...),
    test_text: str = Form("Hello, this is a test of the text-to-speech system.")
):
    """
    Test a specific voice with sample text
    
    - **voice_id**: Voice ID to test
    - **test_text**: Text to use for testing
    """
    try:
        logger.info(f"Testing voice {voice_id}")
        
        # Get voice profile
        voice_profile = await tts_service.get_voice_profile(voice_id)
        
        if not voice_profile:
            raise HTTPException(status_code=404, detail="Voice not found")
        
        # Create test request
        request = TextToSpeechRequest(
            text=test_text,
            voice_id=voice_id,
            language=voice_profile.language,
            emotion=EmotionType.NEUTRAL,
            speech_rate=SpeechRate.NORMAL,
            pitch_level=PitchLevel.NORMAL,
            volume=1.0,
            format="wav"
        )
        
        # Synthesize speech
        result = await tts_service.synthesize_speech(request)
        
        # Return test results
        return {
            "voice_id": voice_id,
            "voice_name": voice_profile.voice_name,
            "test_text": test_text,
            "synthesis_successful": result.synthesis_successful,
            "audio_duration": result.audio_duration,
            "quality_score": result.quality_score,
            "naturalness_score": result.naturalness_score,
            "intelligibility_score": result.intelligibility_score,
            "processing_time": result.processing_time,
            "audio_file_available": os.path.exists(result.audio_file_path) if result.audio_file_path else False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing voice {voice_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error testing voice: {str(e)}") 