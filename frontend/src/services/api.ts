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

// Add auth token to every outgoing request.
// Cache the getSession() promise so concurrent requests share one call
// instead of each awaiting separately (causes Supabase client serialization delays).
let _sessionPromise: Promise<string | null> | null = null;
let _cachedToken: string | null = null;
let _cacheTs = 0;

function _getTokenOnce(): Promise<string | null> {
  const now = Date.now();
  // Use cached token for 30 seconds
  if (_cachedToken && now - _cacheTs < 30_000) {
    return Promise.resolve(_cachedToken);
  }
  // Share one inflight getSession() call across all concurrent requests
  if (!_sessionPromise) {
    _sessionPromise = supabase.auth.getSession()
      .then(({ data: { session } }) => {
        _cachedToken = session?.access_token ?? null;
        _cacheTs = Date.now();
        return _cachedToken;
      })
      .catch(() => null)
      .finally(() => { _sessionPromise = null; });
  }
  return _sessionPromise;
}

// Keep token updated when auth state changes (login, logout, refresh)
supabase.auth.onAuthStateChange((_event, session) => {
  _cachedToken = session?.access_token ?? null;
  _cacheTs = Date.now();
});

api.interceptors.request.use(async (config) => {
  const token = await _getTokenOnce();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
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
