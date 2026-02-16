import { api } from './api';
import type { RecommendationsResponse, RecoveryPlan } from '@/types';

export const recommendationsService = {
  getRecommendations: async (): Promise<RecommendationsResponse> => {
    const response = await api.get('/api/v1/recommendations');
    return response.data;
  },

  getRecoveryPlan: async (): Promise<RecoveryPlan> => {
    const response = await api.get('/api/v1/recommendations/recovery-plan');
    return response.data;
  },
};
