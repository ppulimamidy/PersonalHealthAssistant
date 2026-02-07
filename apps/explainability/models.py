"""
Explainability SQLAlchemy Models

Database models for the explainability (XAI) microservice including
explanations and model cards.
"""

from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from common.models.base import Base
import uuid
from datetime import datetime


class Explanation(Base):
    __tablename__ = "explanations"
    __table_args__ = {"schema": "explainability"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    explanation_type = Column(String)  # prediction, recommendation
    model_id = Column(String)
    input_data = Column(JSON)
    output_data = Column(JSON)
    feature_importance = Column(JSON)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelCard(Base):
    __tablename__ = "model_cards"
    __table_args__ = {"schema": "explainability"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String, unique=True)
    description = Column(String)
    version = Column(String)
    intended_use = Column(String)
    limitations = Column(String)
    training_data_summary = Column(String)
    performance_metrics = Column(JSON)
    ethical_considerations = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
