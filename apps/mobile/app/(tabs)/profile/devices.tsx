/**
 * Phase 2: Devices & Health Sync screen.
 * iOS  → Apple HealthKit via react-native-health (bridge-based, stable)
 * Android → Health Connect via react-native-health-connect
 *
 * HealthKit entitlement must be enabled in Apple Developer Portal before
 * actual data reads work on physical devices. Simulator works for testing.
 * See docs/MOBILE_ARCHITECTURE.md Section 3.10.
 */

import { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity,
  Platform, ActivityIndicator, Alert,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format, subDays } from 'date-fns';
import Constants from 'expo-constants';
import * as Device from 'expo-device';
import { api } from '@/services/api';
import { getSyncTimestamp, setSyncTimestamp } from '@/utils/syncTimestamp';

// ─── Simulator mock data ───────────────────────────────────────────────────────
// iOS Simulator requires a paid dev-team certificate for HealthKit entitlements.
// On simulator we return realistic sample data so the full pipeline can be tested.

function buildMockHealthPoints() {
  const points: Array<{ metric_type: string; date: string; value_json: object }> = [];
  for (let i = 6; i >= 0; i--) {
    const date = format(subDays(new Date(), i), 'yyyy-MM-dd');
    points.push({ metric_type: 'steps',              date, value_json: { steps: 6000 + Math.floor(Math.random() * 6000) } });
    points.push({ metric_type: 'resting_heart_rate', date, value_json: { bpm: 58 + Math.floor(Math.random() * 18) } });
    points.push({ metric_type: 'hrv_sdnn',           date, value_json: { ms: 38 + Math.round(Math.random() * 24 * 10) / 10 } });
    points.push({ metric_type: 'spo2',               date, value_json: { pct: 96 + Math.round(Math.random() * 3 * 10) / 10 } });
    points.push({ metric_type: 'sleep',              date, value_json: { hours: 5.5 + Math.round(Math.random() * 3 * 10) / 10 } });
  }
  return points;
}

// ─── Types ────────────────────────────────────────────────────────────────────

interface SyncMetric {
  label: string;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  unit: string;
  color: string;
  metricType: string;
  valueKey: string;
  format: (v: number) => string;
}

const METRICS: SyncMetric[] = [
  { label: 'Steps',      icon: 'footsteps-outline', unit: 'steps/day', color: '#6EE7B7', metricType: 'steps',              valueKey: 'steps',  format: (v) => v.toLocaleString() },
  { label: 'Sleep',      icon: 'moon-outline',      unit: 'hours',     color: '#818CF8', metricType: 'sleep',              valueKey: 'hours',  format: (v) => v.toFixed(1) },
  { label: 'Heart Rate', icon: 'heart-outline',     unit: 'bpm',       color: '#F87171', metricType: 'resting_heart_rate', valueKey: 'bpm',    format: (v) => String(Math.round(v)) },
  { label: 'HRV',        icon: 'pulse-outline',     unit: 'ms',        color: '#00D4AA', metricType: 'hrv_sdnn',           valueKey: 'ms',     format: (v) => v.toFixed(1) },
  { label: 'SpO₂',       icon: 'water-outline',     unit: '%',         color: '#60A5FA', metricType: 'spo2',               valueKey: 'pct',    format: (v) => v.toFixed(1) },
  { label: 'Workouts',   icon: 'barbell-outline',   unit: 'sessions',  color: '#F5A623', metricType: 'workout',            valueKey: 'count',  format: (v) => String(Math.round(v)) },
];

// ─── iOS HealthKit ─────────────────────────────────────────────────────────────

