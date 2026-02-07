-- Nutrition Service Database Migration
-- Create tables for nutrition service

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Food Recognition Results Table
CREATE TABLE IF NOT EXISTS food_recognition_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) NOT NULL,
    recognition_id VARCHAR(100) UNIQUE NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Image metadata
    image_format VARCHAR(10),
    image_size_bytes INTEGER,
    image_hash VARCHAR(64),
    
    -- Recognition metadata
    models_used JSONB,
    processing_time_ms INTEGER,
    confidence_threshold FLOAT DEFAULT 0.5,
    
    -- Recognition results
    recognized_foods JSONB NOT NULL,
    total_foods_detected INTEGER DEFAULT 0,
    average_confidence FLOAT,
    
    -- User metadata
    meal_type VARCHAR(20),
    cuisine_hint VARCHAR(50),
    region_hint VARCHAR(50),
    dietary_restrictions JSONB,
    preferred_units VARCHAR(10) DEFAULT 'metric',
    
    -- Status and feedback
    is_corrected BOOLEAN DEFAULT FALSE,
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_feedback TEXT
);

-- User Corrections Table
CREATE TABLE IF NOT EXISTS user_corrections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recognition_result_id UUID NOT NULL REFERENCES food_recognition_results(id) ON DELETE CASCADE,
    user_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Correction data
    original_food_name VARCHAR(100) NOT NULL,
    corrected_food_name VARCHAR(100),
    original_portion_g FLOAT,
    corrected_portion_g FLOAT,
    original_confidence FLOAT,
    user_confidence FLOAT DEFAULT 1.0,
    
    -- Correction metadata
    correction_type VARCHAR(20) NOT NULL,
    correction_reason TEXT
);

-- Meal Logs Table
CREATE TABLE IF NOT EXISTS meal_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) NOT NULL,
    recognition_result_id UUID REFERENCES food_recognition_results(id) ON DELETE SET NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Meal metadata
    meal_type VARCHAR(20) NOT NULL,
    meal_name VARCHAR(100),
    meal_description TEXT,
    
    -- Food items
    food_items JSONB NOT NULL,
    
    -- Nutrition totals
    total_calories FLOAT NOT NULL,
    total_protein_g FLOAT NOT NULL,
    total_carbs_g FLOAT NOT NULL,
    total_fat_g FLOAT NOT NULL,
    total_fiber_g FLOAT NOT NULL,
    total_sodium_mg FLOAT NOT NULL,
    total_sugar_g FLOAT NOT NULL,
    micronutrients JSONB,
    
    -- User input
    user_notes TEXT,
    mood_before VARCHAR(20),
    mood_after VARCHAR(20),
    
    -- Integration flags
    synced_to_health_tracking BOOLEAN DEFAULT FALSE,
    synced_to_medical_analysis BOOLEAN DEFAULT FALSE
);

-- Nutrition Goals Table
CREATE TABLE IF NOT EXISTS nutrition_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Goal metadata
    goal_name VARCHAR(100) NOT NULL,
    goal_type VARCHAR(30) NOT NULL,
    goal_description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Target values
    target_calories FLOAT,
    target_protein_g FLOAT,
    target_carbs_g FLOAT,
    target_fat_g FLOAT,
    target_fiber_g FLOAT,
    target_sodium_mg FLOAT,
    
    -- Goal settings
    start_date TIMESTAMP WITH TIME ZONE,
    target_date TIMESTAMP WITH TIME ZONE,
    progress_percentage FLOAT DEFAULT 0.0
);

-- Food Database Table (for caching)
CREATE TABLE IF NOT EXISTS food_database (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    food_name VARCHAR(200) NOT NULL,
    food_category VARCHAR(50),
    source VARCHAR(20) NOT NULL,
    
    -- Nutrition data (per 100g)
    calories_per_100g FLOAT NOT NULL,
    protein_g_per_100g FLOAT NOT NULL,
    carbs_g_per_100g FLOAT NOT NULL,
    fat_g_per_100g FLOAT NOT NULL,
    fiber_g_per_100g FLOAT NOT NULL,
    sodium_mg_per_100g FLOAT NOT NULL,
    sugar_g_per_100g FLOAT NOT NULL,
    micronutrients JSONB,
    
    -- Metadata
    brand_name VARCHAR(100),
    barcode VARCHAR(50),
    serving_size_g FLOAT,
    serving_description VARCHAR(100),
    
    -- Caching
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_accessed TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0
);

-- Model Performance Table
CREATE TABLE IF NOT EXISTS model_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Performance metrics
    accuracy FLOAT,
    processing_time_ms FLOAT,
    success_rate FLOAT,
    error_rate FLOAT,
    
    -- Usage statistics
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    
    -- User feedback
    user_satisfaction_score FLOAT,
    correction_rate FLOAT
);

