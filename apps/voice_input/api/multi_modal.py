"""
Multi-Modal API
API endpoints for processing multi-modal inputs.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from pydantic import BaseModel

from ..models.multi_modal import (
    MultiModalInput,
    MultiModalResult,
    VoiceInput as MultiModalVoiceInput,
    TextInput,
    ImageInput,
    SensorInput
)
from ..services.multi_modal_service import MultiModalService
from common.utils.logging import get_logger

logger = get_logger(__name__)

multi_modal_router = APIRouter(prefix="/multi-modal", tags=["Multi-Modal"])

# Initialize service
multi_modal_service = MultiModalService()


class MultiModalRequest(BaseModel):
    """Request model for multi-modal processing"""
    patient_id: UUID
    session_id: Optional[str] = None
    text_input: Optional[str] = None
    sensor_data: Optional[List[Dict[str, Any]]] = None
    context: Optional[Dict[str, Any]] = None
    priority: int = 1
    urgency_level: int = 1


@multi_modal_router.post("/process", response_model=MultiModalResult)
async def process_multi_modal_input(
    request: MultiModalRequest,
    voice_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None)
):
    """
    Process multi-modal input combining voice, text, image, and sensor data
    
    - **request**: Multi-modal request data
    - **voice_file**: Voice input file (optional)
    - **image_file**: Image input file (optional)
    """
    try:
        logger.info(f"Processing multi-modal input for patient {request.patient_id}")
        
        # Prepare multi-modal input
        multi_modal_input = MultiModalInput(
            patient_id=request.patient_id,
            session_id=request.session_id,
            priority=request.priority,
            urgency_level=request.urgency_level,
            context=request.context or {}
        )
        
        # Process voice input if provided
        if voice_file:
            voice_input = await _process_voice_file(voice_file)
            multi_modal_input.voice_input = voice_input
        
        # Process text input if provided
        if request.text_input:
            text_input = TextInput(
                text_content=request.text_input,
                language="en",  # Default to English
                source="api_input"
            )
            multi_modal_input.text_input = text_input
        
        # Process image input if provided
        if image_file:
            image_input = await _process_image_file(image_file)
            multi_modal_input.image_input = image_input
        
        # Process sensor data if provided
        if request.sensor_data:
            sensor_inputs = []
            for sensor_data in request.sensor_data:
                sensor_input = SensorInput(
                    sensor_type=sensor_data.get("sensor_type", "unknown"),
                    sensor_value=sensor_data.get("sensor_value"),
                    unit=sensor_data.get("unit"),
                    device_id=sensor_data.get("device_id"),
                    location=sensor_data.get("location")
                )
                sensor_inputs.append(sensor_input)
            multi_modal_input.sensor_inputs = sensor_inputs
        
        # Process multi-modal input
        result = await multi_modal_service.process_multi_modal_input(multi_modal_input)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing multi-modal input: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing multi-modal input: {str(e)}")


@multi_modal_router.post("/voice-text", response_model=MultiModalResult)
async def process_voice_and_text(
    patient_id: UUID = Form(...),
    voice_file: UploadFile = File(...),
    text_input: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    """
    Process voice and text input together
    
    - **patient_id**: Patient identifier
    - **voice_file**: Voice input file
    - **text_input**: Additional text input
    - **session_id**: Session identifier (optional)
    """
    try:
        logger.info(f"Processing voice and text input for patient {patient_id}")
        
        # Process voice file
        voice_input = await _process_voice_file(voice_file)
        
        # Create text input
        text_input_obj = TextInput(
            text_content=text_input,
            language="en",
            source="api_input"
        )
        
        # Create multi-modal input
        multi_modal_input = MultiModalInput(
            patient_id=patient_id,
            session_id=session_id,
            voice_input=voice_input,
            text_input=text_input_obj
        )
        
        # Process multi-modal input
        result = await multi_modal_service.process_multi_modal_input(multi_modal_input)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing voice and text input: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing voice and text input: {str(e)}")


@multi_modal_router.post("/voice-sensor", response_model=MultiModalResult)
async def process_voice_and_sensor(
    patient_id: UUID = Form(...),
    voice_file: UploadFile = File(...),
    sensor_data: List[Dict[str, Any]] = Body(...),
    session_id: Optional[str] = Form(None)
):
    """
    Process voice and sensor data together
    
    - **patient_id**: Patient identifier
    - **voice_file**: Voice input file
    - **sensor_data**: List of sensor data
    - **session_id**: Session identifier (optional)
    """
    try:
        logger.info(f"Processing voice and sensor input for patient {patient_id}")
        
        # Process voice file
        voice_input = await _process_voice_file(voice_file)
        
        # Process sensor data
        sensor_inputs = []
        for sensor_data_item in sensor_data:
            sensor_input = SensorInput(
                sensor_type=sensor_data_item.get("sensor_type", "unknown"),
                sensor_value=sensor_data_item.get("sensor_value"),
                unit=sensor_data_item.get("unit"),
                device_id=sensor_data_item.get("device_id"),
                location=sensor_data_item.get("location")
            )
            sensor_inputs.append(sensor_input)
        
        # Create multi-modal input
        multi_modal_input = MultiModalInput(
            patient_id=patient_id,
            session_id=session_id,
            voice_input=voice_input,
            sensor_inputs=sensor_inputs
        )
        
        # Process multi-modal input
        result = await multi_modal_service.process_multi_modal_input(multi_modal_input)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing voice and sensor input: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing voice and sensor input: {str(e)}")


@multi_modal_router.post("/text-sensor", response_model=MultiModalResult)
async def process_text_and_sensor(
    patient_id: UUID = Form(...),
    text_input: str = Form(...),
    sensor_data: List[Dict[str, Any]] = Body(...),
    session_id: Optional[str] = Form(None)
):
    """
    Process text and sensor data together
    
    - **patient_id**: Patient identifier
    - **text_input**: Text input
    - **sensor_data**: List of sensor data
    - **session_id**: Session identifier (optional)
    """
    try:
        logger.info(f"Processing text and sensor input for patient {patient_id}")
        
        # Create text input
        text_input_obj = TextInput(
            text_content=text_input,
            language="en",
            source="api_input"
        )
        
        # Process sensor data
        sensor_inputs = []
        for sensor_data_item in sensor_data:
            sensor_input = SensorInput(
                sensor_type=sensor_data_item.get("sensor_type", "unknown"),
                sensor_value=sensor_data_item.get("sensor_value"),
                unit=sensor_data_item.get("unit"),
                device_id=sensor_data_item.get("device_id"),
                location=sensor_data_item.get("location")
            )
            sensor_inputs.append(sensor_input)
        
        # Create multi-modal input
        multi_modal_input = MultiModalInput(
            patient_id=patient_id,
            session_id=session_id,
            text_input=text_input_obj,
            sensor_inputs=sensor_inputs
        )
        
        # Process multi-modal input
        result = await multi_modal_service.process_multi_modal_input(multi_modal_input)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing text and sensor input: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing text and sensor input: {str(e)}")


@multi_modal_router.get("/fusion-strategies")
async def get_fusion_strategies():
    """
    Get available fusion strategies for multi-modal processing
    """
    try:
        logger.info("Retrieving fusion strategies")
        
        strategies = [
            {
                "strategy": "early_fusion",
                "description": "Combine raw features from different modalities before processing",
                "advantages": ["Preserves all information", "Can capture cross-modal correlations"],
                "disadvantages": ["Higher computational cost", "Requires aligned features"]
            },
            {
                "strategy": "late_fusion",
                "description": "Process each modality separately and combine results",
                "advantages": ["Modular approach", "Lower computational cost"],
                "disadvantages": ["May lose cross-modal information", "Requires good individual models"]
            },
            {
                "strategy": "hybrid_fusion",
                "description": "Combine both early and late fusion approaches",
                "advantages": ["Best of both worlds", "Flexible approach"],
                "disadvantages": ["Complex implementation", "Higher computational cost"]
            }
        ]
        
        return {
            "strategies": strategies,
            "default_strategy": "late_fusion"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving fusion strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving fusion strategies: {str(e)}")


@multi_modal_router.post("/batch-process")
async def batch_process_multi_modal(
    requests: List[MultiModalRequest] = Body(...)
):
    """
    Process multiple multi-modal inputs in batch
    
    - **requests**: List of multi-modal requests
    """
    try:
        logger.info(f"Batch processing {len(requests)} multi-modal inputs")
        
        results = []
        
        for request in requests:
            try:
                # Create multi-modal input
                multi_modal_input = MultiModalInput(
                    patient_id=request.patient_id,
                    session_id=request.session_id,
                    text_input=TextInput(
                        text_content=request.text_input,
                        language="en",
                        source="api_input"
                    ) if request.text_input else None,
                    sensor_inputs=[
                        SensorInput(
                            sensor_type=sensor_data.get("sensor_type", "unknown"),
                            sensor_value=sensor_data.get("sensor_value"),
                            unit=sensor_data.get("unit"),
                            device_id=sensor_data.get("device_id"),
                            location=sensor_data.get("location")
                        ) for sensor_data in request.sensor_data or []
                    ],
                    context=request.context or {},
                    priority=request.priority,
                    urgency_level=request.urgency_level
                )
                
                # Process multi-modal input
                result = await multi_modal_service.process_multi_modal_input(multi_modal_input)
                
                results.append({
                    "patient_id": str(request.patient_id),
                    "success": result.processing_successful,
                    "primary_intent": result.primary_intent,
                    "confidence_score": result.confidence_score,
                    "processing_time": result.processing_time
                })
                
            except Exception as e:
                results.append({
                    "patient_id": str(request.patient_id),
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "batch_id": str(UUID.uuid4()),
            "total_requests": len(requests),
            "successful_processing": len([r for r in results if r["success"]]),
            "failed_processing": len([r for r in results if not r["success"]]),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in batch multi-modal processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in batch multi-modal processing: {str(e)}")


async def _process_voice_file(voice_file: UploadFile) -> MultiModalVoiceInput:
    """Process uploaded voice file"""
    try:
        # Validate file
        if not voice_file.filename or not voice_file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.ogg')):
            raise ValueError("Invalid audio file format")
        
        # Save file temporarily
        import tempfile
        import os
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(voice_file.filename)[1])
        temp_file_path = temp_file.name
        
        content = await voice_file.read()
        temp_file.write(content)
        temp_file.close()
        
        # Create voice input object
        voice_input = MultiModalVoiceInput(
            audio_file_path=temp_file_path,
            audio_duration=0.0,  # Will be calculated during processing
            audio_format=os.path.splitext(voice_file.filename)[1].lower().lstrip('.')
        )
        
        return voice_input
        
    except Exception as e:
        logger.error(f"Error processing voice file: {str(e)}")
        raise


async def _process_image_file(image_file: UploadFile) -> ImageInput:
    """Process uploaded image file"""
    try:
        # Validate file
        if not image_file.filename or not image_file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
            raise ValueError("Invalid image file format")
        
        # Save file temporarily
        import tempfile
        import os
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file.filename)[1])
        temp_file_path = temp_file.name
        
        content = await image_file.read()
        temp_file.write(content)
        temp_file.close()
        
        # Create image input object
        image_input = ImageInput(
            image_file_path=temp_file_path,
            image_format=os.path.splitext(image_file.filename)[1].lower().lstrip('.'),
            image_size={"width": 0, "height": 0}  # Will be calculated during processing
        )
        
        return image_input
        
    except Exception as e:
        logger.error(f"Error processing image file: {str(e)}")
        raise 