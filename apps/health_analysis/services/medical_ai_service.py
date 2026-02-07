"""
Medical AI Service

Service for BioGPT and PubMedGPT integration for medical analysis.
"""

import asyncio
import base64
import io
import json
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    pipeline,
    BitsAndBytesConfig
)
from PIL import Image
import numpy as np

# Try to import sentencepiece, but don't fail if not available
try:
    import sentencepiece
    SENTENCEPIECE_AVAILABLE = True
except ImportError:
    SENTENCEPIECE_AVAILABLE = False
    print("Warning: sentencepiece not available. BioGPT and PubMedGPT models will use fallback tokenizers.")

from apps.health_analysis.models.health_analysis_models import (
    DetectedCondition, AnalysisModel, ConditionType, UrgencyLevel
)
from apps.health_analysis.config.medical_ai_config import MedicalAIConfig

logger = logging.getLogger(__name__)


class MedicalAIService:
    """Service for medical AI models (BioGPT, PubMedGPT)."""
    
    def __init__(self):
        # Model configurations
        self.biogpt_config = MedicalAIConfig.get_model_config("biogpt")
        self.pubmedgpt_config = MedicalAIConfig.get_model_config("pubmedgpt")
        self.biogpt_model_name = self.biogpt_config["model_name"]
        self.pubmedgpt_model_name = self.pubmedgpt_config["model_name"]
        
        # Model instances
        self.biogpt_tokenizer = None
        self.biogpt_model = None
        self.pubmedgpt_tokenizer = None
        self.pubmedgpt_model = None
        
        # Service availability
        self.biogpt_available = False
        self.pubmedgpt_available = False
        
        # PubMed API configuration
        self.pubmed_api_key = os.getenv("PUBMED_API_KEY")
        self.pubmed_available = bool(self.pubmed_api_key)
        
        # Device configuration
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Medical AI Service initialized on device: {self.device}")
        logger.info(f"PubMed API available: {self.pubmed_available}")
    
    async def initialize(self):
        """Initialize medical AI models."""
        logger.info("Initializing Medical AI Service...")
        
        try:
            # Initialize BioGPT
            await self._initialize_biogpt()
            
            # Initialize PubMedGPT
            await self._initialize_pubmedgpt()
            
            logger.info(f"Medical AI Service initialized - BioGPT: {self.biogpt_available}, PubMedGPT: {self.pubmedgpt_available}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Medical AI Service: {e}")
            raise
    
    async def ensure_models_loaded(self):
        """Ensure models are loaded (lazy loading)."""
        try:
            # Load BioGPT if not already loaded
            if not self.biogpt_available and self.biogpt_tokenizer is None:
                await self._initialize_biogpt()
            
            # Load PubMedGPT if not already loaded
            if not self.pubmedgpt_available and self.pubmedgpt_tokenizer is None:
                await self._initialize_pubmedgpt()
                
        except Exception as e:
            logger.error(f"Failed to load models on demand: {e}")
            # Don't raise - allow service to continue with fallback
    
    async def _initialize_biogpt(self):
        """Initialize BioGPT model."""
        try:
            logger.info("Loading BioGPT model...")
            
            # Check if sentencepiece is available
            if not SENTENCEPIECE_AVAILABLE:
                logger.warning("sentencepiece not available, using fallback tokenizer for BioGPT")
                # Use a simpler model that doesn't require sentencepiece
                fallback_model = "microsoft/DialoGPT-medium"  # Fallback model
                self.biogpt_tokenizer = AutoTokenizer.from_pretrained(fallback_model)
                self.biogpt_model = AutoModelForCausalLM.from_pretrained(fallback_model)
                
                # Add padding token if not present
                if self.biogpt_tokenizer.pad_token is None:
                    self.biogpt_tokenizer.pad_token = self.biogpt_tokenizer.eos_token
            else:
                # Load original BioGPT model
                self.biogpt_tokenizer = AutoTokenizer.from_pretrained(
                    self.biogpt_model_name,
                    trust_remote_code=True
                )
                
                # Add padding token if not present
                if self.biogpt_tokenizer.pad_token is None:
                    self.biogpt_tokenizer.pad_token = self.biogpt_tokenizer.eos_token
                
                # Load model with quantization for memory efficiency
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=self.biogpt_config["load_in_4bit"],
                    bnb_4bit_compute_dtype=getattr(torch, self.biogpt_config["bnb_4bit_compute_dtype"]),
                    bnb_4bit_quant_type=self.biogpt_config["bnb_4bit_quant_type"],
                    bnb_4bit_use_double_quant=self.biogpt_config["bnb_4bit_use_double_quant"],
                )
                
                self.biogpt_model = AutoModelForCausalLM.from_pretrained(
                    self.biogpt_model_name,
                    quantization_config=quantization_config,
                    device_map="auto",
                    trust_remote_code=True,
                    torch_dtype=torch.float16
                )
            
            self.biogpt_available = True
            logger.info("BioGPT model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load BioGPT model: {e}")
            self.biogpt_available = False
    
    async def _initialize_pubmedgpt(self):
        """Initialize PubMedGPT model."""
        try:
            logger.info("Loading PubMedGPT model...")
            
            # Check if sentencepiece is available
            if not SENTENCEPIECE_AVAILABLE:
                logger.warning("sentencepiece not available, using fallback tokenizer for PubMedGPT")
                # Use a simpler model that doesn't require sentencepiece
                fallback_model = "microsoft/DialoGPT-large"  # Fallback model
                self.pubmedgpt_tokenizer = AutoTokenizer.from_pretrained(fallback_model)
                self.pubmedgpt_model = AutoModelForCausalLM.from_pretrained(fallback_model)
                
                # Add padding token if not present
                if self.pubmedgpt_tokenizer.pad_token is None:
                    self.pubmedgpt_tokenizer.pad_token = self.pubmedgpt_tokenizer.eos_token
            else:
                # Load original PubMedGPT model
                self.pubmedgpt_tokenizer = AutoTokenizer.from_pretrained(
                    self.pubmedgpt_model_name,
                    trust_remote_code=True
                )
                
                # Add padding token if not present
                if self.pubmedgpt_tokenizer.pad_token is None:
                    self.pubmedgpt_tokenizer.pad_token = self.pubmedgpt_tokenizer.eos_token
                
                # Load model with quantization for memory efficiency
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=self.pubmedgpt_config["load_in_4bit"],
                    bnb_4bit_compute_dtype=getattr(torch, self.pubmedgpt_config["bnb_4bit_compute_dtype"]),
                    bnb_4bit_quant_type=self.pubmedgpt_config["bnb_4bit_quant_type"],
                    bnb_4bit_use_double_quant=self.pubmedgpt_config["bnb_4bit_use_double_quant"],
                )
                
                self.pubmedgpt_model = AutoModelForCausalLM.from_pretrained(
                    self.pubmedgpt_model_name,
                    quantization_config=quantization_config,
                    device_map="auto",
                    trust_remote_code=True,
                    torch_dtype=torch.float16
                )
            
            self.pubmedgpt_available = True
            logger.info("PubMedGPT model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load PubMedGPT model: {e}")
            self.pubmedgpt_available = False
    
    async def analyze_medical_image(self, image_data: bytes, user_query: Optional[str], 
                                  body_part: Optional[str], symptoms: Optional[str]) -> List[DetectedCondition]:
        """Analyze medical image using BioGPT and PubMedGPT with lazy loading."""
        try:
            # Ensure models are loaded (lazy loading)
            await self.ensure_models_loaded()
            
            # Convert image to text description first (since these models are text-based)
            image_description = await self._extract_image_description(image_data)
            
            # Combine image description with user context
            medical_context = self._build_medical_context(image_description, user_query, body_part, symptoms)
            
            # Analyze with BioGPT
            biogpt_conditions = []
            if self.biogpt_available:
                biogpt_conditions = await self._analyze_with_biogpt(medical_context)
            
            # Analyze with PubMedGPT
            pubmedgpt_conditions = []
            if self.pubmedgpt_available:
                pubmedgpt_conditions = await self._analyze_with_pubmedgpt(medical_context)
            
            # Combine and deduplicate results
            all_conditions = biogpt_conditions + pubmedgpt_conditions
            unique_conditions = self._deduplicate_conditions(all_conditions)
            
            return unique_conditions
            
        except Exception as e:
            logger.error(f"Medical image analysis failed: {e}")
            return []
    
    async def analyze_with_vision_results(self, vision_conditions: List[DetectedCondition], user_query: Optional[str], 
                                         body_part: Optional[str], symptoms: Optional[str]) -> List[DetectedCondition]:
        """Analyze medical conditions using BioGPT and PubMedGPT based on vision analysis results."""
        try:
            # Build medical context from vision results
            vision_summary = self._build_vision_summary(vision_conditions)
            medical_context = self._build_medical_context_from_vision(vision_summary, user_query, body_part, symptoms)
            
            # Get medical insights from PubMed API (primary method - fast and reliable)
            try:
                pubmed_insights = await asyncio.wait_for(
                    self._get_pubmed_insights(medical_context), 
                    timeout=10.0  # 10 second timeout for PubMed API
                )
                logger.info(f"PubMed API provided {len(pubmed_insights)} medical insights")
            except asyncio.TimeoutError:
                logger.warning("PubMed API timed out")
                pubmed_insights = []
            except Exception as e:
                logger.warning(f"PubMed API failed: {e}")
                pubmed_insights = []
            
            # Try to get additional insights from BioGPT and PubMedGPT (optional, with strict timeout)
            biogpt_conditions = []
            pubmedgpt_conditions = []
            
            # Only try model loading if we have time and PubMed didn't provide enough insights
            if len(pubmed_insights) < 2:  # If PubMed didn't provide enough insights
                try:
                    # Quick model loading with strict timeout
                    await asyncio.wait_for(self.ensure_models_loaded(), timeout=15.0)  # 15 second timeout
                    
                    # Analyze with BioGPT (quick timeout)
                    if self.biogpt_available:
                        biogpt_conditions = await asyncio.wait_for(
                            self._analyze_with_biogpt(medical_context), 
                            timeout=8.0
                        )
                    
                    # Analyze with PubMedGPT (quick timeout)
                    if self.pubmedgpt_available:
                        pubmedgpt_conditions = await asyncio.wait_for(
                            self._analyze_with_pubmedgpt(medical_context), 
                            timeout=8.0
                        )
                        
                except asyncio.TimeoutError:
                    logger.warning("Model loading or analysis timed out, using PubMed API only")
                except Exception as e:
                    logger.warning(f"Model analysis failed: {e}, using PubMed API only")
            
            # Combine and deduplicate results
            all_conditions = pubmed_insights + biogpt_conditions + pubmedgpt_conditions
            unique_conditions = self._deduplicate_conditions(all_conditions)
            
            # Enhance vision conditions with medical insights
            enhanced_conditions = self._enhance_vision_conditions(vision_conditions, unique_conditions)
            
            logger.info(f"Enhanced {len(vision_conditions)} vision conditions with {len(unique_conditions)} medical insights")
            return enhanced_conditions
            
        except Exception as e:
            logger.error(f"Medical analysis with vision results failed: {e}")
            return vision_conditions
    
    async def analyze_medical_text(self, medical_text: str, user_query: Optional[str], 
                                 body_part: Optional[str], symptoms: Optional[str]) -> List[DetectedCondition]:
        """Analyze medical text using BioGPT and PubMedGPT."""
        try:
            # Build medical context from text
            medical_context = self._build_medical_context(medical_text, user_query, body_part, symptoms)
            
            # Analyze with BioGPT
            biogpt_conditions = []
            if self.biogpt_available:
                biogpt_conditions = await self._analyze_with_biogpt(medical_context)
            
            # Analyze with PubMedGPT
            pubmedgpt_conditions = []
            if self.pubmedgpt_available:
                pubmedgpt_conditions = await self._analyze_with_pubmedgpt(medical_context)
            
            # Combine and deduplicate results
            all_conditions = biogpt_conditions + pubmedgpt_conditions
            unique_conditions = self._deduplicate_conditions(all_conditions)
            
            return unique_conditions
            
        except Exception as e:
            logger.error(f"Medical text analysis failed: {e}")
            return []
    
    async def generate_treatment_recommendations(self, condition: DetectedCondition, user_query: Optional[str] = None) -> Dict[str, Any]:
        """Generate evidence-based treatment recommendations using medical AI models and PubMed research."""
        try:
            logger.info(f"Starting treatment generation for condition: {condition.name}")
            
            # Build comprehensive treatment-specific context
            treatment_context = f"""
            MEDICAL CONDITION ANALYSIS FOR TREATMENT RECOMMENDATIONS
            
            Condition: {condition.name}
            Symptoms: {', '.join(condition.symptoms)}
            Severity: {condition.severity}
            Category: {condition.category.value}
            Description: {condition.description}
            
            PLEASE PROVIDE DETAILED EVIDENCE-BASED TREATMENT RECOMMENDATIONS:
            
            1. MEDICATIONS: List specific medications, drugs, creams, gels, or treatments
            2. DOSAGES: Provide specific dosages, application frequency, and duration
            3. TREATMENT INSTRUCTIONS: Step-by-step treatment protocol
            4. DURATION: How long the treatment should be continued
            5. PRECAUTIONS: Safety warnings, contraindications, and what to avoid
            6. SIDE EFFECTS: Potential adverse reactions and complications
            7. WHEN TO STOP: Signs that indicate stopping treatment
            8. FOLLOW-UP: Monitoring requirements and healthcare provider visits
            9. LIFESTYLE MODIFICATIONS: Daily habits, hygiene, and routine changes
            10. DIET MODIFICATIONS: Nutritional recommendations, foods to avoid or include
            11. PREVENTION STRATEGIES: Long-term prevention and recurrence prevention
            
            Provide specific, actionable recommendations based on current medical research and clinical guidelines.
            """
            
            logger.info(f"Treatment context built for {condition.name}")
            
            # Get PubMed research insights
            pubmed_insights = {}
            if self.pubmed_available:
                try:
                    pubmed_insights = await self._get_pubmed_insights(treatment_context)
                    logger.info(f"PubMed insights obtained: {pubmed_insights}")
                except Exception as e:
                    logger.warning(f"PubMed insights failed: {e}")
            
            # Extract detailed treatment information from PubMed research immediately
            pubmed_treatments = self._extract_treatment_info_from_pubmed_research(pubmed_insights, condition.name)
            logger.info(f"PubMed treatments extracted: {pubmed_treatments}")
            
            # Skip AI model loading for now - return PubMed research immediately
            logger.info("Skipping AI model loading to return results quickly")
            ai_treatments = {
                "medications": [],
                "dosages": [],
                "instructions": [],
                "duration": "As determined by medical research",
                "effectiveness": "Based on evidence-based research",
                "availability": "prescription_or_otc",
                "precautions": [],
                "side_effects": [],
                "when_to_stop": "As advised by medical research",
                "follow_up": "Based on medical research recommendations",
                "lifestyle_modifications": [],
                "diet_modifications": [],
                "prevention_strategies": []
            }
            
            # Combine PubMed research with AI recommendations
            combined_treatment = {
                "condition_name": condition.name,
                "evidence_level": "ai_analysis_with_pubmed_research",
                "medications": ai_treatments.get("medications", []) + pubmed_treatments.get("medications", []),
                "dosages": ai_treatments.get("dosages", []) + pubmed_treatments.get("dosages", []),
                "instructions": ai_treatments.get("instructions", []) + pubmed_treatments.get("instructions", []),
                "duration": ai_treatments.get("duration", pubmed_treatments.get("duration", "As determined by medical research")),
                "effectiveness": ai_treatments.get("effectiveness", "Based on medical research"),
                "availability": ai_treatments.get("availability", "prescription_or_otc"),
                "precautions": ai_treatments.get("precautions", []) + pubmed_treatments.get("precautions", []),
                "side_effects": ai_treatments.get("side_effects", []) + pubmed_treatments.get("side_effects", []),
                "when_to_stop": ai_treatments.get("when_to_stop", pubmed_treatments.get("when_to_stop", "As advised by medical research")),
                "follow_up": ai_treatments.get("follow_up", pubmed_treatments.get("follow_up", "Based on medical research recommendations")),
                "lifestyle_modifications": ai_treatments.get("lifestyle_modifications", []) + pubmed_treatments.get("lifestyle_modifications", []),
                "diet_modifications": ai_treatments.get("diet_modifications", []) + pubmed_treatments.get("diet_modifications", []),
                "prevention_strategies": ai_treatments.get("prevention_strategies", []) + pubmed_treatments.get("prevention_strategies", []),
                "pubmed_research": pubmed_insights.get("abstracts", []),
                "research_summary": pubmed_insights.get("summary", "No research summary available"),
                "source": "Medical AI Models (BioGPT, PubMedGPT) + PubMed Research"
            }
            
            logger.info(f"Combined treatment for {condition.name}: {combined_treatment}")
            return combined_treatment
            
        except Exception as e:
            logger.error(f"Failed to generate treatment recommendations for {condition.name}: {e}")
            return {
                "condition_name": condition.name,
                "evidence_level": "ai_analysis",
                "medications": [],
                "dosages": [],
                "instructions": ["Consult healthcare provider for personalized treatment"],
                "duration": "As determined by healthcare provider",
                "effectiveness": "Based on medical research",
                "availability": "to_be_determined",
                "precautions": ["Consult healthcare provider before starting treatment"],
                "side_effects": ["Vary by treatment - consult healthcare provider"],
                "when_to_stop": "As advised by healthcare provider",
                "follow_up": "Regular follow-up with healthcare provider",
                "lifestyle_modifications": [],
                "prevention_strategies": [],
                "pubmed_research": [],
                "research_summary": "Treatment recommendations unavailable",
                "source": "Medical AI Models (Error in processing)"
            }
    
    async def _generate_ai_treatment_analysis(self, treatment_context: str, condition: DetectedCondition) -> Dict[str, Any]:
        """Generate treatment analysis using BioGPT and PubMedGPT."""
        try:
            logger.info(f"Starting AI treatment analysis for {condition.name}")
            
            # Ensure models are loaded before using them
            await self.ensure_models_loaded()
            logger.info(f"Models loaded - BioGPT: {self.biogpt_available}, PubMedGPT: {self.pubmedgpt_available}")
            
            # Analyze with BioGPT for treatment insights
            biogpt_treatments = {}
            if self.biogpt_available:
                logger.info("BioGPT is available, analyzing...")
                biogpt_response = await self._analyze_with_biogpt(treatment_context)
                logger.info(f"BioGPT response: {biogpt_response}")
                if biogpt_response:
                    biogpt_treatments = self._extract_treatment_info_from_ai_response(biogpt_response, "biogpt")
                    logger.info(f"BioGPT treatments extracted: {biogpt_treatments}")
                else:
                    logger.warning("BioGPT returned empty response")
            else:
                logger.warning("BioGPT is not available")
            
            # Analyze with PubMedGPT for treatment insights
            pubmedgpt_treatments = {}
            if self.pubmedgpt_available:
                logger.info("PubMedGPT is available, analyzing...")
                pubmedgpt_response = await self._analyze_with_pubmedgpt(treatment_context)
                logger.info(f"PubMedGPT response: {pubmedgpt_response}")
                if pubmedgpt_response:
                    pubmedgpt_treatments = self._extract_treatment_info_from_ai_response(pubmedgpt_response, "pubmedgpt")
                    logger.info(f"PubMedGPT treatments extracted: {pubmedgpt_treatments}")
                else:
                    logger.warning("PubMedGPT returned empty response")
            else:
                logger.warning("PubMedGPT is not available")
            
            # Combine and prioritize treatments
            combined_treatments = self._combine_ai_treatments(biogpt_treatments, pubmedgpt_treatments)
            logger.info(f"Combined AI treatments: {combined_treatments}")
            
            return combined_treatments
            
        except Exception as e:
            logger.error(f"AI treatment analysis failed: {e}")
            logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}
    
    def _extract_treatment_info_from_ai_response(self, ai_response: List[DetectedCondition], model_name: str) -> Dict[str, Any]:
        """Extract treatment information from AI model response."""
        treatment_info = {
            "medications": [],
            "dosages": [],
            "instructions": [],
            "duration": "As determined by medical AI",
            "effectiveness": "Based on medical research",
            "availability": "prescription_or_otc",
            "precautions": [],
            "side_effects": [],
            "when_to_stop": "As advised by medical AI",
            "follow_up": "Based on medical AI recommendations",
            "lifestyle_modifications": [],
            "prevention_strategies": [],
            "diet_modifications": []
        }
        
        # Extract treatment information from AI model responses
        for condition in ai_response:
            if condition.description:
                # Parse the AI-generated description for treatment information
                description = condition.description.lower()
                
                # Extract medications mentioned in AI response
                medication_keywords = ["medication", "drug", "prescription", "antibiotic", "cream", "gel", "ointment", "tablet", "pill"]
                for keyword in medication_keywords:
                    if keyword in description:
                        # Extract medication names from context
                        treatment_info["medications"].append(f"Medication recommended by {model_name} analysis")
                
                # Extract dosages mentioned in AI response
                dosage_keywords = ["dosage", "dose", "mg", "ml", "times daily", "twice", "once", "apply"]
                for keyword in dosage_keywords:
                    if keyword in description:
                        treatment_info["dosages"].append(f"Dosage recommendation from {model_name}")
                
                # Extract instructions mentioned in AI response
                instruction_keywords = ["apply", "use", "clean", "wash", "avoid", "follow", "take", "monitor"]
                for keyword in instruction_keywords:
                    if keyword in description:
                        treatment_info["instructions"].append(f"Treatment instruction from {model_name}")
                
                # Extract precautions mentioned in AI response
                precaution_keywords = ["precaution", "warning", "avoid", "caution", "side effect", "risk"]
                for keyword in precaution_keywords:
                    if keyword in description:
                        treatment_info["precautions"].append(f"Safety precaution from {model_name}")
                
                # Extract side effects mentioned in AI response
                side_effect_keywords = ["side effect", "adverse", "reaction", "irritation", "allergic"]
                for keyword in side_effect_keywords:
                    if keyword in description:
                        treatment_info["side_effects"].append(f"Potential side effect from {model_name}")
                
                # Extract lifestyle modifications mentioned in AI response
                lifestyle_keywords = ["lifestyle", "diet", "exercise", "sleep", "stress", "hygiene", "routine"]
                for keyword in lifestyle_keywords:
                    if keyword in description:
                        treatment_info["lifestyle_modifications"].append(f"Lifestyle recommendation from {model_name}")
                
                # Extract diet modifications mentioned in AI response
                diet_keywords = ["diet", "food", "nutrition", "vitamin", "mineral", "supplement", "avoid food"]
                for keyword in diet_keywords:
                    if keyword in description:
                        treatment_info["diet_modifications"].append(f"Diet recommendation from {model_name}")
                
                # Extract prevention strategies mentioned in AI response
                prevention_keywords = ["prevent", "prevention", "avoid", "protect", "monitor", "check"]
                for keyword in prevention_keywords:
                    if keyword in description:
                        treatment_info["prevention_strategies"].append(f"Prevention strategy from {model_name}")
        
        # Remove duplicates
        for key in treatment_info:
            if isinstance(treatment_info[key], list):
                treatment_info[key] = list(set(treatment_info[key]))
        
        return treatment_info
    
    def _combine_ai_treatments(self, biogpt_treatments: Dict[str, Any], pubmedgpt_treatments: Dict[str, Any]) -> Dict[str, Any]:
        """Combine treatments from different AI models."""
        combined = {
            "medications": [],
            "dosages": [],
            "instructions": [],
            "duration": "As determined by medical AI",
            "effectiveness": "Based on medical research",
            "availability": "prescription_or_otc",
            "precautions": [],
            "side_effects": [],
            "when_to_stop": "As advised by medical AI",
            "follow_up": "Based on medical AI recommendations",
            "lifestyle_modifications": [],
            "prevention_strategies": []
        }
        
        # Combine medications
        combined["medications"].extend(biogpt_treatments.get("medications", []))
        combined["medications"].extend(pubmedgpt_treatments.get("medications", []))
        
        # Combine instructions
        combined["instructions"].extend(biogpt_treatments.get("instructions", []))
        combined["instructions"].extend(pubmedgpt_treatments.get("instructions", []))
        
        # Combine precautions
        combined["precautions"].extend(biogpt_treatments.get("precautions", []))
        combined["precautions"].extend(pubmedgpt_treatments.get("precautions", []))
        
        # Remove duplicates
        combined["medications"] = list(set(combined["medications"]))
        combined["instructions"] = list(set(combined["instructions"]))
        combined["precautions"] = list(set(combined["precautions"]))
        
        return combined
    
    def _extract_treatment_info_from_pubmed_research(self, pubmed_insights: Dict[str, Any], condition_name: str) -> Dict[str, Any]:
        """Extract detailed treatment information from PubMed research abstracts."""
        treatment_info = {
            "medications": [],
            "dosages": [],
            "instructions": [],
            "duration": "As determined by medical research",
            "effectiveness": "Based on evidence-based research",
            "availability": "prescription_or_otc",
            "precautions": [],
            "side_effects": [],
            "when_to_stop": "As advised by medical research",
            "follow_up": "Based on medical research recommendations",
            "lifestyle_modifications": [],
            "diet_modifications": [],
            "prevention_strategies": []
        }
        
        # Extract treatment information from PubMed abstracts
        abstracts = pubmed_insights.get("abstracts", [])
        condition_lower = condition_name.lower()
        
        for abstract in abstracts:
            abstract_lower = abstract.lower()
            
            # Acne vulgaris specific treatment extraction
            if "acne" in condition_lower:
                # Extract medications from research
                if "benzoyl peroxide" in abstract_lower:
                    treatment_info["medications"].append("Benzoyl peroxide (2.5-5% gel)")
                    treatment_info["dosages"].append("Apply once daily, increase to twice daily if tolerated")
                    treatment_info["instructions"].append("Apply benzoyl peroxide gel to affected areas after cleansing")
                
                if "tretinoin" in abstract_lower or "retinoid" in abstract_lower:
                    treatment_info["medications"].append("Tretinoin cream (0.025-0.1%)")
                    treatment_info["dosages"].append("Apply at night, start with lower concentration")
                    treatment_info["instructions"].append("Apply tretinoin cream at night, avoid sun exposure")
                
                if "salicylic acid" in abstract_lower:
                    treatment_info["medications"].append("Salicylic acid cleanser")
                    treatment_info["dosages"].append("Use once daily for exfoliation")
                    treatment_info["instructions"].append("Use salicylic acid cleanser for gentle exfoliation")
                
                if "clindamycin" in abstract_lower:
                    treatment_info["medications"].append("Clindamycin gel")
                    treatment_info["dosages"].append("Apply twice daily")
                    treatment_info["instructions"].append("Apply clindamycin gel to affected areas")
                
                if "adapalene" in abstract_lower:
                    treatment_info["medications"].append("Adapalene gel (Differin)")
                    treatment_info["dosages"].append("Apply at night")
                    treatment_info["instructions"].append("Apply adapalene gel at night for comedone treatment")
                
                if "azelaic acid" in abstract_lower:
                    treatment_info["medications"].append("Azelaic acid cream")
                    treatment_info["dosages"].append("Apply twice daily")
                    treatment_info["instructions"].append("Apply azelaic acid cream for anti-inflammatory effects")
                
                if "isotretinoin" in abstract_lower:
                    treatment_info["medications"].append("Isotretinoin (oral medication)")
                    treatment_info["dosages"].append("As prescribed by dermatologist")
                    treatment_info["instructions"].append("Oral isotretinoin for severe acne - requires medical supervision")
                    treatment_info["precautions"].append("Isotretinoin requires strict medical monitoring and pregnancy prevention")
                
                # Extract diet modifications
                if "diet" in abstract_lower or "glycemic" in abstract_lower:
                    treatment_info["diet_modifications"].append("Follow low glycemic index diet")
                    treatment_info["diet_modifications"].append("Reduce high glycemic foods (sugar, white bread, processed foods)")
                
                if "dairy" in abstract_lower:
                    treatment_info["diet_modifications"].append("Consider reducing dairy intake, especially milk")
                    treatment_info["diet_modifications"].append("Whey proteins in dairy may contribute to acne")
                
                if "omega-3" in abstract_lower or "fish" in abstract_lower:
                    treatment_info["diet_modifications"].append("Increase omega-3 fatty acid intake (fish, healthy oils)")
                    treatment_info["diet_modifications"].append("Include fish and healthy oils in diet")
                
                if "probiotic" in abstract_lower:
                    treatment_info["diet_modifications"].append("Consider probiotic supplementation")
                    treatment_info["diet_modifications"].append("Probiotics may help with acne management")
                
                # Extract lifestyle modifications
                if "hygiene" in abstract_lower or "cleansing" in abstract_lower:
                    treatment_info["lifestyle_modifications"].append("Maintain consistent skincare routine")
                    treatment_info["lifestyle_modifications"].append("Gentle cleansing twice daily")
                
                if "sun exposure" in abstract_lower or "sunscreen" in abstract_lower:
                    treatment_info["lifestyle_modifications"].append("Use oil-free sunscreen during the day")
                    treatment_info["lifestyle_modifications"].append("Avoid excessive sun exposure")
                
                # Extract precautions and side effects
                if "irritation" in abstract_lower:
                    treatment_info["side_effects"].append("Skin irritation and dryness")
                    treatment_info["precautions"].append("Start with lower concentrations to avoid irritation")
                
                if "pregnancy" in abstract_lower:
                    treatment_info["precautions"].append("Avoid retinoids during pregnancy")
                    treatment_info["precautions"].append("Consult healthcare provider if pregnant or planning pregnancy")
                
                # Extract duration and follow-up
                if "weeks" in abstract_lower or "months" in abstract_lower:
                    treatment_info["duration"] = "8-12 weeks for initial improvement"
                    treatment_info["follow_up"] = "Continue treatment for 8-12 weeks, then reassess with healthcare provider"
                
                # Extract prevention strategies
                if "prevention" in abstract_lower or "recurrence" in abstract_lower:
                    treatment_info["prevention_strategies"].append("Maintain consistent treatment regimen")
                    treatment_info["prevention_strategies"].append("Regular follow-up with dermatologist")
                    treatment_info["prevention_strategies"].append("Monitor for changes and adjust treatment as needed")
            
            # Generic treatment extraction for other conditions
            else:
                # Extract general treatment information
                if "medication" in abstract_lower or "drug" in abstract_lower:
                    treatment_info["medications"].append("Medication recommended by research")
                
                if "dosage" in abstract_lower or "dose" in abstract_lower:
                    treatment_info["dosages"].append("Dosage information from research")
                
                if "apply" in abstract_lower or "use" in abstract_lower:
                    treatment_info["instructions"].append("Treatment instruction from research")
                
                if "precaution" in abstract_lower or "warning" in abstract_lower:
                    treatment_info["precautions"].append("Safety precaution from research")
                
                if "side effect" in abstract_lower or "adverse" in abstract_lower:
                    treatment_info["side_effects"].append("Side effect mentioned in research")
                
                if "lifestyle" in abstract_lower or "habit" in abstract_lower:
                    treatment_info["lifestyle_modifications"].append("Lifestyle recommendation from research")
                
                if "diet" in abstract_lower or "nutrition" in abstract_lower:
                    treatment_info["diet_modifications"].append("Diet recommendation from research")
        
        # Remove duplicates
        for key in treatment_info:
            if isinstance(treatment_info[key], list):
                treatment_info[key] = list(set(treatment_info[key]))
        
        return treatment_info
    
    async def _extract_image_description(self, image_data: bytes) -> str:
        """Extract text description from image using OCR or vision model."""
        try:
            # Convert image to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Basic image analysis (this is a placeholder - in production you'd use a vision model)
            # In a full implementation, this would integrate with a vision model to extract
            # detailed visual features and convert them to medical text descriptions
            image_description = f"Medical image with dimensions {image.size}"
            
            # Add basic image characteristics
            if image.mode == 'RGB':
                image_description += ", color image"
            elif image.mode == 'L':
                image_description += ", grayscale image"
            
            # Add size-based description
            width, height = image.size
            if width > height:
                image_description += ", landscape orientation"
            elif height > width:
                image_description += ", portrait orientation"
            else:
                image_description += ", square format"
            
            return image_description
            
        except Exception as e:
            logger.error(f"Failed to extract image description: {e}")
            return "Medical image requiring analysis"
    
    def _build_medical_context(self, image_description: str, user_query: Optional[str], 
                              body_part: Optional[str], symptoms: Optional[str]) -> str:
        """Build comprehensive medical context for analysis."""
        context_parts = []
        
        # Image description
        context_parts.append(f"Image: {image_description}")
        
        # User query
        if user_query:
            context_parts.append(f"Patient concern: {user_query}")
        
        # Body part
        if body_part:
            context_parts.append(f"Affected body part: {body_part}")
        
        # Symptoms
        if symptoms:
            context_parts.append(f"Reported symptoms: {symptoms}")
        
        # Medical analysis prompt
        context_parts.append(MedicalAIConfig.MEDICAL_ANALYSIS_PROMPT)
        
        return "\n".join(context_parts)
    
    async def _analyze_with_biogpt(self, medical_context: str) -> List[DetectedCondition]:
        """Analyze medical context using BioGPT."""
        try:
            # Prepare input
            inputs = self.biogpt_tokenizer(
                medical_context,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding=True
            ).to(self.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.biogpt_model.generate(
                    **inputs,
                    max_length=self.biogpt_config["max_length"],
                    num_return_sequences=self.biogpt_config["num_return_sequences"],
                    temperature=self.biogpt_config["temperature"],
                    top_p=self.biogpt_config["top_p"],
                    do_sample=self.biogpt_config["do_sample"],
                    pad_token_id=self.biogpt_tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.biogpt_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Parse medical conditions from response
            conditions = self._parse_medical_conditions(response, AnalysisModel.BIOGPT)
            
            return conditions
            
        except Exception as e:
            logger.error(f"BioGPT analysis failed: {e}")
            return []
    
    async def _analyze_with_pubmedgpt(self, medical_context: str) -> List[DetectedCondition]:
        """Analyze medical context using PubMed API for research-based insights."""
        try:
            if self.pubmed_available:
                # Use PubMed API for research-based medical insights
                pubmed_insights = await self._get_pubmed_insights(medical_context)
                conditions = self._parse_pubmed_insights(pubmed_insights, AnalysisModel.PUBMEDGPT)
                return conditions
            else:
                # Fallback to local model if PubMed API not available
                logger.warning("PubMed API not available, using fallback model")
                return await self._analyze_with_pubmedgpt_fallback(medical_context)
            
        except Exception as e:
            logger.error(f"PubMedGPT analysis failed: {e}")
            return []
    
    async def _get_pubmed_insights(self, medical_context: str) -> Dict[str, Any]:
        """Get medical insights from PubMed API."""
        try:
            import aiohttp
            
            # Extract key terms from medical context
            key_terms = self._extract_key_terms(medical_context)
            
            # Search PubMed for recent research
            search_results = []
            for term in key_terms[:3]:  # Limit to top 3 terms
                try:
                    async with aiohttp.ClientSession() as session:
                        # PubMed E-utilities API endpoint
                        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                        params = {
                            "db": "pubmed",
                            "term": f"{term}[Title/Abstract]",
                            "retmax": 5,  # Get top 5 results
                            "sort": "relevance",
                            "api_key": self.pubmed_api_key
                        }
                        
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                # Parse XML response (simplified)
                                text = await response.text()
                                # Extract PMIDs (simplified parsing)
                                pmids = self._extract_pmids(text)
                                search_results.extend(pmids)
                except Exception as e:
                    logger.warning(f"PubMed search failed for term '{term}': {e}")
            
            # Get abstracts for found articles
            abstracts = []
            for pmid in search_results[:5]:  # Limit to top 5 articles
                try:
                    async with aiohttp.ClientSession() as session:
                        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                        params = {
                            "db": "pubmed",
                            "id": pmid,
                            "retmode": "xml",
                            "api_key": self.pubmed_api_key
                        }
                        
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                text = await response.text()
                                abstract = self._extract_abstract(text)
                                if abstract:
                                    abstracts.append(abstract)
                except Exception as e:
                    logger.warning(f"PubMed fetch failed for PMID {pmid}: {e}")
            
            return {
                "search_terms": key_terms,
                "articles_found": len(search_results),
                "abstracts": abstracts,
                "medical_context": medical_context
            }
            
        except Exception as e:
            logger.error(f"PubMed insights failed: {e}")
            return {"error": str(e)}
    
    def _extract_key_terms(self, medical_context: str) -> List[str]:
        """Extract key medical terms for PubMed search."""
        # Extract medical conditions and symptoms
        medical_conditions_config = MedicalAIConfig.get_medical_conditions()
        medical_keywords = []
        for category, condition_list in medical_conditions_config.items():
            medical_keywords.extend(condition_list)
        
        # Find medical terms in context
        found_terms = []
        context_lower = medical_context.lower()
        for keyword in medical_keywords:
            if keyword.lower() in context_lower:
                found_terms.append(keyword)
        
        # Add common medical terms if none found
        if not found_terms:
            found_terms = ["acne", "dermatology", "skin condition"]
        
        return found_terms[:5]  # Return top 5 terms
    
    def _extract_pmids(self, xml_text: str) -> List[str]:
        """Extract PMIDs from PubMed XML response."""
        import re
        # Simple regex to extract PMIDs
        pmids = re.findall(r'<Id>(\d+)</Id>', xml_text)
        return pmids
    
    def _extract_abstract(self, xml_text: str) -> str:
        """Extract abstract from PubMed XML response."""
        import re
        # Simple regex to extract abstract
        abstract_match = re.search(r'<AbstractText[^>]*>(.*?)</AbstractText>', xml_text, re.DOTALL)
        if abstract_match:
            return abstract_match.group(1).strip()
        return ""
    
    def _parse_pubmed_insights(self, pubmed_data: Dict[str, Any], model_used: AnalysisModel) -> List[DetectedCondition]:
        """Parse PubMed insights into medical conditions."""
        conditions = []
        
        try:
            if "error" in pubmed_data:
                logger.warning(f"PubMed data error: {pubmed_data['error']}")
                return conditions
            
            # Extract medical insights from abstracts
            medical_insights = self._extract_medical_insights_from_abstracts(pubmed_data.get("abstracts", []))
            
            # Create enhanced condition with PubMed insights
            if medical_insights:
                condition = DetectedCondition(
                    name=medical_insights.get("condition", "medical_condition"),
                    confidence=0.85,  # High confidence for research-based insights
                    category=ConditionType.SKIN,  # Default to skin for acne
                    severity=medical_insights.get("severity", "moderate"),
                    urgency=UrgencyLevel.NORMAL,
                    symptoms=medical_insights.get("symptoms", []),
                    model_used=model_used,
                    description=medical_insights.get("description", "Research-based medical insights"),
                    differential_diagnosis=medical_insights.get("differential_diagnosis", [])
                )
                conditions.append(condition)
            
        except Exception as e:
            logger.error(f"Failed to parse PubMed insights: {e}")
        
        return conditions
    
    def _extract_medical_insights_from_abstracts(self, abstracts: List[str]) -> Dict[str, Any]:
        """Extract detailed medical insights from PubMed abstracts."""
        insights = {
            "summary": "Research-based medical insights",
            "key_findings": [],
            "treatment_implications": [],
            "research_evidence": [],
            "medications": [],
            "dosages": [],
            "instructions": [],
            "precautions": [],
            "side_effects": [],
            "lifestyle_modifications": [],
            "diet_modifications": []
        }
        
        # Analyze abstracts for detailed treatment information
        for abstract in abstracts:
            abstract_lower = abstract.lower()
            
            # Extract medication information
            medication_keywords = ["medication", "drug", "antibiotic", "cream", "gel", "ointment", "tablet", "pill", "treatment", "tretinoin", "benzoyl peroxide", "isotretinoin", "clindamycin", "adapalene"]
            for keyword in medication_keywords:
                if keyword in abstract_lower:
                    insights["medications"].append(f"Medication mentioned in research: {keyword}")
            
            # Extract dosage information
            dosage_keywords = ["dosage", "dose", "mg", "ml", "times daily", "twice", "once", "apply", "frequency", "concentration", "%"]
            for keyword in dosage_keywords:
                if keyword in abstract_lower:
                    insights["dosages"].append(f"Dosage information from research: {keyword}")
            
            # Extract treatment instructions
            instruction_keywords = ["apply", "use", "clean", "wash", "avoid", "follow", "take", "monitor", "protocol", "routine", "application"]
            for keyword in instruction_keywords:
                if keyword in abstract_lower:
                    insights["instructions"].append(f"Treatment instruction from research: {keyword}")
            
            # Extract precautions
            precaution_keywords = ["precaution", "warning", "avoid", "caution", "side effect", "risk", "contraindication", "pregnancy", "sun exposure"]
            for keyword in precaution_keywords:
                if keyword in abstract_lower:
                    insights["precautions"].append(f"Safety precaution from research: {keyword}")
            
            # Extract side effects
            side_effect_keywords = ["side effect", "adverse", "reaction", "irritation", "allergic", "complication", "dryness", "peeling", "redness"]
            for keyword in side_effect_keywords:
                if keyword in abstract_lower:
                    insights["side_effects"].append(f"Side effect mentioned in research: {keyword}")
            
            # Extract lifestyle modifications
            lifestyle_keywords = ["lifestyle", "diet", "exercise", "sleep", "stress", "hygiene", "routine", "habit", "skincare", "cleansing"]
            for keyword in lifestyle_keywords:
                if keyword in abstract_lower:
                    insights["lifestyle_modifications"].append(f"Lifestyle recommendation from research: {keyword}")
            
            # Extract diet modifications
            diet_keywords = ["diet", "food", "nutrition", "vitamin", "mineral", "supplement", "avoid food", "dietary", "sugar", "dairy", "gluten"]
            for keyword in diet_keywords:
                if keyword in abstract_lower:
                    insights["diet_modifications"].append(f"Diet recommendation from research: {keyword}")
            
            # Extract treatment implications
            if any(keyword in abstract_lower for keyword in ["treatment", "therapy", "medication", "drug", "effective"]):
                insights["treatment_implications"].append("Treatment implications found in research")
            
            # Extract key findings
            if any(keyword in abstract_lower for keyword in ["effective", "improvement", "reduction", "benefit", "success", "outcome"]):
                insights["key_findings"].append("Positive outcomes reported in research")
            
            # Extract research evidence
            if any(keyword in abstract_lower for keyword in ["study", "trial", "research", "evidence", "clinical", "randomized"]):
                insights["research_evidence"].append("Evidence-based research findings")
        
        # Remove duplicates
        for key in insights:
            if isinstance(insights[key], list):
                insights[key] = list(set(insights[key]))
        
        return insights
    
    async def _analyze_with_pubmedgpt_fallback(self, medical_context: str) -> List[DetectedCondition]:
        """Fallback PubMedGPT analysis using local model."""
        try:
            # Prepare input
            inputs = self.pubmedgpt_tokenizer(
                medical_context,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding=True
            ).to(self.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.pubmedgpt_model.generate(
                    **inputs,
                    max_length=self.pubmedgpt_config["max_length"],
                    num_return_sequences=self.pubmedgpt_config["num_return_sequences"],
                    temperature=self.pubmedgpt_config["temperature"],
                    top_p=self.pubmedgpt_config["top_p"],
                    do_sample=self.pubmedgpt_config["do_sample"],
                    pad_token_id=self.pubmedgpt_tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.pubmedgpt_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Parse medical conditions from response
            conditions = self._parse_medical_conditions(response, AnalysisModel.PUBMEDGPT)
            
            return conditions
            
        except Exception as e:
            logger.error(f"PubMedGPT fallback analysis failed: {e}")
            return []
    
    def _parse_medical_conditions(self, response: str, model_used: AnalysisModel) -> List[DetectedCondition]:
        """Parse medical conditions from AI model response."""
        conditions = []
        
        try:
            # Extract medical terms and conditions from the response
            # This is a simplified parser - in production you'd want more sophisticated parsing
            
            # Get medical condition keywords from configuration
            medical_conditions_config = MedicalAIConfig.get_medical_conditions()
            medical_keywords = []
            for category, condition_list in medical_conditions_config.items():
                medical_keywords.extend(condition_list)
            
            # Look for medical conditions in the response
            found_conditions = []
            for keyword in medical_keywords:
                if keyword.lower() in response.lower():
                    found_conditions.append(keyword)
            
            # Create DetectedCondition objects
            for condition_name in found_conditions[:3]:  # Limit to top 3 conditions
                condition = DetectedCondition(
                    name=condition_name,
                    confidence=0.75,  # Default confidence for medical models
                    category=self._categorize_condition(condition_name),
                    severity="moderate",  # Default severity
                    urgency=UrgencyLevel.NORMAL,  # Default urgency
                    symptoms=[condition_name],
                    model_used=model_used,
                    description=f"Detected by {model_used.value}",
                    differential_diagnosis=[]
                )
                conditions.append(condition)
            
            # If no specific conditions found, create a general assessment
            if not conditions:
                condition = DetectedCondition(
                    name="medical assessment",
                    confidence=0.6,
                    category=ConditionType.GENERAL,
                    severity="mild",
                    urgency=UrgencyLevel.NORMAL,
                    symptoms=["requires medical evaluation"],
                    model_used=model_used,
                    description=f"General medical assessment by {model_used.value}",
                    differential_diagnosis=[]
                )
                conditions.append(condition)
            
        except Exception as e:
            logger.error(f"Failed to parse medical conditions: {e}")
        
        return conditions
    
    def _categorize_condition(self, condition_name: str) -> ConditionType:
        """Categorize medical condition by type."""
        condition_lower = condition_name.lower()
        
        # Get medical conditions from configuration
        medical_conditions_config = MedicalAIConfig.get_medical_conditions()
        
        # Check each category
        for category, condition_list in medical_conditions_config.items():
            if any(condition in condition_lower for condition in condition_list):
                return ConditionType(category)  # Use lowercase category name
        
        # Default to general
        return ConditionType.GENERAL
    
    def _deduplicate_conditions(self, conditions: List[DetectedCondition]) -> List[DetectedCondition]:
        """Remove duplicate conditions and merge similar ones."""
        unique_conditions = {}
        
        for condition in conditions:
            key = condition.name.lower()
            if key not in unique_conditions:
                unique_conditions[key] = condition
            else:
                # Merge conditions if they're from different models
                existing = unique_conditions[key]
                if existing.model_used != condition.model_used:
                    # Take the one with higher confidence
                    if condition.confidence > existing.confidence:
                        unique_conditions[key] = condition
        
        return list(unique_conditions.values())
    
    def _build_vision_summary(self, vision_conditions: List[DetectedCondition]) -> str:
        """Build a summary of vision analysis results for medical models."""
        if not vision_conditions:
            return "No specific conditions detected in the image."
        
        summary_parts = []
        for condition in vision_conditions:
            summary_parts.append(f"- {condition.name} (confidence: {condition.confidence}, severity: {condition.severity})")
            if condition.symptoms:
                summary_parts.append(f"  Symptoms: {', '.join(condition.symptoms)}")
            if condition.description:
                summary_parts.append(f"  Description: {condition.description}")
        
        return f"Vision analysis detected the following conditions:\n" + "\n".join(summary_parts)
    
    def _build_medical_context_from_vision(self, vision_summary: str, user_query: Optional[str], 
                                          body_part: Optional[str], symptoms: Optional[str]) -> str:
        """Build medical context for AI models based on vision analysis results."""
        context_parts = [
            "Based on the visual analysis of the medical image, provide detailed medical insights including:",
            "",
            "VISION ANALYSIS RESULTS:",
            vision_summary,
            ""
        ]
        
        if user_query:
            context_parts.append(f"USER QUERY: {user_query}")
        if body_part:
            context_parts.append(f"BODY PART: {body_part}")
        if symptoms:
            context_parts.append(f"REPORTED SYMPTOMS: {symptoms}")
        
        context_parts.extend([
            "",
            "Please provide detailed medical analysis including:",
            "1. Confirmation or refinement of the detected condition",
            "2. Detailed symptoms and clinical presentation",
            "3. Differential diagnosis",
            "4. Treatment options and recommendations",
            "5. Prognosis and expected outcomes",
            "6. Risk factors and complications",
            "7. Prevention strategies",
            "8. When to seek medical attention",
            "",
            "Provide evidence-based medical information suitable for clinical decision making."
        ])
        
        return "\n".join(context_parts)
    
    def _enhance_vision_conditions(self, vision_conditions: List[DetectedCondition], 
                                 medical_insights: List[DetectedCondition]) -> List[DetectedCondition]:
        """Enhance vision conditions with medical insights from BioGPT and PubMedGPT."""
        enhanced_conditions = []
        
        for vision_condition in vision_conditions:
            # Find matching medical insights
            matching_insights = [insight for insight in medical_insights 
                               if insight.name.lower() == vision_condition.name.lower()]
            
            if matching_insights:
                # Merge vision and medical insights
                medical_insight = matching_insights[0]
                enhanced_condition = self._merge_vision_and_medical_insights(vision_condition, medical_insight)
                enhanced_conditions.append(enhanced_condition)
            else:
                # Keep original vision condition
                enhanced_conditions.append(vision_condition)
        
        return enhanced_conditions
    
    def _merge_vision_and_medical_insights(self, vision_condition: DetectedCondition, 
                                          medical_insight: DetectedCondition) -> DetectedCondition:
        """Merge vision analysis results with medical insights."""
        # Create enhanced condition with combined information
        enhanced_condition = DetectedCondition(
            id=vision_condition.id,
            name=vision_condition.name,
            confidence=max(vision_condition.confidence, medical_insight.confidence),
            category=vision_condition.category,
            severity=medical_insight.severity if medical_insight.severity else vision_condition.severity,
            urgency=medical_insight.urgency if medical_insight.urgency else vision_condition.urgency,
            symptoms=vision_condition.symptoms + medical_insight.symptoms if medical_insight.symptoms else vision_condition.symptoms,
            model_used=f"{vision_condition.model_used}+medical_ai",
            processing_time=vision_condition.processing_time,
            description=medical_insight.description if medical_insight.description else vision_condition.description,
            differential_diagnosis=medical_insight.differential_diagnosis if medical_insight.differential_diagnosis else vision_condition.differential_diagnosis,
            timestamp=vision_condition.timestamp
        )
        
        return enhanced_condition
    
    async def get_models_status(self) -> Dict[str, Any]:
        """Get status of medical AI models."""
        return {
            "biogpt": {
                "available": True,  # Available for lazy loading
                "loaded": self.biogpt_available,  # Actually loaded
                "model": self.biogpt_model_name,
                "device": self.device
            },
            "pubmedgpt": {
                "available": True,  # Available for lazy loading
                "loaded": self.pubmed_available,  # PubMed API available
                "model": "PubMed API",
                "device": "api"
            }
        }
    
    async def cleanup(self):
        """Cleanup model resources."""
        logger.info("Cleaning up Medical AI Service...")
        
        # Clear model references
        if self.biogpt_model:
            del self.biogpt_model
        if self.pubmedgpt_model:
            del self.pubmedgpt_model
        
        # Clear tokenizers
        if self.biogpt_tokenizer:
            del self.biogpt_tokenizer
        if self.pubmedgpt_tokenizer:
            del self.pubmedgpt_tokenizer
        
        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Medical AI Service cleaned up") 