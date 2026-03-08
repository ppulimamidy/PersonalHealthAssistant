'use client';

import { api } from './api';
import type {
  Medication,
  Supplement,
  CreateMedicationRequest,
  CreateSupplementRequest,
  AdherenceStats,
  PrescriptionScanResult,
} from '@/types';

export const medicationsService = {
  // Medications (API returns array; normalize to { medications } for UI)
  getMedications: async (): Promise<{ medications: Medication[] }> => {
    const response = await api.get('/api/v1/medications');
    const data = response.data;
    const medications = Array.isArray(data) ? data : (data?.medications ?? []);
    return { medications };
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

  // Supplements (API may return array; normalize to { supplements } for UI)
  getSupplements: async (): Promise<{ supplements: Supplement[] }> => {
    const response = await api.get('/api/v1/supplements');
    const data = response.data;
    const supplements = Array.isArray(data) ? data : (data?.supplements ?? []);
    return { supplements };
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

  // Prescription / bottle image scan
  scanPrescription: async (file: File): Promise<PrescriptionScanResult> => {
    const form = new FormData();
    form.append('image', file);
    const response = await api.post('/api/v1/medications/scan-prescription', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};
