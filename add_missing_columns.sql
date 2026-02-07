-- Add missing columns to Epic FHIR tables
-- This script adds columns that exist in the model but not in the database

-- Add missing columns to epic_fhir_observations
ALTER TABLE epic_fhir_observations 
ADD COLUMN IF NOT EXISTS code_display VARCHAR(500),
ADD COLUMN IF NOT EXISTS value_quantity INTEGER,
ADD COLUMN IF NOT EXISTS value_unit VARCHAR(100),
ADD COLUMN IF NOT EXISTS value_code VARCHAR(255),
ADD COLUMN IF NOT EXISTS interpretation TEXT,
ADD COLUMN IF NOT EXISTS raw_data JSONB;

-- Add missing columns to epic_fhir_diagnostic_reports
ALTER TABLE epic_fhir_diagnostic_reports 
ADD COLUMN IF NOT EXISTS code_display VARCHAR(500),
ADD COLUMN IF NOT EXISTS category VARCHAR(255),
ADD COLUMN IF NOT EXISTS code VARCHAR(255),
ADD COLUMN IF NOT EXISTS conclusion_code VARCHAR(255),
ADD COLUMN IF NOT EXISTS effective_datetime TIMESTAMP WITHOUT TIME ZONE,
ADD COLUMN IF NOT EXISTS issued TIMESTAMP WITHOUT TIME ZONE,
ADD COLUMN IF NOT EXISTS status VARCHAR(50),
ADD COLUMN IF NOT EXISTS conclusion TEXT,
ADD COLUMN IF NOT EXISTS raw_data JSONB;

-- Add missing columns to epic_fhir_documents
ALTER TABLE epic_fhir_documents 
ADD COLUMN IF NOT EXISTS type_display VARCHAR(500);

-- Add missing columns to epic_fhir_imaging_studies
ALTER TABLE epic_fhir_imaging_studies 
ADD COLUMN IF NOT EXISTS procedure_display VARCHAR(500);

-- Add missing columns to epic_fhir_sync_logs
ALTER TABLE epic_fhir_sync_logs 
ADD COLUMN IF NOT EXISTS records_found INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS records_synced INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS records_failed INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();

-- Update existing NULL values to defaults
UPDATE epic_fhir_observations SET 
    code_display = COALESCE(code_display, ''),
    value_quantity = COALESCE(value_quantity, 0),
    value_unit = COALESCE(value_unit, ''),
    value_code = COALESCE(value_code, ''),
    interpretation = COALESCE(interpretation, ''),
    raw_data = COALESCE(raw_data, '{}'::jsonb)
WHERE code_display IS NULL OR value_quantity IS NULL OR value_unit IS NULL OR value_code IS NULL OR interpretation IS NULL OR raw_data IS NULL;

UPDATE epic_fhir_diagnostic_reports SET 
    code_display = COALESCE(code_display, ''),
    category = COALESCE(category, ''),
    code = COALESCE(code, ''),
    conclusion_code = COALESCE(conclusion_code, ''),
    status = COALESCE(status, ''),
    conclusion = COALESCE(conclusion, ''),
    raw_data = COALESCE(raw_data, '{}'::jsonb)
WHERE code_display IS NULL OR category IS NULL OR code IS NULL OR conclusion_code IS NULL OR status IS NULL OR conclusion IS NULL OR raw_data IS NULL;

UPDATE epic_fhir_documents SET 
    type_display = COALESCE(type_display, '')
WHERE type_display IS NULL;

UPDATE epic_fhir_imaging_studies SET 
    procedure_display = COALESCE(procedure_display, '')
WHERE procedure_display IS NULL;

UPDATE epic_fhir_sync_logs SET 
    records_found = COALESCE(records_found, 0),
    records_synced = COALESCE(records_synced, 0),
    records_failed = COALESCE(records_failed, 0),
    created_at = COALESCE(created_at, NOW())
WHERE records_found IS NULL OR records_synced IS NULL OR records_failed IS NULL OR created_at IS NULL;
