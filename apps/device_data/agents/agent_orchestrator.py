"""
Device Data Agent Orchestrator
Coordinates and manages all device data agents for autonomous operation.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from .base_agent import AgentResult
from .data_quality_agent import DataQualityAgent
from .device_anomaly_agent import DeviceAnomalyAgent
from .calibration_agent import CalibrationAgent
from .sync_monitor_agent import SyncMonitorAgent
from common.utils.logging import get_logger

logger = get_logger(__name__)

class DeviceDataAgentOrchestrator:
    """
    Orchestrates all device data agents for comprehensive device monitoring.
    Coordinates agent execution and consolidates results.
    """
    
    def __init__(self):
        self.agents = {
            "data_quality": DataQualityAgent(),
            "device_anomaly": DeviceAnomalyAgent(),
            "calibration": CalibrationAgent(),
            "sync_monitor": SyncMonitorAgent()
        }
        
        self.logger = get_logger(__name__)
        self.last_run = None
        self.is_running = False
    
    async def run_comprehensive_analysis(self, user_id: str, db: AsyncSession, 
                                       device_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run comprehensive device analysis using all agents.
        
        Args:
            user_id: User ID to analyze
            db: Database session
            device_id: Optional specific device ID
            
        Returns:
            Consolidated results from all agents
        """
        if self.is_running:
            return {"error": "Analysis already in progress"}
        
        self.is_running = True
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Starting comprehensive device analysis for user {user_id}")
            
            # Prepare data for agents
            agent_data = {
                "user_id": user_id,
                "device_id": device_id
            }
            
            # Run all agents concurrently
            tasks = []
            for agent_name, agent in self.agents.items():
                task = asyncio.create_task(
                    agent.process(agent_data, db),
                    name=f"{agent_name}_analysis"
                )
                tasks.append((agent_name, task))
            
            # Wait for all agents to complete
            results = {}
            for agent_name, task in tasks:
                try:
                    result = await task
                    results[agent_name] = result
                    self.logger.info(f"Agent {agent_name} completed successfully")
                except Exception as e:
                    self.logger.error(f"Agent {agent_name} failed: {str(e)}")
                    results[agent_name] = AgentResult(
                        success=False,
                        error=f"Agent {agent_name} failed: {str(e)}"
                    )
            
            # Consolidate results
            consolidated_results = self._consolidate_results(results)
            
            # Update last run time
            self.last_run = datetime.utcnow()
            
            processing_time = (self.last_run - start_time).total_seconds()
            self.logger.info(f"Comprehensive analysis completed in {processing_time:.2f}s")
            
            return consolidated_results
            
        except Exception as e:
            self.logger.error(f"Comprehensive analysis failed: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}
        
        finally:
            self.is_running = False
    
    async def run_specific_agent(self, agent_name: str, user_id: str, 
                               db: AsyncSession, device_id: Optional[str] = None) -> AgentResult:
        """
        Run a specific agent for targeted analysis.
        
        Args:
            agent_name: Name of the agent to run
            user_id: User ID to analyze
            db: Database session
            device_id: Optional specific device ID
            
        Returns:
            Agent result
        """
        if agent_name not in self.agents:
            return AgentResult(
                success=False,
                error=f"Unknown agent: {agent_name}"
            )
        
        try:
            self.logger.info(f"Running {agent_name} agent for user {user_id}")
            
            agent_data = {
                "user_id": user_id,
                "device_id": device_id
            }
            
            result = await self.agents[agent_name].process(agent_data, db)
            
            self.logger.info(f"Agent {agent_name} completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Agent {agent_name} failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Agent {agent_name} failed: {str(e)}"
            )
    
    def _consolidate_results(self, results: Dict[str, AgentResult]) -> Dict[str, Any]:
        """Consolidate results from all agents"""
        consolidated = {
            "timestamp": datetime.utcnow().isoformat(),
            "agents_run": len(results),
            "successful_agents": sum(1 for r in results.values() if r.success),
            "failed_agents": sum(1 for r in results.values() if not r.success),
            "overall_status": "success" if all(r.success for r in results.values()) else "partial_failure",
            "agent_results": {},
            "consolidated_insights": [],
            "consolidated_alerts": [],
            "consolidated_recommendations": [],
            "summary": {}
        }
        
        # Process each agent's results
        for agent_name, result in results.items():
            consolidated["agent_results"][agent_name] = {
                "success": result.success,
                "error": result.error,
                "confidence": result.confidence,
                "processing_time": result.processing_time
            }
            
            if result.success and result.data:
                # Add agent-specific data
                if "data" in result.data:
                    consolidated["agent_results"][agent_name]["data"] = result.data["data"]
                
                # Consolidate insights
                if result.insights:
                    consolidated["consolidated_insights"].extend(result.insights)
                
                # Consolidate alerts
                if result.alerts:
                    consolidated["consolidated_alerts"].extend(result.alerts)
                
                # Consolidate recommendations
                if result.recommendations:
                    consolidated["consolidated_recommendations"].extend(result.recommendations)
        
        # Generate summary
        consolidated["summary"] = self._generate_summary(consolidated)
        
        return consolidated
    
    def _generate_summary(self, consolidated: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of consolidated results"""
        summary = {
            "total_issues_found": 0,
            "critical_issues": 0,
            "high_priority_issues": 0,
            "medium_priority_issues": 0,
            "low_priority_issues": 0,
            "devices_analyzed": 0,
            "devices_needing_attention": 0
        }
        
        # Count issues from agent results
        for agent_name, agent_result in consolidated["agent_results"].items():
            if "data" in agent_result:
                data = agent_result["data"]
                
                # Count different types of issues
                if "quality_issues" in data:
                    summary["total_issues_found"] += len(data["quality_issues"])
                
                if "anomalies" in data:
                    summary["total_issues_found"] += len(data["anomalies"])
                
                if "calibration_issues" in data:
                    summary["total_issues_found"] += len(data["calibration_issues"])
                
                if "sync_issues" in data:
                    summary["total_issues_found"] += len(data["sync_issues"])
                
                # Count devices analyzed
                if "total_devices_analyzed" in data:
                    summary["devices_analyzed"] = max(
                        summary["devices_analyzed"], 
                        data["total_devices_analyzed"]
                    )
        
        # Count priority levels from alerts
        for alert in consolidated["consolidated_alerts"]:
            if "CRITICAL" in alert:
                summary["critical_issues"] += 1
            elif "HIGH" in alert:
                summary["high_priority_issues"] += 1
            elif "MEDIUM" in alert:
                summary["medium_priority_issues"] += 1
            else:
                summary["low_priority_issues"] += 1
        
        # Estimate devices needing attention
        if summary["total_issues_found"] > 0:
            summary["devices_needing_attention"] = min(
                summary["devices_analyzed"], 
                summary["total_issues_found"]
            )
        
        return summary
    
    async def get_agent_health(self) -> Dict[str, Any]:
        """Get health status of all agents"""
        health_status = {
            "orchestrator_status": "healthy" if not self.is_running else "busy",
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "agents": {}
        }
        
        for agent_name, agent in self.agents.items():
            try:
                agent_health = await agent.health_check()
                health_status["agents"][agent_name] = agent_health
            except Exception as e:
                health_status["agents"][agent_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_status
    
    async def cleanup(self):
        """Cleanup all agents"""
        self.logger.info("Cleaning up device data agent orchestrator")
        
        for agent_name, agent in self.agents.items():
            try:
                await agent.cleanup()
                self.logger.info(f"Cleaned up agent: {agent_name}")
            except Exception as e:
                self.logger.error(f"Failed to cleanup agent {agent_name}: {str(e)}")

# Global orchestrator instance
_device_agent_orchestrator = None

async def get_device_agent_orchestrator() -> DeviceDataAgentOrchestrator:
    """Get the global device agent orchestrator instance"""
    global _device_agent_orchestrator
    
    if _device_agent_orchestrator is None:
        _device_agent_orchestrator = DeviceDataAgentOrchestrator()
    
    return _device_agent_orchestrator 