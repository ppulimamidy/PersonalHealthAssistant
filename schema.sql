-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector"; -- For embedding storage
CREATE EXTENSION IF NOT EXISTS "timescaledb"; -- For time-series optimization
CREATE EXTENSION IF NOT EXISTS "duckdb_fdw"; -- For DuckDB integration
CREATE EXTENSION IF NOT EXISTS "http"; -- For Qdrant API calls
CREATE EXTENSION IF NOT EXISTS "pg_kafka"; -- For Kafka integration
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- For query monitoring
CREATE EXTENSION IF NOT EXISTS "postgis"; -- For spatial data

-- Authentication Tables
CREATE TABLE auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    encrypted_password TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_sign_in_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

-- User Profiles
CREATE TABLE public.user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    first_name TEXT,
    last_name TEXT,
    date_of_birth DATE,
    gender TEXT,
    height DECIMAL,
    weight DECIMAL,
    blood_type TEXT,
    emergency_contact TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Medical Conditions
CREATE TABLE public.medical_conditions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    condition_name TEXT NOT NULL,
    diagnosis_date DATE,
    severity TEXT,
    status TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Medications
CREATE TABLE public.medications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    medication_name TEXT NOT NULL,
    dosage TEXT,
    frequency TEXT,
    start_date DATE,
    end_date DATE,
    prescribed_by TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Health Metrics
CREATE TABLE public.health_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    metric_type TEXT NOT NULL,
    value DECIMAL,
    unit TEXT,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source TEXT,
    notes TEXT
);

-- Symptoms
CREATE TABLE public.symptoms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    symptom_name TEXT NOT NULL,
    severity INTEGER,
    duration TEXT,
    notes TEXT,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Device Integration
CREATE TABLE public.devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    device_type TEXT NOT NULL,
    device_id TEXT NOT NULL,
    device_name TEXT,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active'
);

-- Healthcare Providers
CREATE TABLE public.healthcare_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_type TEXT NOT NULL,
    name TEXT NOT NULL,
    specialization TEXT,
    contact_info TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active'
);

-- User-Provider Relationships
CREATE TABLE public.user_provider_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES public.healthcare_providers(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Hospitals/Clinics
CREATE TABLE public.healthcare_facilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    address TEXT,
    contact_info TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active'
);

-- Insurance Companies
CREATE TABLE public.insurance_companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    contact_info TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Insurance
CREATE TABLE public.user_insurance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    insurance_company_id UUID REFERENCES public.insurance_companies(id) ON DELETE CASCADE,
    policy_number TEXT,
    coverage_start_date DATE,
    coverage_end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Products (Store)
CREATE TABLE public.products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    price DECIMAL,
    stock_quantity INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Orders
CREATE TABLE public.orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    order_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT,
    total_amount DECIMAL,
    shipping_address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Order Items
CREATE TABLE public.order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES public.orders(id) ON DELETE CASCADE,
    product_id UUID REFERENCES public.products(id) ON DELETE CASCADE,
    quantity INTEGER,
    price_at_time DECIMAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Health Reports
CREATE TABLE public.health_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL,
    report_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    report_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Medical Imaging
CREATE TABLE public.medical_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    image_type TEXT NOT NULL, -- e.g., 'X-RAY', 'MRI', 'CT-SCAN', 'ULTRASOUND'
    image_url TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size BIGINT,
    mime_type TEXT,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    taken_date TIMESTAMP WITH TIME ZONE,
    facility_id UUID REFERENCES public.healthcare_facilities(id),
    provider_id UUID REFERENCES public.healthcare_providers(id),
    notes TEXT,
    metadata JSONB, -- Store additional image metadata like dimensions, resolution, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Medical Reports
CREATE TABLE public.medical_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL, -- e.g., 'LAB_RESULT', 'IMAGING_REPORT', 'CONSULTATION'
    report_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    provider_id UUID REFERENCES public.healthcare_providers(id),
    facility_id UUID REFERENCES public.healthcare_facilities(id),
    report_content TEXT,
    report_file_url TEXT, -- URL to the PDF or document file
    status TEXT, -- e.g., 'PENDING', 'COMPLETED', 'REVIEWED'
    metadata JSONB, -- Store additional report metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Image-Report Relationships
CREATE TABLE public.image_report_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    image_id UUID REFERENCES public.medical_images(id) ON DELETE CASCADE,
    report_id UUID REFERENCES public.medical_reports(id) ON DELETE CASCADE,
    relationship_type TEXT, -- e.g., 'PRIMARY', 'SUPPORTING', 'REFERENCE'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Device Data Types
CREATE TABLE public.device_data_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL, -- e.g., 'ACTIVITY', 'SLEEP', 'NUTRITION', 'VITALS'
    unit TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Device Data Points
CREATE TABLE public.device_data_points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    device_id UUID REFERENCES public.devices(id) ON DELETE CASCADE,
    data_type_id UUID REFERENCES public.device_data_types(id),
    value DECIMAL,
    unit TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB, -- Store additional data like confidence, quality, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (timestamp);

-- Create partitions for device_data_points
CREATE TABLE device_data_points_y2023m01 PARTITION OF device_data_points
    FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');
CREATE TABLE device_data_points_y2023m02 PARTITION OF device_data_points
    FOR VALUES FROM ('2023-02-01') TO ('2023-03-01');
-- Add more partitions as needed

-- Activity Tracking
CREATE TABLE public.activity_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    activity_type TEXT NOT NULL, -- e.g., 'WALKING', 'RUNNING', 'CYCLING'
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration INTEGER, -- in seconds
    calories_burned DECIMAL,
    distance DECIMAL,
    steps INTEGER,
    heart_rate_avg DECIMAL,
    heart_rate_max DECIMAL,
    heart_rate_min DECIMAL,
    metadata JSONB, -- Store additional activity data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sleep Tracking
CREATE TABLE public.sleep_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration INTEGER, -- in minutes
    quality_score DECIMAL,
    deep_sleep_duration INTEGER,
    light_sleep_duration INTEGER,
    rem_sleep_duration INTEGER,
    awake_duration INTEGER,
    heart_rate_avg DECIMAL,
    metadata JSONB, -- Store additional sleep data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Nutrition Tracking
CREATE TABLE public.nutrition_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    meal_type TEXT, -- e.g., 'BREAKFAST', 'LUNCH', 'DINNER', 'SNACK'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    calories DECIMAL,
    protein DECIMAL,
    carbs DECIMAL,
    fat DECIMAL,
    fiber DECIMAL,
    sugar DECIMAL,
    sodium DECIMAL,
    water_intake DECIMAL,
    notes TEXT,
    metadata JSONB, -- Store additional nutrition data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vital Signs
CREATE TABLE public.vital_signs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    blood_pressure_systolic INTEGER,
    blood_pressure_diastolic INTEGER,
    heart_rate INTEGER,
    temperature DECIMAL,
    blood_oxygen DECIMAL,
    respiratory_rate INTEGER,
    metadata JSONB, -- Store additional vital signs data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Health Goals
CREATE TABLE public.health_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    goal_type TEXT NOT NULL, -- e.g., 'WEIGHT', 'ACTIVITY', 'SLEEP', 'NUTRITION'
    target_value DECIMAL,
    start_date DATE NOT NULL,
    end_date DATE,
    status TEXT, -- e.g., 'ACTIVE', 'COMPLETED', 'ABANDONED'
    progress DECIMAL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Health Insights
