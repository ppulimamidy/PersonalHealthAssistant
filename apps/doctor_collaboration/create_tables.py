"""
Database setup script for Doctor Collaboration Service.

This script creates all necessary database tables and schemas.
"""

import asyncio
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from common.config.settings import get_settings
from common.utils.logging import get_logger, setup_logging
from apps.doctor_collaboration.models.appointment import Appointment
from apps.doctor_collaboration.models.messaging import Message
from apps.doctor_collaboration.models.consultation import Consultation
from apps.doctor_collaboration.models.notification import Notification

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Get settings
settings = get_settings()


def create_schema():
    """Create the doctor_collaboration schema."""
    try:
        # Create database engine
        engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG
        )
        
        # Create schema
        with engine.connect() as conn:
            # Create schema if it doesn't exist
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS doctor_collaboration"))
            conn.commit()
            
        logger.info("Schema 'doctor_collaboration' created successfully")
        
    except Exception as e:
        logger.error(f"Error creating schema: {e}")
        raise


def create_tables():
    """Create all database tables."""
    try:
        # Create database engine
        engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG
        )
        
        # Import all models to ensure they are registered
        from apps.doctor_collaboration.models import *
        
        # Create all tables
        from common.models.base import Base
        Base.metadata.create_all(bind=engine)
        
        logger.info("All tables created successfully")
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise


