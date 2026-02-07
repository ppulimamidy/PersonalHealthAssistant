"""
Base AI Insight Agent
Base class for all AI insight agents with common functionality.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from common.utils.logging import get_logger


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentPriority(str, Enum):
    """Agent execution priority."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentResult:
    """Result of agent execution."""
    success: bool
    agent_name: str
    status: AgentStatus
    data: Optional[Dict[str, Any]] = None
    insights: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    scores: Optional[Dict[str, float]] = None
    patterns: Optional[List[Dict[str, Any]]] = None
    trends: Optional[List[Dict[str, Any]]] = None
    risks: Optional[List[Dict[str, Any]]] = None
    anomalies: Optional[List[Dict[str, Any]]] = None
    predictions: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    confidence_score: Optional[float] = None


class BaseInsightAgent(ABC):
    """Base class for all AI insight agents."""
    
    def __init__(self, agent_name: str, priority: AgentPriority = AgentPriority.NORMAL):
        """
        Initialize the base insight agent.
        
        Args:
            agent_name: Name of the agent
            priority: Execution priority
        """
        self.agent_name = agent_name
        self.priority = priority
        self.status = AgentStatus.IDLE
        self.logger = get_logger(f"ai_insights.agents.{agent_name}")
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Agent capabilities
        self.capabilities = self._get_capabilities()
        self.data_requirements = self._get_data_requirements()
        self.output_schema = self._get_output_schema()
        
        self.logger.info(f"✅ Initialized {agent_name} agent with priority {priority}")
    
    @abstractmethod
    async def execute(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Execute the agent's main logic.
        
        Args:
            data: Input data for analysis
            db: Database session
            
        Returns:
            AgentResult: Result of agent execution
        """
        pass
    
    @abstractmethod
    def _get_capabilities(self) -> List[str]:
        """Get list of agent capabilities."""
        pass
    
    @abstractmethod
    def _get_data_requirements(self) -> List[str]:
        """Get list of required data sources."""
        pass
    
    @abstractmethod
    def _get_output_schema(self) -> Dict[str, Any]:
        """Get output schema for the agent."""
        pass
    
    async def preprocess_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess input data before analysis.
        
        Args:
            data: Raw input data
            
        Returns:
            Dict[str, Any]: Preprocessed data
        """
        try:
            self.logger.info(f"🔄 Preprocessing data for {self.agent_name}")
            
            # Validate data requirements
            missing_data = self._validate_data_requirements(data)
            if missing_data:
                raise ValueError(f"Missing required data: {missing_data}")
            
            # Clean and normalize data
            processed_data = self._clean_data(data)
            
            # Enrich data if needed
            enriched_data = await self._enrich_data(processed_data, data)
            
            self.logger.info(f"✅ Data preprocessing completed for {self.agent_name}")
            return enriched_data
            
        except Exception as e:
            self.logger.error(f"❌ Data preprocessing failed for {self.agent_name}: {e}")
            raise
    
    def _validate_data_requirements(self, data: Dict[str, Any]) -> List[str]:
        """Validate that all required data is present."""
        missing = []
        for requirement in self.data_requirements:
            if requirement not in data or data[requirement] is None:
                missing.append(requirement)
        return missing
    
    def _clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize data."""
        cleaned_data = {}
        
        for key, value in data.items():
            if value is not None:
                # Remove outliers, handle missing values, etc.
                cleaned_data[key] = self._clean_value(value)
        
        return cleaned_data
    
    def _clean_value(self, value: Any) -> Any:
        """Clean a single value."""
        if isinstance(value, (int, float)):
            # Handle numeric outliers
            return value
        elif isinstance(value, str):
            # Clean string data
            return value.strip()
        elif isinstance(value, list):
            # Clean list data
            return [self._clean_value(item) for item in value if item is not None]
        elif isinstance(value, dict):
            # Clean dictionary data
            return {k: self._clean_value(v) for k, v in value.items() if v is not None}
        else:
            return value
    
    async def _enrich_data(self, processed_data: Dict[str, Any], original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich data with additional context or derived features."""
        enriched_data = processed_data.copy()
        
        # Add timestamps if not present
        if 'timestamp' not in enriched_data:
            enriched_data['timestamp'] = datetime.utcnow().isoformat()
        
        # Add data source information
        if 'data_sources' not in enriched_data:
            enriched_data['data_sources'] = list(original_data.keys())
        
        return enriched_data
    
    async def postprocess_results(self, results: AgentResult) -> AgentResult:
        """
        Postprocess agent results.
        
        Args:
            results: Raw agent results
            
        Returns:
            AgentResult: Postprocessed results
        """
        try:
            self.logger.info(f"🔄 Postprocessing results for {self.agent_name}")
            
            # Calculate execution time
            if self.start_time and self.end_time:
                execution_time = int((self.end_time - self.start_time).total_seconds() * 1000)
                results.execution_time_ms = execution_time
            
            # Validate output schema
            self._validate_output_schema(results)
            
            # Add metadata
            results.metadata = self._generate_metadata(results)
            
            # Calculate confidence score if not present
            if results.confidence_score is None:
                results.confidence_score = self._calculate_confidence_score(results)
            
            self.logger.info(f"✅ Results postprocessing completed for {self.agent_name}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Results postprocessing failed for {self.agent_name}: {e}")
            results.error = str(e)
            results.success = False
            return results
    
    def _validate_output_schema(self, results: AgentResult):
        """Validate that results conform to output schema."""
        # Basic validation - can be extended based on specific agent requirements
        if not results.success and not results.error:
            raise ValueError("Failed results must include error message")
    
    def _generate_metadata(self, results: AgentResult) -> Dict[str, Any]:
        """Generate metadata for the results."""
        return {
            'agent_name': self.agent_name,
            'agent_priority': self.priority,
            'execution_timestamp': datetime.utcnow().isoformat(),
            'execution_time_ms': results.execution_time_ms,
            'data_sources_used': self.data_requirements,
            'capabilities_used': self.capabilities,
            'output_schema_version': '1.0'
        }
    
    def _calculate_confidence_score(self, results: AgentResult) -> float:
        """Calculate confidence score for the results."""
        # Default confidence calculation - can be overridden by specific agents
        if not results.success:
            return 0.0
        
        # Base confidence on data quality and result consistency
        confidence = 0.7  # Base confidence
        
        # Adjust based on execution time (faster is better, up to a point)
        if results.execution_time_ms:
            if results.execution_time_ms < 1000:
                confidence += 0.1
            elif results.execution_time_ms > 10000:
                confidence -= 0.1
        
        # Adjust based on data availability
        if results.data and len(results.data) > 0:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            'agent_name': self.agent_name,
            'status': self.status,
            'priority': self.priority,
            'capabilities': self.capabilities,
            'data_requirements': self.data_requirements,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'execution_time_ms': self._get_execution_time() if self.start_time else None
        }
    
    def _get_execution_time(self) -> Optional[int]:
        """Get current execution time in milliseconds."""
        if self.start_time:
            end_time = self.end_time or datetime.utcnow()
            return int((end_time - self.start_time).total_seconds() * 1000)
        return None
    
    async def cancel(self):
        """Cancel agent execution."""
        if self.status == AgentStatus.RUNNING:
            self.status = AgentStatus.CANCELLED
            self.end_time = datetime.utcnow()
            self.logger.info(f"🛑 Cancelled {self.agent_name} agent execution")
    
    def __str__(self) -> str:
        return f"{self.agent_name} (Priority: {self.priority}, Status: {self.status})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.agent_name}', priority='{self.priority}')>" 