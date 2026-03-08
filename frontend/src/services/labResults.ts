import { api } from './api';
import type {
  LabResult,
  LabResultsResponse,
  BiomarkerTrendsResponse,
  LabInsightsResponse,
  CreateLabResultRequest,
  LabTestCategory,
  LabResultScanResult,
  LabProvider,
} from '@/types';

// Base paths (router mounted at /api/v1/lab-results, CRUD at /lab-results sub-path)
const BASE = '/api/v1/lab-results';
const CRUD = `${BASE}/lab-results`;

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
    const response = await api.get<any>(`${CRUD}${query ? `?${query}` : ''}`);
    const data = response.data;
    // Normalise backend shape {results, total_count} → frontend shape {lab_results, total}
    return {
      lab_results: data.lab_results ?? data.results ?? [],
      total: data.total ?? data.total_count ?? 0,
    };
  },

  // Get single lab result by ID
  async getLabResult(id: string): Promise<LabResult> {
    const response = await api.get<LabResult>(`${CRUD}/${id}`);
    return response.data;
  },

  // Create new lab result
  async createLabResult(data: CreateLabResultRequest): Promise<LabResult> {
    // Transform frontend biomarker shape → backend shape
    // Frontend: { biomarker_code, biomarker_name, value, unit, reference_range? }
    // Backend:  { name, value, unit, reference_range?, status }
    const payload = {
      test_date: data.test_date,
      test_type: data.test_type,
      lab_name: data.lab_name || null,
      ordering_provider: data.ordering_provider || null,
      notes: data.notes || null,
      tags: (data as any).tags || [],
      biomarkers: (data.biomarkers || []).map((b: any) => ({
        name: b.biomarker_name || b.name || b.biomarker_code || 'Unknown',
        value: Number(b.value) || 0,
        unit: b.unit || '',
        reference_range: b.reference_range || null,
        status: b.status || 'normal',
      })),
    };
    const response = await api.post<LabResult>(CRUD, payload);
    return response.data;
  },

  // Delete lab result
  async deleteLabResult(id: string): Promise<void> {
    await api.delete(`${CRUD}/${id}`);
  },

  // Get biomarker trends
  async getBiomarkerTrends(biomarkerCode?: string): Promise<BiomarkerTrendsResponse> {
    const url = biomarkerCode
      ? `${BASE}/biomarker-trends?biomarker_code=${biomarkerCode}`
      : `${BASE}/biomarker-trends`;
    const response = await api.get<BiomarkerTrendsResponse>(url);
    return response.data;
  },

  // Get lab insights
  async getLabInsights(priority?: 'high' | 'medium' | 'low'): Promise<LabInsightsResponse> {
    const url = priority
      ? `${BASE}/lab-insights?priority=${priority}`
      : `${BASE}/lab-insights`;
    const response = await api.get<LabInsightsResponse>(url);
    return response.data;
  },

  // Acknowledge insight
  async acknowledgeInsight(insightId: string): Promise<void> {
    await api.patch(`${BASE}/lab-insights/${insightId}/acknowledge`);
  },

  // Get lab test categories
  async getLabTestCategories(): Promise<LabTestCategory[]> {
    const response = await api.get<LabTestCategory[]>(`${BASE}/test-categories`);
    return response.data;
  },

  // Upload lab result PDF
  async uploadLabResultPdf(file: File, labResultId: string): Promise<{ pdf_url: string }> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<{ pdf_url: string }>(
      `${CRUD}/${labResultId}/upload-pdf`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  // Scan a lab report file (image, PDF, or DOCX) using Claude AI
  async scanLabResultImage(file: File): Promise<LabResultScanResult> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<LabResultScanResult>(
      `${BASE}/scan-image`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  // Get available lab providers
  async getLabProviders(): Promise<LabProvider[]> {
    const response = await api.get<LabProvider[]>(`${BASE}/providers`);
    return response.data;
  },

  // Connect to a lab provider (stub)
  async connectLabProvider(providerId: string): Promise<{ success: boolean; coming_soon: boolean; message: string }> {
    const response = await api.post(`${BASE}/connect-provider`, null, {
      params: { provider_id: providerId },
    });
    return response.data;
  },
};
