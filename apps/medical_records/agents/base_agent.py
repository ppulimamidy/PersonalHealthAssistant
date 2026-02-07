"""
Base Agent for Medical Records
Provides common functionality for all medical records agents.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from common.utils.logging import get_logger


class AgentStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentPriority(str, Enum):
    """Agent priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentResult:
    """Result from agent execution."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    insights: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    confidence: float = 0.0
    processing_time_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseMedicalAgent(ABC):
    """Base class for all medical records agents."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = get_logger(f"medical_records.agents.{agent_name}")
        self.status = AgentStatus.PENDING
        self.priority = AgentPriority.NORMAL
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
    async def execute(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Execute the agent with the given data.
        
        Args:
            data: Input data for the agent
            db: Database session
            
        Returns:
            AgentResult: Result of the agent execution
        """
        self.start_time = datetime.utcnow()
        self.status = AgentStatus.RUNNING
        
        try:
            self.logger.info(f"🚀 Starting {self.agent_name} execution")
            
            # Execute the agent-specific logic
            result = await self._process_impl(data, db)
            
            self.status = AgentStatus.COMPLETED
            self.end_time = datetime.utcnow()
            
            # Calculate processing time
            if self.start_time and self.end_time:
                processing_time = int((self.end_time - self.start_time).total_seconds() * 1000)
                if result.processing_time_ms is None:
                    result.processing_time_ms = processing_time
            
            self.logger.info(f"✅ {self.agent_name} completed successfully in {result.processing_time_ms}ms")
            return result
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.end_time = datetime.utcnow()
            
            self.logger.error(f"❌ {self.agent_name} failed: {str(e)}")
            
            return AgentResult(
                success=False,
                error=str(e),
                processing_time_ms=self._calculate_processing_time()
            )
    
    @abstractmethod
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Implement the agent-specific processing logic.
        
        Args:
            data: Input data for the agent
            db: Database session
            
        Returns:
            AgentResult: Result of the agent execution
        """
        pass
    
    def _calculate_processing_time(self) -> Optional[int]:
        """Calculate processing time in milliseconds."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "priority": self.priority.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "processing_time_ms": self._calculate_processing_time()
        }
    
    async def cleanup(self):
        """Cleanup agent resources."""
        self.logger.info(f"🧹 Cleaning up {self.agent_name}")
        # Override in subclasses if needed 