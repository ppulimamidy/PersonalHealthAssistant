-- Migration 013: Nutrition Analyst Preferences
-- Stores per-user nutritional preferences collected by the Nutrition Analyst agent.
-- These are used to personalise every nutrition response and specialist analysis.

CREATE TABLE IF NOT EXISTS public.nutrition_analyst_prefs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT nutrition_analyst_prefs_user_unique UNIQUE (user_id)
);

-- Index for fast single-user lookups
CREATE INDEX IF NOT EXISTS idx_nutrition_analyst_prefs_user
    ON public.nutrition_analyst_prefs (user_id);

-- Auto-update updated_at on every write
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'trg_nutrition_analyst_prefs_updated_at'
    ) THEN
        CREATE TRIGGER trg_nutrition_analyst_prefs_updated_at
            BEFORE UPDATE ON public.nutrition_analyst_prefs
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
    END IF;
END;
$$;

-- Row-level security: users can only read/write their own preferences
ALTER TABLE public.nutrition_analyst_prefs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "nutrition_prefs_select_own"
    ON public.nutrition_analyst_prefs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "nutrition_prefs_insert_own"
    ON public.nutrition_analyst_prefs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "nutrition_prefs_update_own"
    ON public.nutrition_analyst_prefs FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "nutrition_prefs_delete_own"
    ON public.nutrition_analyst_prefs FOR DELETE
    USING (auth.uid() = user_id);

-- Service-role bypass (used by backend upserts via service key)
CREATE POLICY "nutrition_prefs_service_all"
    ON public.nutrition_analyst_prefs FOR ALL
    USING (current_setting('request.jwt.claims', true)::jsonb->>'role' = 'service_role');

COMMENT ON TABLE public.nutrition_analyst_prefs IS
    'Nutritional preferences collected by the Nutrition Analyst AI agent per user. '
    'Stores goals, allergies, dietary restrictions, disliked/preferred foods, and more.';
