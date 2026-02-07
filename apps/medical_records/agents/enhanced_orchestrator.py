"""
Enhanced Agent Orchestrator
Advanced orchestration with real agent routing and execution.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Type
from uuid import UUID
from enum import Enum
from dataclasses import dataclass
import json

from sqlalchemy.ext.asyncio import AsyncSession

from .base_agent import BaseMedicalAgent, AgentResult, AgentStatus, AgentPriority
from .document_reference_agent import DocumentReferenceAgent
from .clinical_nlp_agent import ClinicalNLPAgent
from .lab_result_analyzer_agent import LabResultAnalyzerAgent
from .imaging_analyzer_agent import ImagingAnalyzerAgent
from .critical_alert_agent import CriticalAlertAgent
from common.utils.logging import get_logger


class OrchestrationStatus(str, Enum):
    """Orchestration execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStrategy(str, Enum):
    """Agent execution strategies."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    PRIORITY_BASED = "priority_based"


@dataclass
class OrchestrationResult:
    """Result of orchestration execution."""
    success: bool
    status: OrchestrationStatus
    results: Dict[str, AgentResult]
    execution_time_ms: Optional[int] = None
    error: Optional[str] = None
    insights: List[str] = None
    recommendations: List[str] = None


class EnhancedAgentOrchestrator:
    """Enhanced orchestrator with real agent routing and execution."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.agents = {}
        self.status = OrchestrationStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.execution_results = {}
        self.execution_strategy = ExecutionStrategy.PRIORITY_BASED
        
        # Initialize agents
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all available agents."""
        try:
            # Core medical records agents
            self.agents = {
                "document_reference": DocumentReferenceAgent(),
                "clinical_nlp": ClinicalNLPAgent(),
                "lab_result_analyzer": LabResultAnalyzerAgent(),
                "imaging_analyzer": ImagingAnalyzerAgent(),
                "critical_alert": CriticalAlertAgent()
            }
            
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
            
            self.logger.info(f"✅ Initialized {len(self.agents)} agents")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize agents: {e}")
    
    async def orchestrate_execution(self, data: Dict[str, Any], db: AsyncSession) -> OrchestrationResult:
        """
        Orchestrate the execution of agents based on document analysis.
        
        Args:
            data: Input data for orchestration
            db: Database session
            
        Returns:
            OrchestrationResult: Result of orchestration
        """
        self.start_time = datetime.utcnow()
        self.status = OrchestrationStatus.RUNNING
        
        try:
            self.logger.info("🚀 Starting enhanced agent orchestration")
            
            # Step 1: Document Reference Analysis
            doc_ref_result = await self._execute_document_reference(data, db)
            if not doc_ref_result.success:
                return OrchestrationResult(
                    success=False,
                    status=OrchestrationStatus.FAILED,
                    results={"document_reference": doc_ref_result},
                    error=doc_ref_result.error
                )
            
            # Step 2: Determine routing based on document reference results
            routing_plan = self._create_routing_plan(doc_ref_result.data)
            
            # Step 3: Execute routed agents
            agent_results = await self._execute_routed_agents(routing_plan, data, db)
            
            # Step 4: Generate comprehensive insights
            insights = self._generate_comprehensive_insights(agent_results)
            recommendations = self._generate_comprehensive_recommendations(agent_results)
            
            # Step 5: Update status
            self.status = OrchestrationStatus.COMPLETED
            self.end_time = datetime.utcnow()
            
            execution_time = self._calculate_execution_time()
            
            self.logger.info(f"✅ Enhanced orchestration completed in {execution_time}ms")
            
            return OrchestrationResult(
                success=True,
                status=OrchestrationStatus.COMPLETED,
                results=agent_results,
                execution_time_ms=execution_time,
                insights=insights,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.status = OrchestrationStatus.FAILED
            self.end_time = datetime.utcnow()
            
            self.logger.error(f"❌ Enhanced orchestration failed: {str(e)}")
            
            return OrchestrationResult(
                success=False,
                status=OrchestrationStatus.FAILED,
                results=self.execution_results,
                execution_time_ms=self._calculate_execution_time(),
                error=str(e)
            )
    
    async def _execute_document_reference(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """Execute document reference agent."""
        agent = self.agents.get("document_reference")
        if not agent:
            return AgentResult(
                success=False,
                error="Document reference agent not available"
            )
        
        return await agent.execute(data, db)
    
    def _create_routing_plan(self, doc_ref_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create routing plan based on document reference results."""
        routing_plan = {
            "agents_to_execute": [],
            "execution_order": [],
            "priority_agents": [],
            "conditional_agents": [],
            "parallel_agents": []
        }
        
        # Get routing information from document reference
        routing_info = doc_ref_data.get("routing", {})
        next_agents = routing_info.get("next_agents", [])
        requires_immediate_attention = routing_info.get("requires_immediate_attention", False)
        
        # Determine execution strategy
        if requires_immediate_attention:
            routing_plan["execution_strategy"] = ExecutionStrategy.PRIORITY_BASED
        elif len(next_agents) > 3:
            routing_plan["execution_strategy"] = ExecutionStrategy.PARALLEL
        else:
            routing_plan["execution_strategy"] = ExecutionStrategy.SEQUENTIAL
        
        # Map agent names to actual agents
        agent_mapping = {
            "LabResultAnalyzerAgent": "lab_result_analyzer",
            "ImagingAnalyzerAgent": "imaging_analyzer",
            "CriticalAlertAgent": "critical_alert",
            "ClinicalNLPAgent": "clinical_nlp",
            "AIInsightAgent": "ai_insight"
        }
        
        # Add agents to execution plan
        for agent_name in next_agents:
            mapped_name = agent_mapping.get(agent_name)
            if mapped_name and mapped_name in self.agents:
                routing_plan["agents_to_execute"].append(mapped_name)
                
                # Categorize agents
                if agent_name == "CriticalAlertAgent":
                    routing_plan["priority_agents"].append(mapped_name)
                elif agent_name in ["LabResultAnalyzerAgent", "ImagingAnalyzerAgent"]:
                    routing_plan["parallel_agents"].append(mapped_name)
                else:
                    routing_plan["conditional_agents"].append(mapped_name)
        
        # Always add clinical NLP for text analysis
        if "clinical_nlp" in self.agents and "clinical_nlp" not in routing_plan["agents_to_execute"]:
            routing_plan["agents_to_execute"].append("clinical_nlp")
            routing_plan["conditional_agents"].append("clinical_nlp")
        
        # Determine execution order
        routing_plan["execution_order"] = (
            routing_plan["priority_agents"] +
            routing_plan["parallel_agents"] +
            routing_plan["conditional_agents"]
        )
        
        return routing_plan
    
    async def _execute_routed_agents(self, routing_plan: Dict[str, Any], data: Dict[str, Any], db: AsyncSession) -> Dict[str, AgentResult]:
        """Execute agents based on routing plan."""
        agent_results = {}
        execution_strategy = routing_plan.get("execution_strategy", ExecutionStrategy.SEQUENTIAL)
        
        if execution_strategy == ExecutionStrategy.PRIORITY_BASED:
            agent_results = await self._execute_priority_based(routing_plan, data, db)
        elif execution_strategy == ExecutionStrategy.PARALLEL:
            agent_results = await self._execute_parallel(routing_plan, data, db)
        else:
            agent_results = await self._execute_sequential(routing_plan, data, db)
        
        return agent_results
    
    async def _execute_priority_based(self, routing_plan: Dict[str, Any], data: Dict[str, Any], db: AsyncSession) -> Dict[str, AgentResult]:
        """Execute agents based on priority."""
        agent_results = {}
        
        # Execute priority agents first
        for agent_name in routing_plan["priority_agents"]:
            result = await self._execute_single_agent(agent_name, data, db)
            agent_results[agent_name] = result
            
            # If priority agent fails, consider stopping execution
            if not result.success:
                self.logger.warning(f"Priority agent {agent_name} failed: {result.error}")
        
        # Execute remaining agents
        remaining_agents = routing_plan["parallel_agents"] + routing_plan["conditional_agents"]
        if remaining_agents:
            parallel_results = await self._execute_parallel_agents(remaining_agents, data, db)
            agent_results.update(parallel_results)
        
        return agent_results
    
    async def _execute_parallel(self, routing_plan: Dict[str, Any], data: Dict[str, Any], db: AsyncSession) -> Dict[str, AgentResult]:
        """Execute agents in parallel."""
        agents_to_execute = routing_plan["agents_to_execute"]
        return await self._execute_parallel_agents(agents_to_execute, data, db)
    
    async def _execute_sequential(self, routing_plan: Dict[str, Any], data: Dict[str, Any], db: AsyncSession) -> Dict[str, AgentResult]:
        """Execute agents sequentially."""
        agent_results = {}
        
        for agent_name in routing_plan["execution_order"]:
            result = await self._execute_single_agent(agent_name, data, db)
            agent_results[agent_name] = result
            
            # Pass results to next agent if needed
            if result.success and result.data:
                data[f"{agent_name}_results"] = result.data
        
        return agent_results
    
    async def _execute_parallel_agents(self, agent_names: List[str], data: Dict[str, Any], db: AsyncSession) -> Dict[str, AgentResult]:
        """Execute multiple agents in parallel."""
        tasks = []
        for agent_name in agent_names:
            task = self._execute_single_agent(agent_name, data, db)
            tasks.append((agent_name, task))
        
        # Execute all tasks concurrently
        results = {}
        for agent_name, task in tasks:
            try:
                result = await task
                results[agent_name] = result
            except Exception as e:
                self.logger.error(f"Agent {agent_name} execution failed: {e}")
                results[agent_name] = AgentResult(
                    success=False,
                    error=str(e)
                )
        
        return results
    
    async def _execute_single_agent(self, agent_name: str, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """Execute a single agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            return AgentResult(
                success=False,
                error=f"Agent {agent_name} not available"
            )
        
        try:
            self.logger.info(f"🔄 Executing agent: {agent_name}")
            result = await agent.execute(data, db)
            self.logger.info(f"✅ Agent {agent_name} completed: {result.success}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Agent {agent_name} failed: {e}")
            return AgentResult(
                success=False,
                error=str(e)
            )
    
    def _generate_comprehensive_insights(self, agent_results: Dict[str, AgentResult]) -> List[str]:
        """Generate comprehensive insights from all agent results."""
        insights = []
        
        # Count successful agents
        successful_agents = [name for name, result in agent_results.items() if result.success]
        insights.append(f"Successfully executed {len(successful_agents)} out of {len(agent_results)} agents")
        
        # Document reference insights
        if "document_reference" in agent_results:
            doc_result = agent_results["document_reference"]
            if doc_result.success and doc_result.data:
                doc_data = doc_result.data
                insights.append(f"Document classified as: {doc_data.get('document_type', 'unknown')}")
                insights.append(f"Urgency score: {doc_data.get('urgency_score', {}).get('score', 0)}")
        
        # Clinical NLP insights
        if "clinical_nlp" in agent_results:
            nlp_result = agent_results["clinical_nlp"]
            if nlp_result.success and nlp_result.data:
                nlp_data = nlp_result.data
                insights.append(f"Extracted {nlp_data.get('entity_count', 0)} medical entities")
                insights.append(f"Entity types: {', '.join(nlp_data.get('entity_types', []))}")
        
        # Lab result insights
        if "lab_result_analyzer" in agent_results:
            lab_result = agent_results["lab_result_analyzer"]
            if lab_result.success and lab_result.data:
                lab_data = lab_result.data
                insights.append(f"Analyzed {lab_data.get('trend_count', 0)} lab trends")
                insights.append(f"Detected {lab_data.get('anomaly_count', 0)} anomalies")
        
        # Imaging insights
        if "imaging_analyzer" in agent_results:
            img_result = agent_results["imaging_analyzer"]
            if img_result.success and img_result.data:
                img_data = img_result.data
                insights.append(f"Imaging modality: {img_data.get('modality', 'unknown')}")
                insights.append(f"Found {img_data.get('finding_count', 0)} findings")
        
        # Critical alert insights
        if "critical_alert" in agent_results:
            alert_result = agent_results["critical_alert"]
            if alert_result.success and alert_result.data:
                alert_data = alert_result.data
                insights.append(f"Generated {alert_data.get('alert_count', 0)} critical alerts")
        
        return insights
    
    def _generate_comprehensive_recommendations(self, agent_results: Dict[str, AgentResult]) -> List[str]:
        """Generate comprehensive recommendations from all agent results."""
        recommendations = []
        
        # Collect recommendations from all agents
        for agent_name, result in agent_results.items():
            if result.success and result.recommendations:
                recommendations.extend(result.recommendations[:2])  # Top 2 from each agent
        
        # Add orchestration-level recommendations
        successful_count = len([r for r in agent_results.values() if r.success])
        total_count = len(agent_results)
        
        if successful_count < total_count:
            recommendations.append("Some agents failed - consider manual review")
        
        if successful_count == total_count:
            recommendations.append("All agents completed successfully - comprehensive analysis available")
        
        # Remove duplicates and limit
        unique_recommendations = list(set(recommendations))
        return unique_recommendations[:10]  # Top 10 recommendations
    
    def _calculate_execution_time(self) -> Optional[int]:
        """Calculate total execution time in milliseconds."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return None
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        status = {}
        for agent_name, agent in self.agents.items():
            status[agent_name] = {
                "status": agent.status.value,
                "priority": agent.priority.value,
                "available": True
            }
        return status
    
    async def execute_specific_agent(self, agent_name: str, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """Execute a specific agent by name."""
        agent = self.agents.get(agent_name)
        if not agent:
            return AgentResult(
                success=False,
                error=f"Agent {agent_name} not available"
            )
        
        return await agent.execute(data, db)


# Global enhanced orchestrator instance
enhanced_orchestrator = EnhancedAgentOrchestrator() 