'use client';

import { api } from './api';
import type { UserGoal, CreateGoalRequest, UpdateGoalRequest } from '@/types';

export const goalsService = {
  listGoals: async (status = 'active'): Promise<UserGoal[]> => {
    const response = await api.get('/api/v1/goals', { params: { status } });
    return response.data.goals ?? [];
  },

  createGoal: async (payload: CreateGoalRequest): Promise<UserGoal> => {
    const response = await api.post('/api/v1/goals', payload);
    return response.data;
  },

  updateGoal: async (goalId: string, payload: UpdateGoalRequest): Promise<UserGoal> => {
    const response = await api.patch(`/api/v1/goals/${goalId}`, payload);
    return response.data;
  },

  deleteGoal: async (goalId: string): Promise<void> => {
    await api.delete(`/api/v1/goals/${goalId}`);
  },
};
