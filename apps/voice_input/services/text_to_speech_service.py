"""
Text-to-Speech Service
Service for converting text to speech using various synthesis engines.
"""

import asyncio
import os
import tempfile
import re
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import uuid
# import numpy as np
# import soundfile as sf
# from pydub import AudioSegment
import wave
import math

# Text-to-speech libraries
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

from common.utils.logging import get_logger
from ..models.text_to_speech import (
    TextToSpeechRequest,
    TextToSpeechResult,
    VoiceProfile,
    SpeechSegment,
    VoiceType,
    EmotionType,
    SpeechRate,
    PitchLevel,
    SSMLProcessor
)


logger = get_logger(__name__)


class TextToSpeechService:
    """Service for text-to-speech synthesis"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.supported_formats = ['wav', 'mp3', 'ogg', 'flac']
        self.default_voice_id = "en-US-Neural2-F"
        
        # Initialize synthesis engines
        self.engines = {}
        self._initialize_engines()
        
        # Voice profiles
        self.voice_profiles = self._load_voice_profiles()
        
        # SSML processor
        self.ssml_processor = SSMLProcessor(
            enable_ssml=True,
            supported_tags=["speak", "voice", "prosody", "break", "say-as", "phoneme", "emphasis"],
            voice_attributes={
                "name": "en-US-Neural2-F",
                "language": "en-US",
                "gender": "female"
            },
            prosody_controls={
                "rate": ["x-slow", "slow", "medium", "fast", "x-fast"],
                "pitch": ["x-low", "low", "medium", "high", "x-high"],
                "volume": ["silent", "x-soft", "soft", "medium", "loud", "x-loud"]
            },
            emotion_mapping={
                "happy": EmotionType.HAPPY,
                "sad": EmotionType.SAD,
                "angry": EmotionType.ANGRY,
                "excited": EmotionType.EXCITED,
                "calm": EmotionType.CALM,
                "concerned": EmotionType.CONCERNED,
                "professional": EmotionType.PROFESSIONAL
            }
        )
    
    def _initialize_engines(self):
        """Initialize available TTS engines"""
        try:
            if PYTTSX3_AVAILABLE:
                self.engines['pyttsx3'] = pyttsx3.init()
                self.logger.info("Initialized pyttsx3 engine")
        except Exception as e:
            self.logger.warning(f"Failed to initialize pyttsx3: {str(e)}")
        
        if GTTS_AVAILABLE:
            self.engines['gtts'] = True
            self.logger.info("gTTS engine available")
        
        if EDGE_TTS_AVAILABLE:
            self.engines['edge_tts'] = True
            self.logger.info("Edge TTS engine available")
        
        self.logger.info(f"Available TTS engines: {list(self.engines.keys())}")
    
    def _load_voice_profiles(self) -> Dict[str, VoiceProfile]:
        """Load available voice profiles"""
        profiles = {
            "en-US-Neural2-F": VoiceProfile(
                voice_id="en-US-Neural2-F",
                voice_name="Emma (Neural)",
                language="en-US",
                gender="female",
                age_group="adult",
                accent="American",
                voice_type=VoiceType.NEURAL,
                sample_rate=22050,
                pitch_range={"min": 0.5, "max": 2.0},
                speaking_rate_range={"min": 0.5, "max": 2.0},
                emotion_support=[
                    EmotionType.NEUTRAL, EmotionType.HAPPY, EmotionType.CALM,
                    EmotionType.PROFESSIONAL, EmotionType.CONCERNED
                ],
                quality_metrics={
                    "naturalness": 0.85,
                    "intelligibility": 0.92,
                    "expressiveness": 0.78
                }
            ),
            "en-US-Neural2-M": VoiceProfile(
                voice_id="en-US-Neural2-M",
                voice_name="James (Neural)",
                language="en-US",
                gender="male",
                age_group="adult",
                accent="American",
                voice_type=VoiceType.NEURAL,
                sample_rate=22050,
                pitch_range={"min": 0.5, "max": 2.0},
                speaking_rate_range={"min": 0.5, "max": 2.0},
                emotion_support=[
                    EmotionType.NEUTRAL, EmotionType.HAPPY, EmotionType.CALM,
                    EmotionType.PROFESSIONAL, EmotionType.CONCERNED
                ],
                quality_metrics={
                    "naturalness": 0.87,
                    "intelligibility": 0.94,
                    "expressiveness": 0.80
                }
            ),
            "en-GB-Neural2-F": VoiceProfile(
                voice_id="en-GB-Neural2-F",
                voice_name="Sophie (Neural)",
                language="en-GB",
                gender="female",
                age_group="adult",
                accent="British",
                voice_type=VoiceType.NEURAL,
                sample_rate=22050,
                pitch_range={"min": 0.5, "max": 2.0},
                speaking_rate_range={"min": 0.5, "max": 2.0},
                emotion_support=[
                    EmotionType.NEUTRAL, EmotionType.HAPPY, EmotionType.CALM,
                    EmotionType.PROFESSIONAL
                ],
                quality_metrics={
                    "naturalness": 0.83,
                    "intelligibility": 0.90,
                    "expressiveness": 0.75
                }
            )
        }
        
        return profiles
    
    async def synthesize_speech(
        self, 
        request: TextToSpeechRequest
    ) -> TextToSpeechResult:
        """
        Synthesize speech from text
        
        Args:
            request: Text-to-speech synthesis request
            
        Returns:
            TextToSpeechResult with synthesis details
        """
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Synthesizing speech for text: {request.text[:50]}...")
            
            # Validate request
            self._validate_request(request)
            
            # Get voice profile
            voice_profile = self._get_voice_profile(request.voice_id)
            
            # Process text (SSML if enabled)
            processed_text = await self._process_text(request)
            
            # Choose synthesis engine
            engine = self._select_engine(request.voice_type, voice_profile)
            
            # Synthesize speech
            audio_data, audio_info = await self._synthesize_with_engine(
                engine, processed_text, request, voice_profile
            )
            
            # Save audio file
            audio_file_path = await self._save_audio_file(
                audio_data, audio_info, request.format
            )
            
            # Calculate quality metrics
            quality_metrics = await self._calculate_quality_metrics(
                audio_data, audio_info, voice_profile
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return TextToSpeechResult(
                synthesis_id=uuid.uuid4(),
                text=request.text,
                synthesized_text=processed_text,
                audio_file_path=audio_file_path,
                audio_duration=audio_info.get("duration", 0.0),
                audio_format=request.format,
                sample_rate=audio_info.get("sample_rate", request.sample_rate),
                bit_rate=audio_info.get("bit_rate"),
                file_size=os.path.getsize(audio_file_path),
                voice_id=voice_profile.voice_id,
                voice_name=voice_profile.voice_name,
                language=voice_profile.language,
                voice_type=voice_profile.voice_type,
                emotion=request.emotion,
                speech_rate=request.speech_rate,
                pitch_level=request.pitch_level,
                volume=request.volume,
                quality_score=quality_metrics["overall"],
                naturalness_score=quality_metrics["naturalness"],
                intelligibility_score=quality_metrics["intelligibility"],
                processing_time=processing_time,
                synthesis_successful=True,
                metadata={
                    "engine_used": engine,
                    "voice_profile": voice_profile.dict(),
                    "audio_info": audio_info
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error synthesizing speech: {str(e)}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return TextToSpeechResult(
                synthesis_id=uuid.uuid4(),
                text=request.text,
                synthesized_text="",
                audio_file_path="",
                audio_duration=0.0,
                audio_format=request.format,
                sample_rate=request.sample_rate,
                file_size=0,
                voice_id=request.voice_id or self.default_voice_id,
                voice_name="Unknown",
                language=request.language,
                voice_type=request.voice_type,
                emotion=request.emotion,
                speech_rate=request.speech_rate,
                pitch_level=request.pitch_level,
                volume=request.volume,
                quality_score=0.0,
                naturalness_score=0.0,
                intelligibility_score=0.0,
                processing_time=processing_time,
                synthesis_successful=False,
                processing_errors=[str(e)]
            )
    
    def _validate_request(self, request: TextToSpeechRequest):
        """Validate synthesis request"""
        if not request.text.strip():
            raise ValueError("Text cannot be empty")
        
        if len(request.text) > 5000:
            raise ValueError("Text too long (max 5000 characters)")
        
        if request.volume < 0.0 or request.volume > 2.0:
            raise ValueError("Volume must be between 0.0 and 2.0")
        
        if request.sample_rate not in [8000, 16000, 22050, 44100, 48000]:
            raise ValueError("Invalid sample rate")
    
    def _get_voice_profile(self, voice_id: Optional[str]) -> VoiceProfile:
        """Get voice profile by ID"""
        voice_id = voice_id or self.default_voice_id
        
        if voice_id not in self.voice_profiles:
            # Return default voice if requested voice not found
            return self.voice_profiles[self.default_voice_id]
        
        return self.voice_profiles[voice_id]
    
    async def _process_text(self, request: TextToSpeechRequest) -> str:
        """Process text for synthesis (SSML, etc.)"""
        text = request.text
        
        if request.ssml:
            # Process SSML markup
            text = await self._process_ssml(text, request)
        else:
            # Add basic SSML wrapper for better control
            text = self._wrap_in_ssml(text, request)
        
        return text
    
    async def _process_ssml(self, ssml_text: str, request: TextToSpeechRequest) -> str:
        """Process SSML markup"""
        # Basic SSML processing
        # In production, you would use a proper SSML parser
        
        # Replace emotion tags
        emotion_mapping = self.ssml_processor.emotion_mapping
        for emotion_key, emotion_type in emotion_mapping.items():
            if emotion_key in ssml_text.lower():
                ssml_text = re.sub(
                    rf'<emotion[^>]*>{emotion_key}</emotion>',
                    f'<prosody rate="{self._get_speech_rate_value(request.speech_rate)}" pitch="{self._get_pitch_value(request.pitch_level)}">{emotion_key}</prosody>',
                    ssml_text,
                    flags=re.IGNORECASE
                )
        
        return ssml_text
    
    def _wrap_in_ssml(self, text: str, request: TextToSpeechRequest) -> str:
        """Wrap plain text in SSML markup"""
        rate_value = self._get_speech_rate_value(request.speech_rate)
        pitch_value = self._get_pitch_value(request.pitch_level)
        
        ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{request.language}">
            <voice name="{request.voice_id or self.default_voice_id}">
                <prosody rate="{rate_value}" pitch="{pitch_value}" volume="{request.volume}">
                    {text}
                </prosody>
            </voice>
        </speak>"""
        
        return ssml
    
    def _get_speech_rate_value(self, speech_rate: SpeechRate) -> str:
        """Convert speech rate enum to SSML value"""
        rate_mapping = {
            SpeechRate.VERY_SLOW: "x-slow",
            SpeechRate.SLOW: "slow",
            SpeechRate.NORMAL: "medium",
            SpeechRate.FAST: "fast",
            SpeechRate.VERY_FAST: "x-fast"
        }
        return rate_mapping.get(speech_rate, "medium")
    
    def _get_pitch_value(self, pitch_level: PitchLevel) -> str:
        """Convert pitch level enum to SSML value"""
        pitch_mapping = {
            PitchLevel.VERY_LOW: "x-low",
            PitchLevel.LOW: "low",
            PitchLevel.NORMAL: "medium",
            PitchLevel.HIGH: "high",
            PitchLevel.VERY_HIGH: "x-high"
        }
        return pitch_mapping.get(pitch_level, "medium")
    
    def _select_engine(self, voice_type: VoiceType, voice_profile: VoiceProfile) -> str:
        """Select appropriate synthesis engine"""
        if voice_type == VoiceType.NEURAL and 'edge_tts' in self.engines:
            return 'edge_tts'
        elif 'gtts' in self.engines:
            return 'gtts'
        elif 'pyttsx3' in self.engines:
            return 'pyttsx3'
        else:
            raise ValueError("No suitable TTS engine available")
    
    async def _synthesize_with_engine(
        self, 
        engine: str, 
        text: str, 
        request: TextToSpeechRequest,
        voice_profile: VoiceProfile
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Synthesize speech using specified engine"""
        
        if engine == 'edge_tts':
            return await self._synthesize_with_edge_tts(text, request, voice_profile)
        elif engine == 'gtts':
            return await self._synthesize_with_gtts(text, request, voice_profile)
        elif engine == 'pyttsx3':
            return await self._synthesize_with_pyttsx3(text, request, voice_profile)
        else:
            raise ValueError(f"Unsupported engine: {engine}")
    
    async def _synthesize_with_edge_tts(
        self, 
        text: str, 
        request: TextToSpeechRequest,
        voice_profile: VoiceProfile
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Synthesize using Edge TTS"""
        try:
            # Map voice profiles to actual Edge TTS voices
            voice_mapping = {
                "en-US-Neural2-F": "en-US-JennyNeural",
                "en-US-Neural2-M": "en-US-GuyNeural", 
                "en-GB-Neural2-F": "en-GB-SoniaNeural"
            }
            
            voice = voice_mapping.get(voice_profile.voice_id, "en-US-JennyNeural")
            
            communicate = edge_tts.Communicate(text, voice)
            audio_data = b""
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            # Convert to desired format
            audio_info = {
                "sample_rate": 24000,  # Edge TTS default
                "duration": len(audio_data) / 24000,  # Approximate
                "bit_rate": 128000
            }
            
            return audio_data, audio_info
            
        except Exception as e:
            self.logger.error(f"Edge TTS synthesis failed: {str(e)}")
            raise
    
    async def _synthesize_with_gtts(
        self, 
        text: str, 
        request: TextToSpeechRequest,
        voice_profile: VoiceProfile
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Synthesize using gTTS"""
        try:
            # Create temporary file for gTTS
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Generate speech
            tts = gTTS(text=text, lang=request.language, slow=False)
            tts.save(temp_file_path)
            
            # Read audio data
            with open(temp_file_path, 'rb') as f:
                audio_data = f.read()
            
            # Get audio info
            try:
                from pydub import AudioSegment
                audio_segment = AudioSegment.from_mp3(temp_file_path)
                audio_info = {
                    "sample_rate": audio_segment.frame_rate,
                    "duration": len(audio_segment) / 1000.0,
                    "bit_rate": 128000
                }
            except ImportError:
                # Fallback if pydub is not available
                audio_info = {
                    "sample_rate": 44100,  # Default for mp3
                    "duration": len(audio_data) / 44100,  # Approximate
                    "bit_rate": 128000
                }
            
            # Clean up
            os.unlink(temp_file_path)
            
            return audio_data, audio_info
            
        except Exception as e:
            self.logger.error(f"gTTS synthesis failed: {str(e)}")
            raise
    
    async def _synthesize_with_pyttsx3(
        self, 
        text: str, 
        request: TextToSpeechRequest,
        voice_profile: VoiceProfile
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Synthesize using pyttsx3"""
        try:
            engine = self.engines['pyttsx3']
            
            # Configure engine
            engine.setProperty('rate', self._get_rate_value(request.speech_rate))
            engine.setProperty('volume', request.volume)
            
            # Set voice
            voices = engine.getProperty('voices')
            if voices:
                # Try to find matching voice
                for voice in voices:
                    if voice_profile.language.lower() in voice.id.lower():
                        engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use first available voice
                    engine.setProperty('voice', voices[0].id)
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Synthesize speech
            engine.save_to_file(text, temp_file_path)
            engine.runAndWait()
            
            # Read audio data
            with open(temp_file_path, 'rb') as f:
                audio_data = f.read()
            
            # Get audio info
            with wave.open(temp_file_path, 'rb') as wav_file:
                audio_info = {
                    "sample_rate": wav_file.getframerate(),
                    "duration": wav_file.getnframes() / wav_file.getframerate(),
                    "bit_rate": wav_file.getframerate() * wav_file.getsampwidth() * 8
                }
            
            # Clean up
            os.unlink(temp_file_path)
            
            return audio_data, audio_info
            
        except Exception as e:
            self.logger.error(f"pyttsx3 synthesis failed: {str(e)}")
            raise
    
    def _get_rate_value(self, speech_rate: SpeechRate) -> int:
        """Convert speech rate enum to pyttsx3 rate value"""
        rate_mapping = {
            SpeechRate.VERY_SLOW: 100,
            SpeechRate.SLOW: 150,
            SpeechRate.NORMAL: 200,
            SpeechRate.FAST: 250,
            SpeechRate.VERY_FAST: 300
        }
        return rate_mapping.get(speech_rate, 200)
    
    async def _save_audio_file(
        self, 
        audio_data: bytes, 
        audio_info: Dict[str, Any], 
        format: str
    ) -> str:
        """Save audio data to file"""
        try:
            # Create output file path
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"tts_synthesis_{timestamp}.{format}"
            output_path = os.path.join("/tmp", filename)
            
            # Save audio data
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            
            self.logger.info(f"Audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error saving audio file: {str(e)}")
            raise
    
    async def _calculate_quality_metrics(
        self, 
        audio_data: bytes, 
        audio_info: Dict[str, Any],
        voice_profile: VoiceProfile
    ) -> Dict[str, float]:
        """Calculate quality metrics for synthesized speech"""
        try:
            # Basic quality metrics (in production, you would use more sophisticated analysis)
            naturalness = voice_profile.quality_metrics.get("naturalness", 0.8)
            intelligibility = voice_profile.quality_metrics.get("intelligibility", 0.9)
            
            # Adjust based on audio characteristics
            if audio_info.get("sample_rate", 0) >= 22050:
                intelligibility *= 1.1
            
            if audio_info.get("duration", 0) > 0:
                # Longer audio might have more variation
                naturalness *= 0.95
            
            overall = (naturalness + intelligibility) / 2
            
            return {
                "naturalness": min(1.0, naturalness),
                "intelligibility": min(1.0, intelligibility),
                "overall": min(1.0, overall)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating quality metrics: {str(e)}")
            return {
                "naturalness": 0.7,
                "intelligibility": 0.8,
                "overall": 0.75
            }
    
    async def get_available_voices(self) -> List[VoiceProfile]:
        """Get list of available voices"""
        return list(self.voice_profiles.values())
    
    async def get_voice_profile(self, voice_id: str) -> Optional[VoiceProfile]:
        """Get specific voice profile"""
        return self.voice_profiles.get(voice_id)
    
    async def batch_synthesize(
        self, 
        requests: List[TextToSpeechRequest]
    ) -> List[TextToSpeechResult]:
        """Synthesize multiple texts in batch"""
        results = []
        
        for request in requests:
            try:
                result = await self.synthesize_speech(request)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error in batch synthesis: {str(e)}")
                # Add error result
                results.append(TextToSpeechResult(
                    synthesis_id=uuid.uuid4(),
                    text=request.text,
                    synthesized_text="",
                    audio_file_path="",
                    audio_duration=0.0,
                    audio_format=request.format,
                    sample_rate=request.sample_rate,
                    file_size=0,
                    voice_id=request.voice_id or self.default_voice_id,
                    voice_name="Unknown",
                    language=request.language,
                    voice_type=request.voice_type,
                    emotion=request.emotion,
                    speech_rate=request.speech_rate,
                    pitch_level=request.pitch_level,
                    volume=request.volume,
                    quality_score=0.0,
                    naturalness_score=0.0,
                    intelligibility_score=0.0,
                    processing_time=0.0,
                    synthesis_successful=False,
                    processing_errors=[str(e)]
                ))
        
        return results 