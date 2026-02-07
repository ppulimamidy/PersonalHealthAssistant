"""
Clinical NLP Agent
Agent for clinical text analysis using BioClinicalBERT and Med-PaLM models.
Implements placeholder models for entity extraction and summarization.
"""

import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .base_agent import BaseMedicalAgent, AgentResult
from ..models.documents import DocumentDB, DocumentType
from ..models.clinical_reports import ClinicalReportDB, ReportType
from ..utils.event_streaming import MedicalRecordsEventProducer


class EntityType(str, Enum):
    """Types of medical entities."""
    SYMPTOM = "symptom"
    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    LAB_TEST = "lab_test"
    VITAL_SIGN = "vital_sign"
    BODY_PART = "body_part"
    CONDITION = "condition"
    ALLERGY = "allergy"
    FAMILY_HISTORY = "family_history"
    SOCIAL_HISTORY = "social_history"


@dataclass
class MedicalEntity:
    """Medical entity extracted from text."""
    text: str
    entity_type: EntityType
    start_pos: int
    end_pos: int
    confidence: float
    normalized_value: Optional[str] = None
    snomed_code: Optional[str] = None
    loinc_code: Optional[str] = None


@dataclass
class ClinicalSummary:
    """Clinical summary generated from text."""
    summary: str
    key_findings: List[str]
    recommendations: List[str]
    risk_factors: List[str]
    follow_up_actions: List[str]
    confidence: float


