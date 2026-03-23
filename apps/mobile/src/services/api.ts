/**
 * Mobile API client — adapted from frontend/src/services/api.ts.
 *
 * Key differences from the web version:
 * 1. Base URL uses EXPO_PUBLIC_API_URL (not NEXT_PUBLIC_API_URL)
 * 2. Session expiry redirect uses expo-router instead of window.location.href
 * 3. Token refresh calls supabase.auth.refreshSession() directly (more efficient on mobile)
 * 4. Proactive token refresh when access_token is near expiry
 */

import axios from 'axios';
import { Alert, Platform } from 'react-native';
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

// ── Token cache with proactive refresh ───────────────────────────────────────

let _cachedToken: string | null = null;
let _cacheTs = 0;
let _tokenExpiresAt = 0; // epoch ms
let _inflight: Promise<string | null> | null = null;

/** Margin before expiry to trigger proactive refresh (5 minutes) */
const REFRESH_MARGIN_MS = 5 * 60 * 1000;
/** Cache TTL for token reuse (30 seconds) */
const CACHE_TTL_MS = 30_000;

function _getTokenOnce(): Promise<string | null> {
  const now = Date.now();

  // If token is near expiry, force a refresh
  if (_cachedToken && _tokenExpiresAt > 0 && now > _tokenExpiresAt - REFRESH_MARGIN_MS) {
    _cachedToken = null;
    _cacheTs = 0;
  }

  // Reuse cached token within TTL
  if (_cachedToken && now - _cacheTs < CACHE_TTL_MS) {
    return Promise.resolve(_cachedToken);
  }

  // Share one in-flight getSession() call across concurrent requests
  if (!_inflight) {
    _inflight = supabase.auth
      .getSession()
      .then(({ data }) => {
        _cachedToken = data.session?.access_token ?? null;
        _cacheTs = Date.now();
        // Track expiry time from JWT
        if (data.session?.expires_at) {
          _tokenExpiresAt = data.session.expires_at * 1000; // seconds → ms
        }
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
  if (session?.expires_at) {
    _tokenExpiresAt = session.expires_at * 1000;
  } else {
    _tokenExpiresAt = 0;
  }
});

/**
 * Force-refresh the token cache. Returns true if session is valid.
 * Exported so AppStateListener can call this on foreground resume.
 */
export async function refreshTokenCache(): Promise<boolean> {
  _cachedToken = null;
  _cacheTs = 0;
  _tokenExpiresAt = 0;

  // Try refreshing the session first (handles expired access tokens)
  const { data: refreshed, error: refreshErr } = await supabase.auth.refreshSession();
  if (refreshErr || !refreshed.session) {
    // Refresh failed — check if we still have a valid session
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      return false; // Truly expired
    }
    _cachedToken = session.access_token;
    _cacheTs = Date.now();
    _tokenExpiresAt = (session.expires_at ?? 0) * 1000;
    return true;
  }

  _cachedToken = refreshed.session.access_token;
  _cacheTs = Date.now();
  _tokenExpiresAt = (refreshed.session.expires_at ?? 0) * 1000;
  return true;
}

/** Force logout — clear everything and redirect to login */
export function forceLogout() {
  _cachedToken = null;
  _cacheTs = 0;
  _tokenExpiresAt = 0;
  router.replace('/(auth)/login');
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
let _refreshRejectQueue: Array<(err: unknown) => void> = [];

function _drainQueue(token: string) {
  _refreshQueue.forEach((resolve) => resolve(token));
  _refreshQueue = [];
  _refreshRejectQueue = [];
}

function _rejectQueue(err: unknown) {
  _refreshRejectQueue.forEach((reject) => reject(err));
  _refreshQueue = [];
  _refreshRejectQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as typeof error.config & { _retry?: boolean };

    // ── 401: Token expired — refresh and replay ─────────────────────────────
    if (error.response?.status === 401 && !original._retry) {
      if (_isRefreshing) {
        // Queue this request until the in-flight refresh completes
        return new Promise((resolve, reject) => {
          _refreshQueue.push((newToken: string) => {
            original.headers.Authorization = `Bearer ${newToken}`;
            resolve(api(original));
          });
          _refreshRejectQueue.push(reject);
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
        _tokenExpiresAt = (data.session.expires_at ?? 0) * 1000;
        _drainQueue(newToken);
        _isRefreshing = false;
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      } catch (refreshErr) {
        _isRefreshing = false;
        _rejectQueue(refreshErr);
        // Invalidate cache
        _cachedToken = null;
        _cacheTs = 0;
        _tokenExpiresAt = 0;
        // Show clear message and redirect to login
        Alert.alert(
          'Session Expired',
          'Your session has expired. Please log in again.',
          [{ text: 'OK', onPress: () => forceLogout() }]
        );
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
