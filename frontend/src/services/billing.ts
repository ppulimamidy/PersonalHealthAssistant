import { api } from './api';
import type { SubscriptionData } from '@/types';

export const billingService = {
  getSubscription: async (): Promise<SubscriptionData> => {
    const response = await api.get('/api/v1/billing/subscription');
    return response.data;
  },

  createCheckoutSession: async (tier: 'pro' | 'pro_plus'): Promise<string> => {
    const response = await api.post('/api/v1/billing/create-checkout-session', { tier });
    return response.data.checkout_url;
  },

  createPortalSession: async (): Promise<string> => {
    const response = await api.post('/api/v1/billing/create-portal-session');
    return response.data.portal_url;
  },

  /** Confirm checkout so backend activates subscription (when webhook has not run yet). */
  confirmCheckoutSession: async (sessionId: string): Promise<void> => {
    await api.post('/api/v1/billing/confirm-checkout-session', { session_id: sessionId });
  },

  /** Emergency endpoint to force-activate Pro subscription for stuck incomplete subscriptions. */
  forceActivatePro: async (): Promise<void> => {
    await api.post('/api/v1/billing/force-activate-pro');
  },
};
