"""
Health Integration Service
Handles cross-service communication between device data and health tracking services.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from common.config.settings import get_settings
from common.utils.logging import get_logger
from ..models.data_point import DeviceDataPoint
from ..models.device import Device
from .event_producer import get_event_producer

logger = get_logger(__name__)
settings = get_settings()


class HealthIntegrationService:
    """
    Service for integrating device data with health tracking insights.
    Handles forwarding processed data and receiving health insights.
    """
    
    def __init__(self):
        self.health_tracking_url = f"http://localhost:8002"  # Health tracking service
        self.session = None
        self.event_producer = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"Content-Type": "application/json"}
            )
        return self.session
    
    async def _get_event_producer(self):
        """Get event producer instance"""
        if self.event_producer is None:
            self.event_producer = await get_event_producer()
        return self.event_producer
    
    async def forward_to_health_tracking(self, processed_data: DeviceDataPoint) -> bool:
        """
        Forward processed device data to health tracking service for analysis.
        
        Args:
            processed_data: Processed and validated data point
            
        Returns:
            bool: True if forwarded successfully, False otherwise
        """
        try:
            session = await self._get_session()
            event_producer = await self._get_event_producer()
            
            # Prepare data for health tracking
            health_data = {
                "user_id": str(processed_data.user_id),
                "device_id": str(processed_data.device_id),
                "data_type": processed_data.data_type,
                "value": processed_data.value,
                "unit": processed_data.unit,
                "timestamp": processed_data.timestamp.isoformat(),
                "quality": processed_data.quality,
                "source": "device_data",
                "metadata": processed_data.metadata
            }
            
            # Forward to health tracking service
            url = f"{self.health_tracking_url}/vital-signs/from-device"
            async with session.post(url, json=health_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Forwarded data to health tracking: {result.get('message', 'Success')}")
                    
                    # Publish integration event
                    await event_producer.publish_health_integration_event({
                        "event_type": "data_forwarded_to_health",
                        "data_point_id": str(processed_data.id),
                        "health_tracking_response": result,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    return True
                else:
                    logger.error(f"❌ Failed to forward data to health tracking: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error forwarding data to health tracking: {e}")
            return False
    
    async def receive_health_insights(self, insights: Dict[str, Any]) -> bool:
        """
        Receive health insights from health tracking service.
        
        Args:
            insights: Health insights and recommendations
            
        Returns:
            bool: True if processed successfully, False otherwise
        """
        try:
            event_producer = await self._get_event_producer()
            
            # Process health insights
            insight_type = insights.get("type", "unknown")
            user_id = insights.get("user_id")
            device_id = insights.get("device_id")
            
            logger.info(f"📊 Received health insight: {insight_type} for user {user_id}")
            
            # Publish insight event
            await event_producer.publish_health_insight_event({
                "event_type": "health_insight_received",
                "insight_type": insight_type,
                "user_id": user_id,
                "device_id": device_id,
                "insights": insights,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Handle different insight types
            if insight_type == "anomaly_detected":
                await self._handle_anomaly_insight(insights)
            elif insight_type == "trend_identified":
                await self._handle_trend_insight(insights)
            elif insight_type == "recommendation":
                await self._handle_recommendation_insight(insights)
            elif insight_type == "risk_assessment":
                await self._handle_risk_insight(insights)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing health insights: {e}")
            return False
    
    async def coordinate_analysis(self, device_id: str) -> Dict[str, Any]:
        """
        Coordinate comprehensive analysis between device data and health tracking.
        
        Args:
            device_id: Device to analyze
            
        Returns:
            Dict containing coordinated analysis results
        """
        try:
            session = await self._get_session()
            event_producer = await self._get_event_producer()
            
            # Trigger device data analysis
            device_analysis = await self._trigger_device_analysis(device_id)
            
            # Trigger health tracking analysis
            health_analysis = await self._trigger_health_analysis(device_id)
            
            # Combine and correlate results
            coordinated_results = await self._correlate_analyses(device_analysis, health_analysis)
            
            # Publish coordination event
            await event_producer.publish_coordination_event({
                "event_type": "analysis_coordinated",
                "device_id": device_id,
                "device_analysis": device_analysis,
                "health_analysis": health_analysis,
                "coordinated_results": coordinated_results,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return coordinated_results
            
        except Exception as e:
            logger.error(f"❌ Error coordinating analysis for device {device_id}: {e}")
            return {"error": str(e)}
    
    async def _handle_anomaly_insight(self, insights: Dict[str, Any]):
        """Handle anomaly insights from health tracking"""
        try:
            # Extract anomaly information
            anomaly_data = insights.get("anomaly", {})
            severity = anomaly_data.get("severity", "medium")
            description = anomaly_data.get("description", "")
            
            logger.info(f"🚨 Processing anomaly insight: {severity} - {description}")
            
            # Could trigger device recalibration or sync optimization
            if severity == "high":
                await self._trigger_device_recalibration(insights.get("device_id"))
                
        except Exception as e:
            logger.error(f"❌ Error handling anomaly insight: {e}")
    
    async def _handle_trend_insight(self, insights: Dict[str, Any]):
        """Handle trend insights from health tracking"""
        try:
            trend_data = insights.get("trend", {})
            trend_type = trend_data.get("type", "unknown")
            direction = trend_data.get("direction", "stable")
            
            logger.info(f"📈 Processing trend insight: {trend_type} - {direction}")
            
            # Could adjust device calibration based on trends
            if trend_type == "deteriorating":
                await self._adjust_device_calibration(insights.get("device_id"), "increase_sensitivity")
                
        except Exception as e:
            logger.error(f"❌ Error handling trend insight: {e}")
    
    async def _handle_recommendation_insight(self, insights: Dict[str, Any]):
        """Handle recommendation insights from health tracking"""
        try:
            recommendations = insights.get("recommendations", [])
            
            logger.info(f"💡 Processing {len(recommendations)} recommendations")
            
            for recommendation in recommendations:
                action = recommendation.get("action", "")
                if action == "increase_monitoring":
                    await self._increase_device_monitoring(insights.get("device_id"))
                elif action == "adjust_thresholds":
                    await self._adjust_device_thresholds(insights.get("device_id"), recommendation)
                    
        except Exception as e:
            logger.error(f"❌ Error handling recommendation insight: {e}")
    
    async def _handle_risk_insight(self, insights: Dict[str, Any]):
        """Handle risk assessment insights from health tracking"""
        try:
            risk_data = insights.get("risk", {})
            risk_level = risk_data.get("level", "low")
            risk_factors = risk_data.get("factors", [])
            
            logger.info(f"⚠️ Processing risk insight: {risk_level} - {len(risk_factors)} factors")
            
            # Could trigger emergency protocols or increased monitoring
            if risk_level == "high":
                await self._trigger_emergency_protocols(insights.get("device_id"))
                
        except Exception as e:
            logger.error(f"❌ Error handling risk insight: {e}")
    
    async def _trigger_device_analysis(self, device_id: str) -> Dict[str, Any]:
        """Trigger device data analysis"""
        try:
            session = await self._get_session()
            
            url = f"http://localhost:8004/agents/analyze/{device_id}"
            async with session.post(url, json={"analysis_type": "comprehensive"}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"❌ Device analysis failed: {response.status}")
                    return {"error": f"Device analysis failed: {response.status}"}
                    
        except Exception as e:
            logger.error(f"❌ Error triggering device analysis: {e}")
            return {"error": str(e)}
    
    async def _trigger_health_analysis(self, device_id: str) -> Dict[str, Any]:
        """Trigger health tracking analysis"""
        try:
            session = await self._get_session()
            
            url = f"{self.health_tracking_url}/analytics/device/{device_id}"
            async with session.post(url, json={"analysis_type": "comprehensive"}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"❌ Health analysis failed: {response.status}")
                    return {"error": f"Health analysis failed: {response.status}"}
                    
        except Exception as e:
            logger.error(f"❌ Error triggering health analysis: {e}")
            return {"error": str(e)}
    
    async def _correlate_analyses(self, device_analysis: Dict[str, Any], health_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Correlate device and health analyses"""
        try:
            # Combine insights from both analyses
            correlation = {
                "device_issues": device_analysis.get("quality_issues", []),
                "health_insights": health_analysis.get("insights", []),
                "recommendations": [],
                "alerts": []
            }
            
            # Generate cross-service recommendations
            device_anomalies = device_analysis.get("anomalies", [])
            health_anomalies = health_analysis.get("anomalies", [])
            
            # If both services detect anomalies, prioritize
            if device_anomalies and health_anomalies:
                correlation["alerts"].append({
                    "type": "cross_service_anomaly",
                    "severity": "high",
                    "message": "Anomalies detected by both device and health tracking services",
                    "device_anomalies": len(device_anomalies),
                    "health_anomalies": len(health_anomalies)
                })
            
            # Generate recommendations based on combined analysis
            if device_analysis.get("sync_issues"):
                correlation["recommendations"].append({
                    "type": "device_sync",
                    "priority": "medium",
                    "action": "Check device connectivity and sync settings"
                })
            
            if health_analysis.get("trends"):
                correlation["recommendations"].append({
                    "type": "health_monitoring",
                    "priority": "high",
                    "action": "Increase monitoring frequency based on health trends"
                })
            
            return correlation
            
        except Exception as e:
            logger.error(f"❌ Error correlating analyses: {e}")
            return {"error": str(e)}
    
    async def _trigger_device_recalibration(self, device_id: str):
        """Trigger device recalibration"""
        try:
            session = await self._get_session()
            
            url = f"http://localhost:8004/agents/calibrate/{device_id}"
            async with session.post(url, json={"calibration_type": "automatic"}) as response:
                if response.status == 200:
                    logger.info(f"✅ Device recalibration triggered for {device_id}")
                else:
                    logger.error(f"❌ Device recalibration failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ Error triggering device recalibration: {e}")
    
    async def _adjust_device_calibration(self, device_id: str, adjustment: str):
        """Adjust device calibration based on insights"""
        try:
            logger.info(f"🔧 Adjusting device calibration for {device_id}: {adjustment}")
            # Implementation would depend on specific device capabilities
            
        except Exception as e:
            logger.error(f"❌ Error adjusting device calibration: {e}")
    
    async def _increase_device_monitoring(self, device_id: str):
        """Increase device monitoring frequency"""
        try:
            logger.info(f"📊 Increasing monitoring frequency for device {device_id}")
            # Implementation would adjust sync schedules
            
        except Exception as e:
            logger.error(f"❌ Error increasing device monitoring: {e}")
    
    async def _adjust_device_thresholds(self, device_id: str, recommendation: Dict[str, Any]):
        """Adjust device thresholds based on recommendations"""
        try:
            logger.info(f"⚙️ Adjusting thresholds for device {device_id}")
            # Implementation would update device configuration
            
        except Exception as e:
            logger.error(f"❌ Error adjusting device thresholds: {e}")
    
    async def _trigger_emergency_protocols(self, device_id: str):
        """Trigger emergency protocols for high-risk situations"""
        try:
            logger.warning(f"🚨 Triggering emergency protocols for device {device_id}")
            # Implementation would include emergency notifications, increased monitoring, etc.
            
        except Exception as e:
            logger.error(f"❌ Error triggering emergency protocols: {e}")
    
    async def close(self):
        """Close the service and cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()


# Global instance
_health_integration_service = None


async def get_health_integration_service() -> HealthIntegrationService:
    """Get the global health integration service instance"""
    global _health_integration_service
    if _health_integration_service is None:
        _health_integration_service = HealthIntegrationService()
    return _health_integration_service


async def close_health_integration_service():
    """Close the global health integration service"""
    global _health_integration_service
    if _health_integration_service:
        await _health_integration_service.close()
        _health_integration_service = None 