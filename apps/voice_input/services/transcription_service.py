"""
Transcription Service
Service for converting speech to text using various transcription models.
"""

import asyncio
import os
import tempfile
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import whisper
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

from common.utils.logging import get_logger
from ..models.transcription import TranscriptionResult, TranscriptionSegment


logger = get_logger(__name__)


class TranscriptionService:
    """Service for speech-to-text transcription"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.whisper_model = None
        self.translation_model = None
        self.tokenizer = None
        self.supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko']
        
    async def initialize_models(self):
        """Initialize transcription models"""
        try:
            # Load Whisper model for transcription
            self.whisper_model = whisper.load_model("base")
            self.logger.info("Whisper model loaded successfully")
            
            # Load translation model for language detection and translation
            model_name = "Helsinki-NLP/opus-mt-mul-en"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.translation_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self.logger.info("Translation model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing transcription models: {str(e)}")
            raise
    
    async def transcribe_audio(
        self, 
        audio_file_path: str, 
        voice_input_id: UUID,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text
        
        Args:
            audio_file_path: Path to the audio file
            voice_input_id: ID of the voice input record
            language: Expected language (optional, will auto-detect if not provided)
            
        Returns:
            TranscriptionResult with transcription details
        """
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Transcribing audio for voice input {voice_input_id}")
            
            # Initialize models if not already done
            if self.whisper_model is None:
                await self.initialize_models()
            
            # Validate audio file
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Transcribe with Whisper
            if language:
                result = self.whisper_model.transcribe(
                    audio_file_path, 
                    language=language,
                    task="transcribe"
                )
            else:
                result = self.whisper_model.transcribe(
                    audio_file_path,
                    task="transcribe"
                )
            
            # Extract transcription details
            full_text = result["text"].strip()
            detected_language = result.get("language", "unknown")
            language_confidence = result.get("language_probability", 0.0)
            
            # Process segments
            segments = []
            for segment in result.get("segments", []):
                transcription_segment = TranscriptionSegment(
                    start_time=segment["start"],
                    end_time=segment["end"],
                    text=segment["text"].strip(),
                    confidence=segment.get("avg_logprob", 0.0),
                    speaker_id=None,  # Whisper doesn't do speaker diarization by default
                    language=detected_language,
                    metadata={
                        "no_speech_prob": segment.get("no_speech_prob", 0.0),
                        "temperature": segment.get("temperature", 0.0)
                    }
                )
                segments.append(transcription_segment)
            
            # Calculate overall confidence
            if segments:
                overall_confidence = sum(seg.confidence for seg in segments) / len(segments)
            else:
                overall_confidence = 0.0
            
            # Detect speaker count (basic implementation)
            speaker_count = 1  # Default to 1 speaker
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return TranscriptionResult(
                voice_input_id=voice_input_id,
                transcription_successful=True,
                processing_time=processing_time,
                full_text=full_text,
                segments=segments,
                detected_language=detected_language,
                language_confidence=language_confidence,
                overall_confidence=overall_confidence,
                speaker_count=speaker_count,
                transcription_model="whisper-base",
                processed_at=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error transcribing audio for {voice_input_id}: {str(e)}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return TranscriptionResult(
                voice_input_id=voice_input_id,
                transcription_successful=False,
                processing_time=processing_time,
                full_text="",
                segments=[],
                detected_language="unknown",
                language_confidence=0.0,
                overall_confidence=0.0,
                speaker_count=0,
                transcription_model="whisper-base",
                transcription_errors=[str(e)],
                processed_at=datetime.utcnow()
            )
    
    async def enhance_transcription(
        self, 
        transcription_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Enhance transcription with context-aware corrections
        
        Args:
            transcription_text: Original transcription text
            context: Additional context for enhancement
            
        Returns:
            Enhanced transcription text
        """
        try:
            # Basic enhancement: capitalize sentences and fix common errors
            enhanced_text = transcription_text.strip()
            
            # Capitalize first letter of sentences
            sentences = enhanced_text.split('. ')
            enhanced_sentences = []
            for sentence in sentences:
                if sentence:
                    enhanced_sentences.append(sentence[0].upper() + sentence[1:])
            
            enhanced_text = '. '.join(enhanced_sentences)
            
            # Fix common transcription errors
            common_fixes = {
                "i'm": "I'm",
                "i'll": "I'll",
                "i've": "I've",
                "i'd": "I'd",
                "don't": "don't",
                "can't": "can't",
                "won't": "won't",
                "it's": "it's",
                "that's": "that's",
                "there's": "there's",
                "here's": "here's"
            }
            
            for wrong, correct in common_fixes.items():
                enhanced_text = enhanced_text.replace(wrong, correct)
            
            # Apply health-specific corrections if context indicates health domain
            if context and context.get("domain") == "health":
                health_fixes = {
                    "blood pressure": "blood pressure",
                    "heart rate": "heart rate",
                    "blood sugar": "blood sugar",
                    "temperature": "temperature",
                    "pain": "pain",
                    "symptom": "symptom",
                    "medication": "medication",
                    "doctor": "doctor",
                    "hospital": "hospital"
                }
                
                for wrong, correct in health_fixes.items():
                    enhanced_text = enhanced_text.replace(wrong, correct)
            
            return enhanced_text
            
        except Exception as e:
            self.logger.error(f"Error enhancing transcription: {str(e)}")
            return transcription_text  # Return original if enhancement fails
    
    async def translate_text(
        self, 
        text: str, 
        source_language: str, 
        target_language: str = "en"
    ) -> str:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code (default: English)
            
        Returns:
            Translated text
        """
        try:
            if source_language == target_language:
                return text
            
            # Use the translation model
            if self.translation_model is None:
                await self.initialize_models()
            
            # Prepare input for translation
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
            
            # Generate translation
            with torch.no_grad():
                translated = self.translation_model.generate(**inputs)
            
            # Decode translation
            translated_text = self.tokenizer.decode(translated[0], skip_special_tokens=True)
            
            return translated_text
            
        except Exception as e:
            self.logger.error(f"Error translating text: {str(e)}")
            return text  # Return original if translation fails
    
    async def detect_language(self, text: str) -> Dict[str, float]:
        """
        Detect language of text with confidence scores
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of language codes and confidence scores
        """
        try:
            # Use a simple language detection approach
            # In production, you might want to use a more sophisticated library like langdetect
            
            # This is a simplified implementation
            # You could integrate with services like Google Cloud Translation API or Azure Translator
            
            # For now, return a default result
            return {
                "en": 0.8,
                "es": 0.1,
                "fr": 0.05,
                "de": 0.03,
                "other": 0.02
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting language: {str(e)}")
            return {"en": 1.0}  # Default to English
    
    async def extract_keywords(self, text: str, domain: str = "general") -> List[str]:
        """
        Extract keywords from transcribed text
        
        Args:
            text: Transcribed text
            domain: Domain for keyword extraction (health, general, etc.)
            
        Returns:
            List of extracted keywords
        """
        try:
            # Simple keyword extraction based on frequency and domain
            words = text.lower().split()
            
            # Remove common stop words
            stop_words = {
                "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", 
                "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
                "have", "has", "had", "do", "does", "did", "will", "would", "could",
                "should", "may", "might", "can", "this", "that", "these", "those"
            }
            
            # Filter out stop words and short words
            keywords = [word for word in words if word not in stop_words and len(word) > 2]
            
            # Add domain-specific keywords for health
            if domain == "health":
                health_keywords = {
                    "pain", "symptom", "medication", "doctor", "hospital", "blood", 
                    "pressure", "heart", "rate", "temperature", "fever", "headache",
                    "nausea", "dizziness", "fatigue", "appointment", "emergency"
                }
                keywords.extend([word for word in words if word in health_keywords])
            
            # Return unique keywords
            return list(set(keywords))
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {str(e)}")
            return [] 