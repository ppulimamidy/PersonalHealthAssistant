'use client';

import { api } from './api';
import type { CarePlan, CreateCarePlanRequest, UpdateCarePlanRequest } from '@/types';

export const carePlansService = {
  listPlans: async (status = 'active'): Promise<CarePlan[]> => {
    const res = await api.get('/api/v1/care-plans', { params: { status } });
    return res.data.plans ?? [];
  },

  createPlan: async (payload: CreateCarePlanRequest): Promise<CarePlan> => {
    const res = await api.post('/api/v1/care-plans', payload);
    return res.data;
  },

  updatePlan: async (planId: string, payload: UpdateCarePlanRequest): Promise<CarePlan> => {
    const res = await api.patch(`/api/v1/care-plans/${planId}`, payload);
    return res.data;
  },

  deletePlan: async (planId: string): Promise<void> => {
    await api.delete(`/api/v1/care-plans/${planId}`);
  },

  suggestPlanForPatient: async (payload: {
    share_token: string;
    title: string;
    description?: string;
    metric_type?: string;
    target_value?: number;
    target_unit?: string;
    target_date?: string;
    notes?: string;
  }): Promise<CarePlan> => {
    const res = await api.post('/api/v1/care-plans/for-patient', payload);
    return res.data;
  },
};
