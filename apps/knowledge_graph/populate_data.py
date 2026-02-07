#!/usr/bin/env python3
"""
Data Population Script for Knowledge Graph Service.

This script populates the knowledge graph with medical ontologies,
sample data, and drug interactions.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from apps.knowledge_graph.data_population.data_population_manager import DataPopulationManager
from apps.knowledge_graph.services.knowledge_graph_service import KnowledgeGraphService
from common.utils.logging import setup_logging

setup_logging()


async def main():
    """Main function for data population."""
    print("🚀 Starting Knowledge Graph Data Population...")
    
    # Initialize knowledge graph service
    service = KnowledgeGraphService()
    await service.initialize()
    
    # Initialize data population manager
    manager = DataPopulationManager(service)
    
    try:
        print("📊 Step 1: Generating sample medical data...")
        sample_results = await manager.populate_sample_data_only()
        print(f"✅ Sample data generated: {sample_results['total_entities']} entities, {sample_results['total_relationships']} relationships")
        
        print("💊 Step 2: Importing drug interactions...")
        drug_results = await manager.populate_drug_interactions_only()
        print(f"✅ Drug interactions imported: {drug_results['total_entities']} entities, {drug_results['total_relationships']} relationships")
        
        print("🔍 Step 3: Validating data population...")
        validation_results = await manager.validate_population()
        print(f"✅ Validation completed: {validation_results['total_entities']} total entities, {validation_results['total_relationships']} total relationships")
        
        print("\n📈 Knowledge Graph Statistics:")
        print(f"   - Total Entities: {validation_results['total_entities']}")
        print(f"   - Total Relationships: {validation_results['total_relationships']}")
        print(f"   - Entity Types: {validation_results['entity_types']}")
        print(f"   - Relationship Types: {validation_results['relationship_types']}")
        print(f"   - Ontology Sources: {validation_results['ontology_sources']}")
        
        if validation_results['validation_errors']:
            print(f"⚠️  Validation Errors: {validation_results['validation_errors']}")
        
        print("\n🎉 Knowledge Graph Data Population Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Error during data population: {e}")
        sys.exit(1)
    
    finally:
        await service.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 