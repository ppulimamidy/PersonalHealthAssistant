import { api } from './api';
import type { DailyHealthScore, TrajectoryResponse } from '@/types';

export const healthScoreService = {
  getScore: async (): Promise<DailyHealthScore> => {
    const response = await api.get('/api/v1/health-score');
    return response.data;
  },

  getTrajectory: async (): Promise<TrajectoryResponse> => {
    const response = await api.get('/api/v1/health-score/trajectory');
    return response.data;
  },
};
