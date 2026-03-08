'use client';

import { api } from './api';

export interface CheckinStatus {
  last_checkin_at: string | null;
  days_since_last: number | null;
  should_prompt: boolean;
}

export interface CheckinResponse {
  id: string;
  energy: number;
  mood: number;
  pain: number;
  notes?: string | null;
  checked_in_at: string;
}

export interface CreateCheckinRequest {
  energy: number;
  mood: number;
  pain: number;
  notes?: string;
}

export const checkinsService = {
  getStatus: async (): Promise<CheckinStatus> => {
    const res = await api.get('/api/v1/checkins/status');
    return res.data;
  },

  createCheckin: async (payload: CreateCheckinRequest): Promise<CheckinResponse> => {
    const res = await api.post('/api/v1/checkins', payload);
    return res.data;
  },

  getHistory: async (limit = 12): Promise<CheckinResponse[]> => {
    const res = await api.get('/api/v1/checkins/history', { params: { limit } });
    return res.data;
  },
};
