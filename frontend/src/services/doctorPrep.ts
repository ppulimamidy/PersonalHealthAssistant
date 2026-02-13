import { api } from './api';
import type { DoctorPrepReport } from '@/types';

export const doctorPrepService = {
  // Generate a new doctor visit prep report
  generateReport: async (days: 7 | 30 | 90 = 30): Promise<DoctorPrepReport> => {
    const response = await api.post('/api/v1/doctor-prep/generate', {
      days,
    });
    return response.data;
  },

  // Get existing reports
  getReports: async (): Promise<DoctorPrepReport[]> => {
    const response = await api.get('/api/v1/doctor-prep/reports');
    return response.data;
  },

  // Get specific report
  getReport: async (reportId: string): Promise<DoctorPrepReport> => {
    const response = await api.get(`/api/v1/doctor-prep/reports/${reportId}`);
    return response.data;
  },

  // Export report as PDF
  exportPDF: async (reportId: string): Promise<Blob> => {
    const response = await api.get(`/api/v1/doctor-prep/reports/${reportId}/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },
};
