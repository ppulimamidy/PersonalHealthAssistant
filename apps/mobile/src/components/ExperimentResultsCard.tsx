import { useState } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

interface LatestResult {
  id: string;
  title: string;
  recommendation_pattern: string;
  duration_days: number;
  adherence_days: number;
  adherence_pct: number;
  baseline_metrics: Record<string, number | null>;
  outcome_metrics: Record<string, number | null>;
  outcome_delta: Record<string, number>;
  summary: string | null;
  completed_at: string | null;
  status: string;
}

const METRIC_LABELS: Record<string, string> = {
  sleep_score: 'Sleep Score',
  sleep_efficiency: 'Sleep Efficiency',
  deep_sleep_hours: 'Deep Sleep',
  hrv_balance: 'HRV Balance',
  resting_heart_rate: 'Resting HR',
  readiness_score: 'Readiness',
  recovery_index: 'Recovery',
  temperature_deviation: 'Temp Deviation',
  steps: 'Steps',
  activity_score: 'Activity',
};

const LOWER_IS_BETTER = new Set(['resting_heart_rate', 'temperature_deviation']);

function DeltaBar({ metric, delta }: { metric: string; delta: number }) {
  const isLowerBetter = LOWER_IS_BETTER.has(metric);
  const improved = isLowerBetter ? delta < -1 : delta > 1;
  const declined = isLowerBetter ? delta > 1 : delta < -1;
  const color = improved ? '#00D4AA' : declined ? '#F87171' : '#526380';
  const barPct = Math.min(Math.abs(delta) / 30 * 100, 100);
  const label = METRIC_LABELS[metric] || metric.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <View className="flex-row items-center gap-2 mb-2">
      <Text className="text-xs text-[#8B97A8] w-24" numberOfLines={1}>{label}</Text>
      <View className="flex-1 h-2 rounded-full" style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}>
        <View className="h-2 rounded-full" style={{ width: `${barPct}%`, backgroundColor: color }} />
      </View>
      <Text className="text-xs font-sansMedium w-12 text-right" style={{ color }}>
        {delta > 0 ? '+' : ''}{Math.round(delta)}%
      </Text>
    </View>
  );
}

export default function ExperimentResultsCard() {
  const queryClient = useQueryClient();
  const [dismissed, setDismissed] = useState(false);

  const { data: result, isLoading } = useQuery<LatestResult | null>({
    queryKey: ['latest-result'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/interventions/latest-result');
      return data || null;
    },
    staleTime: 60_000,
  });

  const keepMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/api/v1/interventions/${id}/keep-as-habit`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['latest-result'] });
      queryClient.invalidateQueries({ queryKey: ['top-recommendation'] });
    },
  });

  if (isLoading || !result || dismissed) return null;

  const sortedDeltas = Object.entries(result.outcome_delta)
    .filter(([, v]) => Math.abs(v) > 0.5)
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
    .slice(0, 5);

  const hasImprovements = sortedDeltas.some(([m, d]) => {
    const isLower = LOWER_IS_BETTER.has(m);
    return isLower ? d < -1 : d > 1;
  });

  return (
    <View
      className="rounded-2xl p-4 mb-4"
      style={{
        backgroundColor: hasImprovements ? 'rgba(0,212,170,0.04)' : 'rgba(255,255,255,0.03)',
        borderWidth: 1,
        borderColor: hasImprovements ? 'rgba(0,212,170,0.15)' : 'rgba(255,255,255,0.06)',
      }}
    >
      {/* Header */}
      <View className="flex-row items-center justify-between mb-3">
        <View className="flex-row items-center gap-2">
          <View
            className="w-7 h-7 rounded-lg items-center justify-center"
            style={{ backgroundColor: hasImprovements ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.06)' }}
          >
            <Ionicons
              name={hasImprovements ? 'trophy-outline' : 'checkmark-circle-outline'}
              size={14}
              color={hasImprovements ? '#00D4AA' : '#526380'}
            />
          </View>
          <Text
            className="text-[10px] font-bold uppercase tracking-wider"
            style={{ color: hasImprovements ? '#00D4AA' : '#8B97A8' }}
          >
            Experiment Complete!
          </Text>
        </View>
        <TouchableOpacity onPress={() => setDismissed(true)} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
          <Ionicons name="close" size={16} color="#3D4F66" />
        </TouchableOpacity>
      </View>

      {/* Title */}
      <Text className="text-sm font-sansMedium text-[#E8EDF5] mb-1">{result.title}</Text>
      <Text className="text-xs text-[#526380] mb-3">
        {result.duration_days} days · {Math.round(result.adherence_pct)}% adherence
      </Text>

      {/* Metric deltas */}
      {sortedDeltas.length > 0 && (
        <View className="mb-3">
          {sortedDeltas.map(([metric, delta]) => (
            <DeltaBar key={metric} metric={metric} delta={delta} />
          ))}
        </View>
      )}

      {/* AI Summary */}
      {result.summary && (
        <Text className="text-xs text-[#8B97A8] leading-5 mb-4" style={{ fontStyle: 'italic' }}>
          &ldquo;{result.summary}&rdquo;
        </Text>
      )}

      {/* CTAs */}
      <View className="flex-row items-center gap-3">
        <TouchableOpacity
          onPress={() => keepMutation.mutate(result.id)}
          disabled={keepMutation.isPending}
          className="flex-row items-center gap-1.5 px-4 py-2.5 rounded-xl"
          style={{ backgroundColor: '#00D4AA', opacity: keepMutation.isPending ? 0.6 : 1 }}
          activeOpacity={0.85}
        >
          {keepMutation.isPending ? (
            <ActivityIndicator size="small" color="#080B10" />
          ) : (
            <Text className="text-sm font-sansMedium" style={{ color: '#080B10' }}>Keep as Habit</Text>
          )}
        </TouchableOpacity>
        <TouchableOpacity onPress={() => setDismissed(true)}>
          <Text className="text-xs text-[#526380]">Dismiss</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
