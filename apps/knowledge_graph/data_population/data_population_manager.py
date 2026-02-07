"""
Data Population Manager for Knowledge Graph Service.

This module orchestrates the entire data population process, including
ontology imports, sample data generation, and drug interactions.
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import argparse

from apps.knowledge_graph.services.knowledge_graph_service import KnowledgeGraphService
from apps.knowledge_graph.data_population.ontology_importer import OntologyImporter
from apps.knowledge_graph.data_population.sample_data_generator import SampleDataGenerator
from apps.knowledge_graph.data_population.drug_interaction_importer import DrugInteractionImporter
from apps.knowledge_graph.models.knowledge_models import EntityType, RelationshipType, OntologySource

logger = logging.getLogger(__name__)


class DataPopulationManager:
    """Manages the complete data population process."""
    
    def __init__(self, knowledge_graph_service: KnowledgeGraphService):
        self.service = knowledge_graph_service
        self.ontology_importer = OntologyImporter(knowledge_graph_service)
        self.sample_data_generator = SampleDataGenerator(knowledge_graph_service)
        self.drug_interaction_importer = DrugInteractionImporter(knowledge_graph_service)
        
        self.population_stats = {
            "total_entities": 0,
            "total_relationships": 0,
            "total_errors": 0,
            "start_time": None,
            "end_time": None,
            "components": {}
        }
    
    async def populate_all_data(self, data_path: str = "data") -> Dict[str, Any]:
        """Populate the knowledge graph with all available data."""
        logger.info("Starting comprehensive data population...")
        
        self.population_stats["start_time"] = datetime.utcnow()
        
        try:
            # 1. Import medical ontologies
            logger.info("Step 1: Importing medical ontologies...")
            ontology_results = await self.ontology_importer.import_all_ontologies(data_path)
            self.population_stats["components"]["ontologies"] = ontology_results
            
            # 2. Generate sample data
            logger.info("Step 2: Generating sample data...")
            sample_results = await self.sample_data_generator.generate_sample_entities()
            self.population_stats["components"]["sample_data"] = sample_results
            
            # 3. Generate disease-specific knowledge graphs
            logger.info("Step 3: Generating disease-specific knowledge graphs...")
            disease_results = await self.sample_data_generator.generate_disease_specific_data()
            self.population_stats["components"]["disease_data"] = disease_results
            
            # 4. Import drug interactions
            logger.info("Step 4: Importing drug interactions...")
            drug_results = await self.drug_interaction_importer.import_drug_interactions()
            self.population_stats["components"]["drug_interactions"] = drug_results
            
            # Calculate totals
            self._calculate_totals()
            
            # 5. Create embeddings for all entities
            logger.info("Step 5: Creating embeddings for all entities...")
            await self._create_embeddings()
            
            # 6. Generate knowledge graph statistics
            logger.info("Step 6: Generating knowledge graph statistics...")
            await self._generate_statistics()
            
        except Exception as e:
            logger.error(f"Error during data population: {e}")
            self.population_stats["total_errors"] += 1
        
        self.population_stats["end_time"] = datetime.utcnow()
        
        # Save population report
        await self._save_population_report()
        
        logger.info("Data population completed successfully!")
        return self.population_stats
    
    async def populate_ontologies_only(self, data_path: str = "data") -> Dict[str, Any]:
        """Populate only medical ontologies."""
        logger.info("Starting ontology-only population...")
        
        self.population_stats["start_time"] = datetime.utcnow()
        
        try:
            ontology_results = await self.ontology_importer.import_all_ontologies(data_path)
            self.population_stats["components"]["ontologies"] = ontology_results
            
            # Calculate totals
            self._calculate_totals()
            
            # Create embeddings
            await self._create_embeddings()
            
        except Exception as e:
            logger.error(f"Error during ontology population: {e}")
            self.population_stats["total_errors"] += 1
        
        self.population_stats["end_time"] = datetime.utcnow()
        await self._save_population_report()
        
        return self.population_stats
    
    async def populate_sample_data_only(self) -> Dict[str, Any]:
        """Populate only sample data."""
        logger.info("Starting sample data-only population...")
        
        self.population_stats["start_time"] = datetime.utcnow()
        
        try:
            # Generate sample data
            sample_results = await self.sample_data_generator.generate_sample_entities()
            self.population_stats["components"]["sample_data"] = sample_results
            
            # Generate disease-specific data
            disease_results = await self.sample_data_generator.generate_disease_specific_data()
            self.population_stats["components"]["disease_data"] = disease_results
            
            # Calculate totals
            self._calculate_totals()
            
            # Create embeddings
            await self._create_embeddings()
            
        except Exception as e:
            logger.error(f"Error during sample data population: {e}")
            self.population_stats["total_errors"] += 1
        
        self.population_stats["end_time"] = datetime.utcnow()
        await self._save_population_report()
        
        return self.population_stats
    
    async def populate_drug_interactions_only(self) -> Dict[str, Any]:
        """Populate only drug interactions."""
        logger.info("Starting drug interaction-only population...")
        
        self.population_stats["start_time"] = datetime.utcnow()
        
        try:
            drug_results = await self.drug_interaction_importer.import_drug_interactions()
            self.population_stats["components"]["drug_interactions"] = drug_results
            
            # Calculate totals
            self._calculate_totals()
            
            # Create embeddings
            await self._create_embeddings()
            
        except Exception as e:
            logger.error(f"Error during drug interaction population: {e}")
            self.population_stats["total_errors"] += 1
        
        self.population_stats["end_time"] = datetime.utcnow()
        await self._save_population_report()
        
        return self.population_stats
    
    def _calculate_totals(self):
        """Calculate total statistics from all components."""
        self.population_stats["total_entities"] = 0
        self.population_stats["total_relationships"] = 0
        self.population_stats["total_errors"] = 0
        
        for component_name, component_stats in self.population_stats["components"].items():
            if component_stats:
                # Add entities
                self.population_stats["total_entities"] += (
                    component_stats.get("concepts_imported", 0) +
                    component_stats.get("codes_imported", 0) +
                    component_stats.get("entities_created", 0) +
                    component_stats.get("diseases_created", 0) +
                    component_stats.get("interactions_imported", 0) +
                    component_stats.get("side_effects_imported", 0) +
                    component_stats.get("contraindications_imported", 0)
                )
                
                # Add relationships
                self.population_stats["total_relationships"] += (
                    component_stats.get("relationships_imported", 0) +
                    component_stats.get("relationships_created", 0)
                )
                
                # Add errors
                self.population_stats["total_errors"] += component_stats.get("errors", 0)
    
    async def _create_embeddings(self):
        """Create embeddings for all entities in the knowledge graph."""
        logger.info("Creating embeddings for all entities...")
        
        try:
            # Get all entities
            entities = await self.service.list_medical_entities(limit=10000)
            
            logger.info(f"Creating embeddings for {len(entities)} entities...")
            
            # Create embeddings in batches
            batch_size = 100
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]
                
                for entity in batch:
                    try:
                        # Create embedding for entity
                        await self.service.create_entity_embedding(entity.id)
                        
                    except Exception as e:
                        logger.error(f"Error creating embedding for entity {entity.id}: {e}")
                
                if i % 1000 == 0:
                    logger.info(f"Processed {i} entities for embeddings...")
            
            logger.info("Embedding creation completed!")
            
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
    
    async def _generate_statistics(self):
        """Generate comprehensive knowledge graph statistics."""
        logger.info("Generating knowledge graph statistics...")
        
        try:
            stats = await self.service.get_statistics()
            logger.info(f"Knowledge graph statistics: {stats}")
            
        except Exception as e:
            logger.error(f"Error generating statistics: {e}")
    
    async def _save_population_report(self):
        """Save a detailed population report."""
        try:
            report = {
                "population_stats": self.population_stats,
                "timestamp": datetime.utcnow().isoformat(),
                "service_version": "1.0.0"
            }
            
            # Create reports directory
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            # Save report
            report_file = reports_dir / f"population_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Population report saved to: {report_file}")
            
        except Exception as e:
            logger.error(f"Error saving population report: {e}")
    
    async def validate_population(self) -> Dict[str, Any]:
        """Validate the data population results."""
        logger.info("Validating data population results...")
        
        validation_results = {
            "total_entities": 0,
            "total_relationships": 0,
            "entity_types": {},
            "relationship_types": {},
            "ontology_sources": {},
            "validation_errors": []
        }
        
        try:
            # Get overall statistics
            stats = await self.service.get_statistics()
            validation_results["total_entities"] = stats.total_entities
            validation_results["total_relationships"] = stats.total_relationships
            
            # Validate entity distribution
            for entity_type in EntityType:
                try:
                    entities = await self.service.list_medical_entities(
                        entity_type=entity_type,
                        limit=1000
                    )
                    validation_results["entity_types"][entity_type.value] = len(entities)
                except Exception as e:
                    validation_results["validation_errors"].append(f"Error validating {entity_type.value}: {e}")
            
            # Validate relationship distribution
            for relationship_type in RelationshipType:
                try:
                    relationships = await self.service.list_relationships(
                        relationship_type=relationship_type,
                        limit=1000
                    )
                    validation_results["relationship_types"][relationship_type.value] = len(relationships)
                except Exception as e:
                    validation_results["validation_errors"].append(f"Error validating {relationship_type.value}: {e}")
            
            # Validate ontology sources
            for source in OntologySource:
                try:
                    entities = await self.service.list_medical_entities(
                        ontology_source=source,
                        limit=1000
                    )
                    validation_results["ontology_sources"][source.value] = len(entities)
                except Exception as e:
                    validation_results["validation_errors"].append(f"Error validating {source.value}: {e}")
            
            logger.info(f"Validation completed: {validation_results}")
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            validation_results["validation_errors"].append(str(e))
        
        return validation_results
    
    async def cleanup_test_data(self):
        """Clean up test data from the knowledge graph."""
        logger.info("Cleaning up test data...")
        
        try:
            # Remove sample data entities
            sample_entities = await self.service.list_medical_entities(
                ontology_source=OntologySource.SAMPLE_DATA,
                limit=10000
            )
            
            for entity in sample_entities:
                try:
                    await self.service.delete_medical_entity(entity.id)
                except Exception as e:
                    logger.error(f"Error deleting sample entity {entity.id}: {e}")
            
            # Remove drug interaction data entities
            drug_entities = await self.service.list_medical_entities(
                ontology_source=OntologySource.DRUG_INTERACTION_DATA,
                limit=10000
            )
            
            for entity in drug_entities:
                try:
                    await self.service.delete_medical_entity(entity.id)
                except Exception as e:
                    logger.error(f"Error deleting drug entity {entity.id}: {e}")
            
            logger.info("Test data cleanup completed!")
            
        except Exception as e:
            logger.error(f"Error during test data cleanup: {e}")


async def main():
    """Main function for data population."""
    parser = argparse.ArgumentParser(description="Knowledge Graph Data Population")
    parser.add_argument("--mode", choices=["all", "ontologies", "sample", "drugs"], 
                       default="all", help="Population mode")
    parser.add_argument("--data-path", default="data", help="Path to ontology data files")
    parser.add_argument("--validate", action="store_true", help="Validate population results")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test data")
    
    args = parser.parse_args()
    
    # Initialize knowledge graph service
    service = KnowledgeGraphService()
    await service.initialize()
    
    # Initialize data population manager
    manager = DataPopulationManager(service)
    
    try:
        if args.cleanup:
            await manager.cleanup_test_data()
            return
        
        # Run population based on mode
        if args.mode == "all":
            results = await manager.populate_all_data(args.data_path)
        elif args.mode == "ontologies":
            results = await manager.populate_ontologies_only(args.data_path)
        elif args.mode == "sample":
            results = await manager.populate_sample_data_only()
        elif args.mode == "drugs":
            results = await manager.populate_drug_interactions_only()
        
        print(f"Data population completed: {results}")
        
        if args.validate:
            validation_results = await manager.validate_population()
            print(f"Validation results: {validation_results}")
    
    finally:
        await service.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 