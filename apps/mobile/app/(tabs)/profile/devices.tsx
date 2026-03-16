/**
 * Health Devices screen.
 * YOUR DEVICES: Apple Health (live sync) + Oura Ring (coming soon)
 * ADD A WEARABLE: grid of coming-soon devices
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
import { getSyncTimestamp, setSyncTimestamp, clearSyncTimestamp } from '@/utils/syncTimestamp';

// NitroModules-based library — safe to import statically on all platforms.
// isHealthDataAvailable() returns false on Android so iOS-only code is never reached.
// v13: HKQuantityTypeIdentifier / HKCategoryTypeIdentifier are TypeScript types only,
// not runtime objects. Pass the raw string literals directly to the API.
import HealthKit from '@kingstinct/react-native-healthkit';

// ─── Simulator mock data ───────────────────────────────────────────────────────

function buildMockHealthPoints() {
  const points: Array<{ metric_type: string; date: string; value_json: object }> = [];
  const workoutTypes = ['yoga', 'running', 'cycling', 'strength', 'walking'];
  for (let i = 6; i >= 0; i--) {
    const date = format(subDays(new Date(), i), 'yyyy-MM-dd');
    points.push({ metric_type: 'steps',              date, value_json: { steps: 6000 + Math.floor(Math.random() * 6000) } });
    points.push({ metric_type: 'resting_heart_rate', date, value_json: { bpm: 58 + Math.floor(Math.random() * 18) } });
    points.push({ metric_type: 'hrv_sdnn',           date, value_json: { ms: 38 + Math.round(Math.random() * 24 * 10) / 10 } });
    points.push({ metric_type: 'spo2',               date, value_json: { pct: 96 + Math.round(Math.random() * 3 * 10) / 10 } });
    points.push({ metric_type: 'sleep',              date, value_json: { hours: 5.5 + Math.round(Math.random() * 3 * 10) / 10 } });
    points.push({ metric_type: 'respiratory_rate',   date, value_json: { rate: 13 + Math.round(Math.random() * 5 * 10) / 10 } });
    points.push({ metric_type: 'active_calories',    date, value_json: { kcal: 250 + Math.floor(Math.random() * 350) } });
    // Workouts ~5 out of 7 days
    if (i !== 1 && i !== 4) {
      const type = workoutTypes[Math.floor(Math.random() * workoutTypes.length)];
      const mins = 25 + Math.floor(Math.random() * 45);
      points.push({ metric_type: 'workout', date, value_json: { minutes: mins, sessions: 1, active_calories: Math.round(mins * 4.5), types: [type] } });
    }
    // VO2 max only syncs occasionally (latest reading)
    if (i === 0) {
      points.push({ metric_type: 'vo2_max', date, value_json: { ml_kg_min: 36 + Math.round(Math.random() * 14 * 10) / 10 } });
    }
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
  { label: 'Steps',            icon: 'footsteps-outline',   unit: 'steps/day',  color: '#6EE7B7', metricType: 'steps',              valueKey: 'steps',      format: (v) => v.toLocaleString() },
  { label: 'Sleep',            icon: 'moon-outline',        unit: 'hours',      color: '#818CF8', metricType: 'sleep',              valueKey: 'hours',      format: (v) => v.toFixed(1) + 'h' },
  { label: 'Heart Rate',       icon: 'heart-outline',       unit: 'bpm',        color: '#F87171', metricType: 'resting_heart_rate', valueKey: 'bpm',        format: (v) => String(Math.round(v)) + ' bpm' },
  { label: 'HRV',              icon: 'pulse-outline',       unit: 'ms',         color: '#00D4AA', metricType: 'hrv_sdnn',           valueKey: 'ms',         format: (v) => v.toFixed(1) + ' ms' },
  { label: 'SpO₂',             icon: 'water-outline',       unit: '%',          color: '#60A5FA', metricType: 'spo2',               valueKey: 'pct',        format: (v) => v.toFixed(1) + '%' },
  { label: 'Respiratory Rate', icon: 'cellular-outline',    unit: 'breaths/min', color: '#A78BFA', metricType: 'respiratory_rate',  valueKey: 'rate',       format: (v) => v.toFixed(1) + ' /min' },
  { label: 'Active Calories',  icon: 'flame-outline',       unit: 'kcal',       color: '#FB923C', metricType: 'active_calories',    valueKey: 'kcal',       format: (v) => Math.round(v) + ' kcal' },
  { label: 'Workouts',         icon: 'barbell-outline',     unit: 'min',        color: '#F59E0B', metricType: 'workout',            valueKey: 'minutes',    format: (v) => Math.round(v) + ' min' },
  { label: 'VO₂ Max',          icon: 'speedometer-outline', unit: 'mL/kg/min',  color: '#34D399', metricType: 'vo2_max',            valueKey: 'ml_kg_min',  format: (v) => v.toFixed(1) + ' mL/kg/min' },
];

// ─── Batched upload helper ─────────────────────────────────────────────────────

const BATCH_SIZE = 400; // stay well under the 500 API limit

async function uploadInBatches(
  source: 'healthkit' | 'health_connect',
  dataPoints: Array<{ metric_type: string; date: string; value_json: object }>,
  syncTimestamp: string,
  onProgress: (msg: string) => void,
): Promise<{ accepted: number; skipped: number }> {
  let totalAccepted = 0;
  let totalSkipped = 0;
  for (let i = 0; i < dataPoints.length; i += BATCH_SIZE) {
    const batch = dataPoints.slice(i, i + BATCH_SIZE);
    const batchNum = Math.floor(i / BATCH_SIZE) + 1;
    const totalBatches = Math.ceil(dataPoints.length / BATCH_SIZE);
    if (totalBatches > 1) {
      onProgress(`Uploading batch ${batchNum}/${totalBatches} (${batch.length} points)…`);
    } else {
      onProgress(`Uploading ${batch.length} data points…`);
    }
    const { data } = await api.post('/api/v1/health-data/ingest', {
      source,
      data_points: batch,
      sync_timestamp: syncTimestamp,
    });
    totalAccepted += data?.accepted ?? 0;
    totalSkipped += data?.skipped ?? 0;
  }
  return { accepted: totalAccepted, skipped: totalSkipped };
}

// ─── iOS HealthKit ─────────────────────────────────────────────────────────────

async function syncHealthKit(onProgress: (msg: string) => void) {
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
    const latest: Record<string, number> = {};
    for (const dp of dataPoints) {
      const val = Object.values(dp.value_json as Record<string, number>)[0];
      if (val != null) latest[dp.metric_type] = val;
    }
    return { ...result, latestValues: latest };
  }

  const available = await HealthKit.isHealthDataAvailable();
  if (!available) {
    throw new Error('Apple Health is not available on this device. Make sure you have a supported iPhone with iOS 13+.');
  }

  onProgress('Requesting permissions…');

  await HealthKit.requestAuthorization({
    toRead: [
      'HKQuantityTypeIdentifierStepCount',
      'HKQuantityTypeIdentifierHeartRate',
      'HKQuantityTypeIdentifierHeartRateVariabilitySDNN',
      'HKQuantityTypeIdentifierOxygenSaturation',
      'HKQuantityTypeIdentifierRespiratoryRate',
      'HKQuantityTypeIdentifierActiveEnergyBurned',
      'HKQuantityTypeIdentifierVO2Max',
      'HKCategoryTypeIdentifierSleepAnalysis',
      'HKWorkoutTypeIdentifier',
    ],
  } as any);

  const lastSync = await getSyncTimestamp('healthkit');
  const isFirstSync = !lastSync;
  const now = new Date();

  // First connect: pull up to 3 years of historical data for baseline insights
  // Subsequent syncs: pull only since last sync
  const since = lastSync
    ? new Date(lastSync)
    : new Date(now.getFullYear() - 3, now.getMonth(), now.getDate());

  console.log('[HK] lastSync:', lastSync, 'isFirstSync:', isFirstSync, 'since:', since.toISOString());

  onProgress(isFirstSync
    ? 'First sync — loading historical data (this may take a moment)…'
    : 'Reading data…');

  // Anchor at midnight so daily buckets align to calendar days (not arbitrary times)
  const anchor = new Date(since);
  anchor.setHours(0, 0, 0, 0);

  const dateRange = { filter: { date: { startDate: anchor, endDate: now } } };
  const catOpts = { limit: -1, filter: { date: { startDate: anchor, endDate: now } } } as any;

  // Helper: query deduplicated daily statistics (merges iPhone + Apple Watch sources)
  // Uses the same deduplication algorithm as the Apple Health summary screen
  async function dailyStats(
    identifier: string,
    stat: 'cumulativeSum' | 'discreteAverage' | 'discreteMin' | 'discreteMax' | 'mostRecent',
    unit?: string,
  ) {
    const opts = unit ? { ...dateRange, unit } : dateRange;
    const results = await HealthKit.queryStatisticsCollectionForQuantity(
      identifier as any,
      [stat],
      anchor,         // anchorDate: midnight-aligned
      { day: 1 },     // interval: 1 calendar day
      opts as any,
    );
    return results;
  }

  const dataPoints: Array<{ metric_type: string; date: string; value_json: object }> = [];

  onProgress('Querying steps…');
  try {
    const stats = await dailyStats('HKQuantityTypeIdentifierStepCount', 'cumulativeSum', 'count');
    console.log('[HK] steps days:', stats.length, 'first:', stats[stats.length - 1]?.startDate, 'last:', stats[0]?.startDate);
    for (const s of stats) {
      if (s.sumQuantity && s.startDate) {
        const date = format(s.startDate, 'yyyy-MM-dd');
        dataPoints.push({ metric_type: 'steps', date, value_json: { steps: Math.round(s.sumQuantity.quantity) } });
      }
    }
  } catch (e) { console.warn('[HK] steps error:', e); }

  onProgress('Querying heart rate…');
  try {
    const stats = await dailyStats('HKQuantityTypeIdentifierHeartRate', 'discreteAverage', 'count/min');
    for (const s of stats) {
      if (s.averageQuantity && s.startDate) {
        const date = format(s.startDate, 'yyyy-MM-dd');
        dataPoints.push({ metric_type: 'resting_heart_rate', date, value_json: { bpm: Math.round(s.averageQuantity.quantity) } });
      }
    }
  } catch (e) { console.warn('[HK] heartRate error:', e); }

  onProgress('Querying HRV…');
  try {
    const stats = await dailyStats('HKQuantityTypeIdentifierHeartRateVariabilitySDNN', 'discreteAverage', 'ms');
    for (const s of stats) {
      if (s.averageQuantity && s.startDate) {
        const date = format(s.startDate, 'yyyy-MM-dd');
        // Requested in 'ms' unit — no conversion needed
        dataPoints.push({ metric_type: 'hrv_sdnn', date, value_json: { ms: Math.round(s.averageQuantity.quantity * 10) / 10 } });
      }
    }
  } catch (e) { console.warn('[HK] HRV error:', e); }

  onProgress('Querying SpO₂…');
  try {
    const stats = await dailyStats('HKQuantityTypeIdentifierOxygenSaturation', 'discreteAverage', '%');
    for (const s of stats) {
      if (s.averageQuantity && s.startDate) {
        const date = format(s.startDate, 'yyyy-MM-dd');
        // Requested in '%' unit (0-100) — no conversion needed
        dataPoints.push({ metric_type: 'spo2', date, value_json: { pct: Math.round(s.averageQuantity.quantity * 10) / 10 } });
      }
    }
  } catch (e) { console.warn('[HK] SpO2 error:', e); }

  onProgress('Querying sleep…');
  try {
    // Sleep uses category samples — no statistics API available. Filter to avoid double counting.
    const samples = await HealthKit.queryCategorySamples(
      'HKCategoryTypeIdentifierSleepAnalysis', catOpts,
    );
    const byDay: Record<string, number> = {};
    for (const s of samples) {
      if (s.value === 0) continue; // skip InBed (0), count all sleep stages (1–5)
      const day = format(s.startDate, 'yyyy-MM-dd');
      const hrs = (s.endDate.getTime() - s.startDate.getTime()) / 3_600_000;
      byDay[day] = (byDay[day] ?? 0) + hrs;
    }
    for (const [date, hrs] of Object.entries(byDay)) {
      dataPoints.push({ metric_type: 'sleep', date, value_json: { hours: Math.round(hrs * 10) / 10 } });
    }
  } catch (e) { console.warn('[HK] sleep error:', e); }

  onProgress('Querying respiratory rate…');
  try {
    const stats = await dailyStats('HKQuantityTypeIdentifierRespiratoryRate', 'discreteAverage', 'count/min');
    for (const s of stats) {
      if (s.averageQuantity && s.startDate) {
        const date = format(s.startDate, 'yyyy-MM-dd');
        dataPoints.push({ metric_type: 'respiratory_rate', date, value_json: { rate: Math.round(s.averageQuantity.quantity * 10) / 10 } });
      }
    }
  } catch (e) { console.warn('[HK] respiratoryRate error:', e); }

  onProgress('Querying active calories…');
  try {
    const stats = await dailyStats('HKQuantityTypeIdentifierActiveEnergyBurned', 'cumulativeSum', 'kcal');
    for (const s of stats) {
      if (s.sumQuantity && s.startDate) {
        const date = format(s.startDate, 'yyyy-MM-dd');
        dataPoints.push({ metric_type: 'active_calories', date, value_json: { kcal: Math.round(s.sumQuantity.quantity) } });
      }
    }
  } catch (e) { console.warn('[HK] activeCals error:', e); }

  onProgress('Querying VO₂ max…');
  try {
    const stats = await dailyStats('HKQuantityTypeIdentifierVO2Max', 'mostRecent', 'ml/(kg*min)');
    for (const s of stats) {
      if (s.mostRecentQuantity && s.startDate) {
        const date = format(s.startDate, 'yyyy-MM-dd');
        dataPoints.push({ metric_type: 'vo2_max', date, value_json: { ml_kg_min: Math.round(s.mostRecentQuantity.quantity * 10) / 10 } });
      }
    }
  } catch (e) { console.warn('[HK] vo2max error:', e); }

  onProgress('Querying workouts…');
  try {
    const workoutTypeMap: Record<number, string> = {
      13: 'cycling', 37: 'running', 46: 'swimming', 50: 'strength',
      52: 'walking', 57: 'yoga', 64: 'hiit', 72: 'mindfulness', 84: 'pilates',
    };
    const workouts = await HealthKit.queryWorkoutSamples({
      limit: -1, filter: dateRange.filter,
    } as any);
    const byDay: Record<string, { minutes: number; sessions: number; active_calories: number; types: string[] }> = {};
    for (const w of workouts) {
      const day = format(w.startDate, 'yyyy-MM-dd');
      const durationMin = w.duration?.quantity ? w.duration.quantity / 60 : (w.endDate.getTime() - w.startDate.getTime()) / 60_000;
      const typeName = workoutTypeMap[w.workoutActivityType as number] ?? 'other';
      const kcal = w.totalEnergyBurned?.quantity ?? 0;
      if (!byDay[day]) byDay[day] = { minutes: 0, sessions: 0, active_calories: 0, types: [] };
      byDay[day].minutes += durationMin;
      byDay[day].sessions += 1;
      byDay[day].active_calories += kcal;
      if (!byDay[day].types.includes(typeName)) byDay[day].types.push(typeName);
    }
    for (const [date, agg] of Object.entries(byDay)) {
      dataPoints.push({ metric_type: 'workout', date, value_json: { minutes: Math.round(agg.minutes), sessions: agg.sessions, active_calories: Math.round(agg.active_calories), types: agg.types } });
    }
  } catch (e) { console.warn('[HK] workouts error:', e); }

  console.log('[HK] Total data points collected:', dataPoints.length);

  if (dataPoints.length === 0) {
    return { accepted: 0, skipped: 0, message: 'No new data since last sync.' };
  }

  const result = await uploadInBatches('healthkit', dataPoints, now.toISOString(), onProgress);
  await setSyncTimestamp('healthkit', now.toISOString());

  // Build latestValues so metric rows populate in the UI
  const latestValues: Record<string, number> = {};
  for (const dp of dataPoints) {
    const val = Object.values(dp.value_json as Record<string, number>)[0];
    if (val != null) latestValues[dp.metric_type] = val;
  }
  return { ...result, latestValues };
}

// ─── Android Health Connect ────────────────────────────────────────────────────

async function syncHealthConnect(onProgress: (msg: string) => void) {
  if (!Device.isDevice) {
    onProgress('Emulator detected — using sample data…');
    const dataPoints = buildMockHealthPoints();
    const now = new Date();
    onProgress(`Uploading ${dataPoints.length} data points…`);
    const { data: result } = await api.post('/api/v1/health-data/ingest', {
      source: 'health_connect',
      data_points: dataPoints,
      sync_timestamp: now.toISOString(),
    });
    await setSyncTimestamp('health_connect', now.toISOString());
    const latest: Record<string, number> = {};
    for (const dp of dataPoints) {
      const val = Object.values(dp.value_json as Record<string, number>)[0];
      if (val != null) latest[dp.metric_type] = val;
    }
    return { ...result, latestValues: latest };
  }

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
    { accessType: 'read', recordType: 'ActiveCaloriesBurned' },
    { accessType: 'read', recordType: 'RespiratoryRate' },
  ]);

  const lastSync = await getSyncTimestamp('health_connect');
  const isFirstSync = !lastSync;
  const now = new Date();

  // First connect: pull up to 30 days (Health Connect retention limit for third-party apps)
  // Subsequent syncs: pull only since last sync
  const since = lastSync ? new Date(lastSync) : subDays(now, 30);
  const timeRangeFilter = {
    operator: 'between' as const,
    startTime: since.toISOString(),
    endTime: now.toISOString(),
  };

  onProgress(isFirstSync
    ? 'First sync — loading up to 30 days of history…'
    : 'Reading health data…');

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

  try {
    const { records: hrv } = await readRecords('HeartRateVariabilityRmssd', { timeRangeFilter });
    const byDay: Record<string, number[]> = {};
    for (const r of hrv) {
      const day = format(new Date(r.time), 'yyyy-MM-dd');
      (byDay[day] ??= []).push(r.heartRateVariabilityMillis);
    }
    for (const [date, vals] of Object.entries(byDay)) {
      const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
      dataPoints.push({ metric_type: 'hrv_sdnn', date, value_json: { ms: Math.round(avg * 10) / 10 } });
    }
  } catch { /* no data */ }

  try {
    const { records: spo2 } = await readRecords('OxygenSaturation', { timeRangeFilter });
    const byDay: Record<string, number[]> = {};
    for (const r of spo2) {
      const day = format(new Date(r.time), 'yyyy-MM-dd');
      (byDay[day] ??= []).push(r.percentage * 100);
    }
    for (const [date, vals] of Object.entries(byDay)) {
      const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
      dataPoints.push({ metric_type: 'spo2', date, value_json: { pct: Math.round(avg * 10) / 10 } });
    }
  } catch { /* no data */ }

  try {
    const { records: rr } = await readRecords('RespiratoryRate', { timeRangeFilter });
    const byDay: Record<string, number[]> = {};
    for (const r of rr) {
      const day = format(new Date(r.time), 'yyyy-MM-dd');
      (byDay[day] ??= []).push(r.rate);
    }
    for (const [date, vals] of Object.entries(byDay)) {
      const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
      dataPoints.push({ metric_type: 'respiratory_rate', date, value_json: { rate: Math.round(avg * 10) / 10 } });
    }
  } catch { /* no data */ }

  try {
    const { records: cals } = await readRecords('ActiveCaloriesBurned', { timeRangeFilter });
    const byDay: Record<string, number> = {};
    for (const r of cals) {
      const day = format(new Date(r.startTime), 'yyyy-MM-dd');
      byDay[day] = (byDay[day] ?? 0) + r.energy.inKilocalories;
    }
    for (const [date, total] of Object.entries(byDay)) {
      dataPoints.push({ metric_type: 'active_calories', date, value_json: { kcal: Math.round(total) } });
    }
  } catch { /* no data */ }

  try {
    const { records: sessions } = await readRecords('ExerciseSession', { timeRangeFilter });
    const exerciseTypeMap: Record<number, string> = {
      56: 'yoga', 79: 'running', 8: 'cycling', 62: 'pilates',
      70: 'rowing', 97: 'strength', 99: 'swimming', 37: 'walking',
      54: 'hiit', 55: 'interval_training',
    };
    const byDay: Record<string, { minutes: number; sessions: number; types: string[] }> = {};
    for (const s of sessions) {
      const day = format(new Date(s.startTime), 'yyyy-MM-dd');
      const durationMin = (new Date(s.endTime).getTime() - new Date(s.startTime).getTime()) / 60_000;
      const typeName = exerciseTypeMap[s.exerciseType] ?? 'other';
      if (!byDay[day]) byDay[day] = { minutes: 0, sessions: 0, types: [] };
      byDay[day].minutes += durationMin;
      byDay[day].sessions += 1;
      if (!byDay[day].types.includes(typeName)) byDay[day].types.push(typeName);
    }
    for (const [date, agg] of Object.entries(byDay)) {
      dataPoints.push({ metric_type: 'workout', date, value_json: { minutes: Math.round(agg.minutes), sessions: agg.sessions, active_calories: 0, types: agg.types } });
    }
  } catch { /* no data */ }

  if (dataPoints.length === 0) {
    return { accepted: 0, skipped: 0, message: 'No new data since last sync.' };
  }

  const result = await uploadInBatches('health_connect', dataPoints, now.toISOString(), onProgress);
  await setSyncTimestamp('health_connect', now.toISOString());

  // Build latestValues so metric rows populate in the UI
  const latestValues: Record<string, number> = {};
  for (const dp of dataPoints) {
    const val = Object.values(dp.value_json as Record<string, number>)[0];
    if (val != null) latestValues[dp.metric_type] = val;
  }
  return { ...result, latestValues };
}