def create_indexes():
    """Create database indexes for better performance."""
    try:
        # Create database engine
        engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG
        )
        
        with engine.connect() as conn:
            # Create indexes for appointments
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_appointments_patient_id 
                ON doctor_collaboration.appointments(patient_id)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_appointments_doctor_id 
                ON doctor_collaboration.appointments(doctor_id)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_appointments_scheduled_date 
                ON doctor_collaboration.appointments(scheduled_date)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_appointments_status 
                ON doctor_collaboration.appointments(status)
            """))
            
            # Create indexes for messages
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_sender_id 
                ON doctor_collaboration.messages(sender_id)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_recipient_id 
                ON doctor_collaboration.messages(recipient_id)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_sent_at 
                ON doctor_collaboration.messages(sent_at)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_status 
                ON doctor_collaboration.messages(status)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_thread_id 
                ON doctor_collaboration.messages(thread_id)
            """))
            
            # Create indexes for consultations
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_consultations_patient_id 
                ON doctor_collaboration.consultations(patient_id)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_consultations_doctor_id 
                ON doctor_collaboration.consultations(doctor_id)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_consultations_scheduled_date 
                ON doctor_collaboration.consultations(scheduled_date)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_consultations_status 
                ON doctor_collaboration.consultations(status)
            """))
            
            # Create indexes for notifications
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notifications_recipient_id 
                ON doctor_collaboration.notifications(recipient_id)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notifications_created_at 
                ON doctor_collaboration.notifications(created_at)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notifications_status 
                ON doctor_collaboration.notifications(status)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notifications_type 
                ON doctor_collaboration.notifications(notification_type)
            """))
            
            conn.commit()
            
        logger.info("All indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        raise


def create_sample_data():
    """Create sample data for testing."""
    try:
        # Create database engine
        engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG
        )
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Check if sample data already exists
            existing_appointments = db.query(Appointment).count()
            if existing_appointments > 0:
                logger.info("Sample data already exists, skipping creation")
                return
            
            # Create sample appointments
            from datetime import datetime, timedelta
            from apps.doctor_collaboration.models.appointment import AppointmentStatus, AppointmentType
            import uuid
            
            # Sample user IDs (these would typically come from the auth service)
            sample_patient_id = uuid.uuid4()
            sample_doctor_id = uuid.uuid4()
            
            # Create sample appointments
            sample_appointments = [
                Appointment(
                    id=uuid.uuid4(),
                    patient_id=sample_patient_id,
                    doctor_id=sample_doctor_id,
                    appointment_type=AppointmentType.CONSULTATION,
                    status=AppointmentStatus.SCHEDULED,
                    scheduled_date=datetime.utcnow() + timedelta(days=1),
                    duration_minutes=30,
                    timezone="UTC",
                    location="Virtual Consultation",
                    modality="telemedicine",
                    notes="Initial consultation",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Appointment(
                    id=uuid.uuid4(),
                    patient_id=sample_patient_id,
                    doctor_id=sample_doctor_id,
                    appointment_type=AppointmentType.FOLLOW_UP,
                    status=AppointmentStatus.CONFIRMED,
                    scheduled_date=datetime.utcnow() + timedelta(days=3),
                    duration_minutes=45,
                    timezone="UTC",
                    location="Office Visit",
                    modality="in_person",
                    notes="Follow-up appointment",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            ]
            
            # Create sample messages
            from apps.doctor_collaboration.models.messaging import MessageStatus, MessageType, MessagePriority
            
            sample_messages = [
                Message(
                    id=uuid.uuid4(),
                    sender_id=sample_doctor_id,
                    recipient_id=sample_patient_id,
                    message_type=MessageType.TEXT,
                    priority=MessagePriority.NORMAL,
                    status=MessageStatus.DELIVERED,
                    content="Hello! I wanted to check in on your progress.",
                    subject="Progress Check",
                    sent_at=datetime.utcnow() - timedelta(hours=2),
                    delivered_at=datetime.utcnow() - timedelta(hours=1),
                    created_at=datetime.utcnow() - timedelta(hours=2),
                    updated_at=datetime.utcnow() - timedelta(hours=1)
                ),
                Message(
                    id=uuid.uuid4(),
                    sender_id=sample_patient_id,
                    recipient_id=sample_doctor_id,
                    message_type=MessageType.TEXT,
                    priority=MessagePriority.NORMAL,
                    status=MessageStatus.SENT,
                    content="Thank you! I'm feeling much better now.",
                    subject="Re: Progress Check",
                    sent_at=datetime.utcnow() - timedelta(hours=1),
                    created_at=datetime.utcnow() - timedelta(hours=1),
                    updated_at=datetime.utcnow() - timedelta(hours=1)
                )
            ]
            
            # Create sample consultations
            from apps.doctor_collaboration.models.consultation import ConsultationStatus, ConsultationType, ConsultationPriority
            
            sample_consultations = [
                Consultation(
                    id=uuid.uuid4(),
                    patient_id=sample_patient_id,
                    doctor_id=sample_doctor_id,
                    consultation_type=ConsultationType.INITIAL,
                    status=ConsultationStatus.COMPLETED,
                    priority=ConsultationPriority.NORMAL,
                    scheduled_date=datetime.utcnow() - timedelta(days=7),
                    duration_minutes=30,
                    timezone="UTC",
                    location="Virtual Consultation",
                    modality="telemedicine",
                    chief_complaint="General health check",
                    started_at=datetime.utcnow() - timedelta(days=7),
                    completed_at=datetime.utcnow() - timedelta(days=7, minutes=-25),
                    created_at=datetime.utcnow() - timedelta(days=7),
                    updated_at=datetime.utcnow() - timedelta(days=7)
                )
            ]
            
            # Create sample notifications
            from apps.doctor_collaboration.models.notification import NotificationStatus, NotificationType, NotificationPriority, NotificationChannel
            
            sample_notifications = [
                Notification(
                    id=uuid.uuid4(),
                    recipient_id=sample_patient_id,
                    notification_type=NotificationType.APPOINTMENT,
                    priority=NotificationPriority.NORMAL,
                    status=NotificationStatus.DELIVERED,
                    title="Appointment Reminder",
                    content="You have an appointment tomorrow at 10:00 AM",
                    channel=NotificationChannel.EMAIL,
                    sent_at=datetime.utcnow() - timedelta(hours=6),
                    delivered_at=datetime.utcnow() - timedelta(hours=5),
                    created_at=datetime.utcnow() - timedelta(hours=6),
                    updated_at=datetime.utcnow() - timedelta(hours=5)
                ),
                Notification(
                    id=uuid.uuid4(),
                    recipient_id=sample_patient_id,
                    notification_type=NotificationType.MESSAGE,
                    priority=NotificationPriority.NORMAL,
                    status=NotificationStatus.DELIVERED,
                    title="New Message",
                    content="You have received a new message from your doctor",
                    channel=NotificationChannel.PUSH,
                    sent_at=datetime.utcnow() - timedelta(hours=2),
                    delivered_at=datetime.utcnow() - timedelta(hours=1),
                    created_at=datetime.utcnow() - timedelta(hours=2),
                    updated_at=datetime.utcnow() - timedelta(hours=1)
                )
            ]
            
            # Add all sample data to database
            db.add_all(sample_appointments)
            db.add_all(sample_messages)
            db.add_all(sample_consultations)
            db.add_all(sample_notifications)
            
            db.commit()
            
            logger.info("Sample data created successfully")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating sample data: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        raise


def verify_database():
    """Verify database setup."""
    try:
        # Create database engine
        engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG
        )
        
        with engine.connect() as conn:
            # Check if schema exists
            result = conn.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = 'doctor_collaboration'
            """))
            
            if not result.fetchone():
                raise Exception("Schema 'doctor_collaboration' does not exist")
            
            # Check if tables exist
            tables = ['appointments', 'messages', 'consultations', 'notifications']
            for table in tables:
                result = conn.execute(text(f"""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'doctor_collaboration' 
                    AND table_name = '{table}'
                """))
                
                if not result.fetchone():
                    raise Exception(f"Table '{table}' does not exist")
            
            # Check if indexes exist
            indexes = [
                'idx_appointments_patient_id',
                'idx_messages_sender_id',
                'idx_consultations_patient_id',
                'idx_notifications_recipient_id'
            ]
            
            for index in indexes:
                result = conn.execute(text(f"""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE schemaname = 'doctor_collaboration' 
                    AND indexname = '{index}'
                """))
                
                if not result.fetchone():
                    logger.warning(f"Index '{index}' does not exist")
            
        logger.info("Database verification completed successfully")
        
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        raise


def main():
    """Main function to set up the database."""
    try:
        logger.info("Starting database setup for Doctor Collaboration Service...")
        
        # Create schema
        logger.info("Creating schema...")
        create_schema()
        
        # Create tables
        logger.info("Creating tables...")
        create_tables()
        
        # Create indexes
        logger.info("Creating indexes...")
        create_indexes()
        
        # Create sample data (optional)
        logger.info("Creating sample data...")
        create_sample_data()
        
        # Verify setup
        logger.info("Verifying database setup...")
        verify_database()
        
        logger.info("Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 