/**
 * Mobile API client — adapted from frontend/src/services/api.ts.
 *
 * Key differences from the web version:
 * 1. Base URL uses EXPO_PUBLIC_API_URL (not NEXT_PUBLIC_API_URL)
 * 2. Session expiry redirect uses expo-router instead of window.location.href
 * 3. Token refresh calls supabase.auth.refreshSession() directly (more efficient on mobile)
 */

import axios from 'axios';
import { Platform } from 'react-native';
import { router } from 'expo-router';
import { supabase } from '../lib/supabase';
import { useSubscriptionStore } from '../stores/subscriptionStore';

// On Android emulator, localhost refers to the emulator itself; 10.0.2.2 reaches the host Mac.
const _rawUrl = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8100';
const API_BASE_URL =
  Platform.OS === 'android'
    ? _rawUrl.replace('localhost', '10.0.2.2')
    : _rawUrl;

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
});

// ── Token cache (matches frontend/src/services/api.ts pattern) ───────────────

let _cachedToken: string | null = null;
let _cacheTs = 0;
let _inflight: Promise<string | null> | null = null;

function _getTokenOnce(): Promise<string | null> {
  const now = Date.now();
  // Reuse cached token for 30 seconds
  if (_cachedToken && now - _cacheTs < 30_000) {
    return Promise.resolve(_cachedToken);
  }
  // Share one in-flight getSession() call across concurrent requests
  if (!_inflight) {
    _inflight = supabase.auth
      .getSession()
      .then(({ data }) => {
        _cachedToken = data.session?.access_token ?? null;
        _cacheTs = Date.now();
        _inflight = null;
        return _cachedToken;
      })
      .catch(() => {
        _inflight = null;
        return null;
      });
  }
  return _inflight;
}

// Keep cache fresh on auth state changes (login, token refresh, logout)
supabase.auth.onAuthStateChange((_event, session) => {
  _cachedToken = session?.access_token ?? null;
  _cacheTs = Date.now();
});

/** Exported so AppStateListener can force a refresh */
export async function refreshTokenCache(): Promise<void> {
  _cachedToken = null;
  _cacheTs = 0;
  const { data } = await supabase.auth.getSession();
  _cachedToken = data.session?.access_token ?? null;
  _cacheTs = Date.now();
}

// ── Request interceptor: inject Supabase JWT ──────────────────────────────────

api.interceptors.request.use(async (config) => {
  const token = await _getTokenOnce();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
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
        // Update cache with fresh token
        _cachedToken = newToken;
        _cacheTs = Date.now();
        _drainQueue(newToken);
        _isRefreshing = false;
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      } catch {
        _isRefreshing = false;
        _refreshQueue = [];
        // Invalidate cache
        _cachedToken = null;
        _cacheTs = 0;
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
