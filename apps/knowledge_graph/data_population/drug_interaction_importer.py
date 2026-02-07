"""
Drug Interaction Importer for Knowledge Graph Service.

This module imports drug interactions, side effects, and contraindications
from various medical databases and sources.
"""

import asyncio
import logging
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import httpx

from apps.knowledge_graph.models.knowledge_models import (
    EntityType, RelationshipType, ConfidenceLevel, EvidenceLevel, OntologySource,
    MedicalEntityCreate, RelationshipCreate
)
from apps.knowledge_graph.services.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)


class DrugInteractionImporter:
    """Imports drug interactions and related data."""
    
    def __init__(self, knowledge_graph_service: KnowledgeGraphService):
        self.service = knowledge_graph_service
        
        # Common drug interactions
        self.drug_interactions = [
            {
                "drug1": "Warfarin",
                "drug2": "Aspirin",
                "interaction": "Increased bleeding risk",
                "severity": "Major",
                "description": "Combination increases risk of bleeding complications"
            },
            {
                "drug1": "Warfarin",
                "drug2": "Ibuprofen",
                "interaction": "Increased bleeding risk",
                "severity": "Major",
                "description": "NSAIDs can increase warfarin's anticoagulant effect"
            },
            {
                "drug1": "Metformin",
                "drug2": "Furosemide",
                "interaction": "Increased metformin levels",
                "severity": "Moderate",
                "description": "Furosemide may increase metformin concentration"
            },
            {
                "drug1": "Lisinopril",
                "drug2": "Ibuprofen",
                "interaction": "Reduced blood pressure control",
                "severity": "Moderate",
                "description": "NSAIDs may reduce ACE inhibitor effectiveness"
            },
            {
                "drug1": "Atorvastatin",
                "drug2": "Grapefruit Juice",
                "interaction": "Increased statin levels",
                "severity": "Major",
                "description": "Grapefruit juice inhibits statin metabolism"
            },
            {
                "drug1": "Sertraline",
                "drug2": "Aspirin",
                "interaction": "Increased bleeding risk",
                "severity": "Moderate",
                "description": "SSRIs may increase bleeding risk with antiplatelets"
            },
            {
                "drug1": "Omeprazole",
                "drug2": "Atorvastatin",
                "interaction": "Increased statin levels",
                "severity": "Minor",
                "description": "Proton pump inhibitors may increase statin absorption"
            },
            {
                "drug1": "Amlodipine",
                "drug2": "Simvastatin",
                "interaction": "Increased statin levels",
                "severity": "Moderate",
                "description": "Calcium channel blockers may increase statin levels"
            },
            {
                "drug1": "Losartan",
                "drug2": "Ibuprofen",
                "interaction": "Reduced blood pressure control",
                "severity": "Moderate",
                "description": "NSAIDs may reduce ARB effectiveness"
            },
            {
                "drug1": "Metformin",
                "drug2": "Alcohol",
                "interaction": "Increased lactic acidosis risk",
                "severity": "Major",
                "description": "Alcohol increases risk of lactic acidosis with metformin"
            }
        ]
        
        # Drug side effects
        self.drug_side_effects = [
            {
                "drug": "Metformin",
                "side_effects": ["Nausea", "Diarrhea", "Stomach upset", "Lactic acidosis"],
                "frequency": "Common"
            },
            {
                "drug": "Lisinopril",
                "side_effects": ["Dry cough", "Dizziness", "Headache", "High potassium"],
                "frequency": "Common"
            },
            {
                "drug": "Atorvastatin",
                "side_effects": ["Muscle pain", "Liver problems", "Headache", "Nausea"],
                "frequency": "Common"
            },
            {
                "drug": "Aspirin",
                "side_effects": ["Stomach upset", "Bleeding", "Ringing in ears", "Allergic reactions"],
                "frequency": "Common"
            },
            {
                "drug": "Ibuprofen",
                "side_effects": ["Stomach irritation", "Kidney problems", "High blood pressure", "Heart problems"],
                "frequency": "Common"
            },
            {
                "drug": "Omeprazole",
                "side_effects": ["Headache", "Diarrhea", "Stomach pain", "Vitamin B12 deficiency"],
                "frequency": "Common"
            },
            {
                "drug": "Sertraline",
                "side_effects": ["Nausea", "Insomnia", "Sexual dysfunction", "Weight changes"],
                "frequency": "Common"
            },
            {
                "drug": "Amlodipine",
                "side_effects": ["Swelling", "Dizziness", "Headache", "Flushing"],
                "frequency": "Common"
            },
            {
                "drug": "Losartan",
                "side_effects": ["Dizziness", "High potassium", "Chest pain", "Back pain"],
                "frequency": "Common"
            },
            {
                "drug": "Simvastatin",
                "side_effects": ["Muscle pain", "Liver problems", "Headache", "Nausea"],
                "frequency": "Common"
            }
        ]
        
        # Drug contraindications
        self.drug_contraindications = [
            {
                "drug": "Warfarin",
                "contraindications": ["Pregnancy", "Active bleeding", "Severe liver disease", "Recent surgery"],
                "severity": "Absolute"
            },
            {
                "drug": "Metformin",
                "contraindications": ["Severe kidney disease", "Metabolic acidosis", "Heart failure", "Liver disease"],
                "severity": "Absolute"
            },
            {
                "drug": "Lisinopril",
                "contraindications": ["Pregnancy", "Angioedema history", "Bilateral renal artery stenosis"],
                "severity": "Absolute"
            },
            {
                "drug": "Atorvastatin",
                "contraindications": ["Active liver disease", "Pregnancy", "Breastfeeding"],
                "severity": "Absolute"
            },
            {
                "drug": "Aspirin",
                "contraindications": ["Active bleeding", "Peptic ulcer", "Aspirin allergy", "Children with viral infections"],
                "severity": "Absolute"
            },
            {
                "drug": "Ibuprofen",
                "contraindications": ["Active bleeding", "Peptic ulcer", "Kidney disease", "Heart failure"],
                "severity": "Relative"
            },
            {
                "drug": "Omeprazole",
                "contraindications": ["Omeprazole allergy", "Pregnancy first trimester"],
                "severity": "Absolute"
            },
            {
                "drug": "Sertraline",
                "contraindications": ["MAOI use", "Sertraline allergy", "Severe liver disease"],
                "severity": "Absolute"
            },
            {
                "drug": "Amlodipine",
                "contraindications": ["Amlodipine allergy", "Severe aortic stenosis"],
                "severity": "Absolute"
            },
            {
                "drug": "Losartan",
                "contraindications": ["Pregnancy", "Losartan allergy", "Bilateral renal artery stenosis"],
                "severity": "Absolute"
            }
        ]
    
    async def import_drug_interactions(self) -> Dict[str, Any]:
        """Import drug interactions."""
        logger.info("Starting drug interaction import...")
        
        stats = {
            "interactions_imported": 0,
            "side_effects_imported": 0,
            "contraindications_imported": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }
        
        try:
            # Import drug interactions
            await self._import_drug_interactions(stats)
            
            # Import side effects
            await self._import_drug_side_effects(stats)
            
            # Import contraindications
            await self._import_drug_contraindications(stats)
            
        except Exception as e:
            logger.error(f"Error importing drug interactions: {e}")
            stats["errors"] += 1
            
        stats["end_time"] = datetime.utcnow()
        logger.info(f"Drug interaction import completed: {stats}")
        return stats
    
    async def _import_drug_interactions(self, stats: Dict[str, Any]):
        """Import drug interactions."""
        logger.info("Importing drug interactions...")
        
        for interaction in self.drug_interactions:
            try:
                # Create or get drug entities
                drug1_entity = await self._get_or_create_drug_entity(interaction["drug1"])
                drug2_entity = await self._get_or_create_drug_entity(interaction["drug2"])
                
                if drug1_entity and drug2_entity:
                    # Create interaction relationship
                    relationship = RelationshipCreate(
                        source_entity_id=drug1_entity.id,
                        target_entity_id=drug2_entity.id,
                        relationship_type=RelationshipType.INTERACTS_WITH,
                        confidence_level=ConfidenceLevel.HIGH,
                        evidence_level=EvidenceLevel.LEVEL_1,
                        metadata={
                            "interaction_type": "drug_drug_interaction",
                            "severity": interaction["severity"],
                            "description": interaction["description"],
                            "source": "drug_interaction_importer"
                        }
                    )
                    
                    await self.service.create_relationship(relationship)
                    stats["interactions_imported"] += 1
                    
                    if stats["interactions_imported"] % 10 == 0:
                        logger.info(f"Imported {stats['interactions_imported']} drug interactions")
                        
            except Exception as e:
                logger.error(f"Error importing drug interaction {interaction}: {e}")
                stats["errors"] += 1
    
    async def _import_drug_side_effects(self, stats: Dict[str, Any]):
        """Import drug side effects."""
        logger.info("Importing drug side effects...")
        
        for drug_effects in self.drug_side_effects:
            try:
                # Get or create drug entity
                drug_entity = await self._get_or_create_drug_entity(drug_effects["drug"])
                
                if drug_entity:
                    for side_effect in drug_effects["side_effects"]:
                        # Create or get side effect entity
                        side_effect_entity = await self._get_or_create_entity(
                            side_effect, EntityType.SIDE_EFFECT
                        )
                        
                        if side_effect_entity:
                            # Create side effect relationship
                            relationship = RelationshipCreate(
                                source_entity_id=drug_entity.id,
                                target_entity_id=side_effect_entity.id,
                                relationship_type=RelationshipType.HAS_SIDE_EFFECT,
                                confidence_level=ConfidenceLevel.HIGH,
                                evidence_level=EvidenceLevel.LEVEL_1,
                                metadata={
                                    "frequency": drug_effects["frequency"],
                                    "source": "drug_interaction_importer"
                                }
                            )
                            
                            await self.service.create_relationship(relationship)
                            stats["side_effects_imported"] += 1
                            
            except Exception as e:
                logger.error(f"Error importing side effects for {drug_effects['drug']}: {e}")
                stats["errors"] += 1
    
    async def _import_drug_contraindications(self, stats: Dict[str, Any]):
        """Import drug contraindications."""
        logger.info("Importing drug contraindications...")
        
        for drug_contraindications in self.drug_contraindications:
            try:
                # Get or create drug entity
                drug_entity = await self._get_or_create_drug_entity(drug_contraindications["drug"])
                
                if drug_entity:
                    for contraindication in drug_contraindications["contraindications"]:
                        # Create or get contraindication entity
                        contraindication_entity = await self._get_or_create_entity(
                            contraindication, EntityType.CONTRAINDICATION
                        )
                        
                        if contraindication_entity:
                            # Create contraindication relationship
                            relationship = RelationshipCreate(
                                source_entity_id=drug_entity.id,
                                target_entity_id=contraindication_entity.id,
                                relationship_type=RelationshipType.CONTRAINDICATED_IN,
                                confidence_level=ConfidenceLevel.HIGH,
                                evidence_level=EvidenceLevel.LEVEL_1,
                                metadata={
                                    "severity": drug_contraindications["severity"],
                                    "source": "drug_interaction_importer"
                                }
                            )
                            
                            await self.service.create_relationship(relationship)
                            stats["contraindications_imported"] += 1
                            
            except Exception as e:
                logger.error(f"Error importing contraindications for {drug_contraindications['drug']}: {e}")
                stats["errors"] += 1
    
    async def _get_or_create_drug_entity(self, drug_name: str) -> Optional[Any]:
        """Get or create a drug entity."""
        try:
            # Try to find existing drug entity
            existing_entities = await self.service.search_medical_entities(
                query=drug_name,
                entity_type=EntityType.MEDICATION,
                limit=1
            )
            
            if existing_entities:
                return existing_entities[0]
            
            # Create new drug entity
            drug_entity = MedicalEntityCreate(
                name=drug_name.replace(" ", "_").upper(),
                display_name=drug_name,
                entity_type=EntityType.MEDICATION,
                description=f"Medication: {drug_name}",
                ontology_source=OntologySource.DRUG_INTERACTION_DATA,
                confidence_level=ConfidenceLevel.MEDIUM,
                evidence_level=EvidenceLevel.LEVEL_2,
                metadata={
                    "source": "drug_interaction_importer",
                    "drug_type": "prescription"
                }
            )
            
            return await self.service.create_medical_entity(drug_entity)
            
        except Exception as e:
            logger.error(f"Error getting or creating drug entity for {drug_name}: {e}")
            return None
    
    async def _get_or_create_entity(self, name: str, entity_type: EntityType) -> Optional[Any]:
        """Get or create an entity of specified type."""
        try:
            # Try to find existing entity
            existing_entities = await self.service.search_medical_entities(
                query=name,
                entity_type=entity_type,
                limit=1
            )
            
            if existing_entities:
                return existing_entities[0]
            
            # Create new entity
            entity = MedicalEntityCreate(
                name=name.replace(" ", "_").upper(),
                display_name=name,
                entity_type=entity_type,
                description=f"{entity_type.value}: {name}",
                ontology_source=OntologySource.DRUG_INTERACTION_DATA,
                confidence_level=ConfidenceLevel.MEDIUM,
                evidence_level=EvidenceLevel.LEVEL_2,
                metadata={
                    "source": "drug_interaction_importer",
                    "entity_category": entity_type.value
                }
            )
            
            return await self.service.create_medical_entity(entity)
            
        except Exception as e:
            logger.error(f"Error getting or creating entity for {name}: {e}")
            return None
    
    async def import_from_file(self, file_path: str) -> Dict[str, Any]:
        """Import drug interactions from a file."""
        logger.info(f"Importing drug interactions from file: {file_path}")
        
        stats = {
            "interactions_imported": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }
        
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() == '.csv':
                await self._import_from_csv(file_path, stats)
            elif file_path.suffix.lower() == '.json':
                await self._import_from_json(file_path, stats)
            else:
                logger.error(f"Unsupported file format: {file_path.suffix}")
                stats["errors"] += 1
                
        except Exception as e:
            logger.error(f"Error importing from file {file_path}: {e}")
            stats["errors"] += 1
            
        stats["end_time"] = datetime.utcnow()
        logger.info(f"File import completed: {stats}")
        return stats
    
    async def _import_from_csv(self, file_path: Path, stats: Dict[str, Any]):
        """Import drug interactions from CSV file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    drug1 = row.get('drug1', '')
                    drug2 = row.get('drug2', '')
                    interaction = row.get('interaction', '')
                    severity = row.get('severity', 'Unknown')
                    
                    if drug1 and drug2:
                        drug1_entity = await self._get_or_create_drug_entity(drug1)
                        drug2_entity = await self._get_or_create_drug_entity(drug2)
                        
                        if drug1_entity and drug2_entity:
                            relationship = RelationshipCreate(
                                source_entity_id=drug1_entity.id,
                                target_entity_id=drug2_entity.id,
                                relationship_type=RelationshipType.INTERACTS_WITH,
                                confidence_level=ConfidenceLevel.MEDIUM,
                                evidence_level=EvidenceLevel.LEVEL_2,
                                metadata={
                                    "interaction_type": "drug_drug_interaction",
                                    "severity": severity,
                                    "description": interaction,
                                    "source": "csv_file_import"
                                }
                            )
                            
                            await self.service.create_relationship(relationship)
                            stats["interactions_imported"] += 1
                            
                except Exception as e:
                    logger.error(f"Error importing CSV row {row}: {e}")
                    stats["errors"] += 1
    
    async def _import_from_json(self, file_path: Path, stats: Dict[str, Any]):
        """Import drug interactions from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            for interaction in data:
                try:
                    drug1 = interaction.get('drug1', '')
                    drug2 = interaction.get('drug2', '')
                    interaction_desc = interaction.get('interaction', '')
                    severity = interaction.get('severity', 'Unknown')
                    
                    if drug1 and drug2:
                        drug1_entity = await self._get_or_create_drug_entity(drug1)
                        drug2_entity = await self._get_or_create_drug_entity(drug2)
                        
                        if drug1_entity and drug2_entity:
                            relationship = RelationshipCreate(
                                source_entity_id=drug1_entity.id,
                                target_entity_id=drug2_entity.id,
                                relationship_type=RelationshipType.INTERACTS_WITH,
                                confidence_level=ConfidenceLevel.MEDIUM,
                                evidence_level=EvidenceLevel.LEVEL_2,
                                metadata={
                                    "interaction_type": "drug_drug_interaction",
                                    "severity": severity,
                                    "description": interaction_desc,
                                    "source": "json_file_import"
                                }
                            )
                            
                            await self.service.create_relationship(relationship)
                            stats["interactions_imported"] += 1
                            
                except Exception as e:
                    logger.error(f"Error importing JSON interaction {interaction}: {e}")
                    stats["errors"] += 1 