CREATE TABLE public.health_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    insight_type TEXT NOT NULL, -- e.g., 'ACTIVITY', 'SLEEP', 'NUTRITION', 'VITALS'
    title TEXT NOT NULL,
    description TEXT,
    severity TEXT, -- e.g., 'INFO', 'WARNING', 'ALERT'
    data_points JSONB, -- Store relevant data points for the insight
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Nutrition Photos
CREATE TABLE public.nutrition_photos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    nutrition_log_id UUID REFERENCES public.nutrition_logs(id) ON DELETE CASCADE,
    photo_url TEXT NOT NULL,
    thumbnail_url TEXT,
    file_name TEXT NOT NULL,
    file_size BIGINT,
    mime_type TEXT,
    taken_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    photo_type TEXT, -- e.g., 'MEAL', 'SUPPLEMENT', 'INGREDIENT'
    metadata JSONB, -- Store additional photo metadata like dimensions, location, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Supplements
CREATE TABLE public.supplements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    brand TEXT,
    category TEXT, -- e.g., 'VITAMIN', 'MINERAL', 'PROTEIN', 'HERBAL'
    serving_size TEXT,
    serving_unit TEXT,
    description TEXT,
    ingredients TEXT[],
    nutritional_info JSONB, -- Store detailed nutritional information
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Supplements
CREATE TABLE public.user_supplements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    supplement_id UUID REFERENCES public.supplements(id) ON DELETE CASCADE,
    start_date DATE,
    end_date DATE,
    dosage TEXT,
    frequency TEXT,
    notes TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Supplement Logs
CREATE TABLE public.supplement_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    user_supplement_id UUID REFERENCES public.user_supplements(id) ON DELETE CASCADE,
    taken_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    dosage TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Supplement Photos
CREATE TABLE public.supplement_photos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    supplement_log_id UUID REFERENCES public.supplement_logs(id) ON DELETE CASCADE,
    photo_url TEXT NOT NULL,
    thumbnail_url TEXT,
    file_name TEXT NOT NULL,
    file_size BIGINT,
    mime_type TEXT,
    taken_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI Analysis Results
CREATE TABLE public.nutrition_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    nutrition_log_id UUID REFERENCES public.nutrition_logs(id) ON DELETE CASCADE,
    photo_id UUID REFERENCES public.nutrition_photos(id) ON DELETE CASCADE,
    analysis_type TEXT NOT NULL, -- e.g., 'FOOD_RECOGNITION', 'PORTION_SIZE', 'NUTRITIONAL_ESTIMATE'
    detected_items JSONB, -- Store AI-detected food items
    nutritional_estimate JSONB, -- Store estimated nutritional values
    confidence_score DECIMAL,
    analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Medical Literature & Knowledge Graph
CREATE TABLE public.medical_literature (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source TEXT NOT NULL, -- e.g., 'PUBMED', 'CLINICAL_TRIALS'
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    authors TEXT[],
    publication_date DATE,
    abstract TEXT,
    full_text TEXT,
    keywords TEXT[],
    embedding vector(1536), -- For semantic search
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.medical_terms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    term_type TEXT NOT NULL, -- e.g., 'DRUG', 'CONDITION', 'GENE', 'BIOMARKER'
    name TEXT NOT NULL,
    code TEXT, -- e.g., RxNorm code
    description TEXT,
    synonyms TEXT[],
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.interaction_graph (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_term_id UUID REFERENCES public.medical_terms(id),
    target_term_id UUID REFERENCES public.medical_terms(id),
    interaction_type TEXT NOT NULL, -- e.g., 'DRUG_FOOD', 'DRUG_SUPPLEMENT', 'GENE_DRUG'
    effect_type TEXT, -- e.g., 'INCREASE', 'DECREASE', 'INHIBIT'
    severity TEXT, -- e.g., 'MILD', 'MODERATE', 'SEVERE'
    evidence_level TEXT, -- e.g., 'STRONG', 'MODERATE', 'WEAK'
    description TEXT,
    literature_references UUID[] REFERENCES public.medical_literature(id),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Lab Results & Biomarkers
CREATE TABLE public.lab_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    lab_source_id UUID REFERENCES public.healthcare_facilities(id),
    test_date TIMESTAMP WITH TIME ZONE NOT NULL,
    report_type TEXT NOT NULL,
    report_url TEXT,
    ocr_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.biomarkers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lab_result_id UUID REFERENCES public.lab_results(id) ON DELETE CASCADE,
    biomarker_name TEXT NOT NULL,
    value DECIMAL,
    unit TEXT,
    reference_range TEXT,
    interpretation TEXT,
    status TEXT, -- e.g., 'NORMAL', 'HIGH', 'LOW'
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Event Logging & AI Explainability
CREATE TABLE public.event_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source TEXT NOT NULL, -- e.g., 'USER_INPUT', 'DEVICE', 'AI_ANALYSIS'
    data JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (event_timestamp);

-- Create partitions for event_logs
CREATE TABLE event_logs_y2023m01 PARTITION OF event_logs
    FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');
CREATE TABLE event_logs_y2023m02 PARTITION OF event_logs
    FOR VALUES FROM ('2023-02-01') TO ('2023-03-01');
-- Add more partitions as needed

CREATE TABLE public.causal_inferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    cause_event_id UUID REFERENCES public.event_logs(id),
    effect_event_id UUID REFERENCES public.event_logs(id),
    confidence_score DECIMAL,
    explanation TEXT,
    evidence_sources JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Voice & Multimodal Inputs
CREATE TABLE public.voice_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    audio_url TEXT NOT NULL,
    transcription TEXT,
    duration INTEGER,
    language TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Create partitions for voice_logs
CREATE TABLE voice_logs_y2023m01 PARTITION OF voice_logs
    FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');
CREATE TABLE voice_logs_y2023m02 PARTITION OF voice_logs
    FOR VALUES FROM ('2023-02-01') TO ('2023-03-01');
-- Add more partitions as needed

CREATE TABLE public.raw_input_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    input_type TEXT NOT NULL, -- e.g., 'VOICE', 'IMAGE', 'TEXT'
    source_url TEXT,
    processed_data JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Doctor Mode & Reports
CREATE TABLE public.event_timelines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_data JSONB,
    source TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.report_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_name TEXT NOT NULL,
    template_type TEXT NOT NULL,
    content JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version TEXT NOT NULL DEFAULT '1.0',
    is_latest BOOLEAN DEFAULT true,
    previous_version_id UUID REFERENCES public.report_templates(id)
);

CREATE TABLE public.clinician_annotations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES public.healthcare_providers(id),
    annotation_type TEXT NOT NULL,
    content TEXT,
    reference_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Genomics & Personal Markers
CREATE TABLE public.genomic_markers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    marker_name TEXT NOT NULL,
    marker_type TEXT NOT NULL,
    description TEXT,
    reference_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.user_genomics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    marker_id UUID REFERENCES public.genomic_markers(id),
    value TEXT,
    interpretation TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analytics & Alerts
CREATE TABLE public.analytics_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    snapshot_type TEXT NOT NULL,
    snapshot_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metrics JSONB,
    insights JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.anomaly_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT,
    trigger_data JSONB,
    status TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Audit & Consent
CREATE TABLE public.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    action_data JSONB,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.consent_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    consent_type TEXT NOT NULL,
    version TEXT NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_latest BOOLEAN DEFAULT true,
    previous_version_id UUID REFERENCES public.consent_records(id)
);

