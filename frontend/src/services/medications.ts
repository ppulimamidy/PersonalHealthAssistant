'use client';

import { api } from './api';
import type {
  Medication,
  Supplement,
  CreateMedicationRequest,
  CreateSupplementRequest,
  AdherenceStats,
} from '@/types';

export const medicationsService = {
  // Medications
  getMedications: async (): Promise<{ medications: Medication[] }> => {
    const response = await api.get('/api/v1/medications');
    return response.data;
  },

  createMedication: async (payload: CreateMedicationRequest): Promise<Medication> => {
    const response = await api.post('/api/v1/medications', payload);
    return response.data;
  },

  updateMedication: async (id: string, payload: Partial<CreateMedicationRequest>): Promise<Medication> => {
    const response = await api.put(`/api/v1/medications/${id}`, payload);
    return response.data;
  },

  deleteMedication: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/medications/${id}`);
  },

  // Supplements
  getSupplements: async (): Promise<{ supplements: Supplement[] }> => {
    const response = await api.get('/api/v1/supplements');
    return response.data;
  },

  createSupplement: async (payload: CreateSupplementRequest): Promise<Supplement> => {
    const response = await api.post('/api/v1/supplements', payload);
    return response.data;
  },

  updateSupplement: async (id: string, payload: Partial<CreateSupplementRequest>): Promise<Supplement> => {
    const response = await api.put(`/api/v1/supplements/${id}`, payload);
    return response.data;
  },

  deleteSupplement: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/supplements/${id}`);
  },

  // Adherence
  getAdherenceStats: async (days: number = 30): Promise<AdherenceStats> => {
    const response = await api.get('/api/v1/adherence/stats', {
      params: { days },
    });
    return response.data;
  },
};