async function syncHealthKit(onProgress: (msg: string) => void) {
  if (Constants.executionEnvironment === 'storeClient') {
    throw new Error(
      'Apple Health requires a development build.\n\nRun: npm run ios\n\nThen reopen the app.'
    );
  }

  onProgress('Requesting permissions…');

  // Simulator: HealthKit entitlement requires a paid dev-team cert which ad-hoc
  // signing can't provide. Use mock data so the full pipeline is testable.
  if (!Device.isDevice) {
    onProgress('Simulator detected — using sample data…');
    const dataPoints = buildMockHealthPoints();
    const now = new Date();
    onProgress(`Uploading ${dataPoints.length} data points…`);
    const { data: result } = await api.post('/api/v1/health-data/ingest', {
      source: 'healthkit',
      data_points: dataPoints,
      sync_timestamp: now.toISOString(),
    });
    await setSyncTimestamp('healthkit', now.toISOString());
    // Extract most recent value per metric from the points we just synced
    const latest: Record<string, number> = {};
    for (const dp of dataPoints) {
      const val = Object.values(dp.value_json as Record<string, number>)[0];
      if (val != null) latest[dp.metric_type] = val;
    }
    return { ...result, latestValues: latest };
  }

  // VitalixHealthKit is a custom Expo Module (ios/Vitalix/VitalixHealthKitModule.swift)
  // It uses EXUtilities.catchException to convert HealthKit NSExceptions → NSError,
  // avoiding the EXC_BREAKPOINT crash in Nitro Modules' withCheckedThrowingContinuation.
  const { requireNativeModule } = await import('expo-modules-core');
  const HK = requireNativeModule('VitalixHealthKit');

  await HK.requestAuthorization();

  onProgress('Permissions granted, reading data…');
  const lastSync = await getSyncTimestamp('healthkit');
  const since = lastSync ? new Date(lastSync) : subDays(new Date(), 7);
  const now = new Date();
  const fromMs = since.getTime();
  const toMs   = now.getTime();

  const dataPoints: Array<{ metric_type: string; date: string; value_json: object }> = [];

  // Steps — sum per day
  onProgress('Querying steps…');
  try {
    const steps: Array<{ startDate: number; quantity: number }> =
      await HK.queryQuantitySamples('HKQuantityTypeIdentifierStepCount', fromMs, toMs);
    const byDay: Record<string, number> = {};
    for (const s of steps) {
      const day = format(new Date(s.startDate), 'yyyy-MM-dd');
      byDay[day] = (byDay[day] ?? 0) + s.quantity;
    }
    for (const [date, count] of Object.entries(byDay)) {
      dataPoints.push({ metric_type: 'steps', date, value_json: { steps: Math.round(count) } });
    }
  } catch { /* no data */ }

  // Heart Rate — daily average
  try {
    const hr: Array<{ startDate: number; quantity: number }> =
      await HK.queryQuantitySamples('HKQuantityTypeIdentifierHeartRate', fromMs, toMs);
    const byDay: Record<string, number[]> = {};
    for (const s of hr) {
      const day = format(new Date(s.startDate), 'yyyy-MM-dd');
      (byDay[day] ??= []).push(s.quantity);
    }
    for (const [date, vals] of Object.entries(byDay)) {
      const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
      dataPoints.push({ metric_type: 'resting_heart_rate', date, value_json: { bpm: Math.round(avg) } });
    }
  } catch { /* no data */ }

  // HRV — daily average
  try {
    const hrv: Array<{ startDate: number; quantity: number }> =
      await HK.queryQuantitySamples('HKQuantityTypeIdentifierHeartRateVariabilitySDNN', fromMs, toMs);
    const byDay: Record<string, number[]> = {};
    for (const s of hrv) {
      const day = format(new Date(s.startDate), 'yyyy-MM-dd');
      (byDay[day] ??= []).push(s.quantity);
    }
    for (const [date, vals] of Object.entries(byDay)) {
      const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
      dataPoints.push({ metric_type: 'hrv_sdnn', date, value_json: { ms: Math.round(avg * 10) / 10 } });
    }
  } catch { /* no data */ }

  // SpO2 — daily average (HealthKit stores as 0–1 fraction → multiply × 100)
  try {
    const spo2: Array<{ startDate: number; quantity: number }> =
      await HK.queryQuantitySamples('HKQuantityTypeIdentifierOxygenSaturation', fromMs, toMs);
    const byDay: Record<string, number[]> = {};
    for (const s of spo2) {
      const day = format(new Date(s.startDate), 'yyyy-MM-dd');
      (byDay[day] ??= []).push(s.quantity * 100);
    }
    for (const [date, vals] of Object.entries(byDay)) {
      const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
      dataPoints.push({ metric_type: 'spo2', date, value_json: { pct: Math.round(avg * 10) / 10 } });
    }
  } catch { /* no data */ }

  // Sleep — total hours per night (skip InBed=0, Awake=2; count sleep stages only)
  try {
    const sleep: Array<{ startDate: number; endDate: number; value: number }> =
      await HK.queryCategorySamples('HKCategoryTypeIdentifierSleepAnalysis', fromMs, toMs);
    const byDay: Record<string, number> = {};
    for (const s of sleep) {
      if (s.value === 0 || s.value === 2) continue;
      const day = format(new Date(s.startDate), 'yyyy-MM-dd');
      const hrs = (s.endDate - s.startDate) / 3_600_000;
      byDay[day] = (byDay[day] ?? 0) + hrs;
    }
    for (const [date, hrs] of Object.entries(byDay)) {
      dataPoints.push({ metric_type: 'sleep', date, value_json: { hours: Math.round(hrs * 10) / 10 } });
    }
  } catch { /* no data */ }

  if (dataPoints.length === 0) {
    return { accepted: 0, skipped: 0, message: 'No new data since last sync.' };
  }

  onProgress(`Uploading ${dataPoints.length} data points…`);

  const { data: result } = await api.post('/api/v1/health-data/ingest', {
    source: 'healthkit',
    data_points: dataPoints,
    sync_timestamp: now.toISOString(),
  });

  await setSyncTimestamp('healthkit', now.toISOString());
  return result;
}

