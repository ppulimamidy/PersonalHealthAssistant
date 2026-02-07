"""
Voice Input API
API endpoints for voice input processing and management.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends
from fastapi.responses import FileResponse
import os
import tempfile
import uuid

from ..models.voice_input import (
    VoiceInputCreate, 
    VoiceInputUpdate, 
    VoiceInputResponse,
    InputType,
    InputStatus
)
from ..services.voice_processing_service import VoiceProcessingService
from ..services.transcription_service import TranscriptionService
from ..services.intent_recognition_service import IntentRecognitionService
from ..services.voice_input_service import VoiceInputService
from common.utils.logging import get_logger

logger = get_logger(__name__)

voice_input_router = APIRouter(prefix="/voice-input", tags=["Voice Input"])

# Initialize services
voice_processor = VoiceProcessingService()
transcription_service = TranscriptionService()
intent_recognition_service = IntentRecognitionService()
voice_input_service = VoiceInputService()


@voice_input_router.post("/upload", response_model=VoiceInputResponse)
async def upload_voice_input(
    background_tasks: BackgroundTasks,
    patient_id: UUID = Form(...),
    session_id: Optional[str] = Form(None),
    input_type: InputType = Form(InputType.VOICE_COMMAND),
    priority: int = Form(1),
    audio_file: UploadFile = File(...),
    text_input: Optional[str] = Form(None),
    context: Optional[str] = Form(None)
):
    """
    Upload and process voice input
    
    - **patient_id**: Patient identifier
    - **session_id**: Session identifier (optional)
    - **input_type**: Type of voice input
    - **priority**: Processing priority
    - **audio_file**: Audio file to upload
    - **text_input**: Additional text input (optional)
    - **context**: Additional context (optional)
    """
    try:
        logger.info(f"Uploading voice input for patient {patient_id}")
        
        # Validate audio file
        if not audio_file.filename or not audio_file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.ogg')):
            raise HTTPException(status_code=400, detail="Invalid audio file format")
        
        # Save uploaded file
        temp_file_path = await _save_uploaded_file(audio_file)
        
        # Create voice input data
        voice_input_data = VoiceInputCreate(
            patient_id=patient_id,
            session_id=session_id,
            input_type=input_type,
            priority=priority,
            text_input=text_input,
            context=context
        )
        
        # Create voice input record
        voice_input = await voice_input_service.create_voice_input(voice_input_data, temp_file_path)
        
        # Process in background
        background_tasks.add_task(
            _process_voice_input_background,
            temp_file_path,
            voice_input.id,
            voice_input_data
        )
        
        return voice_input
        
    except Exception as e:
        logger.error(f"Error uploading voice input: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading voice input: {str(e)}")


@voice_input_router.get("/{voice_input_id}", response_model=VoiceInputResponse)
async def get_voice_input(voice_input_id: UUID):
    """
    Get voice input by ID
    
    - **voice_input_id**: Voice input identifier
    """
    try:
        logger.info(f"Retrieving voice input {voice_input_id}")
        
        voice_input = await voice_input_service.get_voice_input(voice_input_id)
        if not voice_input:
            raise HTTPException(status_code=404, detail="Voice input not found")
        
        return voice_input
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving voice input {voice_input_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving voice input")


@voice_input_router.get("/patient/{patient_id}", response_model=List[VoiceInputResponse])
async def get_patient_voice_inputs(
    patient_id: UUID,
    limit: int = 10,
    offset: int = 0,
    status: Optional[InputStatus] = None
):
    """
    Get voice inputs for a patient
    
    - **patient_id**: Patient identifier
    - **limit**: Maximum number of results
    - **offset**: Number of results to skip
    - **status**: Filter by status
    """
    try:
        logger.info(f"Retrieving voice inputs for patient {patient_id}")
        
        voice_inputs = await voice_input_service.get_patient_voice_inputs(
            patient_id, limit, offset, status
        )
        
        return voice_inputs
        
    except Exception as e:
        logger.error(f"Error retrieving voice inputs for patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving voice inputs")


@voice_input_router.put("/{voice_input_id}", response_model=VoiceInputResponse)
async def update_voice_input(
    voice_input_id: UUID,
    voice_input_update: VoiceInputUpdate
):
    """
    Update voice input
    
    - **voice_input_id**: Voice input identifier
    - **voice_input_update**: Updated voice input data
    """
    try:
        updated_voice_input = await voice_input_service.update_voice_input(
            voice_input_id, voice_input_update
        )
        
        if not updated_voice_input:
            raise HTTPException(status_code=404, detail="Voice input not found")
        
        return updated_voice_input
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating voice input {voice_input_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating voice input")


@voice_input_router.delete("/{voice_input_id}")
async def delete_voice_input(voice_input_id: UUID):
    """
    Delete voice input
    
    - **voice_input_id**: Voice input identifier
    """
    try:
        deleted = await voice_input_service.delete_voice_input(voice_input_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Voice input not found")
        
        return {"message": "Voice input deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting voice input {voice_input_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting voice input")


@voice_input_router.get("/{voice_input_id}/audio")
async def get_voice_input_audio(voice_input_id: UUID):
    """
    Get audio file for voice input
    
    - **voice_input_id**: Voice input identifier
    """
    try:
        # This would fetch audio file path from database in production
        # For now, return a mock file
        mock_audio_path = "/tmp/mock_audio.wav"
        
        if not os.path.exists(mock_audio_path):
            # Create a mock audio file for testing
            import wave
            import struct
            
            with wave.open(mock_audio_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                
                # Generate 1 second of silence
                frames = struct.pack('h' * 16000, *([0] * 16000))
                wav_file.writeframes(frames)
        
        return FileResponse(
            mock_audio_path,
            media_type="audio/wav",
            filename=f"voice_input_{voice_input_id}.wav"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving audio for voice input {voice_input_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="Audio file not found")


@voice_input_router.post("/{voice_input_id}/reprocess")
async def reprocess_voice_input(
    voice_input_id: UUID,
    background_tasks: BackgroundTasks
):
    """
    Reprocess voice input
    
    - **voice_input_id**: Voice input identifier
    """
    try:
        # This would trigger reprocessing in production
        background_tasks.add_task(_reprocess_voice_input_background, voice_input_id)
        
        return {"message": "Voice input reprocessing started"}
        
    except Exception as e:
        logger.error(f"Error reprocessing voice input {voice_input_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error reprocessing voice input")


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


async def _process_voice_input_background(
    audio_file_path: str,
    voice_input_id: uuid.UUID,
    voice_input_data: VoiceInputCreate
):
    """Process voice input in background"""
    try:
        logger.info(f"Processing voice input in background: {audio_file_path}")
        
        # Process audio quality
        audio_result = await voice_processor.analyze_audio_quality(audio_file_path)
        
        # Transcribe audio
        transcription_result = await transcription_service.transcribe_audio(
            audio_file_path,
            voice_input_id
        )
        
        # Recognize intent
        intent_result = await intent_recognition_service.recognize_intent(
            transcription_result.full_text,
            voice_input_id
        )
        
        # Update voice input record with results
        await voice_input_service.update_processing_results(
            voice_input_id,
            transcription_text=transcription_result.full_text,
            confidence_score=transcription_result.overall_confidence,
            language_detected=transcription_result.detected_language,
            detected_intent=intent_result.detected_intent if intent_result else None,
            entities=intent_result.entities if intent_result else [],
            processing_time=transcription_result.processing_time,
            processing_errors=transcription_result.transcription_errors,
            processing_metadata={
                "audio_quality": audio_result.quality_score,
                "transcription_model": transcription_result.transcription_model,
                "intent_confidence": intent_result.confidence_score if intent_result else 0.0
            }
        )
        
        logger.info(f"Completed background processing for voice input {voice_input_id}")
        
        # Clean up temporary file
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)
            
    except Exception as e:
        logger.error(f"Error in background voice input processing: {str(e)}")
        # Update with error information
        try:
            await voice_input_service.update_processing_results(
                voice_input_id,
                processing_errors=[str(e)],
                processing_metadata={"error": str(e)}
            )
        except Exception as update_error:
            logger.error(f"Error updating voice input with error: {str(update_error)}")


async def _reprocess_voice_input_background(voice_input_id: UUID):
    """Reprocess voice input in background"""
    try:
        logger.info(f"Reprocessing voice input {voice_input_id} in background")
        
        # This would fetch the voice input from database and reprocess it
        # For now, just log the action
        
        logger.info(f"Completed reprocessing for voice input {voice_input_id}")
        
    except Exception as e:
        logger.error(f"Error in background voice input reprocessing: {str(e)}") 