'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { SubscriptionData, SubscriptionTier } from '@/types';

interface SubscriptionState {
  subscription: SubscriptionData | null;
  isLoading: boolean;
  showUpgradeModal: boolean;
  setSubscription: (sub: SubscriptionData | null) => void;
  setLoading: (loading: boolean) => void;
  setShowUpgradeModal: (show: boolean) => void;
  getTier: () => SubscriptionTier;
  canUseFeature: (feature: string) => boolean;
}

export const useSubscriptionStore = create<SubscriptionState>()(
  persist(
    (set, get) => ({
      subscription: null,
      isLoading: false,
      showUpgradeModal: false,
      setSubscription: (subscription) => set({ subscription }),
      setLoading: (isLoading) => set({ isLoading }),
      setShowUpgradeModal: (showUpgradeModal) => set({ showUpgradeModal }),
      getTier: () => get().subscription?.tier || 'free',
      canUseFeature: (feature: string) => {
        const sub = get().subscription;
        if (!sub) return true; // Optimistic — let backend enforce
        const usage = sub.usage[feature as keyof typeof sub.usage];
        if (!usage) return true;
        if (usage.limit === -1) return true;
        return usage.used < usage.limit;
      },
    }),
    {
      name: 'subscription-storage',
      partialize: (state) => ({ subscription: state.subscription }),
    }
  )
);
