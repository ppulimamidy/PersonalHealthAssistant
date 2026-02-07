"""
Vision Analysis API
API endpoints for vision-enabled voice input processing with image analysis.
"""

import os
import tempfile
import shutil
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
import traceback

from ..models.vision_analysis import (
    ImageUploadRequest,
    ImageUploadResponse,
    SpeechToTextRequest,
    SpeechToTextResponse,
    VisionAnalysisRequest,
    VisionAnalysisResponse,
    TextToSpeechRequest,
    TextToSpeechResponse,
    VisionVoiceAnalysisRequest,
    VisionVoiceAnalysisResponse,
    VisionAnalysisSession,
    VisionAnalysisHistory,
    VisionAnalysisStats,
    VisionModelProvider,
    TTSProvider,
    AudioFormat,
    ImageFormat
)
from ..services.medical_prompt_engine import MedicalDomain
from ..services.vision_analysis_service import VisionAnalysisService
from common.utils.logging import get_logger

logger = get_logger(__name__)

vision_analysis_router = APIRouter(prefix="/vision-analysis", tags=["Vision Analysis"])

# Import service manager
from ..services.service_manager import get_vision_analysis_service


@vision_analysis_router.post("/upload-image", response_model=ImageUploadResponse)
async def upload_image(
    patient_id: UUID = Form(...),
    image_file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Upload an image for vision analysis
    
    - **patient_id**: Patient identifier
    - **image_file**: Image file to upload
    - **session_id**: Session identifier (optional)
    """
    vision_analysis_service = get_vision_analysis_service()
    if not vision_analysis_service:
        raise HTTPException(status_code=503, detail="Vision Analysis Service not available")
    
    try:
        logger.info(f"Uploading image for patient {patient_id}")
        
        # Validate image file
        if not image_file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file.filename)[1]) as temp_file:
            shutil.copyfileobj(image_file.file, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Upload image using service
            result = await vision_analysis_service.upload_image(temp_file_path, patient_id, session_id)
            return result
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")


@vision_analysis_router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(
    audio_file: UploadFile = File(...),
    language: str = Form("en"),
    model: str = Form("whisper-1"),
    enhance_audio: bool = Form(True),
    medical_context: bool = Form(True)
):
    """
    Convert speech to text
    
    - **audio_file**: Audio file to transcribe
    - **language**: Language code (default: en)
    - **model**: STT model to use (default: whisper-1)
    - **enhance_audio**: Whether to enhance audio quality (default: True)
    """
    vision_analysis_service = get_vision_analysis_service()
    if not vision_analysis_service:
        raise HTTPException(status_code=503, detail="Vision Analysis Service not available")
    
    try:
        logger.info("Converting speech to text")
        
        # Validate audio file
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as temp_file:
            shutil.copyfileobj(audio_file.file, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Convert speech to text using service
            result = await vision_analysis_service.speech_to_text(temp_file_path, language, enhance_audio)
            
            # If medical context is enabled, validate the transcribed text
            if medical_context and result.text:
                medical_validation = vision_analysis_service.medical_prompt_engine.validate_medical_query(result.text)
                logger.info(f"Medical validation for transcribed text: {medical_validation}")
                
                # Add medical context to response if it's medical-related
                if medical_validation["is_medical"]:
                    result.medical_context = {
                        "is_medical": True,
                        "domain": medical_validation["domain"].value,
                        "confidence": medical_validation["confidence"]
                    }
            
            return result
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error in speech-to-text conversion: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error in speech-to-text conversion: {str(e)}\n{traceback.format_exc()}")


@vision_analysis_router.post("/analyze-vision", response_model=VisionAnalysisResponse)
async def analyze_vision(
    image_file: UploadFile = File(...),
    query: str = Form(...),
    provider: VisionModelProvider = Form(VisionModelProvider.GROQ),
    model: str = Form("meta-llama/llama-4-scout-17b-16e-instruct"),
    max_tokens: int = Form(1000),
    temperature: float = Form(0.7),
    medical_domain: Optional[str] = Form(None)
):
    """
    Analyze image with vision model
    
    - **image_file**: Image file to analyze
    - **query**: Text query for vision analysis
    - **provider**: Vision model provider (groq or openai)
    - **model**: Vision model to use
    - **max_tokens**: Maximum tokens for response
    - **temperature**: Response temperature
    """
    vision_analysis_service = get_vision_analysis_service()
    if not vision_analysis_service:
        raise HTTPException(status_code=503, detail="Vision Analysis Service not available")
    
    try:
        logger.info(f"Analyzing image with {provider} vision model")
        
        # Validate image file
        if not image_file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file.filename)[1]) as temp_file:
            shutil.copyfileobj(image_file.file, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Validate medical domain if provided
            if medical_domain:
                try:
                    domain = MedicalDomain(medical_domain)
                    logger.info(f"Using specified medical domain: {domain.value}")
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid medical domain: {medical_domain}")
            else:
                domain = None
                logger.info("No medical domain specified, will auto-detect from query")
            
            # Analyze image using service with medical focus
            if provider == VisionModelProvider.GROQ:
                result = await vision_analysis_service.analyze_vision_groq(
                    temp_file_path, query, model, max_tokens, temperature
                )
            elif provider == VisionModelProvider.OPENAI:
                result = await vision_analysis_service.analyze_vision_openai(
                    temp_file_path, query, model, max_tokens, temperature
                )
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
            
            return result
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error in vision analysis: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error in vision analysis: {str(e)}\n{traceback.format_exc()}")


@vision_analysis_router.post("/text-to-speech", response_model=TextToSpeechResponse)
async def text_to_speech(
    text: str = Form(...),
    provider: TTSProvider = Form(TTSProvider.EDGE_TTS),
    voice: str = Form("en-US-JennyNeural"),
    language: str = Form("en-US"),
    audio_format: AudioFormat = Form(AudioFormat.MP3),
    speed: float = Form(1.0),
    pitch: float = Form(1.0),
    volume: float = Form(1.0)
):
    """
    Convert text to speech
    
    - **text**: Text to convert to speech
    - **provider**: TTS provider (edge_tts, gtts, pyttsx3, openai_tts)
    - **voice**: Voice to use
    - **language**: Language code
    - **audio_format**: Output audio format
    - **speed**: Speech speed multiplier
    - **pitch**: Speech pitch multiplier
    - **volume**: Speech volume multiplier
    """
    vision_analysis_service = get_vision_analysis_service()
    if not vision_analysis_service:
        raise HTTPException(status_code=503, detail="Vision Analysis Service not available")
    
    try:
        logger.info(f"Converting text to speech using {provider}")
        
        # Convert text to speech using service
        if provider == TTSProvider.EDGE_TTS:
            result = await vision_analysis_service.text_to_speech_edge(text, voice, audio_format)
        elif provider == TTSProvider.OPENAI_TTS:
            result = await vision_analysis_service.text_to_speech_openai(text, voice, audio_format)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported TTS provider: {provider}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in text-to-speech conversion: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error in text-to-speech conversion: {str(e)}\n{traceback.format_exc()}")


@vision_analysis_router.post("/complete-analysis", response_model=VisionVoiceAnalysisResponse)
async def complete_vision_voice_analysis(
    patient_id: UUID = Form(...),
    session_id: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    voice_query_file: Optional[UploadFile] = File(None),
    text_query: Optional[str] = Form(None),
    vision_provider: VisionModelProvider = Form(VisionModelProvider.GROQ),
    vision_model: str = Form("meta-llama/llama-4-scout-17b-16e-instruct"),
    tts_provider: TTSProvider = Form(TTSProvider.EDGE_TTS),
    tts_voice: str = Form("en-US-JennyNeural"),
    audio_output_format: AudioFormat = Form(AudioFormat.MP3)
):
    """
    Complete vision-enabled voice analysis workflow
    
    This endpoint processes the complete workflow:
    1. Upload image (if provided)
    2. Convert speech to text (if voice query provided)
    3. Analyze image with vision model
    4. Convert response to speech
    
    - **patient_id**: Patient identifier
    - **session_id**: Session identifier (optional)
    - **image_file**: Image file to analyze (optional)
    - **voice_query_file**: Voice query file (optional)
    - **text_query**: Text query as alternative to voice (optional)
    - **vision_provider**: Vision model provider
    - **vision_model**: Vision model to use
    - **tts_provider**: TTS provider
    - **tts_voice**: TTS voice
    - **audio_output_format**: Output audio format
    """
    vision_analysis_service = get_vision_analysis_service()
    if not vision_analysis_service:
        raise HTTPException(status_code=503, detail="Vision Analysis Service not available")
    
    try:
        logger.info(f"Processing complete vision voice analysis for patient {patient_id}")
        
        # Validate inputs
        if not image_file and not voice_query_file and not text_query:
            raise HTTPException(status_code=400, detail="Either image_file, voice_query_file, or text_query must be provided")
        
        if not voice_query_file and not text_query:
            raise HTTPException(status_code=400, detail="Either voice_query_file or text_query must be provided")
        
        # Prepare request data
        request_data = {
            "patient_id": str(patient_id),
            "session_id": session_id,
            "vision_provider": vision_provider.value,
            "vision_model": vision_model,
            "tts_provider": tts_provider.value,
            "tts_voice": tts_voice,
            "audio_output_format": audio_output_format.value
        }
        
        # Handle image file
        if image_file:
            if not image_file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Image file must be an image")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file.filename)[1]) as temp_file:
                shutil.copyfileobj(image_file.file, temp_file)
                request_data["image_file"] = temp_file.name
        
        # Handle voice query file
        if voice_query_file:
            if not voice_query_file.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail="Voice query file must be an audio file")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(voice_query_file.filename)[1]) as temp_file:
                shutil.copyfileobj(voice_query_file.file, temp_file)
                request_data["voice_query_file"] = temp_file.name
        
        # Handle text query
        if text_query:
            request_data["text_query"] = text_query
        
        try:
            # Process complete analysis
            result = await vision_analysis_service.process_vision_voice_analysis(request_data)
            return result
        finally:
            # Clean up temporary files
            for key in ["image_file", "voice_query_file"]:
                if key in request_data and os.path.exists(request_data[key]):
                    os.unlink(request_data[key])
            
    except Exception as e:
        logger.error(f"Error in complete vision voice analysis: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error in complete vision voice analysis: {str(e)}\n{traceback.format_exc()}")


@vision_analysis_router.get("/audio/{tts_id}")
async def get_audio_file(tts_id: str):
    """
    Get generated audio file
    
    - **tts_id**: TTS identifier
    """
    try:
        vision_analysis_service = get_vision_analysis_service()
        if not vision_analysis_service:
            raise HTTPException(status_code=503, detail="Vision Analysis Service not available")
        
        # Look for audio file in output directory
        output_dir = vision_analysis_service.output_dir
        for file in os.listdir(output_dir):
            if file.startswith(tts_id):
                file_path = os.path.join(output_dir, file)
                return FileResponse(file_path, media_type="audio/mpeg")
        
        raise HTTPException(status_code=404, detail="Audio file not found")
        
    except Exception as e:
        logger.error(f"Error retrieving audio file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving audio file: {str(e)}")


@vision_analysis_router.get("/image/{image_id}")
async def get_image_file(image_id: str):
    """
    Get uploaded image file
    
    - **image_id**: Image identifier
    """
    vision_analysis_service = get_vision_analysis_service()
    if not vision_analysis_service:
        raise HTTPException(status_code=503, detail="Vision Analysis Service not available")
    
    try:
        # Look for image file in image directory
        image_dir = vision_analysis_service.image_dir
        for root, dirs, files in os.walk(image_dir):
            for file in files:
                if file.startswith(image_id):
                    file_path = os.path.join(root, file)
                    return FileResponse(file_path, media_type="image/jpeg")
        
        raise HTTPException(status_code=404, detail="Image file not found")
        
    except Exception as e:
        logger.error(f"Error retrieving image file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving image file: {str(e)}")


@vision_analysis_router.get("/providers/vision")
async def get_vision_providers():
    """Get available vision model providers"""
    return {
        "providers": [
            {
                "name": "groq",
                "display_name": "GROQ",
                "models": [
                    "meta-llama/llama-4-scout-17b-16e-instruct",
                    "llama-70b-4096",
                    "llama-70b-4096-2"
                ],
                "description": "Fast inference with Llama models"
            },
            {
                "name": "openai",
                "display_name": "OpenAI",
                "models": [
                    "gpt-4-vision-preview",
                    "gpt-4o",
                    "gpt-4o-mini"
                ],
                "description": "High-quality vision analysis with GPT models"
            }
        ]
    }


@vision_analysis_router.get("/providers/tts")
async def get_tts_providers():
    """Get available TTS providers"""
    return {
        "providers": [
            {
                "name": "edge_tts",
                "display_name": "Microsoft Edge TTS",
                "voices": [
                    "en-US-JennyNeural",
                    "en-US-GuyNeural",
                    "en-GB-SoniaNeural",
                    "en-GB-RyanNeural"
                ],
                "description": "High-quality neural voices"
            },
            {
                "name": "openai_tts",
                "display_name": "OpenAI TTS",
                "voices": [
                    "alloy",
                    "echo",
                    "fable",
                    "onyx",
                    "nova",
                    "shimmer"
                ],
                "description": "Advanced text-to-speech with natural voices"
            }
        ]
    }


@vision_analysis_router.get("/formats/audio")
async def get_audio_formats():
    """Get supported audio formats"""
    return {
        "formats": [
            {"name": "mp3", "description": "MP3 audio format"},
            {"name": "wav", "description": "WAV audio format"},
            {"name": "m4a", "description": "M4A audio format"},
            {"name": "ogg", "description": "OGG audio format"},
            {"name": "flac", "description": "FLAC audio format"}
        ]
    }


@vision_analysis_router.get("/formats/image")
async def get_image_formats():
    """Get supported image formats"""
    return {
        "formats": [
            {"name": "jpeg", "description": "JPEG image format"},
            {"name": "jpg", "description": "JPG image format"},
            {"name": "png", "description": "PNG image format"},
            {"name": "webp", "description": "WebP image format"},
            {"name": "tiff", "description": "TIFF image format"},
            {"name": "bmp", "description": "BMP image format"}
        ]
    }


@vision_analysis_router.get("/medical-domains")
async def get_medical_domains():
    """
    Get available medical domains and their configurations
    
    Returns the list of supported medical domains with their keywords and settings
    """
    from config.medical_domains import MEDICAL_DOMAIN_CONFIG, MedicalDomain
    
    try:
        domains = {}
        for domain in MedicalDomain:
            config = MEDICAL_DOMAIN_CONFIG[domain]
            domains[domain.value] = {
                "keywords": config["keywords"],
                "analysis_focus": config["analysis_focus"],
                "disclaimer": config["disclaimer"],
                "recommended_models": config["recommended_models"],
                "temperature": config["temperature"],
                "max_tokens": config["max_tokens"]
            }
        
        return {
            "medical_domains": domains,
            "total_domains": len(domains)
        }
    except Exception as e:
        logger.error(f"Error getting medical domains: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting medical domains: {str(e)}")


@vision_analysis_router.post("/detect-medical-domain")
async def detect_medical_domain(query: str = Form(...)):
    """
    Detect medical domain from query text
    
    - **query**: Text query to analyze for medical domain detection
    """
    vision_analysis_service = get_vision_analysis_service()
    if not vision_analysis_service:
        raise HTTPException(status_code=503, detail="Vision Analysis Service not available")
    
    try:
        # Use the medical prompt engine to detect domain
        medical_validation = vision_analysis_service.medical_prompt_engine.validate_medical_query(query)
        
        return {
            "query": query,
            "detected_domain": medical_validation["domain"].value,
            "is_medical": medical_validation["is_medical"],
            "confidence": medical_validation["confidence"],
            "keywords_found": [
                keyword for keyword in medical_validation["domain"].value.split() 
                if keyword.lower() in query.lower()
            ]
        }
    except Exception as e:
        logger.error(f"Error detecting medical domain: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error detecting medical domain: {str(e)}")


@vision_analysis_router.get("/health")
async def health_check():
    """Health check for vision analysis service"""
    return {
        "service": "vision_analysis",
        "status": "healthy",
        "version": "1.0.0",
        "features": [
            "Image upload and processing",
            "Speech-to-text conversion",
            "Vision model analysis (GROQ, OpenAI)",
            "Text-to-speech synthesis",
            "Complete vision-enabled voice analysis workflow",
            "Medical domain detection and analysis"
        ]
    } 