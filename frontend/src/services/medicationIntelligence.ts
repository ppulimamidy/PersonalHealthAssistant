import { api } from './api';
import type {
  InteractionAlertsResponse,
  MedicationCorrelationsResponse,
  MedicationInteraction,
} from '@/types';

export const medicationIntelligenceService = {
  // Get interaction alerts for current user
  async getInteractionAlerts(): Promise<InteractionAlertsResponse> {
    const response = await api.get<InteractionAlertsResponse>(
      '/medication-interactions/alerts'
    );
    return response.data;
  },

  // Acknowledge an interaction alert
  async acknowledgeAlert(alertId: string): Promise<void> {
    await api.post(`/medication-interactions/alerts/${alertId}/acknowledge`);
  },

  // Dismiss an interaction alert
  async dismissAlert(alertId: string): Promise<void> {
    await api.post(`/medication-interactions/alerts/${alertId}/dismiss`);
  },

  // Get medication-vitals correlations for a specific medication
  async getMedicationVitalsCorrelations(
    medicationId: string,
    days: number = 30
  ): Promise<MedicationCorrelationsResponse> {
    const response = await api.get<MedicationCorrelationsResponse>(
      `/medications/${medicationId}/vitals-correlations`,
      {
        params: { days },
      }
    );
    return response.data;
  },

  // Search for known medication interactions
  async searchInteractions(query: string): Promise<{ interactions: MedicationInteraction[]; total: number }> {
    const response = await api.get<{ interactions: MedicationInteraction[]; total: number }>(
      '/medication-interactions/search',
      {
        params: { query },
      }
    );
    return response.data;
  },
};
