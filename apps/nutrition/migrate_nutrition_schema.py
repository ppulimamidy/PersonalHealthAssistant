#!/usr/bin/env python3
"""
Simple Database Migration Script for Nutrition Service

This script creates the nutrition schema and tables in the existing database.
"""

import os
import sys
import logging
from pathlib import Path
from sqlalchemy import create_engine, text

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_nutrition_schema():
    """Create nutrition schema and tables."""
    try:
        logger.info("Starting nutrition schema migration...")
        
        # Database connection
        DATABASE_URL = "postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:5432/health_assistant"
        
        # Create engine
        engine = create_engine(DATABASE_URL, echo=True)
        
        # Create schema and tables
        with engine.connect() as connection:
            # Create schema
            logger.info("Creating nutrition schema...")
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS nutrition"))
            connection.commit()
            
            # Create tables
            logger.info("Creating nutrition tables...")
            
            # Food Recognition Results Table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS nutrition.food_recognition_results (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id VARCHAR(50) NOT NULL,
                    recognition_id VARCHAR(100) UNIQUE NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    image_format VARCHAR(10),
                    image_size_bytes INTEGER,
                    image_hash VARCHAR(64),
                    models_used JSONB,
                    processing_time_ms INTEGER,
                    confidence_threshold FLOAT DEFAULT 0.5,
                    recognized_foods JSONB NOT NULL,
                    total_foods_detected INTEGER DEFAULT 0,
                    average_confidence FLOAT,
                    meal_type VARCHAR(20),
                    cuisine_hint VARCHAR(50),
                    region_hint VARCHAR(50),
                    dietary_restrictions JSONB,
                    preferred_units VARCHAR(10) DEFAULT 'metric',
                    is_corrected BOOLEAN DEFAULT FALSE,
                    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
                    user_feedback TEXT
                )
            """))
            
            # User Corrections Table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS nutrition.user_corrections (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    recognition_result_id UUID NOT NULL REFERENCES nutrition.food_recognition_results(id) ON DELETE CASCADE,
                    user_id VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    original_food_name VARCHAR(100) NOT NULL,
                    corrected_food_name VARCHAR(100),
                    original_portion_g FLOAT,
                    corrected_portion_g FLOAT,
                    original_confidence FLOAT,
                    user_confidence FLOAT DEFAULT 1.0,
                    correction_type VARCHAR(20) NOT NULL,
                    correction_reason TEXT
                )
            """))
            
            # Meal Logs Table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS nutrition.meal_logs (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id VARCHAR(50) NOT NULL,
                    recognition_result_id UUID REFERENCES nutrition.food_recognition_results(id) ON DELETE SET NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    meal_type VARCHAR(20) NOT NULL,
                    meal_name VARCHAR(100),
                    meal_description TEXT,
                    food_items JSONB NOT NULL,
                    total_calories FLOAT NOT NULL,
                    total_protein_g FLOAT NOT NULL,
                    total_carbs_g FLOAT NOT NULL,
                    total_fat_g FLOAT NOT NULL,
                    total_fiber_g FLOAT NOT NULL,
                    total_sodium_mg FLOAT NOT NULL,
                    total_sugar_g FLOAT NOT NULL,
                    micronutrients JSONB,
                    user_notes TEXT,
                    mood_before VARCHAR(20),
                    mood_after VARCHAR(20),
                    synced_to_health_tracking BOOLEAN DEFAULT FALSE,
                    synced_to_medical_analysis BOOLEAN DEFAULT FALSE
                )
            """))
            
            # Nutrition Goals Table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS nutrition.nutrition_goals (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    goal_name VARCHAR(100) NOT NULL,
                    goal_type VARCHAR(30) NOT NULL,
                    goal_description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    target_calories FLOAT,
                    target_protein_g FLOAT,
                    target_carbs_g FLOAT,
                    target_fat_g FLOAT,
                    target_fiber_g FLOAT,
                    target_sodium_mg FLOAT,
                    start_date TIMESTAMP WITH TIME ZONE,
                    target_date TIMESTAMP WITH TIME ZONE,
                    progress_percentage FLOAT DEFAULT 0.0
                )
            """))
            
            # Food Database Table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS nutrition.food_database (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    food_name VARCHAR(200) NOT NULL,
                    food_category VARCHAR(50),
                    source VARCHAR(20) NOT NULL,
                    calories_per_100g FLOAT NOT NULL,
                    protein_g_per_100g FLOAT NOT NULL,
                    carbs_g_per_100g FLOAT NOT NULL,
                    fat_g_per_100g FLOAT NOT NULL,
                    fiber_g_per_100g FLOAT NOT NULL,
                    sodium_mg_per_100g FLOAT NOT NULL,
                    sugar_g_per_100g FLOAT NOT NULL,
                    micronutrients JSONB,
                    brand_name VARCHAR(100),
                    barcode VARCHAR(50),
                    serving_size_g FLOAT,
                    serving_description VARCHAR(100),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    last_accessed TIMESTAMP WITH TIME ZONE,
                    access_count INTEGER DEFAULT 0
                )
            """))
            
            # Model Performance Table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS nutrition.model_performance (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    model_name VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    accuracy FLOAT,
                    processing_time_ms FLOAT,
                    success_rate FLOAT,
                    error_rate FLOAT,
                    total_requests INTEGER DEFAULT 0,
                    successful_requests INTEGER DEFAULT 0,
                    failed_requests INTEGER DEFAULT 0,
                    user_satisfaction_score FLOAT,
                    correction_rate FLOAT
                )
            """))
            
            # User Preferences Table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS nutrition.user_preferences (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id VARCHAR(50) UNIQUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    dietary_restrictions JSONB,
                    allergies JSONB,
                    preferred_cuisines JSONB,
                    disliked_foods JSONB,
                    preferred_units VARCHAR(10) DEFAULT 'metric',
                    calorie_goal FLOAT,
                    protein_goal_g FLOAT,
                    carb_goal_g FLOAT,
                    fat_goal_g FLOAT,
                    enable_nutrition_alerts BOOLEAN DEFAULT TRUE,
                    enable_meal_reminders BOOLEAN DEFAULT TRUE,
                    alert_thresholds JSONB,
                    preferred_recognition_models JSONB,
                    confidence_threshold FLOAT DEFAULT 0.7,
                    enable_portion_estimation BOOLEAN DEFAULT TRUE
                )
            """))
            
            connection.commit()
        
        logger.info("✅ Nutrition schema and tables created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

def create_indexes():
    """Create indexes for better performance."""
    try:
        logger.info("Creating nutrition indexes...")
        
        DATABASE_URL = "postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:5432/health_assistant"
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Food Recognition Results Indexes
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_nutrition_food_recognition_user_timestamp ON nutrition.food_recognition_results(user_id, timestamp)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_nutrition_food_recognition_recognition_id ON nutrition.food_recognition_results(recognition_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_nutrition_food_recognition_meal_type ON nutrition.food_recognition_results(meal_type)"))
            
            # Meal Logs Indexes
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_nutrition_meal_logs_user_meal_date ON nutrition.meal_logs(user_id, timestamp)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_nutrition_meal_logs_meal_type ON nutrition.meal_logs(meal_type)"))
            
            # Nutrition Goals Indexes
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_nutrition_goals_user_active ON nutrition.nutrition_goals(user_id, is_active)"))
            
            # Food Database Indexes
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_nutrition_food_database_name_category ON nutrition.food_database(food_name, food_category)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_nutrition_food_database_barcode ON nutrition.food_database(barcode)"))
            
            # User Preferences Indexes
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_nutrition_user_preferences_user_id ON nutrition.user_preferences(user_id)"))
            
            connection.commit()
        
        logger.info("✅ Nutrition indexes created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Index creation failed: {e}")
        return False

def verify_tables():
    """Verify that all tables were created successfully."""
    try:
        logger.info("Verifying nutrition tables...")
        
        DATABASE_URL = "postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:5432/health_assistant"
        engine = create_engine(DATABASE_URL)
        
        expected_tables = [
            "food_recognition_results",
            "user_corrections", 
            "meal_logs",
            "nutrition_goals",
            "food_database",
            "model_performance",
            "user_preferences"
        ]
        
        with engine.connect() as connection:
            for table_name in expected_tables:
                result = connection.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'nutrition' 
                        AND table_name = '{table_name}'
                    );
                """))
                
                exists = result.fetchone()[0]
                if exists:
                    logger.info(f"✓ Table 'nutrition.{table_name}' exists")
                else:
                    logger.error(f"✗ Table 'nutrition.{table_name}' missing")
                    return False
        
        logger.info("✅ All nutrition tables verified successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def main():
    """Main migration function."""
    logger.info("🚀 Starting Nutrition Schema Migration")
    
    # Create schema and tables
    if not create_nutrition_schema():
        logger.error("❌ Failed to create nutrition schema")
        sys.exit(1)
    
    # Create indexes
    if not create_indexes():
        logger.error("❌ Failed to create indexes")
        sys.exit(1)
    
    # Verify tables
    if not verify_tables():
        logger.error("❌ Failed to verify tables")
        sys.exit(1)
    
    logger.info("🎉 Nutrition Schema Migration Completed Successfully!")

if __name__ == "__main__":
    main() 