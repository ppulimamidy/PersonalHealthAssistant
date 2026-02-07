"""
Medical Records Agent Orchestrator
Coordinates and manages the execution of medical records agents.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Type
from uuid import UUID
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from .base_agent import BaseMedicalAgent, AgentResult, AgentStatus, AgentPriority
from .document_reference_agent import DocumentReferenceAgent
from .clinical_nlp_agent import ClinicalNLPAgent
from common.utils.logging import get_logger


class OrchestrationStatus(str, Enum):
    """Orchestration execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentOrchestrator:
    """Orchestrates the execution of medical records agents."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.agents = {}
        self.status = OrchestrationStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.execution_results = {}
        
        # Initialize agents
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all available agents."""
        try:
            self.agents = {
                "document_reference": DocumentReferenceAgent(),
                "clinical_nlp": ClinicalNLPAgent()
            }
            
            # Add advanced analytics agents if available
            try:
                from .lab_result_analyzer_agent import LabResultAnalyzerAgent
                from .imaging_analyzer_agent import ImagingAnalyzerAgent
                from .critical_alert_agent import CriticalAlertAgent
                
                self.agents.update({
                    "lab_result_analyzer": LabResultAnalyzerAgent(),
                    "imaging_analyzer": ImagingAnalyzerAgent(),
                    "critical_alert": CriticalAlertAgent()
                })
            except ImportError:
                self.logger.warning("Advanced analytics agents not available")
            
            # Add health tracking agents if available
            try:
                from apps.health_tracking.agents.trend_analyzer import TrendAnalyzerAgent
                from apps.health_tracking.agents.anomaly_detector import AnomalyDetectorAgent
                from apps.health_tracking.agents.pattern_recognizer import PatternRecognizerAgent
                from apps.health_tracking.agents.risk_assessor import RiskAssessorAgent
                from apps.health_tracking.agents.predictive_models_agent import PredictiveModelsAgent
                from apps.health_tracking.agents.deep_learning_agent import DeepLearningAgent
                from apps.health_tracking.agents.realtime_analytics_agent import RealTimeAnalyticsAgent
                
                self.agents.update({
                    "trend_analyzer": TrendAnalyzerAgent(),
                    "anomaly_detector": AnomalyDetectorAgent(),
                    "pattern_recognizer": PatternRecognizerAgent(),
                    "risk_assessor": RiskAssessorAgent(),
                    "predictive_models": PredictiveModelsAgent(),
                    "deep_learning": DeepLearningAgent(),
                    "realtime_analytics": RealTimeAnalyticsAgent()
                })
            except ImportError:
                self.logger.warning("Health tracking agents not available")
            
            self.logger.info(f"✅ Initialized {len(self.agents)} agents (medical records + advanced analytics)")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize agents: {e}")
    
    async def process_document(self, document_id: str, db: AsyncSession, **kwargs) -> Dict[str, Any]:
        """
        Process a document through the agent pipeline.
        
        Args:
            document_id: ID of the document to process
            db: Database session
            **kwargs: Additional parameters
            
        Returns:
            Dict containing orchestration results
        """
        self.start_time = datetime.utcnow()
        self.status = OrchestrationStatus.RUNNING
        self.execution_results = {}
        
        try:
            self.logger.info(f"🚀 Starting document processing orchestration for document {document_id}")
            
            # Step 1: Document Reference Agent
            doc_ref_result = await self._execute_document_reference_agent(document_id, db, **kwargs)
            self.execution_results["document_reference"] = doc_ref_result
            
            if not doc_ref_result.success:
                self.status = OrchestrationStatus.FAILED
                return self._create_orchestration_result()
            
            # Step 2: Clinical NLP Agent (if document contains text)
            if kwargs.get("text") or kwargs.get("content"):
                nlp_result = await self._execute_clinical_nlp_agent(document_id, db, **kwargs)
                self.execution_results["clinical_nlp"] = nlp_result
            else:
                self.logger.info("📝 No text content provided, skipping Clinical NLP Agent")
                self.execution_results["clinical_nlp"] = AgentResult(
                    success=True,
                    data={"skipped": True, "reason": "No text content provided"}
                )
            
            # Step 3: Route to additional agents based on document reference results
            if doc_ref_result.success and doc_ref_result.data:
                routing_info = doc_ref_result.data.get("routing_info", {})
                next_agents = routing_info.get("next_agents", [])
                
                for agent_name in next_agents:
                    await self._execute_routed_agent(agent_name, document_id, db, **kwargs)
            
            self.status = OrchestrationStatus.COMPLETED
            self.end_time = datetime.utcnow()
            
            self.logger.info(f"✅ Document processing orchestration completed for document {document_id}")
            return self._create_orchestration_result()
            
        except Exception as e:
            self.status = OrchestrationStatus.FAILED
            self.end_time = datetime.utcnow()
            
            self.logger.error(f"❌ Document processing orchestration failed: {str(e)}")
            return self._create_orchestration_result(error=str(e))
    
    async def _execute_document_reference_agent(self, document_id: str, db: AsyncSession, **kwargs) -> AgentResult:
        """Execute the Document Reference Agent."""
        try:
            agent = self.agents.get("document_reference")
            if not agent:
                return AgentResult(
                    success=False,
                    error="Document Reference Agent not available"
                )
            
            data = {
                "document_id": document_id,
                "document_type": kwargs.get("document_type"),
                "content": kwargs.get("content", ""),
                "title": kwargs.get("title", "")
            }
            
            self.logger.info(f"🔍 Executing Document Reference Agent for document {document_id}")
            result = await agent.execute(data, db)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Document Reference Agent execution failed: {e}")
            return AgentResult(
                success=False,
                error=f"Document Reference Agent execution failed: {str(e)}"
            )
    
    async def _execute_clinical_nlp_agent(self, document_id: str, db: AsyncSession, **kwargs) -> AgentResult:
        """Execute the Clinical NLP Agent."""
        try:
            agent = self.agents.get("clinical_nlp")
            if not agent:
                return AgentResult(
                    success=False,
                    error="Clinical NLP Agent not available"
                )
            
            data = {
                "document_id": document_id,
                "text": kwargs.get("text") or kwargs.get("content", ""),
                "document_type": kwargs.get("document_type", "clinical_note")
            }
            
            self.logger.info(f"🧠 Executing Clinical NLP Agent for document {document_id}")
            result = await agent.execute(data, db)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Clinical NLP Agent execution failed: {e}")
            return AgentResult(
                success=False,
                error=f"Clinical NLP Agent execution failed: {str(e)}"
            )
    
    async def _execute_routed_agent(self, agent_name: str, document_id: str, db: AsyncSession, **kwargs) -> AgentResult:
        """Execute a routed agent based on document reference results."""
        try:
            # Map agent names to actual agent instances
            agent_mapping = {
                "LabResultAnalyzerAgent": "lab_result_analyzer",
                "ImagingAnalyzerAgent": "imaging_analyzer", 
                "CriticalAlertAgent": "critical_alert",
                "ClinicalNLPAgent": "clinical_nlp",
                "AIInsightAgent": "ai_insight"
            }
            
            mapped_name = agent_mapping.get(agent_name)
            if not mapped_name or mapped_name not in self.agents:
                self.logger.warning(f"Agent {agent_name} not available")
                return AgentResult(
                    success=False,
                    error=f"Agent {agent_name} not available"
                )
            
            # Execute the actual agent
            agent = self.agents[mapped_name]
            data = {"document_id": document_id, **kwargs}
            
            self.logger.info(f"🔄 Executing {agent_name} for document {document_id}")
            result = await agent.execute(data, db)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Routed agent execution failed: {e}")
            return AgentResult(
                success=False,
                error=f"Routed agent execution failed: {str(e)}"
            )
    
    async def execute_agent(self, agent_name: str, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Execute a specific agent.
        
        Args:
            agent_name: Name of the agent to execute
            data: Input data for the agent
            db: Database session
            
        Returns:
            AgentResult: Result of the agent execution
        """
        try:
            agent = self.agents.get(agent_name)
            if not agent:
                return AgentResult(
                    success=False,
                    error=f"Agent '{agent_name}' not found"
                )
            
            self.logger.info(f"🎯 Executing {agent_name} agent")
            result = await agent.execute(data, db)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Agent execution failed: {e}")
            return AgentResult(
                success=False,
                error=f"Agent execution failed: {str(e)}"
            )
    
    async def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get status of a specific agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent '{agent_name}' not found"}
        
        return agent.get_status()
    
    async def get_all_agent_statuses(self) -> Dict[str, Any]:
        """Get status of all agents."""
        statuses = {}
        for agent_name, agent in self.agents.items():
            statuses[agent_name] = agent.get_status()
        
        return statuses
    
    def _create_orchestration_result(self, error: Optional[str] = None) -> Dict[str, Any]:
        """Create orchestration result summary."""
        result = {
            "orchestration_id": str(UUID.uuid4()),
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_agents": len(self.agents),
            "executed_agents": len(self.execution_results),
            "agent_results": {}
        }
        
        # Add processing time
        if self.start_time and self.end_time:
            processing_time = int((self.end_time - self.start_time).total_seconds() * 1000)
            result["processing_time_ms"] = processing_time
        
        # Add error if present
        if error:
            result["error"] = error
        
        # Add individual agent results
        for agent_name, agent_result in self.execution_results.items():
            result["agent_results"][agent_name] = {
                "success": agent_result.success,
                "error": agent_result.error,
                "confidence": agent_result.confidence,
                "processing_time_ms": agent_result.processing_time_ms,
                "insights": agent_result.insights,
                "recommendations": agent_result.recommendations
            }
        
        return result
    
    async def cleanup(self):
        """Cleanup all agents."""
        try:
            self.logger.info("🧹 Cleaning up agent orchestrator")
            
            for agent_name, agent in self.agents.items():
                try:
                    await agent.cleanup()
                    self.logger.info(f"✅ Cleaned up {agent_name} agent")
                except Exception as e:
                    self.logger.error(f"❌ Failed to cleanup {agent_name} agent: {e}")
            
            self.logger.info("✅ Agent orchestrator cleanup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Agent orchestrator cleanup failed: {e}")
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            "orchestrator_status": self.status.value,
            "total_agents": len(self.agents),
            "available_agents": list(self.agents.keys()),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "last_execution_results": len(self.execution_results)
        }


# Global orchestrator instance
_orchestrator: Optional[AgentOrchestrator] = None


async def get_agent_orchestrator() -> AgentOrchestrator:
    """Get the global agent orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


async def cleanup_agent_orchestrator():
    """Cleanup the global agent orchestrator instance."""
    global _orchestrator
    if _orchestrator:
        await _orchestrator.cleanup()
        _orchestrator = None 