// ─── Types for summaries ──────────────────────────────────────────────────────

interface MetricSummary {
  latest_value: number | null;
  latest_date: string | null;
  avg_7d: number | null;
  avg_30d: number | null;
  avg_90d: number | null;
  trend_7d: 'up' | 'down' | 'stable' | null;
  trend_30d: 'up' | 'down' | 'stable' | null;
  data_points_total: number;
  is_anomalous: boolean;
  anomaly_severity: 'low' | 'medium' | 'high' | null;
  anomaly_detail: string | null;
}

type Summaries = Record<string, MetricSummary>;

const TREND_ICON: Record<string, { icon: React.ComponentProps<typeof Ionicons>['name']; color: string }> = {
  up:     { icon: 'trending-up',    color: '#6EE7B7' },
  down:   { icon: 'trending-down',  color: '#F87171' },
  stable: { icon: 'remove-outline', color: '#526380' },
};

// ─── Metric Row ───────────────────────────────────────────────────────────────

function MetricRow({
  metric, value, summary,
}: {
  metric: SyncMetric;
  value: number | null;
  summary?: MetricSummary;
}) {
  const displayValue = value ?? summary?.latest_value;
  const trend = summary?.trend_7d;
  const trendInfo = trend ? TREND_ICON[trend] : null;
  const avg7 = summary?.avg_7d;
  const avg30 = summary?.avg_30d;
  const avg90 = summary?.avg_90d;

  return (
    <View className="py-2.5 border-b border-surface-border last:border-0">
      <View className="flex-row items-center">
        <View
          className="w-8 h-8 rounded-lg items-center justify-center mr-3"
          style={{ backgroundColor: `${metric.color}18` }}
        >
          <Ionicons name={metric.icon} size={16} color={metric.color} />
        </View>
        <Text className="text-[#E8EDF5] text-sm flex-1">{metric.label}</Text>
        {trendInfo && (
          <Ionicons name={trendInfo.icon} size={14} color={trendInfo.color} style={{ marginRight: 6 }} />
        )}
        {displayValue != null ? (
          <Text className="text-sm font-sansMedium" style={{ color: metric.color }}>
            {metric.format(displayValue)}
          </Text>
        ) : (
          <Text className="text-[#3A4A5C] text-xs">—</Text>
        )}
      </View>
      {/* Averages row */}
      {(avg7 != null || avg30 != null || avg90 != null) && (
        <View className="flex-row ml-11 mt-1 gap-3">
          {avg7 != null && (
            <Text className="text-[#526380] text-[10px]">
              7d: {metric.format(avg7)}
            </Text>
          )}
          {avg30 != null && (
            <Text className="text-[#526380] text-[10px]">
              30d: {metric.format(avg30)}
            </Text>
          )}
          {avg90 != null && (
            <Text className="text-[#526380] text-[10px]">
              90d: {metric.format(avg90)}
            </Text>
          )}
        </View>
      )}
      {/* Anomaly badge */}
      {summary?.is_anomalous && (
        <View className="flex-row items-center ml-11 mt-1">
          <Ionicons
            name="warning"
            size={10}
            color={summary.anomaly_severity === 'high' ? '#F87171' : '#F59E0B'}
          />
          <Text
            className="text-[10px] ml-1"
            style={{ color: summary.anomaly_severity === 'high' ? '#F87171' : '#F59E0B' }}
          >
            {summary.anomaly_detail}
          </Text>
        </View>
      )}
    </View>
  );
}

