"""
Document Reference Agent
Intelligent agent for processing medical documents, extracting tags, scoring urgency,
and routing to appropriate downstream agents.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .base_agent import BaseMedicalAgent, AgentResult
from ..models.documents import DocumentDB, DocumentType, ProcessingStatus
from ..models.lab_results_db import LabResultDB
from ..models.clinical_reports import ClinicalReportDB, ReportType, ReportPriority
from ..utils.event_streaming import MedicalRecordsEventProducer


class DocumentCategory(str, Enum):
    """Document categories for classification."""
    LABORATORY = "laboratory"
    IMAGING = "imaging"
    CLINICAL_NOTE = "clinical_note"
    DISCHARGE = "discharge"
    PROCEDURE = "procedure"
    PATHOLOGY = "pathology"
    RADIOLOGY = "radiology"
    PRESCRIPTION = "prescription"
    REFERRAL = "referral"
    CONSENT = "consent"
    ADMINISTRATIVE = "administrative"
    OTHER = "other"


class UrgencyLevel(str, Enum):
    """Document urgency levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DocumentReferenceAgent(BaseMedicalAgent):
    """Agent for intelligent document processing and routing."""
    
    def __init__(self):
        super().__init__("DocumentReferenceAgent")
        self.event_producer = MedicalRecordsEventProducer()
        
        # Medical terminology patterns for classification
        self.lab_patterns = [
            r'\b(cbc|complete blood count|hemoglobin|hgb|white blood cell|wbc|platelet|pt|inr|aptt)\b',
            r'\b(chemistry|cmp|bmp|glucose|creatinine|bun|sodium|potassium|chloride|co2)\b',
            r'\b(lipid|cholesterol|triglyceride|hdl|ldl|a1c|hba1c|diabetes)\b',
            r'\b(thyroid|tsh|t3|t4|free t4|thyroxine)\b',
            r'\b(urinalysis|urine|protein|ketone|glucose|blood|leukocyte)\b'
        ]
        
        self.imaging_patterns = [
            r'\b(x-ray|xray|radiograph|chest x-ray|abdominal x-ray)\b',
            r'\b(ct scan|cat scan|computed tomography|cta|ctp)\b',
            r'\b(mri|magnetic resonance|mra|mrv)\b',
            r'\b(ultrasound|sonogram|echo|echocardiogram)\b',
            r'\b(pet scan|positron emission tomography|spect)\b',
            r'\b(mammogram|mammography|breast imaging)\b'
        ]
        
        self.critical_patterns = [
            r'\b(critical|urgent|emergency|stat|immediate)\b',
            r'\b(abnormal|elevated|decreased|high|low)\b',
            r'\b(cancer|malignant|tumor|metastasis)\b',
            r'\b(infection|sepsis|bacteremia|fungemia)\b',
            r'\b(bleeding|hemorrhage|anemia|thrombocytopenia)\b',
            r'\b(heart attack|myocardial infarction|chest pain)\b',
            r'\b(stroke|cva|tia|neurological deficit)\b'
        ]
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Process a document for intelligent classification and routing.
        
        Args:
            data: Dictionary containing document information
            db: Database session
            
        Returns:
            AgentResult: Processing result with tags, urgency, and routing information
        """
        document_id = data.get("document_id")
        document_type = data.get("document_type")
        content = data.get("content", "")
        title = data.get("title", "")
        
        if not document_id:
            return AgentResult(
                success=False,
                error="document_id is required"
            )
        
        try:
            # Check if we have content provided directly or need to fetch from database
            if content:
                # Use provided content directly
                document = None
                use_provided_content = True
            else:
                # Get document from database
                document = await self._get_document(db, document_id)
                if not document:
                    return AgentResult(
                        success=False,
                        error=f"Document {document_id} not found"
                    )
                use_provided_content = False
            
            # Extract tags and classify document
            tags = await self._extract_tags(document, content, title, use_provided_content, document_type)
            
            # Score urgency
            urgency_score = await self._score_urgency(document, content, title, use_provided_content, document_type)
            
            # Determine routing
            routing_info = await self._determine_routing(document, tags, urgency_score, use_provided_content, document_type)
            
            # Update document with tags and metadata (only if document exists in DB)
            if document and not use_provided_content:
                await self._update_document_metadata(db, document, tags, urgency_score, routing_info)
            
            # Publish event to Kafka (only if document exists in DB)
            if document and not use_provided_content:
                await self._publish_document_event(document, tags, urgency_score, routing_info)
            
            # Generate insights and recommendations
            insights = self._generate_insights(document, tags, urgency_score, use_provided_content, document_type)
            recommendations = self._generate_recommendations(document, tags, urgency_score, routing_info, use_provided_content, document_type)
            
            return AgentResult(
                success=True,
                data={
                    "document_id": str(document_id),
                    "tags": tags,
                    "urgency_score": urgency_score,
                    "routing_info": routing_info,
                    "category": self._determine_category(tags),
                    "processing_status": "completed",
                    "content_provided": use_provided_content
                },
                insights=insights,
                recommendations=recommendations,
                confidence=0.85
            )
            
        except Exception as e:
            self.logger.error(f"Document processing failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Document processing failed: {str(e)}"
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
    
    async def _extract_tags(self, document: DocumentDB, content: str, title: str, use_provided_content: bool, document_type: str = None) -> List[str]:
        """Extract tags from document content and title."""
        tags = []
        full_text = f"{title} {content}".lower()
        
        # Extract document type tags
        if document and document.document_type:
            tags.append(document.document_type.value)
        elif use_provided_content and document_type:
            tags.append(document_type)
        
        # Extract medical terminology tags
        for pattern in self.lab_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                tags.extend(["laboratory", "lab_result"])
                break
        
        for pattern in self.imaging_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                tags.extend(["imaging", "radiology"])
                break
        
        # Extract critical indicators
        for pattern in self.critical_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                tags.append("critical")
                break
        
        # Extract specific medical terms
        medical_terms = [
            "diabetes", "hypertension", "cardiology", "oncology", "neurology",
            "orthopedics", "pediatrics", "geriatrics", "emergency", "icu"
        ]
        
        for term in medical_terms:
            if term in full_text:
                tags.append(term)
        
        # Remove duplicates and return
        return list(set(tags))
    
    async def _score_urgency(self, document: 'DocumentDB', content: str, title: str, use_provided_content: bool, document_type: str = None) -> dict:
        urgency_score = 0.0
        urgency_factors = []
        full_text = f"{title} {content}".lower()
        critical_count = 0
        for pattern in self.critical_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                critical_count += 1
                urgency_factors.append(f"Critical term: {pattern}")
        if critical_count > 0:
            urgency_score += min(critical_count * 0.3, 1.0)
        type_priority = {
            "lab_report": 0.4,
            "imaging_report": 0.5,
            "clinical_note": 0.3,
            "discharge_summary": 0.6,
            "operative_report": 0.7,
            "pathology_report": 0.8,
            "radiology_report": 0.5,
            "ekg_report": 0.6
        }
        doc_type_val = None
        if document and hasattr(document, 'document_type') and document.document_type:
            doc_type_val = document.document_type.value if hasattr(document.document_type, 'value') else str(document.document_type)
        elif use_provided_content and document_type:
            doc_type_val = document_type
        if doc_type_val in type_priority:
            urgency_score += type_priority[doc_type_val]
            urgency_factors.append(f"Document type: {doc_type_val}")
        abnormal_indicators = [
            r'\b(abnormal|elevated|decreased|high|low|positive|negative)\b',
            r'\b(out of range|outside normal|reference range)\b',
            r'\b(follow up|follow-up|recheck|repeat)\b'
        ]
        for pattern in abnormal_indicators:
            if re.search(pattern, full_text, re.IGNORECASE):
                urgency_score += 0.2
                urgency_factors.append("Abnormal indicators detected")
                break
        urgency_score = min(urgency_score, 1.0)
        if urgency_score >= 0.8:
            urgency_level = UrgencyLevel.CRITICAL
        elif urgency_score >= 0.6:
            urgency_level = UrgencyLevel.HIGH
        elif urgency_score >= 0.4:
            urgency_level = UrgencyLevel.MEDIUM
        else:
            urgency_level = UrgencyLevel.LOW
        return {
            "score": round(urgency_score, 2),
            "level": urgency_level.value,
            "factors": urgency_factors
        }
    
    async def _determine_routing(self, document: DocumentDB, tags: List[str], urgency_score: Dict[str, Any], use_provided_content: bool, document_type: str = None) -> Dict[str, Any]:
        """Determine routing for the document."""
        routing = {
            "next_agents": [],
            "priority": "normal",
            "requires_immediate_attention": False,
            "ai_insight_service": True,
            "explainability_service": False,
            "knowledge_graph": False
        }
        
        # Determine next agents based on tags
        if "laboratory" in tags or "lab_result" in tags:
            routing["next_agents"].append("LabResultAnalyzerAgent")
        
        if "imaging" in tags or "radiology" in tags:
            routing["next_agents"].append("ImagingAnalyzerAgent")
        
        if "critical" in tags:
            routing["next_agents"].append("CriticalAlertAgent")
            routing["requires_immediate_attention"] = True
            routing["priority"] = "high"
        
        if "clinical_note" in tags:
            routing["next_agents"].append("ClinicalNLPAgent")
            routing["explainability_service"] = True
        
        # Always route to AI Insight Service for analysis
        routing["next_agents"].append("AIInsightAgent")
        
        # Route to Knowledge Graph for complex documents
        if len(tags) > 3 or urgency_score["score"] > 0.6:
            routing["knowledge_graph"] = True
        
        return routing
    
    async def _update_document_metadata(self, db: AsyncSession, document: DocumentDB, tags: List[str], urgency_score: Dict[str, Any], routing_info: Dict[str, Any]):
        """Update document with processing metadata."""
        try:
            # Update document tags
            if not document.tags:
                document.tags = []
            document.tags.extend(tags)
            document.tags = list(set(document.tags))  # Remove duplicates
            
            # Update document metadata
            if not document.document_document_metadata:
                document.document_document_metadata = {}
            
            document.document_document_metadata.update({
                "processed_by_agent": self.agent_name,
                "processing_timestamp": datetime.utcnow().isoformat(),
                "urgency_score": urgency_score,
                "routing_info": routing_info,
                "category": self._determine_category(tags)
            })
            
            # Update processing status
            document.processing_status = ProcessingStatus.COMPLETED
            
            await db.commit()
            
        except Exception as e:
            self.logger.error(f"Error updating document metadata: {e}")
            await db.rollback()
    
    async def _publish_document_event(self, document: 'DocumentDB', tags: list, urgency_score: dict, routing_info: dict, use_provided_content: bool = False, document_type: str = None):
        try:
            event = {
                "event_type": "document_processed",
                "timestamp": datetime.utcnow().isoformat(),
                "document_id": str(document.id) if document else None,
                "patient_id": str(document.patient_id) if document else None,
                "document_type": document.document_type.value if document and hasattr(document.document_type, 'value') else (document_type if use_provided_content else None),
                "tags": tags,
                "urgency_score": urgency_score,
                "routing_info": routing_info,
                "source": "DocumentReferenceAgent"
            }
            await self.event_producer.publish_document_event(event)
            self.logger.info(f"\ud83d\udce4 Published document event for {event['document_id']}")
        except Exception as e:
            self.logger.error(f"Error publishing document event: {e}")
    
    def _determine_category(self, tags: List[str]) -> str:
        """Determine document category from tags."""
        if "laboratory" in tags or "lab_result" in tags:
            return DocumentCategory.LABORATORY.value
        elif "imaging" in tags or "radiology" in tags:
            return DocumentCategory.IMAGING.value
        elif "clinical_note" in tags:
            return DocumentCategory.CLINICAL_NOTE.value
        elif "discharge" in tags:
            return DocumentCategory.DISCHARGE.value
        elif "procedure" in tags or "operative" in tags:
            return DocumentCategory.PROCEDURE.value
        elif "pathology" in tags:
            return DocumentCategory.PATHOLOGY.value
        else:
            return DocumentCategory.OTHER.value
    
    def _generate_insights(self, document: DocumentDB, tags: List[str], urgency_score: Dict[str, Any], use_provided_content: bool, document_type: str = None) -> List[str]:
        """Generate insights from document processing."""
        insights = []
        
        if tags:
            insights.append(f"Document classified with {len(tags)} tags: {', '.join(tags[:5])}")
        
        if urgency_score["score"] > 0.7:
            insights.append(f"High urgency document detected (score: {urgency_score['score']})")
        
        if "critical" in tags:
            insights.append("Critical medical content identified - immediate review recommended")
        
        if "laboratory" in tags or "imaging" in tags:
            insights.append("Diagnostic document detected - routing to specialized analysis")
        
        if "critical" in tags or urgency_score["score"] > 0.8:
            insights.append("This document may require urgent attention.")
        
        if "lab_result" in tags:
            insights.append("Lab results detected.")
        
        if "imaging" in tags:
            insights.append("Imaging report detected.")
        
        return insights
    
    def _generate_recommendations(self, document: DocumentDB, tags: List[str], urgency_score: Dict[str, Any], routing_info: Dict[str, Any], use_provided_content: bool, document_type: str = None) -> List[str]:
        """Generate recommendations based on document analysis."""
        recommendations = []
        
        if urgency_score["score"] > 0.8:
            recommendations.append("Immediate clinical review required")
        
        if "critical" in tags:
            recommendations.append("Consider urgent notification to care team")
        
        if routing_info["requires_immediate_attention"]:
            recommendations.append("Route to high-priority processing queue")
        
        if "laboratory" in tags:
            recommendations.append("Schedule lab result trend analysis")
        
        if "imaging" in tags:
            recommendations.append("Consider radiology AI analysis for findings")
        
        if "critical_alert_agent" in routing_info.get("next_agents", []):
            recommendations.append("Route to critical alert agent for immediate review.")
        
        return recommendations 