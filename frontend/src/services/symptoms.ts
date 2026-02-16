'use client';

import { api } from './api';
import type {
  SymptomJournalEntry,
  CreateSymptomRequest,
  SymptomAnalytics,
  SymptomPattern,
} from '@/types';

export const symptomsService = {
  // Journal entries
  getSymptoms: async (params?: {
    days?: number;
    symptom_type?: string;
    min_severity?: number;
  }): Promise<{ symptoms: SymptomJournalEntry[] }> => {
    const response = await api.get('/api/v1/symptoms/journal', { params });
    return response.data;
  },

  createSymptom: async (payload: CreateSymptomRequest): Promise<SymptomJournalEntry> => {
    const response = await api.post('/api/v1/symptoms/journal', payload);
    return response.data;
  },

  updateSymptom: async (id: string, payload: Partial<CreateSymptomRequest>): Promise<SymptomJournalEntry> => {
    const response = await api.put(`/api/v1/symptoms/journal/${id}`, payload);
    return response.data;
  },

  deleteSymptom: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/symptoms/journal/${id}`);
  },

  // Analytics
  getAnalytics: async (days: number = 30): Promise<SymptomAnalytics> => {
    const response = await api.get('/api/v1/symptoms/analytics', {
      params: { days },
    });
    return response.data;
  },

  // Patterns
  getPatterns: async (): Promise<{ patterns: SymptomPattern[] }> => {
    const response = await api.get('/api/v1/symptoms/patterns');
    return response.data;
  },

  detectPatterns: async (): Promise<{ message: string; detected_count: number }> => {
    const response = await api.post('/api/v1/symptoms/patterns/detect');
    return response.data;
  },
};
