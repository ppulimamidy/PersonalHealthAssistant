import { api } from './api';
import type { CorrelationResults, Correlation, CorrelationSummary } from '@/types';

export const correlationsService = {
  getCorrelations: async (days: 7 | 14 = 14): Promise<CorrelationResults> => {
    const response = await api.get('/api/v1/correlations', { params: { days } });
    return response.data;
  },

  refreshCorrelations: async (days: 7 | 14 = 14): Promise<CorrelationResults> => {
    const response = await api.post('/api/v1/correlations/refresh', null, {
      params: { days },
    });
    return response.data;
  },

  getCorrelationDetail: async (id: string): Promise<Correlation> => {
    const response = await api.get(`/api/v1/correlations/detail/${id}`);
    return response.data;
  },

  getSummary: async (): Promise<CorrelationSummary> => {
    const response = await api.get('/api/v1/correlations/summary');
    return response.data;
  },
};
