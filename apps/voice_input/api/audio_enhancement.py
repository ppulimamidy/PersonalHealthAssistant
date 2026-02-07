"""
Audio Enhancement API
API endpoints for enhancing audio quality.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
import os
import tempfile

from ..models.audio_processing import AudioEnhancementResult
from ..services.audio_enhancement_service import AudioEnhancementService
from common.utils.logging import get_logger

logger = get_logger(__name__)

audio_enhancement_router = APIRouter(prefix="/audio-enhancement", tags=["Audio Enhancement"])

# Initialize service
audio_enhancement_service = AudioEnhancementService()


@audio_enhancement_router.post("/enhance", response_model=AudioEnhancementResult)
async def enhance_audio(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    enhancement_methods: Optional[str] = Form("normalization,noise_reduction"),
    voice_input_id: Optional[UUID] = Form(None)
):
    """
    Enhance audio quality
    
    - **audio_file**: Audio file to enhance
    - **enhancement_methods**: Comma-separated list of enhancement methods
    - **voice_input_id**: Associated voice input ID (optional)
    """
    try:
        logger.info(f"Enhancing audio file: {audio_file.filename}")
        
        # Validate audio file
        if not audio_file.filename or not audio_file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.ogg')):
            raise HTTPException(status_code=400, detail="Invalid audio file format")
        
        # Parse enhancement methods
        methods = [method.strip() for method in enhancement_methods.split(',')] if enhancement_methods else ["normalization", "noise_reduction"]
        
        # Save uploaded file
        temp_file_path = await _save_uploaded_file(audio_file)
        
        # Enhance audio
        enhancement_result = await audio_enhancement_service.enhance_audio(
            temp_file_path,
            methods
        )
        
        # Clean up original file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return enhancement_result
        
    except Exception as e:
        logger.error(f"Error enhancing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enhancing audio: {str(e)}")


@audio_enhancement_router.get("/enhanced-audio/{enhancement_id}")
async def get_enhanced_audio(enhancement_id: str):
    """
    Get enhanced audio file
    
    - **enhancement_id**: Enhancement result identifier
    """
    try:
        # This would fetch the enhanced audio file path from database in production
        # For now, return a mock file
        mock_enhanced_path = "/tmp/mock_enhanced_audio.wav"
        
        if not os.path.exists(mock_enhanced_path):
            # Create a mock enhanced audio file for testing
            import wave
            import struct
            
            with wave.open(mock_enhanced_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                
                # Generate 1 second of enhanced audio (sine wave)
                import math
                frames = []
                for i in range(16000):
                    sample = int(32767 * 0.3 * math.sin(2 * math.pi * 440 * i / 16000))
                    frames.append(sample)
                
                frame_data = struct.pack('h' * len(frames), *frames)
                wav_file.writeframes(frame_data)
        
        return FileResponse(
            mock_enhanced_path,
            media_type="audio/wav",
            filename=f"enhanced_audio_{enhancement_id}.wav"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving enhanced audio {enhancement_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="Enhanced audio file not found")


@audio_enhancement_router.post("/batch-enhance")
async def batch_enhance_audio(
    background_tasks: BackgroundTasks,
    audio_files: List[UploadFile] = File(...),
    enhancement_methods: Optional[str] = Form("normalization,noise_reduction")
):
    """
    Enhance multiple audio files in batch
    
    - **audio_files**: List of audio files to enhance
    - **enhancement_methods**: Comma-separated list of enhancement methods
    """
    try:
        logger.info(f"Batch enhancing {len(audio_files)} audio files")
        
        # Parse enhancement methods
        methods = [method.strip() for method in enhancement_methods.split(',')] if enhancement_methods else ["normalization", "noise_reduction"]
        
        # Save uploaded files
        temp_file_paths = []
        for audio_file in audio_files:
            if not audio_file.filename or not audio_file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.ogg')):
                raise HTTPException(status_code=400, detail=f"Invalid audio file format: {audio_file.filename}")
            
            temp_file_path = await _save_uploaded_file(audio_file)
            temp_file_paths.append(temp_file_path)
        
        # Enhance audio files in batch
        enhancement_results = await audio_enhancement_service.batch_enhance_audio(
            temp_file_paths,
            methods
        )
        
        # Clean up original files
        for temp_file_path in temp_file_paths:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
        return {
            "batch_id": str(UUID.uuid4()),
            "total_files": len(audio_files),
            "successful_enhancements": len([r for r in enhancement_results if r.enhancement_applied]),
            "failed_enhancements": len([r for r in enhancement_results if not r.enhancement_applied]),
            "results": [
                {
                    "original_file": os.path.basename(r.original_audio_path),
                    "enhanced_file": os.path.basename(r.enhanced_audio_path) if r.enhanced_audio_path else None,
                    "enhancement_applied": r.enhancement_applied,
                    "improvement_score": r.improvement_score,
                    "processing_time": r.processing_time,
                    "success": bool(r.enhancement_applied)
                }
                for r in enhancement_results
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in batch audio enhancement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in batch audio enhancement: {str(e)}")


@audio_enhancement_router.get("/enhancement-methods")
async def get_enhancement_methods():
    """
    Get available audio enhancement methods
    """
    try:
        logger.info("Retrieving enhancement methods")
        
        methods = [
            {
                "method": "normalization",
                "description": "Normalize audio levels to improve volume consistency",
                "use_case": "Audio with inconsistent volume levels",
                "processing_time": "Low"
            },
            {
                "method": "noise_reduction",
                "description": "Reduce background noise using spectral gating",
                "use_case": "Audio with background noise or interference",
                "processing_time": "Medium"
            },
            {
                "method": "filtering",
                "description": "Apply high-pass and low-pass filters to remove unwanted frequencies",
                "use_case": "Audio with low-frequency rumble or high-frequency noise",
                "processing_time": "Low"
            },
            {
                "method": "compression",
                "description": "Apply dynamic range compression to even out volume levels",
                "use_case": "Audio with wide dynamic range",
                "processing_time": "Low"
            }
        ]
        
        return {
            "methods": methods,
            "default_methods": ["normalization", "noise_reduction"],
            "supported_formats": [".wav", ".mp3", ".m4a", ".flac", ".ogg"]
        }
        
    except Exception as e:
        logger.error(f"Error retrieving enhancement methods: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving enhancement methods: {str(e)}")


@audio_enhancement_router.post("/compare")
async def compare_audio_quality(
    original_audio: UploadFile = File(...),
    enhanced_audio: UploadFile = File(...)
):
    """
    Compare quality between original and enhanced audio
    
    - **original_audio**: Original audio file
    - **enhanced_audio**: Enhanced audio file
    """
    try:
        logger.info("Comparing audio quality between original and enhanced files")
        
        # Validate audio files
        for audio_file in [original_audio, enhanced_audio]:
            if not audio_file.filename or not audio_file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.ogg')):
                raise HTTPException(status_code=400, detail="Invalid audio file format")
        
        # Save uploaded files
        original_path = await _save_uploaded_file(original_audio)
        enhanced_path = await _save_uploaded_file(enhanced_audio)
        
        # Analyze both files
        original_analysis = await audio_enhancement_service._analyze_audio_quality(
            await audio_enhancement_service._load_audio(original_path)
        )
        enhanced_analysis = await audio_enhancement_service._analyze_audio_quality(
            await audio_enhancement_service._load_audio(enhanced_path)
        )
        
        # Calculate improvements
        improvements = {
            "signal_to_noise_ratio": enhanced_analysis.signal_to_noise_ratio - original_analysis.signal_to_noise_ratio,
            "speech_clarity": enhanced_analysis.speech_clarity - original_analysis.speech_clarity,
            "volume_consistency": enhanced_analysis.volume_consistency - original_analysis.volume_consistency,
            "overall_quality": enhanced_analysis.overall_quality_score - original_analysis.overall_quality_score
        }
        
        # Clean up files
        for path in [original_path, enhanced_path]:
            if os.path.exists(path):
                os.remove(path)
        
        return {
            "original_quality": {
                "signal_to_noise_ratio": original_analysis.signal_to_noise_ratio,
                "background_noise_level": original_analysis.background_noise_level,
                "speech_clarity": original_analysis.speech_clarity,
                "volume_consistency": original_analysis.volume_consistency,
                "overall_quality_score": original_analysis.overall_quality_score,
                "audio_artifacts": original_analysis.audio_artifacts
            },
            "enhanced_quality": {
                "signal_to_noise_ratio": enhanced_analysis.signal_to_noise_ratio,
                "background_noise_level": enhanced_analysis.background_noise_level,
                "speech_clarity": enhanced_analysis.speech_clarity,
                "volume_consistency": enhanced_analysis.volume_consistency,
                "overall_quality_score": enhanced_analysis.overall_quality_score,
                "audio_artifacts": enhanced_analysis.audio_artifacts
            },
            "improvements": improvements,
            "overall_improvement": sum(improvements.values()) / len(improvements)
        }
        
    except Exception as e:
        logger.error(f"Error comparing audio quality: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error comparing audio quality: {str(e)}")


@audio_enhancement_router.post("/convert-format")
async def convert_audio_format(
    audio_file: UploadFile = File(...),
    output_format: str = Form("wav"),
    sample_rate: int = Form(16000)
):
    """
    Convert audio to different format and sample rate
    
    - **audio_file**: Audio file to convert
    - **output_format**: Desired output format (wav, mp3, m4a, flac, ogg)
    - **sample_rate**: Desired sample rate in Hz
    """
    try:
        logger.info(f"Converting audio to {output_format} format with {sample_rate}Hz sample rate")
        
        # Validate audio file
        if not audio_file.filename or not audio_file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.ogg')):
            raise HTTPException(status_code=400, detail="Invalid audio file format")
        
        # Validate output format
        if output_format.lower() not in ['wav', 'mp3', 'm4a', 'flac', 'ogg']:
            raise HTTPException(status_code=400, detail="Invalid output format")
        
        # Save uploaded file
        temp_file_path = await _save_uploaded_file(audio_file)
        
        # Convert audio format
        converted_path = await audio_enhancement_service.convert_audio_format(
            temp_file_path,
            output_format,
            sample_rate
        )
        
        # Return converted file
        response = FileResponse(
            converted_path,
            media_type=f"audio/{output_format}",
            filename=f"converted_audio.{output_format}"
        )
        
        # Clean up original file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return response
        
    except Exception as e:
        logger.error(f"Error converting audio format: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error converting audio format: {str(e)}")


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