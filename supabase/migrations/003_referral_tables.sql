-- Referral system tables
-- Run this in Supabase SQL Editor

-- Referral codes (one per user)
CREATE TABLE IF NOT EXISTS referrals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    referrer_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    code VARCHAR(16) NOT NULL UNIQUE,
    referral_count INTEGER DEFAULT 0,
    credits_earned INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT unique_referrer UNIQUE (referrer_id)
);

-- Referral redemptions (tracks who used whose code)
CREATE TABLE IF NOT EXISTS referral_redemptions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    referral_code VARCHAR(16) NOT NULL REFERENCES referrals(code) ON DELETE CASCADE,
    referrer_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    redeemed_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT unique_redemption UNIQUE (redeemed_by)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_referrals_code ON referrals(code);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_redemptions_referrer ON referral_redemptions(referrer_id);
CREATE INDEX IF NOT EXISTS idx_redemptions_redeemed_by ON referral_redemptions(redeemed_by);

-- RLS policies
ALTER TABLE referrals ENABLE ROW LEVEL SECURITY;
ALTER TABLE referral_redemptions ENABLE ROW LEVEL SECURITY;

-- Users can read their own referral row
CREATE POLICY referrals_select_own ON referrals
    FOR SELECT USING (auth.uid() = referrer_id);

-- Users can insert their own referral row
CREATE POLICY referrals_insert_own ON referrals
    FOR INSERT WITH CHECK (auth.uid() = referrer_id);

-- Users can update their own referral row
CREATE POLICY referrals_update_own ON referrals
    FOR UPDATE USING (auth.uid() = referrer_id);

-- Anyone can read referrals by code (for validation)
CREATE POLICY referrals_select_by_code ON referrals
    FOR SELECT USING (true);

-- Users can insert redemptions for themselves
CREATE POLICY redemptions_insert_own ON referral_redemptions
    FOR INSERT WITH CHECK (auth.uid() = redeemed_by);

-- Users can read redemptions where they're the referrer
CREATE POLICY redemptions_select_referrer ON referral_redemptions
    FOR SELECT USING (auth.uid() = referrer_id);

-- Service role bypasses all RLS (for backend API calls)
