/**
 * Mobile API client — adapted from frontend/src/services/api.ts.
 *
 * Key differences from the web version:
 * 1. Base URL uses EXPO_PUBLIC_API_URL (not NEXT_PUBLIC_API_URL)
 * 2. Session expiry redirect uses expo-router instead of window.location.href
 * 3. Token refresh calls supabase.auth.refreshSession() directly (more efficient on mobile)
 */

import axios from 'axios';
import { router } from 'expo-router';
import { supabase } from '../lib/supabase';
import { useSubscriptionStore } from '../stores/subscriptionStore';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8100';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
});

// ── Request interceptor: inject Supabase JWT ──────────────────────────────────

api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// ── Response interceptor: handle 401 with queue, 403 upgrade modal ───────────

let _isRefreshing = false;
let _refreshQueue: Array<(token: string) => void> = [];

function _drainQueue(token: string) {
  _refreshQueue.forEach((resolve) => resolve(token));
  _refreshQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Attach _retry flag to config so we don't loop
    const original = error.config as typeof error.config & { _retry?: boolean };

    // ── 401: Token expired — refresh and replay ─────────────────────────────
    if (error.response?.status === 401 && !original._retry) {
      if (_isRefreshing) {
        // Queue this request until the in-flight refresh completes
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
          throw refreshError ?? new Error('Session expired');
        }
        const newToken = data.session.access_token;
        _drainQueue(newToken);
        _isRefreshing = false;
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      } catch {
        _isRefreshing = false;
        _refreshQueue = [];
        // No valid session — redirect to login
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
          router.replace('/(auth)/login');
        }
        return Promise.reject(error);
      }
    }

    // ── 403 usage_limit_reached: show upgrade modal ─────────────────────────
    if (
      error.response?.status === 403 &&
      error.response?.data?.error === 'usage_limit_reached'
    ) {
      useSubscriptionStore.getState().setShowUpgradeModal(true);
    }

    return Promise.reject(error);
  }
);
