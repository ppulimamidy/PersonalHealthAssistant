import { api } from './api';
import type { AIInsight } from '@/types';

export const insightsService = {
  // Get AI-generated insights (max 5)
  getInsights: async (): Promise<AIInsight[]> => {
    const response = await api.get('/api/v1/insights', {
      params: { limit: 5 },
    });
    return response.data;
  },

  // Get insight details with full explanation
  getInsightDetail: async (insightId: string): Promise<AIInsight> => {
    const response = await api.get(`/api/v1/insights/${insightId}`);
    return response.data;
  },

  // Dismiss an insight
  dismissInsight: async (insightId: string): Promise<void> => {
    await api.post(`/api/v1/insights/${insightId}/dismiss`);
  },

  // Request fresh insights generation
  refreshInsights: async (): Promise<AIInsight[]> => {
    const response = await api.post('/api/v1/insights/refresh');
    return response.data;
  },
};
