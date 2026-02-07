"""
Base Agent Class for Device Data Agents
Provides common functionality for all autonomous device data agents.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from prometheus_client import Counter, Histogram, Gauge
from sqlalchemy.ext.asyncio import AsyncSession

from common.utils.logging import get_logger
from common.utils.resilience import with_resilience, CircuitBreaker
from common.models.base import BaseServiceException

logger = get_logger(__name__)

class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    DISABLED = "disabled"

@dataclass
class AgentResult:
    """Result from agent processing"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    insights: Optional[List[str]] = None
    alerts: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    confidence: float = 0.0
    processing_time: float = 0.0
    error: Optional[str] = None

class BaseDeviceAgent(ABC):
    """
    Base class for all device data agents.
    Provides common functionality for logging, metrics, and resilience.
    """
    
    def __init__(self, agent_name: str, circuit_breaker_config: Optional[Dict[str, Any]] = None):
        self.agent_name = agent_name
        self.status = AgentStatus.IDLE
        self.last_run = None
        self.run_count = 0
        self.error_count = 0
        
        # Circuit breaker for resilience
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_config.get("failure_threshold", 5),
            recovery_timeout=circuit_breaker_config.get("recovery_timeout", 60),
            expected_exception=BaseServiceException
        )
        
        # Prometheus metrics - disabled to avoid duplicate registration issues
        self.metrics = {
            "processing_time": None,
            "success_count": None,
            "error_count": None,
            "active_agents": None
        }
        
        # Initialize agent
        self._initialize()
    
    def _initialize(self):
        """Initialize the agent"""
        logger.info(f"Initializing {self.agent_name} agent")
        self.metrics["active_agents"].labels(agent_name=self.agent_name).inc()
    
    async def process(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Main processing method with resilience and metrics.
        
        Args:
            data: Input data for processing
            db: Database session
            
        Returns:
            AgentResult with processing results
        """
        start_time = time.time()
        self.status = AgentStatus.PROCESSING
        self.run_count += 1
        
        try:
            # Use circuit breaker for resilience
            result = await self.circuit_breaker.call(
                self._process_impl, data, db
            )
            
            # Record success metrics (if available)
            processing_time = time.time() - start_time
            if self.metrics["processing_time"]:
                self.metrics["processing_time"].labels(
                    agent_name=self.agent_name,
                    operation="process"
                ).observe(processing_time)
            
            if self.metrics["success_count"]:
                self.metrics["success_count"].labels(
                    agent_name=self.agent_name,
                    operation="process"
                ).inc()
            
            # Update result with timing
            result.processing_time = processing_time
            self.last_run = datetime.utcnow()
            self.status = AgentStatus.IDLE
            
            logger.info(f"{self.agent_name} processed successfully in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            # Record error metrics
            processing_time = time.time() - start_time
            self.error_count += 1
            self.status = AgentStatus.ERROR
            
            if self.metrics["error_count"]:
                self.metrics["error_count"].labels(
                    agent_name=self.agent_name,
                    operation="process",
                    error_type=type(e).__name__
                ).inc()
            
            logger.error(f"{self.agent_name} processing failed: {str(e)}")
            
            return AgentResult(
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    @abstractmethod
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Implementation of agent processing logic.
        Must be implemented by subclasses.
        
        Args:
            data: Input data for processing
            db: Database session
            
        Returns:
            AgentResult with processing results
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the agent"""
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "success_rate": (self.run_count - self.error_count) / max(self.run_count, 1),
            "circuit_breaker_state": self.circuit_breaker.state.value
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info(f"Cleaning up {self.agent_name} agent")
        if self.metrics["active_agents"]:
            self.metrics["active_agents"].labels(agent_name=self.agent_name).dec()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics for the agent"""
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "success_rate": (self.run_count - self.error_count) / max(self.run_count, 1),
            "last_run": self.last_run.isoformat() if self.last_run else None
        } 