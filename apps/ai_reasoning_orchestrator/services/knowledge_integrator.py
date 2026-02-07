"""
Knowledge Integrator Service
Integrates medical knowledge from knowledge graph and external sources for AI reasoning.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from common.utils.logging import get_logger

logger = get_logger(__name__)

class KnowledgeIntegrator:
    """Integrates medical knowledge for AI reasoning"""
    
    def __init__(self):
        self.logger = logger
        self.knowledge_graph_url = "http://knowledge-graph-service:8000"
        self.ai_insights_url = "http://ai-insights-service:8000"
    
    async def get_relevant_knowledge(
        self, 
        query: str, 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get relevant medical knowledge for reasoning.
        
        Args:
            query: Health query or question
            user_context: User's health data context
            
        Returns:
            Relevant medical knowledge
        """
        self.logger.info(f"🔍 Retrieving relevant knowledge for query: {query[:100]}...")
        
        # Collect knowledge from multiple sources in parallel
        tasks = [
            self._get_knowledge_graph_data(query, user_context),
            self._get_medical_literature(query, user_context),
            self._get_drug_interactions(user_context),
            self._get_clinical_guidelines(query, user_context)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine knowledge from all sources
        knowledge_context = {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "knowledge_graph": {},
            "medical_literature": [],
            "drug_interactions": [],
            "clinical_guidelines": [],
            "risk_factors": [],
            "evidence_level": "moderate"
        }
        
        # Process knowledge graph results
        if not isinstance(results[0], Exception) and results[0]:
            knowledge_context["knowledge_graph"] = results[0]
        
        # Process medical literature results
        if not isinstance(results[1], Exception) and results[1]:
            knowledge_context["medical_literature"] = results[1].get("papers", [])
        
        # Process drug interactions
        if not isinstance(results[2], Exception) and results[2]:
            knowledge_context["drug_interactions"] = results[2].get("interactions", [])
        
        # Process clinical guidelines
        if not isinstance(results[3], Exception) and results[3]:
            knowledge_context["clinical_guidelines"] = results[3].get("guidelines", [])
        
        # Extract risk factors from user context
        knowledge_context["risk_factors"] = self._extract_risk_factors(user_context)
        
        # Determine evidence level
        knowledge_context["evidence_level"] = self._determine_evidence_level(knowledge_context)
        
        self.logger.info(f"✅ Knowledge integration completed")
        return knowledge_context
    
    async def _get_knowledge_graph_data(
        self, 
        query: str, 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get relevant data from knowledge graph"""
        try:
            # Extract key medical entities from query and user context
            entities = self._extract_medical_entities(query, user_context)
            
            url = f"{self.knowledge_graph_url}/api/v1/knowledge-graph/search"
            payload = {
                "query": query,
                "entities": entities,
                "limit": 20
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to fetch knowledge graph data: {response.status_code}")
                    return {}
        except Exception as e:
            self.logger.error(f"Error fetching knowledge graph data: {e}")
            return {}
    
    async def _get_medical_literature(
        self, 
        query: str, 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get relevant medical literature"""
        try:
            url = f"{self.ai_insights_url}/api/v1/ai-insights/search-medical-entities"
            payload = {
                "query": query,
                "limit": 10
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to fetch medical literature: {response.status_code}")
                    return {"papers": []}
        except Exception as e:
            self.logger.error(f"Error fetching medical literature: {e}")
            return {"papers": []}
    
    async def _get_drug_interactions(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get drug interactions for user's medications"""
        try:
            medications = user_context.get("medications", [])
            if not medications:
                return {"interactions": []}
            
            # Extract medication names
            med_names = []
            for med in medications:
                if isinstance(med, dict):
                    med_names.append(med.get("name", ""))
                elif isinstance(med, str):
                    med_names.append(med)
            
            if not med_names:
                return {"interactions": []}
            
            url = f"{self.knowledge_graph_url}/api/v1/knowledge-graph/drug-interactions"
            payload = {
                "medications": med_names,
                "include_supplements": True,
                "include_food": True
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to fetch drug interactions: {response.status_code}")
                    return {"interactions": []}
        except Exception as e:
            self.logger.error(f"Error fetching drug interactions: {e}")
            return {"interactions": []}
    
    async def _get_clinical_guidelines(
        self, 
        query: str, 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get relevant clinical guidelines"""
        try:
            # Extract conditions from user context
            conditions = self._extract_conditions(user_context)
            
            url = f"{self.knowledge_graph_url}/api/v1/knowledge-graph/clinical-guidelines"
            payload = {
                "query": query,
                "conditions": conditions,
                "limit": 10
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Failed to fetch clinical guidelines: {response.status_code}")
                    return {"guidelines": []}
        except Exception as e:
            self.logger.error(f"Error fetching clinical guidelines: {e}")
            return {"guidelines": []}
    
    def _extract_medical_entities(self, query: str, user_context: Dict[str, Any]) -> List[str]:
        """Extract medical entities from query and user context"""
        entities = []
        
        # Extract from query (simplified)
        query_lower = query.lower()
        common_symptoms = [
            "headache", "fatigue", "dizziness", "nausea", "pain", 
            "fever", "cough", "shortness of breath", "chest pain"
        ]
        
        for symptom in common_symptoms:
            if symptom in query_lower:
                entities.append(symptom)
        
        # Extract from user context
        symptoms = user_context.get("symptoms", [])
        for symptom in symptoms:
            if isinstance(symptom, dict):
                entities.append(symptom.get("name", ""))
            elif isinstance(symptom, str):
                entities.append(symptom)
        
        medications = user_context.get("medications", [])
        for med in medications:
            if isinstance(med, dict):
                entities.append(med.get("name", ""))
            elif isinstance(med, str):
                entities.append(med)
        
        return list(set(entities))  # Remove duplicates
    
    def _extract_conditions(self, user_context: Dict[str, Any]) -> List[str]:
        """Extract medical conditions from user context"""
        conditions = []
        
        # Extract from medical records
        medical_records = user_context.get("medical_records", [])
        for record in medical_records:
            if isinstance(record, dict):
                diagnosis = record.get("diagnosis", "")
                if diagnosis:
                    conditions.append(diagnosis)
        
        # Extract from lab results
        lab_results = user_context.get("lab_results", [])
        for lab in lab_results:
            if isinstance(lab, dict):
                condition = lab.get("condition", "")
                if condition:
                    conditions.append(condition)
        
        return list(set(conditions))
    
    def _extract_risk_factors(self, user_context: Dict[str, Any]) -> List[str]:
        """Extract risk factors from user context"""
        risk_factors = []
        
        # Analyze vitals for risk factors
        vitals = user_context.get("vitals", {})
        if vitals:
            # Blood pressure risk
            bp_data = vitals.get("blood_pressure", [])
            if bp_data:
                for bp in bp_data:
                    if isinstance(bp, dict):
                        systolic = bp.get("systolic", 0)
                        diastolic = bp.get("diastolic", 0)
                        if systolic > 140 or diastolic > 90:
                            risk_factors.append("hypertension")
                        elif systolic > 120 or diastolic > 80:
                            risk_factors.append("prehypertension")
            
            # Blood glucose risk
            glucose_data = vitals.get("blood_glucose", [])
            if glucose_data:
                for glucose in glucose_data:
                    if isinstance(glucose, dict):
                        value = glucose.get("value", 0)
                        if value > 126:
                            risk_factors.append("diabetes")
                        elif value > 100:
                            risk_factors.append("prediabetes")
        
        # Analyze symptoms for risk factors
        symptoms = user_context.get("symptoms", [])
        for symptom in symptoms:
            if isinstance(symptom, dict):
                name = symptom.get("name", "").lower()
                if "chest pain" in name:
                    risk_factors.append("cardiovascular_risk")
                elif "shortness of breath" in name:
                    risk_factors.append("respiratory_risk")
        
        return list(set(risk_factors))
    
    def _determine_evidence_level(self, knowledge_context: Dict[str, Any]) -> str:
        """Determine the level of evidence available"""
        evidence_score = 0
        
        # Knowledge graph data
        if knowledge_context.get("knowledge_graph"):
            evidence_score += 2
        
        # Medical literature
        if knowledge_context.get("medical_literature"):
            evidence_score += 3
        
        # Drug interactions
        if knowledge_context.get("drug_interactions"):
            evidence_score += 1
        
        # Clinical guidelines
        if knowledge_context.get("clinical_guidelines"):
            evidence_score += 2
        
        # Risk factors
        if knowledge_context.get("risk_factors"):
            evidence_score += 1
        
        # Determine level based on score
        if evidence_score >= 6:
            return "high"
        elif evidence_score >= 3:
            return "moderate"
        else:
            return "low"
