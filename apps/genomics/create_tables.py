"""
Database setup script for Genomics Service.

This script creates all necessary tables for the genomics service including:
- Genomic data storage
- Genetic variants
- Analysis results
- Pharmacogenomic profiles
- Ancestry analysis
- Genetic counseling
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.config.settings import get_settings
from apps.genomics.models.genomic_data import GenomicData, GeneticVariant, PharmacogenomicProfile
from apps.genomics.models.analysis import GenomicAnalysis, DiseaseRiskAssessment, AncestryAnalysis
from apps.genomics.models.counseling import GeneticCounseling, CounselingSession, RiskReport
from common.models.base import Base

# Get settings
settings = get_settings()

def create_genomics_schema():
    """Create genomics schema and tables."""
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Create schema
    with engine.connect() as conn:
        # Create genomics schema
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS genomics"))
        conn.commit()
    
    # Create tables
    Base.metadata.create_all(bind=engine, tables=[
        GenomicData.__table__,
        GeneticVariant.__table__,
        PharmacogenomicProfile.__table__,
        GenomicAnalysis.__table__,
        DiseaseRiskAssessment.__table__,
        AncestryAnalysis.__table__,
        GeneticCounseling.__table__,
        CounselingSession.__table__,
        RiskReport.__table__
    ])
    
    print("✅ Genomics schema and tables created successfully!")

def create_indexes():
    """Create database indexes for better performance."""
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # GenomicData indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_genomic_data_user_id 
            ON genomics.genomic_data(user_id)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_genomic_data_source 
            ON genomics.genomic_data(data_source)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_genomic_data_format 
            ON genomics.genomic_data(data_format)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_genomic_data_quality 
            ON genomics.genomic_data(quality_status)
        """))
        
        # GeneticVariant indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_genetic_variant_chromosome 
            ON genomics.genetic_variants(chromosome)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_genetic_variant_position 
            ON genomics.genetic_variants(position)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_genetic_variant_gene 
            ON genomics.genetic_variants(gene_name)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_genetic_variant_rs_id 
            ON genomics.genetic_variants(rs_id)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_genetic_variant_clinical 
            ON genomics.genetic_variants(clinical_significance)
        """))
        
        # PharmacogenomicProfile indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pharmacogenomic_user_id 
            ON genomics.pharmacogenomic_profiles(user_id)
        """))
        
        # GenomicAnalysis indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_genomic_analysis_user_id 
            ON genomics.genomic_analyses(user_id)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_genomic_analysis_type 
            ON genomics.genomic_analyses(analysis_type)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_genomic_analysis_status 
            ON genomics.genomic_analyses(status)
        """))
        
        # DiseaseRiskAssessment indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_disease_risk_disease 
            ON genomics.disease_risk_assessments(disease_name)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_disease_risk_level 
            ON genomics.disease_risk_assessments(risk_level)
        """))
        
        # AncestryAnalysis indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ancestry_analysis_user_id 
            ON genomics.ancestry_analyses(analysis_id)
        """))
        
        # GeneticCounseling indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_counseling_user_id 
            ON genomics.genetic_counseling(user_id)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_counseling_type 
            ON genomics.genetic_counseling(counseling_type)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_counseling_status 
            ON genomics.genetic_counseling(session_status)
        """))
        
        # RiskReport indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_risk_report_user_id 
            ON genomics.risk_reports(user_id)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_risk_report_type 
            ON genomics.risk_reports(report_type)
        """))
        
        conn.commit()
    
    print("✅ Database indexes created successfully!")

def seed_sample_data():
    """Seed sample data for testing."""
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Sample genomic data
        sample_genomic_data = GenomicData(
            user_id="550e8400-e29b-41d4-a716-446655440000",  # Sample user ID
            data_source="direct_to_consumer",
            data_format="vcf",
            file_path="/app/genomic_data/sample.vcf",
            file_size=1024000,
            checksum="abc123def456",
            sample_id="SAMPLE001",
            quality_score=0.95,
            quality_status="excellent",
            is_processed=True,
            is_analyzed=True
        )
        
        db.add(sample_genomic_data)
        db.commit()
        
        print("✅ Sample data seeded successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding sample data: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main function to set up the database."""
    print("🚀 Setting up Genomics Service database...")
    
    try:
        # Create schema and tables
        create_genomics_schema()
        
        # Create indexes
        create_indexes()
        
        # Seed sample data (optional)
        # seed_sample_data()
        
        print("🎉 Genomics Service database setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 