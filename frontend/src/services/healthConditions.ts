import { api } from './api';
import type {
  HealthCondition,
  ConditionCatalogItem,
  UserHealthProfile,
  QuestionnaireData,
} from '@/types';

export const healthConditionsService = {
  // Conditions CRUD
  listConditions: async (): Promise<HealthCondition[]> => {
    const response = await api.get('/api/v1/health-conditions');
    return response.data;
  },

  getCatalog: async (): Promise<ConditionCatalogItem[]> => {
    const response = await api.get('/api/v1/health-conditions/catalog');
    return response.data;
  },

  addCondition: async (data: {
    condition_name: string;
    condition_category: string;
    severity: string;
    diagnosed_date?: string;
    notes?: string;
  }): Promise<HealthCondition> => {
    const response = await api.post('/api/v1/health-conditions', data);
    return response.data;
  },

  updateCondition: async (
    id: string,
    data: Partial<{
      condition_name: string;
      condition_category: string;
      severity: string;
      diagnosed_date: string;
      notes: string;
      is_active: boolean;
    }>,
  ): Promise<HealthCondition> => {
    const response = await api.put(`/api/v1/health-conditions/${id}`, data);
    return response.data;
  },

  deleteCondition: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/health-conditions/${id}`);
  },

  // Questionnaire
  getQuestionnaire: async (): Promise<QuestionnaireData> => {
    const response = await api.get('/api/v1/health-questionnaire');
    return response.data;
  },

  submitQuestionnaire: async (
    answers: Record<string, unknown>,
  ): Promise<{ saved: boolean; profile_updated: boolean; message: string }> => {
    const response = await api.post('/api/v1/health-questionnaire', { answers });
    return response.data;
  },

  // Profile
  getHealthProfile: async (): Promise<UserHealthProfile> => {
    const response = await api.get('/api/v1/health-questionnaire/profile');
    return response.data;
  },
};
