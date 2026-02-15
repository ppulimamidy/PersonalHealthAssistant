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
};
