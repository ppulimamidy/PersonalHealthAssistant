import { api } from './api';
import type { ReferralInfo, ReferralStats } from '@/types';

export const referralService = {
  getCode: async (): Promise<ReferralInfo> => {
    const response = await api.get('/api/v1/referral/code');
    return response.data;
  },

  getStats: async (): Promise<ReferralStats> => {
    const response = await api.get('/api/v1/referral/stats');
    return response.data;
  },

  redeem: async (code: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post('/api/v1/referral/redeem', { code });
    return response.data;
  },
};
