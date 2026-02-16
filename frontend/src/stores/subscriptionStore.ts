'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { SubscriptionData, SubscriptionTier } from '@/types';

function normalizeTier(t: string | undefined): SubscriptionTier {
  const s = t ? String(t).toLowerCase() : '';
  if (s === 'pro_plus') return 'pro_plus';
  if (s === 'pro') return 'pro';
  return 'free';
}

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
      setSubscription: (subscription) => {
        if (subscription?.tier && typeof subscription.tier === 'string') {
          subscription = { ...subscription, tier: normalizeTier(subscription.tier) };
        }
        set({ subscription });
      },
      setLoading: (isLoading) => set({ isLoading }),
      setShowUpgradeModal: (showUpgradeModal) => set({ showUpgradeModal }),
      getTier: () => normalizeTier(get().subscription?.tier),
      canUseFeature: (feature: string) => {
        const sub = get().subscription;
        if (!sub) return true; // Optimistic — let backend enforce
        const usage = sub.usage[feature as keyof typeof sub.usage];
        if (!usage) return true;
        if (usage.limit === -1) return true;
        if (usage.limit === 0) return false; // Explicitly blocked
        return usage.used < usage.limit;
      },
    }),
    {
      name: 'subscription-storage',
      partialize: (state) => ({ subscription: state.subscription }),
    }
  )
);
