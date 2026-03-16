/**
 * Phase 4: Trends screen.
 * Shows 30-day time-series charts for key health metrics.
 * Data: GET /api/v1/health/timeline?days=30
 */

import { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/services/api';
import { MiniLineChart } from '@/components/MiniLineChart';
import { HealthRings, type RingData } from '@/components/HealthRings';
import {
  loadDataSourcePrefs,
  toApiPriority,
  type SourceOption,
  type DataSourcePrefs,
} from '@/utils/dataSourcePrefs';

// ─── Types ────────────────────────────────────────────────────────────────────

interface TimelineEntry {
  date: string;
  sleep?: { sleep_score?: number; total_sleep_duration?: number };
  readiness?: { readiness_score?: number; hrv_balance?: number; resting_heart_rate?: number };
  activity?: { steps?: number; activity_score?: number; active_calories?: number };
  sources?: string[];
  native?: {
    respiratory_rate?: number;
    spo2?: number;
    active_calories?: number;
    workout_minutes?: number;
    vo2_max?: number;
  };
}

interface MetricConfig {
  label: string;
  key: (e: TimelineEntry) => number | undefined;
  unit: string;
  color: string;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  higherIsBetter: boolean;
}

const SOURCE_BADGE: Record<string, { label: string; color: string }> = {
  oura: { label: '⊙', color: '#818CF8' },
  healthkit: { label: '🍎', color: '#F87171' },
  health_connect: { label: '💚', color: '#34D399' },
};

const METRICS: MetricConfig[] = [
  // ── Core (from Oura or computed) ──
  {
    label: 'Sleep Score',
    key: (e) => e.sleep?.sleep_score,
    unit: 'pts',
    color: '#818CF8',
    icon: 'moon-outline',
    higherIsBetter: true,
  },
  {
    label: 'Readiness',
    key: (e) => e.readiness?.readiness_score,
    unit: 'pts',
    color: '#6EE7B7',
    icon: 'battery-charging-outline',
    higherIsBetter: true,
  },
  {
    label: 'Activity Score',
    key: (e) => e.activity?.activity_score,
    unit: 'pts',
    color: '#F5A623',
    icon: 'walk-outline',
    higherIsBetter: true,
  },
  // ── Heart & Vitals ──
  {
    label: 'Resting HR',
    key: (e) => e.readiness?.resting_heart_rate,
    unit: 'bpm',
    color: '#F87171',
    icon: 'heart-outline',
    higherIsBetter: false,
  },
  {
    label: 'HRV',
    key: (e) => e.readiness?.hrv_balance,
    unit: 'ms',
    color: '#00D4AA',
    icon: 'pulse-outline',
    higherIsBetter: true,
  },
  {
    label: 'SpO₂',
    key: (e) => e.native?.spo2,
    unit: '%',
    color: '#60A5FA',
    icon: 'water-outline',
    higherIsBetter: true,
  },
  {
    label: 'Respiratory Rate',
    key: (e) => e.native?.respiratory_rate,
    unit: '/min',
    color: '#A78BFA',
    icon: 'cellular-outline',
    higherIsBetter: false,
  },
  // ── Activity ──
  {
    label: 'Daily Steps',
    key: (e) => e.activity?.steps,
    unit: 'steps',
    color: '#34D399',
    icon: 'footsteps-outline',
    higherIsBetter: true,
  },
  {
    label: 'Active Calories',
    key: (e) => e.native?.active_calories ?? e.activity?.active_calories,
    unit: 'kcal',
    color: '#FB923C',
    icon: 'flame-outline',
    higherIsBetter: true,
  },
  {
    label: 'Workouts',
    key: (e) => e.native?.workout_minutes,
    unit: 'min',
    color: '#F59E0B',
    icon: 'barbell-outline',
    higherIsBetter: true,
  },
  {
    label: 'VO₂ Max',
    key: (e) => e.native?.vo2_max,
    unit: 'mL/kg/min',
    color: '#2DD4BF',
    icon: 'speedometer-outline',
    higherIsBetter: true,
  },
];

const DAY_OPTIONS = [7, 14, 30, 60, 90] as const;

// ─── Metric Chart Card ────────────────────────────────────────────────────────

function MetricCard({ metric, entries }: Readonly<{ metric: MetricConfig; entries: TimelineEntry[] }>) {
  const data = entries
    .map((e) => metric.key(e))
    .filter((v): v is number => v != null && !Number.isNaN(v));

  if (data.length === 0) {
    return (
      <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
        <View className="flex-row items-center gap-2 mb-2">
          <Ionicons name={metric.icon} size={16} color={metric.color} />
          <Text className="text-[#526380] text-sm font-sansMedium">{metric.label}</Text>
        </View>
        <Text className="text-[#3A4A5C] text-xs">No data available</Text>
      </View>
    );
  }

  const latest = data[data.length - 1];
  const avg = data.reduce((a, b) => a + b, 0) / data.length;
  const trend = data.length >= 7 ? latest - (data.at(-8) ?? data[0]) : 0;
  const trendUp = trend > 0;
  const trendColor = (trendUp === metric.higherIsBetter) ? '#6EE7B7' : '#F87171';

  const isScoreMetric = metric.label === 'Sleep Score' || metric.label === 'Readiness' || metric.label === 'Activity Score';
  let latestDisplay: string;
  if (metric.label === 'Daily Steps') {
    latestDisplay = latest.toLocaleString();
  } else if (isScoreMetric) {
    latestDisplay = String(Math.round(latest));
  } else {
    latestDisplay = latest.toFixed(0);
  }

  let trendIcon: React.ComponentProps<typeof Ionicons>['name'];
  if (trend === 0) {
    trendIcon = 'remove';
  } else if (trendUp) {
    trendIcon = 'trending-up';
  } else {
    trendIcon = 'trending-down';
  }

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
      <View className="flex-row items-center justify-between mb-1">
        <View className="flex-row items-center gap-2">
          <Ionicons name={metric.icon} size={16} color={metric.color} />
          <Text className="text-[#526380] text-sm font-sansMedium">{metric.label}</Text>
        </View>
        <View className="flex-row items-center gap-1">
          <Ionicons
            name={trendIcon}
            size={14}
            color={trend === 0 ? '#526380' : trendColor}
          />
          <Text className="text-xl font-display" style={{ color: metric.color }}>
            {latestDisplay}
          </Text>
          {metric.unit ? (
            <Text className="text-[#526380] text-xs">{metric.unit}</Text>
          ) : null}
        </View>
      </View>

      <MiniLineChart data={data} color={metric.color} height={64} showLastValue={false} />

      <View className="flex-row justify-between items-center mt-2">
        <Text className="text-[#526380] text-xs">
          Avg: {metric.label === 'Daily Steps' ? avg.toLocaleString(undefined, { maximumFractionDigits: 0 }) : avg.toFixed(1)}{' '}
          {metric.unit}
        </Text>
        <View className="flex-row items-center gap-2">
          {/* Source badges */}
          {(() => {
            const allSources = new Set(entries.flatMap((e) => e.sources ?? []));
            return Array.from(allSources).map((s) => {
              const badge = SOURCE_BADGE[s];
              return badge ? (
                <Text key={s} style={{ color: badge.color, fontSize: 10 }}>{badge.label}</Text>
              ) : null;
            });
          })()}
          <Text className="text-[#526380] text-xs">{data.length}d</Text>
        </View>
      </View>
    </View>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

export default function TrendsScreen() {
  const [days, setDays] = useState<7 | 14 | 30 | 60 | 90>(30);
  const [sourcePriority, setSourcePriority] = useState<SourceOption>('auto');

  useEffect(() => {
    loadDataSourcePrefs().then((p: DataSourcePrefs) => setSourcePriority(toApiPriority(p)));
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

  const entries = Array.isArray(data) ? data : (data?.entries ?? []);

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <Text className="text-xl font-display text-[#E8EDF5] flex-1">Health Timeline</Text>
        {/* Day range */}
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
        {isLoading && <ActivityIndicator color="#00D4AA" className="mt-10" />}
        {!isLoading && entries.length === 0 && (
          <View className="items-center py-16">
            <Ionicons name="analytics-outline" size={44} color="#526380" />
            <Text className="text-[#526380] text-base mt-3">No trend data yet</Text>
            <Text className="text-[#526380] text-sm mt-1 text-center">
              Connect a wearable device to see health trends
            </Text>
          </View>
        )}
        {/* Health Rings — today's snapshot */}
        {!isLoading && entries.length > 0 && (() => {
          const today = entries[entries.length - 1]; // most recent
          const sleepHrs = today?.sleep?.total_sleep_duration
            ? today.sleep.total_sleep_duration / 3600
            : 0;
          const hrv = today?.readiness?.hrv_balance ?? 0;
          const steps = today?.activity?.steps ?? 0;
          const readiness = today?.readiness?.readiness_score ?? 0;
          const sleepScore = today?.sleep?.sleep_score;
          const activityScore = today?.activity?.activity_score;
          const overallScore = sleepScore && readiness && activityScore
            ? Math.round((sleepScore * 0.4 + readiness * 0.35 + activityScore * 0.25))
            : null;

          const ringData: RingData = {
            sleep:    { value: sleepHrs, goal: 8 },
            heart:    { value: hrv, goal: hrv > 0 ? Math.max(hrv * 1.1, 50) : 50 },
            activity: { value: steps, goal: 8000 },
            recovery: { value: readiness, goal: 100 },
            overallScore,
          };

          return (
            <View className="bg-surface-raised border border-surface-border rounded-2xl p-5 mb-4 items-center">
              <HealthRings data={ringData} size={180} />
            </View>
          );
        })()}
        {!isLoading && entries.length > 0 && METRICS.map((m) => (
          <MetricCard key={m.label} metric={m} entries={entries} />
        ))}

        {/* Daily Timeline Cards */}
        {!isLoading && entries.length > 0 && (
          <>
            <Text className="text-[#526380] text-xs uppercase tracking-wider mt-6 mb-3">Daily Timeline</Text>
            {entries.map((entry) => (
              <DailyTimelineCard key={entry.date} entry={entry} />
            ))}
          </>
        )}
      </View>
    </ScrollView>
  );
}

// ─── Daily Timeline Card (mobile) ────────────────────────────────────────────

function DailyTimelineCard({ entry }: { entry: TimelineEntry }) {
  const [expanded, setExpanded] = useState(false);
  const native = entry.native;
  const sources = entry.sources ?? [];

  const formatDur = (secs?: number) => {
    if (!secs) return '—';
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    return `${h}h ${m}m`;
  };

  const dateLabel = (() => {
    const d = new Date(entry.date + 'T00:00:00');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  })();

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-2">
      <TouchableOpacity onPress={() => setExpanded((v) => !v)} activeOpacity={0.8}>
        <View className="flex-row items-center justify-between">
          <View>
            <Text className="text-[#E8EDF5] text-sm font-sansMedium">{dateLabel}</Text>
            {sources.length > 0 && (
              <View className="flex-row gap-1 mt-1">
                {sources.map((s) => {
                  const badge = SOURCE_BADGE[s];
                  return badge ? (
                    <Text key={s} style={{ color: badge.color, fontSize: 9 }}>{badge.label}</Text>
                  ) : null;
                })}
              </View>
            )}
          </View>
          <View className="flex-row items-center gap-3">
            {entry.sleep?.sleep_score != null && (
              <View className="items-center">
                <View className="w-10 h-10 rounded-full items-center justify-center border-2" style={{ borderColor: '#818CF8' }}>
                  <Text className="text-xs font-sansMedium" style={{ color: '#818CF8' }}>{entry.sleep.sleep_score}</Text>
                </View>
                <Text className="text-[8px] text-[#526380] mt-0.5">Sleep</Text>
              </View>
            )}
            {entry.readiness?.hrv_balance != null && (
              <View className="items-center">
                <View className="w-10 h-10 rounded-full items-center justify-center border-2" style={{ borderColor: '#F87171' }}>
                  <Text className="text-xs font-sansMedium" style={{ color: '#F87171' }}>{Math.round(entry.readiness.hrv_balance)}</Text>
                </View>
                <Text className="text-[8px] text-[#526380] mt-0.5">Heart</Text>
              </View>
            )}
            {entry.activity?.activity_score != null && (
              <View className="items-center">
                <View className="w-10 h-10 rounded-full items-center justify-center border-2" style={{ borderColor: '#6EE7B7' }}>
                  <Text className="text-xs font-sansMedium" style={{ color: '#6EE7B7' }}>{entry.activity.activity_score}</Text>
                </View>
                <Text className="text-[8px] text-[#526380] mt-0.5">Activity</Text>
              </View>
            )}
            {entry.readiness?.readiness_score != null && (
              <View className="items-center">
                <View className="w-10 h-10 rounded-full items-center justify-center border-2" style={{ borderColor: '#F59E0B' }}>
                  <Text className="text-xs font-sansMedium" style={{ color: '#F59E0B' }}>{entry.readiness.readiness_score}</Text>
                </View>
                <Text className="text-[8px] text-[#526380] mt-0.5">Recovery</Text>
              </View>
            )}
            <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={16} color="#526380" />
          </View>
        </View>
      </TouchableOpacity>

      {expanded && (
        <View className="mt-3 pt-3 border-t border-surface-border">
          <View className="flex-row flex-wrap gap-x-6 gap-y-3">
            {/* Sleep */}
            {entry.sleep && (
              <View style={{ minWidth: '40%' }}>
                <Text className="text-[10px] font-sansMedium mb-1" style={{ color: '#818CF8' }}>Sleep</Text>
                <Text className="text-[#526380] text-[10px]">Duration: <Text className="text-[#E8EDF5]">{formatDur(entry.sleep.total_sleep_duration)}</Text></Text>
                <Text className="text-[#526380] text-[10px]">Deep: <Text className="text-[#E8EDF5]">{formatDur(entry.sleep.deep_sleep_duration)}</Text></Text>
                <Text className="text-[#526380] text-[10px]">REM: <Text className="text-[#E8EDF5]">{formatDur(entry.sleep.rem_sleep_duration)}</Text></Text>
                <Text className="text-[#526380] text-[10px]">Efficiency: <Text className="text-[#E8EDF5]">{entry.sleep.sleep_efficiency}%</Text></Text>
              </View>
            )}
            {/* Heart */}
            {entry.readiness && (
              <View style={{ minWidth: '40%' }}>
                <Text className="text-[10px] font-sansMedium mb-1" style={{ color: '#F87171' }}>Heart</Text>
                <Text className="text-[#526380] text-[10px]">HRV: <Text className="text-[#E8EDF5]">{entry.readiness.hrv_balance} ms</Text></Text>
                <Text className="text-[#526380] text-[10px]">Resting HR: <Text className="text-[#E8EDF5]">{entry.readiness.resting_heart_rate} bpm</Text></Text>
                {native?.spo2 != null && <Text className="text-[#526380] text-[10px]">SpO₂: <Text className="text-[#E8EDF5]">{native.spo2.toFixed(1)}%</Text></Text>}
                {native?.respiratory_rate != null && <Text className="text-[#526380] text-[10px]">Resp: <Text className="text-[#E8EDF5]">{native.respiratory_rate.toFixed(1)}/min</Text></Text>}
              </View>
            )}
            {/* Activity */}
            {entry.activity && (
              <View style={{ minWidth: '40%' }}>
                <Text className="text-[10px] font-sansMedium mb-1" style={{ color: '#6EE7B7' }}>Activity</Text>
                <Text className="text-[#526380] text-[10px]">Steps: <Text className="text-[#E8EDF5]">{entry.activity.steps?.toLocaleString()}</Text></Text>
                <Text className="text-[#526380] text-[10px]">Calories: <Text className="text-[#E8EDF5]">{native?.active_calories ?? entry.activity.active_calories} kcal</Text></Text>
                {native?.workout_minutes != null && <Text className="text-[#526380] text-[10px]">Workouts: <Text className="text-[#E8EDF5]">{native.workout_minutes} min</Text></Text>}
                {native?.vo2_max != null && <Text className="text-[#526380] text-[10px]">VO₂ Max: <Text className="text-[#E8EDF5]">{native.vo2_max.toFixed(1)}</Text></Text>}
              </View>
            )}
          </View>
        </View>
      )}
    </View>
  );
}
