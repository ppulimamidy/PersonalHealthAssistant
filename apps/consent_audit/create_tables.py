"""
Database migration script for the Personal Health Assistant Consent Audit Service.

This script creates the necessary database tables and schemas for consent audit functionality.
It uses the ORM models defined in models/audit.py to ensure consistency.
"""

import asyncio
import os
import sys
from sqlalchemy import text

# Add the project root to Python path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from common.database.connection import get_db_manager
from common.models.base import Base
from common.utils.logging import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def create_consent_audit_schema():
    """Create the consent_audit schema."""
    db_manager = get_db_manager()

    async with db_manager.get_async_session() as db:
        try:
            await db.execute(text("CREATE SCHEMA IF NOT EXISTS consent_audit"))
            await db.commit()
            logger.info("Created consent_audit schema")
        except Exception as e:
            logger.error(f"Failed to create consent_audit schema: {e}")
            await db.rollback()
            raise


async def create_consent_audit_tables():
    """Create the consent audit tables using raw SQL for maximum control."""
    db_manager = get_db_manager()

    async with db_manager.get_async_session() as db:
        try:
            # ---------------------------------------------------------------
            # consent_audit_logs
            # ---------------------------------------------------------------
            await db.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS consent_audit.consent_audit_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) DEFAULT 'medium' NOT NULL,
                    event_description TEXT NOT NULL,
                    event_data JSONB DEFAULT '{}' NOT NULL,
                    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    session_id UUID,
                    actor_id UUID NOT NULL,
                    actor_type VARCHAR(50) NOT NULL,
                    actor_role VARCHAR(100),
                    consent_record_id UUID,
                    data_subject_id UUID,
                    gdpr_compliant BOOLEAN DEFAULT TRUE NOT NULL,
                    hipaa_compliant BOOLEAN DEFAULT TRUE NOT NULL,
                    compliance_notes TEXT,
                    compliance_issues JSONB DEFAULT '[]' NOT NULL,
                    risk_level VARCHAR(20) DEFAULT 'low' NOT NULL,
                    risk_factors JSONB DEFAULT '[]' NOT NULL,
                    mitigation_actions JSONB DEFAULT '[]' NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """
                )
            )

            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_cal_user_id
                ON consent_audit.consent_audit_logs(user_id)
            """
                )
            )
            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_cal_event_type
                ON consent_audit.consent_audit_logs(event_type)
            """
                )
            )
            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_cal_event_timestamp
                ON consent_audit.consent_audit_logs(event_timestamp)
            """
                )
            )
            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_cal_severity
                ON consent_audit.consent_audit_logs(severity)
            """
                )
            )

            # ---------------------------------------------------------------
            # data_processing_audits
            # ---------------------------------------------------------------
            await db.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS consent_audit.data_processing_audits (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    processing_purpose VARCHAR(50) NOT NULL,
                    processing_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    processing_duration INTEGER,
                    data_categories JSONB DEFAULT '[]' NOT NULL,
                    data_volume INTEGER,
                    data_sensitivity VARCHAR(20) DEFAULT 'medium' NOT NULL,
                    consent_record_id UUID,
                    data_subject_id UUID,
                    processing_method VARCHAR(50) NOT NULL,
                    processing_location VARCHAR(255),
                    processing_tools JSONB DEFAULT '[]' NOT NULL,
                    third_parties_involved JSONB DEFAULT '[]' NOT NULL,
                    data_shared_with JSONB DEFAULT '[]' NOT NULL,
                    legal_basis VARCHAR(100) NOT NULL,
                    consent_verified BOOLEAN DEFAULT FALSE NOT NULL,
                    consent_verification_method VARCHAR(100),
                    compliance_status VARCHAR(30) DEFAULT 'pending_review' NOT NULL,
                    data_encrypted BOOLEAN DEFAULT TRUE NOT NULL,
                    access_controls JSONB DEFAULT '[]' NOT NULL,
                    retention_period INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """
                )
            )

            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_dpa_user_id
                ON consent_audit.data_processing_audits(user_id)
            """
                )
            )
            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_dpa_purpose
                ON consent_audit.data_processing_audits(processing_purpose)
            """
                )
            )
            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_dpa_timestamp
                ON consent_audit.data_processing_audits(processing_timestamp)
            """
                )
            )
            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_dpa_compliance
                ON consent_audit.data_processing_audits(compliance_status)
            """
                )
            )

            # ---------------------------------------------------------------
            # compliance_reports
            # ---------------------------------------------------------------
            await db.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS consent_audit.compliance_reports (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    report_type VARCHAR(50) NOT NULL,
                    framework VARCHAR(20),
                    report_period_start TIMESTAMP NOT NULL,
                    report_period_end TIMESTAMP NOT NULL,
                    report_status VARCHAR(20) DEFAULT 'draft' NOT NULL,
                    user_id UUID,
                    organization_id UUID,
                    scope_description TEXT NOT NULL,
                    total_consents INTEGER DEFAULT 0 NOT NULL,
                    active_consents INTEGER DEFAULT 0 NOT NULL,
                    expired_consents INTEGER DEFAULT 0 NOT NULL,
                    withdrawn_consents INTEGER DEFAULT 0 NOT NULL,
                    compliance_violations INTEGER DEFAULT 0 NOT NULL,
                    security_incidents INTEGER DEFAULT 0 NOT NULL,
                    data_breaches INTEGER DEFAULT 0 NOT NULL,
                    data_processing_events INTEGER DEFAULT 0 NOT NULL,
                    data_sharing_events INTEGER DEFAULT 0 NOT NULL,
                    data_access_events INTEGER DEFAULT 0 NOT NULL,
                    executive_summary TEXT,
                    detailed_findings JSONB DEFAULT '{}' NOT NULL,
                    recommendations JSONB DEFAULT '[]' NOT NULL,
                    action_items JSONB DEFAULT '[]' NOT NULL,
                    gdpr_compliance_score INTEGER,
                    hipaa_compliance_score INTEGER,
                    overall_compliance_score INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    submitted_at TIMESTAMP
                )
            """
                )
            )

            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_cr_report_type
                ON consent_audit.compliance_reports(report_type)
            """
                )
            )
            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_cr_framework
                ON consent_audit.compliance_reports(framework)
            """
                )
            )
            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_cr_status
                ON consent_audit.compliance_reports(report_status)
            """
                )
            )
            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_cr_period
                ON consent_audit.compliance_reports(report_period_start, report_period_end)
            """
                )
            )

            # ---------------------------------------------------------------
            # consent_records
            # ---------------------------------------------------------------
            await db.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS consent_audit.consent_records (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    consent_type VARCHAR(100) NOT NULL,
                    purpose VARCHAR(255) NOT NULL,
                    granted BOOLEAN DEFAULT TRUE NOT NULL,
                    granted_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    revoked_at TIMESTAMP,
                    version VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """
                )
            )

            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_crec_user_id
                ON consent_audit.consent_records(user_id)
            """
                )
            )
            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_crec_consent_type
                ON consent_audit.consent_records(consent_type)
            """
                )
            )
            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_crec_granted
                ON consent_audit.consent_records(granted)
            """
                )
            )

            await db.commit()
            logger.info("Created consent audit tables successfully")

        except Exception as e:
            logger.error(f"Failed to create consent audit tables: {e}")
            await db.rollback()
            raise


async def create_audit_triggers():
    """Create audit triggers for automatic updated_at management."""
    db_manager = get_db_manager()

    async with db_manager.get_async_session() as db:
        try:
            # Create function to update updated_at timestamp
            await db.execute(
                text(
                    """
                CREATE OR REPLACE FUNCTION consent_audit.update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """
                )
            )

            # Triggers for tables that have updated_at
            for table in (
                "data_processing_audits",
                "compliance_reports",
                "consent_records",
            ):
                trigger_name = f"update_{table}_updated_at"
                await db.execute(
                    text(
                        f"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_trigger WHERE tgname = '{trigger_name}'
                        ) THEN
                            CREATE TRIGGER {trigger_name}
                            BEFORE UPDATE ON consent_audit.{table}
                            FOR EACH ROW EXECUTE FUNCTION consent_audit.update_updated_at_column();
                        END IF;
                    END $$;
                """
                    )
                )

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