class AdvancedBioClinicalBERT:
    """Advanced BioClinicalBERT implementation with real model integration."""
    
    def __init__(self):
        # Import the advanced AI models
        try:
            from .advanced_ai_models import ai_model_manager
            self.ai_model_manager = ai_model_manager
            self.use_advanced_models = True
        except ImportError:
            self.use_advanced_models = False
            # Fallback to enhanced patterns
            self.entity_patterns = {
                EntityType.SYMPTOM: [
                    r'\b(pain|ache|discomfort|nausea|vomiting|fever|chills|fatigue|weakness|dizziness)\b',
                    r'\b(shortness of breath|dyspnea|chest pain|headache|abdominal pain|cough)\b',
                    r'\b(swelling|edema|rash|itching|numbness|tingling|paralysis)\b',
                    r'\b(anxiety|depression|insomnia|irritability|mood changes)\b'
                ],
                EntityType.DIAGNOSIS: [
                    r'\b(diabetes|hypertension|asthma|copd|heart disease|stroke)\b',
                    r'\b(cancer|tumor|malignancy|infection|pneumonia|uti|sepsis)\b',
                    r'\b(depression|anxiety|bipolar|schizophrenia|ptsd)\b',
                    r'\b(arthritis|osteoporosis|fibromyalgia|lupus)\b'
                ],
                EntityType.MEDICATION: [
                    r'\b(aspirin|ibuprofen|acetaminophen|metformin|insulin|lisinopril)\b',
                    r'\b(atorvastatin|amlodipine|metoprolol|furosemide|warfarin)\b',
                    r'\b(omeprazole|pantoprazole|albuterol|fluticasone|prednisone)\b',
                    r'\b(amoxicillin|azithromycin|doxycycline|ciprofloxacin)\b'
                ],
                EntityType.PROCEDURE: [
                    r'\b(surgery|operation|biopsy|endoscopy|colonoscopy|catheterization)\b',
                    r'\b(angioplasty|stent|pacemaker|defibrillator|transplant)\b',
                    r'\b(chemotherapy|radiation|dialysis|ventilation|intubation)\b',
                    r'\b(appendectomy|cholecystectomy|hysterectomy|prostatectomy)\b'
                ],
                EntityType.LAB_TEST: [
                    r'\b(cbc|complete blood count|hemoglobin|hgb|white blood cell|wbc|platelet)\b',
                    r'\b(chemistry|cmp|bmp|glucose|creatinine|bun|sodium|potassium)\b',
                    r'\b(lipid|cholesterol|triglyceride|hdl|ldl|a1c|hba1c)\b',
                    r'\b(thyroid|tsh|t3|t4|free t4|thyroxine|psa|ca125)\b'
                ],
                EntityType.VITAL_SIGN: [
                    r'\b(blood pressure|bp|systolic|diastolic|heart rate|pulse)\b',
                    r'\b(temperature|temp|respiratory rate|oxygen saturation|spo2)\b',
                    r'\b(weight|height|bmi|body mass index|waist circumference)\b'
                ],
                EntityType.BODY_PART: [
                    r'\b(heart|lung|liver|kidney|brain|stomach|intestine|colon)\b',
                    r'\b(arm|leg|hand|foot|head|neck|chest|abdomen|back)\b',
                    r'\b(eye|ear|nose|throat|mouth|tongue|teeth|joint)\b'
                ]
            }
    
    def extract_entities(self, text: str) -> List[MedicalEntity]:
        """Extract medical entities from text using advanced models or patterns."""
        if self.use_advanced_models:
            try:
                # Use advanced AI models
                entities_data = self.ai_model_manager.get_model("bio_clinical_bert").extract_entities(text)
                return [self._dict_to_entity(entity_data) for entity_data in entities_data]
            except Exception as e:
                # Fallback to pattern matching
                return self._extract_with_patterns(text)
        else:
            return self._extract_with_patterns(text)
    
    def _extract_with_patterns(self, text: str) -> List[MedicalEntity]:
        """Extract entities using enhanced pattern matching."""
        entities = []
        text_lower = text.lower()
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    original_text = text[match.start():match.end()]
                    
                    # Calculate confidence based on pattern specificity
                    confidence = self._calculate_pattern_confidence(pattern, original_text)
                    
                    entity = MedicalEntity(
                        text=original_text,
                        entity_type=entity_type,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=confidence,
                        normalized_value=original_text.lower()
                    )
                    entities.append(entity)
        
        # Remove overlapping entities
        return self._remove_overlapping_entities(entities)
    
    def _calculate_pattern_confidence(self, pattern: str, text: str) -> float:
        """Calculate confidence score for pattern-based extraction."""
        # More specific patterns get higher confidence
        if len(pattern.split('|')) == 1:
            return 0.9  # Single specific term
        elif len(pattern.split('|')) <= 5:
            return 0.8  # Small group of terms
        else:
            return 0.7  # Large group of terms
    
    def _dict_to_entity(self, entity_data: Dict[str, Any]) -> MedicalEntity:
        """Convert dictionary to MedicalEntity."""
        return MedicalEntity(
            text=entity_data['text'],
            entity_type=EntityType(entity_data['entity_type']),
            start_pos=entity_data['start_pos'],
            end_pos=entity_data['end_pos'],
            confidence=entity_data['confidence'],
            normalized_value=entity_data['normalized_value']
        )
    
    def _remove_overlapping_entities(self, entities: List[MedicalEntity]) -> List[MedicalEntity]:
        """Remove overlapping entities, keeping the longer ones."""
        if not entities:
            return entities
        
        # Sort by length (longest first) and start position
        entities.sort(key=lambda x: (len(x.text), -x.start_pos), reverse=True)
        
        filtered_entities = []
        for entity in entities:
            # Check if this entity overlaps with any already accepted entity
            overlaps = False
            for accepted in filtered_entities:
                if (entity.start_pos < accepted.end_pos and 
                    entity.end_pos > accepted.start_pos):
                    overlaps = True
                    break
            
            if not overlaps:
                filtered_entities.append(entity)
        
        # Sort back by start position
        filtered_entities.sort(key=lambda x: x.start_pos)
        return filtered_entities


