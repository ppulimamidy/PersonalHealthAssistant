import { api } from './api';
import type { SymptomCorrelationsResponse } from '@/types';

export const symptomCorrelationsService = {
  // Get correlations for a specific symptom type
  async getSymptomCorrelations(
    symptomType: string,
    days: number = 30
  ): Promise<SymptomCorrelationsResponse> {
    const response = await api.get<SymptomCorrelationsResponse>(
      `/symptoms/${symptomType}/correlations`,
      {
        params: { days },
      }
    );
    return response.data;
  },

  // Validate a trigger pattern
  async validateTriggerPattern(
    symptomType: string,
    patternId: string,
    validated: boolean
  ): Promise<void> {
    await api.post(`/symptoms/${symptomType}/triggers/${patternId}/validate`, {
      validated,
    });
  },
};
