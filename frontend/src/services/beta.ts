import axios from 'axios';
import type { BetaSignupResponse } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const betaService = {
  signup: async (email: string): Promise<BetaSignupResponse> => {
    const response = await axios.post(`${API_BASE_URL}/api/v1/beta/signup`, { email });
    return response.data;
  },

  getCount: async (): Promise<number> => {
    const response = await axios.get(`${API_BASE_URL}/api/v1/beta/count`);
    return response.data.count;
  },
};
