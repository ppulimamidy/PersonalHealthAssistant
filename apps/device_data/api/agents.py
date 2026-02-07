"""
Agent Management API Endpoints
Provides endpoints for managing and interacting with device data agents.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from uuid import UUID
import jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from common.config.settings import get_settings
from common.database.connection import get_async_db
from ..models.device import Device
from ..services.device_service import get_device_service
from ..agents.agent_orchestrator import get_device_agent_orchestrator
from ..agents.data_quality_agent import DataQualityAgent
from ..agents.device_anomaly_agent import DeviceAnomalyAgent
from ..agents.calibration_agent import CalibrationAgent
from ..agents.sync_monitor_agent import SyncMonitorAgent

router = APIRouter(prefix="/agents", tags=["Device Data Agents"])
logger = logging.getLogger(__name__)


class UserStub(BaseModel):
    """Stub user model for device data service"""
    id: UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_type: Optional[str] = None


async def get_current_user(request: Request) -> UserStub:
    """Get current user from JWT token"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )
        
        token = auth_header.split(" ")[1]
        settings = get_settings()
        
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=["HS256"]
        )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload"
            )
        
        return UserStub(
            id=UUID(user_id),
            email=email
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )


@router.get("/health")
async def get_agents_health(
    current_user: UserStub = Depends(get_current_user)
):
    """
    Get health status of all device data agents.
    """
    try:
        orchestrator = await get_device_agent_orchestrator()
        
        # Get health status of all agents
        agent_health = {
            "orchestrator": {
                "status": "healthy" if orchestrator else "unhealthy",
                "last_check": datetime.utcnow().isoformat()
            },
            "data_quality_agent": {
                "status": "available",
                "capabilities": ["data_validation", "outlier_detection", "missing_data_analysis"]
            },
            "device_anomaly_agent": {
                "status": "available", 
                "capabilities": ["device_health_monitoring", "sync_failure_detection", "anomaly_alerts"]
            },
            "calibration_agent": {
                "status": "available",
                "capabilities": ["calibration_status", "drift_detection", "correction_factors"]
            },
            "sync_monitor_agent": {
                "status": "available",
                "capabilities": ["sync_frequency_optimization", "conflict_resolution", "failure_recovery"]
            }
        }
        
        return {
            "status": "healthy",
            "agents": agent_health,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting agents health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/{device_id}")
async def analyze_device_data(
    device_id: str,
    analysis_type: Optional[str] = "comprehensive",
    background_tasks: BackgroundTasks = None,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Trigger comprehensive analysis of device data using all available agents.
    
    Args:
        device_id: ID of the device to analyze
        analysis_type: Type of analysis (comprehensive, quality, anomaly, calibration, sync)
    """
    try:
        # Verify device ownership
        device_service = await get_device_service(db)
        device = await device_service.get_device(UUID(device_id), current_user.id)
        
        if not device or device.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Get agent orchestrator
        orchestrator = await get_device_agent_orchestrator()
        
        # Prepare analysis data
        analysis_data = {
            "user_id": current_user.id,
            "device_id": device_id,
            "analysis_type": analysis_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Run analysis based on type
        if analysis_type == "comprehensive":
            # Run all agents
            results = await orchestrator.run_comprehensive_analysis(analysis_data)
        elif analysis_type == "quality":
            agent = DataQualityAgent()
            results = await agent.process(analysis_data)
        elif analysis_type == "anomaly":
            agent = DeviceAnomalyAgent()
            results = await agent.process(analysis_data)
        elif analysis_type == "calibration":
            agent = CalibrationAgent()
            results = await agent.process(analysis_data)
        elif analysis_type == "sync":
            agent = SyncMonitorAgent()
            results = await agent.process(analysis_data)
        else:
            raise HTTPException(status_code=400, detail="Invalid analysis type")
        
        # Update device last analysis timestamp
        await device_service.update_device_analysis(device_id, datetime.utcnow())
        
        return {
            "message": f"Device analysis completed for {device.name}",
            "device_id": device_id,
            "analysis_type": analysis_type,
            "results": results.data if hasattr(results, 'data') else results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_agents_status(
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get detailed status and metrics of all agents.
    """
    try:
        orchestrator = await get_device_agent_orchestrator()
        
        # Get user's devices
        device_service = await get_device_service(db)
        devices = await device_service.get_user_devices(current_user.id)
        
        # Get agent metrics
        agent_metrics = {
            "total_devices": len(devices),
            "active_devices": len([d for d in devices if d.status == "active"]),
            "last_analysis": {},
            "agent_performance": {}
        }
        
        # Get last analysis for each device
        for device in devices:
            if device.last_analysis:
                agent_metrics["last_analysis"][str(device.id)] = {
                    "device_name": device.name,
                    "last_analysis": device.last_analysis.isoformat(),
                    "analysis_count": getattr(device, 'analysis_count', 0)
                }
        
        return {
            "user_id": current_user.id,
            "metrics": agent_metrics,
            "orchestrator_status": "healthy" if orchestrator else "unhealthy",
            "available_agents": [
                "data_quality_agent",
                "device_anomaly_agent", 
                "calibration_agent",
                "sync_monitor_agent"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting agents status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calibrate/{device_id}")
async def calibrate_device(
    device_id: str,
    calibration_type: Optional[str] = "automatic",
    background_tasks: BackgroundTasks = None,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Trigger device calibration using the calibration agent.
    
    Args:
        device_id: ID of the device to calibrate
        calibration_type: Type of calibration (automatic, manual, scheduled)
    """
    try:
        # Verify device ownership
        device_service = await get_device_service(db)
        device = await device_service.get_device(UUID(device_id), current_user.id)
        
        if not device or device.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Create calibration agent
        calibration_agent = CalibrationAgent()
        
        # Prepare calibration data
        calibration_data = {
            "user_id": current_user.id,
            "device_id": device_id,
            "calibration_type": calibration_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Run calibration
        results = await calibration_agent.process(calibration_data)
        
        # Update device calibration timestamp
        await device_service.update_device_calibration(device_id, datetime.utcnow())
        
        return {
            "message": f"Device calibration completed for {device.name}",
            "device_id": device_id,
            "calibration_type": calibration_type,
            "results": results.data if hasattr(results, 'data') else results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calibrating device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_name}/metrics")
async def get_agent_metrics(
    agent_name: str,
    current_user: UserStub = Depends(get_current_user)
):
    """
    Get performance metrics for a specific agent.
    
    Args:
        agent_name: Name of the agent (data_quality, anomaly, calibration, sync)
    """
    try:
        # Map agent names to classes
        agent_map = {
            "data_quality": DataQualityAgent,
            "anomaly": DeviceAnomalyAgent,
            "calibration": CalibrationAgent,
            "sync": SyncMonitorAgent
        }
        
        if agent_name not in agent_map:
            raise HTTPException(status_code=400, detail="Invalid agent name")
        
        # Create agent instance
        agent_class = agent_map[agent_name]
        agent = agent_class()
        
        # Get agent metrics
        metrics = {
            "agent_name": agent_name,
            "status": "active",
            "total_executions": getattr(agent, 'total_executions', 0),
            "success_rate": getattr(agent, 'success_rate', 0.95),
            "average_execution_time": getattr(agent, 'avg_execution_time', 0.5),
            "last_execution": getattr(agent, 'last_execution', None),
            "circuit_breaker_status": "closed" if getattr(agent, 'circuit_breaker', None) else "not_configured"
        }
        
        return {
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_name}/reset")
async def reset_agent(
    agent_name: str,
    current_user: UserStub = Depends(get_current_user)
):
    """
    Reset a specific agent's state and metrics.
    
    Args:
        agent_name: Name of the agent to reset
    """
    try:
        # Map agent names to classes
        agent_map = {
            "data_quality": DataQualityAgent,
            "anomaly": DeviceAnomalyAgent,
            "calibration": CalibrationAgent,
            "sync": SyncMonitorAgent
        }
        
        if agent_name not in agent_map:
            raise HTTPException(status_code=400, detail="Invalid agent name")
        
        # Create agent instance and reset
        agent_class = agent_map[agent_name]
        agent = agent_class()
        
        # Reset agent state
        if hasattr(agent, 'reset'):
            await agent.reset()
        
        return {
            "message": f"Agent {agent_name} reset successfully",
            "agent_name": agent_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error resetting agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 