"""
Reasoning Service for GraphQL BFF
Handles health reasoning queries through the AI Reasoning Orchestrator.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from common.utils.logging import get_logger

logger = get_logger(__name__)

class ReasoningService:
    """Service for health reasoning queries"""
    
    def __init__(self, service_registry: Dict[str, Any]):
        self.service_registry = service_registry
        self.logger = logger
    
    async def query_health(
        self,
        query: str,
        reasoning_type: str = "symptom_analysis",
        time_window: str = "24h",
        data_types: Optional[List[str]] = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """Query health reasoning through AI Reasoning Orchestrator"""
        try:
            orchestrator_config = self.service_registry.get("ai_reasoning_orchestrator")
            if not orchestrator_config:
                raise Exception("AI Reasoning Orchestrator not available")
            
            url = f"{orchestrator_config['url']}/api/v1/reason"
            payload = {
                "query": query,
                "reasoning_type": reasoning_type,
                "time_window": time_window,
                "data_types": data_types or ["vitals", "symptoms", "medications", "nutrition"]
            }
            headers = {"Authorization": f"Bearer user-{user_id}"} if user_id else {}
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to query health reasoning: {response.status_code}")
                    return self._generate_fallback_reasoning_result(query, reasoning_type)
                    
        except Exception as e:
            self.logger.error(f"Error querying health reasoning: {e}")
            return self._generate_fallback_reasoning_result(query, reasoning_type)
    
    async def generate_doctor_report(
        self, 
        user_id: str, 
        time_window: str = "30d"
    ) -> Dict[str, Any]:
        """Generate comprehensive doctor report"""
        try:
            orchestrator_config = self.service_registry.get("ai_reasoning_orchestrator")
            if not orchestrator_config:
                raise Exception("AI Reasoning Orchestrator not available")
            
            url = f"{orchestrator_config['url']}/api/v1/doctor-mode/report"
            payload = {
                "time_window": time_window
            }
            headers = {"Authorization": f"Bearer user-{user_id}"}
            
            async with httpx.AsyncClient(timeout=120.0) as client:  # Longer timeout for reports
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to generate doctor report: {response.status_code}")
                    return self._generate_fallback_doctor_report(user_id, time_window)
                    
        except Exception as e:
            self.logger.error(f"Error generating doctor report: {e}")
            return self._generate_fallback_doctor_report(user_id, time_window)
    
    async def natural_language_query(
        self, 
        question: str, 
        user_id: str,
        time_window: str = "24h"
    ) -> Dict[str, Any]:
        """Process natural language health questions"""
        try:
            orchestrator_config = self.service_registry.get("ai_reasoning_orchestrator")
            if not orchestrator_config:
                raise Exception("AI Reasoning Orchestrator not available")
            
            url = f"{orchestrator_config['url']}/api/v1/query"
            payload = {
                "question": question,
                "time_window": time_window
            }
            headers = {"Authorization": f"Bearer user-{user_id}"}
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to process natural language query: {response.status_code}")
                    return self._generate_fallback_natural_language_result(question)
                    
        except Exception as e:
            self.logger.error(f"Error processing natural language query: {e}")
            return self._generate_fallback_natural_language_result(question)
    
    async def get_insights_by_type(
        self, 
        user_id: str, 
        insight_type: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get insights by type"""
        try:
            # Use AI Insights service for type-specific insights
            ai_insights_config = self.service_registry.get("ai_insights")
            if not ai_insights_config:
                raise Exception("AI Insights service not available")
            
            url = f"{ai_insights_config['url']}/api/v1/ai-insights/insights"
            params = {
                "patient_id": user_id,
                "insight_type": insight_type,
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
                    self.logger.warning(f"Failed to get insights by type: {response.status_code}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error getting insights by type: {e}")
            return []
    
    async def get_recommendations(
        self, 
        user_id: str, 
        category: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get health recommendations"""
        try:
            # Use AI Insights service for recommendations
            ai_insights_config = self.service_registry.get("ai_insights")
            if not ai_insights_config:
                raise Exception("AI Insights service not available")
            
            url = f"{ai_insights_config['url']}/api/v1/ai-insights/recommendations"
            params = {
                "patient_id": user_id,
                "category": category,
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
                    self.logger.warning(f"Failed to get recommendations: {response.status_code}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error getting recommendations: {e}")
            return []
    
    async def analyze_trends(
        self, 
        user_id: str, 
        metric: str,
        time_window: str = "30d"
    ) -> Dict[str, Any]:
        """Analyze trends for a specific health metric"""
        try:
            # Use AI Insights service for trend analysis
            ai_insights_config = self.service_registry.get("ai_insights")
            if not ai_insights_config:
                raise Exception("AI Insights service not available")
            
            url = f"{ai_insights_config['url']}/api/v1/ai-insights/patterns"
            params = {
                "patient_id": user_id,
                "metric": metric,
                "time_window": time_window
            }
            headers = {"Authorization": f"Bearer user-{user_id}"}
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to analyze trends: {response.status_code}")
                    return self._generate_fallback_trend_analysis(metric)
                    
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            return self._generate_fallback_trend_analysis(metric)
    
    def _generate_fallback_reasoning_result(self, query: str, reasoning_type: str) -> Dict[str, Any]:
        """Generate fallback reasoning result when services are unavailable"""
        return {
            "query": query,
            "reasoning": f"Unable to complete {reasoning_type} analysis for: {query}. Service temporarily unavailable.",
            "insights": [],
            "recommendations": [],
            "evidence": {},
            "confidence": "uncertain",
            "processing_time": 0.0,
            "data_sources": [],
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_fallback_doctor_report(self, user_id: str, time_window: str) -> Dict[str, Any]:
        """Generate fallback doctor report when services are unavailable"""
        return {
            "patient_id": user_id,
            "report_date": datetime.now().isoformat(),
            "time_period": time_window,
            "summary": "Doctor report generation temporarily unavailable due to service issues.",
            "key_insights": [],
            "recommendations": [],
            "trends": [],
            "anomalies": [],
            "data_quality": {},
            "confidence_score": 0.0,
            "next_steps": ["Try again later when services are available"]
        }
    
    def _generate_fallback_natural_language_result(self, question: str) -> Dict[str, Any]:
        """Generate fallback result for natural language queries"""
        return {
            "query": question,
            "reasoning": f"Unable to process question: {question}. Service temporarily unavailable.",
            "insights": [],
            "recommendations": [],
            "evidence": {},
            "confidence": "uncertain",
            "processing_time": 0.0,
            "data_sources": [],
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_fallback_trend_analysis(self, metric: str) -> Dict[str, Any]:
        """Generate fallback trend analysis"""
        return {
            "metric": metric,
            "trend": "unknown",
            "direction": "unknown",
            "confidence": "uncertain",
            "data_points": [],
            "analysis": f"Trend analysis for {metric} temporarily unavailable.",
            "recommendations": []
        }
