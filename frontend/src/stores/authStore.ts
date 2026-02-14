import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, OuraConnection, UserProfile } from '@/types';

interface AuthState {
  user: User | null;
  profile: UserProfile | null;
  ouraConnection: OuraConnection | null;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  setProfile: (profile: UserProfile | null) => void;
  setOuraConnection: (connection: OuraConnection | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      profile: null,
      ouraConnection: null,
      isLoading: true,
      setUser: (user) => set({ user }),
      setProfile: (profile) => set({ profile }),
      setOuraConnection: (ouraConnection) => set({ ouraConnection }),
      setLoading: (isLoading) => set({ isLoading }),
      logout: () => set({ user: null, profile: null, ouraConnection: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, profile: state.profile }),
    }
  )
);
