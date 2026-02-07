"""
Sample Data Generator for Knowledge Graph Service.

This module generates sample medical entities and relationships for testing
and demonstration purposes.
"""

import asyncio
import logging
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from apps.knowledge_graph.models.knowledge_models import (
    EntityType, RelationshipType, ConfidenceLevel, EvidenceLevel, OntologySource,
    MedicalEntityCreate, RelationshipCreate
)
from apps.knowledge_graph.services.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)


class SampleDataGenerator:
    """Generates sample medical data for the knowledge graph."""
    
    def __init__(self, knowledge_graph_service: KnowledgeGraphService):
        self.service = knowledge_graph_service
        
        # Sample medical data
        self.conditions = [
            {"name": "Diabetes Mellitus Type 2", "type": EntityType.CONDITION, "description": "A chronic metabolic disorder characterized by high blood sugar"},
            {"name": "Hypertension", "type": EntityType.CONDITION, "description": "High blood pressure"},
            {"name": "Asthma", "type": EntityType.CONDITION, "description": "Chronic inflammatory disease of the airways"},
            {"name": "Coronary Artery Disease", "type": EntityType.CONDITION, "description": "Narrowing of coronary arteries due to plaque buildup"},
            {"name": "Depression", "type": EntityType.CONDITION, "description": "Mental health disorder characterized by persistent sadness"},
            {"name": "Osteoarthritis", "type": EntityType.CONDITION, "description": "Degenerative joint disease"},
            {"name": "Chronic Kidney Disease", "type": EntityType.CONDITION, "description": "Progressive loss of kidney function"},
            {"name": "COPD", "type": EntityType.CONDITION, "description": "Chronic obstructive pulmonary disease"},
            {"name": "Heart Failure", "type": EntityType.CONDITION, "description": "Heart's inability to pump blood effectively"},
            {"name": "Stroke", "type": EntityType.CONDITION, "description": "Brain damage due to interrupted blood supply"}
        ]
        
        self.symptoms = [
            {"name": "Chest Pain", "type": EntityType.SYMPTOM, "description": "Pain or discomfort in the chest area"},
            {"name": "Shortness of Breath", "type": EntityType.SYMPTOM, "description": "Difficulty breathing or feeling breathless"},
            {"name": "Fatigue", "type": EntityType.SYMPTOM, "description": "Extreme tiredness or lack of energy"},
            {"name": "Headache", "type": EntityType.SYMPTOM, "description": "Pain in the head or upper neck"},
            {"name": "Nausea", "type": EntityType.SYMPTOM, "description": "Feeling of sickness with urge to vomit"},
            {"name": "Dizziness", "type": EntityType.SYMPTOM, "description": "Sensation of spinning or lightheadedness"},
            {"name": "Joint Pain", "type": EntityType.SYMPTOM, "description": "Pain in joints or surrounding tissues"},
            {"name": "Swelling", "type": EntityType.SYMPTOM, "description": "Enlargement of body parts due to fluid accumulation"},
            {"name": "Fever", "type": EntityType.SYMPTOM, "description": "Elevated body temperature above normal"},
            {"name": "Cough", "type": EntityType.SYMPTOM, "description": "Sudden expulsion of air from the lungs"}
        ]
        
        self.medications = [
            {"name": "Metformin", "type": EntityType.MEDICATION, "description": "Oral diabetes medication"},
            {"name": "Lisinopril", "type": EntityType.MEDICATION, "description": "ACE inhibitor for hypertension"},
            {"name": "Atorvastatin", "type": EntityType.MEDICATION, "description": "Statin medication for cholesterol"},
            {"name": "Aspirin", "type": EntityType.MEDICATION, "description": "Blood thinner and pain reliever"},
            {"name": "Ibuprofen", "type": EntityType.MEDICATION, "description": "Non-steroidal anti-inflammatory drug"},
            {"name": "Omeprazole", "type": EntityType.MEDICATION, "description": "Proton pump inhibitor for acid reflux"},
            {"name": "Sertraline", "type": EntityType.MEDICATION, "description": "Selective serotonin reuptake inhibitor"},
            {"name": "Amlodipine", "type": EntityType.MEDICATION, "description": "Calcium channel blocker for hypertension"},
            {"name": "Losartan", "type": EntityType.MEDICATION, "description": "Angiotensin receptor blocker"},
            {"name": "Simvastatin", "type": EntityType.MEDICATION, "description": "Statin medication for cholesterol"}
        ]
        
        self.treatments = [
            {"name": "Lifestyle Modification", "type": EntityType.TREATMENT, "description": "Changes in diet, exercise, and habits"},
            {"name": "Physical Therapy", "type": EntityType.TREATMENT, "description": "Therapeutic exercises and techniques"},
            {"name": "Surgery", "type": EntityType.TREATMENT, "description": "Surgical intervention for medical conditions"},
            {"name": "Radiation Therapy", "type": EntityType.TREATMENT, "description": "Use of radiation to treat cancer"},
            {"name": "Chemotherapy", "type": EntityType.TREATMENT, "description": "Use of drugs to treat cancer"},
            {"name": "Psychotherapy", "type": EntityType.TREATMENT, "description": "Talk therapy for mental health conditions"},
            {"name": "Cardiac Rehabilitation", "type": EntityType.TREATMENT, "description": "Program to improve heart health"},
            {"name": "Pulmonary Rehabilitation", "type": EntityType.TREATMENT, "description": "Program to improve lung function"},
            {"name": "Dialysis", "type": EntityType.TREATMENT, "description": "Treatment for kidney failure"},
            {"name": "Immunotherapy", "type": EntityType.TREATMENT, "description": "Treatment that uses the immune system"}
        ]
        
        self.procedures = [
            {"name": "Blood Test", "type": EntityType.PROCEDURE, "description": "Laboratory analysis of blood samples"},
            {"name": "X-Ray", "type": EntityType.PROCEDURE, "description": "Radiographic imaging procedure"},
            {"name": "MRI Scan", "type": EntityType.PROCEDURE, "description": "Magnetic resonance imaging"},
            {"name": "CT Scan", "type": EntityType.PROCEDURE, "description": "Computed tomography imaging"},
            {"name": "Echocardiogram", "type": EntityType.PROCEDURE, "description": "Ultrasound of the heart"},
            {"name": "Endoscopy", "type": EntityType.PROCEDURE, "description": "Internal examination using a camera"},
            {"name": "Biopsy", "type": EntityType.PROCEDURE, "description": "Removal of tissue for examination"},
            {"name": "Colonoscopy", "type": EntityType.PROCEDURE, "description": "Examination of the colon"},
            {"name": "Mammogram", "type": EntityType.PROCEDURE, "description": "Breast cancer screening"},
            {"name": "Stress Test", "type": EntityType.PROCEDURE, "description": "Cardiac stress testing"}
        ]
        
        self.lab_tests = [
            {"name": "Complete Blood Count", "type": EntityType.LAB_TEST, "description": "Comprehensive blood cell analysis"},
            {"name": "Comprehensive Metabolic Panel", "type": EntityType.LAB_TEST, "description": "Blood chemistry analysis"},
            {"name": "Lipid Panel", "type": EntityType.LAB_TEST, "description": "Cholesterol and triglyceride levels"},
            {"name": "Hemoglobin A1C", "type": EntityType.LAB_TEST, "description": "Long-term blood sugar control"},
            {"name": "Thyroid Function Tests", "type": EntityType.LAB_TEST, "description": "Thyroid hormone levels"},
            {"name": "Urinalysis", "type": EntityType.LAB_TEST, "description": "Analysis of urine composition"},
            {"name": "C-Reactive Protein", "type": EntityType.LAB_TEST, "description": "Inflammation marker"},
            {"name": "Troponin", "type": EntityType.LAB_TEST, "description": "Heart damage marker"},
            {"name": "PSA Test", "type": EntityType.LAB_TEST, "description": "Prostate-specific antigen"},
            {"name": "Glucose Test", "type": EntityType.LAB_TEST, "description": "Blood sugar measurement"}
        ]
        
        self.vital_signs = [
            {"name": "Blood Pressure", "type": EntityType.VITAL_SIGN, "description": "Systolic and diastolic pressure"},
            {"name": "Heart Rate", "type": EntityType.VITAL_SIGN, "description": "Pulse rate measurement"},
            {"name": "Temperature", "type": EntityType.VITAL_SIGN, "description": "Body temperature"},
            {"name": "Respiratory Rate", "type": EntityType.VITAL_SIGN, "description": "Breathing rate"},
            {"name": "Oxygen Saturation", "type": EntityType.VITAL_SIGN, "description": "Blood oxygen level"},
            {"name": "Weight", "type": EntityType.VITAL_SIGN, "description": "Body weight measurement"},
            {"name": "Height", "type": EntityType.VITAL_SIGN, "description": "Body height measurement"},
            {"name": "BMI", "type": EntityType.VITAL_SIGN, "description": "Body mass index"},
            {"name": "Pain Scale", "type": EntityType.VITAL_SIGN, "description": "Subjective pain assessment"},
            {"name": "Blood Glucose", "type": EntityType.VITAL_SIGN, "description": "Blood sugar level"}
        ]
        
        self.risk_factors = [
            {"name": "Smoking", "type": EntityType.RISK_FACTOR, "description": "Tobacco use risk factor"},
            {"name": "Obesity", "type": EntityType.RISK_FACTOR, "description": "Excess body weight"},
            {"name": "Family History", "type": EntityType.RISK_FACTOR, "description": "Genetic predisposition"},
            {"name": "Age", "type": EntityType.RISK_FACTOR, "description": "Advanced age risk factor"},
            {"name": "Sedentary Lifestyle", "type": EntityType.RISK_FACTOR, "description": "Lack of physical activity"},
            {"name": "Poor Diet", "type": EntityType.RISK_FACTOR, "description": "Unhealthy eating habits"},
            {"name": "Alcohol Use", "type": EntityType.RISK_FACTOR, "description": "Excessive alcohol consumption"},
            {"name": "Stress", "type": EntityType.RISK_FACTOR, "description": "Chronic stress exposure"},
            {"name": "Environmental Exposure", "type": EntityType.RISK_FACTOR, "description": "Toxic substance exposure"},
            {"name": "Previous Medical History", "type": EntityType.RISK_FACTOR, "description": "Prior medical conditions"}
        ]
    
    async def generate_sample_entities(self) -> Dict[str, Any]:
        """Generate sample medical entities."""
        logger.info("Generating sample medical entities...")
        
        stats = {
            "entities_created": 0,
            "relationships_created": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }
        
        all_entities = (
            self.conditions + self.symptoms + self.medications + 
            self.treatments + self.procedures + self.lab_tests + 
            self.vital_signs + self.risk_factors
        )
        
        created_entities = []
        
        # Create entities
        for entity_data in all_entities:
            try:
                entity = MedicalEntityCreate(
                    name=entity_data["name"].replace(" ", "_").upper(),
                    display_name=entity_data["name"],
                    entity_type=entity_data["type"],
                    description=entity_data["description"],
                    ontology_source=OntologySource.CUSTOM,
                    confidence_level=ConfidenceLevel.MEDIUM,
                    evidence_level=EvidenceLevel.LEVEL_C,
                    metadata={
                        "source": "sample_data_generator",
                        "category": entity_data["type"].value
                    }
                )
                
                created_entity = await self.service.create_medical_entity(entity)
                created_entities.append(created_entity)
                stats["entities_created"] += 1
                
                if stats["entities_created"] % 10 == 0:
                    logger.info(f"Created {stats['entities_created']} sample entities")
                    
            except Exception as e:
                logger.error(f"Error creating sample entity {entity_data['name']}: {e}")
                stats["errors"] += 1
        
        # Create relationships
        await self._create_sample_relationships(created_entities, stats)
        
        stats["end_time"] = datetime.utcnow()
        logger.info(f"Sample data generation completed: {stats}")
        return stats
    
    async def _create_sample_relationships(self, entities: List[Any], stats: Dict[str, Any]):
        """Create sample relationships between entities."""
        logger.info("Creating sample relationships...")
        
        # Condition-Symptom relationships
        condition_symptom_mappings = {
            "Diabetes Mellitus Type 2": ["Fatigue"],
            "Hypertension": ["Headache", "Chest Pain"],
            "Asthma": ["Shortness of Breath", "Cough", "Chest Pain"],
            "Coronary Artery Disease": ["Chest Pain", "Shortness of Breath", "Fatigue"],
            "Depression": ["Fatigue"],
            "Osteoarthritis": ["Joint Pain"],
            "Chronic Kidney Disease": ["Fatigue", "Nausea"],
            "COPD": ["Shortness of Breath", "Cough", "Fatigue"],
            "Heart Failure": ["Shortness of Breath", "Fatigue"],
            "Stroke": ["Headache", "Dizziness"]
        }
        
        # Condition-Treatment relationships
        condition_treatment_mappings = {
            "Diabetes Mellitus Type 2": ["Lifestyle Modification", "Metformin"],
            "Hypertension": ["Lifestyle Modification", "Lisinopril", "Amlodipine"],
            "Asthma": ["Physical Therapy"],
            "Coronary Artery Disease": ["Lifestyle Modification", "Aspirin", "Atorvastatin"],
            "Depression": ["Psychotherapy", "Sertraline"],
            "Osteoarthritis": ["Physical Therapy", "Ibuprofen"],
            "Chronic Kidney Disease": ["Dialysis"],
            "COPD": ["Pulmonary Rehabilitation"],
            "Heart Failure": ["Cardiac Rehabilitation"],
            "Stroke": ["Physical Therapy"]
        }
        
        # Condition-Risk Factor relationships
        condition_risk_mappings = {
            "Diabetes Mellitus Type 2": ["Obesity", "Family History", "Sedentary Lifestyle"],
            "Hypertension": ["Age", "Obesity", "Poor Diet"],
            "Asthma": ["Family History"],
            "Coronary Artery Disease": ["Smoking", "Obesity", "Family History"],
            "Depression": ["Family History"],
            "Osteoarthritis": ["Age", "Obesity"],
            "Chronic Kidney Disease": ["Diabetes Mellitus Type 2", "Hypertension"],
            "COPD": ["Smoking"],
            "Heart Failure": ["Coronary Artery Disease", "Hypertension"],
            "Stroke": ["Hypertension", "Smoking", "Age"]
        }
        
        # Create relationships
        for condition_name, symptoms in condition_symptom_mappings.items():
            await self._create_relationships_for_condition(
                condition_name, symptoms, RelationshipType.MANIFESTS_AS, entities, stats
            )
        
        for condition_name, treatments in condition_treatment_mappings.items():
            await self._create_relationships_for_condition(
                condition_name, treatments, RelationshipType.TREATED_BY, entities, stats
            )
        
        for condition_name, risk_factors in condition_risk_mappings.items():
            await self._create_relationships_for_condition(
                condition_name, risk_factors, RelationshipType.RISK_FACTOR_FOR, entities, stats
            )
        
        # Create medication interactions
        medication_interactions = [
            ("Metformin", "Lisinopril", "May increase risk of lactic acidosis"),
            ("Aspirin", "Ibuprofen", "May reduce aspirin's effectiveness"),
            ("Atorvastatin", "Simvastatin", "Should not be taken together"),
            ("Lisinopril", "Amlodipine", "May cause excessive blood pressure reduction"),
            ("Sertraline", "Aspirin", "May increase bleeding risk")
        ]
        
        for med1, med2, description in medication_interactions:
            await self._create_medication_interaction(med1, med2, description, entities, stats)
    
    async def _create_relationships_for_condition(
        self, 
        condition_name: str, 
        related_items: List[str], 
        relationship_type: RelationshipType, 
        entities: List[Any], 
        stats: Dict[str, Any]
    ):
        """Create relationships for a specific condition."""
        try:
            condition_entity = next(
                (e for e in entities if e.display_name == condition_name), 
                None
            )
            
            if condition_entity:
                for item_name in related_items:
                    related_entity = next(
                        (e for e in entities if e.display_name == item_name), 
                        None
                    )
                    
                    if related_entity:
                        relationship = RelationshipCreate(
                            source_entity_id=condition_entity.id,
                            target_entity_id=related_entity.id,
                            relationship_type=relationship_type,
                            confidence=ConfidenceLevel.MEDIUM,
                            evidence_level=EvidenceLevel.LEVEL_C,
                            metadata={
                                "source": "sample_data_generator",
                                "description": f"Sample relationship between {condition_name} and {item_name}"
                            }
                        )
                        
                        await self.service.create_relationship(relationship)
                        stats["relationships_created"] += 1
                        
        except Exception as e:
            logger.error(f"Error creating relationships for {condition_name}: {e}")
            stats["errors"] += 1
    
    async def _create_medication_interaction(
        self, 
        med1: str, 
        med2: str, 
        description: str, 
        entities: List[Any], 
        stats: Dict[str, Any]
    ):
        """Create medication interaction relationship."""
        try:
            med1_entity = next(
                (e for e in entities if e.display_name == med1), 
                None
            )
            med2_entity = next(
                (e for e in entities if e.display_name == med2), 
                None
            )
            
            if med1_entity and med2_entity:
                relationship = RelationshipCreate(
                    source_entity_id=med1_entity.id,
                    target_entity_id=med2_entity.id,
                    relationship_type=RelationshipType.INTERACTS_WITH,
                    confidence=ConfidenceLevel.MEDIUM,
                    evidence_level=EvidenceLevel.LEVEL_C,
                    metadata={
                        "source": "sample_data_generator",
                        "description": description,
                        "interaction_type": "drug_interaction"
                    }
                )
                
                await self.service.create_relationship(relationship)
                stats["relationships_created"] += 1
                
        except Exception as e:
            logger.error(f"Error creating medication interaction {med1}-{med2}: {e}")
            stats["errors"] += 1
    
    async def generate_disease_specific_data(self) -> Dict[str, Any]:
        """Generate disease-specific knowledge graphs."""
        logger.info("Generating disease-specific knowledge graphs...")
        
        stats = {
            "diseases_created": 0,
            "relationships_created": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }
        
        # Diabetes knowledge graph
        diabetes_data = {
            "condition": "Diabetes Mellitus Type 2",
            "symptoms": ["Increased Thirst", "Frequent Urination", "Fatigue", "Blurred Vision", "Slow Healing"],
            "complications": ["Diabetic Retinopathy", "Diabetic Nephropathy", "Diabetic Neuropathy", "Cardiovascular Disease"],
            "treatments": ["Metformin", "Insulin", "Lifestyle Modification", "Blood Sugar Monitoring"],
            "risk_factors": ["Obesity", "Family History", "Age", "Sedentary Lifestyle", "Poor Diet"],
            "lab_tests": ["Hemoglobin A1C", "Fasting Blood Glucose", "Oral Glucose Tolerance Test", "Lipid Panel"],
            "vital_signs": ["Blood Glucose", "Blood Pressure", "Weight", "BMI"]
        }
        
        await self._create_disease_knowledge_graph(diabetes_data, stats)
        
        # Hypertension knowledge graph
        hypertension_data = {
            "condition": "Hypertension",
            "symptoms": ["Headache", "Chest Pain", "Shortness of Breath", "Dizziness", "Vision Problems"],
            "complications": ["Heart Attack", "Stroke", "Kidney Disease", "Eye Damage"],
            "treatments": ["Lisinopril", "Amlodipine", "Lifestyle Modification", "Salt Restriction"],
            "risk_factors": ["Age", "Obesity", "Family History", "Smoking", "Stress"],
            "lab_tests": ["Complete Blood Count", "Comprehensive Metabolic Panel", "Lipid Panel", "Urinalysis"],
            "vital_signs": ["Blood Pressure", "Heart Rate", "Weight", "BMI"]
        }
        
        await self._create_disease_knowledge_graph(hypertension_data, stats)
        
        stats["end_time"] = datetime.utcnow()
        logger.info(f"Disease-specific data generation completed: {stats}")
        return stats
    
    async def _create_disease_knowledge_graph(self, disease_data: Dict[str, Any], stats: Dict[str, Any]):
        """Create a comprehensive knowledge graph for a specific disease."""
        try:
            # Create main condition entity
            condition_entity = MedicalEntityCreate(
                name=disease_data["condition"].replace(" ", "_").upper(),
                display_name=disease_data["condition"],
                entity_type=EntityType.CONDITION,
                description=f"Comprehensive knowledge graph for {disease_data['condition']}",
                ontology_source=OntologySource.CUSTOM,
                confidence_level=ConfidenceLevel.HIGH,
                evidence_level=EvidenceLevel.LEVEL_B,
                metadata={
                    "source": "disease_knowledge_graph",
                    "disease_type": "chronic_condition"
                }
            )
            
            created_condition = await self.service.create_medical_entity(condition_entity)
            stats["diseases_created"] += 1
            
            # Create related entities and relationships
            for category, items in disease_data.items():
                if category != "condition":
                    for item in items:
                        # Create entity if it doesn't exist
                        entity = MedicalEntityCreate(
                            name=item.replace(" ", "_").upper(),
                            display_name=item,
                            entity_type=self._get_entity_type_for_category(category),
                            description=f"{item} related to {disease_data['condition']}",
                            ontology_source=OntologySource.CUSTOM,
                            confidence_level=ConfidenceLevel.MEDIUM,
                            evidence_level=EvidenceLevel.LEVEL_C,
                            metadata={
                                "source": "disease_knowledge_graph",
                                "disease": disease_data["condition"],
                                "category": category
                            }
                        )
                        
                        created_entity = await self.service.create_medical_entity(entity)
                        
                        # Create relationship
                        relationship_type = self._get_relationship_type_for_category(category)
                        relationship = RelationshipCreate(
                            source_entity_id=created_condition.id,
                            target_entity_id=created_entity.id,
                            relationship_type=relationship_type,
                            confidence=ConfidenceLevel.MEDIUM,
                            evidence_level=EvidenceLevel.LEVEL_C,
                            metadata={
                                "source": "disease_knowledge_graph",
                                "description": f"Relationship between {disease_data['condition']} and {item}"
                            }
                        )
                        
                        await self.service.create_relationship(relationship)
                        stats["relationships_created"] += 1
                        
        except Exception as e:
            logger.error(f"Error creating disease knowledge graph for {disease_data.get('condition', 'Unknown')}: {e}")
            stats["errors"] += 1
    
    def _get_entity_type_for_category(self, category: str) -> EntityType:
        """Get entity type for a given category."""
        category_mapping = {
            "symptoms": EntityType.SYMPTOM,
            "complications": EntityType.CONDITION,
            "treatments": EntityType.TREATMENT,
            "risk_factors": EntityType.RISK_FACTOR,
            "lab_tests": EntityType.LAB_TEST,
            "vital_signs": EntityType.VITAL_SIGN
        }
        return category_mapping.get(category, EntityType.CONDITION)
    
    def _get_relationship_type_for_category(self, category: str) -> RelationshipType:
        """Get relationship type for a given category."""
        relationship_mapping = {
            "symptoms": RelationshipType.MANIFESTS_AS,
            "complications": RelationshipType.COMPLICATES,
            "treatments": RelationshipType.TREATED_BY,
            "risk_factors": RelationshipType.RISK_FACTOR_FOR,
            "lab_tests": RelationshipType.MONITORED_BY,
            "vital_signs": RelationshipType.MONITORED_BY
        }
        return relationship_mapping.get(category, RelationshipType.ASSOCIATED_WITH) 