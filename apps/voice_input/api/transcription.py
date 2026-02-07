"""
Transcription API
API endpoints for speech-to-text transcription.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
import os
import tempfile
import uuid
import traceback

from ..models.transcription import (
    TranscriptionResult,
    TranscriptionSegment,
    TranscriptionEnhancement
)
from ..services.transcription_service import TranscriptionService
from ..services.voice_processing_service import VoiceProcessingService
from common.utils.logging import get_logger

logger = get_logger(__name__)

transcription_router = APIRouter(prefix="/transcription", tags=["Transcription"])

# Import service manager
from ..services.service_manager import get_transcription_service, get_voice_processing_service


@transcription_router.post("/transcribe", response_model=TranscriptionResult)
async def transcribe_audio(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    enhance_transcription: bool = Form(True),
    voice_input_id: Optional[UUID] = Form(None)
):
    """
    Transcribe audio file to text
    
    - **audio_file**: Audio file to transcribe
    - **language**: Expected language (optional, will auto-detect if not provided)
    - **enhance_transcription**: Whether to enhance the transcription
    - **voice_input_id**: Associated voice input ID (optional)
    """
    try:
        logger.info(f"Transcribing audio file: {audio_file.filename}")
        
        # Get service instances
        transcription_service = get_transcription_service()
        voice_processor = get_voice_processing_service()
        
        if not transcription_service:
            raise HTTPException(status_code=503, detail="Transcription Service not available")
        
        if not voice_processor:
            raise HTTPException(status_code=503, detail="Voice Processing Service not available")
        
        # Validate audio file
        if not audio_file.filename or not audio_file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.ogg')):
            raise HTTPException(status_code=400, detail="Invalid audio file format")
        
        # Save uploaded file
        temp_file_path = await _save_uploaded_file(audio_file)
        
        # Process audio quality first
        audio_result = await voice_processor.analyze_audio_quality(temp_file_path)
        
        # Transcribe audio
        transcription_result = await transcription_service.transcribe_audio(
            temp_file_path,
            voice_input_id or uuid.uuid4(),
            language
        )
        
        # Enhance transcription if requested
        if enhance_transcription and transcription_result.transcription_successful:
            enhanced_text = await transcription_service.enhance_transcription(
                transcription_result.full_text
            )
            transcription_result.full_text = enhanced_text
        
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return transcription_result
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}\n{traceback.format_exc()}")


@transcription_router.post("/enhance", response_model=TranscriptionEnhancement)
async def enhance_transcription(
    transcription_text: str,
    context: Optional[dict] = None
):
    """
    Enhance existing transcription
    
    - **transcription_text**: Original transcription text
    - **context**: Additional context for enhancement
    """
    try:
        logger.info("Enhancing transcription")
        
        # Enhance transcription
        enhanced_text = await transcription_service.enhance_transcription(
            transcription_text,
            context
        )
        
        # Calculate corrections (simplified)
        corrections = []
        if enhanced_text != transcription_text:
            corrections.append({
                "original": transcription_text,
                "enhanced": enhanced_text,
                "type": "general_improvement"
            })
        
        return TranscriptionEnhancement(
            original_transcription=transcription_text,
            enhanced_transcription=enhanced_text,
            corrections_applied=corrections,
            enhancement_score=0.8 if corrections else 1.0,
            processing_time=0.1,
            enhancement_metadata={"method": "rule_based"}
        )
        
    except Exception as e:
        logger.error(f"Error enhancing transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enhancing transcription: {str(e)}")


@transcription_router.post("/translate")
async def translate_transcription(
    transcription_text: str,
    source_language: str,
    target_language: str = "en"
):
    """
    Translate transcription to target language
    
    - **transcription_text**: Text to translate
    - **source_language**: Source language code
    - **target_language**: Target language code (default: English)
    """
    try:
        logger.info(f"Translating transcription from {source_language} to {target_language}")
        
        # Translate text
        translated_text = await transcription_service.translate_text(
            transcription_text,
            source_language,
            target_language
        )
        
        return {
            "original_text": transcription_text,
            "translated_text": translated_text,
            "source_language": source_language,
            "target_language": target_language,
            "translation_successful": True
        }
        
    except Exception as e:
        logger.error(f"Error translating transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error translating transcription: {str(e)}")


@transcription_router.post("/detect-language")
async def detect_language(transcription_text: str):
    """
    Detect language of transcription
    
    - **transcription_text**: Text to analyze
    """
    try:
        logger.info("Detecting language of transcription")
        
        # Detect language
        language_scores = await transcription_service.detect_language(transcription_text)
        
        # Get primary language
        primary_language = max(language_scores.items(), key=lambda x: x[1])
        
        return {
            "text": transcription_text,
            "detected_language": primary_language[0],
            "confidence": primary_language[1],
            "all_languages": language_scores
        }
        
    except Exception as e:
        logger.error(f"Error detecting language: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error detecting language: {str(e)}")


@transcription_router.post("/extract-keywords")
async def extract_keywords(
    transcription_text: str,
    domain: str = "general"
):
    """
    Extract keywords from transcription
    
    - **transcription_text**: Text to analyze
    - **domain**: Domain for keyword extraction (health, general, etc.)
    """
    try:
        logger.info(f"Extracting keywords from transcription (domain: {domain})")
        
        # Extract keywords
        keywords = await transcription_service.extract_keywords(transcription_text, domain)
        
        return {
            "text": transcription_text,
            "domain": domain,
            "keywords": keywords,
            "keyword_count": len(keywords)
        }
        
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting keywords: {str(e)}")


@transcription_router.get("/segments/{transcription_id}")
async def get_transcription_segments(transcription_id: UUID):
    """
    Get transcription segments
    
    - **transcription_id**: Transcription identifier
    """
    try:
        # This would fetch from database in production
        # For now, return mock data
        segments = [
            TranscriptionSegment(
                start_time=0.0,
                end_time=2.5,
                text="Hello, I have",
                confidence=0.95,
                speaker_id="speaker_1",
                language="en"
            ),
            TranscriptionSegment(
                start_time=2.5,
                end_time=5.0,
                text="a headache today",
                confidence=0.92,
                speaker_id="speaker_1",
                language="en"
            )
        ]
        
        return {
            "transcription_id": transcription_id,
            "segments": segments,
            "total_segments": len(segments)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving transcription segments {transcription_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="Transcription segments not found")


@transcription_router.post("/batch-transcribe")
async def batch_transcribe_audio(
    background_tasks: BackgroundTasks,
    audio_files: List[UploadFile] = File(...),
    language: Optional[str] = Form(None),
    enhance_transcription: bool = Form(True)
):
    """
    Transcribe multiple audio files in batch
    
    - **audio_files**: List of audio files to transcribe
    - **language**: Expected language (optional)
    - **enhance_transcription**: Whether to enhance transcriptions
    """
    try:
        logger.info(f"Batch transcribing {len(audio_files)} audio files")
        
        results = []
        
        for audio_file in audio_files:
            try:
                # Validate audio file
                if not audio_file.filename or not audio_file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.ogg')):
                    results.append({
                        "filename": audio_file.filename,
                        "success": False,
                        "error": "Invalid audio file format"
                    })
                    continue
                
                # Save uploaded file
                temp_file_path = await _save_uploaded_file(audio_file)
                
                # Transcribe audio
                transcription_result = await transcription_service.transcribe_audio(
                    temp_file_path,
                    uuid.uuid4(),
                    language
                )
                
                # Enhance transcription if requested
                if enhance_transcription and transcription_result.transcription_successful:
                    enhanced_text = await transcription_service.enhance_transcription(
                        transcription_result.full_text
                    )
                    transcription_result.full_text = enhanced_text
                
                results.append({
                    "filename": audio_file.filename,
                    "success": transcription_result.transcription_successful,
                    "transcription": transcription_result.full_text,
                    "confidence": transcription_result.overall_confidence,
                    "language": transcription_result.detected_language,
                    "processing_time": transcription_result.processing_time
                })
                
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    
            except Exception as e:
                results.append({
                    "filename": audio_file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "batch_id": str(uuid.uuid4()),
            "total_files": len(audio_files),
            "successful_transcriptions": len([r for r in results if r["success"]]),
            "failed_transcriptions": len([r for r in results if not r["success"]]),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in batch transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in batch transcription: {str(e)}")


async def _save_uploaded_file(upload_file: UploadFile) -> str:
    """Save uploaded file to temporary location"""
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(upload_file.filename)[1])
        temp_file_path = temp_file.name
        
        # Write uploaded content
        content = await upload_file.read()
        temp_file.write(content)
        temp_file.close()
        
        logger.info(f"Saved uploaded file to {temp_file_path}")
        return temp_file_path
        
    except Exception as e:
        logger.error(f"Error saving uploaded file: {str(e)}")
        raise 