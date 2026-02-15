-- Monetization tables for Personal Health Assistant
-- Run in Supabase SQL Editor

-- 1. Subscriptions table
CREATE TABLE IF NOT EXISTS public.subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_customer_id TEXT NOT NULL,
  stripe_subscription_id TEXT UNIQUE,
  tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'pro', 'pro_plus')),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'past_due', 'canceled', 'trialing', 'incomplete')),
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_customer_id ON public.subscriptions(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_subscription_id ON public.subscriptions(stripe_subscription_id);

-- 2. Usage tracking table
CREATE TABLE IF NOT EXISTS public.usage_tracking (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  feature TEXT NOT NULL CHECK (feature IN ('ai_insights', 'nutrition_scans', 'doctor_prep', 'pdf_export')),
  week_start DATE NOT NULL,
  usage_count INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, feature, week_start)
);

CREATE INDEX IF NOT EXISTS idx_usage_tracking_user_week ON public.usage_tracking(user_id, week_start);

-- 3. Beta signups table
CREATE TABLE IF NOT EXISTS public.beta_signups (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL UNIQUE,
  source TEXT DEFAULT 'landing_page',
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'invited', 'joined')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_beta_signups_email ON public.beta_signups(email);

-- 4. Row Level Security
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can read own subscription" ON public.subscriptions
  FOR SELECT USING (auth.uid() = user_id);

ALTER TABLE public.usage_tracking ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can read own usage" ON public.usage_tracking
  FOR SELECT USING (auth.uid() = user_id);

ALTER TABLE public.beta_signups ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can insert beta signup" ON public.beta_signups
  FOR INSERT WITH CHECK (true);
