'use client';

import { api } from './api';
import type {
  PredictionsResponse,
  RisksResponse,
  TrendsResponse,
  PersonalizedHealthScore,
} from '@/types';

export const predictionsService = {
  // Get predictions
  getPredictions: async (days: number = 30): Promise<PredictionsResponse> => {
    const response = await api.get(`/api/v1/predictions/predictions?days=${days}`);
    return response.data;
  },

  // Get risk assessments
  getRisks: async (): Promise<RisksResponse> => {
    const response = await api.get('/api/v1/predictions/risks');
    return response.data;
  },

  // Get trend analyses
  getTrends: async (days: number = 30): Promise<TrendsResponse> => {
    const response = await api.get(`/api/v1/predictions/trends?days=${days}`);
    return response.data;
  },

  // Get health score
  getHealthScore: async (scoreType: string): Promise<PersonalizedHealthScore> => {
    const response = await api.get(`/api/v1/predictions/health-scores/${scoreType}`);
    return response.data;
  },
};