// ─── Coming Soon Badge ────────────────────────────────────────────────────────

function ComingSoonBadge() {
  return (
    <View className="bg-[#1E2A3B] rounded-full px-2 py-0.5">
      <Text className="text-[#526380] text-[10px] font-sansMedium">Soon</Text>
    </View>
  );
}

// ─── Wearable Grid Tile ───────────────────────────────────────────────────────

function WearableTile({
  icon,
  label,
  iconColor,
}: {
  icon: React.ComponentProps<typeof Ionicons>['name'];
  label: string;
  iconColor: string;
}) {
  return (
    <View
      className="bg-surface-raised border border-surface-border rounded-2xl items-center justify-center py-4"
      style={{ width: '30%' }}
    >
      <View
        className="w-10 h-10 rounded-xl items-center justify-center mb-2"
        style={{ backgroundColor: `${iconColor}15` }}
      >
        <Ionicons name={icon} size={20} color={iconColor} />
      </View>
      <Text className="text-[#E8EDF5] text-xs font-sansMedium text-center">{label}</Text>
      <View className="mt-1.5">
        <ComingSoonBadge />
      </View>
    </View>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

export default function DevicesScreen() {
  const queryClient = useQueryClient();
  const [syncing, setSyncing] = useState(false);
  const [ouraSyncing, setOuraSyncing] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);
  const [progress, setProgress] = useState('');
  const [lastResult, setLastResult] = useState<{ accepted: number; skipped: number; message?: string } | null>(null);
  const [ouraResult, setOuraResult] = useState<{ accepted: number } | null>(null);
  const [latestValues, setLatestValues] = useState<Record<string, number>>({});

  const syncKey = Platform.OS === 'ios' ? 'healthkit' : 'health_connect';

  const { data: lastSyncTs } = useQuery({
    queryKey: ['sync-timestamp', syncKey],
    queryFn: () => getSyncTimestamp(syncKey),
  });

  const { data: nativeHealthStatus, refetch: refetchNativeStatus } = useQuery({
    queryKey: ['native-health-status'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/api/v1/health-data/status');
        return data as {
          healthkit: { connected: boolean; last_sync: string | null };
          health_connect: { connected: boolean; last_sync: string | null };
        };
      } catch {
        return null;
      }
    },
    staleTime: 0,
  });

  const nativeConnected = Platform.OS === 'ios'
    ? !!nativeHealthStatus?.healthkit?.connected
    : !!nativeHealthStatus?.health_connect?.connected;

  const { data: ouraStatus } = useQuery({
    queryKey: ['oura-connection'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/api/v1/oura/connection');
        return data as { is_active: boolean; is_sandbox?: boolean } | null;
      } catch {
        return null;
      }
    },
    staleTime: 0,
  });

  const ouraConnected = !!ouraStatus?.is_active;

  // Fetch pre-computed summaries (rolling averages, trends, anomalies)
  const { data: summaries, refetch: refetchSummaries } = useQuery({
    queryKey: ['health-summaries'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/api/v1/health-data/summaries');
        return data as Summaries;
      } catch {
        return null;
      }
    },
    staleTime: 60_000,
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
      refetchNativeStatus();
      // Summaries are recomputed in background on the server;
      // refetch after a short delay to pick up the new values
      setTimeout(() => refetchSummaries(), 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Sync failed';
      Alert.alert('Sync failed', msg);
    } finally {
      setSyncing(false);
      setProgress('');
    }
  }, [queryClient, refetchNativeStatus, refetchSummaries]);

  const handleFullSync = useCallback(() => {
    const period = Platform.OS === 'ios' ? 'up to 3 years' : 'up to 30 days';
    Alert.alert(
      'Full History Sync',
      `This will re-download ${period} of health data to establish accurate baselines and averages. This may take a minute.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sync History',
          onPress: async () => {
            await clearSyncTimestamp(syncKey);
            queryClient.invalidateQueries({ queryKey: ['sync-timestamp'] });
            handleSync();
          },
        },
      ]
    );
  }, [syncKey, queryClient, handleSync]);

  const handleHealthDisconnect = useCallback(() => {
    const sourceName = Platform.OS === 'ios' ? 'Apple Health' : 'Health Connect';
    const sourceKey = Platform.OS === 'ios' ? 'healthkit' : 'health_connect';
    Alert.alert(
      `Disconnect ${sourceName}`,
      'This will remove all synced health data. You can reconnect anytime.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Disconnect',
          style: 'destructive',
          onPress: async () => {
            setIsDisconnecting(true);
            try {
              await api.delete(`/api/v1/health-data/source/${sourceKey}`);
              setLatestValues({});
              setLastResult(null);
              queryClient.invalidateQueries({ queryKey: ['native-health-status'] });
              queryClient.invalidateQueries({ queryKey: ['batch'] });
            } catch {
              Alert.alert('Error', `Could not disconnect ${sourceName}`);
            } finally {
              setIsDisconnecting(false);
            }
          },
        },
      ]
    );
  }, [queryClient]);

  const handleOuraSync = useCallback(async () => {
    setOuraSyncing(true);
    try {
      const { data } = await api.post('/api/v1/oura/sync');
      setOuraResult({ accepted: data?.synced_records ?? 0 });
      queryClient.invalidateQueries({ queryKey: ['batch'] });
    } catch {
      Alert.alert('Sync failed', 'Could not sync Oura data');
    } finally {
      setOuraSyncing(false);
    }
  }, [queryClient]);

  const handleOuraDisconnect = useCallback(() => {
    Alert.alert('Disconnect Oura Ring', 'Stop syncing Oura data?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Disconnect',
        style: 'destructive',
        onPress: async () => {
          try {
            await api.delete('/api/v1/oura/connection');
            queryClient.setQueryData(['oura-connection'], null);
          } catch {
            Alert.alert('Error', 'Could not disconnect Oura Ring');
          }
        },
      },
    ]);
  }, [queryClient]);

  const handleOuraConnect = useCallback(async () => {
    setIsConnecting(true);
    try {
      const mobileRedirectUri = 'vitalix://oura-callback';
      const { data } = await api.get('/api/v1/oura/auth-url', {
        params: { redirect_uri: mobileRedirectUri },
      });
      if (data?.sandbox_mode) {
        queryClient.setQueryData(['oura-connection'], { is_active: true, is_sandbox: true });
      } else if (data?.auth_url) {
        // Production OAuth — use in-app browser that captures the deep link callback
        const { openAuthSessionAsync } = await import('expo-web-browser');
        const result = await openAuthSessionAsync(data.auth_url, mobileRedirectUri);
        if (result.type === 'success' && result.url) {
          // Parse the code from the redirect URL
          const url = new URL(result.url);
          const code = url.searchParams.get('code');
          if (code) {
            await api.post('/api/v1/oura/callback', { code, redirect_uri: mobileRedirectUri });
            queryClient.invalidateQueries({ queryKey: ['oura-connection'] });
          } else {
            Alert.alert('Connection failed', 'Authorization code not received.');
          }
        } else if (result.type === 'cancel') {
          // User dismissed — no-op
        }
      } else {
        Alert.alert('Not configured', 'Oura integration is not set up yet.');
      }
    } catch {
      Alert.alert('Error', 'Could not initiate Oura connection');
    } finally {
      setIsConnecting(false);
    }
  }, [queryClient]);

  const platformName = Platform.OS === 'ios' ? 'Apple Health' : 'Google Health Connect';

  const hasValues = Object.keys(latestValues).length > 0 || (summaries && Object.keys(summaries).length > 0);

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 48 }}>
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <Text className="text-xl font-display text-[#E8EDF5]">Health Devices</Text>
      </View>

      <View className="px-6 pt-6">

        {/* ── YOUR DEVICES ─────────────────────────────────────────────────── */}
        <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3">Your Devices</Text>

        {/* Apple Health / Health Connect card */}
        <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
          {/* Device row */}
          <View className="flex-row items-center mb-4">
            <View className="w-12 h-12 rounded-xl items-center justify-center mr-3" style={{ backgroundColor: '#F8717120' }}>
              <Ionicons name="heart" size={24} color="#F87171" />
            </View>
            <View className="flex-1">
              <Text className="text-[#E8EDF5] font-sansMedium text-base">{platformName}</Text>
              <Text className="text-[#526380] text-xs mt-0.5">
                {nativeConnected
                  ? (lastSyncTs ? `Last synced ${format(new Date(lastSyncTs), 'MMM d, h:mm a')}` : 'Synced')
                  : 'Not connected'}
              </Text>
            </View>
            <View className="flex-row items-center gap-1.5">
              <View className="w-2 h-2 rounded-full" style={{ backgroundColor: nativeConnected ? '#6EE7B7' : '#3A4A5C' }} />
              <Text className="text-xs font-sansMedium" style={{ color: nativeConnected ? '#6EE7B7' : '#526380' }}>
                {nativeConnected ? 'Connected' : 'Not linked'}
              </Text>
            </View>
          </View>

          {/* Sync result banner */}
          {lastResult && (
            <View className="bg-primary-500/10 border border-primary-500/30 rounded-xl px-3 py-2.5 mb-3">
              <Text className="text-primary-500 text-sm font-sansMedium">
                {lastResult.message ?? `Synced ${lastResult.accepted} data points`}
                {!lastResult.message && lastResult.skipped > 0
                  ? ` (${lastResult.skipped} already up to date)`
                  : ''}
              </Text>
            </View>
          )}

          {nativeConnected ? (
            <>
              <View className="flex-row gap-2">
                <TouchableOpacity
                  onPress={handleSync}
                  disabled={syncing || isDisconnecting}
                  className="flex-1 bg-primary-500 rounded-xl py-3 items-center"
                  activeOpacity={0.8}
                >
                  {syncing ? (
                    <View className="flex-row items-center gap-2">
                      <ActivityIndicator size="small" color="#080B10" />
                      <Text className="text-obsidian-900 font-sansMedium text-sm">{progress}</Text>
                    </View>
                  ) : (
                    <Text className="text-obsidian-900 font-sansMedium text-sm">Sync Now</Text>
                  )}
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={handleHealthDisconnect}
                  disabled={syncing || isDisconnecting}
                  className="px-4 rounded-xl py-3 items-center"
                  style={{ backgroundColor: 'rgba(255,255,255,0.04)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.08)' }}
                  activeOpacity={0.8}
                >
                  {isDisconnecting
                    ? <ActivityIndicator size="small" color="#526380" />
                    : <Text className="text-[#526380] font-sansMedium text-sm">Disconnect</Text>
                  }
                </TouchableOpacity>
              </View>
              <TouchableOpacity
                onPress={handleFullSync}
                disabled={syncing}
                className="mt-2 items-center"
                activeOpacity={0.7}
              >
                <Text className="text-[#526380] text-xs underline">
                  {Platform.OS === 'ios' ? 'Sync full history (up to 3 years)' : 'Sync full history (up to 30 days)'}
                </Text>
              </TouchableOpacity>
            </>
          ) : (
            /* Not connected — show Connect & Sync */
            <TouchableOpacity
              onPress={handleSync}
              disabled={syncing}
              className="bg-primary-500 rounded-xl py-3 items-center"
              activeOpacity={0.8}
            >
              {syncing ? (
                <View className="flex-row items-center gap-2">
                  <ActivityIndicator size="small" color="#080B10" />
                  <Text className="text-obsidian-900 font-sansMedium text-sm">{progress}</Text>
                </View>
              ) : (
                <Text className="text-obsidian-900 font-sansMedium text-sm">Connect & Sync</Text>
              )}
            </TouchableOpacity>
          )}

          {/* Metric rows — shown after first sync */}
          {hasValues && (
            <View className="mt-4 pt-4 border-t border-surface-border">
              <View className="flex-row items-center mb-2">
                <Ionicons name="heart" size={12} color="#F87171" />
                <Text className="text-[#526380] text-xs ml-1.5">{platformName}</Text>
              </View>
              {METRICS.map((m) => (
                <MetricRow
                  key={m.metricType}
                  metric={m}
                  value={latestValues[m.metricType] ?? null}
                  summary={summaries?.[m.metricType]}
                />
              ))}
            </View>
          )}
        </View>

        {/* Oura Ring card */}
        <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-6">
          <View className="flex-row items-center mb-4">
            <View className="w-12 h-12 rounded-xl items-center justify-center mr-3" style={{ backgroundColor: '#818CF820' }}>
              <Ionicons name="radio-button-on-outline" size={24} color="#818CF8" />
            </View>
            <View className="flex-1">
              <Text className="text-[#E8EDF5] font-sansMedium text-base">Oura Ring</Text>
              <Text className="text-[#526380] text-xs mt-0.5">
                {ouraConnected ? 'Sleep, HRV & readiness syncing' : 'Track sleep, HRV & readiness'}
              </Text>
            </View>
            <View className="flex-row items-center gap-1.5">
              <View className="w-2 h-2 rounded-full" style={{ backgroundColor: ouraConnected ? '#6EE7B7' : '#3A4A5C' }} />
              <Text className="text-xs font-sansMedium" style={{ color: ouraConnected ? '#6EE7B7' : '#526380' }}>
                {ouraConnected ? 'Connected' : 'Not linked'}
              </Text>
            </View>
          </View>

          {ouraResult && (
            <View className="bg-primary-500/10 border border-primary-500/30 rounded-xl px-3 py-2.5 mb-3">
              <Text className="text-primary-500 text-sm font-sansMedium">
                {`Synced ${ouraResult.accepted} data points`}
              </Text>
            </View>
          )}

          {ouraConnected ? (
            <View className="flex-row gap-2">
              <TouchableOpacity
                onPress={handleOuraSync}
                disabled={ouraSyncing}
                className="flex-1 bg-primary-500/10 border border-primary-500/30 rounded-xl py-3 items-center"
                activeOpacity={0.8}
              >
                {ouraSyncing
                  ? <ActivityIndicator size="small" color="#818CF8" />
                  : <Text className="text-primary-500 font-sansMedium text-sm">Sync Now</Text>
                }
              </TouchableOpacity>
              <TouchableOpacity
                onPress={handleOuraDisconnect}
                className="px-4 rounded-xl py-3 items-center"
                style={{ backgroundColor: 'rgba(255,255,255,0.04)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.08)' }}
                activeOpacity={0.8}
              >
                <Text className="text-[#526380] font-sansMedium text-sm">Disconnect</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <TouchableOpacity
              onPress={handleOuraConnect}
              disabled={isConnecting}
              className="rounded-xl py-3 items-center"
              style={{ backgroundColor: '#818CF820', borderWidth: 1, borderColor: '#818CF840' }}
              activeOpacity={0.8}
            >
              {isConnecting
                ? <ActivityIndicator size="small" color="#818CF8" />
                : <Text className="text-[#818CF8] font-sansMedium text-sm">Connect Oura Ring</Text>
              }
            </TouchableOpacity>
          )}
        </View>

        {/* ── ADD A WEARABLE ────────────────────────────────────────────────── */}
        <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3">Add a Wearable</Text>
        <View className="flex-row flex-wrap gap-3 mb-6">
          <WearableTile icon="watch-outline"          label="Garmin"   iconColor="#00D4AA" />
          <WearableTile icon="fitness-outline"        label="Whoop"    iconColor="#F5A623" />
          <WearableTile icon="body-outline"           label="Fitbit"   iconColor="#60A5FA" />
          <WearableTile icon="phone-portrait-outline" label="Samsung"  iconColor="#6EE7B7" />
          <WearableTile icon="pulse-outline"          label="Polar"    iconColor="#F87171" />
          <WearableTile icon="add-circle-outline"     label="More"     iconColor="#818CF8" />
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