-- Create indexes for better query performance
CREATE INDEX idx_user_profiles_user_id ON public.user_profiles(user_id);
CREATE INDEX idx_medical_conditions_user_id ON public.medical_conditions(user_id);
CREATE INDEX idx_medications_user_id ON public.medications(user_id);
CREATE INDEX idx_health_metrics_user_id ON public.health_metrics(user_id);
CREATE INDEX idx_symptoms_user_id ON public.symptoms(user_id);
CREATE INDEX idx_devices_user_id ON public.devices(user_id);
CREATE INDEX idx_user_provider_relationships_user_id ON public.user_provider_relationships(user_id);
CREATE INDEX idx_user_provider_relationships_provider_id ON public.user_provider_relationships(provider_id);
CREATE INDEX idx_user_insurance_user_id ON public.user_insurance(user_id);
CREATE INDEX idx_orders_user_id ON public.orders(user_id);
CREATE INDEX idx_order_items_order_id ON public.order_items(order_id);
CREATE INDEX idx_health_reports_user_id ON public.health_reports(user_id);
CREATE INDEX idx_medical_images_user_id ON public.medical_images(user_id);
CREATE INDEX idx_medical_images_facility_id ON public.medical_images(facility_id);
CREATE INDEX idx_medical_images_provider_id ON public.medical_images(provider_id);
CREATE INDEX idx_medical_reports_user_id ON public.medical_reports(user_id);
CREATE INDEX idx_medical_reports_provider_id ON public.medical_reports(provider_id);
CREATE INDEX idx_medical_reports_facility_id ON public.medical_reports(facility_id);
CREATE INDEX idx_image_report_relationships_image_id ON public.image_report_relationships(image_id);
CREATE INDEX idx_image_report_relationships_report_id ON public.image_report_relationships(report_id);
CREATE INDEX idx_device_data_points_user_id ON public.device_data_points(user_id);
CREATE INDEX idx_device_data_points_device_id ON public.device_data_points(device_id);
CREATE INDEX idx_device_data_points_data_type_id ON public.device_data_points(data_type_id);
CREATE INDEX idx_device_data_points_timestamp ON public.device_data_points(timestamp);
CREATE INDEX idx_activity_sessions_user_id ON public.activity_sessions(user_id);
CREATE INDEX idx_activity_sessions_start_time ON public.activity_sessions(start_time);
CREATE INDEX idx_sleep_sessions_user_id ON public.sleep_sessions(user_id);
CREATE INDEX idx_sleep_sessions_start_time ON public.sleep_sessions(start_time);
CREATE INDEX idx_nutrition_logs_user_id ON public.nutrition_logs(user_id);
CREATE INDEX idx_nutrition_logs_timestamp ON public.nutrition_logs(timestamp);
CREATE INDEX idx_vital_signs_user_id ON public.vital_signs(user_id);
CREATE INDEX idx_vital_signs_timestamp ON public.vital_signs(timestamp);
CREATE INDEX idx_health_goals_user_id ON public.health_goals(user_id);
CREATE INDEX idx_health_goals_status ON public.health_goals(status);
CREATE INDEX idx_health_insights_user_id ON public.health_insights(user_id);
CREATE INDEX idx_health_insights_insight_type ON public.health_insights(insight_type);
CREATE INDEX idx_nutrition_photos_user_id ON public.nutrition_photos(user_id);
CREATE INDEX idx_nutrition_photos_nutrition_log_id ON public.nutrition_photos(nutrition_log_id);
CREATE INDEX idx_supplements_category ON public.supplements(category);
CREATE INDEX idx_user_supplements_user_id ON public.user_supplements(user_id);
CREATE INDEX idx_user_supplements_supplement_id ON public.user_supplements(supplement_id);
CREATE INDEX idx_supplement_logs_user_id ON public.supplement_logs(user_id);
CREATE INDEX idx_supplement_logs_user_supplement_id ON public.supplement_logs(user_supplement_id);
CREATE INDEX idx_supplement_photos_user_id ON public.supplement_photos(user_id);
CREATE INDEX idx_supplement_photos_supplement_log_id ON public.supplement_photos(supplement_log_id);
CREATE INDEX idx_nutrition_analysis_user_id ON public.nutrition_analysis(user_id);
CREATE INDEX idx_nutrition_analysis_nutrition_log_id ON public.nutrition_analysis(nutrition_log_id);
CREATE INDEX idx_nutrition_analysis_photo_id ON public.nutrition_analysis(photo_id);
CREATE INDEX idx_medical_literature_source ON public.medical_literature(source);
CREATE INDEX idx_medical_terms_term_type ON public.medical_terms(term_type);
CREATE INDEX idx_interaction_graph_source_term ON public.interaction_graph(source_term_id);
CREATE INDEX idx_interaction_graph_target_term ON public.interaction_graph(target_term_id);
CREATE INDEX idx_lab_results_user_id ON public.lab_results(user_id);
CREATE INDEX idx_biomarkers_lab_result_id ON public.biomarkers(lab_result_id);
CREATE INDEX idx_event_logs_user_id ON public.event_logs(user_id);
CREATE INDEX idx_voice_logs_user_id ON public.voice_logs(user_id);
CREATE INDEX idx_event_timelines_user_id ON public.event_timelines(user_id);
CREATE INDEX idx_clinician_annotations_user_id ON public.clinician_annotations(user_id);
CREATE INDEX idx_user_genomics_user_id ON public.user_genomics(user_id);
CREATE INDEX idx_analytics_snapshots_user_id ON public.analytics_snapshots(user_id);
CREATE INDEX idx_anomaly_alerts_user_id ON public.anomaly_alerts(user_id);
CREATE INDEX idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX idx_consent_records_user_id ON public.consent_records(user_id);

-- Create RLS (Row Level Security) policies
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medical_conditions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.health_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.symptoms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_provider_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_insurance ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.health_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medical_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medical_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.image_report_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.device_data_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.device_data_points ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sleep_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vital_signs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.health_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.health_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.supplements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_supplements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.supplement_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.supplement_photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medical_literature ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medical_terms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interaction_graph ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lab_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.biomarkers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.causal_inferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.voice_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.raw_input_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event_timelines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinician_annotations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.genomic_markers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_genomics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analytics_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.anomaly_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consent_records ENABLE ROW LEVEL SECURITY;

-- Create policies for user data access
CREATE POLICY "Users can view their own profile"
    ON public.user_profiles
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own profile"
    ON public.user_profiles
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Similar policies for other tables...

-- Create RLS policies for new tables
CREATE POLICY "Users can view their own medical images"
    ON public.medical_images
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own medical reports"
    ON public.medical_reports
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Healthcare providers can view their patients' medical images"
    ON public.medical_images
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.user_provider_relationships
            WHERE user_id = medical_images.user_id
            AND provider_id = auth.uid()
        )
    );

