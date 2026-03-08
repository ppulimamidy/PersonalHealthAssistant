-- Migration 023: Add source and is_pinned columns to user_goals
-- Supports "pin a doctor instruction" feature

ALTER TABLE user_goals ADD COLUMN IF NOT EXISTS source VARCHAR(10) DEFAULT 'user';
ALTER TABLE user_goals ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT false;

-- Index so pinned goals are fetched quickly
CREATE INDEX IF NOT EXISTS idx_user_goals_pinned ON user_goals (user_id, is_pinned, created_at DESC);
