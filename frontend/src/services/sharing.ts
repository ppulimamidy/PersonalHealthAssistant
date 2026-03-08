import { api } from './api';
import type { ShareLink, CreateShareRequest, SharedHealthSummary } from '@/types';

export const sharingService = {
  listShares: async (): Promise<ShareLink[]> => {
    const response = await api.get('/api/v1/share/');
    return response.data;
  },

  createShare: async (payload: CreateShareRequest): Promise<ShareLink> => {
    const response = await api.post('/api/v1/share/', payload);
    return response.data;
  },

  revokeShare: async (linkId: string): Promise<void> => {
    await api.delete(`/api/v1/share/${linkId}`);
  },

  // Public — no auth token needed. Call directly with fetch or unauthenticated axios.
  getPublicSummary: async (token: string): Promise<SharedHealthSummary> => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8100';
    const res = await fetch(`${baseUrl}/api/v1/share/public/${token}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },
};
