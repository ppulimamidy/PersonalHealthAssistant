import { api } from './api';
import type {
  LabResult,
  LabResultsResponse,
  BiomarkerTrendsResponse,
  LabInsightsResponse,
  CreateLabResultRequest,
  LabTestCategory,
} from '@/types';

export const labResultsService = {
  // Get lab results with optional filters
  async getLabResults(params?: {
    test_type?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<LabResultsResponse> {
    const queryParams = new URLSearchParams();
    if (params?.test_type) queryParams.append('test_type', params.test_type);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);

    const query = queryParams.toString();
    const url = `/lab-results${query ? `?${query}` : ''}`;

    const response = await api.get<LabResultsResponse>(url);
    return response.data;
  },

  // Get single lab result by ID
  async getLabResult(id: string): Promise<LabResult> {
    const response = await api.get<LabResult>(`/lab-results/${id}`);
    return response.data;
  },

  // Create new lab result
  async createLabResult(data: CreateLabResultRequest): Promise<LabResult> {
    const response = await api.post<LabResult>('/lab-results', data);
    return response.data;
  },

  // Update lab result
  async updateLabResult(id: string, data: Partial<CreateLabResultRequest>): Promise<LabResult> {
    const response = await api.put<LabResult>(`/lab-results/${id}`, data);
    return response.data;
  },

  // Delete lab result
  async deleteLabResult(id: string): Promise<void> {
    await api.delete(`/lab-results/${id}`);
  },

  // Get biomarker trends
  async getBiomarkerTrends(biomarkerCode?: string): Promise<BiomarkerTrendsResponse> {
    const url = biomarkerCode
      ? `/lab-results/biomarker-trends?biomarker_code=${biomarkerCode}`
      : '/lab-results/biomarker-trends';

    const response = await api.get<BiomarkerTrendsResponse>(url);
    return response.data;
  },

  // Get lab insights
  async getLabInsights(priority?: 'high' | 'medium' | 'low'): Promise<LabInsightsResponse> {
    const url = priority
      ? `/lab-results/lab-insights?priority=${priority}`
      : '/lab-results/lab-insights';

    const response = await api.get<LabInsightsResponse>(url);
    return response.data;
  },

  // Acknowledge insight
  async acknowledgeInsight(insightId: string): Promise<void> {
    await api.post(`/lab-results/lab-insights/${insightId}/acknowledge`);
  },

  // Get lab test categories
  async getLabTestCategories(): Promise<LabTestCategory[]> {
    const response = await api.get<LabTestCategory[]>('/lab-results/test-categories');
    return response.data;
  },

  // Upload lab result PDF
  async uploadLabResultPdf(file: File, labResultId: string): Promise<{ pdf_url: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<{ pdf_url: string }>(
      `/lab-results/${labResultId}/upload-pdf`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },
};
