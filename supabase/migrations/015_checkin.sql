-- Migration 015: Add last_checkin_at to profiles for periodic vitals check-in
ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS last_checkin_at TIMESTAMPTZ;