// ─── Android Health Connect ────────────────────────────────────────────────────

async function syncHealthConnect(onProgress: (msg: string) => void) {
  const { initialize, requestPermission, readRecords } =
    await import('react-native-health-connect');

  onProgress('Initializing Health Connect…');
  const available = await initialize();
  if (!available) {
    throw new Error('Health Connect is not installed. Install it from the Google Play Store.');
  }

  onProgress('Requesting permissions…');
  await requestPermission([
    { accessType: 'read', recordType: 'Steps' },
    { accessType: 'read', recordType: 'SleepSession' },
    { accessType: 'read', recordType: 'HeartRate' },
    { accessType: 'read', recordType: 'HeartRateVariabilityRmssd' },
    { accessType: 'read', recordType: 'OxygenSaturation' },
    { accessType: 'read', recordType: 'ExerciseSession' },
  ]);

  const lastSync = await getSyncTimestamp('health_connect');
  const since = lastSync ? new Date(lastSync) : subDays(new Date(), 7);
  const now = new Date();
  const timeRangeFilter = {
    operator: 'between' as const,
    startTime: since.toISOString(),
    endTime: now.toISOString(),
  };

  onProgress('Reading health data…');

  const dataPoints: Array<{ metric_type: string; date: string; value_json: object }> = [];

  try {
    const { records: steps } = await readRecords('Steps', { timeRangeFilter });
    const byDay: Record<string, number> = {};
    for (const r of steps) {
      const day = format(new Date(r.startTime), 'yyyy-MM-dd');
      byDay[day] = (byDay[day] ?? 0) + r.count;
    }
    for (const [date, count] of Object.entries(byDay)) {
      dataPoints.push({ metric_type: 'steps', date, value_json: { steps: count } });
    }
  } catch { /* no data */ }

  try {
    const { records: hr } = await readRecords('HeartRate', { timeRangeFilter });
    const byDay: Record<string, number[]> = {};
    for (const r of hr) {
      const day = format(new Date(r.startTime), 'yyyy-MM-dd');
      if (!byDay[day]) byDay[day] = [];
      for (const sample of r.samples) byDay[day].push(sample.beatsPerMinute);
    }
    for (const [date, vals] of Object.entries(byDay)) {
      const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
      dataPoints.push({ metric_type: 'resting_heart_rate', date, value_json: { bpm: Math.round(avg) } });
    }
  } catch { /* no data */ }

  if (dataPoints.length === 0) {
    return { accepted: 0, skipped: 0, message: 'No new data since last sync.' };
  }

  onProgress(`Uploading ${dataPoints.length} data points…`);

  const { data: result } = await api.post('/api/v1/health-data/ingest', {
    source: 'health_connect',
    data_points: dataPoints,
    sync_timestamp: now.toISOString(),
  });

  await setSyncTimestamp('health_connect', now.toISOString());
  return result;
}

// ─── Screen ────────────────────────────────────────────────────────────────────

