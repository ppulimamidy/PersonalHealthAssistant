"""
Vision Analysis Service
Service for processing vision-enabled voice input with image analysis.
"""

import os
import asyncio
import base64
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4, UUID
import httpx
import aiohttp
from PIL import Image
import numpy as np
import whisper
import edge_tts
import asyncio
import tempfile
import shutil

from ..models.vision_analysis import (
    ImageUploadResponse,
    SpeechToTextResponse,
    VisionAnalysisResponse,
    TextToSpeechResponse,
    VisionVoiceAnalysisResponse,
    VisionModelProvider,
    TTSProvider,
    AudioFormat,
    ImageFormat
)
from common.utils.logging import get_logger
from ..services.medical_prompt_engine import MedicalPromptEngine, MedicalDomain

logger = get_logger(__name__)


class VisionAnalysisService:
    """Service for vision-enabled voice analysis"""
    
    def __init__(self):
        """Initialize the vision analysis service"""
        self.upload_dir = "uploads/vision_analysis"
        self.audio_dir = "uploads/audio"
        self.image_dir = "uploads/images"
        self.output_dir = "outputs/vision_analysis"
        self._settings = None
        
        # Create directories if they don't exist
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize medical prompt engine
        self.medical_prompt_engine = MedicalPromptEngine()
        
        logger.info("Vision Analysis Service initialized")
    
    @property
    def groq_api_key(self):
        """Get GROQ API key from environment"""
        import os
        return os.getenv('GROQ_API_KEY')
    
    @property
    def openai_api_key(self):
        """Get OpenAI API key from environment"""
        import os
        return os.getenv('OPENAI_API_KEY')
    
    async def initialize(self):
        """Initialize the service"""
        logger.info("Initializing Vision Analysis Service...")
        
        # Load Whisper model
        try:
            self.whisper_model = whisper.load_model("base")
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.whisper_model = None
    
    async def upload_image(self, image_file_path: str, patient_id: UUID, session_id: Optional[str] = None) -> ImageUploadResponse:
        """Upload and process an image"""
        try:
            start_time = time.time()
            
            # Generate unique image ID
            image_id = uuid4()
            
            # Get image information
            with Image.open(image_file_path) as img:
                image_format = img.format.lower()
                image_size = os.path.getsize(image_file_path)
                image_dimensions = {"width": img.width, "height": img.height}
            
            # Create patient-specific directory
            patient_dir = os.path.join(self.image_dir, str(patient_id))
            os.makedirs(patient_dir, exist_ok=True)
            
            # Copy image to patient directory
            new_image_path = os.path.join(patient_dir, f"{image_id}.{image_format}")
            shutil.copy2(image_file_path, new_image_path)
            
            processing_time = time.time() - start_time
            
            return ImageUploadResponse(
                image_id=image_id,
                patient_id=patient_id,
                session_id=session_id,
                image_path=new_image_path,
                image_format=ImageFormat(image_format),
                image_size=image_size,
                image_dimensions=image_dimensions,
                upload_timestamp=datetime.now(),
                status="uploaded"
            )
            
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            raise Exception(f"Failed to upload image: {str(e)}")
    
    async def speech_to_text(self, audio_file_path: str, language: str = "en", enhance_audio: bool = True) -> SpeechToTextResponse:
        """Convert speech to text using Whisper"""
        try:
            start_time = time.time()
            transcription_id = uuid4()
            
            if not self.whisper_model:
                raise Exception("Whisper model not initialized")
            
            # Load and transcribe audio
            result = self.whisper_model.transcribe(
                audio_file_path,
                language=language,
                task="transcribe"
            )
            
            processing_time = time.time() - start_time
            
            return SpeechToTextResponse(
                transcription_id=transcription_id,
                text=result["text"].strip(),
                confidence=result.get("confidence", 0.0),
                language=result.get("language", language),
                duration=result.get("duration", 0.0),
                word_timestamps=result.get("segments", []),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in speech-to-text conversion: {e}")
            raise Exception(f"Failed to convert speech to text: {str(e)}")
    
    async def analyze_vision_groq(self, image_path: str, query: str, model: str = "meta-llama/llama-4-scout-17b-16e-instruct", max_tokens: int = 1000, temperature: float = 0.7) -> VisionAnalysisResponse:
        """Analyze image using GROQ Llama model with medical focus"""
        try:
            start_time = time.time()
            analysis_id = uuid4()
            
            # Detect medical domain and create medical-specific prompt
            medical_validation = self.medical_prompt_engine.validate_medical_query(query)
            domain = medical_validation["domain"]
            
            # Create medical-specific system and user prompts
            system_prompt = self.medical_prompt_engine.create_medical_system_prompt(domain)
            medical_query = self.medical_prompt_engine.create_medical_vision_prompt(query, domain)
            
            # Prepare request payload with medical context
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": medical_query
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"GROQ API error: {response.status_code} - {response.text}")
                
                result = response.json()
                
            # Extract response
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            
            # Calculate cost
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            cost = (input_tokens * self.cost_tracker["groq"]["input"] + 
                   output_tokens * self.cost_tracker["groq"]["output"]) / 1000
            
            processing_time = time.time() - start_time
            
            return VisionAnalysisResponse(
                analysis_id=analysis_id,
                query=query,
                response=content,
                confidence=0.9,  # GROQ doesn't provide confidence scores
                provider=VisionModelProvider.GROQ,
                model=model,
                processing_time=processing_time,
                tokens_used=tokens_used,
                cost=cost,
                medical_domain=domain.value,
                medical_confidence=medical_validation["confidence"]
            )
            
        except Exception as e:
            logger.error(f"Error in GROQ vision analysis: {e}")
            raise Exception(f"Failed to analyze image with GROQ: {str(e)}")
    
    async def analyze_vision_openai(self, image_path: str, query: str, model: str = "gpt-4-vision-preview", max_tokens: int = 1000, temperature: float = 0.7) -> VisionAnalysisResponse:
        """Analyze image using OpenAI vision model with medical focus"""
        try:
            start_time = time.time()
            analysis_id = uuid4()
            
            # Read and encode image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Detect medical domain and create medical-specific prompt
            medical_validation = self.medical_prompt_engine.validate_medical_query(query)
            domain = medical_validation["domain"]
            
            # Create medical-specific system and user prompts
            system_prompt = self.medical_prompt_engine.create_medical_system_prompt(domain)
            medical_query = self.medical_prompt_engine.create_medical_vision_prompt(query, domain)
            
            # Prepare request payload with medical context
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": medical_query
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
                
                result = response.json()
                
            # Extract response
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            
            # Calculate cost
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            cost = (input_tokens * self.cost_tracker["openai"]["input"] + 
                   output_tokens * self.cost_tracker["openai"]["output"]) / 1000
            
            processing_time = time.time() - start_time
            
            return VisionAnalysisResponse(
                analysis_id=analysis_id,
                query=query,
                response=content,
                confidence=0.9,  # OpenAI doesn't provide confidence scores
                provider=VisionModelProvider.OPENAI,
                model=model,
                processing_time=processing_time,
                tokens_used=tokens_used,
                cost=cost,
                medical_domain=domain.value,
                medical_confidence=medical_validation["confidence"]
            )
            
        except Exception as e:
            logger.error(f"Error in OpenAI vision analysis: {e}")
            raise Exception(f"Failed to analyze image with OpenAI: {str(e)}")
    
    async def text_to_speech_edge(self, text: str, voice: str = "en-US-JennyNeural", audio_format: AudioFormat = AudioFormat.MP3) -> TextToSpeechResponse:
        """Convert text to speech using Edge TTS"""
        try:
            start_time = time.time()
            tts_id = uuid4()
            
            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Generate output file path
            output_path = os.path.join(self.output_dir, f"{tts_id}.{audio_format.value}")
            
            # Convert text to speech
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            
            # Get file information
            file_size = os.path.getsize(output_path)
            
            # Estimate duration (rough calculation)
            words_per_minute = 150
            word_count = len(text.split())
            duration = (word_count / words_per_minute) * 60
            
            processing_time = time.time() - start_time
            
            return TextToSpeechResponse(
                tts_id=tts_id,
                audio_file_path=output_path,
                audio_format=audio_format,
                duration=duration,
                file_size=file_size,
                provider=TTSProvider.EDGE_TTS,
                voice=voice,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in Edge TTS conversion: {e}")
            raise Exception(f"Failed to convert text to speech with Edge TTS: {str(e)}")
    
    async def text_to_speech_openai(self, text: str, voice: str = "alloy", audio_format: AudioFormat = AudioFormat.MP3) -> TextToSpeechResponse:
        """Convert text to speech using OpenAI TTS"""
        try:
            start_time = time.time()
            tts_id = uuid4()
            
            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Generate output file path
            output_path = os.path.join(self.output_dir, f"{tts_id}.{audio_format.value}")
            
            # Prepare request
            payload = {
                "model": "tts-1",
                "input": text,
                "voice": voice,
                "response_format": audio_format.value
            }
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"OpenAI TTS API error: {response.status_code} - {response.text}")
                
                # Save audio file
                with open(output_path, "wb") as f:
                    f.write(response.content)
            
            # Get file information
            file_size = os.path.getsize(output_path)
            
            # Estimate duration (rough calculation)
            words_per_minute = 150
            word_count = len(text.split())
            duration = (word_count / words_per_minute) * 60
            
            processing_time = time.time() - start_time
            
            return TextToSpeechResponse(
                tts_id=tts_id,
                audio_file_path=output_path,
                audio_format=audio_format,
                duration=duration,
                file_size=file_size,
                provider=TTSProvider.OPENAI_TTS,
                voice=voice,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in OpenAI TTS conversion: {e}")
            raise Exception(f"Failed to convert text to speech with OpenAI TTS: {str(e)}")
    
    async def process_vision_voice_analysis(self, request_data: Dict[str, Any]) -> VisionVoiceAnalysisResponse:
        """Process complete vision-enabled voice analysis"""
        try:
            start_time = time.time()
            analysis_id = uuid4()
            
            patient_id = UUID(request_data["patient_id"])
            session_id = request_data.get("session_id")
            image_file = request_data.get("image_file")
            voice_query_file = request_data.get("voice_query_file")
            text_query = request_data.get("text_query")
            vision_provider = VisionModelProvider(request_data.get("vision_provider", "groq"))
            vision_model = request_data.get("vision_model", "llava-3.1-8b-instant")
            tts_provider = TTSProvider(request_data.get("tts_provider", "edge_tts"))
            tts_voice = request_data.get("tts_voice", "en-US-JennyNeural")
            audio_output_format = AudioFormat(request_data.get("audio_output_format", "mp3"))
            
            # Initialize response components
            image_upload = None
            speech_to_text = None
            vision_analysis = None
            text_to_speech = None
            total_cost = 0.0
            cost_breakdown = {}
            error_message = None
            
            try:
                # Step 1: Upload image if provided
                if image_file:
                    image_upload = await self.upload_image(image_file, patient_id, session_id)
                
                # Step 2: Convert speech to text if voice query provided
                if voice_query_file:
                    speech_to_text = await self.speech_to_text(voice_query_file)
                    query = speech_to_text.text
                elif text_query:
                    query = text_query
                else:
                    raise Exception("Either voice_query_file or text_query must be provided")
                
                # Step 3: Analyze image with vision model
                if image_upload:
                    if vision_provider == VisionModelProvider.GROQ:
                        vision_analysis = await self.analyze_vision_groq(
                            image_upload.image_path, 
                            query, 
                            vision_model
                        )
                    elif vision_provider == VisionModelProvider.OPENAI:
                        vision_analysis = await self.analyze_vision_openai(
                            image_upload.image_path, 
                            query, 
                            vision_model
                        )
                    
                    if vision_analysis:
                        total_cost += vision_analysis.cost or 0.0
                        cost_breakdown["vision_analysis"] = vision_analysis.cost or 0.0
                
                # Step 4: Convert response to speech
                response_text = vision_analysis.response if vision_analysis else "No image analysis available"
                
                if tts_provider == TTSProvider.EDGE_TTS:
                    text_to_speech = await self.text_to_speech_edge(
                        response_text, 
                        tts_voice, 
                        audio_output_format
                    )
                elif tts_provider == TTSProvider.OPENAI_TTS:
                    text_to_speech = await self.text_to_speech_openai(
                        response_text, 
                        tts_voice, 
                        audio_output_format
                    )
                
                if text_to_speech:
                    # Estimate TTS cost
                    tts_cost = (len(response_text) / 1000) * self.cost_tracker["tts"]
                    total_cost += tts_cost
                    cost_breakdown["text_to_speech"] = tts_cost
                
                status = "completed"
                
            except Exception as e:
                error_message = str(e)
                status = "failed"
                logger.error(f"Error in vision voice analysis: {e}")
            
            processing_end_time = time.time()
            total_processing_time = processing_end_time - start_time
            
            return VisionVoiceAnalysisResponse(
                analysis_id=analysis_id,
                patient_id=patient_id,
                session_id=session_id,
                image_upload=image_upload,
                speech_to_text=speech_to_text,
                vision_analysis=vision_analysis,
                text_to_speech=text_to_speech,
                processing_start_time=datetime.fromtimestamp(start_time),
                processing_end_time=datetime.fromtimestamp(processing_end_time),
                total_processing_time=total_processing_time,
                status=status,
                error_message=error_message,
                total_cost=total_cost,
                cost_breakdown=cost_breakdown
            )
            
        except Exception as e:
            logger.error(f"Error in vision voice analysis processing: {e}")
            raise Exception(f"Failed to process vision voice analysis: {str(e)}")
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up Vision Analysis Service...")
        # Cleanup any temporary files or resources
        pass 