CREATE POLICY "Healthcare providers can view their patients' medical reports"
    ON public.medical_reports
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.user_provider_relationships
            WHERE user_id = medical_reports.user_id
            AND provider_id = auth.uid()
        )
    );

CREATE POLICY "Users can view their own device data"
    ON public.device_data_points
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own activity data"
    ON public.activity_sessions
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own sleep data"
    ON public.sleep_sessions
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own nutrition data"
    ON public.nutrition_logs
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own vital signs"
    ON public.vital_signs
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own health goals"
    ON public.health_goals
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own health insights"
    ON public.health_insights
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own nutrition photos"
    ON public.nutrition_photos
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own supplements"
    ON public.user_supplements
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own supplement logs"
    ON public.supplement_logs
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own supplement photos"
    ON public.supplement_photos
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own nutrition analysis"
    ON public.nutrition_analysis
    FOR SELECT
    USING (auth.uid() = user_id);

-- Create views for common analytics queries
CREATE VIEW public.daily_activity_summary AS
SELECT 
    user_id,
    DATE(timestamp) as date,
    COUNT(*) as data_points_count,
    AVG(value) as average_value,
    MIN(value) as min_value,
    MAX(value) as max_value
FROM public.device_data_points
GROUP BY user_id, DATE(timestamp);

CREATE VIEW public.weekly_health_metrics AS
SELECT 
    user_id,
    DATE_TRUNC('week', timestamp) as week_start,
    AVG(heart_rate) as avg_heart_rate,
    AVG(blood_pressure_systolic) as avg_systolic,
    AVG(blood_pressure_diastolic) as avg_diastolic,
    AVG(blood_oxygen) as avg_blood_oxygen
FROM public.vital_signs
GROUP BY user_id, DATE_TRUNC('week', timestamp);

CREATE VIEW public.daily_nutrition_summary AS
SELECT 
    nl.user_id,
    DATE(nl.timestamp) as date,
    COUNT(DISTINCT nl.id) as meal_count,
    COUNT(DISTINCT np.id) as photo_count,
    SUM(nl.calories) as total_calories,
    SUM(nl.protein) as total_protein,
    SUM(nl.carbs) as total_carbs,
    SUM(nl.fat) as total_fat,
    SUM(nl.water_intake) as total_water
FROM public.nutrition_logs nl
LEFT JOIN public.nutrition_photos np ON nl.id = np.nutrition_log_id
GROUP BY nl.user_id, DATE(nl.timestamp);

CREATE VIEW public.supplement_usage_summary AS
SELECT 
    us.user_id,
    s.name as supplement_name,
    s.category as supplement_category,
    COUNT(sl.id) as times_taken,
    MIN(sl.taken_at) as first_taken,
    MAX(sl.taken_at) as last_taken
FROM public.user_supplements us
JOIN public.supplements s ON us.supplement_id = s.id
LEFT JOIN public.supplement_logs sl ON us.id = sl.user_supplement_id
GROUP BY us.user_id, s.name, s.category;

-- Add AI-specific indexes for semantic search
CREATE INDEX medical_terms_embedding_idx ON public.medical_terms 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

CREATE INDEX medical_literature_embedding_idx ON public.medical_literature 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Add AI model-related tables
CREATE TABLE public.training_datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_name TEXT NOT NULL,
    dataset_type TEXT NOT NULL,
    description TEXT,
    data_sources JSONB,
    preprocessing_steps JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.model_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    architecture TEXT NOT NULL,
    hyperparameters JSONB,
    training_dataset_id UUID REFERENCES public.training_datasets(id),
    performance_metrics JSONB,
    deployment_status TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.model_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_version_id UUID REFERENCES public.model_versions(id),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    input_data JSONB,
    prediction JSONB,
    confidence_score DECIMAL,
    prediction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for new tables
CREATE INDEX idx_training_datasets_dataset_type ON public.training_datasets(dataset_type);
CREATE INDEX idx_model_versions_model_name ON public.model_versions(model_name);
CREATE INDEX idx_model_versions_deployment_status ON public.model_versions(deployment_status);
CREATE INDEX idx_model_predictions_model_version_id ON public.model_predictions(model_version_id);
CREATE INDEX idx_model_predictions_user_id ON public.model_predictions(user_id);
CREATE INDEX idx_model_predictions_prediction_timestamp ON public.model_predictions(prediction_timestamp);

-- Enable RLS for new tables
ALTER TABLE public.training_datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_predictions ENABLE ROW LEVEL SECURITY;

