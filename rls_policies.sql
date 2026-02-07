-- Enable Row Level Security on tables
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medical_conditions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.health_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.symptoms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.healthcare_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_provider_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.healthcare_facilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.insurance_companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_insurance ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Anon can read device data types"
    ON public.device_data_types
    FOR SELECT
    USING (true);
CREATE POLICY "Users can view their own profile"
    ON public.user_profiles FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can update their own profile"
    ON public.user_profiles FOR UPDATE
    USING (user_id = auth.uid());

CREATE POLICY "Users can view their own medical conditions"
    ON public.medical_conditions FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can manage their own medical conditions"
    ON public.medical_conditions FOR ALL
    USING (user_id = auth.uid());

CREATE POLICY "Users can view their own medications"
    ON public.medications FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can manage their own medications"
    ON public.medications FOR ALL
    USING (user_id = auth.uid());

CREATE POLICY "Users can view their own health metrics"
    ON public.health_metrics FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own health metrics"
    ON public.health_metrics FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can view their own symptoms"
    ON public.symptoms FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can manage their own symptoms"
    ON public.symptoms FOR ALL
    USING (user_id = auth.uid());

CREATE POLICY "Users can view their own devices"
    ON public.devices FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can manage their own devices"
    ON public.devices FOR ALL
    USING (user_id = auth.uid());

CREATE POLICY "Users can view their own provider relationships"
    ON public.user_provider_relationships FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can manage their own provider relationships"
    ON public.user_provider_relationships FOR ALL
    USING (user_id = auth.uid());

CREATE POLICY "Users can view their own insurance"
    ON public.user_insurance FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can manage their own insurance"
    ON public.user_insurance FOR ALL
    USING (user_id = auth.uid());

-- Grant necessary permissions to roles
GRANT SELECT ON public.healthcare_providers TO anon, authenticated;
GRANT SELECT ON public.healthcare_facilities TO anon, authenticated;
GRANT SELECT ON public.insurance_companies TO anon, authenticated; 