/**
 * Auth store — adapted from frontend/src/stores/authStore.ts.
 * Change: persist storage uses AsyncStorage instead of localStorage.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { User } from '../types';

interface UserProfile {
  date_of_birth?: string;
  biological_sex?: string;
  weight_kg?: number;
  height_cm?: number;
  primary_goals?: string[];
  onboarding_completed_at?: string;
  last_checkin_at?: string;
  user_role?: string;
}

// Supabase User type from supabase-js (minimal fields we use)
interface SupabaseUser {
  id: string;
  email?: string;
  user_metadata?: Record<string, unknown>;
}

interface AuthState {
  user: SupabaseUser | null;
  profile: UserProfile | null;
  isLoading: boolean;
  setUser: (user: SupabaseUser | null) => void;
  setProfile: (profile: UserProfile | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      profile: null,
      isLoading: false,
      setUser: (user) => set({ user }),
      setProfile: (profile) => set({ profile }),
      setLoading: (isLoading) => set({ isLoading }),
      logout: () => set({ user: null, profile: null }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => AsyncStorage),
      // Only persist user and profile — not loading state
      partialize: (state) => ({ user: state.user, profile: state.profile }),
    }
  )
);
