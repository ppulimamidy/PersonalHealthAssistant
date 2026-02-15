import axios from 'axios';
import { supabase } from '@/lib/supabase';
import { useSubscriptionStore } from '@/stores/subscriptionStore';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Only redirect to login if the user has no active session.
      // If we *do* have a session, let the UI show the error instead of bouncing.
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        window.location.href = '/login';
      }
    }

    // Usage limit reached — show upgrade modal
    if (
      error.response?.status === 403 &&
      error.response?.data?.error === 'usage_limit_reached'
    ) {
      useSubscriptionStore.getState().setShowUpgradeModal(true);
    }

    return Promise.reject(error);
  }
);
