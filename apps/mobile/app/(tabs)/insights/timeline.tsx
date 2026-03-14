/**
 * Phase 4: Timeline screen.
 * Scrollable date-by-date health diary.
 * Data: GET /api/v1/health/timeline?days=30
 */

import { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format, isToday, isYesterday } from 'date-fns';
import { api } from '@/services/api';
import {
  loadDataSourcePrefs,
  toApiPriority,
  type SourceOption,
} from '@/utils/dataSourcePrefs';

// ─── Types ────────────────────────────────────────────────────────────────────

interface AltMetrics {
  source: string;
  steps?: number;
  sleep_hours?: number;
  resting_heart_rate?: number;
  hrv_ms?: number;
}

interface TimelineEntry {
  date: string;
  sources?: string[];
  alt_metrics?: AltMetrics;
  sleep?: {
    sleep_score?: number;
    total_sleep_duration?: number;
    sleep_efficiency?: number;
    deep_sleep_duration?: number;
  };
  readiness?: {
    readiness_score?: number;
    hrv_balance?: number;
    resting_heart_rate?: number;
    recovery_index?: number;
  };
  activity?: {
    steps?: number;
    activity_score?: number;
    active_calories?: number;
  };
}

const DAY_OPTIONS = [7, 14, 30] as const;

// ─── Score Ring (compact) ─────────────────────────────────────────────────────

function ScoreChip({ value, label, color }: Readonly<{ value: number; label: string; color: string }>) {
  return (
    <View className="items-center flex-1">
      <Text className="font-display text-lg" style={{ color }}>
        {Math.round(value)}
      </Text>
      <Text className="text-[#526380] text-xs">{label}</Text>
    </View>
  );
}

// ─── Timeline Day Card ────────────────────────────────────────────────────────

function DayCard({ entry }: Readonly<{ entry: TimelineEntry }>) {
  const d = new Date(entry.date);
  let dateLabel = format(d, 'EEE, MMM d');
  if (isToday(d)) dateLabel = 'Today';
  else if (isYesterday(d)) dateLabel = 'Yesterday';

  const sleep = entry.sleep?.sleep_score;
  const readiness = entry.readiness?.readiness_score;
  const activity = entry.activity?.activity_score;
  const steps = entry.activity?.steps;
  const hr = entry.readiness?.resting_heart_rate;
  const hrv = entry.readiness?.hrv_balance;

  const sleepHrs = entry.sleep?.total_sleep_duration
    ? (entry.sleep.total_sleep_duration / 3600).toFixed(1)
    : null;

  const topScore = Math.max(sleep ?? 0, readiness ?? 0, activity ?? 0);
  let topColor = '#F87171';
  if (topScore >= 80) topColor = '#6EE7B7';
  else if (topScore >= 60) topColor = '#F5A623';

  let sleepColor = '#F87171';
  if (sleep == null || sleep >= 80) sleepColor = '#818CF8';
  else if (sleep >= 60) sleepColor = '#F5A623';

  let readinessColor = '#F87171';
  if (readiness == null || readiness >= 80) readinessColor = '#6EE7B7';
  else if (readiness >= 60) readinessColor = '#F5A623';

  let activityColor = '#F87171';
  if (activity == null || activity >= 60) activityColor = '#F5A623';

  const sourceLabels: Record<string, string> = {
    oura: 'Oura',
    healthkit: 'Apple Health',
    health_connect: 'Health Connect',
  };

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
      {/* Date row */}
      <View className="flex-row items-center justify-between mb-3">
        <Text className="text-[#E8EDF5] font-sansMedium text-sm">{dateLabel}</Text>
        <View className="flex-row items-center gap-2">
          {entry.sources && entry.sources.length > 0 && (
            <View className="flex-row gap-1">
              {entry.sources.map((s) => (
                <View key={s} className="bg-[#1E2A3B] rounded-full px-1.5 py-0.5">
                  <Text className="text-[#526380] text-[9px]">{sourceLabels[s] ?? s}</Text>
                </View>
              ))}
            </View>
          )}
          <View
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: topScore > 0 ? topColor : '#1E2A3B' }}
          />
        </View>
      </View>

      {/* Scores row */}
      {(sleep != null || readiness != null || activity != null) && (
        <View className="flex-row mb-3 pb-3 border-b border-surface-border">
          {sleep != null && <ScoreChip value={sleep} label="Sleep" color={sleepColor} />}
          {readiness != null && <ScoreChip value={readiness} label="Readiness" color={readinessColor} />}
          {activity != null && <ScoreChip value={activity} label="Activity" color={activityColor} />}
        </View>
      )}

      {/* Detail row */}
      <View className="flex-row flex-wrap gap-3">
        {sleepHrs != null && (
          <View className="flex-row items-center gap-1">
            <Ionicons name="moon-outline" size={12} color="#526380" />
            <Text className="text-[#526380] text-xs">{sleepHrs}h sleep</Text>
          </View>
        )}
        {steps != null && (
          <View className="flex-row items-center gap-1">
            <Ionicons name="footsteps-outline" size={12} color="#526380" />
            <Text className="text-[#526380] text-xs">{steps.toLocaleString()} steps</Text>
          </View>
        )}
        {hr != null && (
          <View className="flex-row items-center gap-1">
            <Ionicons name="heart-outline" size={12} color="#526380" />
            <Text className="text-[#526380] text-xs">{hr} bpm</Text>
          </View>
        )}
        {hrv != null && (
          <View className="flex-row items-center gap-1">
            <Ionicons name="pulse-outline" size={12} color="#526380" />
            <Text className="text-[#526380] text-xs">HRV {hrv}</Text>
          </View>
        )}
      </View>

      {/* Alt source comparison row */}
      {entry.alt_metrics && (() => {
        const alt = entry.alt_metrics;
        const SOURCE_NAMES: Record<string, string> = { oura: 'Oura', healthkit: 'Apple Health', health_connect: 'Health Connect' };
        const altLabel = SOURCE_NAMES[alt.source] ?? alt.source;
        const hasAlt = alt.steps != null || alt.sleep_hours != null || alt.resting_heart_rate != null || alt.hrv_ms != null;
        if (!hasAlt) return null;
        return (
          <View className="mt-2 pt-2 border-t border-surface-border">
            <Text className="text-[#3A4A5C] text-[10px] mb-1">{altLabel} also tracked:</Text>
            <View className="flex-row flex-wrap gap-3">
              {alt.steps != null && (
                <Text className="text-[#3A4A5C] text-xs">{alt.steps.toLocaleString()} steps</Text>
              )}
              {alt.sleep_hours != null && (
                <Text className="text-[#3A4A5C] text-xs">{alt.sleep_hours.toFixed(1)}h sleep</Text>
              )}
              {alt.resting_heart_rate != null && (
                <Text className="text-[#3A4A5C] text-xs">{alt.resting_heart_rate} bpm</Text>
              )}
              {alt.hrv_ms != null && (
                <Text className="text-[#3A4A5C] text-xs">HRV {alt.hrv_ms.toFixed(1)} ms</Text>
              )}
            </View>
          </View>
        );
      })()}
    </View>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

