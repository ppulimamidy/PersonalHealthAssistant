"""
Voice Input Service
Handles voice input database operations and business logic.
"""

import os
import tempfile
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import logging

from ..models.voice_input import (
    VoiceInputResponse,
    VoiceInputCreate,
    VoiceInputUpdate,
    InputType,
    InputStatus
)
from common.utils.logging import get_logger

logger = get_logger(__name__)


class VoiceInputService:
    """Service for managing voice input data and operations."""
    
    def __init__(self):
        """Initialize the voice input service."""
        self.mock_data = {}  # In-memory storage for mock data
        self._initialize_mock_data()
        logger.info("Voice Input Service initialized")
    
    def _initialize_mock_data(self):
        """Initialize mock data for testing."""
        now = datetime.utcnow()
        
        # Create some mock voice inputs
        for i in range(10):
            voice_input_id = uuid.uuid4()
            self.mock_data[str(voice_input_id)] = {
                "id": voice_input_id,
                "patient_id": uuid.uuid4(),
                "session_id": f"session_{i+1}",
                "input_type": InputType.VOICE_COMMAND,
                "status": InputStatus.COMPLETED,
                "priority": 1,
                "audio_duration": 10.5 + i,
                "audio_format": "wav",
                "audio_quality_score": 0.85,
                "transcription_text": f"Voice input {i+1} - I have a headache and need to see a doctor",
                "confidence_score": 0.92,
                "language_detected": "en",
                "detected_intent": "symptom_report",
                "entities": {
                    "symptom": {"value": "headache", "confidence": 0.95},
                    "action": {"value": "see doctor", "confidence": 0.88}
                },
                "text_input": None,
                "image_data": None,
                "sensor_data": None,
                "context": f"Patient reporting symptoms - session {i+1}",
                "processing_time": 2.5 + i * 0.1,
                "processing_errors": [],
                "processing_metadata": {
                    "model_version": "1.0.0",
                    "processing_steps": ["audio_analysis", "transcription", "intent_recognition"]
                },
                "created_at": now - timedelta(hours=i+1),
                "updated_at": now - timedelta(minutes=i*30),
                "processed_at": now - timedelta(minutes=i*30)
            }
    
    async def create_voice_input(self, voice_input_data: VoiceInputCreate, audio_file_path: str) -> VoiceInputResponse:
        """
        Create a new voice input record.
        
        Args:
            voice_input_data: Voice input creation data
            audio_file_path: Path to the audio file
            
        Returns:
            VoiceInputResponse object
        """
        try:
            voice_input_id = uuid.uuid4()
            now = datetime.utcnow()
            
            # Create voice input record
            voice_input = {
                "id": voice_input_id,
                "patient_id": voice_input_data.patient_id,
                "session_id": voice_input_data.session_id or f"session_{voice_input_id}",
                "input_type": voice_input_data.input_type,
                "status": InputStatus.PROCESSING,
                "priority": voice_input_data.priority,
                "audio_duration": 0.0,  # Will be updated after processing
                "audio_format": os.path.splitext(audio_file_path)[1][1:],
                "audio_quality_score": 0.0,  # Will be updated after processing
                "transcription_text": "",
                "confidence_score": 0.0,
                "language_detected": "unknown",
                "detected_intent": "",
                "entities": {},
                "text_input": voice_input_data.text_input,
                "image_data": None,
                "sensor_data": None,
                "context": voice_input_data.context,
                "processing_time": 0.0,
                "processing_errors": [],
                "processing_metadata": {},
                "created_at": now,
                "updated_at": now,
                "processed_at": None
            }
            
            # Store in mock database
            self.mock_data[str(voice_input_id)] = voice_input
            
            logger.info(f"Created voice input {voice_input_id}")
            return VoiceInputResponse(**voice_input)
            
        except Exception as e:
            logger.error(f"Error creating voice input: {str(e)}")
            raise
    
    async def get_voice_input(self, voice_input_id: uuid.UUID) -> Optional[VoiceInputResponse]:
        """
        Get voice input by ID.
        
        Args:
            voice_input_id: Voice input identifier
            
        Returns:
            VoiceInputResponse object or None
        """
        try:
            voice_input_data = self.mock_data.get(str(voice_input_id))
            if voice_input_data:
                return VoiceInputResponse(**voice_input_data)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving voice input {voice_input_id}: {str(e)}")
            raise
    
    async def get_patient_voice_inputs(
        self, 
        patient_id: uuid.UUID, 
        limit: int = 10, 
        offset: int = 0,
        status: Optional[InputStatus] = None
    ) -> List[VoiceInputResponse]:
        """
        Get voice inputs for a patient.
        
        Args:
            patient_id: Patient identifier
            limit: Maximum number of results
            offset: Number of results to skip
            status: Filter by status
            
        Returns:
            List of VoiceInputResponse objects
        """
        try:
            # Filter by patient_id and status
            filtered_inputs = []
            for voice_input_data in self.mock_data.values():
                if voice_input_data["patient_id"] == patient_id:
                    if status is None or voice_input_data["status"] == status:
                        filtered_inputs.append(voice_input_data)
            
            # Sort by created_at (newest first)
            filtered_inputs.sort(key=lambda x: x["created_at"], reverse=True)
            
            # Apply pagination
            paginated_inputs = filtered_inputs[offset:offset + limit]
            
            return [VoiceInputResponse(**input_data) for input_data in paginated_inputs]
            
        except Exception as e:
            logger.error(f"Error retrieving voice inputs for patient {patient_id}: {str(e)}")
            raise
    
    async def update_voice_input(
        self, 
        voice_input_id: uuid.UUID, 
        voice_input_update: VoiceInputUpdate
    ) -> Optional[VoiceInputResponse]:
        """
        Update voice input.
        
        Args:
            voice_input_id: Voice input identifier
            voice_input_update: Updated voice input data
            
        Returns:
            Updated VoiceInputResponse object or None
        """
        try:
            voice_input_data = self.mock_data.get(str(voice_input_id))
            if not voice_input_data:
                return None
            
            # Update fields
            update_data = voice_input_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                voice_input_data[field] = value
            
            voice_input_data["updated_at"] = datetime.utcnow()
            
            logger.info(f"Updated voice input {voice_input_id}")
            return VoiceInputResponse(**voice_input_data)
            
        except Exception as e:
            logger.error(f"Error updating voice input {voice_input_id}: {str(e)}")
            raise
    
    async def delete_voice_input(self, voice_input_id: uuid.UUID) -> bool:
        """
        Delete voice input.
        
        Args:
            voice_input_id: Voice input identifier
            
        Returns:
            True if deleted, False if not found
        """
        try:
            if str(voice_input_id) in self.mock_data:
                del self.mock_data[str(voice_input_id)]
                logger.info(f"Deleted voice input {voice_input_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting voice input {voice_input_id}: {str(e)}")
            raise
    
    async def update_processing_results(
        self,
        voice_input_id: uuid.UUID,
        transcription_text: str = None,
        confidence_score: float = None,
        language_detected: str = None,
        detected_intent: str = None,
        entities: Dict[str, Any] = None,
        processing_time: float = None,
        processing_errors: List[str] = None,
        processing_metadata: Dict = None
    ) -> Optional[VoiceInputResponse]:
        """
        Update voice input with processing results.
        
        Args:
            voice_input_id: Voice input identifier
            transcription_text: Transcribed text
            confidence_score: Confidence score
            language_detected: Detected language
            detected_intent: Detected intent
            entities: Extracted entities
            processing_time: Processing time
            processing_errors: Processing errors
            processing_metadata: Processing metadata
            
        Returns:
            Updated VoiceInputResponse object or None
        """
        try:
            voice_input_data = self.mock_data.get(str(voice_input_id))
            if not voice_input_data:
                return None
            
            # Update processing results
            if transcription_text is not None:
                voice_input_data["transcription_text"] = transcription_text
            if confidence_score is not None:
                voice_input_data["confidence_score"] = confidence_score
            if language_detected is not None:
                voice_input_data["language_detected"] = language_detected
            if detected_intent is not None:
                voice_input_data["detected_intent"] = detected_intent
            if entities is not None:
                voice_input_data["entities"] = entities
            if processing_time is not None:
                voice_input_data["processing_time"] = processing_time
            if processing_errors is not None:
                voice_input_data["processing_errors"] = processing_errors
            if processing_metadata is not None:
                voice_input_data["processing_metadata"] = processing_metadata
            
            # Update status and timestamps
            voice_input_data["status"] = InputStatus.COMPLETED
            voice_input_data["updated_at"] = datetime.utcnow()
            voice_input_data["processed_at"] = datetime.utcnow()
            
            logger.info(f"Updated processing results for voice input {voice_input_id}")
            return VoiceInputResponse(**voice_input_data)
            
        except Exception as e:
            logger.error(f"Error updating processing results for voice input {voice_input_id}: {str(e)}")
            raise 