class AdvancedMedPaLM:
    """Advanced Med-PaLM implementation with real model integration."""
    
    def __init__(self):
        # Import the advanced AI models
        try:
            from .advanced_ai_models import ai_model_manager
            self.ai_model_manager = ai_model_manager
            self.use_advanced_models = True
        except ImportError:
            self.use_advanced_models = False
            # Fallback to enhanced templates
            self.summary_templates = {
                "lab_report": {
                    "template": "Lab results show {key_findings}. {abnormal_values} {recommendations}",
                    "key_sections": ["results", "abnormal", "recommendations"]
                },
                "clinical_note": {
                    "template": "Patient presents with {symptoms}. Assessment: {diagnosis}. Plan: {treatment_plan}",
                    "key_sections": ["symptoms", "diagnosis", "treatment"]
                },
                "imaging_report": {
                    "template": "Imaging findings: {findings}. {abnormalities} {recommendations}",
                    "key_sections": ["findings", "abnormalities", "recommendations"]
                },
                "discharge_summary": {
                    "template": "Hospital course: {course}. Discharge diagnosis: {diagnosis}. Follow-up: {follow_up}",
                    "key_sections": ["course", "diagnosis", "follow_up"]
                }
            }
    
    def summarize_clinical_text(self, text: str, document_type: str = "clinical_note") -> ClinicalSummary:
        """Generate clinical summary from text using advanced models or templates."""
        if self.use_advanced_models:
            try:
                # Use advanced AI models
                summary_data = self.ai_model_manager.get_model("med_palm").summarize_clinical_text(text, document_type)
                return self._dict_to_summary(summary_data)
            except Exception as e:
                # Fallback to template-based summarization
                return self._summarize_with_templates(text, document_type)
        else:
            return self._summarize_with_templates(text, document_type)
    
    def _summarize_with_templates(self, text: str, document_type: str) -> ClinicalSummary:
        """Generate summary using enhanced templates."""
        # Extract key information using advanced patterns
        key_findings = self._extract_key_findings(text)
        recommendations = self._extract_recommendations(text)
        risk_factors = self._extract_risk_factors(text)
        follow_up_actions = self._extract_follow_up_actions(text)
        
        # Generate summary using template
        template = self.summary_templates.get(document_type, self.summary_templates["clinical_note"])
        
        summary_parts = {
            "key_findings": ", ".join(key_findings[:3]) if key_findings else "no significant findings",
            "abnormal_values": self._extract_abnormal_values(text),
            "recommendations": ", ".join(recommendations[:2]) if recommendations else "continue monitoring",
            "symptoms": ", ".join(self._extract_symptoms(text)[:3]) if self._extract_symptoms(text) else "no symptoms reported",
            "diagnosis": ", ".join(self._extract_diagnoses(text)[:2]) if self._extract_diagnoses(text) else "under evaluation",
            "treatment_plan": ", ".join(recommendations[:3]) if recommendations else "continue current treatment",
            "findings": ", ".join(key_findings[:3]) if key_findings else "normal findings",
            "abnormalities": self._extract_abnormalities(text),
            "course": self._extract_hospital_course(text),
            "follow_up": ", ".join(follow_up_actions[:3]) if follow_up_actions else "routine follow-up"
        }
        
        summary = template["template"].format(**summary_parts)
        
        return ClinicalSummary(
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            risk_factors=risk_factors,
            follow_up_actions=follow_up_actions,
            confidence=0.75
        )
    
    def _dict_to_summary(self, summary_data: Dict[str, Any]) -> ClinicalSummary:
        """Convert dictionary to ClinicalSummary."""
        return ClinicalSummary(
            summary=summary_data['summary'],
            key_findings=summary_data['key_findings'],
            recommendations=summary_data['recommendations'],
            risk_factors=summary_data['risk_factors'],
            follow_up_actions=summary_data['follow_up_actions'],
            confidence=summary_data['confidence']
        )
    
    def _extract_key_findings(self, text: str) -> List[str]:
        """Extract key findings from text."""
        findings = []
        
        # Look for patterns indicating findings
        patterns = [
            r'\b(finding|result|shows|reveals|demonstrates|indicates)\b[^.]*\.',
            r'\b(normal|abnormal|elevated|decreased|positive|negative)\b[^.]*\.',
            r'\b(consistent with|suggestive of|indicative of)\b[^.]*\.'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            findings.extend(matches)
        
        return findings[:5]  # Limit to top 5 findings
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from text."""
        recommendations = []
        
        patterns = [
            r'\b(recommend|suggest|advise|consider|follow up|monitor)\b[^.]*\.',
            r'\b(continue|discontinue|start|stop|increase|decrease)\b[^.]*\.',
            r'\b(repeat|recheck|retest|reevaluate)\b[^.]*\.'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            recommendations.extend(matches)
        
        return recommendations[:5]
    
    def _extract_risk_factors(self, text: str) -> List[str]:
        """Extract risk factors from text."""
        risk_factors = []
        
        patterns = [
            r'\b(risk factor|high risk|increased risk|family history)\b[^.]*\.',
            r'\b(smoking|obesity|diabetes|hypertension|high cholesterol)\b',
            r'\b(age|gender|ethnicity|lifestyle|occupation)\b[^.]*\.'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            risk_factors.extend(matches)
        
        return risk_factors[:5]
    
    def _extract_follow_up_actions(self, text: str) -> List[str]:
        """Extract follow-up actions from text."""
        actions = []
        
        patterns = [
            r'\b(follow up|follow-up|return|revisit|schedule|appointment)\b[^.]*\.',
            r'\b(repeat|recheck|monitor|observe|watch)\b[^.]*\.',
            r'\b(call|contact|notify|report back)\b[^.]*\.'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            actions.extend(matches)
        
        return actions[:5]
    
    def _extract_abnormal_values(self, text: str) -> str:
        """Extract abnormal values from text."""
        abnormal_patterns = [
            r'\b(abnormal|elevated|decreased|high|low|positive|negative)\b[^.]*\.'
        ]
        
        for pattern in abnormal_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return "no abnormal values detected"
    
    def _extract_symptoms(self, text: str) -> List[str]:
        """Extract symptoms from text."""
        symptoms = []
        
        symptom_patterns = [
            r'\b(pain|ache|discomfort|nausea|vomiting|fever|chills|fatigue)\b',
            r'\b(shortness of breath|dyspnea|chest pain|headache|abdominal pain)\b'
        ]
        
        for pattern in symptom_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            symptoms.extend(matches)
        
        return list(set(symptoms))
    
    def _extract_diagnoses(self, text: str) -> List[str]:
        """Extract diagnoses from text."""
        diagnoses = []
        
        diagnosis_patterns = [
            r'\b(diagnosis|diagnosed with|diagnostic impression)\b[^.]*\.',
            r'\b(diabetes|hypertension|asthma|copd|heart disease|stroke)\b',
            r'\b(cancer|tumor|infection|pneumonia|uti|sepsis)\b'
        ]
        
        for pattern in diagnosis_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            diagnoses.extend(matches)
        
        return list(set(diagnoses))
    
    def _extract_abnormalities(self, text: str) -> str:
        """Extract abnormalities from text."""
        abnormal_patterns = [
            r'\b(abnormal|lesion|mass|nodule|opacity|effusion|edema)\b[^.]*\.'
        ]
        
        for pattern in abnormal_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return f"Abnormalities detected: {matches[0]}"
        
        return "No significant abnormalities detected"


class ClinicalNLPAgent(BaseMedicalAgent):
    """Agent for clinical NLP using BioClinicalBERT and Med-PaLM."""
    
    def __init__(self):
        super().__init__("ClinicalNLPAgent")
        self.bioclinical_bert = AdvancedBioClinicalBERT()
        self.med_palm = AdvancedMedPaLM()
        self.event_producer = MedicalRecordsEventProducer()
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Process clinical text for entity extraction and summarization.
        
        Args:
            data: Dictionary containing text and document information
            db: Database session
            
        Returns:
            AgentResult: Processing result with entities and summary
        """
        document_id = data.get("document_id")
        text = data.get("text", "")
        document_type = data.get("document_type", "clinical_note")
        
        if not document_id or not text:
            return AgentResult(
                success=False,
                error="document_id and text are required"
            )
        
        try:
            # Try to get document from database
            document = await self._get_document(db, document_id)
            use_provided_content = False
            if not document:
                use_provided_content = True

            # Extract entities using BioClinicalBERT
            entities = self.bioclinical_bert.extract_entities(text)
            
            # Generate summary using Med-PaLM
            summary = self.med_palm.summarize_clinical_text(text, document_type)
            
            if document and not use_provided_content:
                # Update document with NLP results
                await self._update_document_nlp_results(db, document, entities, summary)
                # Publish NLP event to Kafka
                await self._publish_nlp_event(document, entities, summary)
            
            # Generate insights and recommendations
            insights = self._generate_insights(entities, summary)
            recommendations = self._generate_recommendations(entities, summary)
            
            return AgentResult(
                success=True,
                data={
                    "document_id": str(document_id),
                    "entities": [self._entity_to_dict(entity) for entity in entities],
                    "summary": self._summary_to_dict(summary),
                    "entity_count": len(entities),
                    "entity_types": list(set(entity.entity_type.value for entity in entities)),
                    "processing_status": "completed",
                    "content_provided": use_provided_content
                },
                insights=insights,
                recommendations=recommendations,
                confidence=0.80
            )
            
        except Exception as e:
            self.logger.error(f"Clinical NLP processing failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Clinical NLP processing failed: {str(e)}"
            )
    
    async def _get_document(self, db: AsyncSession, document_id: str) -> Optional[DocumentDB]:
        """Get document from database."""
        try:
            result = await db.execute(
                select(DocumentDB).where(DocumentDB.id == UUID(document_id))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Error fetching document: {e}")
            return None
    
    async def _update_document_nlp_results(self, db: AsyncSession, document: DocumentDB, entities: List[MedicalEntity], summary: ClinicalSummary):
        """Update document with NLP processing results."""
        try:
            # Update document metadata with NLP results
            if not document.document_document_metadata:
                document.document_document_metadata = {}
            
            document.document_document_metadata.update({
                "nlp_processed_by": self.agent_name,
                "nlp_processing_timestamp": datetime.utcnow().isoformat(),
                "entities": [self._entity_to_dict(entity) for entity in entities],
                "summary": self._summary_to_dict(summary),
                "entity_count": len(entities),
                "entity_types": list(set(entity.entity_type.value for entity in entities))
            })
            
            await db.commit()
            
        except Exception as e:
            self.logger.error(f"Error updating document NLP results: {e}")
            await db.rollback()
    
    async def _publish_nlp_event(self, document: DocumentDB, entities: List[MedicalEntity], summary: ClinicalSummary):
        """Publish NLP processing event to Kafka."""
        try:
            event = {
                "event_type": "clinical_nlp_completed",
                "timestamp": datetime.utcnow().isoformat(),
                "document_id": str(document.id),
                "patient_id": str(document.patient_id),
                "document_type": document.document_type.value,
                "entities": [self._entity_to_dict(entity) for entity in entities],
                "summary": self._summary_to_dict(summary),
                "entity_count": len(entities),
                "source": "ClinicalNLPAgent"
            }
            
            await self.event_producer.publish_nlp_event(event)
            self.logger.info(f"📤 Published NLP event for {document.id}")
            
        except Exception as e:
            self.logger.error(f"Error publishing NLP event: {e}")
    
    def _entity_to_dict(self, entity: MedicalEntity) -> Dict[str, Any]:
        """Convert MedicalEntity to dictionary."""
        return {
            "text": entity.text,
            "entity_type": entity.entity_type.value,
            "start_pos": entity.start_pos,
            "end_pos": entity.end_pos,
            "confidence": entity.confidence,
            "normalized_value": entity.normalized_value,
            "snomed_code": entity.snomed_code,
            "loinc_code": entity.loinc_code
        }
    
    def _summary_to_dict(self, summary: ClinicalSummary) -> Dict[str, Any]:
        """Convert ClinicalSummary to dictionary."""
        return {
            "summary": summary.summary,
            "key_findings": summary.key_findings,
            "recommendations": summary.recommendations,
            "risk_factors": summary.risk_factors,
            "follow_up_actions": summary.follow_up_actions,
            "confidence": summary.confidence
        }
    
    def _generate_insights(self, entities: List[MedicalEntity], summary: ClinicalSummary) -> List[str]:
        """Generate insights from NLP processing."""
        insights = []
        
        if entities:
            insights.append(f"Extracted {len(entities)} medical entities from text")
            
            # Count entities by type
            entity_counts = {}
            for entity in entities:
                entity_type = entity.entity_type.value
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            for entity_type, count in entity_counts.items():
                insights.append(f"Found {count} {entity_type} entities")
        
        if summary.key_findings:
            insights.append(f"Identified {len(summary.key_findings)} key clinical findings")
        
        if summary.risk_factors:
            insights.append(f"Detected {len(summary.risk_factors)} risk factors")
        
        if summary.recommendations:
            insights.append(f"Generated {len(summary.recommendations)} clinical recommendations")
        
        return insights
    
    def _generate_recommendations(self, entities: List[MedicalEntity], summary: ClinicalSummary) -> List[str]:
        """Generate recommendations based on NLP results."""
        recommendations = []
        
        # Check for critical entities
        critical_entities = [e for e in entities if e.entity_type in [EntityType.DIAGNOSIS, EntityType.SYMPTOM]]
        if len(critical_entities) > 5:
            recommendations.append("High entity density detected - consider detailed clinical review")
        
        # Check for missing entity types
        entity_types = set(e.entity_type for e in entities)
        if EntityType.MEDICATION not in entity_types:
            recommendations.append("No medications detected - verify medication documentation")
        
        if EntityType.LAB_TEST not in entity_types and EntityType.VITAL_SIGN not in entity_types:
            recommendations.append("Limited objective data - consider additional testing")
        
        # Add summary recommendations
        if summary.recommendations:
            recommendations.extend(summary.recommendations[:3])
        
        return recommendations 