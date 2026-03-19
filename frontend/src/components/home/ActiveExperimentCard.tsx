'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Beaker, Check, X, TrendingUp, TrendingDown, Minus, ChevronDown, ChevronUp } from 'lucide-react';
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
  notes?: string;
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
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const h = 24;
  const w = 80;
  const step = w / (points.length - 1);
  const path = points
    .map((v, i) => {
      const x = i * step;
      const y = h - ((v - min) / range) * h;
      return `${i === 0 ? 'M' : 'L'}${x},${y}`;
    })
    .join(' ');

  return (
    <svg width={w} height={h} className="flex-shrink-0">
      <path d={path} fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function ActiveExperimentCard() {
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

  // Build sparkline data for the key metric
  const sparkData: number[] = [];
  if (km && intervention.metric_trend) {
    const metricPoints = intervention.metric_trend
      .filter((p) => p.metric === km.metric && p.value != null)
      .map((p) => p.value as number);
    sparkData.push(...metricPoints);
  }

  const deltaColor = km?.direction === 'up' ? '#00D4AA' : km?.direction === 'down' ? '#F87171' : '#526380';
  const DeltaIcon = km?.direction === 'up' ? TrendingUp : km?.direction === 'down' ? TrendingDown : Minus;

  return (
    <div
      className="rounded-xl p-5"
      style={{
        backgroundColor: 'rgba(167,139,250,0.04)',
        border: '1px solid rgba(167,139,250,0.15)',
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: 'rgba(167,139,250,0.12)' }}
          >
            <Beaker className="w-4 h-4 text-[#A78BFA]" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-[#A78BFA]">
              Active Experiment
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-[#526380]">
          <span>Day {dayNumber} of {intervention.duration_days}</span>
        </div>
      </div>

      {/* Title */}
      <h3 className="text-sm font-semibold text-[#E8EDF5] mb-2">{intervention.title}</h3>

      {/* Progress bar */}
      <div className="h-1.5 w-full rounded-full bg-white/5 mb-3 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${progressPct}%`, backgroundColor: '#A78BFA' }}
        />
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-4 mb-3">
        {/* Adherence */}
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-[#526380] uppercase tracking-wider">Adherence</span>
          <span className="text-xs font-medium text-[#E8EDF5]">
            {intervention.adherence_pct != null ? `${Math.round(intervention.adherence_pct)}%` : '—'}
          </span>
        </div>

        {/* Key metric delta */}
        {km && km.delta_pct != null && (
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[#526380] uppercase tracking-wider">{km.label}</span>
            <div className="flex items-center gap-1">
              <DeltaIcon className="w-3 h-3" style={{ color: deltaColor }} />
              <span className="text-xs font-medium" style={{ color: deltaColor }}>
                {km.delta_pct > 0 ? '+' : ''}{km.delta_pct}%
              </span>
            </div>
            {sparkData.length >= 2 && <MiniSparkline points={sparkData} color={deltaColor} />}
          </div>
        )}
      </div>

      {/* Check-in toggle */}
      {!checkedInToday ? (
        <div
          className="flex items-center justify-between rounded-lg p-3 mb-2"
          style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
        >
          <span className="text-xs text-[#8B97A8]">Did you follow through today?</span>
          <div className="flex gap-2">
            <button
              onClick={() => checkinMutation.mutate({ id: intervention.id, adhered: true })}
              disabled={checkinMutation.isPending}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
              style={{ backgroundColor: 'rgba(0,212,170,0.12)', color: '#00D4AA' }}
            >
              <Check className="w-3 h-3" /> Yes
            </button>
            <button
              onClick={() => checkinMutation.mutate({ id: intervention.id, adhered: false })}
              disabled={checkinMutation.isPending}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
              style={{ backgroundColor: 'rgba(248,113,113,0.12)', color: '#F87171' }}
            >
              <X className="w-3 h-3" /> No
            </button>
          </div>
        </div>
      ) : (
        <div
          className="flex items-center gap-2 rounded-lg p-3 mb-2"
          style={{ backgroundColor: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.12)' }}
        >
          <Check className="w-3.5 h-3.5 text-[#00D4AA]" />
          <span className="text-xs text-[#00D4AA]">Checked in for today</span>
        </div>
      )}

      {/* Expand/collapse for details */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-[#526380] hover:text-[#8B97A8] transition-colors mt-1"
      >
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {expanded ? 'Less' : 'Details'}
      </button>

      {expanded && (
        <div className="mt-3 space-y-2">
          {intervention.description && (
            <p className="text-xs text-[#8B97A8] leading-relaxed">{intervention.description}</p>
          )}

          {/* All tracked metrics vs baseline */}
          {intervention.baseline_metrics && (
            <div className="space-y-1.5 mt-2">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#526380]">
                Tracked Metrics vs Baseline
              </p>
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
                    <div key={metric} className="flex items-center justify-between text-xs">
                      <span className="text-[#526380]">{label}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-[#3D4F66]">{baseVal != null ? Math.round(baseVal as number) : '—'}</span>
                        <span className="text-[#3D4F66]">→</span>
                        <span className="text-[#8B97A8]">{current != null ? Math.round(current) : '—'}</span>
                        {delta != null && (
                          <span
                            className="text-[10px] font-medium"
                            style={{ color: delta > 1 ? '#00D4AA' : delta < -1 ? '#F87171' : '#526380' }}
                          >
                            {delta > 0 ? '+' : ''}{Math.round(delta)}%
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
            </div>
          )}

          {/* Abandon */}
          <button
            onClick={() => {
              if (confirm('Are you sure you want to abandon this experiment?')) {
                abandonMutation.mutate(intervention.id);
              }
            }}
            className="text-xs text-[#F87171]/60 hover:text-[#F87171] transition-colors mt-2"
          >
            Abandon experiment
          </button>
        </div>
      )}
    </div>
  );
}
