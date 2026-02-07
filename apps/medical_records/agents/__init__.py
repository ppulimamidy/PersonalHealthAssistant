"""
Medical Records Agents Module
Contains specialized AI agents for medical records processing and analysis.
"""

from .base_agent import BaseMedicalAgent, AgentResult
from .document_reference_agent import DocumentReferenceAgent
from .clinical_nlp_agent import ClinicalNLPAgent
from .lab_result_analyzer_agent import LabResultAnalyzerAgent
from .imaging_analyzer_agent import ImagingAnalyzerAgent
from .critical_alert_agent import CriticalAlertAgent
from .agent_orchestrator import AgentOrchestrator

__all__ = [
    "BaseMedicalAgent",
    "AgentResult", 
    "DocumentReferenceAgent",
    "ClinicalNLPAgent",
    "LabResultAnalyzerAgent",
    "ImagingAnalyzerAgent",
    "CriticalAlertAgent",
    "AgentOrchestrator"
] 