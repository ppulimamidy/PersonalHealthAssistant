'use client';

import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { CheckCircle2, Circle, SkipForward, Target, Pause, Play, XCircle, FlaskConical } from 'lucide-react';
import { api } from '@/services/api';
import { format } from 'date-fns';

interface Phase {
  name: string;
  description: string;
  phase_type: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  outcome_summary: string | null;
  checkpoints: Array<{ action?: string; type?: string; data?: Record<string, unknown>; recorded_at?: string }>;
  tracked_metrics: string[];
}

interface JourneyDetail {
  id: string;
  title: string;
  condition: string | null;
  goal_type: string;
  specialist_agent_id: string | null;
  duration_type: string;
  target_metrics: string[];
  phases: Phase[];
  current_phase: number;
  status: string;
  baseline_snapshot: Record<string, number | null> | null;
  outcome_snapshot: Record<string, number | null> | null;
  started_at: string;
  completed_at: string | null;
  total_phases: number;
  progress_pct: number;
  current_phase_name: string | null;
  days_active: number;
}

const STATUS_ICONS: Record<string, typeof CheckCircle2> = {
  completed: CheckCircle2,
  active: FlaskConical,
  skipped: SkipForward,
  pending: Circle,
};

const STATUS_COLORS: Record<string, string> = {
  completed: '#00D4AA',
  active: '#60A5FA',
  skipped: '#3D4F66',
  pending: '#1E2A3B',
};

