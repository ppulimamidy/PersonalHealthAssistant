import { api } from './api';
import type { ManagedProfile, LinkProfileRequest, PatientAlert } from '@/types';

export const caregiverService = {
  listManaged: async (): Promise<ManagedProfile[]> => {
    const response = await api.get('/api/v1/caregiver/managed');
    return response.data;
  },

  linkProfile: async (payload: LinkProfileRequest): Promise<ManagedProfile> => {
    const response = await api.post('/api/v1/caregiver/managed', payload);
    return response.data;
  },

  unlinkProfile: async (linkId: string): Promise<void> => {
    await api.delete(`/api/v1/caregiver/managed/${linkId}`);
  },

  getAlerts: async (): Promise<PatientAlert[]> => {
    const response = await api.get('/api/v1/caregiver/alerts');
    return response.data;
  },
};
