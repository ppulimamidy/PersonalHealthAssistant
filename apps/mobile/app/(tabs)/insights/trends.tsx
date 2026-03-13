/**
 * Phase 4: Trends screen.
 * Shows 30-day time-series charts for key health metrics.
 * Data: GET /api/v1/health/timeline?days=30
 */

import { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { api } from '@/services/api';
import { MiniLineChart } from '@/components/MiniLineChart';

// ─── Types ────────────────────────────────────────────────────────────────────

interface TimelineEntry {
  date: string;
  sleep?: { sleep_score?: number; total_sleep_duration?: number };
  readiness?: { readiness_score?: number; hrv_balance?: number; resting_heart_rate?: number };
  activity?: { steps?: number; activity_score?: number; active_calories?: number };
}

interface MetricConfig {
  label: string;
  key: (e: TimelineEntry) => number | undefined;
  unit: string;
  color: string;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  higherIsBetter: boolean;
}

const METRICS: MetricConfig[] = [
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
  {
    label: 'Resting HR',
    key: (e) => e.readiness?.resting_heart_rate,
    unit: 'bpm',
    color: '#F87171',
    icon: 'heart-outline',
    higherIsBetter: false,
  },
  {
    label: 'HRV Balance',
    key: (e) => e.readiness?.hrv_balance,
    unit: '',
    color: '#00D4AA',
    icon: 'pulse-outline',
    higherIsBetter: true,
  },
  {
    label: 'Daily Steps',
    key: (e) => e.activity?.steps,
    unit: 'steps',
    color: '#60A5FA',
    icon: 'footsteps-outline',
    higherIsBetter: true,
  },
];

const DAY_OPTIONS = [7, 14, 30] as const;

// ─── Metric Chart Card ────────────────────────────────────────────────────────

function MetricCard({ metric, entries }: { metric: MetricConfig; entries: TimelineEntry[] }) {
  const data = entries
    .map((e) => metric.key(e))
    .filter((v): v is number => v != null && !isNaN(v));

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
  const trend = data.length >= 7 ? latest - data[Math.max(0, data.length - 8)] : 0;
  const trendUp = trend > 0;
  const trendColor = (trendUp === metric.higherIsBetter) ? '#6EE7B7' : '#F87171';

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
      <View className="flex-row items-center justify-between mb-1">
        <View className="flex-row items-center gap-2">
          <Ionicons name={metric.icon} size={16} color={metric.color} />
          <Text className="text-[#526380] text-sm font-sansMedium">{metric.label}</Text>
        </View>
        <View className="flex-row items-center gap-1">
          <Ionicons
            name={trend === 0 ? 'remove' : trendUp ? 'trending-up' : 'trending-down'}
            size={14}
            color={trend === 0 ? '#526380' : trendColor}
          />
          <Text className="text-xl font-display" style={{ color: metric.color }}>
            {metric.label === 'Daily Steps'
              ? latest.toLocaleString()
              : metric.label === 'Sleep Score' || metric.label === 'Readiness' || metric.label === 'Activity Score'
              ? Math.round(latest)
              : latest.toFixed(0)}
          </Text>
          {metric.unit ? (
            <Text className="text-[#526380] text-xs">{metric.unit}</Text>
          ) : null}
        </View>
      </View>

      <MiniLineChart data={data} color={metric.color} height={64} showLastValue={false} />

      <View className="flex-row justify-between mt-2">
        <Text className="text-[#526380] text-xs">
          Avg: {metric.label === 'Daily Steps' ? avg.toLocaleString(undefined, { maximumFractionDigits: 0 }) : avg.toFixed(1)}{' '}
          {metric.unit}
        </Text>
        <Text className="text-[#526380] text-xs">{data.length} days</Text>
      </View>
    </View>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

export default function TrendsScreen() {
  const [days, setDays] = useState<7 | 14 | 30>(30);

  const { data, isLoading } = useQuery<{ entries: TimelineEntry[] }>({
    queryKey: ['health-timeline', days],
    queryFn: async () => {
      const { data: resp } = await api.get(`/api/v1/health/timeline?days=${days}`);
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
        <Text className="text-xl font-display text-[#E8EDF5] flex-1">Trends</Text>
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
        {isLoading ? (
          <ActivityIndicator color="#00D4AA" className="mt-10" />
        ) : entries.length === 0 ? (
          <View className="items-center py-16">
            <Ionicons name="analytics-outline" size={44} color="#526380" />
            <Text className="text-[#526380] text-base mt-3">No trend data yet</Text>
            <Text className="text-[#526380] text-sm mt-1 text-center">
              Connect a wearable device to see health trends
            </Text>
          </View>
        ) : (
          METRICS.map((m) => (
            <MetricCard key={m.label} metric={m} entries={entries} />
          ))
        )}
      </View>
    </ScrollView>
  );
}
