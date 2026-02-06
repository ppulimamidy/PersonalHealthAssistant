-- PostgreSQL Extensions for Personal Health Assistant
-- Essential extensions that work with TimescaleDB x86_64 image

-- Core Extensions (already available in TimescaleDB)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Text Search & Matching Extensions (Compatible)
CREATE EXTENSION IF NOT EXISTS pg_trgm;                   -- For fuzzy text matching and similarity
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;             -- For string similarity and fuzzy matching
CREATE EXTENSION IF NOT EXISTS unaccent;                  -- Remove accents for better search

-- JSON & Data Processing Extensions (Compatible)
CREATE EXTENSION IF NOT EXISTS hstore;                    -- Key-value store for flexible data
CREATE EXTENSION IF NOT EXISTS citext;                    -- Case-insensitive text type
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;        -- Query performance monitoring
CREATE EXTENSION IF NOT EXISTS tablefunc;                 -- Table functions for data analysis
CREATE EXTENSION IF NOT EXISTS ltree;                     -- Hierarchical tree structures
CREATE EXTENSION IF NOT EXISTS pg_visibility;             -- Visibility map utilities
CREATE EXTENSION IF NOT EXISTS pg_prewarm;                -- Preload data into buffer cache
CREATE EXTENSION IF NOT EXISTS postgres_fdw;              -- Foreign data wrapper
CREATE EXTENSION IF NOT EXISTS file_fdw;                  -- File foreign data wrapper

-- TimescaleDB is already installed and configured
-- CREATE EXTENSION IF NOT EXISTS timescaledb;           -- Time-series database extension

-- Note: http and pgaudit extensions are not available in TimescaleDB image
-- CREATE EXTENSION IF NOT EXISTS http;                  -- Not available in this image
-- CREATE EXTENSION IF NOT EXISTS pgaudit;               -- Not available in this image
-- These would need to be installed separately if required

-- Time Series & Analytics Extensions (Compatible)
CREATE EXTENSION IF NOT EXISTS tsm_system_rows;           -- System sampling for analytics
CREATE EXTENSION IF NOT EXISTS tsm_system_time;           -- Time-based sampling

-- Statistical & Mathematical Extensions (Compatible)
CREATE EXTENSION IF NOT EXISTS tsm_system_rows;           -- System sampling for analytics
CREATE EXTENSION IF NOT EXISTS tsm_system_time;           -- Time-based sampling

-- Data Validation & Quality Extensions (Compatible)
CREATE EXTENSION IF NOT EXISTS ltree;                     -- Hierarchical tree structures

-- Performance & Monitoring Extensions (Compatible)
CREATE EXTENSION IF NOT EXISTS pg_visibility;             -- Visibility map information
CREATE EXTENSION IF NOT EXISTS pg_prewarm;                -- Preload data into buffer cache

-- Data Integration Extensions (Compatible)
CREATE EXTENSION IF NOT EXISTS postgres_fdw;              -- Foreign data wrapper for PostgreSQL
CREATE EXTENSION IF NOT EXISTS file_fdw;                  -- File foreign data wrapper
-- CREATE EXTENSION IF NOT EXISTS http;                      -- HTTP client for external APIs

-- Security & Audit Extensions (Compatible)
-- CREATE EXTENSION IF NOT EXISTS pgaudit;                   -- Comprehensive audit logging

-- Custom Functions for Health Analytics
CREATE OR REPLACE FUNCTION public.calculate_bmi(weight_kg DECIMAL, height_m DECIMAL)
RETURNS DECIMAL AS $$
BEGIN
    RETURN weight_kg / (height_m * height_m);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to calculate age from date of birth
