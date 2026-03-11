import { api } from './api';
import type {
  ActiveIntervention,
  StartInterventionRequest,
  InterventionCheckin,
  InterventionOutcome,
} from '@/types';

export const interventionsService = {
  /** Start a new N-of-1 intervention trial from a recommendation. */
  start: async (body: StartInterventionRequest): Promise<ActiveIntervention> => {
    const response = await api.post('/api/v1/interventions', body);
    return response.data;
  },

  /** List all interventions, optionally filtered by status. */
  list: async (status?: 'active' | 'completed' | 'abandoned'): Promise<ActiveIntervention[]> => {
    const params = status ? { status } : undefined;
    const response = await api.get('/api/v1/interventions', { params });
    return response.data;
  },

  /** Get a single intervention with its check-in history. */
  get: async (id: string): Promise<ActiveIntervention> => {
    const response = await api.get(`/api/v1/interventions/${id}`);
    return response.data;
  },

  /** Log daily adherence for an active intervention. */
  checkin: async (
    id: string,
    adhered: boolean,
    notes?: string,
    checkinDate?: string,
  ): Promise<InterventionCheckin> => {
    const response = await api.post(`/api/v1/interventions/${id}/checkin`, {
      adhered,
      notes,
      checkin_date: checkinDate,
    });
    return response.data;
  },

  /** Complete the trial: captures outcome, writes to agent_memory. */
  complete: async (id: string): Promise<InterventionOutcome> => {
    const response = await api.post(`/api/v1/interventions/${id}/complete`);
    return response.data;
  },

  /** Abandon an active intervention. */
  abandon: async (id: string): Promise<{ status: string }> => {
    const response = await api.patch(`/api/v1/interventions/${id}/abandon`);
    return response.data;
  },
};
