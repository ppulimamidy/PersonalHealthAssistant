"""
Medical Records Agents API
API endpoints for agent orchestration and execution.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ..agents.agent_orchestrator import get_agent_orchestrator, AgentOrchestrator
from ..agents.enhanced_orchestrator import enhanced_orchestrator
from ..agents.machine_learning_pipeline import ml_pipeline
from ..agents.base_agent import AgentResult
from common.database.connection import get_async_session
from common.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/agents", tags=["Medical Records Agents"])


@router.post("/process-document/{document_id}")
async def process_document_with_agents(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Process a document through the agent pipeline.
    
    Args:
        document_id: ID of the document to process
        background_tasks: FastAPI background tasks
        db: Database session
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing orchestration results
    """
    try:
        logger.info(f"🎯 Processing document {document_id} with agents")
        
        # Get document from database to extract content
        # This is a simplified version - in practice you'd fetch the actual document
        document_data = {
            "document_id": document_id,
            "document_type": "clinical_note",  # Default type
            "content": "",  # Would be fetched from database
            "title": ""  # Would be fetched from database
        }
        
        # Process document through agent pipeline
        result = await orchestrator.process_document(document_id, db, **document_data)
        
        return {
            "success": True,
            "message": f"Document {document_id} processed successfully",
            "orchestration_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to process document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )


@router.post("/execute/{agent_name}")
async def execute_agent(
    agent_name: str,
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_session),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Execute a specific agent.
    
    Args:
        agent_name: Name of the agent to execute
        data: Input data for the agent
        db: Database session
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing agent execution results
    """
    try:
        logger.info(f"🎯 Executing agent {agent_name}")
        
        # Execute the agent
        result = await orchestrator.execute_agent(agent_name, data, db)
        
        return {
            "success": result.success,
            "agent_name": agent_name,
            "result": {
                "success": result.success,
                "error": result.error,
                "data": result.data,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "confidence": result.confidence,
                "processing_time_ms": result.processing_time_ms
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to execute agent {agent_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute agent: {str(e)}"
        )


@router.get("/status")
async def get_agents_status(
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Get status of all agents.
    
    Args:
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing status of all agents
    """
    try:
        logger.info("📊 Getting agents status")
        
        # Get orchestrator status
        orchestrator_status = orchestrator.get_orchestrator_status()
        
        # Get individual agent statuses
        agent_statuses = await orchestrator.get_all_agent_statuses()
        
        return {
            "success": True,
            "orchestrator": orchestrator_status,
            "agents": agent_statuses,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get agents status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agents status: {str(e)}"
        )


@router.get("/status/{agent_name}")
async def get_agent_status(
    agent_name: str,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Get status of a specific agent.
    
    Args:
        agent_name: Name of the agent
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing agent status
    """
    try:
        logger.info(f"📊 Getting status for agent {agent_name}")
        
        # Get agent status
        agent_status = await orchestrator.get_agent_status(agent_name)
        
        if "error" in agent_status:
            raise HTTPException(
                status_code=404,
                detail=agent_status["error"]
            )
        
        return {
            "success": True,
            "agent_name": agent_name,
            "status": agent_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get agent status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.post("/process-document-with-content")
async def process_document_with_content(
    document_id: str,
    content: str,
    document_type: str = "clinical_note",
    title: str = "",
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_async_session),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Process a document with provided content through the agent pipeline.
    
    Args:
        document_id: ID of the document to process
        content: Document content text
        document_type: Type of document
        title: Document title
        background_tasks: FastAPI background tasks
        db: Database session
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing orchestration results
    """
    try:
        logger.info(f"🎯 Processing document {document_id} with content through agents")
        
        # Process document through agent pipeline
        result = await orchestrator.process_document(
            document_id, 
            db, 
            content=content,
            text=content,  # For NLP agent
            document_type=document_type,
            title=title
        )
        
        return {
            "success": True,
            "message": f"Document {document_id} processed successfully with content",
            "orchestration_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to process document {document_id} with content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document with content: {str(e)}"
        )


@router.post("/document-reference-agent")
async def execute_document_reference_agent(
    document_id: str,
    content: str = "",
    title: str = "",
    document_type: str = "clinical_note",
    db: AsyncSession = Depends(get_async_session),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Execute the Document Reference Agent specifically.
    
    Args:
        document_id: ID of the document
        content: Document content
        title: Document title
        document_type: Type of document
        db: Database session
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing Document Reference Agent results
    """
    try:
        logger.info(f"🔍 Executing Document Reference Agent for document {document_id}")
        
        data = {
            "document_id": document_id,
            "content": content,
            "title": title,
            "document_type": document_type
        }
        
        result = await orchestrator.execute_agent("document_reference", data, db)
        
        return {
            "success": result.success,
            "agent_name": "document_reference",
            "result": {
                "success": result.success,
                "error": result.error,
                "data": result.data,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "confidence": result.confidence,
                "processing_time_ms": result.processing_time_ms
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to execute Document Reference Agent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute Document Reference Agent: {str(e)}"
        )


@router.post("/clinical-nlp-agent")
async def execute_clinical_nlp_agent(
    document_id: str,
    text: str,
    document_type: str = "clinical_note",
    db: AsyncSession = Depends(get_async_session),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Execute the Clinical NLP Agent specifically.
    
    Args:
        document_id: ID of the document
        text: Text content for NLP processing
        document_type: Type of document
        db: Database session
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing Clinical NLP Agent results
    """
    try:
        logger.info(f"🧠 Executing Clinical NLP Agent for document {document_id}")
        
        data = {
            "document_id": document_id,
            "text": text,
            "document_type": document_type
        }
        
        result = await orchestrator.execute_agent("clinical_nlp", data, db)
        
        return {
            "success": result.success,
            "agent_name": "clinical_nlp",
            "result": {
                "success": result.success,
                "error": result.error,
                "data": result.data,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "confidence": result.confidence,
                "processing_time_ms": result.processing_time_ms
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to execute Clinical NLP Agent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute Clinical NLP Agent: {str(e)}"
        )


@router.get("/health")
async def agents_health_check(
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Health check for agents.
    
    Args:
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing health status
    """
    try:
        # Get orchestrator status
        orchestrator_status = orchestrator.get_orchestrator_status()
        
        # Check if agents are available
        agent_statuses = await orchestrator.get_all_agent_statuses()
        available_agents = len(agent_statuses)
        
        # Determine overall health
        is_healthy = (
            orchestrator_status["orchestrator_status"] != "failed" and
            available_agents > 0
        )
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "orchestrator_status": orchestrator_status["orchestrator_status"],
            "available_agents": available_agents,
            "total_agents": orchestrator_status["total_agents"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Agents health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/lab-result-analyzer")
async def execute_lab_result_analyzer(
    patient_id: str,
    lab_result_id: Optional[str] = None,
    analysis_period_days: int = 90,
    db: AsyncSession = Depends(get_async_session),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Execute lab result analyzer agent.
    
    Args:
        patient_id: Patient ID for analysis
        lab_result_id: Specific lab result ID (optional)
        analysis_period_days: Number of days to analyze (default: 90)
        db: Database session
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing lab analysis results
    """
    try:
        logger.info(f"🔬 Executing lab result analyzer for patient {patient_id}")
        
        data = {
            "patient_id": patient_id,
            "lab_result_id": lab_result_id,
            "analysis_period_days": analysis_period_days
        }
        
        # Execute the lab result analyzer agent
        result = await orchestrator.execute_agent("LabResultAnalyzerAgent", data, db)
        
        return {
            "success": result.success,
            "agent_name": "LabResultAnalyzerAgent",
            "patient_id": patient_id,
            "result": {
                "success": result.success,
                "error": result.error,
                "data": result.data,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "confidence": result.confidence,
                "processing_time_ms": result.processing_time_ms
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to execute lab result analyzer: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute lab result analyzer: {str(e)}"
        )


@router.post("/imaging-analyzer")
async def execute_imaging_analyzer(
    patient_id: str,
    report_id: str,
    report_text: str,
    db: AsyncSession = Depends(get_async_session),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Execute imaging analyzer agent.
    
    Args:
        patient_id: Patient ID
        report_id: Imaging report ID
        report_text: Imaging report text content
        db: Database session
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing imaging analysis results
    """
    try:
        logger.info(f"🖼️ Executing imaging analyzer for patient {patient_id}, report {report_id}")
        
        data = {
            "patient_id": patient_id,
            "report_id": report_id,
            "report_text": report_text
        }
        
        # Execute the imaging analyzer agent
        result = await orchestrator.execute_agent("ImagingAnalyzerAgent", data, db)
        
        return {
            "success": result.success,
            "agent_name": "ImagingAnalyzerAgent",
            "patient_id": patient_id,
            "report_id": report_id,
            "result": {
                "success": result.success,
                "error": result.error,
                "data": result.data,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "confidence": result.confidence,
                "processing_time_ms": result.processing_time_ms
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to execute imaging analyzer: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute imaging analyzer: {str(e)}"
        )


@router.post("/critical-alert-agent")
async def execute_critical_alert_agent(
    patient_id: str,
    monitoring_period_hours: int = 24,
    include_historical: bool = True,
    db: AsyncSession = Depends(get_async_session),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Execute critical alert agent.
    
    Args:
        patient_id: Patient ID for monitoring
        monitoring_period_hours: Hours to monitor (default: 24)
        include_historical: Include historical data (default: True)
        db: Database session
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing critical alert results
    """
    try:
        logger.info(f"🚨 Executing critical alert agent for patient {patient_id}")
        
        data = {
            "patient_id": patient_id,
            "monitoring_period_hours": monitoring_period_hours,
            "include_historical": include_historical
        }
        
        # Execute the critical alert agent
        result = await orchestrator.execute_agent("CriticalAlertAgent", data, db)
        
        return {
            "success": result.success,
            "agent_name": "CriticalAlertAgent",
            "patient_id": patient_id,
            "result": {
                "success": result.success,
                "error": result.error,
                "data": result.data,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "confidence": result.confidence,
                "processing_time_ms": result.processing_time_ms
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to execute critical alert agent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute critical alert agent: {str(e)}"
        )


@router.post("/comprehensive-analysis")
async def execute_comprehensive_analysis(
    patient_id: str,
    analysis_period_days: int = 90,
    include_lab_analysis: bool = True,
    include_critical_alerts: bool = True,
    include_advanced_analytics: bool = True,
    db: AsyncSession = Depends(get_async_session),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Execute comprehensive analysis using multiple agents.
    
    Args:
        patient_id: Patient ID for comprehensive analysis
        analysis_period_days: Number of days to analyze (default: 90)
        include_lab_analysis: Include lab result analysis (default: True)
        include_critical_alerts: Include critical alert monitoring (default: True)
        db: Database session
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing comprehensive analysis results
    """
    try:
        logger.info(f"🔍 Executing comprehensive analysis for patient {patient_id}")
        
        results = {}
        
        # Execute lab result analyzer if requested
        if include_lab_analysis:
            lab_data = {
                "patient_id": patient_id,
                "analysis_period_days": analysis_period_days
            }
            lab_result = await orchestrator.execute_agent("LabResultAnalyzerAgent", lab_data, db)
            results["lab_analysis"] = {
                "success": lab_result.success,
                "data": lab_result.data,
                "insights": lab_result.insights,
                "recommendations": lab_result.recommendations
            }
        
        # Execute critical alert agent if requested
        if include_critical_alerts:
            alert_data = {
                "patient_id": patient_id,
                "monitoring_period_hours": analysis_period_days * 24,
                "include_historical": True
            }
            alert_result = await orchestrator.execute_agent("CriticalAlertAgent", alert_data, db)
            results["critical_alerts"] = {
                "success": alert_result.success,
                "data": alert_result.data,
                "insights": alert_result.insights,
                "recommendations": alert_result.recommendations
            }
        
        # Execute advanced analytics if requested
        if include_advanced_analytics:
            try:
                # Trend analysis
                trend_data = {
                    "user_id": patient_id,
                    "analysis_period_days": analysis_period_days
                }
                trend_result = await orchestrator.execute_agent("trend_analyzer", trend_data, db)
                results["trend_analysis"] = {
                    "success": trend_result.success,
                    "data": trend_result.data,
                    "insights": trend_result.insights,
                    "recommendations": trend_result.recommendations
                }
                
                # Anomaly detection
                anomaly_data = {
                    "user_id": patient_id,
                    "analysis_period_days": analysis_period_days
                }
                anomaly_result = await orchestrator.execute_agent("anomaly_detector", anomaly_data, db)
                results["anomaly_detection"] = {
                    "success": anomaly_result.success,
                    "data": anomaly_result.data,
                    "insights": anomaly_result.insights,
                    "recommendations": anomaly_result.recommendations
                }
                
                # Risk assessment
                risk_data = {
                    "user_id": patient_id,
                    "analysis_period_days": analysis_period_days
                }
                risk_result = await orchestrator.execute_agent("risk_assessor", risk_data, db)
                results["risk_assessment"] = {
                    "success": risk_result.success,
                    "data": risk_result.data,
                    "insights": risk_result.insights,
                    "recommendations": risk_result.recommendations
                }
                
                # Predictive modeling
                predictive_data = {
                    "user_id": patient_id,
                    "prediction_type": "disease_risk",
                    "time_horizon": 365
                }
                predictive_result = await orchestrator.execute_agent("predictive_models", predictive_data, db)
                results["predictive_models"] = {
                    "success": predictive_result.success,
                    "data": predictive_result.data,
                    "insights": predictive_result.insights,
                    "recommendations": predictive_result.recommendations
                }
                
            except Exception as e:
                logger.error(f"Advanced analytics failed: {e}")
                results["advanced_analytics"] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Note: Imaging analysis requires specific report data, so it's not included in comprehensive analysis
        # It should be called separately with specific imaging report data
        
        return {
            "success": True,
            "patient_id": patient_id,
            "analysis_period_days": analysis_period_days,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to execute comprehensive analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute comprehensive analysis: {str(e)}"
        )


@router.post("/advanced-analytics/predictive-models")
async def execute_predictive_models(
    user_id: str,
    prediction_type: str = "disease_risk",
    target_disease: Optional[str] = None,
    time_horizon: int = 365,
    db: AsyncSession = Depends(get_async_session),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Execute predictive models for health forecasting.
    
    Args:
        user_id: User ID for prediction
        prediction_type: Type of prediction (disease_risk, readmission_risk, etc.)
        target_disease: Specific disease to predict (optional)
        time_horizon: Prediction time horizon in days
        db: Database session
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing predictive model results
    """
    try:
        logger.info(f"🔮 Executing predictive models for user {user_id}")
        
        data = {
            "user_id": user_id,
            "prediction_type": prediction_type,
            "target_disease": target_disease,
            "time_horizon": time_horizon
        }
        
        result = await orchestrator.execute_agent("predictive_models", data, db)
        
        return {
            "success": result.success,
            "agent_name": "predictive_models",
            "user_id": user_id,
            "prediction_type": prediction_type,
            "result": {
                "success": result.success,
                "error": result.error,
                "data": result.data,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "confidence": result.confidence,
                "processing_time_ms": result.processing_time_ms
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to execute predictive models: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute predictive models: {str(e)}"
        )


@router.post("/advanced-analytics/deep-learning")
async def execute_deep_learning(
    user_id: str,
    model_type: str = "lstm",
    target_metric: Optional[str] = None,
    prediction_horizon: int = 30,
    db: AsyncSession = Depends(get_async_session),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Execute deep learning models for advanced analytics.
    
    Args:
        user_id: User ID for analysis
        model_type: Type of model (lstm, cnn, autoencoder, transformer)
        target_metric: Specific metric to analyze (optional)
        prediction_horizon: Prediction horizon in days
        db: Database session
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing deep learning results
    """
    try:
        logger.info(f"🧠 Executing deep learning models for user {user_id}")
        
        data = {
            "user_id": user_id,
            "model_type": model_type,
            "target_metric": target_metric,
            "prediction_horizon": prediction_horizon
        }
        
        result = await orchestrator.execute_agent("deep_learning", data, db)
        
        return {
            "success": result.success,
            "agent_name": "deep_learning",
            "user_id": user_id,
            "model_type": model_type,
            "result": {
                "success": result.success,
                "error": result.error,
                "data": result.data,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "confidence": result.confidence,
                "processing_time_ms": result.processing_time_ms
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to execute deep learning: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute deep learning: {str(e)}"
        )


@router.post("/advanced-analytics/realtime")
async def execute_realtime_analytics(
    user_id: str,
    analysis_window: int = 3600,
    include_correlations: bool = True,
    db: AsyncSession = Depends(get_async_session),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> Dict[str, Any]:
    """
    Execute real-time analytics for immediate insights.
    
    Args:
        user_id: User ID for real-time analysis
        analysis_window: Analysis window in seconds
        include_correlations: Include correlation analysis
        db: Database session
        orchestrator: Agent orchestrator
        
    Returns:
        Dict containing real-time analytics results
    """
    try:
        logger.info(f"⚡ Executing real-time analytics for user {user_id}")
        
        data = {
            "user_id": user_id,
            "analysis_window": analysis_window,
            "include_correlations": include_correlations
        }
        
        result = await orchestrator.execute_agent("realtime_analytics", data, db)
        
        return {
            "success": result.success,
            "agent_name": "realtime_analytics",
            "user_id": user_id,
            "result": {
                "success": result.success,
                "error": result.error,
                "data": result.data,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "confidence": result.confidence,
                "processing_time_ms": result.processing_time_ms
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to execute real-time analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute real-time analytics: {str(e)}"
        )


# Enhanced Orchestration Endpoints
@router.post("/enhanced-orchestration")
async def execute_enhanced_orchestration(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Execute enhanced agent orchestration with real routing and execution.
    
    Args:
        data: Input data for orchestration
        db: Database session
        
    Returns:
        Dict containing enhanced orchestration results
    """
    try:
        logger.info("🚀 Starting enhanced agent orchestration")
        
        # Execute enhanced orchestration
        result = await enhanced_orchestrator.orchestrate_execution(data, db)
        
        return {
            "success": result.success,
            "status": result.status.value,
            "results": {
                agent_name: {
                    "success": agent_result.success,
                    "error": agent_result.error,
                    "data": agent_result.data,
                    "insights": agent_result.insights,
                    "recommendations": agent_result.recommendations,
                    "confidence": agent_result.confidence,
                    "processing_time_ms": agent_result.processing_time_ms
                } for agent_name, agent_result in result.results.items()
            },
            "execution_time_ms": result.execution_time_ms,
            "insights": result.insights,
            "recommendations": result.recommendations,
            "error": result.error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Enhanced orchestration failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced orchestration failed: {str(e)}"
        )


@router.get("/enhanced-orchestration/status")
async def get_enhanced_orchestration_status() -> Dict[str, Any]:
    """
    Get status of enhanced orchestration.
    
    Returns:
        Dict containing enhanced orchestration status
    """
    try:
        logger.info("📊 Getting enhanced orchestration status")
        
        # Get agent statuses
        agent_statuses = await enhanced_orchestrator.get_agent_status()
        
        return {
            "success": True,
            "orchestrator_status": enhanced_orchestrator.status.value,
            "agents": agent_statuses,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get enhanced orchestration status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get enhanced orchestration status: {str(e)}"
        )


# Machine Learning Pipeline Endpoints
@router.post("/ml-pipeline/train")
async def train_ml_models(
    training_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Train machine learning models.
    
    Args:
        training_data: Training data for models
        
    Returns:
        Dict containing training results
    """
    try:
        logger.info("🚀 Starting ML model training")
        
        # Generate training data if not provided
        if not training_data:
            training_data = await ml_pipeline.generate_training_data()
        
        # Train models
        results = await ml_pipeline.train_models(training_data)
        
        return {
            "success": True,
            "training_status": ml_pipeline.training_status.value,
            "results": {
                model_name: {
                    "accuracy": metrics.accuracy,
                    "precision": metrics.precision,
                    "recall": metrics.recall,
                    "f1_score": metrics.f1_score,
                    "training_time_seconds": metrics.training_time_seconds,
                    "model_size_mb": metrics.model_size_mb,
                    "version": metrics.version,
                    "created_at": metrics.created_at.isoformat()
                } for model_name, metrics in results.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ ML model training failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ML model training failed: {str(e)}"
        )


@router.post("/ml-pipeline/predict/document-type")
async def predict_document_type(text: str) -> Dict[str, Any]:
    """
    Predict document type using trained model.
    
    Args:
        text: Text to classify
        
    Returns:
        Dict containing prediction results
    """
    try:
        logger.info("🔮 Predicting document type")
        
        # Predict document type
        prediction = await ml_pipeline.predict_document_type(text)
        
        return {
            "success": True,
            "prediction": prediction,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Document type prediction failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Document type prediction failed: {str(e)}"
        )


@router.post("/ml-pipeline/predict/urgency")
async def predict_urgency(text: str) -> Dict[str, Any]:
    """
    Predict urgency score using trained model.
    
    Args:
        text: Text to analyze for urgency
        
    Returns:
        Dict containing urgency prediction
    """
    try:
        logger.info("🔮 Predicting urgency score")
        
        # Predict urgency
        urgency_score = await ml_pipeline.predict_urgency(text)
        
        return {
            "success": True,
            "urgency_score": urgency_score,
            "urgency_level": "high" if urgency_score > 0.7 else "medium" if urgency_score > 0.4 else "low",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Urgency prediction failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Urgency prediction failed: {str(e)}"
        )


@router.get("/ml-pipeline/status")
async def get_ml_pipeline_status() -> Dict[str, Any]:
    """
    Get status of machine learning pipeline.
    
    Returns:
        Dict containing ML pipeline status
    """
    try:
        logger.info("📊 Getting ML pipeline status")
        
        # Get model statuses
        model_statuses = await ml_pipeline.get_model_status()
        
        return {
            "success": True,
            "training_status": ml_pipeline.training_status.value,
            "models": model_statuses,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get ML pipeline status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ML pipeline status: {str(e)}"
        ) 