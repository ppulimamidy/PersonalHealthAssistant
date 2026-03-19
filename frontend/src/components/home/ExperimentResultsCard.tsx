'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, Trophy, X } from 'lucide-react';
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

// Lower is better for these
const LOWER_IS_BETTER = new Set(['resting_heart_rate', 'temperature_deviation']);

function DeltaBar({ metric, delta }: { metric: string; delta: number }) {
  const isLowerBetter = LOWER_IS_BETTER.has(metric);
  const improved = isLowerBetter ? delta < -1 : delta > 1;
  const declined = isLowerBetter ? delta > 1 : delta < -1;
  const color = improved ? '#00D4AA' : declined ? '#F87171' : '#526380';
  const barWidth = Math.min(Math.abs(delta), 30);
  const label = METRIC_LABELS[metric] || metric.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-[#8B97A8] w-28 flex-shrink-0 truncate">{label}</span>
      <div className="flex-1 flex items-center gap-2">
        <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${(barWidth / 30) * 100}%`, backgroundColor: color }}
          />
        </div>
        <span className="text-xs font-medium w-12 text-right" style={{ color }}>
          {delta > 0 ? '+' : ''}{Math.round(delta)}%
        </span>
      </div>
    </div>
  );
}

export function ExperimentResultsCard() {
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

  // Sort deltas by absolute value descending, take top 5
  const sortedDeltas = Object.entries(result.outcome_delta)
    .filter(([, v]) => Math.abs(v) > 0.5)
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
    .slice(0, 5);

  const hasImprovements = sortedDeltas.some(([m, d]) => {
    const isLower = LOWER_IS_BETTER.has(m);
    return isLower ? d < -1 : d > 1;
  });

  return (
    <div
      className="rounded-xl p-5"
      style={{
        backgroundColor: hasImprovements ? 'rgba(0,212,170,0.04)' : 'rgba(255,255,255,0.03)',
        border: `1px solid ${hasImprovements ? 'rgba(0,212,170,0.15)' : 'rgba(255,255,255,0.06)'}`,
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: hasImprovements ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.06)' }}
          >
            {hasImprovements
              ? <Trophy className="w-4 h-4 text-[#00D4AA]" />
              : <CheckCircle2 className="w-4 h-4 text-[#526380]" />
            }
          </div>
          <div>
            <p
              className="text-xs font-semibold uppercase tracking-wider"
              style={{ color: hasImprovements ? '#00D4AA' : '#8B97A8' }}
            >
              Experiment Complete!
            </p>
          </div>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="text-[#3D4F66] hover:text-[#526380] transition-colors p-1"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Title + duration */}
      <h3 className="text-sm font-semibold text-[#E8EDF5] mb-1">{result.title}</h3>
      <p className="text-xs text-[#526380] mb-3">
        {result.duration_days} days · {Math.round(result.adherence_pct)}% adherence
      </p>

      {/* Metric deltas */}
      {sortedDeltas.length > 0 && (
        <div className="space-y-2 mb-4">
          {sortedDeltas.map(([metric, delta]) => (
            <DeltaBar key={metric} metric={metric} delta={delta} />
          ))}
        </div>
      )}

      {/* AI Summary */}
      {result.summary && (
        <p className="text-xs text-[#8B97A8] leading-relaxed mb-4 italic">
          &ldquo;{result.summary}&rdquo;
        </p>
      )}

      {/* CTAs */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => keepMutation.mutate(result.id)}
          disabled={keepMutation.isPending}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all hover:opacity-90 disabled:opacity-50"
          style={{ backgroundColor: '#00D4AA', color: '#080B10' }}
        >
          {keepMutation.isPending ? 'Saving...' : 'Keep as Habit'}
        </button>
        <button
          onClick={() => setDismissed(true)}
          className="text-xs text-[#526380] hover:text-[#8B97A8] transition-colors"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