function TimelineBody({ isLoading, entries }: Readonly<{ isLoading: boolean; entries: TimelineEntry[] }>) {
  if (isLoading) return <ActivityIndicator color="#00D4AA" className="mt-10" />;
  if (entries.length === 0) {
    return (
      <View className="items-center py-16">
        <Ionicons name="calendar-outline" size={44} color="#526380" />
        <Text className="text-[#526380] text-base mt-3">No timeline data</Text>
        <Text className="text-[#526380] text-sm mt-1 text-center">
          Connect a wearable device to populate your health timeline
        </Text>
      </View>
    );
  }
  return <>{entries.map((entry) => <DayCard key={entry.date} entry={entry} />)}</>;
}

export default function TimelineScreen() {
  const [days, setDays] = useState<7 | 14 | 30>(14);
  const [sourcePriority, setSourcePriority] = useState<SourceOption>('auto');

  useEffect(() => {
    loadDataSourcePrefs().then((p) => setSourcePriority(toApiPriority(p)));
  }, []);

  const { data, isLoading } = useQuery<{ entries: TimelineEntry[] }>({
    queryKey: ['health-timeline', days, sourcePriority],
    queryFn: async () => {
      const { data: resp } = await api.get(
        `/api/v1/health/timeline?days=${days}&source_priority=${sourcePriority}`
      );
      return { entries: Array.isArray(resp) ? resp : (resp?.entries ?? []) };
    },
  });

  const rawEntries = Array.isArray(data) ? data : (data?.entries ?? []);
  const entries = [...rawEntries].reverse(); // most recent first

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <Text className="text-xl font-display text-[#E8EDF5] flex-1">Timeline</Text>
        <View className="flex-row gap-1">
          {DAY_OPTIONS.map((d) => (
            <TouchableOpacity
              key={d}
              onPress={() => setDays(d)}
              className="px-2.5 py-1 rounded-lg"
              style={{
                backgroundColor: days === d ? '#00D4AA20' : 'transparent',
                borderWidth: 1,
                borderColor: days === d ? '#00D4AA' : '#1E2A3B',
              }}
            >
              <Text className="text-xs font-sansMedium" style={{ color: days === d ? '#00D4AA' : '#526380' }}>
                {d}d
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View className="px-6 pt-5">
        <TimelineBody isLoading={isLoading} entries={entries} />
      </View>
    </ScrollView>
  );
}
