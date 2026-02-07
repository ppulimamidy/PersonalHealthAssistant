"""
Intent Recognition Service
Service for understanding user intentions and extracting entities from voice input.
"""

import asyncio
import re
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import spacy
from transformers import pipeline

from common.utils.logging import get_logger
from ..models.intent_recognition import (
    IntentRecognitionRequest,
    IntentRecognitionResult,
    IntentType,
    EntityType,
    Entity,
    Intent,
    IntentConfidence,
    EntityConfidence,
    HealthIntent
)


logger = get_logger(__name__)


class IntentRecognitionService:
    """Service for recognizing user intentions from voice input"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.nlp = None
        self.sentiment_analyzer = None
        
        # Intent patterns for health domain
        self.health_intent_patterns = {
            "symptom_report": [
                r"\b(pain|ache|hurt|sore|uncomfortable|discomfort)\b",
                r"\b(headache|stomachache|backache|toothache)\b",
                r"\b(fever|temperature|hot|cold|chills)\b",
                r"\b(nausea|vomit|sick|dizzy|lightheaded)\b",
                r"\b(fatigue|tired|exhausted|weak)\b",
                r"\b(cough|sneeze|runny nose|congestion)\b"
            ],
            "medication_query": [
                r"\b(medication|medicine|pill|drug|prescription)\b",
                r"\b(dose|dosage|take|refill|side effect)\b",
                r"\b(when|how much|how often|missed)\b"
            ],
            "appointment_request": [
                r"\b(appointment|schedule|book|reschedule|cancel)\b",
                r"\b(doctor|physician|specialist|clinic|hospital)\b",
                r"\b(urgent|emergency|asap|soon)\b"
            ],
            "emergency_alert": [
                r"\b(emergency|urgent|critical|severe|serious)\b",
                r"\b(chest pain|heart attack|stroke|bleeding)\b",
                r"\b(can't breathe|difficulty breathing|shortness of breath)\b",
                r"\b(unconscious|passed out|fainted)\b"
            ],
            "wellness_query": [
                r"\b(exercise|workout|fitness|diet|nutrition)\b",
                r"\b(sleep|rest|stress|anxiety|mood)\b",
                r"\b(weight|blood pressure|heart rate|steps)\b"
            ]
        }
        
        # Entity patterns
        self.entity_patterns = {
            "body_part": [
                r"\b(head|neck|shoulder|arm|hand|finger|chest|back|stomach|leg|foot|toe)\b",
                r"\b(eye|ear|nose|mouth|throat|heart|lung|liver|kidney)\b"
            ],
            "severity": [
                r"\b(mild|moderate|severe|intense|sharp|dull|throbbing)\b",
                r"\b(slight|minor|major|extreme|unbearable)\b"
            ],
            "duration": [
                r"\b(hours?|days?|weeks?|months?|years?)\b",
                r"\b(since|for|about|around|approximately)\b"
            ],
            "medication": [
                r"\b(aspirin|ibuprofen|acetaminophen|tylenol|advil)\b",
                r"\b(insulin|metformin|lisinopril|amlodipine|atorvastatin)\b"
            ],
            "time": [
                r"\b(today|tomorrow|yesterday|morning|afternoon|evening|night)\b",
                r"\b(week|month|year|hour|minute)\b"
            ]
        }
    
    async def initialize_models(self):
        """Initialize NLP models"""
        try:
            # Load spaCy model for NLP tasks
            self.nlp = spacy.load("en_core_web_sm")
            
            # Load sentiment analysis model
            self.sentiment_analyzer = pipeline("sentiment-analysis")
            
            self.logger.info("Intent recognition models loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing intent recognition models: {str(e)}")
            raise
    
    async def recognize_intent(
        self, 
        transcription_text: str, 
        voice_input_id: UUID,
        context: Optional[Dict[str, Any]] = None
    ) -> IntentRecognitionResult:
        """
        Recognize intent from transcribed text
        
        Args:
            transcription_text: Transcribed text from voice input
            voice_input_id: ID of the voice input record
            context: Additional context for intent recognition
            
        Returns:
            IntentRecognitionResult with recognized intents and entities
        """
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Recognizing intent for voice input {voice_input_id}")
            
            # Initialize models if not already done
            if self.nlp is None:
                await self.initialize_models()
            
            # Analyze text with spaCy
            doc = self.nlp(transcription_text.lower())
            
            # Recognize intents
            intents = await self._recognize_intents(transcription_text, doc)
            
            # Extract entities
            entities = await self._extract_entities(transcription_text, doc)
            
            # Analyze sentiment
            sentiment = await self._analyze_sentiment(transcription_text)
            
            # Determine urgency level
            urgency_level = await self._determine_urgency(transcription_text, intents)
            
            # Extract context
            extracted_context = await self._extract_context(transcription_text, doc, context)
            
            # Get primary intent
            primary_intent = intents[0] if intents else Intent(
                intent_name="unknown",
                confidence=0.0,
                category="general",
                priority=1,
                requires_action=False
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return IntentRecognitionResult(
                voice_input_id=voice_input_id,
                transcription_text=transcription_text,
                recognition_successful=True,
                processing_time=processing_time,
                primary_intent=primary_intent,
                secondary_intents=intents[1:] if len(intents) > 1 else [],
                entities=entities,
                context=extracted_context,
                sentiment=sentiment,
                urgency_level=urgency_level,
                recognition_model="spacy+patterns",
                processed_at=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error recognizing intent for {voice_input_id}: {str(e)}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return IntentRecognitionResult(
                voice_input_id=voice_input_id,
                transcription_text=transcription_text,
                recognition_successful=False,
                processing_time=processing_time,
                primary_intent=Intent(
                    intent_name="error",
                    confidence=0.0,
                    category="error",
                    priority=1,
                    requires_action=False
                ),
                secondary_intents=[],
                entities=[],
                context={},
                sentiment="neutral",
                urgency_level=1,
                recognition_model="spacy+patterns",
                recognition_errors=[str(e)],
                processed_at=datetime.utcnow()
            )
    
    async def _recognize_intents(self, text: str, doc) -> List[Intent]:
        """Recognize intents from text using pattern matching and NLP"""
        intents = []
        text_lower = text.lower()
        
        # Check health-specific intents
        for intent_name, patterns in self.health_intent_patterns.items():
            confidence = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    matches += 1
            
            if matches > 0:
                confidence = min(matches / len(patterns), 1.0)
                
                # Determine category and priority
                category = "health"
                priority = 1
                requires_action = False
                
                if intent_name == "emergency_alert":
                    priority = 5
                    requires_action = True
                elif intent_name == "appointment_request":
                    priority = 3
                    requires_action = True
                elif intent_name == "symptom_report":
                    priority = 4
                    requires_action = True
                elif intent_name == "medication_query":
                    priority = 2
                    requires_action = False
                
                intent = Intent(
                    intent_name=intent_name,
                    confidence=confidence,
                    category=category,
                    priority=priority,
                    requires_action=requires_action,
                    metadata={"pattern_matches": matches}
                )
                intents.append(intent)
        
        # Sort by confidence and priority
        intents.sort(key=lambda x: (x.confidence, x.priority), reverse=True)
        
        return intents
    
    async def _extract_entities(self, text: str, doc) -> List[Entity]:
        """Extract entities from text"""
        entities = []
        text_lower = text.lower()
        
        # Extract entities using patterns
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    entity = Entity(
                        entity_type=entity_type,
                        entity_value=match.group(),
                        confidence=0.8,  # Pattern-based confidence
                        start_position=match.start(),
                        end_position=match.end(),
                        metadata={"pattern": pattern}
                    )
                    entities.append(entity)
        
        # Extract entities using spaCy NER
        for ent in doc.ents:
            # Map spaCy entity types to our types
            entity_type_mapping = {
                "PERSON": "person",
                "ORG": "organization",
                "GPE": "location",
                "DATE": "date",
                "TIME": "time",
                "CARDINAL": "number",
                "QUANTITY": "measurement"
            }
            
            entity_type = entity_type_mapping.get(ent.label_, ent.label_.lower())
            
            entity = Entity(
                entity_type=entity_type,
                entity_value=ent.text,
                confidence=0.9,  # spaCy confidence
                start_position=ent.start_char,
                end_position=ent.end_char,
                metadata={"spacy_label": ent.label_}
            )
            entities.append(entity)
        
        return entities
    
    async def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of the text"""
        try:
            if self.sentiment_analyzer is None:
                return "neutral"
            
            result = self.sentiment_analyzer(text[:512])  # Limit text length
            sentiment = result[0]["label"].lower()
            
            # Map sentiment labels
            sentiment_mapping = {
                "positive": "positive",
                "negative": "negative",
                "neutral": "neutral"
            }
            
            return sentiment_mapping.get(sentiment, "neutral")
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {str(e)}")
            return "neutral"
    
    async def _determine_urgency(self, text: str, intents: List[Intent]) -> int:
        """Determine urgency level based on text and intents"""
        urgency_level = 1  # Default low urgency
        
        text_lower = text.lower()
        
        # Check for emergency keywords
        emergency_keywords = [
            "emergency", "urgent", "critical", "severe", "serious",
            "immediately", "asap", "now", "help", "danger"
        ]
        
        for keyword in emergency_keywords:
            if keyword in text_lower:
                urgency_level = 5
                break
        
        # Check intent priority
        if intents:
            max_priority = max(intent.priority for intent in intents)
            urgency_level = max(urgency_level, max_priority)
        
        return urgency_level
    
    async def _extract_context(self, text: str, doc, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract context from text and provided context"""
        extracted_context = {}
        
        # Extract temporal context
        temporal_keywords = ["today", "yesterday", "tomorrow", "morning", "afternoon", "evening", "night"]
        for keyword in temporal_keywords:
            if keyword in text.lower():
                extracted_context["temporal"] = keyword
                break
        
        # Extract location context
        location_entities = [ent for ent in doc.ents if ent.label_ in ["GPE", "LOC"]]
        if location_entities:
            extracted_context["location"] = location_entities[0].text
        
        # Extract person context
        person_entities = [ent for ent in doc.ents if ent.label_ == "PERSON"]
        if person_entities:
            extracted_context["person"] = person_entities[0].text
        
        # Merge with provided context
        if context:
            extracted_context.update(context)
        
        return extracted_context
    
    async def extract_health_intent(self, text: str) -> HealthIntent:
        """Extract health-specific intent information"""
        try:
            text_lower = text.lower()
            
            # Extract symptoms
            symptoms = []
            symptom_patterns = [
                r"\b(headache|migraine|stomachache|backache|toothache)\b",
                r"\b(fever|chills|sweating|hot|cold)\b",
                r"\b(nausea|vomiting|dizziness|lightheaded)\b",
                r"\b(fatigue|tiredness|weakness|exhaustion)\b",
                r"\b(cough|sneeze|runny nose|congestion|sore throat)\b",
                r"\b(chest pain|shortness of breath|difficulty breathing)\b"
            ]
            
            for pattern in symptom_patterns:
                matches = re.findall(pattern, text_lower)
                symptoms.extend(matches)
            
            # Extract medications
            medications = []
            medication_patterns = [
                r"\b(aspirin|ibuprofen|acetaminophen|tylenol|advil)\b",
                r"\b(insulin|metformin|lisinopril|amlodipine|atorvastatin)\b"
            ]
            
            for pattern in medication_patterns:
                matches = re.findall(pattern, text_lower)
                medications.extend(matches)
            
            # Extract body parts
            body_parts = []
            body_part_patterns = [
                r"\b(head|neck|shoulder|arm|hand|chest|back|stomach|leg|foot)\b",
                r"\b(eye|ear|nose|mouth|throat|heart|lung)\b"
            ]
            
            for pattern in body_part_patterns:
                matches = re.findall(pattern, text_lower)
                body_parts.extend(matches)
            
            # Determine severity level
            severity_level = None
            if any(word in text_lower for word in ["severe", "intense", "unbearable"]):
                severity_level = "severe"
            elif any(word in text_lower for word in ["moderate", "medium"]):
                severity_level = "moderate"
            elif any(word in text_lower for word in ["mild", "slight", "minor"]):
                severity_level = "mild"
            
            # Determine duration
            duration = None
            duration_patterns = [
                r"(\d+)\s*(hours?|days?|weeks?|months?)",
                r"(since|for)\s*(\d+)\s*(hours?|days?|weeks?|months?)"
            ]
            
            for pattern in duration_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    duration = match.group()
                    break
            
            return HealthIntent(
                symptoms=list(set(symptoms)),
                medications=list(set(medications)),
                body_parts=list(set(body_parts)),
                severity_level=severity_level,
                duration=duration
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting health intent: {str(e)}")
            return HealthIntent() 