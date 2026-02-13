import { api } from './api';
import type {
  OuraConnection,
  SleepData,
  ActivityData,
  ReadinessData,
  TimelineEntry
} from '@/types';

// Check if sandbox mode is enabled
const USE_SANDBOX = process.env.NEXT_PUBLIC_USE_SANDBOX === 'true';

interface AuthUrlResponse {
  auth_url: string | null;
  sandbox_mode: boolean;
  message?: string;
}

interface OuraStatus {
  sandbox_mode: boolean;
  oauth_configured: boolean;
  message: string;
}

export const ouraService = {
  // Check if running in sandbox mode
  isSandboxMode: (): boolean => {
    return USE_SANDBOX;
  },

  // Get Oura integration status
  getStatus: async (): Promise<OuraStatus> => {
    const response = await api.get('/api/v1/oura/status');
    return response.data;
  },

  // Get OAuth URL to initiate Oura connection
  // In sandbox mode, returns null (no OAuth needed)
  getAuthUrl: async (): Promise<AuthUrlResponse> => {
    const response = await api.get('/api/v1/oura/auth-url');
    return response.data;
  },

  // Handle OAuth callback
  // In sandbox mode, this auto-connects
  handleCallback: async (code: string): Promise<OuraConnection> => {
    const response = await api.post('/api/v1/oura/callback', { code });
    return response.data;
  },

  // Get connection status
  // In sandbox mode, always returns connected
  getConnectionStatus: async (): Promise<OuraConnection | null> => {
    try {
      const response = await api.get('/api/v1/oura/connection');
      return response.data;
    } catch {
      return null;
    }
  },

  // Disconnect Oura
  disconnect: async (): Promise<void> => {
    await api.delete('/api/v1/oura/connection');
  },

  // Sync latest data from Oura
  // In sandbox mode, generates fresh mock data
  syncData: async (): Promise<{ synced_records: number; is_sandbox: boolean }> => {
    const response = await api.post('/api/v1/oura/sync');
    return response.data;
  },

  // Get sleep data
  getSleepData: async (startDate: string, endDate: string): Promise<SleepData[]> => {
    const response = await api.get('/api/v1/oura/sleep', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  },

  // Get activity data
  getActivityData: async (startDate: string, endDate: string): Promise<ActivityData[]> => {
    const response = await api.get('/api/v1/oura/activity', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  },

  // Get readiness data
  getReadinessData: async (startDate: string, endDate: string): Promise<ReadinessData[]> => {
    const response = await api.get('/api/v1/oura/readiness', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  },

  // Get combined timeline data
  getTimeline: async (days: 7 | 30 = 7): Promise<TimelineEntry[]> => {
    const response = await api.get('/api/v1/health/timeline', {
      params: { days },
    });
    return response.data;
  },
};