export default function DevicesScreen() {
  const queryClient = useQueryClient();
  const [syncing, setSyncing] = useState(false);
  const [progress, setProgress] = useState('');
  const [lastResult, setLastResult] = useState<{ accepted: number; skipped: number; message?: string } | null>(null);
  const [latestValues, setLatestValues] = useState<Record<string, number>>({});

  const syncKey = Platform.OS === 'ios' ? 'healthkit' : 'health_connect';

  const { data: lastSyncTs } = useQuery({
    queryKey: ['sync-timestamp', syncKey],
    queryFn: () => getSyncTimestamp(syncKey),
  });

  const handleSync = useCallback(async () => {
    setSyncing(true);
    setProgress('Starting…');
    setLastResult(null);
    try {
      const result = Platform.OS === 'ios'
        ? await syncHealthKit(setProgress)
        : await syncHealthConnect(setProgress);
      if (result?.latestValues) setLatestValues(result.latestValues);
      setLastResult(result);
      queryClient.invalidateQueries({ queryKey: ['sync-timestamp'] });
      queryClient.invalidateQueries({ queryKey: ['batch'] });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Sync failed';
      Alert.alert('Sync failed', msg);
    } finally {
      setSyncing(false);
      setProgress('');
    }
  }, [queryClient]);

  const platformName = Platform.OS === 'ios' ? 'Apple Health' : 'Google Health Connect';
  const platformIcon: React.ComponentProps<typeof Ionicons>['name'] = Platform.OS === 'ios' ? 'heart' : 'fitness';
  const platformColor = Platform.OS === 'ios' ? '#F87171' : '#4CAF50';

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <Text className="text-xl font-display text-[#E8EDF5]">Health Sync</Text>
      </View>

      <View className="px-6 pt-6">
        {/* Connection card */}
        <View className="bg-surface-raised border border-surface-border rounded-2xl p-5 mb-5">
          <View className="flex-row items-center gap-4 mb-4">
            <View className="w-14 h-14 rounded-2xl items-center justify-center" style={{ backgroundColor: `${platformColor}20` }}>
              <Ionicons name={platformIcon} size={28} color={platformColor} />
            </View>
            <View className="flex-1">
              <Text className="text-[#E8EDF5] font-sansMedium text-base">{platformName}</Text>
              <Text className="text-[#526380] text-xs mt-0.5">
                {lastSyncTs
                  ? `Last synced ${format(new Date(lastSyncTs), 'MMM d, h:mm a')}`
                  : 'Never synced'}
              </Text>
            </View>
            <View className="w-2.5 h-2.5 rounded-full bg-primary-500" />
          </View>

          {lastResult && (
            <View className="bg-primary-500/10 border border-primary-500/30 rounded-xl px-4 py-3 mb-4">
              <Text className="text-primary-500 text-sm font-sansMedium">
                {lastResult.message ?? `Synced ${lastResult.accepted} data points`}
                {lastResult.skipped > 0 ? ` (${lastResult.skipped} already up to date)` : ''}
              </Text>
            </View>
          )}

          <TouchableOpacity
            onPress={handleSync}
            disabled={syncing}
            className="bg-primary-500 rounded-xl py-3.5 items-center"
            activeOpacity={0.8}
          >
            {syncing ? (
              <View className="flex-row items-center gap-2">
                <ActivityIndicator size="small" color="#080B10" />
                <Text className="text-obsidian-900 font-sansMedium text-sm">{progress}</Text>
              </View>
            ) : (
              <Text className="text-obsidian-900 font-sansMedium">Sync Now</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Metrics grid */}
        <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3">Data We Collect</Text>
        <View className="flex-row flex-wrap gap-3 mb-5">
          {METRICS.map((m) => {
            const raw = latestValues[m.metricType];
            const valueStr = raw != null ? m.format(raw) : null;
            return (
              <View
                key={m.label}
                className="bg-surface-raised border border-surface-border rounded-xl p-3 items-center"
                style={{ width: '30%' }}
              >
                <View className="w-9 h-9 rounded-xl items-center justify-center mb-2" style={{ backgroundColor: `${m.color}20` }}>
                  <Ionicons name={m.icon} size={18} color={m.color} />
                </View>
                <Text className="text-[#E8EDF5] text-xs font-sansMedium text-center">{m.label}</Text>
                {valueStr != null ? (
                  <Text className="text-xs font-sansMedium text-center mt-0.5" style={{ color: m.color }}>{valueStr}</Text>
                ) : (
                  <Text className="text-[#526380] text-xs text-center mt-0.5">{m.unit}</Text>
                )}
              </View>
            );
          })}
        </View>

        {/* Privacy note */}
        <View className="bg-surface border border-surface-border rounded-xl px-4 py-3 flex-row gap-3">
          <Ionicons name="lock-closed-outline" size={16} color="#526380" style={{ marginTop: 1 }} />
          <Text className="text-[#526380] text-xs leading-4 flex-1">
            Your health data is encrypted and stored privately. It is never shared with third parties.
            You can delete your data at any time from Settings.
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}
