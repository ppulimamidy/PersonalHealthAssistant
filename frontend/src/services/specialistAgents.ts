import { api } from './api';
import type { MetaAnalysisReport } from '@/types';

export const specialistAgentsService = {
  // Generate meta-analysis report
  async generateMetaAnalysis(days: number = 30): Promise<MetaAnalysisReport> {
    const response = await api.post<MetaAnalysisReport>(
      '/specialist-agents/meta-analysis',
      {},
      {
        params: { days },
      }
    );
    return response.data;
  },

  // Get cached meta-analysis report
  async getCachedMetaAnalysis(): Promise<MetaAnalysisReport | null> {
    try {
      const response = await api.get<MetaAnalysisReport>(
        '/specialist-agents/meta-analysis/latest'
      );
      return response.data;
    } catch (error) {
      // No cached report found
      return null;
    }
  },
};
