"""
Intent Recognition API
API endpoints for recognizing user intentions from voice input.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import uuid
from fastapi import APIRouter, HTTPException, Form, Body
from pydantic import BaseModel

from ..models.intent_recognition import (
    IntentRecognitionResult,
    Intent,
    Entity,
    HealthIntent
)
from ..services.intent_recognition_service import IntentRecognitionService
from common.utils.logging import get_logger

logger = get_logger(__name__)

intent_recognition_router = APIRouter(prefix="/intent", tags=["Intent Recognition"])

# Initialize service
intent_recognition_service = IntentRecognitionService()


class IntentRecognitionRequest(BaseModel):
    """Request model for intent recognition"""
    text: str
    voice_input_id: Optional[UUID] = None
    context: Optional[Dict[str, Any]] = None


@intent_recognition_router.post("/recognize", response_model=IntentRecognitionResult)
async def recognize_intent(request: IntentRecognitionRequest):
    """
    Recognize intent from text
    
    - **text**: Text to analyze for intent
    - **voice_input_id**: Associated voice input ID (optional)
    - **context**: Additional context for intent recognition
    """
    try:
        logger.info(f"Recognizing intent from text: {request.text[:50]}...")
        
        # Recognize intent
        intent_result = await intent_recognition_service.recognize_intent(
            request.text,
            request.voice_input_id or uuid.uuid4(),
            request.context
        )
        
        return intent_result
        
    except Exception as e:
        logger.error(f"Error recognizing intent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error recognizing intent: {str(e)}")


@intent_recognition_router.post("/health-intent", response_model=HealthIntent)
async def extract_health_intent(text: str = Form(...)):
    """
    Extract health-specific intent information
    
    - **text**: Text to analyze for health intent
    """
    try:
        logger.info("Extracting health intent from text")
        
        # Extract health intent
        health_intent = await intent_recognition_service.extract_health_intent(text)
        
        return health_intent
        
    except Exception as e:
        logger.error(f"Error extracting health intent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting health intent: {str(e)}")


@intent_recognition_router.post("/analyze-sentiment")
async def analyze_sentiment(text: str = Form(...)):
    """
    Analyze sentiment of text
    
    - **text**: Text to analyze for sentiment
    """
    try:
        logger.info("Analyzing sentiment of text")
        
        # This would use the sentiment analyzer from the service
        # For now, return mock data
        sentiment_result = {
            "text": text,
            "sentiment": "neutral",
            "confidence": 0.75,
            "positive_score": 0.3,
            "negative_score": 0.2,
            "neutral_score": 0.5
        }
        
        return sentiment_result
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing sentiment: {str(e)}")


@intent_recognition_router.post("/extract-entities")
async def extract_entities(text: str = Form(...)):
    """
    Extract entities from text
    
    - **text**: Text to extract entities from
    """
    try:
        logger.info("Extracting entities from text")
        
        # This would use the entity extraction from the service
        # For now, return mock data
        entities = [
            {
                "entity_type": "symptom",
                "entity_value": "headache",
                "confidence": 0.9,
                "start_position": 15,
                "end_position": 24
            },
            {
                "entity_type": "body_part",
                "entity_value": "head",
                "confidence": 0.8,
                "start_position": 0,
                "end_position": 4
            }
        ]
        
        return {
            "text": text,
            "entities": entities,
            "entity_count": len(entities)
        }
        
    except Exception as e:
        logger.error(f"Error extracting entities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting entities: {str(e)}")


@intent_recognition_router.post("/determine-urgency")
async def determine_urgency(text: str = Form(...)):
    """
    Determine urgency level from text
    
    - **text**: Text to analyze for urgency
    """
    try:
        logger.info("Determining urgency level from text")
        
        # This would use the urgency determination from the service
        # For now, return mock data
        urgency_result = {
            "text": text,
            "urgency_level": 3,
            "urgency_description": "moderate",
            "keywords_found": ["pain", "discomfort"],
            "recommendation": "Schedule appointment within 24-48 hours"
        }
        
        return urgency_result
        
    except Exception as e:
        logger.error(f"Error determining urgency: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error determining urgency: {str(e)}")


@intent_recognition_router.get("/intents", response_model=List[Dict[str, Any]])
async def get_available_intents():
    """
    Get list of available intents and their patterns
    """
    try:
        logger.info("Retrieving available intents")
        
        # Return intent patterns from the service
        intents = [
            {
                "intent_name": "symptom_report",
                "category": "health",
                "priority": 4,
                "requires_action": True,
                "description": "User reporting health symptoms",
                "examples": ["I have a headache", "My stomach hurts", "I'm feeling dizzy"]
            },
            {
                "intent_name": "medication_query",
                "category": "health",
                "priority": 2,
                "requires_action": False,
                "description": "User asking about medications",
                "examples": ["When should I take my medicine?", "Do I need a refill?"]
            },
            {
                "intent_name": "appointment_request",
                "category": "health",
                "priority": 3,
                "requires_action": True,
                "description": "User requesting medical appointment",
                "examples": ["I need to see a doctor", "Can I schedule an appointment?"]
            },
            {
                "intent_name": "emergency_alert",
                "category": "health",
                "priority": 5,
                "requires_action": True,
                "description": "User reporting emergency situation",
                "examples": ["I'm having chest pain", "This is an emergency"]
            },
            {
                "intent_name": "wellness_query",
                "category": "health",
                "priority": 1,
                "requires_action": False,
                "description": "User asking about wellness and lifestyle",
                "examples": ["How can I improve my health?", "What exercises should I do?"]
            }
        ]
        
        return intents
        
    except Exception as e:
        logger.error(f"Error retrieving available intents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving available intents: {str(e)}")


@intent_recognition_router.get("/entities", response_model=List[Dict[str, Any]])
async def get_available_entities():
    """
    Get list of available entity types and their patterns
    """
    try:
        logger.info("Retrieving available entities")
        
        # Return entity patterns from the service
        entities = [
            {
                "entity_type": "body_part",
                "description": "Anatomical body parts",
                "examples": ["head", "neck", "shoulder", "arm", "chest", "back", "stomach", "leg"]
            },
            {
                "entity_type": "symptom",
                "description": "Health symptoms and conditions",
                "examples": ["pain", "headache", "fever", "nausea", "fatigue", "cough"]
            },
            {
                "entity_type": "medication",
                "description": "Medication names",
                "examples": ["aspirin", "ibuprofen", "insulin", "metformin"]
            },
            {
                "entity_type": "severity",
                "description": "Severity levels",
                "examples": ["mild", "moderate", "severe", "intense", "sharp"]
            },
            {
                "entity_type": "duration",
                "description": "Time durations",
                "examples": ["hours", "days", "weeks", "months", "years"]
            },
            {
                "entity_type": "time",
                "description": "Time references",
                "examples": ["today", "tomorrow", "morning", "afternoon", "evening"]
            }
        ]
        
        return entities
        
    except Exception as e:
        logger.error(f"Error retrieving available entities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving available entities: {str(e)}")


@intent_recognition_router.post("/batch-recognize")
async def batch_recognize_intents(texts: List[str] = Body(...)):
    """
    Recognize intents from multiple texts in batch
    
    - **texts**: List of texts to analyze
    """
    try:
        logger.info(f"Batch recognizing intents for {len(texts)} texts")
        
        results = []
        
        for text in texts:
            try:
                # Recognize intent for each text
                intent_result = await intent_recognition_service.recognize_intent(
                    text,
                    uuid.uuid4()
                )
                
                results.append({
                    "text": text,
                    "success": intent_result.recognition_successful,
                    "primary_intent": intent_result.primary_intent.intent_name if intent_result.primary_intent else None,
                    "confidence": intent_result.primary_intent.confidence if intent_result.primary_intent else 0.0,
                    "urgency_level": intent_result.urgency_level,
                    "sentiment": intent_result.sentiment,
                    "entity_count": len(intent_result.entities)
                })
                
            except Exception as e:
                results.append({
                    "text": text,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "batch_id": str(uuid.uuid4()),
            "total_texts": len(texts),
            "successful_recognitions": len([r for r in results if r["success"]]),
            "failed_recognitions": len([r for r in results if not r["success"]]),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in batch intent recognition: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in batch intent recognition: {str(e)}") 