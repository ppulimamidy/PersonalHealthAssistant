"""
Database Models for Nutrition Service

SQLAlchemy models for nutrition data storage and management.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Boolean,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from common.models.base import Base


class FoodRecognitionResult(Base):
    """Model for storing food recognition results."""

    __tablename__ = "food_recognition_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(50), nullable=False, index=True)
    recognition_id = Column(String(100), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Image metadata
    image_format = Column(String(10), nullable=True)
    image_size_bytes = Column(Integer, nullable=True)
    image_hash = Column(String(64), nullable=True)

    # Recognition metadata
    models_used = Column(JSON, nullable=True)  # List of models used
    processing_time_ms = Column(Integer, nullable=True)
    confidence_threshold = Column(Float, default=0.5)

    # Recognition results
    recognized_foods = Column(JSON, nullable=False)  # Array of recognized food items
    total_foods_detected = Column(Integer, default=0)
    average_confidence = Column(Float, nullable=True)

    # User metadata
    meal_type = Column(String(20), nullable=True)  # breakfast, lunch, dinner, snack
    cuisine_hint = Column(String(50), nullable=True)
    region_hint = Column(String(50), nullable=True)
    dietary_restrictions = Column(JSON, nullable=True)  # Array of restrictions
    preferred_units = Column(String(10), default="metric")

    # Status and feedback
    is_corrected = Column(Boolean, default=False)
    user_rating = Column(Integer, nullable=True)
    user_feedback = Column(Text, nullable=True)

    # Relationships
    corrections = relationship(
        "UserCorrection",
        back_populates="recognition_result",
        cascade="all, delete-orphan",
    )
    meal_logs = relationship("MealLog", back_populates="recognition_result")

    # Indexes and schema
    __table_args__ = (
        Index("idx_food_recognition_user_timestamp", "user_id", "timestamp"),
        Index("idx_food_recognition_recognition_id", "recognition_id"),
        Index("idx_food_recognition_meal_type", "meal_type"),
        Index("idx_food_recognition_is_corrected", "is_corrected"),
        {"schema": "nutrition"},
    )


class UserCorrection(Base):
    """Model for storing user corrections to recognition results."""

    __tablename__ = "user_corrections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recognition_result_id = Column(
        UUID(as_uuid=True),
        ForeignKey("nutrition.food_recognition_results.id"),
        nullable=False,
    )
    user_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Correction data
    original_food_name = Column(String(100), nullable=False)
    corrected_food_name = Column(String(100), nullable=True)
    original_portion_g = Column(Float, nullable=True)
    corrected_portion_g = Column(Float, nullable=True)
    original_confidence = Column(Float, nullable=True)
    user_confidence = Column(Float, default=1.0)

    # Correction metadata
    correction_type = Column(String(20), nullable=False)  # add, remove, modify, portion
    correction_reason = Column(Text, nullable=True)

    # Relationships
    recognition_result = relationship(
        "FoodRecognitionResult", back_populates="corrections"
    )

    # Indexes and schema
    __table_args__ = (
        Index("idx_user_correction_user_timestamp", "user_id", "timestamp"),
        Index("idx_user_correction_recognition_result", "recognition_result_id"),
        Index("idx_user_correction_type", "correction_type"),
        {"schema": "nutrition"},
    )


class MealLog(Base):
    """Model for storing meal logs."""

    __tablename__ = "meal_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(50), nullable=False, index=True)
    recognition_result_id = Column(
        UUID(as_uuid=True),
        ForeignKey("nutrition.food_recognition_results.id"),
        nullable=True,
    )
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Meal metadata
    meal_type = Column(String(20), nullable=False)  # breakfast, lunch, dinner, snack
    meal_name = Column(String(100), nullable=True)
    meal_description = Column(Text, nullable=True)

    # Food items
    food_items = Column(JSON, nullable=False)  # Array of food items with nutrition data

    # Nutrition totals
    total_calories = Column(Float, nullable=False)
    total_protein_g = Column(Float, nullable=False)
    total_carbs_g = Column(Float, nullable=False)
    total_fat_g = Column(Float, nullable=False)
    total_fiber_g = Column(Float, nullable=False)
    total_sodium_mg = Column(Float, nullable=False)
    total_sugar_g = Column(Float, nullable=False)
    micronutrients = Column(JSON, nullable=True)

    # User input
    user_notes = Column(Text, nullable=True)
    mood_before = Column(String(20), nullable=True)
    mood_after = Column(String(20), nullable=True)

    # Integration flags
    synced_to_health_tracking = Column(Boolean, default=False)
    synced_to_medical_analysis = Column(Boolean, default=False)

    # Relationships
    recognition_result = relationship(
        "FoodRecognitionResult", back_populates="meal_logs"
    )

    # Indexes and schema
    __table_args__ = (
        Index("idx_meal_log_user_timestamp", "user_id", "timestamp"),
        Index("idx_meal_log_meal_type", "meal_type"),
        Index("idx_meal_log_recognition_result", "recognition_result_id"),
        Index(
            "idx_meal_log_synced_flags",
            "synced_to_health_tracking",
            "synced_to_medical_analysis",
        ),
        {"schema": "nutrition"},
    )


class NutritionGoal(Base):
    """Model for storing user nutrition goals."""

    __tablename__ = "nutrition_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Goal metadata
    goal_name = Column(String(100), nullable=False)
    goal_type = Column(
        String(30), nullable=False
    )  # weight_loss, muscle_gain, maintenance, health_improvement
    goal_description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Target values
    target_calories = Column(Float, nullable=True)
    target_protein_g = Column(Float, nullable=True)
    target_carbs_g = Column(Float, nullable=True)
    target_fat_g = Column(Float, nullable=True)
    target_fiber_g = Column(Float, nullable=True)
    target_sodium_mg = Column(Float, nullable=True)

    # Goal settings
    start_date = Column(DateTime, nullable=True)
    target_date = Column(DateTime, nullable=True)
    progress_percentage = Column(Float, default=0.0)

    # Indexes and schema
    __table_args__ = (
        Index("idx_user_active_goals", "user_id", "is_active"),
        Index("idx_goal_type", "goal_type"),
        Index("idx_goal_dates", "start_date", "target_date"),
        {"schema": "nutrition"},
    )


class FoodDatabase(Base):
    """Model for caching food database entries."""

    __tablename__ = "food_database"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    food_name = Column(String(200), nullable=False, index=True)
    food_category = Column(String(50), nullable=True, index=True)
    source = Column(String(20), nullable=False)  # nutritionix, usda, custom

    # Nutrition data (per 100g)
    calories_per_100g = Column(Float, nullable=False)
    protein_g_per_100g = Column(Float, nullable=False)
    carbs_g_per_100g = Column(Float, nullable=False)
    fat_g_per_100g = Column(Float, nullable=False)
    fiber_g_per_100g = Column(Float, nullable=False)
    sodium_mg_per_100g = Column(Float, nullable=False)
    sugar_g_per_100g = Column(Float, nullable=False)
    micronutrients = Column(JSON, nullable=True)

    # Metadata
    brand_name = Column(String(100), nullable=True)
    barcode = Column(String(50), nullable=True, index=True)
    serving_size_g = Column(Float, nullable=True)
    serving_description = Column(String(100), nullable=True)

    # Caching
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_accessed = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0)

    # Indexes and schema
    __table_args__ = (
        Index("idx_food_name_category", "food_name", "food_category"),
        Index("idx_source", "source"),
        Index("idx_barcode", "barcode"),
        Index(
            "idx_access_count", "access_count", postgresql_ops={"access_count": "DESC"}
        ),
        Index(
            "idx_last_accessed",
            "last_accessed",
            postgresql_ops={"last_accessed": "DESC"},
        ),
        {"schema": "nutrition"},
    )


class ModelPerformance(Base):
    """Model for tracking model performance metrics."""

    __tablename__ = "model_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Performance metrics
    accuracy = Column(Float, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    success_rate = Column(Float, nullable=True)
    error_rate = Column(Float, nullable=True)

    # Usage statistics
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)

    # User feedback
    user_satisfaction_score = Column(Float, nullable=True)
    correction_rate = Column(Float, nullable=True)

    # Indexes and schema
    __table_args__ = (
        Index("idx_model_timestamp", "model_name", "timestamp"),
        Index("idx_model_accuracy", "model_name", "accuracy"),
        Index("idx_model_processing_time", "model_name", "processing_time_ms"),
        {"schema": "nutrition"},
    )


class UserPreferences(Base):
    """Model for storing user nutrition preferences."""

    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(50), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Dietary preferences
    dietary_restrictions = Column(JSON, nullable=True)  # Array of restrictions
    allergies = Column(JSON, nullable=True)  # Array of allergies
    preferred_cuisines = Column(JSON, nullable=True)  # Array of preferred cuisines
    disliked_foods = Column(JSON, nullable=True)  # Array of disliked foods

    # Measurement preferences
    preferred_units = Column(String(10), default="metric")  # metric, imperial
    calorie_goal = Column(Float, nullable=True)
    protein_goal_g = Column(Float, nullable=True)
    carb_goal_g = Column(Float, nullable=True)
    fat_goal_g = Column(Float, nullable=True)

    # Notification preferences
    enable_nutrition_alerts = Column(Boolean, default=True)
    enable_meal_reminders = Column(Boolean, default=True)
    alert_thresholds = Column(JSON, nullable=True)  # Custom alert thresholds

    # Recognition preferences
    preferred_recognition_models = Column(
        JSON, nullable=True
    )  # Array of preferred models
    confidence_threshold = Column(Float, default=0.7)
    enable_portion_estimation = Column(Boolean, default=True)

    # Indexes and schema
    __table_args__ = (
        Index("idx_user_preferences_user_id", "user_id"),
        {"schema": "nutrition"},
    )
