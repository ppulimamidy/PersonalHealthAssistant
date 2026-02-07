"""
Multi-Modal Service
Service for combining and processing multiple input modalities.
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import uuid
import numpy as np

from common.utils.logging import get_logger
from ..models.multi_modal import (
    MultiModalRequest,
    MultiModalResult,
    FusionStrategy,
    ModalityType,
    ConfidenceScore,
    ProcessingStatus,
    MultiModalInput,
    VoiceInput,
    TextInput,
    ImageInput,
    SensorInput
)
from .voice_processing_service import VoiceProcessingService
from .transcription_service import TranscriptionService
from .intent_recognition_service import IntentRecognitionService
from .medical_integration_service import MedicalIntegrationService


logger = get_logger(__name__)


class MultiModalService:
    """Service for processing multi-modal inputs"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.voice_processor = VoiceProcessingService()
        self.transcription_service = TranscriptionService()
        self.intent_recognition_service = IntentRecognitionService()
        self.medical_integration_service = MedicalIntegrationService()
        
        # Fusion strategies
        self.fusion_strategies = {
            "early": self._early_fusion,
            "late": self._late_fusion,
            "hybrid": self._hybrid_fusion
        }
    
    async def process_multi_modal_input(
        self, 
        multi_modal_input: MultiModalInput
    ) -> MultiModalResult:
        """
        Process multi-modal input combining all modalities
        
        Args:
            multi_modal_input: Combined multi-modal input data
            
        Returns:
            MultiModalResult with combined analysis
        """
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Processing multi-modal input for patient {multi_modal_input.patient_id}")
            
            # Process each modality
            voice_result = None
            text_result = None
            image_result = None
            sensor_result = None
            
            # Process voice input if present
            if multi_modal_input.voice_input:
                voice_result = await self._process_voice_modality(multi_modal_input.voice_input)
            
            # Process text input if present
            if multi_modal_input.text_input:
                text_result = await self._process_text_modality(multi_modal_input.text_input)
            
            # Process image input if present
            if multi_modal_input.image_input:
                image_result = await self._process_image_modality(multi_modal_input.image_input)
            
            # Process sensor inputs if present
            if multi_modal_input.sensor_inputs:
                sensor_result = await self._process_sensor_modality(multi_modal_input.sensor_inputs)
            
            # Combine results using fusion strategy
            combined_result = await self._fuse_modalities(
                voice_result, text_result, image_result, sensor_result, multi_modal_input
            )
            
            # Perform medical analysis if medical intent is detected
            medical_analysis_result = None
            if self._is_medical_query(combined_result["combined_text"], combined_result["primary_intent"]):
                medical_analysis_result = await self._perform_medical_analysis(
                    multi_modal_input, combined_result
                )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return MultiModalResult(
                input_id=uuid.uuid4(),  # Generate new ID for multi-modal result
                processing_successful=True,
                processing_time=processing_time,
                combined_text=combined_result["combined_text"],
                primary_intent=combined_result["primary_intent"],
                confidence_score=combined_result["confidence_score"],
                voice_processing_result=voice_result,
                text_processing_result=text_result,
                image_processing_result=image_result,
                sensor_processing_result=sensor_result,
                entities=combined_result["entities"],
                health_indicators=combined_result["health_indicators"],
                recommendations=combined_result["recommendations"],
                medical_analysis_result=medical_analysis_result,
                processed_at=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error processing multi-modal input: {str(e)}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return MultiModalResult(
                input_id=uuid.uuid4(),
                processing_successful=False,
                processing_time=processing_time,
                combined_text="",
                primary_intent="error",
                confidence_score=0.0,
                processing_errors=[str(e)],
                processed_at=datetime.utcnow()
            )
    
    async def _process_voice_modality(self, voice_input: VoiceInput) -> Dict[str, Any]:
        """Process voice modality"""
        try:
            # Process audio quality
            audio_result = await self.voice_processor.process_voice_input(
                voice_input.audio_file_path, 
                uuid.uuid4()
            )
            
            # Transcribe audio
            transcription_result = await self.transcription_service.transcribe_audio(
                voice_input.audio_file_path,
                uuid.uuid4()
            )
            
            # Recognize intent from transcription
            intent_result = await self.intent_recognition_service.recognize_intent(
                transcription_result.full_text,
                uuid.uuid4()
            )
            
            return {
                "audio_quality": audio_result.dict() if audio_result else None,
                "transcription": transcription_result.dict() if transcription_result else None,
                "intent": intent_result.dict() if intent_result else None,
                "text": transcription_result.full_text if transcription_result else "",
                "confidence": transcription_result.overall_confidence if transcription_result else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Error processing voice modality: {str(e)}")
            return {
                "error": str(e),
                "text": "",
                "confidence": 0.0
            }
    
    async def _process_text_modality(self, text_input: TextInput) -> Dict[str, Any]:
        """Process text modality"""
        try:
            # Recognize intent from text
            intent_result = await self.intent_recognition_service.recognize_intent(
                text_input.text_content,
                uuid.uuid4()
            )
            
            # Extract health-specific information
            health_intent = await self.intent_recognition_service.extract_health_intent(
                text_input.text_content
            )
            
            return {
                "intent": intent_result.dict() if intent_result else None,
                "health_intent": health_intent.dict() if health_intent else None,
                "text": text_input.text_content,
                "confidence": intent_result.primary_intent.confidence if intent_result else 0.0,
                "language": text_input.language,
                "source": text_input.source
            }
            
        except Exception as e:
            self.logger.error(f"Error processing text modality: {str(e)}")
            return {
                "error": str(e),
                "text": text_input.text_content,
                "confidence": 0.0
            }
    
    async def _process_image_modality(self, image_input: ImageInput) -> Dict[str, Any]:
        """Process image modality"""
        try:
            # Basic image analysis (placeholder for actual image processing)
            # In production, you would integrate with computer vision services
            
            image_analysis = {
                "format": image_input.image_format,
                "size": image_input.image_size,
                "ocr_text": image_input.ocr_text or "",
                "analysis": image_input.image_analysis or {}
            }
            
            # Extract text from image if OCR is available
            extracted_text = image_input.ocr_text or ""
            
            # Recognize intent from OCR text if available
            intent_result = None
            if extracted_text:
                intent_result = await self.intent_recognition_service.recognize_intent(
                    extracted_text,
                    uuid.uuid4()
                )
            
            return {
                "image_analysis": image_analysis,
                "intent": intent_result.dict() if intent_result else None,
                "text": extracted_text,
                "confidence": intent_result.primary_intent.confidence if intent_result else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Error processing image modality: {str(e)}")
            return {
                "error": str(e),
                "text": "",
                "confidence": 0.0
            }
    
    async def _process_sensor_modality(self, sensor_inputs: List[SensorInput]) -> Dict[str, Any]:
        """Process sensor modality"""
        try:
            # Analyze sensor data
            sensor_analysis = {}
            health_indicators = {}
            
            for sensor in sensor_inputs:
                sensor_type = sensor.sensor_type
                sensor_value = sensor.sensor_value
                
                # Store sensor data
                if sensor_type not in sensor_analysis:
                    sensor_analysis[sensor_type] = []
                
                sensor_analysis[sensor_type].append({
                    "value": sensor_value,
                    "unit": sensor.unit,
                    "timestamp": sensor.timestamp.isoformat(),
                    "device_id": sensor.device_id,
                    "location": sensor.location
                })
                
                # Extract health indicators
                if sensor_type in ["heart_rate", "blood_pressure", "temperature", "blood_sugar"]:
                    health_indicators[sensor_type] = {
                        "value": sensor_value,
                        "unit": sensor.unit,
                        "timestamp": sensor.timestamp.isoformat()
                    }
            
            # Generate text description of sensor data
            sensor_text = self._generate_sensor_text(sensor_inputs)
            
            return {
                "sensor_analysis": sensor_analysis,
                "health_indicators": health_indicators,
                "text": sensor_text,
                "confidence": 0.9,  # Sensor data is typically reliable
                "sensor_count": len(sensor_inputs)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing sensor modality: {str(e)}")
            return {
                "error": str(e),
                "text": "",
                "confidence": 0.0
            }
    
    async def _fuse_modalities(
        self,
        voice_result: Optional[Dict[str, Any]],
        text_result: Optional[Dict[str, Any]],
        image_result: Optional[Dict[str, Any]],
        sensor_result: Optional[Dict[str, Any]],
        input_data: MultiModalInput
    ) -> Dict[str, Any]:
        """Fuse results from different modalities"""
        
        # Collect all text inputs
        texts = []
        confidences = []
        
        if voice_result and voice_result.get("text"):
            texts.append(voice_result["text"])
            confidences.append(voice_result.get("confidence", 0.0))
        
        if text_result and text_result.get("text"):
            texts.append(text_result["text"])
            confidences.append(text_result.get("confidence", 0.0))
        
        if image_result and image_result.get("text"):
            texts.append(image_result["text"])
            confidences.append(image_result.get("confidence", 0.0))
        
        if sensor_result and sensor_result.get("text"):
            texts.append(sensor_result["text"])
            confidences.append(sensor_result.get("confidence", 0.0))
        
        # Combine text
        combined_text = " ".join(texts) if texts else ""
        
        # Determine primary intent
        primary_intent = "unknown"
        overall_confidence = 0.0
        
        # Collect all intents and their confidences
        all_intents = []
        
        for result in [voice_result, text_result, image_result]:
            if result and result.get("intent"):
                intent_data = result["intent"]
                if intent_data.get("primary_intent"):
                    all_intents.append({
                        "intent": intent_data["primary_intent"]["intent_name"],
                        "confidence": intent_data["primary_intent"]["confidence"],
                        "priority": intent_data["primary_intent"]["priority"]
                    })
        
        # Select primary intent based on confidence and priority
        if all_intents:
            # Sort by priority first, then by confidence
            all_intents.sort(key=lambda x: (x["priority"], x["confidence"]), reverse=True)
            primary_intent = all_intents[0]["intent"]
            overall_confidence = all_intents[0]["confidence"]
        
        # Combine entities
        entities = []
        for result in [voice_result, text_result, image_result]:
            if result and result.get("intent") and result["intent"].get("entities"):
                entities.extend(result["intent"]["entities"])
        
        # Combine health indicators
        health_indicators = {}
        if sensor_result and sensor_result.get("health_indicators"):
            health_indicators.update(sensor_result["health_indicators"])
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            primary_intent, health_indicators, input_data.urgency_level
        )
        
        return {
            "combined_text": combined_text,
            "primary_intent": primary_intent,
            "confidence_score": overall_confidence,
            "entities": entities,
            "health_indicators": health_indicators,
            "recommendations": recommendations
        }
    
    def _generate_sensor_text(self, sensor_inputs: List[SensorInput]) -> str:
        """Generate text description of sensor data"""
        if not sensor_inputs:
            return ""
        
        descriptions = []
        for sensor in sensor_inputs:
            unit_str = f" {sensor.unit}" if sensor.unit else ""
            location_str = f" at {sensor.location}" if sensor.location else ""
            descriptions.append(f"{sensor.sensor_type.replace('_', ' ')}: {sensor.sensor_value}{unit_str}{location_str}")
        
        return ". ".join(descriptions)
    
    def _generate_recommendations(
        self, 
        primary_intent: str, 
        health_indicators: Dict[str, Any], 
        urgency_level: int
    ) -> List[str]:
        """Generate recommendations based on intent and health indicators"""
        recommendations = []
        
        # Emergency recommendations
        if urgency_level >= 4:
            recommendations.append("Consider seeking immediate medical attention")
        
        # Intent-based recommendations
        if primary_intent == "symptom_report":
            recommendations.append("Schedule an appointment with your healthcare provider")
            recommendations.append("Monitor your symptoms and keep a symptom diary")
        
        elif primary_intent == "medication_query":
            recommendations.append("Consult with your pharmacist or healthcare provider")
            recommendations.append("Review your medication schedule and dosages")
        
        elif primary_intent == "appointment_request":
            recommendations.append("Contact your healthcare provider's office")
            recommendations.append("Prepare a list of questions for your appointment")
        
        elif primary_intent == "wellness_query":
            recommendations.append("Consider lifestyle modifications for better health")
            recommendations.append("Track your wellness metrics regularly")
        
        # Health indicator-based recommendations
        if "heart_rate" in health_indicators:
            hr_value = health_indicators["heart_rate"]["value"]
            if hr_value > 100:
                recommendations.append("Your heart rate is elevated - consider rest and relaxation")
            elif hr_value < 60:
                recommendations.append("Your heart rate is low - consult with your healthcare provider")
        
        if "blood_pressure" in health_indicators:
            bp_value = health_indicators["blood_pressure"]["value"]
            if isinstance(bp_value, dict) and bp_value.get("systolic", 0) > 140:
                recommendations.append("Your blood pressure is elevated - consider lifestyle changes")
        
        return recommendations
    
    async def _early_fusion(self, modalities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Early fusion strategy - combine raw features"""
        # Placeholder for early fusion implementation
        return {"method": "early_fusion", "result": "combined_features"}
    
    async def _late_fusion(self, modalities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Late fusion strategy - combine processed results"""
        # Placeholder for late fusion implementation
        return {"method": "late_fusion", "result": "combined_results"}
    
    async def _hybrid_fusion(self, modalities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Hybrid fusion strategy - combine both early and late fusion"""
        # Placeholder for hybrid fusion implementation
        return {"method": "hybrid_fusion", "result": "combined_hybrid"} 

    async def _perform_medical_analysis(
        self, 
        multi_modal_input: MultiModalInput,
        combined_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Perform medical analysis on multi-modal input"""
        try:
            # Extract symptoms and medical context
            symptoms = self._extract_symptoms_from_combined_result(combined_result)
            medical_context = self._extract_medical_context(combined_result)
            
            # Perform medical analysis
            medical_result = await self.medical_integration_service.analyze_medical_query(
                patient_id=multi_modal_input.patient_id,
                query_text=combined_result["combined_text"],
                symptoms=symptoms,
                medical_history=medical_context,
                session_id=multi_modal_input.session_id,
                analysis_type="comprehensive"
            )
            
            return medical_result
            
        except Exception as e:
            self.logger.error(f"Error in medical analysis: {str(e)}")
            return None
    
    def _is_medical_query(self, combined_text: str, primary_intent: str) -> bool:
        """Check if the query is medical-related"""
        # Check intent
        medical_intents = ["symptom_report", "medication_query", "emergency_alert", "wellness_query"]
        if primary_intent in medical_intents:
            return True
        
        # Check text content
        medical_keywords = [
            "pain", "ache", "hurt", "symptom", "condition", "diagnosis", "treatment",
            "medicine", "medication", "doctor", "health", "medical", "disease",
            "fever", "headache", "nausea", "fatigue", "cough", "rash", "lesion"
        ]
        
        text_lower = combined_text.lower()
        return any(keyword in text_lower for keyword in medical_keywords)
    
    def _extract_symptoms_from_combined_result(self, combined_result: Dict[str, Any]) -> List[str]:
        """Extract symptoms from combined result"""
        symptoms = []
        
        # Extract from combined text
        if combined_result.get("combined_text"):
            text_lower = combined_result["combined_text"].lower()
            symptom_keywords = [
                "pain", "ache", "hurt", "sore", "uncomfortable", "discomfort",
                "headache", "stomachache", "backache", "toothache",
                "fever", "temperature", "hot", "cold", "chills",
                "nausea", "vomit", "sick", "dizzy", "lightheaded",
                "fatigue", "tired", "exhausted", "weak",
                "cough", "sneeze", "runny nose", "congestion"
            ]
            
            for keyword in symptom_keywords:
                if keyword in text_lower:
                    symptoms.append(keyword)
        
        # Extract from entities
        entities = combined_result.get("entities", [])
        for entity in entities:
            if hasattr(entity, 'entity_type') and entity.entity_type == 'symptom':
                symptoms.append(entity.entity_value)
        
        return list(set(symptoms))  # Remove duplicates
    
    def _extract_medical_context(self, combined_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract medical context from combined result"""
        return {
            "primary_intent": combined_result.get("primary_intent"),
            "confidence_score": combined_result.get("confidence_score"),
            "entities": combined_result.get("entities", []),
            "health_indicators": combined_result.get("health_indicators", {}),
            "recommendations": combined_result.get("recommendations", [])
        } 