export default function JourneyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const { data: journey, isLoading } = useQuery<JourneyDetail>({
    queryKey: ['journey', id],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/journeys/${id}`);
      return data;
    },
  });

  const advanceMutation = useMutation({
    mutationFn: async (skip: boolean) => {
      await api.post(`/api/v1/journeys/${id}/advance`, { skip });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journey', id] });
      queryClient.invalidateQueries({ queryKey: ['active-journey'] });
    },
  });

  const pauseMutation = useMutation({
    mutationFn: async () => { await api.patch(`/api/v1/journeys/${id}/pause`); },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journey', id] });
      queryClient.invalidateQueries({ queryKey: ['active-journey'] });
    },
  });

  const resumeMutation = useMutation({
    mutationFn: async () => { await api.patch(`/api/v1/journeys/${id}/resume`); },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journey', id] });
      queryClient.invalidateQueries({ queryKey: ['active-journey'] });
    },
  });

  const abandonMutation = useMutation({
    mutationFn: async () => { await api.patch(`/api/v1/journeys/${id}/abandon`); },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journey', id] });
      queryClient.invalidateQueries({ queryKey: ['active-journey'] });
    },
  });

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto space-y-4">
        {[1, 2, 3].map((i) => <div key={i} className="h-24 bg-white/5 rounded-xl animate-pulse" />)}
      </div>
    );
  }

  if (!journey) {
    return <div className="text-center text-[#526380] mt-20">Journey not found</div>;
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Target className="w-5 h-5 text-[#60A5FA]" />
          <h1 className="text-xl font-bold text-[#E8EDF5]">{journey.title}</h1>
        </div>
        <p className="text-sm text-[#526380]">
          {journey.days_active} days active · {Math.round(journey.progress_pct)}% complete
          {journey.status !== 'active' && (
            <span className="ml-2 text-xs uppercase font-medium" style={{ color: journey.status === 'completed' ? '#00D4AA' : '#F87171' }}>
              {journey.status}
            </span>
          )}
        </p>
      </div>

      {/* Phase stepper */}
      <div className="space-y-3">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#526380]">Phases</p>
        {journey.phases.map((phase, i) => {
          const Icon = STATUS_ICONS[phase.status] || Circle;
          const color = STATUS_COLORS[phase.status] || '#1E2A3B';
          const isCurrent = i === journey.current_phase && journey.status === 'active';

          return (
            <div
              key={i}
              className="rounded-xl p-4"
              style={{
                backgroundColor: isCurrent ? 'rgba(96,165,250,0.04)' : 'rgba(255,255,255,0.03)',
                border: `1px solid ${isCurrent ? 'rgba(96,165,250,0.15)' : 'rgba(255,255,255,0.06)'}`,
              }}
            >
              <div className="flex items-start gap-3">
                <Icon className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color }} />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-[#E8EDF5]">{phase.name}</span>
                    {isCurrent && (
                      <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-full bg-[#60A5FA]/15 text-[#60A5FA]">
                        Current
                      </span>
                    )}
                    <span className="text-[9px] uppercase text-[#3D4F66]">{phase.phase_type}</span>
                  </div>
                  {phase.description && (
                    <p className="text-xs text-[#8B97A8] mt-1 leading-relaxed">{phase.description}</p>
                  )}
                  {phase.started_at && (
                    <p className="text-[10px] text-[#3D4F66] mt-1">
                      Started {format(new Date(phase.started_at), 'MMM d, yyyy')}
                      {phase.completed_at && ` · Completed ${format(new Date(phase.completed_at), 'MMM d')}`}
                    </p>
                  )}
                  {phase.outcome_summary && (
                    <p className="text-xs text-[#6EE7B7] mt-1 italic">{phase.outcome_summary}</p>
                  )}
                  {/* Checkpoints with recorded data */}
                  {phase.checkpoints.filter((c) => c.recorded_at).map((c, ci) => (
                    <div key={ci} className="mt-1 text-[10px] text-[#F5A623]">
                      Lab recorded: {c.recorded_at ? format(new Date(c.recorded_at), 'MMM d') : ''}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Actions */}
      {journey.status === 'active' && (
        <div className="flex items-center gap-3">
          <button
            onClick={() => advanceMutation.mutate(false)}
            disabled={advanceMutation.isPending}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all hover:opacity-90"
            style={{ backgroundColor: '#60A5FA', color: '#080B10' }}
          >
            {advanceMutation.isPending ? 'Advancing...' : 'Complete Phase & Advance'}
          </button>
          <button
            onClick={() => advanceMutation.mutate(true)}
            className="text-xs text-[#526380] hover:text-[#8B97A8] transition-colors"
          >
            Skip Phase
          </button>
          <button
            onClick={() => pauseMutation.mutate()}
            className="flex items-center gap-1 text-xs text-[#526380] hover:text-[#F5A623] transition-colors ml-auto"
          >
            <Pause className="w-3 h-3" /> Pause
          </button>
          <button
            onClick={() => { if (confirm('Abandon this journey?')) abandonMutation.mutate(); }}
            className="flex items-center gap-1 text-xs text-[#526380] hover:text-[#F87171] transition-colors"
          >
            <XCircle className="w-3 h-3" /> Abandon
          </button>
        </div>
      )}

      {journey.status === 'paused' && (
        <div className="flex items-center gap-3">
          <button
            onClick={() => resumeMutation.mutate()}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium"
            style={{ backgroundColor: '#00D4AA', color: '#080B10' }}
          >
            <Play className="w-3.5 h-3.5" /> Resume Journey
          </button>
          <button
            onClick={() => { if (confirm('Abandon this journey?')) abandonMutation.mutate(); }}
            className="text-xs text-[#526380] hover:text-[#F87171] transition-colors"
          >
            Abandon
          </button>
        </div>
      )}

      {/* Baseline vs outcome (if completed) */}
      {journey.status === 'completed' && journey.baseline_snapshot && journey.outcome_snapshot && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#526380] mb-2">
            Journey Outcome (Baseline → Final)
          </p>
          <div className="space-y-1.5">
            {Object.entries(journey.baseline_snapshot)
              .filter(([, v]) => v != null)
              .slice(0, 8)
              .map(([metric, baseVal]) => {
                const outVal = journey.outcome_snapshot?.[metric];
                const delta = baseVal && outVal ? (((outVal - baseVal) / Math.abs(baseVal)) * 100) : null;
                const label = metric.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
                return (
                  <div key={metric} className="flex items-center justify-between text-xs">
                    <span className="text-[#526380]">{label}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-[#3D4F66]">{Math.round(baseVal as number)}</span>
                      <span className="text-[#3D4F66]">→</span>
                      <span className="text-[#8B97A8]">{outVal != null ? Math.round(outVal) : '—'}</span>
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
        </div>
      )}
    </div>
  );
}
