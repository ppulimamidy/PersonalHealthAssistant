-- Migration 014: User Profiles
-- Stores core demographic and onboarding data collected at registration.
-- This is the canonical source for DOB, biological sex, weight, and primary goals.
-- Keyed on auth.users.id (id IS the user UUID — no separate user_id column).

CREATE TABLE IF NOT EXISTS public.profiles (
    id                      UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name               TEXT,
    date_of_birth           DATE        NOT NULL,
    biological_sex          TEXT        NOT NULL
                            CHECK (biological_sex IN ('male', 'female', 'other', 'prefer_not_to_say')),
    weight_kg               NUMERIC(5,1),
    height_cm               INTEGER,
    primary_goals           JSONB       NOT NULL DEFAULT '[]'::jsonb,
    onboarding_completed_at TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Fast lookup by primary key (also serves as the user lookup)
CREATE INDEX IF NOT EXISTS idx_profiles_id ON public.profiles (id);

-- Reuse the set_updated_at() function created in migration 013.
-- Guard prevents duplicate trigger if this migration is re-run.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_profiles_updated_at'
    ) THEN
        CREATE TRIGGER trg_profiles_updated_at
            BEFORE UPDATE ON public.profiles
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
    END IF;
END;
$$;

-- Row-level security: each user can only read/write their own row.
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles_select_own"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "profiles_insert_own"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "profiles_update_own"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- Service-role bypass (used by backend upserts via service key)
CREATE POLICY "profiles_service_all"
    ON public.profiles FOR ALL
    USING (current_setting('request.jwt.claims', true)::jsonb->>'role' = 'service_role');

COMMENT ON TABLE public.profiles IS
    'Core demographic profile per user. Collected at registration (DOB, sex, weight) '
    'and during onboarding (primary goals, health conditions). '
    'onboarding_completed_at is set when the user finishes all onboarding steps.';
