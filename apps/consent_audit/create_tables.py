"""
Database migration script for the Personal Health Assistant Consent Audit Service.

This script creates the necessary database tables and schemas for consent audit functionality.
"""

import asyncio
import os
import sys
from sqlalchemy import text

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.database.connection import get_db_manager
from common.utils.logging import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def create_consent_audit_schema():
    """Create the consent_audit schema."""
    db_manager = get_db_manager()
    
    async with db_manager.get_async_session() as db:
        try:
            # Create schema
            await db.execute(text("CREATE SCHEMA IF NOT EXISTS consent_audit"))
            await db.commit()
            logger.info("Created consent_audit schema")
        except Exception as e:
            logger.error(f"Failed to create consent_audit schema: {e}")
            await db.rollback()
            raise


async def create_consent_audit_tables():
    """Create the consent audit tables."""
    db_manager = get_db_manager()
    
    async with db_manager.get_async_session() as db:
        try:
            # Create consent_audit_logs table
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS consent_audit.consent_audit_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    event_type VARCHAR(50) NOT NULL,
                    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    severity VARCHAR(20) DEFAULT 'medium',
                    user_id UUID NOT NULL REFERENCES auth.users(id),
                    consent_record_id UUID REFERENCES auth.consent_records(id),
                    data_subject_id UUID,
                    event_description TEXT NOT NULL,
                    event_data JSONB DEFAULT '{}',
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    session_id UUID,
                    actor_id UUID NOT NULL REFERENCES auth.users(id),
                    actor_type VARCHAR(50) NOT NULL,
                    actor_role VARCHAR(100),
                    gdpr_compliant BOOLEAN DEFAULT TRUE,
                    hipaa_compliant BOOLEAN DEFAULT TRUE,
                    compliance_notes TEXT,
                    compliance_issues JSONB DEFAULT '[]',
                    risk_level VARCHAR(20) DEFAULT 'low',
                    risk_factors JSONB DEFAULT '[]',
                    mitigation_actions JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create indexes
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_consent_audit_logs_user_id 
                ON consent_audit.consent_audit_logs(user_id)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_consent_audit_logs_event_type 
                ON consent_audit.consent_audit_logs(event_type)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_consent_audit_logs_event_timestamp 
                ON consent_audit.consent_audit_logs(event_timestamp)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_consent_audit_logs_consent_record_id 
                ON consent_audit.consent_audit_logs(consent_record_id)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_consent_audit_logs_data_subject_id 
                ON consent_audit.consent_audit_logs(data_subject_id)
            """))
            
            # Create data_processing_audits table
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS consent_audit.data_processing_audits (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    processing_purpose VARCHAR(50) NOT NULL,
                    processing_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    processing_duration INTEGER,
                    data_categories JSONB DEFAULT '[]',
                    data_volume INTEGER,
                    data_sensitivity VARCHAR(20) DEFAULT 'medium',
                    user_id UUID NOT NULL REFERENCES auth.users(id),
                    consent_record_id UUID REFERENCES auth.consent_records(id),
                    data_subject_id UUID,
                    processing_method VARCHAR(50) NOT NULL,
                    processing_location VARCHAR(255),
                    processing_tools JSONB DEFAULT '[]',
                    third_parties_involved JSONB DEFAULT '[]',
                    data_shared_with JSONB DEFAULT '[]',
                    legal_basis VARCHAR(100) NOT NULL,
                    consent_verified BOOLEAN DEFAULT FALSE,
                    consent_verification_method VARCHAR(100),
                    compliance_status VARCHAR(30) DEFAULT 'pending_review',
                    data_encrypted BOOLEAN DEFAULT TRUE,
                    access_controls JSONB DEFAULT '[]',
                    retention_period INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create indexes for data_processing_audits
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_data_processing_audits_user_id 
                ON consent_audit.data_processing_audits(user_id)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_data_processing_audits_processing_purpose 
                ON consent_audit.data_processing_audits(processing_purpose)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_data_processing_audits_processing_timestamp 
                ON consent_audit.data_processing_audits(processing_timestamp)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_data_processing_audits_compliance_status 
                ON consent_audit.data_processing_audits(compliance_status)
            """))
            
            # Create compliance_reports table
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS consent_audit.compliance_reports (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    report_type VARCHAR(50) NOT NULL,
                    report_period_start TIMESTAMP NOT NULL,
                    report_period_end TIMESTAMP NOT NULL,
                    report_status VARCHAR(20) DEFAULT 'draft',
                    user_id UUID REFERENCES auth.users(id),
                    organization_id UUID,
                    scope_description TEXT NOT NULL,
                    total_consents INTEGER DEFAULT 0,
                    active_consents INTEGER DEFAULT 0,
                    expired_consents INTEGER DEFAULT 0,
                    withdrawn_consents INTEGER DEFAULT 0,
                    compliance_violations INTEGER DEFAULT 0,
                    security_incidents INTEGER DEFAULT 0,
                    data_breaches INTEGER DEFAULT 0,
                    data_processing_events INTEGER DEFAULT 0,
                    data_sharing_events INTEGER DEFAULT 0,
                    data_access_events INTEGER DEFAULT 0,
                    executive_summary TEXT,
                    detailed_findings JSONB DEFAULT '{}',
                    recommendations JSONB DEFAULT '[]',
                    action_items JSONB DEFAULT '[]',
                    gdpr_compliance_score INTEGER,
                    hipaa_compliance_score INTEGER,
                    overall_compliance_score INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    submitted_at TIMESTAMP
                )
            """))
            
            # Create indexes for compliance_reports
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_compliance_reports_user_id 
                ON consent_audit.compliance_reports(user_id)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_compliance_reports_report_type 
                ON consent_audit.compliance_reports(report_type)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_compliance_reports_report_status 
                ON consent_audit.compliance_reports(report_status)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_compliance_reports_period 
                ON consent_audit.compliance_reports(report_period_start, report_period_end)
            """))
            
            await db.commit()
            logger.info("Created consent audit tables successfully")
            
        except Exception as e:
            logger.error(f"Failed to create consent audit tables: {e}")
            await db.rollback()
            raise


async def create_audit_triggers():
    """Create audit triggers for automatic logging."""
    db_manager = get_db_manager()
    
    async with db_manager.get_async_session() as db:
        try:
            # Create function to update updated_at timestamp
            await db.execute(text("""
                CREATE OR REPLACE FUNCTION consent_audit.update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """))
            
            # Create trigger for data_processing_audits
            await db.execute(text("""
                CREATE TRIGGER update_data_processing_audits_updated_at 
                BEFORE UPDATE ON consent_audit.data_processing_audits 
                FOR EACH ROW EXECUTE FUNCTION consent_audit.update_updated_at_column();
            """))
            
            # Create trigger for compliance_reports
            await db.execute(text("""
                CREATE TRIGGER update_compliance_reports_updated_at 
                BEFORE UPDATE ON consent_audit.compliance_reports 
                FOR EACH ROW EXECUTE FUNCTION consent_audit.update_updated_at_column();
            """))
            
            await db.commit()
            logger.info("Created audit triggers successfully")
            
        except Exception as e:
            logger.error(f"Failed to create audit triggers: {e}")
            await db.rollback()
            raise


async def main():
    """Main function to create all database objects."""
    try:
        logger.info("Starting consent audit database setup...")
        
        # Create schema
        await create_consent_audit_schema()
        
        # Create tables
        await create_consent_audit_tables()
        
        # Create triggers
        await create_audit_triggers()
        
        logger.info("Consent audit database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to setup consent audit database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 