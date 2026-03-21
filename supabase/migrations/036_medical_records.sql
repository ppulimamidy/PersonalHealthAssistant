-- Medical Records — pathology, genomic/molecular, and imaging reports
-- Extends beyond blood labs to support the full medical record spectrum

CREATE TABLE IF NOT EXISTS public.medical_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  record_type TEXT NOT NULL CHECK (record_type IN ('pathology', 'genomic', 'imaging')),
  title TEXT,
  report_date DATE,
  provider_name TEXT,
  facility_name TEXT,
  extracted_data JSONB NOT NULL DEFAULT '{}',
  raw_text TEXT,
  ai_summary TEXT,
  file_url TEXT,
  original_filename TEXT,
  tags JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_medical_records_user
  ON public.medical_records(user_id, record_type, report_date DESC);

-- RLS
ALTER TABLE public.medical_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own medical records"
  ON public.medical_records FOR ALL
  USING (user_id = auth.uid()::text);

-- Service role bypass
CREATE POLICY "Service role full access medical_records"
  ON public.medical_records FOR ALL
  TO service_role
  USING (true) WITH CHECK (true);