-- Convert time-series tables to hypertables
SELECT create_hypertable('device_data_points', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

SELECT create_hypertable('event_logs', 'event_timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

SELECT create_hypertable('voice_logs', 'created_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

SELECT create_hypertable('vital_signs', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create data retention policies
CREATE OR REPLACE FUNCTION public.cleanup_old_time_series_data()
RETURNS void AS $$
BEGIN
    -- Remove chunks older than retention period
    -- Device data: Keep 1 year of detailed data, 5 years of aggregated data
    PERFORM drop_chunks('device_data_points', INTERVAL '1 year');
    
    -- Event logs: Keep 6 months of detailed data, 2 years of aggregated data
    PERFORM drop_chunks('event_logs', INTERVAL '6 months');
    
    -- Voice logs: Keep 3 months of detailed data, 1 year of aggregated data
    PERFORM drop_chunks('voice_logs', INTERVAL '3 months');
    
    -- Vital signs: Keep 1 year of detailed data, 5 years of aggregated data
    PERFORM drop_chunks('vital_signs', INTERVAL '1 year');
END;
$$ LANGUAGE plpgsql;

-- Create aggregated tables for historical data
CREATE TABLE public.device_data_points_aggregated (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    data_type_id UUID REFERENCES public.device_data_types(id),
    time_bucket TIMESTAMP WITH TIME ZONE,
    avg_value DECIMAL,
    min_value DECIMAL,
    max_value DECIMAL,
    sample_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, data_type_id, time_bucket)
);

CREATE TABLE public.event_logs_aggregated (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    time_bucket TIMESTAMP WITH TIME ZONE,
    event_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, event_type, time_bucket)
);

CREATE TABLE public.vital_signs_aggregated (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    time_bucket TIMESTAMP WITH TIME ZONE,
    avg_heart_rate DECIMAL,
    avg_blood_pressure_systolic DECIMAL,
    avg_blood_pressure_diastolic DECIMAL,
    avg_blood_oxygen DECIMAL,
    sample_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, time_bucket)
);

-- Create continuous aggregates
CREATE MATERIALIZED VIEW device_data_points_hourly
WITH (timescaledb.continuous) AS
SELECT
    user_id,
    data_type_id,
    time_bucket('1 hour', timestamp) AS bucket,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    COUNT(*) as sample_count
FROM device_data_points
GROUP BY user_id, data_type_id, bucket
WITH NO DATA;

CREATE MATERIALIZED VIEW vital_signs_hourly
WITH (timescaledb.continuous) AS
SELECT
    user_id,
    time_bucket('1 hour', timestamp) AS bucket,
    AVG(heart_rate) as avg_heart_rate,
    AVG(blood_pressure_systolic) as avg_systolic,
    AVG(blood_pressure_diastolic) as avg_diastolic,
    AVG(blood_oxygen) as avg_blood_oxygen,
    COUNT(*) as sample_count
FROM vital_signs
GROUP BY user_id, bucket
WITH NO DATA;

-- Create data migration function
CREATE OR REPLACE FUNCTION public.migrate_to_aggregated_tables()
RETURNS void AS $$
BEGIN
    -- Migrate device data points to aggregated table
    INSERT INTO device_data_points_aggregated
    SELECT
        user_id,
        data_type_id,
        date_trunc('day', timestamp) as time_bucket,
        AVG(value) as avg_value,
        MIN(value) as min_value,
        MAX(value) as max_value,
        COUNT(*) as sample_count
    FROM device_data_points
    WHERE timestamp < NOW() - INTERVAL '1 year'
    GROUP BY user_id, data_type_id, time_bucket
    ON CONFLICT (user_id, data_type_id, time_bucket)
    DO UPDATE SET
        avg_value = EXCLUDED.avg_value,
        min_value = EXCLUDED.min_value,
        max_value = EXCLUDED.max_value,
        sample_count = EXCLUDED.sample_count;

    -- Migrate vital signs to aggregated table
    INSERT INTO vital_signs_aggregated
    SELECT
        user_id,
        date_trunc('day', timestamp) as time_bucket,
        AVG(heart_rate) as avg_heart_rate,
        AVG(blood_pressure_systolic) as avg_systolic,
        AVG(blood_pressure_diastolic) as avg_diastolic,
        AVG(blood_oxygen) as avg_blood_oxygen,
        COUNT(*) as sample_count
    FROM vital_signs
    WHERE timestamp < NOW() - INTERVAL '1 year'
    GROUP BY user_id, time_bucket
    ON CONFLICT (user_id, time_bucket)
    DO UPDATE SET
        avg_heart_rate = EXCLUDED.avg_heart_rate,
        avg_systolic = EXCLUDED.avg_systolic,
        avg_diastolic = EXCLUDED.avg_diastolic,
        avg_blood_oxygen = EXCLUDED.avg_blood_oxygen,
        sample_count = EXCLUDED.sample_count;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled jobs for data management
SELECT cron.schedule('0 0 * * *', $$SELECT public.cleanup_old_time_series_data()$$);
SELECT cron.schedule('0 1 * * *', $$SELECT public.migrate_to_aggregated_tables()$$);

-- Create indexes for aggregated tables
CREATE INDEX idx_device_data_points_aggregated_user_id ON public.device_data_points_aggregated(user_id);
CREATE INDEX idx_device_data_points_aggregated_time_bucket ON public.device_data_points_aggregated(time_bucket);
CREATE INDEX idx_event_logs_aggregated_user_id ON public.event_logs_aggregated(user_id);
CREATE INDEX idx_event_logs_aggregated_time_bucket ON public.event_logs_aggregated(time_bucket);
CREATE INDEX idx_vital_signs_aggregated_user_id ON public.vital_signs_aggregated(user_id);
CREATE INDEX idx_vital_signs_aggregated_time_bucket ON public.vital_signs_aggregated(time_bucket);

-- Enable RLS for aggregated tables
ALTER TABLE public.device_data_points_aggregated ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event_logs_aggregated ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vital_signs_aggregated ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for aggregated tables
CREATE POLICY "Users can view their own aggregated device data"
    ON public.device_data_points_aggregated
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own aggregated event logs"
    ON public.event_logs_aggregated
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own aggregated vital signs"
    ON public.vital_signs_aggregated
    FOR SELECT
    USING (auth.uid() = user_id);

-- Create analytics schema for OLAP queries
CREATE SCHEMA IF NOT EXISTS analytics;

-- Create analytics tables in DuckDB
CREATE FOREIGN TABLE analytics.daily_health_metrics (
    user_id UUID,
    date DATE,
    avg_heart_rate DECIMAL,
    avg_blood_pressure_systolic DECIMAL,
    avg_blood_pressure_diastolic DECIMAL,
    avg_blood_oxygen DECIMAL,
    total_steps INTEGER,
    total_calories_burned DECIMAL,
    total_sleep_duration INTEGER,
    total_water_intake DECIMAL,
    total_calories_consumed DECIMAL,
    total_protein DECIMAL,
    total_carbs DECIMAL,
    total_fat DECIMAL,
    total_fiber DECIMAL,
    total_sugar DECIMAL,
    total_sodium DECIMAL,
    supplement_count INTEGER,
    medication_count INTEGER,
    event_count INTEGER,
    anomaly_count INTEGER
) SERVER duckdb_server
OPTIONS (
    database '/path/to/analytics.duckdb',
    table 'daily_health_metrics'
);

CREATE FOREIGN TABLE analytics.weekly_health_trends (
    user_id UUID,
    week_start DATE,
    avg_heart_rate DECIMAL,
    avg_blood_pressure_systolic DECIMAL,
    avg_blood_pressure_diastolic DECIMAL,
    avg_blood_oxygen DECIMAL,
    total_steps INTEGER,
    total_calories_burned DECIMAL,
    avg_sleep_duration INTEGER,
    avg_water_intake DECIMAL,
    avg_calories_consumed DECIMAL,
    avg_protein DECIMAL,
    avg_carbs DECIMAL,
    avg_fat DECIMAL,
    avg_fiber DECIMAL,
    avg_sugar DECIMAL,
    avg_sodium DECIMAL,
    supplement_frequency DECIMAL,
    medication_frequency DECIMAL,
    event_frequency DECIMAL,
    anomaly_frequency DECIMAL,
    health_score DECIMAL
) SERVER duckdb_server
OPTIONS (
    database '/path/to/analytics.duckdb',
    table 'weekly_health_trends'
);

CREATE FOREIGN TABLE analytics.monthly_health_insights (
    user_id UUID,
    month_start DATE,
    health_trend TEXT,
    risk_factors JSONB,
    improvement_areas JSONB,
    achievement_metrics JSONB,
    recommendation_metrics JSONB,
    compliance_score DECIMAL,
    wellness_score DECIMAL,
    activity_score DECIMAL,
    nutrition_score DECIMAL,
    sleep_score DECIMAL,
    stress_score DECIMAL
) SERVER duckdb_server
OPTIONS (
    database '/path/to/analytics.duckdb',
    table 'monthly_health_insights'
);

-- Create materialized views for common analytics queries
CREATE MATERIALIZED VIEW analytics.user_health_summary AS
SELECT
    u.id as user_id,
    up.first_name,
    up.last_name,
    up.date_of_birth,
    up.gender,
    COUNT(DISTINCT mc.id) as condition_count,
    COUNT(DISTINCT m.id) as medication_count,
    COUNT(DISTINCT us.id) as supplement_count,
    COUNT(DISTINCT vs.id) as vital_signs_count,
    COUNT(DISTINCT as2.id) as activity_sessions_count,
    COUNT(DISTINCT ss.id) as sleep_sessions_count,
    COUNT(DISTINCT nl.id) as nutrition_logs_count,
    COUNT(DISTINCT ha.id) as anomaly_count
FROM auth.users u
LEFT JOIN public.user_profiles up ON u.id = up.user_id
LEFT JOIN public.medical_conditions mc ON u.id = mc.user_id
LEFT JOIN public.medications m ON u.id = m.user_id
LEFT JOIN public.user_supplements us ON u.id = us.user_id
LEFT JOIN public.vital_signs vs ON u.id = vs.user_id
LEFT JOIN public.activity_sessions as2 ON u.id = as2.user_id
LEFT JOIN public.sleep_sessions ss ON u.id = ss.user_id
LEFT JOIN public.nutrition_logs nl ON u.id = nl.user_id
LEFT JOIN public.anomaly_alerts ha ON u.id = ha.user_id
GROUP BY u.id, up.first_name, up.last_name, up.date_of_birth, up.gender;

-- Create function to refresh analytics data
CREATE OR REPLACE FUNCTION public.refresh_analytics_data()
RETURNS void AS $$
BEGIN
    -- Refresh materialized views
    REFRESH MATERIALIZED VIEW analytics.user_health_summary;
    
    -- Export data to DuckDB
    -- Note: This would typically be handled by a separate ETL process
    -- The following is a placeholder for the concept
    PERFORM duckdb_execute(
        'COPY (SELECT * FROM analytics.user_health_summary) TO ''/path/to/analytics.duckdb'' (FORMAT PARQUET)'
    );
END;
$$ LANGUAGE plpgsql;

-- Create scheduled job for analytics refresh
SELECT cron.schedule('0 2 * * *', $$SELECT public.refresh_analytics_data()$$);

-- Create analytics API views
CREATE VIEW analytics.dashboard_metrics AS
SELECT
    dhm.*,
    wht.health_score as weekly_health_score,
    mhi.health_trend,
    mhi.risk_factors,
    mhi.improvement_areas,
    mhi.achievement_metrics,
    mhi.recommendation_metrics,
    mhi.compliance_score,
    mhi.wellness_score,
    mhi.activity_score,
    mhi.nutrition_score,
    mhi.sleep_score,
    mhi.stress_score
FROM analytics.daily_health_metrics dhm
LEFT JOIN analytics.weekly_health_trends wht 
    ON dhm.user_id = wht.user_id 
    AND dhm.date >= wht.week_start 
    AND dhm.date < wht.week_start + INTERVAL '7 days'
LEFT JOIN analytics.monthly_health_insights mhi 
    ON dhm.user_id = mhi.user_id 
    AND dhm.date >= mhi.month_start 
    AND dhm.date < mhi.month_start + INTERVAL '1 month';

-- Create RLS policies for analytics
ALTER TABLE analytics.daily_health_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.weekly_health_trends ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.monthly_health_insights ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own analytics data"
    ON analytics.daily_health_metrics
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own weekly trends"
    ON analytics.weekly_health_trends
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own monthly insights"
    ON analytics.monthly_health_insights
    FOR SELECT
    USING (auth.uid() = user_id);

-- Create indexes for analytics tables
CREATE INDEX idx_daily_health_metrics_user_date ON analytics.daily_health_metrics(user_id, date);
CREATE INDEX idx_weekly_health_trends_user_week ON analytics.weekly_health_trends(user_id, week_start);
CREATE INDEX idx_monthly_health_insights_user_month ON analytics.monthly_health_insights(user_id, month_start);

-- Create vector search configuration
CREATE TABLE public.vector_search_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_name TEXT NOT NULL,
    vector_size INTEGER NOT NULL,
    distance_metric TEXT NOT NULL, -- e.g., 'Cosine', 'Euclidean', 'Dot'
    qdrant_url TEXT NOT NULL,
    qdrant_api_key TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create vector search collections
CREATE TABLE public.vector_collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    vector_size INTEGER NOT NULL,
    distance_metric TEXT NOT NULL,
    qdrant_collection_id TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create vector search points
CREATE TABLE public.vector_points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID REFERENCES public.vector_collections(id),
    point_id TEXT NOT NULL, -- Qdrant point ID
    vector vector(1536), -- Local vector for small collections
    payload JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create function to sync vectors to Qdrant
CREATE OR REPLACE FUNCTION public.sync_vectors_to_qdrant()
RETURNS void AS $$
DECLARE
    v_collection RECORD;
    v_point RECORD;
    v_payload JSONB;
BEGIN
    -- Get collections that need syncing
    FOR v_collection IN 
        SELECT * FROM public.vector_collections 
        WHERE qdrant_collection_id IS NOT NULL
    LOOP
        -- Get points that need syncing
        FOR v_point IN 
            SELECT * FROM public.vector_points 
            WHERE collection_id = v_collection.id
        LOOP
            -- Prepare payload
            v_payload := jsonb_build_object(
                'id', v_point.point_id,
                'vector', v_point.vector,
                'payload', v_point.payload
            );
            
            -- Sync to Qdrant
            PERFORM http_post(
                v_collection.qdrant_collection_id || '/points',
                v_payload,
                'application/json'
            );
        END LOOP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create function for hybrid search
CREATE OR REPLACE FUNCTION public.hybrid_search(
    p_collection_id UUID,
    p_query_vector vector(1536),
    p_limit INTEGER DEFAULT 10,
    p_threshold DECIMAL DEFAULT 0.7
)
RETURNS TABLE (
    point_id TEXT,
    similarity DECIMAL,
    payload JSONB
) AS $$
DECLARE
    v_collection RECORD;
    v_result JSONB;
BEGIN
    -- Get collection info
    SELECT * INTO v_collection 
    FROM public.vector_collections 
    WHERE id = p_collection_id;
    
    -- If collection is small, use pgvector
    IF EXISTS (
        SELECT 1 FROM public.vector_points 
        WHERE collection_id = p_collection_id 
        LIMIT 10000
    ) THEN
        RETURN QUERY
        SELECT 
            vp.point_id,
            (vp.vector <=> p_query_vector) as similarity,
            vp.payload
        FROM public.vector_points vp
        WHERE vp.collection_id = p_collection_id
        AND (vp.vector <=> p_query_vector) < p_threshold
        ORDER BY similarity
        LIMIT p_limit;
    ELSE
        -- Use Qdrant for large collections
        v_result := http_post(
            v_collection.qdrant_collection_id || '/search',
            jsonb_build_object(
                'vector', p_query_vector,
                'limit', p_limit,
                'threshold', p_threshold
            ),
            'application/json'
        );
        
        RETURN QUERY
        SELECT 
            (v->>'id')::TEXT as point_id,
            (v->>'score')::DECIMAL as similarity,
            (v->'payload')::JSONB as payload
        FROM jsonb_array_elements(v_result->'result') v;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for vector search
CREATE INDEX idx_vector_points_collection_id ON public.vector_points(collection_id);
CREATE INDEX idx_vector_points_point_id ON public.vector_points(point_id);

-- Enable RLS for vector search tables
ALTER TABLE public.vector_search_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vector_collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vector_points ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for vector search
CREATE POLICY "Users can view vector search config"
    ON public.vector_search_config
    FOR SELECT
    USING (true);

CREATE POLICY "Users can view vector collections"
    ON public.vector_collections
    FOR SELECT
    USING (true);

CREATE POLICY "Users can view vector points"
    ON public.vector_points
    FOR SELECT
    USING (true);

-- Create scheduled job for vector sync
SELECT cron.schedule('*/5 * * * *', $$SELECT public.sync_vectors_to_qdrant()$$);

-- Create streaming buffer tables
CREATE TABLE public.stream_buffer (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stream_type TEXT NOT NULL,
    device_id UUID REFERENCES public.devices(id),
    user_id UUID REFERENCES auth.users(id),
    raw_data JSONB,
    processed BOOLEAN DEFAULT false,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
) PARTITION BY RANGE (created_at);

-- Create partitions for stream buffer
CREATE TABLE stream_buffer_y2023m01 PARTITION OF stream_buffer
    FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');
CREATE TABLE stream_buffer_y2023m02 PARTITION OF stream_buffer
    FOR VALUES FROM ('2023-02-01') TO ('2023-03-01');

-- Create stream processing configuration
CREATE TABLE public.stream_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stream_type TEXT NOT NULL,
    buffer_size INTEGER NOT NULL,
    flush_interval INTEGER NOT NULL, -- in seconds
    batch_size INTEGER NOT NULL,
    kafka_topic TEXT,
    kafka_config JSONB,
    processing_config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create stream processing status
CREATE TABLE public.stream_processing_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stream_type TEXT NOT NULL,
    last_processed_id UUID,
    last_processed_at TIMESTAMP WITH TIME ZONE,
    processed_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    status TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create stream processing errors
CREATE TABLE public.stream_processing_errors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stream_type TEXT NOT NULL,
    buffer_id UUID REFERENCES public.stream_buffer(id),
    error_type TEXT NOT NULL,
    error_message TEXT,
    error_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create function to process stream buffer
CREATE OR REPLACE FUNCTION public.process_stream_buffer()
RETURNS void AS $$
DECLARE
    v_config RECORD;
    v_buffer RECORD;
    v_batch_size INTEGER;
    v_processed_count INTEGER := 0;
    v_error_count INTEGER := 0;
BEGIN
    -- Get stream configurations
    FOR v_config IN 
        SELECT * FROM public.stream_config 
        WHERE status = 'active'
    LOOP
        -- Process buffer in batches
        FOR v_buffer IN 
            SELECT * FROM public.stream_buffer 
            WHERE stream_type = v_config.stream_type 
            AND processed = false 
            AND error_count < 3
            LIMIT v_config.batch_size
        LOOP
            BEGIN
                -- Process based on stream type
                CASE v_config.stream_type
                    WHEN 'device_data' THEN
                        -- Process device data
                        INSERT INTO public.device_data_points (
                            user_id,
                            device_id,
                            data_type_id,
                            value,
                            unit,
                            timestamp,
                            metadata
                        )
                        SELECT 
                            v_buffer.user_id,
                            v_buffer.device_id,
                            (v_buffer.raw_data->>'data_type_id')::UUID,
                            (v_buffer.raw_data->>'value')::DECIMAL,
                            v_buffer.raw_data->>'unit',
                            (v_buffer.raw_data->>'timestamp')::TIMESTAMP WITH TIME ZONE,
                            v_buffer.raw_data->'metadata'
                        FROM public.stream_buffer
                        WHERE id = v_buffer.id;

                    WHEN 'vital_signs' THEN
                        -- Process vital signs
                        INSERT INTO public.vital_signs (
                            user_id,
                            timestamp,
                            blood_pressure_systolic,
                            blood_pressure_diastolic,
                            heart_rate,
                            temperature,
                            blood_oxygen,
                            respiratory_rate,
                            metadata
                        )
                        SELECT 
                            v_buffer.user_id,
                            (v_buffer.raw_data->>'timestamp')::TIMESTAMP WITH TIME ZONE,
                            (v_buffer.raw_data->>'blood_pressure_systolic')::INTEGER,
                            (v_buffer.raw_data->>'blood_pressure_diastolic')::INTEGER,
                            (v_buffer.raw_data->>'heart_rate')::INTEGER,
                            (v_buffer.raw_data->>'temperature')::DECIMAL,
                            (v_buffer.raw_data->>'blood_oxygen')::DECIMAL,
                            (v_buffer.raw_data->>'respiratory_rate')::INTEGER,
                            v_buffer.raw_data->'metadata'
                        FROM public.stream_buffer
                        WHERE id = v_buffer.id;

                    -- Add more stream types as needed
                END CASE;

                -- Mark as processed
                UPDATE public.stream_buffer
                SET processed = true,
                    processed_at = NOW()
                WHERE id = v_buffer.id;

                v_processed_count := v_processed_count + 1;

            EXCEPTION WHEN OTHERS THEN
                -- Log error
                INSERT INTO public.stream_processing_errors (
                    stream_type,
                    buffer_id,
                    error_type,
                    error_message,
                    error_data
                ) VALUES (
                    v_config.stream_type,
                    v_buffer.id,
                    'PROCESSING_ERROR',
                    SQLERRM,
                    jsonb_build_object(
                        'raw_data', v_buffer.raw_data,
                        'error_detail', SQLERRM
                    )
                );

                -- Increment error count
                UPDATE public.stream_buffer
                SET error_count = error_count + 1
                WHERE id = v_buffer.id;

                v_error_count := v_error_count + 1;
            END;
        END LOOP;

        -- Update processing status
        UPDATE public.stream_processing_status
        SET last_processed_at = NOW(),
            processed_count = processed_count + v_processed_count,
            error_count = error_count + v_error_count,
            status = CASE 
                WHEN v_error_count > 0 THEN 'WARNING'
                ELSE 'OK'
            END
        WHERE stream_type = v_config.stream_type;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create function to clean up processed buffer
CREATE OR REPLACE FUNCTION public.cleanup_stream_buffer()
RETURNS void AS $$
BEGIN
    -- Delete processed records older than 24 hours
    DELETE FROM public.stream_buffer
    WHERE processed = true
    AND created_at < NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql;

-- Create scheduled jobs for stream processing
SELECT cron.schedule('*/5 * * * *', $$SELECT public.process_stream_buffer()$$);
SELECT cron.schedule('0 * * * *', $$SELECT public.cleanup_stream_buffer()$$);

-- Create indexes for stream processing
CREATE INDEX idx_stream_buffer_stream_type ON public.stream_buffer(stream_type);
CREATE INDEX idx_stream_buffer_processed ON public.stream_buffer(processed);
CREATE INDEX idx_stream_buffer_created_at ON public.stream_buffer(created_at);
CREATE INDEX idx_stream_processing_errors_stream_type ON public.stream_processing_errors(stream_type);
CREATE INDEX idx_stream_processing_errors_created_at ON public.stream_processing_errors(created_at);

-- Enable RLS for stream processing tables
ALTER TABLE public.stream_buffer ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stream_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stream_processing_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stream_processing_errors ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for stream processing
CREATE POLICY "Users can view their own stream data"
    ON public.stream_buffer
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own processing status"
    ON public.stream_processing_status
    FOR SELECT
    USING (true);

CREATE POLICY "Users can view their own processing errors"
    ON public.stream_processing_errors
    FOR SELECT
    USING (auth.uid() = user_id);

-- Create Kafka consumer function
CREATE OR REPLACE FUNCTION public.kafka_consumer()
RETURNS void AS $$
DECLARE
    v_message RECORD;
BEGIN
    -- Consume messages from Kafka
    FOR v_message IN 
        SELECT * FROM kafka_consume('health_metrics_topic')
    LOOP
        -- Insert into stream buffer
        INSERT INTO public.stream_buffer (
            stream_type,
            device_id,
            user_id,
            raw_data
        ) VALUES (
            v_message.stream_type,
            v_message.device_id,
            v_message.user_id,
            v_message.data
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled job for Kafka consumer
SELECT cron.schedule('* * * * *', $$SELECT public.kafka_consumer()$$);

-- Food Items and Nutrition
CREATE TABLE public.food_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    brand TEXT,
    category TEXT,
    serving_size DECIMAL,
    serving_unit TEXT,
    calories DECIMAL,
    protein DECIMAL,
    carbs DECIMAL,
    fat DECIMAL,
    fiber DECIMAL,
    sugar DECIMAL,
    sodium DECIMAL,
    vitamins JSONB,
    minerals JSONB,
    allergens TEXT[],
    ingredients TEXT[],
    nutrition_facts JSONB,
    image_url TEXT,
    barcode TEXT,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.nutrition_log_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nutrition_log_id UUID REFERENCES public.nutrition_logs(id) ON DELETE CASCADE,
    food_item_id UUID REFERENCES public.food_items(id),
    serving_size DECIMAL,
    serving_unit TEXT,
    calories DECIMAL,
    protein DECIMAL,
    carbs DECIMAL,
    fat DECIMAL,
    fiber DECIMAL,
    sugar DECIMAL,
    sodium DECIMAL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced Exercise/Activity Details
CREATE TABLE public.activity_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    required_metrics TEXT[],
    optional_metrics TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.activity_routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    activity_session_id UUID REFERENCES public.activity_sessions(id) ON DELETE CASCADE,
    route_data GEOMETRY(LINESTRING, 4326),
    elevation_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.activity_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    activity_session_id UUID REFERENCES public.activity_sessions(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    metric_value DECIMAL,
    metric_unit TEXT,
    timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced Medication Management
CREATE TABLE public.prescriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    medication_id UUID REFERENCES public.medications(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES public.healthcare_providers(id),
    prescription_date DATE NOT NULL,
    prescription_number TEXT,
    refills_authorized INTEGER,
    refills_remaining INTEGER,
    last_refill_date DATE,
    next_refill_date DATE,
    pharmacy_id UUID REFERENCES public.healthcare_facilities(id),
    status TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Comprehensive Lab Test Management
CREATE TABLE public.lab_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_name TEXT NOT NULL,
    description TEXT,
    loinc_code TEXT,
    category TEXT,
    common_units TEXT,
    normal_range_male JSONB,
    normal_range_female JSONB,
    associated_biomarkers TEXT[],
    preparation_instructions TEXT,
    turnaround_time TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.lab_test_panels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    panel_name TEXT NOT NULL,
    description TEXT,
    tests UUID[] REFERENCES public.lab_tests(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced Health Reports
CREATE TABLE public.daily_health_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    vital_signs_summary JSONB,
    activity_summary JSONB,
    nutrition_summary JSONB,
    sleep_summary JSONB,
    medication_summary JSONB,
    insights JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.monthly_wellness_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    month_start DATE NOT NULL,
    health_trends JSONB,
    risk_factors JSONB,
    improvement_areas JSONB,
    achievement_metrics JSONB,
    recommendation_metrics JSONB,
    compliance_score DECIMAL,
    wellness_score DECIMAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Feedback System
CREATE TABLE public.user_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    feedback_type TEXT NOT NULL,
    reference_type TEXT NOT NULL, -- e.g., 'recommendation', 'insight', 'report'
    reference_id UUID,
    rating INTEGER,
    feedback_text TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced Consent Management
CREATE TABLE public.consent_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    data_categories TEXT[],
    retention_period INTEGER, -- in days
    required_consents TEXT[],
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add status fields to existing tables
ALTER TABLE public.devices ADD COLUMN status TEXT DEFAULT 'active';
ALTER TABLE public.user_supplements ADD COLUMN status TEXT DEFAULT 'active';
ALTER TABLE public.healthcare_providers ADD COLUMN status TEXT DEFAULT 'active';
ALTER TABLE public.healthcare_facilities ADD COLUMN status TEXT DEFAULT 'active';

-- Create indexes for new tables
CREATE INDEX idx_food_items_name ON public.food_items(name);
CREATE INDEX idx_food_items_barcode ON public.food_items(barcode);
CREATE INDEX idx_nutrition_log_items_nutrition_log_id ON public.nutrition_log_items(nutrition_log_id);
CREATE INDEX idx_activity_types_category ON public.activity_types(category);
CREATE INDEX idx_activity_routes_activity_session_id ON public.activity_routes(activity_session_id);
CREATE INDEX idx_activity_metrics_activity_session_id ON public.activity_metrics(activity_session_id);
CREATE INDEX idx_prescriptions_user_id ON public.prescriptions(user_id);
CREATE INDEX idx_prescriptions_medication_id ON public.prescriptions(medication_id);
CREATE INDEX idx_lab_tests_loinc_code ON public.lab_tests(loinc_code);
CREATE INDEX idx_lab_test_panels_panel_name ON public.lab_test_panels(panel_name);
CREATE INDEX idx_daily_health_summaries_user_date ON public.daily_health_summaries(user_id, date);
CREATE INDEX idx_monthly_wellness_reports_user_month ON public.monthly_wellness_reports(user_id, month_start);
CREATE INDEX idx_user_feedback_user_id ON public.user_feedback(user_id);
CREATE INDEX idx_user_feedback_reference ON public.user_feedback(reference_type, reference_id);
CREATE INDEX idx_consent_types_name ON public.consent_types(name);

-- Enable RLS for new tables
ALTER TABLE public.food_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_log_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.prescriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lab_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lab_test_panels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_health_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.monthly_wellness_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consent_types ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for new tables
CREATE POLICY "Users can view their own nutrition log items"
    ON public.nutrition_log_items
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.nutrition_logs
            WHERE id = nutrition_log_items.nutrition_log_id
            AND user_id = auth.uid()
        )
    );

CREATE POLICY "Users can view their own activity routes"
    ON public.activity_routes
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.activity_sessions
            WHERE id = activity_routes.activity_session_id
            AND user_id = auth.uid()
        )
    );

CREATE POLICY "Users can view their own prescriptions"
    ON public.prescriptions
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own health summaries"
    ON public.daily_health_summaries
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own wellness reports"
    ON public.monthly_wellness_reports
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own feedback"
    ON public.user_feedback
    FOR SELECT
    USING (auth.uid() = user_id);

-- Create RLS policies for new tables
CREATE POLICY "Users can view their own nutrition log items"
    ON public.nutrition_log_items
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.nutrition_logs
            WHERE id = nutrition_log_items.nutrition_log_id
            AND user_id = auth.uid()
        )
    );

CREATE POLICY "Users can view their own activity routes"
    ON public.activity_routes
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.activity_sessions
            WHERE id = activity_routes.activity_session_id
            AND user_id = auth.uid()
        )
    );

CREATE POLICY "Users can view their own prescriptions"
    ON public.prescriptions
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own health summaries"
    ON public.daily_health_summaries
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own wellness reports"
    ON public.monthly_wellness_reports
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own feedback"
    ON public.user_feedback
    FOR SELECT
    USING (auth.uid() = user_id); 