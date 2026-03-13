/**
 * Subscription store — adapted from frontend/src/stores/subscriptionStore.ts.
 * Change: persist storage uses AsyncStorage instead of localStorage.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { SubscriptionData, SubscriptionTier } from '../types';

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
      getTier: () => get().subscription?.tier ?? 'free',
      canUseFeature: (feature: string): boolean => {
        const sub = get().subscription;
        if (!sub?.usage) return false;
        const info = sub.usage[feature as keyof typeof sub.usage];
        if (!info) return true; // Feature not gated
        if (info.limit === -1) return true; // Unlimited
        if (info.limit === 0) return false; // Blocked
        return info.used < info.limit;
      },
    }),
    {
      name: 'subscription-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        subscription: state.subscription,
        showUpgradeModal: state.showUpgradeModal,
      }),
    }
  )
);
