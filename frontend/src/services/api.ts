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

// Add auth token to every outgoing request
api.interceptors.request.use(async (config) => {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// --- Refresh-token machinery ---
// Prevents concurrent refreshes: if one is already in flight, queue all
// subsequent 401 requests and replay them once the new token arrives.
let _isRefreshing = false;
let _refreshQueue: Array<(token: string) => void> = [];

function _drainQueue(token: string) {
  _refreshQueue.forEach((resolve) => resolve(token));
  _refreshQueue = [];
}

// Handle auth errors and automatic token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as typeof error.config & { _retry?: boolean };

    // --- 401: attempt token refresh, then replay ---
    if (error.response?.status === 401 && !original._retry) {
      if (_isRefreshing) {
        // Another request is already refreshing — queue this one
        return new Promise((resolve) => {
          _refreshQueue.push((newToken: string) => {
            original.headers.Authorization = `Bearer ${newToken}`;
            resolve(api(original));
          });
        });
      }

      original._retry = true;
      _isRefreshing = true;

      try {
        const { data, error: refreshError } = await supabase.auth.refreshSession();

        if (refreshError || !data.session) {
          throw refreshError ?? new Error('Session refresh returned no session');
        }

        const newToken = data.session.access_token;
        _drainQueue(newToken);
        _isRefreshing = false;

        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      } catch (refreshErr) {
        _isRefreshing = false;
        _refreshQueue = [];

        // Refresh failed — only bounce to login if there truly is no session
        const {
          data: { session },
        } = await supabase.auth.getSession();
        if (!session) {
          window.location.href = '/login';
        }

        return Promise.reject(refreshErr);
      }
    }

    // --- 403: usage limit reached — show upgrade modal ---
    if (
      error.response?.status === 403 &&
      error.response?.data?.error === 'usage_limit_reached'
    ) {
      useSubscriptionStore.getState().setShowUpgradeModal(true);
    }

    return Promise.reject(error);
  }
);
