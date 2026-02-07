"""
Medical Ontology Importer for Knowledge Graph Service.

This module provides functionality to import and process medical ontologies
including SNOMED CT, ICD-10, ICD-11, LOINC, and RxNorm.
"""

import asyncio
import logging
import json
import csv
import gzip
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import httpx
from neo4j import AsyncGraphDatabase
from qdrant_client import AsyncQdrantClient
from sentence_transformers import SentenceTransformer

from apps.knowledge_graph.models.knowledge_models import (
    EntityType, RelationshipType, ConfidenceLevel, EvidenceLevel, OntologySource,
    MedicalEntityCreate, RelationshipCreate
)
from apps.knowledge_graph.services.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)


class OntologyImporter:
    """Imports medical ontologies into the knowledge graph."""
    
    def __init__(self, knowledge_graph_service: KnowledgeGraphService):
        self.service = knowledge_graph_service
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    async def import_snomed_ct(self, data_path: str) -> Dict[str, Any]:
        """Import SNOMED CT concepts and relationships."""
        logger.info("Starting SNOMED CT import...")
        
        stats = {
            "concepts_imported": 0,
            "relationships_imported": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }
        
        try:
            # Import concepts
            concepts_file = Path(data_path) / "sct2_Concept_Snapshot_INT_20240731.txt"
            if concepts_file.exists():
                await self._import_snomed_concepts(concepts_file, stats)
            
            # Import relationships
            relationships_file = Path(data_path) / "sct2_Relationship_Snapshot_INT_20240731.txt"
            if relationships_file.exists():
                await self._import_snomed_relationships(relationships_file, stats)
            
            # Import descriptions
            descriptions_file = Path(data_path) / "sct2_Description_Snapshot_INT_20240731.txt"
            if descriptions_file.exists():
                await self._import_snomed_descriptions(descriptions_file, stats)
                
        except Exception as e:
            logger.error(f"Error importing SNOMED CT: {e}")
            stats["errors"] += 1
            
        stats["end_time"] = datetime.utcnow()
        logger.info(f"SNOMED CT import completed: {stats}")
        return stats
    
    async def _import_snomed_concepts(self, file_path: Path, stats: Dict[str, Any]):
        """Import SNOMED CT concepts."""
        logger.info(f"Importing SNOMED CT concepts from {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)  # Skip header
            
            for row in reader:
                try:
                    if len(row) >= 5:
                        concept_id, effective_time, active, module_id, definition_status_id = row[:5]
                        
                        if active == '1':  # Only import active concepts
                            entity_data = MedicalEntityCreate(
                                name=f"SNOMED_{concept_id}",
                                display_name=f"SNOMED Concept {concept_id}",
                                entity_type=EntityType.CONDITION,
                                description=f"SNOMED CT Concept ID: {concept_id}",
                                ontology_source=OntologySource.SNOMED_CT,
                                ontology_id=concept_id,
                                confidence_level=ConfidenceLevel.HIGH,
                                evidence_level=EvidenceLevel.LEVEL_1,
                                metadata={
                                    "effective_time": effective_time,
                                    "module_id": module_id,
                                    "definition_status_id": definition_status_id,
                                    "snomed_concept_id": concept_id
                                }
                            )
                            
                            await self.service.create_medical_entity(entity_data)
                            stats["concepts_imported"] += 1
                            
                            if stats["concepts_imported"] % 1000 == 0:
                                logger.info(f"Imported {stats['concepts_imported']} SNOMED concepts")
                                
                except Exception as e:
                    logger.error(f"Error importing SNOMED concept {row}: {e}")
                    stats["errors"] += 1
    
    async def _import_snomed_relationships(self, file_path: Path, stats: Dict[str, Any]):
        """Import SNOMED CT relationships."""
        logger.info(f"Importing SNOMED CT relationships from {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)  # Skip header
            
            for row in reader:
                try:
                    if len(row) >= 7:
                        source_id, destination_id, relationship_group, type_id, characteristic_type_id, modifier_id, active = row[:7]
                        
                        if active == '1':  # Only import active relationships
                            # Map SNOMED relationship types to our types
                            relationship_type = self._map_snomed_relationship_type(type_id)
                            
                            if relationship_type:
                                relationship_data = RelationshipCreate(
                                    source_entity_id=f"SNOMED_{source_id}",
                                    target_entity_id=f"SNOMED_{destination_id}",
                                    relationship_type=relationship_type,
                                    confidence_level=ConfidenceLevel.HIGH,
                                    evidence_level=EvidenceLevel.LEVEL_1,
                                    metadata={
                                        "snomed_type_id": type_id,
                                        "relationship_group": relationship_group,
                                        "characteristic_type_id": characteristic_type_id,
                                        "modifier_id": modifier_id
                                    }
                                )
                                
                                await self.service.create_relationship(relationship_data)
                                stats["relationships_imported"] += 1
                                
                                if stats["relationships_imported"] % 1000 == 0:
                                    logger.info(f"Imported {stats['relationships_imported']} SNOMED relationships")
                                    
                except Exception as e:
                    logger.error(f"Error importing SNOMED relationship {row}: {e}")
                    stats["errors"] += 1
    
    async def _import_snomed_descriptions(self, file_path: Path, stats: Dict[str, Any]):
        """Import SNOMED CT descriptions."""
        logger.info(f"Importing SNOMED CT descriptions from {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)  # Skip header
            
            for row in reader:
                try:
                    if len(row) >= 7:
                        description_id, effective_time, active, module_id, concept_id, language_code, type_id, term, case_significance_id = row[:9]
                        
                        if active == '1' and type_id == '900000000000003001':  # Fully specified name
                            # Update the entity with the description
                            await self.service.update_medical_entity(
                                entity_id=f"SNOMED_{concept_id}",
                                update_data={"display_name": term, "description": term}
                            )
                            
                except Exception as e:
                    logger.error(f"Error importing SNOMED description {row}: {e}")
                    stats["errors"] += 1
    
    def _map_snomed_relationship_type(self, type_id: str) -> Optional[RelationshipType]:
        """Map SNOMED CT relationship types to our relationship types."""
        snomed_type_mapping = {
            "116680003": RelationshipType.IS_A,  # Is a
            "363698007": RelationshipType.FINDING_SITE,  # Finding site
            "363699004": RelationshipType.PROCEDURE_SITE,  # Procedure site
            "260686004": RelationshipType.METHOD,  # Method
            "246075003": RelationshipType.CAUSATIVE_AGENT,  # Causative agent
            "363700003": RelationshipType.DIRECT_SUBSTANCE,  # Direct substance
            "363701004": RelationshipType.DIRECT_MORPHOLOGY,  # Direct morphology
            "363702006": RelationshipType.DIRECT_DEVICE,  # Direct device
            "363703001": RelationshipType.DIRECT_PROCEDURE,  # Direct procedure
            "363704007": RelationshipType.DIRECT_ACTIVITY,  # Direct activity
            "363705008": RelationshipType.DIRECT_ATTRIBUTE,  # Direct attribute
            "363706009": RelationshipType.DIRECT_CONTEXT,  # Direct context
            "363707000": RelationshipType.DIRECT_TEMPORAL,  # Direct temporal
            "363708005": RelationshipType.DIRECT_QUANTIFIER,  # Direct quantifier
            "363709002": RelationshipType.DIRECT_SCALE,  # Direct scale
            "363710007": RelationshipType.DIRECT_REFERENCE,  # Direct reference
            "363711006": RelationshipType.DIRECT_PART,  # Direct part
            "363712004": RelationshipType.DIRECT_FORM,  # Direct form
            "363713009": RelationshipType.DIRECT_SPECIMEN,  # Direct specimen
            "363714003": RelationshipType.DIRECT_SPECIMEN_PROCEDURE,  # Direct specimen procedure
            "363715002": RelationshipType.DIRECT_SPECIMEN_ATTRIBUTE,  # Direct specimen attribute
            "363716001": RelationshipType.DIRECT_SPECIMEN_CONTEXT,  # Direct specimen context
            "363717005": RelationshipType.DIRECT_SPECIMEN_TEMPORAL,  # Direct specimen temporal
            "363718000": RelationshipType.DIRECT_SPECIMEN_QUANTIFIER,  # Direct specimen quantifier
            "363719008": RelationshipType.DIRECT_SPECIMEN_SCALE,  # Direct specimen scale
            "363720002": RelationshipType.DIRECT_SPECIMEN_REFERENCE,  # Direct specimen reference
            "363721003": RelationshipType.DIRECT_SPECIMEN_PART,  # Direct specimen part
            "363722005": RelationshipType.DIRECT_SPECIMEN_FORM,  # Direct specimen form
        }
        
        return snomed_type_mapping.get(type_id, RelationshipType.RELATED_TO)
    
    async def import_icd10(self, data_path: str) -> Dict[str, Any]:
        """Import ICD-10 codes and descriptions."""
        logger.info("Starting ICD-10 import...")
        
        stats = {
            "codes_imported": 0,
            "relationships_imported": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }
        
        try:
            icd10_file = Path(data_path) / "icd10cm_codes_2024.txt"
            if icd10_file.exists():
                await self._import_icd10_codes(icd10_file, stats)
                
        except Exception as e:
            logger.error(f"Error importing ICD-10: {e}")
            stats["errors"] += 1
            
        stats["end_time"] = datetime.utcnow()
        logger.info(f"ICD-10 import completed: {stats}")
        return stats
    
    async def _import_icd10_codes(self, file_path: Path, stats: Dict[str, Any]):
        """Import ICD-10 codes."""
        logger.info(f"Importing ICD-10 codes from {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    line = line.strip()
                    if line and '\t' in line:
                        code, description = line.split('\t', 1)
                        
                        entity_data = MedicalEntityCreate(
                            name=f"ICD10_{code}",
                            display_name=description,
                            entity_type=EntityType.CONDITION,
                            description=f"ICD-10 Code: {code} - {description}",
                            ontology_source=OntologySource.ICD_10,
                            ontology_id=code,
                            confidence_level=ConfidenceLevel.HIGH,
                            evidence_level=EvidenceLevel.LEVEL_1,
                            metadata={
                                "icd10_code": code,
                                "icd10_description": description
                            }
                        )
                        
                        await self.service.create_medical_entity(entity_data)
                        stats["codes_imported"] += 1
                        
                        if stats["codes_imported"] % 1000 == 0:
                            logger.info(f"Imported {stats['codes_imported']} ICD-10 codes")
                            
                except Exception as e:
                    logger.error(f"Error importing ICD-10 code {line}: {e}")
                    stats["errors"] += 1
    
    async def import_rxnorm(self, data_path: str) -> Dict[str, Any]:
        """Import RxNorm drug concepts."""
        logger.info("Starting RxNorm import...")
        
        stats = {
            "concepts_imported": 0,
            "relationships_imported": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }
        
        try:
            rxnorm_file = Path(data_path) / "rxnorm_concepts.txt"
            if rxnorm_file.exists():
                await self._import_rxnorm_concepts(rxnorm_file, stats)
                
        except Exception as e:
            logger.error(f"Error importing RxNorm: {e}")
            stats["errors"] += 1
            
        stats["end_time"] = datetime.utcnow()
        logger.info(f"RxNorm import completed: {stats}")
        return stats
    
    async def _import_rxnorm_concepts(self, file_path: Path, stats: Dict[str, Any]):
        """Import RxNorm concepts."""
        logger.info(f"Importing RxNorm concepts from {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='|')
            next(reader)  # Skip header
            
            for row in reader:
                try:
                    if len(row) >= 3:
                        rxcui, name, tty = row[:3]
                        
                        entity_data = MedicalEntityCreate(
                            name=f"RXNORM_{rxcui}",
                            display_name=name,
                            entity_type=EntityType.MEDICATION,
                            description=f"RxNorm Concept: {name} (TTY: {tty})",
                            ontology_source=OntologySource.RXNORM,
                            ontology_id=rxcui,
                            confidence_level=ConfidenceLevel.HIGH,
                            evidence_level=EvidenceLevel.LEVEL_1,
                            metadata={
                                "rxcui": rxcui,
                                "name": name,
                                "tty": tty
                            }
                        )
                        
                        await self.service.create_medical_entity(entity_data)
                        stats["concepts_imported"] += 1
                        
                        if stats["concepts_imported"] % 1000 == 0:
                            logger.info(f"Imported {stats['concepts_imported']} RxNorm concepts")
                            
                except Exception as e:
                    logger.error(f"Error importing RxNorm concept {row}: {e}")
                    stats["errors"] += 1
    
    async def import_loinc(self, data_path: str) -> Dict[str, Any]:
        """Import LOINC laboratory codes."""
        logger.info("Starting LOINC import...")
        
        stats = {
            "codes_imported": 0,
            "relationships_imported": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }
        
        try:
            loinc_file = Path(data_path) / "loinc.csv"
            if loinc_file.exists():
                await self._import_loinc_codes(loinc_file, stats)
                
        except Exception as e:
            logger.error(f"Error importing LOINC: {e}")
            stats["errors"] += 1
            
        stats["end_time"] = datetime.utcnow()
        logger.info(f"LOINC import completed: {stats}")
        return stats
    
    async def _import_loinc_codes(self, file_path: Path, stats: Dict[str, Any]):
        """Import LOINC codes."""
        logger.info(f"Importing LOINC codes from {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    loinc_num = row.get('LOINC_NUM', '')
                    component = row.get('COMPONENT', '')
                    property = row.get('PROPERTY', '')
                    time_aspct = row.get('TIME_ASPCT', '')
                    system = row.get('SYSTEM', '')
                    scale_typ = row.get('SCALE_TYP', '')
                    method_typ = row.get('METHOD_TYP', '')
                    class_type = row.get('CLASS', '')
                    
                    if loinc_num and component:
                        display_name = f"{component} - {property} - {system}"
                        
                        entity_data = MedicalEntityCreate(
                            name=f"LOINC_{loinc_num}",
                            display_name=display_name,
                            entity_type=EntityType.LAB_TEST,
                            description=f"LOINC Code: {loinc_num} - {display_name}",
                            ontology_source=OntologySource.LOINC,
                            ontology_id=loinc_num,
                            confidence_level=ConfidenceLevel.HIGH,
                            evidence_level=EvidenceLevel.LEVEL_1,
                            metadata={
                                "loinc_num": loinc_num,
                                "component": component,
                                "property": property,
                                "time_aspct": time_aspct,
                                "system": system,
                                "scale_typ": scale_typ,
                                "method_typ": method_typ,
                                "class_type": class_type
                            }
                        )
                        
                        await self.service.create_medical_entity(entity_data)
                        stats["codes_imported"] += 1
                        
                        if stats["codes_imported"] % 1000 == 0:
                            logger.info(f"Imported {stats['codes_imported']} LOINC codes")
                            
                except Exception as e:
                    logger.error(f"Error importing LOINC code {row}: {e}")
                    stats["errors"] += 1
    
    async def import_all_ontologies(self, data_path: str) -> Dict[str, Any]:
        """Import all available ontologies."""
        logger.info("Starting comprehensive ontology import...")
        
        results = {
            "snomed_ct": None,
            "icd10": None,
            "rxnorm": None,
            "loinc": None,
            "total_entities": 0,
            "total_relationships": 0,
            "total_errors": 0,
            "start_time": datetime.utcnow()
        }
        
        # Import each ontology
        if Path(data_path).exists():
            results["snomed_ct"] = await self.import_snomed_ct(data_path)
            results["icd10"] = await self.import_icd10(data_path)
            results["rxnorm"] = await self.import_rxnorm(data_path)
            results["loinc"] = await self.import_loinc(data_path)
        
        # Calculate totals
        for ontology_result in results.values():
            if ontology_result:
                results["total_entities"] += ontology_result.get("concepts_imported", 0) + ontology_result.get("codes_imported", 0)
                results["total_relationships"] += ontology_result.get("relationships_imported", 0)
                results["total_errors"] += ontology_result.get("errors", 0)
        
        results["end_time"] = datetime.utcnow()
        logger.info(f"Comprehensive ontology import completed: {results}")
        return results 