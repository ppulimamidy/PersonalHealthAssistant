"""
AI Reasoning Engine Service
Core reasoning engine using LangChain and GPT-4 for health insights generation.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import httpx
from common.utils.logging import get_logger

# Import models
from ..models.reasoning_models import (
    Insight, Recommendation, Evidence, InsightType, 
    EvidenceSource, ConfidenceLevel, ReasoningType
)

logger = get_logger(__name__)

class AIReasoningEngine:
    """AI reasoning engine for health insights generation"""
    
    def __init__(self):
        self.logger = logger
        self.ai_insights_url = "http://ai-insights-service:8000"
        
        # Reasoning templates for different types of analysis
        self.reasoning_templates = {
            "symptom_analysis": self._symptom_analysis_template,
            "daily_summary": self._daily_summary_template,
            "doctor_report": self._doctor_report_template,
            "real_time_insights": self._real_time_insights_template,
            "trend_analysis": self._trend_analysis_template,
            "correlation_analysis": self._correlation_analysis_template,
            "risk_assessment": self._risk_assessment_template,
            "medication_review": self._medication_review_template
        }
    
    async def reason(
        self,
        query: str,
        user_data: Dict[str, Any],
        knowledge_context: Dict[str, Any],
        reasoning_type: ReasoningType
    ) -> Dict[str, Any]:
        """
        Perform AI reasoning to generate insights and recommendations.
        
        Args:
            query: Health query or question
            user_data: Aggregated user health data
            knowledge_context: Medical knowledge context
            reasoning_type: Type of reasoning to perform
            
        Returns:
            Reasoning results with insights and recommendations
        """
        self.logger.info(f"🧠 Starting AI reasoning for type: {reasoning_type}")
        
        try:
            # Get reasoning template
            template_func = self.reasoning_templates.get(reasoning_type.value, self._default_template)
            
            # Prepare context for AI reasoning
            reasoning_context = self._prepare_reasoning_context(
                query, user_data, knowledge_context, reasoning_type
            )
            
            # Generate reasoning using AI insights service
            reasoning_result = await self._generate_ai_reasoning(
                template_func, reasoning_context
            )
            
            # Parse and structure the results
            structured_result = self._structure_reasoning_results(
                reasoning_result, user_data, knowledge_context
            )
            
            self.logger.info(f"✅ AI reasoning completed successfully")
            return structured_result
            
        except Exception as e:
            self.logger.error(f"❌ AI reasoning failed: {e}")
            return self._generate_fallback_result(query, reasoning_type)
    
    def _prepare_reasoning_context(
        self,
        query: str,
        user_data: Dict[str, Any],
        knowledge_context: Dict[str, Any],
        reasoning_type: ReasoningType
    ) -> Dict[str, Any]:
        """Prepare context for AI reasoning"""
        
        # Extract key data points
        vitals = user_data.get("vitals", {})
        symptoms = user_data.get("symptoms", [])
        medications = user_data.get("medications", [])
        nutrition = user_data.get("nutrition", [])
        sleep = user_data.get("sleep", [])
        activity = user_data.get("activity", [])
        
        # Prepare structured context
        context = {
            "query": query,
            "reasoning_type": reasoning_type.value,
            "user_data_summary": {
                "vitals_count": len(vitals) if isinstance(vitals, list) else 0,
                "symptoms_count": len(symptoms),
                "medications_count": len(medications),
                "nutrition_count": len(nutrition),
                "sleep_count": len(sleep),
                "activity_count": len(activity),
                "data_quality_score": user_data.get("summary", {}).get("data_quality_score", 0.0)
            },
            "recent_symptoms": self._extract_recent_symptoms(symptoms),
            "current_medications": self._extract_medication_names(medications),
            "recent_vitals": self._extract_recent_vitals(vitals),
            "recent_nutrition": self._extract_recent_nutrition(nutrition),
            "knowledge_context": {
                "risk_factors": knowledge_context.get("risk_factors", []),
                "drug_interactions": knowledge_context.get("drug_interactions", []),
                "clinical_guidelines": knowledge_context.get("clinical_guidelines", []),
                "evidence_level": knowledge_context.get("evidence_level", "moderate")
            }
        }
        
        return context
    
    async def _generate_ai_reasoning(
        self,
        template_func,
        reasoning_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate reasoning using AI insights service"""
        try:
            # Prepare prompt using template
            prompt = template_func(reasoning_context)
            
            url = f"{self.ai_insights_url}/api/v1/ai-insights/generate"
            payload = {
                "prompt": prompt,
                "context": reasoning_context,
                "max_tokens": 2000,
                "temperature": 0.3
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to generate AI reasoning: {response.status_code}")
                    return self._generate_fallback_reasoning(reasoning_context)
                    
        except Exception as e:
            self.logger.error(f"Error generating AI reasoning: {e}")
            return self._generate_fallback_reasoning(reasoning_context)
    
    def _structure_reasoning_results(
        self,
        ai_result: Dict[str, Any],
        user_data: Dict[str, Any],
        knowledge_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Structure AI reasoning results into standardized format"""
        
        # Extract reasoning text
        reasoning_text = ai_result.get("reasoning", "Analysis completed based on available data.")
        
        # Generate insights
        insights = self._generate_insights(ai_result, user_data, knowledge_context)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(ai_result, user_data, knowledge_context)
        
        # Generate evidence
        evidence = self._generate_evidence(user_data, knowledge_context)
        
        # Calculate confidence
        confidence = self._calculate_confidence(user_data, knowledge_context)
        
        return {
            "reasoning": reasoning_text,
            "insights": insights,
            "recommendations": recommendations,
            "evidence": evidence,
            "confidence": confidence,
            "data_sources": list(user_data.get("data_sources", []))
        }
    
    def _generate_insights(
        self,
        ai_result: Dict[str, Any],
        user_data: Dict[str, Any],
        knowledge_context: Dict[str, Any]
    ) -> List[Insight]:
        """Generate structured insights from AI reasoning"""
        insights = []
        
        # Extract insights from AI result
        ai_insights = ai_result.get("insights", [])
        
        for ai_insight in ai_insights:
            if isinstance(ai_insight, dict):
                insight = Insight(
                    type=InsightType(ai_insight.get("type", "symptom_analysis")),
                    title=ai_insight.get("title", "Health Insight"),
                    description=ai_insight.get("description", ""),
                    severity=ai_insight.get("severity"),
                    confidence=ConfidenceLevel(ai_insight.get("confidence", "medium")),
                    actionable=ai_insight.get("actionable", True)
                )
                insights.append(insight)
        
        # Generate additional insights from data analysis
        data_insights = self._analyze_data_for_insights(user_data, knowledge_context)
        insights.extend(data_insights)
        
        return insights
    
    def _generate_recommendations(
        self,
        ai_result: Dict[str, Any],
        user_data: Dict[str, Any],
        knowledge_context: Dict[str, Any]
    ) -> List[Recommendation]:
        """Generate structured recommendations from AI reasoning"""
        recommendations = []
        
        # Extract recommendations from AI result
        ai_recommendations = ai_result.get("recommendations", [])
        
        for ai_rec in ai_recommendations:
            if isinstance(ai_rec, dict):
                recommendation = Recommendation(
                    title=ai_rec.get("title", "Health Recommendation"),
                    description=ai_rec.get("description", ""),
                    category=ai_rec.get("category", "general"),
                    priority=ai_rec.get("priority", "medium"),
                    actionable=ai_rec.get("actionable", True),
                    follow_up=ai_rec.get("follow_up")
                )
                recommendations.append(recommendation)
        
        # Generate additional recommendations from data analysis
        data_recommendations = self._analyze_data_for_recommendations(user_data, knowledge_context)
        recommendations.extend(data_recommendations)
        
        return recommendations
    
    def _generate_evidence(
        self,
        user_data: Dict[str, Any],
        knowledge_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate evidence supporting the reasoning"""
        evidence = {
            "data_sources": user_data.get("data_sources", []),
            "knowledge_sources": list(knowledge_context.keys()),
            "risk_factors": knowledge_context.get("risk_factors", []),
            "drug_interactions": knowledge_context.get("drug_interactions", []),
            "trends": self._identify_trends(user_data),
            "anomalies": self._identify_anomalies(user_data),
            "data_quality": user_data.get("summary", {})
        }
        
        return evidence
    
    def _calculate_confidence(
        self,
        user_data: Dict[str, Any],
        knowledge_context: Dict[str, Any]
    ) -> ConfidenceLevel:
        """Calculate confidence level in reasoning results"""
        confidence_score = 0
        
        # Data quality contribution
        data_quality = user_data.get("summary", {}).get("data_quality_score", 0.0)
        confidence_score += data_quality * 0.4
        
        # Knowledge availability contribution
        evidence_level = knowledge_context.get("evidence_level", "low")
        if evidence_level == "high":
            confidence_score += 0.4
        elif evidence_level == "moderate":
            confidence_score += 0.2
        
        # Data completeness contribution
        data_types = user_data.get("data_sources", [])
        if len(data_types) >= 5:
            confidence_score += 0.2
        elif len(data_types) >= 3:
            confidence_score += 0.1
        
        # Determine confidence level
        if confidence_score >= 0.8:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.2:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN
    
    # Reasoning templates
    def _symptom_analysis_template(self, context: Dict[str, Any]) -> str:
        """Template for symptom analysis reasoning"""
        return f"""
        Analyze the following health query and provide detailed reasoning:
        
        Query: {context['query']}
        
        User Data:
        - Recent symptoms: {context['recent_symptoms']}
        - Current medications: {context['current_medications']}
        - Recent vitals: {context['recent_vitals']}
        - Data quality: {context['user_data_summary']['data_quality_score']}
        
        Knowledge Context:
        - Risk factors: {context['knowledge_context']['risk_factors']}
        - Drug interactions: {len(context['knowledge_context']['drug_interactions'])} found
        - Evidence level: {context['knowledge_context']['evidence_level']}
        
        Please provide:
        1. Detailed reasoning about possible causes
        2. Key insights with confidence levels
        3. Actionable recommendations
        4. Evidence supporting your analysis
        """
    
    def _daily_summary_template(self, context: Dict[str, Any]) -> str:
        """Template for daily summary reasoning"""
        return f"""
        Generate a comprehensive daily health summary:
        
        User Data Summary:
        - Vitals recorded: {context['user_data_summary']['vitals_count']}
        - Symptoms reported: {context['user_data_summary']['symptoms_count']}
        - Medications taken: {context['user_data_summary']['medications_count']}
        - Nutrition logged: {context['user_data_summary']['nutrition_count']}
        - Sleep data: {context['user_data_summary']['sleep_count']}
        - Activity data: {context['user_data_summary']['activity_count']}
        
        Recent Data:
        - Symptoms: {context['recent_symptoms']}
        - Vitals: {context['recent_vitals']}
        - Nutrition: {context['recent_nutrition']}
        
        Please provide:
        1. Overall health status summary
        2. Key trends and patterns
        3. Notable insights
        4. Recommendations for tomorrow
        """
    
    def _doctor_report_template(self, context: Dict[str, Any]) -> str:
        """Template for doctor report reasoning"""
        return f"""
        Generate a comprehensive doctor mode report:
        
        Data Coverage:
        - Data quality score: {context['user_data_summary']['data_quality_score']}
        - Data types available: {len(context['user_data_summary'])} types
        
        Clinical Context:
        - Risk factors: {context['knowledge_context']['risk_factors']}
        - Drug interactions: {len(context['knowledge_context']['drug_interactions'])} identified
        - Clinical guidelines: {len(context['knowledge_context']['clinical_guidelines'])} relevant
        
        Please provide:
        1. Executive summary for healthcare provider
        2. Key clinical insights
        3. Risk assessments
        4. Treatment recommendations
        5. Follow-up suggestions
        """
    
    def _default_template(self, context: Dict[str, Any]) -> str:
        """Default reasoning template"""
        return f"""
        Analyze the following health query:
        
        Query: {context['query']}
        Data available: {context['user_data_summary']}
        
        Please provide reasoned analysis with insights and recommendations.
        """
    
    def _real_time_insights_template(self, context: Dict[str, Any]) -> str:
        """Template for real-time insights reasoning"""
        return f"""
        Generate real-time health insights:
        
        Recent Data:
        - Symptoms: {context['recent_symptoms']}
        - Vitals: {context['recent_vitals']}
        - Activity: {context['user_data_summary']['activity_count']} records
        
        Please provide:
        1. Immediate health status assessment
        2. Urgent alerts if any
        3. Quick recommendations
        4. Next monitoring steps
        """
    
    def _trend_analysis_template(self, context: Dict[str, Any]) -> str:
        """Template for trend analysis reasoning"""
        return f"""
        Analyze health trends over time:
        
        Data Summary:
        - Vitals: {context['user_data_summary']['vitals_count']} records
        - Symptoms: {context['user_data_summary']['symptoms_count']} reports
        - Medications: {context['user_data_summary']['medications_count']} entries
        - Data quality: {context['user_data_summary']['data_quality_score']}
        
        Please provide:
        1. Trend identification
        2. Pattern analysis
        3. Predictive insights
        4. Trend-based recommendations
        """
    
    def _correlation_analysis_template(self, context: Dict[str, Any]) -> str:
        """Template for correlation analysis reasoning"""
        return f"""
        Analyze correlations between health factors:
        
        Available Data:
        - Vitals: {context['recent_vitals']}
        - Symptoms: {context['recent_symptoms']}
        - Medications: {context['current_medications']}
        - Nutrition: {context['recent_nutrition']}
        
        Please provide:
        1. Correlation analysis
        2. Causal relationships
        3. Factor interactions
        4. Intervention opportunities
        """
    
    def _risk_assessment_template(self, context: Dict[str, Any]) -> str:
        """Template for risk assessment reasoning"""
        return f"""
        Assess health risks:
        
        Risk Factors: {context['knowledge_context']['risk_factors']}
        Current Medications: {context['current_medications']}
        Recent Symptoms: {context['recent_symptoms']}
        Vitals: {context['recent_vitals']}
        
        Please provide:
        1. Risk factor analysis
        2. Risk level assessment
        3. Mitigation strategies
        4. Monitoring recommendations
        """
    
    def _medication_review_template(self, context: Dict[str, Any]) -> str:
        """Template for medication review reasoning"""
        return f"""
        Review medication safety and effectiveness:
        
        Current Medications: {context['current_medications']}
        Drug Interactions: {len(context['knowledge_context']['drug_interactions'])} found
        Recent Symptoms: {context['recent_symptoms']}
        Vitals: {context['recent_vitals']}
        
        Please provide:
        1. Medication safety assessment
        2. Interaction analysis
        3. Effectiveness evaluation
        4. Optimization recommendations
        """
    
    # Helper methods
    def _extract_recent_symptoms(self, symptoms: List[Dict[str, Any]]) -> List[str]:
        """Extract recent symptoms from user data"""
        recent_symptoms = []
        for symptom in symptoms[-5:]:  # Last 5 symptoms
            if isinstance(symptom, dict):
                name = symptom.get("name", "")
                if name:
                    recent_symptoms.append(name)
        return recent_symptoms
    
    def _extract_medication_names(self, medications: List[Dict[str, Any]]) -> List[str]:
        """Extract medication names from user data"""
        med_names = []
        for med in medications:
            if isinstance(med, dict):
                name = med.get("name", "")
                if name:
                    med_names.append(name)
        return med_names
    
    def _extract_recent_vitals(self, vitals: Dict[str, Any]) -> Dict[str, Any]:
        """Extract recent vital signs"""
        recent_vitals = {}
        if isinstance(vitals, dict):
            for vital_type, data in vitals.items():
                if isinstance(data, list) and data:
                    recent_vitals[vital_type] = data[-1]  # Most recent
        return recent_vitals
    
    def _extract_recent_nutrition(self, nutrition: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract recent nutrition data"""
        return nutrition[-3:] if nutrition else []  # Last 3 meals
    
    def _analyze_data_for_insights(self, user_data: Dict[str, Any], knowledge_context: Dict[str, Any]) -> List[Insight]:
        """Analyze user data to generate additional insights"""
        insights = []
        
        # Analyze vitals for insights
        vitals = user_data.get("vitals", {})
        if vitals:
            # Add vital-specific insights here
            pass
        
        # Analyze symptoms for patterns
        symptoms = user_data.get("symptoms", [])
        if len(symptoms) > 0:
            insights.append(Insight(
                type=InsightType.SYMPTOM_ANALYSIS,
                title="Symptom Tracking Active",
                description=f"User has reported {len(symptoms)} symptoms recently",
                confidence=ConfidenceLevel.MEDIUM,
                actionable=True
            ))
        
        return insights
    
    def _analyze_data_for_recommendations(self, user_data: Dict[str, Any], knowledge_context: Dict[str, Any]) -> List[Recommendation]:
        """Analyze user data to generate additional recommendations"""
        recommendations = []
        
        # Data quality recommendations
        data_quality = user_data.get("summary", {}).get("data_quality_score", 0.0)
        if data_quality < 0.5:
            recommendations.append(Recommendation(
                title="Improve Data Quality",
                description="Consider logging more health data for better insights",
                category="data_quality",
                priority="medium"
            ))
        
        return recommendations
    
    def _identify_trends(self, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify trends in user data"""
        trends = []
        # Add trend identification logic here
        return trends
    
    def _identify_anomalies(self, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify anomalies in user data"""
        anomalies = []
        # Add anomaly detection logic here
        return anomalies
    
    def _generate_fallback_reasoning(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback reasoning when AI service is unavailable"""
        return {
            "reasoning": f"Analysis based on available data. Query: {context['query']}",
            "insights": [],
            "recommendations": [],
            "confidence": "low"
        }
    
    def _generate_fallback_result(self, query: str, reasoning_type: ReasoningType) -> Dict[str, Any]:
        """Generate fallback result when reasoning fails"""
        return {
            "reasoning": f"Unable to complete {reasoning_type.value} analysis for: {query}",
            "insights": [],
            "recommendations": [],
            "evidence": {},
            "confidence": "uncertain",
            "data_sources": []
        }
