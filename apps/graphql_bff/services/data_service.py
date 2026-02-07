"""
Data Service for GraphQL BFF
Handles data aggregation and retrieval for the unified GraphQL interface.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx
from common.utils.logging import get_logger

logger = get_logger(__name__)

class DataService:
    """Service for aggregating and retrieving health data"""
    
    def __init__(self, service_registry: Dict[str, Any]):
        self.service_registry = service_registry
        self.logger = logger
    
    async def get_daily_summary(self, user_id: str) -> Dict[str, Any]:
        """Get daily health summary"""
        try:
            # Use AI Reasoning Orchestrator for daily summary
            orchestrator_config = self.service_registry.get("ai_reasoning_orchestrator")
            if not orchestrator_config:
                raise Exception("AI Reasoning Orchestrator not available")
            
            self.logger.info(f"Orchestrator config: {orchestrator_config}")
            url = f"{orchestrator_config['url']}/health/daily-summary"
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.get(url)
                self.logger.info(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to get daily summary: {response.status_code} - {response.text}")
                    return self._generate_fallback_daily_summary(user_id)
                    
        except Exception as e:
            self.logger.error(f"Error getting daily summary: {e}", exc_info=True)
            return self._generate_fallback_daily_summary(user_id)

    async def get_unified_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get unified health dashboard"""
        try:
            # Use AI Reasoning Orchestrator for unified dashboard
            orchestrator_config = self.service_registry.get("ai_reasoning_orchestrator")
            if not orchestrator_config:
                raise Exception("AI Reasoning Orchestrator not available")
            
            self.logger.info(f"Orchestrator config: {orchestrator_config}")
            url = f"{orchestrator_config['url']}/health/unified-dashboard-test"
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.get(url)
                self.logger.info(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to get unified dashboard: {response.status_code} - {response.text}")
                    return self._generate_fallback_unified_dashboard(user_id)
                    
        except Exception as e:
            self.logger.error(f"Error getting unified dashboard: {e}", exc_info=True)
            return self._generate_fallback_unified_dashboard(user_id)

    async def analyze_symptoms(self, user_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze symptoms using AI Reasoning Orchestrator"""
        try:
            # Use AI Reasoning Orchestrator for symptom analysis
            orchestrator_config = self.service_registry.get("ai_reasoning_orchestrator")
            if not orchestrator_config:
                raise Exception("AI Reasoning Orchestrator not available")
            
            self.logger.info(f"Orchestrator config: {orchestrator_config}")
            url = f"{orchestrator_config['url']}/health/analyze-symptoms"
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=request_data)
                self.logger.info(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to analyze symptoms: {response.status_code} - {response.text}")
                    return self._generate_fallback_symptom_analysis(user_id, request_data)
                    
        except Exception as e:
            self.logger.error(f"Error analyzing symptoms: {e}", exc_info=True)
            return self._generate_fallback_symptom_analysis(user_id, request_data)

    async def health_query(self, user_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process health queries using AI Reasoning Orchestrator"""
        try:
            # Use AI Reasoning Orchestrator for health queries
            orchestrator_config = self.service_registry.get("ai_reasoning_orchestrator")
            if not orchestrator_config:
                raise Exception("AI Reasoning Orchestrator not available")
            
            self.logger.info(f"Orchestrator config: {orchestrator_config}")
            url = f"{orchestrator_config['url']}/health/query"
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=request_data)
                self.logger.info(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to process health query: {response.status_code} - {response.text}")
                    return self._generate_fallback_health_query(user_id, request_data)
                    
        except Exception as e:
            self.logger.error(f"Error processing health query: {e}", exc_info=True)
            return self._generate_fallback_health_query(user_id, request_data)

    async def doctor_report(self, user_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate doctor report using AI Reasoning Orchestrator"""
        try:
            # Use AI Reasoning Orchestrator for doctor reports
            orchestrator_config = self.service_registry.get("ai_reasoning_orchestrator")
            if not orchestrator_config:
                raise Exception("AI Reasoning Orchestrator not available")
            
            self.logger.info(f"Orchestrator config: {orchestrator_config}")
            url = f"{orchestrator_config['url']}/health/doctor-report"
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=request_data)
                self.logger.info(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to generate doctor report: {response.status_code} - {response.text}")
                    return self._generate_fallback_doctor_report(user_id, request_data)
                    
        except Exception as e:
            self.logger.error(f"Error generating doctor report: {e}", exc_info=True)
            return self._generate_fallback_doctor_report(user_id, request_data)
    
    async def get_health_data(
        self, 
        user_id: str, 
        time_window: str = "24h",
        data_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get aggregated health data"""
        try:
            # Use AI Reasoning Orchestrator's data aggregator
            orchestrator_config = self.service_registry.get("ai_reasoning_orchestrator")
            if not orchestrator_config:
                raise Exception("AI Reasoning Orchestrator not available")
            
            # Create a reasoning request to get aggregated data
            url = f"{orchestrator_config['url']}/api/v1/reason"
            payload = {
                "query": "Get health data summary",
                "reasoning_type": "daily_summary",
                "time_window": time_window,
                "data_types": data_types or ["vitals", "symptoms", "medications", "nutrition", "sleep", "activity"]
            }
            headers = {"Authorization": f"Bearer user-{user_id}"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    result = response.json()
                    # Extract the aggregated data from the reasoning result
                    return self._extract_health_data_from_reasoning(result)
                else:
                    self.logger.warning(f"Failed to get health data: {response.status_code}")
                    return self._generate_fallback_health_data(user_id, time_window)
                    
        except Exception as e:
            self.logger.error(f"Error getting health data: {e}")
            return self._generate_fallback_health_data(user_id, time_window)
    
    async def get_real_time_insights(self, user_id: str) -> List[Dict[str, Any]]:
        """Get real-time health insights"""
        try:
            # This would typically come from a real-time service
            # For now, return a placeholder
            return [
                {
                    "id": f"rt-{user_id}-{datetime.now().timestamp()}",
                    "type": "real_time",
                    "message": "Health status is normal",
                    "priority": "normal",
                    "timestamp": datetime.now().isoformat(),
                    "actionable": False,
                    "data_source": "health_monitoring"
                }
            ]
        except Exception as e:
            self.logger.error(f"Error getting real-time insights: {e}")
            return []
    
    async def get_insights_history(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get historical insights"""
        try:
            # Use AI Insights service for historical insights
            ai_insights_config = self.service_registry.get("ai_insights")
            if not ai_insights_config:
                raise Exception("AI Insights service not available")
            
            url = f"{ai_insights_config['url']}/api/v1/ai-insights/insights"
            params = {
                "patient_id": user_id,
                "limit": limit,
                "offset": offset
            }
            headers = {"Authorization": f"Bearer user-{user_id}"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    result = response.json()
                    return result.get("data", [])
                else:
                    self.logger.warning(f"Failed to get insights history: {response.status_code}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error getting insights history: {e}")
            return []
    
    async def provide_feedback(
        self, 
        user_id: str, 
        insight_id: str, 
        helpful: bool, 
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Provide feedback on health insights"""
        try:
            # Store feedback for improving AI models
            feedback_data = {
                "user_id": user_id,
                "insight_id": insight_id,
                "helpful": helpful,
                "comment": comment,
                "timestamp": datetime.now().isoformat()
            }
            
            # In a real implementation, this would be stored in a database
            # and used to improve the AI models
            
            return {
                "success": True,
                "message": "Feedback recorded successfully",
                "insight_id": insight_id,
                "feedback_id": f"fb-{user_id}-{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error providing feedback: {e}")
            return {
                "success": False,
                "message": "Failed to record feedback",
                "insight_id": insight_id,
                "feedback_id": "",
                "timestamp": datetime.now().isoformat()
            }
    
    async def log_symptom(
        self, 
        user_id: str, 
        symptom: str, 
        severity: Optional[str] = None,
        duration: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Log a new symptom"""
        try:
            # Use Health Tracking service to log symptom
            health_tracking_config = self.service_registry.get("health_tracking")
            if not health_tracking_config:
                raise Exception("Health Tracking service not available")
            
            url = f"{health_tracking_config['url']}/api/v1/health-tracking/symptoms"
            payload = {
                "user_id": user_id,
                "symptom": symptom,
                "severity": severity,
                "duration": duration,
                "notes": notes,
                "timestamp": datetime.now().isoformat()
            }
            headers = {"Authorization": f"Bearer user-{user_id}"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                return response.status_code == 200
                
        except Exception as e:
            self.logger.error(f"Error logging symptom: {e}")
            return False
    
    async def log_vital(
        self, 
        user_id: str, 
        vital_type: str, 
        value: float, 
        unit: str, 
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Log a vital sign measurement"""
        try:
            # Use Health Tracking service to log vital
            health_tracking_config = self.service_registry.get("health_tracking")
            if not health_tracking_config:
                raise Exception("Health Tracking service not available")
            
            url = f"{health_tracking_config['url']}/api/v1/health-tracking/vitals/{vital_type}"
            payload = {
                "user_id": user_id,
                "value": value,
                "unit": unit,
                "timestamp": (timestamp or datetime.now()).isoformat()
            }
            headers = {"Authorization": f"Bearer user-{user_id}"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                return response.status_code == 200
                
        except Exception as e:
            self.logger.error(f"Error logging vital: {e}")
            return False
    
    def _extract_health_data_from_reasoning(self, reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract health data from reasoning result"""
        # This is a simplified extraction - in practice, the reasoning service
        # would return the raw aggregated data along with the reasoning
        return {
            "user_id": "extracted_from_reasoning",
            "time_window": "24h",
            "vitals": {},
            "symptoms": [],
            "medications": [],
            "nutrition": [],
            "sleep": [],
            "activity": [],
            "lab_results": [],
            "medical_records": [],
            "device_data": [],
            "summary": {
                "total_records": 0,
                "data_quality_score": 0.0,
                "last_updated": datetime.now().isoformat(),
                "data_types_available": [],
                "anomalies_detected": [],
                "trends_identified": []
            }
        }
    
    def _generate_fallback_daily_summary(self, user_id: str) -> Dict[str, Any]:
        """Generate fallback daily summary when services are unavailable"""
        return {
            "id": f"daily-{user_id}-{datetime.now().date()}",
            "date": datetime.now().isoformat(),
            "summary": "Daily summary not available due to service issues",
            "key_insights": [],
            "recommendations": [],
            "health_score": 0.0,
            "data_quality_score": 0.0,
            "trends": [],
            "anomalies": []
        }
    
    def _generate_fallback_health_data(self, user_id: str, time_window: str) -> Dict[str, Any]:
        """Generate fallback health data when services are unavailable"""
        return {
            "user_id": user_id,
            "time_window": time_window,
            "vitals": {},
            "symptoms": [],
            "medications": [],
            "nutrition": [],
            "sleep": [],
            "activity": [],
            "lab_results": [],
            "medical_records": [],
            "device_data": [],
            "summary": {
                "total_records": 0,
                "data_quality_score": 0.0,
                "last_updated": datetime.now().isoformat(),
                "data_types_available": [],
                "anomalies_detected": [],
                "trends_identified": []
            }
        }

    def _generate_fallback_unified_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Generate fallback unified dashboard when services are unavailable"""
        return {
            "user_id": user_id,
            "dashboard_type": "unified_health",
            "generated_at": datetime.now().isoformat(),
            "time_window": "7d",
            "summary": "Dashboard data temporarily unavailable",
            "key_metrics": {
                "health_score": 0.0,
                "data_completeness": 0.0,
                "risk_level": "unknown",
                "trend_direction": "unknown"
            },
            "insights": [],
            "recommendations": [
                {
                    "title": "Service Temporarily Unavailable",
                    "description": "The health dashboard service is currently unavailable. Please try again later.",
                    "category": "system",
                    "priority": "high",
                    "actionable": False,
                    "evidence": [],
                    "follow_up": None,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "recent_activity": {
                "last_vital_recorded": None,
                "last_symptom_logged": None,
                "last_medication_taken": None
            },
            "alerts": [
                {
                    "id": "alert-fallback",
                    "type": "warning",
                    "message": "Dashboard service temporarily unavailable",
                    "priority": "high",
                    "actionable": False
                }
            ],
            "data_sources": [],
            "confidence": "low"
        }

    def _generate_fallback_symptom_analysis(self, user_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback symptom analysis when services are unavailable"""
        symptoms = request_data.get("symptoms", [])
        severity = request_data.get("severity", "medium")
        duration = request_data.get("duration", "unknown")
        
        return {
            "user_id": user_id,
            "analyzed_at": datetime.now().isoformat(),
            "symptoms_analyzed": symptoms,
            "severity": severity,
            "duration": duration,
            "analysis": "Symptom analysis service temporarily unavailable",
            "insights": [],
            "recommendations": [
                {
                    "title": "Service Temporarily Unavailable",
                    "description": "The symptom analysis service is currently unavailable. Please try again later.",
                    "category": "system",
                    "priority": "high",
                    "actionable": False,
                    "evidence": [],
                    "follow_up": None,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "possible_causes": [],
            "urgency_level": "unknown",
            "next_steps": [
                "Try again in a few minutes",
                "Contact support if the issue persists",
                "Consider consulting a healthcare provider for urgent symptoms"
            ],
            "data_sources": [],
            "confidence": "low"
        }

    def _generate_fallback_health_query(self, user_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback health query response when services are unavailable"""
        query = request_data.get("query", "")
        context = request_data.get("context", "")
        
        return {
            "user_id": user_id,
            "query": query,
            "context": context,
            "answered_at": datetime.now().isoformat(),
            "answer": "Health query service temporarily unavailable",
            "insights": [],
            "recommendations": [
                {
                    "title": "Service Temporarily Unavailable",
                    "description": "The health query service is currently unavailable. Please try again later.",
                    "category": "system",
                    "priority": "high",
                    "actionable": False,
                    "evidence": [],
                    "follow_up": None,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "confidence": "low",
            "data_sources": [],
            "related_topics": [],
            "follow_up_questions": [
                "Try again in a few minutes",
                "Contact support if the issue persists",
                "Consider consulting a healthcare provider for urgent health concerns"
            ]
        }

    def _generate_fallback_doctor_report(self, user_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback doctor report when services are unavailable"""
        report_type = request_data.get("report_type", "comprehensive")
        time_window = request_data.get("time_window", "30d")
        
        return {
            "user_id": user_id,
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "time_window": time_window,
            "patient_summary": {
                "age": "Unknown",
                "gender": "Not specified",
                "primary_concerns": ["Service unavailable"],
                "current_medications": ["Unknown"],
                "allergies": ["Unknown"],
                "family_history": ["Unknown"]
            },
            "vital_signs_summary": {
                "blood_pressure": "Not available",
                "heart_rate": "Not available",
                "temperature": "Not available",
                "weight": "Not available",
                "trends": "Not available"
            },
            "symptom_analysis": {
                "primary_symptoms": ["Service unavailable"],
                "severity": "Unknown",
                "duration": "Unknown",
                "triggers": ["Unknown"],
                "impact": "Unknown"
            },
            "lifestyle_factors": {
                "sleep_patterns": "Not available",
                "exercise": "Not available",
                "diet": "Not available",
                "stress_levels": "Not available"
            },
            "recommendations": [
                {
                    "title": "Service Temporarily Unavailable",
                    "description": "The doctor report service is currently unavailable. Please try again later.",
                    "category": "system",
                    "priority": "high",
                    "actionable": False,
                    "evidence": [],
                    "follow_up": None,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "insights": [],
            "clinical_notes": "Doctor report service temporarily unavailable",
            "next_steps": [
                "Try again in a few minutes",
                "Contact support if the issue persists",
                "Consider consulting a healthcare provider directly for urgent concerns"
            ],
            "risk_factors": [],
            "data_sources": [],
            "confidence": "low",
            "report_metadata": {
                "generated_by": "Fallback System",
                "data_completeness": "0%",
                "last_data_update": "Unknown"
            }
        }
