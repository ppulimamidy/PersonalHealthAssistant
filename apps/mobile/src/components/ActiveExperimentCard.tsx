import { useState } from 'react';
import { View, Text, TouchableOpacity, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Svg, { Polyline } from 'react-native-svg';
import { api } from '@/services/api';

interface MetricTrendPoint {
  date: string;
  metric: string;
  value: number | null;
}

interface KeyMetricDelta {
  metric: string;
  label: string;
  baseline_value: number | null;
  current_value: number | null;
  delta_pct: number | null;
  direction: string;
}

interface Checkin {
  id: string;
  checkin_date: string;
  adhered: boolean;
}

interface ActiveIntervention {
  id: string;
  recommendation_pattern: string;
  title: string;
  description: string | null;
  duration_days: number;
  started_at: string;
  ends_at: string;
  status: string;
  adherence_days: number;
  adherence_pct: number | null;
  days_remaining: number | null;
  baseline_metrics: Record<string, number | null> | null;
  checkins: Checkin[] | null;
  metric_trend: MetricTrendPoint[] | null;
  key_metric: KeyMetricDelta | null;
  today_checked_in: boolean | null;
}

function MiniSparkline({ points, color }: { points: number[]; color: string }) {
  if (points.length < 2) return null;
  const w = 60;
  const h = 20;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const step = w / (points.length - 1);
  const coords = points.map((v, i) => `${i * step},${h - ((v - min) / range) * h}`).join(' ');
  return (
    <Svg width={w} height={h}>
      <Polyline points={coords} fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}

export default function ActiveExperimentCard() {
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState(false);

  const { data: intervention, isLoading } = useQuery<ActiveIntervention | null>({
    queryKey: ['active-intervention'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/interventions/active');
      return data || null;
    },
    staleTime: 60_000,
  });

  const checkinMutation = useMutation({
    mutationFn: async ({ id, adhered }: { id: string; adhered: boolean }) => {
      await api.post(`/api/v1/interventions/${id}/checkin`, { adhered });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['active-intervention'] });
    },
  });

  const abandonMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.patch(`/api/v1/interventions/${id}/abandon`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['active-intervention'] });
      queryClient.invalidateQueries({ queryKey: ['top-recommendation'] });
    },
  });

  if (isLoading || !intervention) return null;

  const dayNumber = intervention.duration_days - (intervention.days_remaining ?? 0);
  const progressPct = Math.min((dayNumber / intervention.duration_days) * 100, 100);
  const km = intervention.key_metric;
  const checkedInToday = intervention.today_checked_in ?? false;

  const sparkData: number[] = [];
  if (km && intervention.metric_trend) {
    sparkData.push(
      ...intervention.metric_trend
        .filter((p) => p.metric === km.metric && p.value != null)
        .map((p) => p.value as number),
    );
  }

  const deltaColor = km?.direction === 'up' ? '#00D4AA' : km?.direction === 'down' ? '#F87171' : '#526380';
  const deltaIcon = km?.direction === 'up' ? 'trending-up' : km?.direction === 'down' ? 'trending-down' : 'remove';

  return (
    <View
      className="rounded-2xl p-4 mb-4"
      style={{
        backgroundColor: 'rgba(167,139,250,0.04)',
        borderWidth: 1,
        borderColor: 'rgba(167,139,250,0.15)',
      }}
    >
      {/* Header */}
      <View className="flex-row items-center justify-between mb-3">
        <View className="flex-row items-center gap-2">
          <View
            className="w-7 h-7 rounded-lg items-center justify-center"
            style={{ backgroundColor: 'rgba(167,139,250,0.12)' }}
          >
            <Ionicons name="flask-outline" size={14} color="#A78BFA" />
          </View>
          <Text className="text-[10px] font-bold uppercase tracking-wider" style={{ color: '#A78BFA' }}>
            Active Experiment
          </Text>
        </View>
        <Text className="text-xs text-[#526380]">
          Day {dayNumber} of {intervention.duration_days}
        </Text>
      </View>

      {/* Title */}
      <Text className="text-sm font-sansMedium text-[#E8EDF5] mb-2">{intervention.title}</Text>

      {/* Progress bar */}
      <View className="h-1.5 rounded-full mb-3" style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}>
        <View
          className="h-1.5 rounded-full"
          style={{ width: `${progressPct}%`, backgroundColor: '#A78BFA' }}
        />
      </View>

      {/* Stats row */}
      <View className="flex-row items-center gap-4 mb-3">
        <View className="flex-row items-center gap-1.5">
          <Text className="text-[10px] text-[#526380] uppercase tracking-wider">Adherence</Text>
          <Text className="text-xs font-sansMedium text-[#E8EDF5]">
            {intervention.adherence_pct != null ? `${Math.round(intervention.adherence_pct)}%` : '—'}
          </Text>
        </View>

        {km && km.delta_pct != null && (
          <View className="flex-row items-center gap-1.5">
            <Text className="text-[10px] text-[#526380] uppercase tracking-wider">{km.label}</Text>
            <Ionicons name={deltaIcon as never} size={12} color={deltaColor} />
            <Text className="text-xs font-sansMedium" style={{ color: deltaColor }}>
              {km.delta_pct > 0 ? '+' : ''}{km.delta_pct}%
            </Text>
            {sparkData.length >= 2 && <MiniSparkline points={sparkData} color={deltaColor} />}
          </View>
        )}
      </View>

      {/* Check-in */}
      {!checkedInToday ? (
        <View
          className="flex-row items-center justify-between rounded-xl p-3 mb-2"
          style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}
        >
          <Text className="text-xs text-[#8B97A8]">Follow through today?</Text>
          <View className="flex-row gap-2">
            <TouchableOpacity
              onPress={() => checkinMutation.mutate({ id: intervention.id, adhered: true })}
              disabled={checkinMutation.isPending}
              className="flex-row items-center gap-1 px-3 py-1.5 rounded-lg"
              style={{ backgroundColor: 'rgba(0,212,170,0.12)' }}
              activeOpacity={0.7}
            >
              <Ionicons name="checkmark" size={12} color="#00D4AA" />
              <Text className="text-xs font-sansMedium" style={{ color: '#00D4AA' }}>Yes</Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => checkinMutation.mutate({ id: intervention.id, adhered: false })}
              disabled={checkinMutation.isPending}
              className="flex-row items-center gap-1 px-3 py-1.5 rounded-lg"
              style={{ backgroundColor: 'rgba(248,113,113,0.12)' }}
              activeOpacity={0.7}
            >
              <Ionicons name="close" size={12} color="#F87171" />
              <Text className="text-xs font-sansMedium" style={{ color: '#F87171' }}>No</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : (
        <View
          className="flex-row items-center gap-2 rounded-xl p-3 mb-2"
          style={{ backgroundColor: 'rgba(0,212,170,0.06)', borderWidth: 1, borderColor: 'rgba(0,212,170,0.12)' }}
        >
          <Ionicons name="checkmark-circle" size={14} color="#00D4AA" />
          <Text className="text-xs" style={{ color: '#00D4AA' }}>Checked in for today</Text>
        </View>
      )}

      {/* Expand/collapse */}
      <TouchableOpacity
        onPress={() => setExpanded(!expanded)}
        className="flex-row items-center gap-1 mt-1"
      >
        <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={12} color="#526380" />
        <Text className="text-xs text-[#526380]">{expanded ? 'Less' : 'Details'}</Text>
      </TouchableOpacity>

      {expanded && (
        <View className="mt-3">
          {intervention.description && (
            <Text className="text-xs text-[#8B97A8] leading-5 mb-2">{intervention.description}</Text>
          )}

          {intervention.baseline_metrics && (
            <View className="mt-1">
              <Text className="text-[9px] font-bold uppercase tracking-wider text-[#526380] mb-1.5">
                Tracked Metrics vs Baseline
              </Text>
              {Object.entries(intervention.baseline_metrics)
                .filter(([, v]) => v != null)
                .slice(0, 6)
                .map(([metric, baseVal]) => {
                  const current = intervention.metric_trend
                    ?.filter((p) => p.metric === metric && p.value != null)
                    .slice(-1)[0]?.value;
                  const delta = baseVal && current ? (((current - baseVal) / Math.abs(baseVal)) * 100) : null;
                  const label = metric.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
                  return (
                    <View key={metric} className="flex-row items-center justify-between mb-1">
                      <Text className="text-xs text-[#526380] flex-1">{label}</Text>
                      <View className="flex-row items-center gap-2">
                        <Text className="text-[10px] text-[#3D4F66]">{baseVal != null ? Math.round(baseVal as number) : '—'}</Text>
                        <Text className="text-[10px] text-[#3D4F66]">→</Text>
                        <Text className="text-[10px] text-[#8B97A8]">{current != null ? Math.round(current) : '—'}</Text>
                        {delta != null && (
                          <Text
                            className="text-[10px] font-sansMedium"
                            style={{ color: delta > 1 ? '#00D4AA' : delta < -1 ? '#F87171' : '#526380' }}
                          >
                            {delta > 0 ? '+' : ''}{Math.round(delta)}%
                          </Text>
                        )}
                      </View>
                    </View>
                  );
                })}
            </View>
          )}

          <TouchableOpacity
            onPress={() => {
              Alert.alert(
                'Abandon Experiment',
                'Are you sure? Your progress will be lost.',
                [
                  { text: 'Cancel', style: 'cancel' },
                  { text: 'Abandon', style: 'destructive', onPress: () => abandonMutation.mutate(intervention.id) },
                ],
              );
            }}
            className="mt-3"
          >
            <Text className="text-xs" style={{ color: 'rgba(248,113,113,0.6)' }}>Abandon experiment</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}