CREATE OR REPLACE FUNCTION public.calculate_age(birth_date DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN EXTRACT(YEAR FROM AGE(birth_date));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to get health metrics trend
CREATE OR REPLACE FUNCTION public.get_health_trend(
    p_user_id UUID,
    p_metric_type TEXT,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    date_bucket DATE,
    avg_value DECIMAL,
    min_value DECIMAL,
    max_value DECIMAL,
    count_readings INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE(recorded_at) as date_bucket,
        AVG(value) as avg_value,
        MIN(value) as min_value,
        MAX(value) as max_value,
        COUNT(*) as count_readings
    FROM public.health_metrics
    WHERE user_id = p_user_id 
        AND metric_type = p_metric_type
        AND recorded_at >= CURRENT_DATE - INTERVAL '1 day' * p_days
    GROUP BY DATE(recorded_at)
    ORDER BY date_bucket;
END;
$$ LANGUAGE plpgsql;

-- Function to detect anomalies in health metrics
CREATE OR REPLACE FUNCTION public.detect_anomalies(
    p_user_id UUID,
    p_metric_type TEXT,
    p_threshold DECIMAL DEFAULT 2.0
)
RETURNS TABLE (
    recorded_at TIMESTAMP WITH TIME ZONE,
    value DECIMAL,
    z_score DECIMAL,
    is_anomaly BOOLEAN
) AS $$
DECLARE
    avg_val DECIMAL;
    std_dev DECIMAL;
BEGIN
    -- Calculate mean and standard deviation
    SELECT AVG(value), STDDEV(value)
    INTO avg_val, std_dev
    FROM public.health_metrics
    WHERE user_id = p_user_id AND metric_type = p_metric_type;
    
    -- Return anomalies based on z-score
    RETURN QUERY
    SELECT 
        hm.recorded_at,
        hm.value,
        ABS((hm.value - avg_val) / NULLIF(std_dev, 0)) as z_score,
        ABS((hm.value - avg_val) / NULLIF(std_dev, 0)) > p_threshold as is_anomaly
    FROM public.health_metrics hm
    WHERE hm.user_id = p_user_id 
        AND hm.metric_type = p_metric_type
        AND std_dev > 0;
END;
$$ LANGUAGE plpgsql;

-- Function for fuzzy medical term search
CREATE OR REPLACE FUNCTION public.search_medical_terms(search_term TEXT, similarity_threshold DECIMAL DEFAULT 0.3)
RETURNS TABLE (
    id UUID,
    name TEXT,
    term_type TEXT,
    description TEXT,
    similarity DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mt.id,
        mt.name,
        mt.term_type,
        mt.description,
        GREATEST(
            similarity(mt.name, search_term),
            similarity(COALESCE(mt.description, ''), search_term)
        ) as similarity
    FROM public.medical_terms mt
    WHERE 
        mt.name % search_term OR
        mt.description % search_term OR
        GREATEST(
            similarity(mt.name, search_term),
            similarity(COALESCE(mt.description, ''), search_term)
        ) > similarity_threshold
    ORDER BY similarity DESC;
END;
$$ LANGUAGE plpgsql;

-- Function for health data aggregation
CREATE OR REPLACE FUNCTION public.aggregate_health_data(
    p_user_id UUID,
    p_start_date DATE,
    p_end_date DATE
)
RETURNS TABLE (
    metric_type TEXT,
    avg_value DECIMAL,
    min_value DECIMAL,
    max_value DECIMAL,
    count_readings INTEGER,
    trend TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH daily_avgs AS (
        SELECT 
            metric_type,
            DATE(recorded_at) as day,
            AVG(value) as daily_avg
        FROM public.health_metrics
        WHERE user_id = p_user_id 
            AND recorded_at >= p_start_date 
            AND recorded_at <= p_end_date
        GROUP BY metric_type, DATE(recorded_at)
    ),
    trends AS (
        SELECT 
            metric_type,
            AVG(daily_avg) as avg_value,
            MIN(daily_avg) as min_value,
            MAX(daily_avg) as max_value,
            COUNT(*) as count_readings,
            CASE 
                WHEN AVG(daily_avg) > LAG(AVG(daily_avg)) OVER (PARTITION BY metric_type ORDER BY day) THEN 'increasing'
                WHEN AVG(daily_avg) < LAG(AVG(daily_avg)) OVER (PARTITION BY metric_type ORDER BY day) THEN 'decreasing'
                ELSE 'stable'
            END as trend
        FROM daily_avgs
        GROUP BY metric_type
    )
    SELECT * FROM trends;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions for extensions
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated, service_role; 