-- User Preferences Table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Dietary preferences
    dietary_restrictions JSONB,
    allergies JSONB,
    preferred_cuisines JSONB,
    disliked_foods JSONB,
    
    -- Measurement preferences
    preferred_units VARCHAR(10) DEFAULT 'metric',
    calorie_goal FLOAT,
    protein_goal_g FLOAT,
    carb_goal_g FLOAT,
    fat_goal_g FLOAT,
    
    -- Notification preferences
    enable_nutrition_alerts BOOLEAN DEFAULT TRUE,
    enable_meal_reminders BOOLEAN DEFAULT TRUE,
    alert_thresholds JSONB,
    
    -- Recognition preferences
    preferred_recognition_models JSONB,
    confidence_threshold FLOAT DEFAULT 0.7,
    enable_portion_estimation BOOLEAN DEFAULT TRUE
);

-- Create Indexes for better performance

-- Food Recognition Results Indexes
CREATE INDEX IF NOT EXISTS idx_food_recognition_user_timestamp ON food_recognition_results(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_food_recognition_recognition_id ON food_recognition_results(recognition_id);
CREATE INDEX IF NOT EXISTS idx_food_recognition_meal_type ON food_recognition_results(meal_type);
CREATE INDEX IF NOT EXISTS idx_food_recognition_is_corrected ON food_recognition_results(is_corrected);

-- User Corrections Indexes
CREATE INDEX IF NOT EXISTS idx_user_corrections_user_timestamp ON user_corrections(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_user_corrections_recognition_result ON user_corrections(recognition_result_id);
CREATE INDEX IF NOT EXISTS idx_user_corrections_type ON user_corrections(correction_type);

-- Meal Logs Indexes
CREATE INDEX IF NOT EXISTS idx_meal_logs_user_meal_date ON meal_logs(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_meal_logs_meal_type ON meal_logs(meal_type);
CREATE INDEX IF NOT EXISTS idx_meal_logs_recognition_result ON meal_logs(recognition_result_id);
CREATE INDEX IF NOT EXISTS idx_meal_logs_synced_flags ON meal_logs(synced_to_health_tracking, synced_to_medical_analysis);

-- Nutrition Goals Indexes
CREATE INDEX IF NOT EXISTS idx_nutrition_goals_user_active ON nutrition_goals(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_nutrition_goals_type ON nutrition_goals(goal_type);
CREATE INDEX IF NOT EXISTS idx_nutrition_goals_dates ON nutrition_goals(start_date, target_date);

-- Food Database Indexes
CREATE INDEX IF NOT EXISTS idx_food_database_name_category ON food_database(food_name, food_category);
CREATE INDEX IF NOT EXISTS idx_food_database_source ON food_database(source);
CREATE INDEX IF NOT EXISTS idx_food_database_barcode ON food_database(barcode);
CREATE INDEX IF NOT EXISTS idx_food_database_access_count ON food_database(access_count DESC);
CREATE INDEX IF NOT EXISTS idx_food_database_last_accessed ON food_database(last_accessed DESC);

-- Model Performance Indexes
CREATE INDEX IF NOT EXISTS idx_model_performance_model_timestamp ON model_performance(model_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_model_performance_accuracy ON model_performance(model_name, accuracy);
CREATE INDEX IF NOT EXISTS idx_model_performance_processing_time ON model_performance(model_name, processing_time_ms);

-- User Preferences Indexes
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Create Triggers for updated_at timestamps

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for tables with updated_at columns
CREATE TRIGGER update_nutrition_goals_updated_at 
    BEFORE UPDATE ON nutrition_goals 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_food_database_updated_at 
    BEFORE UPDATE ON food_database 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON user_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries

-- Daily Nutrition Summary View
CREATE OR REPLACE VIEW daily_nutrition_summary AS
SELECT 
    user_id,
    DATE(timestamp) as date,
    COUNT(*) as meal_count,
    SUM(total_calories) as total_calories,
    SUM(total_protein_g) as total_protein_g,
    SUM(total_carbs_g) as total_carbs_g,
    SUM(total_fat_g) as total_fat_g,
    SUM(total_fiber_g) as total_fiber_g,
    SUM(total_sodium_mg) as total_sodium_mg,
    SUM(total_sugar_g) as total_sugar_g
FROM meal_logs
GROUP BY user_id, DATE(timestamp);

-- Model Performance Summary View
CREATE OR REPLACE VIEW model_performance_summary AS
SELECT 
    model_name,
    DATE(timestamp) as date,
    COUNT(*) as total_requests,
    AVG(accuracy) as avg_accuracy,
    AVG(processing_time_ms) as avg_processing_time_ms,
    AVG(success_rate) as avg_success_rate,
    AVG(user_satisfaction_score) as avg_satisfaction
FROM model_performance
GROUP BY model_name, DATE(timestamp);

-- User Recognition Statistics View
CREATE OR REPLACE VIEW user_recognition_stats AS
SELECT 
    user_id,
    COUNT(*) as total_recognitions,
    AVG(average_confidence) as avg_confidence,
    COUNT(CASE WHEN is_corrected THEN 1 END) as corrected_count,
    COUNT(CASE WHEN user_rating IS NOT NULL THEN 1 END) as rated_count,
    AVG(user_rating) as avg_rating
FROM food_recognition_results
GROUP BY user_id;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nutrition_service_user;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO nutrition_service_user; 