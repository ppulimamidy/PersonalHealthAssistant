import { api } from './api';
import type { DailyHealthScore } from '@/types';

export const healthScoreService = {
  getScore: async (): Promise<DailyHealthScore> => {
    const response = await api.get('/api/v1/health-score');
    return response.data;
  },
};
