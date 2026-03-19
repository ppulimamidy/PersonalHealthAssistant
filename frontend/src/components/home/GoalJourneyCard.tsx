'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { Target, ChevronRight } from 'lucide-react';
import { api } from '@/services/api';

interface JourneyOverview {
  id: string;
  title: string;
  condition: string | null;
  goal_type: string;
  specialist_agent_id: string | null;
  duration_type: string;
  target_metrics: string[];
  phases: Array<{ name: string; status: string; description?: string }>;
  current_phase: number;
  status: string;
  total_phases: number;
  progress_pct: number;
  current_phase_name: string | null;
  days_active: number;
}

const GOAL_LABELS: Record<string, string> = {
  condition_management: 'Condition Management',
  weight_loss: 'Weight Loss',
  weight_gain: 'Weight Gain',
  muscle_building: 'Muscle Building',
  sleep_optimization: 'Sleep Optimization',
  hormone_optimization: 'Hormone Optimization',
  gut_health: 'Gut Health',
  cardiac_rehab: 'Cardiac Rehab',
  mental_health: 'Mental Wellness',
  general_wellness: 'General Wellness',
};

export function GoalJourneyCard() {
  const { data: journey, isLoading } = useQuery<JourneyOverview | null>({
    queryKey: ['active-journey'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/journeys/active');
      return data || null;
    },
    staleTime: 60_000,
  });

  if (isLoading || !journey) return null;

  const completedPhases = journey.phases.filter((p) => p.status === 'completed').length;

  return (
    <div
      className="rounded-xl p-5"
      style={{
        backgroundColor: 'rgba(96,165,250,0.04)',
        border: '1px solid rgba(96,165,250,0.15)',
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: 'rgba(96,165,250,0.12)' }}
          >
            <Target className="w-4 h-4 text-[#60A5FA]" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-[#60A5FA]">
              {GOAL_LABELS[journey.goal_type] || 'Health Journey'}
            </p>
          </div>
        </div>
        <span className="text-[10px] text-[#526380]">{journey.days_active}d active</span>
      </div>

      {/* Title */}
      <h3 className="text-sm font-semibold text-[#E8EDF5] mb-1">{journey.title}</h3>
      <p className="text-xs text-[#526380] mb-3">
        Phase {journey.current_phase + 1} of {journey.total_phases}
        {journey.current_phase_name && ` · ${journey.current_phase_name}`}
      </p>

      {/* Phase stepper */}
      <div className="flex gap-1 mb-3">
        {journey.phases.map((phase, i) => {
          const color =
            phase.status === 'completed' ? '#00D4AA'
            : phase.status === 'active' ? '#60A5FA'
            : phase.status === 'skipped' ? '#3D4F66'
            : '#1E2A3B';
          return (
            <div
              key={i}
              className="flex-1 h-1.5 rounded-full transition-all"
              style={{ backgroundColor: color }}
              title={`${phase.name}: ${phase.status}`}
            />
          );
        })}
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-4 mb-3 text-xs">
        <div>
          <span className="text-[10px] text-[#526380] uppercase tracking-wider">Progress</span>
          <span className="ml-1.5 text-[#E8EDF5] font-medium">{Math.round(journey.progress_pct)}%</span>
        </div>
        <div>
          <span className="text-[10px] text-[#526380] uppercase tracking-wider">Phases</span>
          <span className="ml-1.5 text-[#E8EDF5] font-medium">{completedPhases}/{journey.total_phases}</span>
        </div>
      </div>

      {/* Current phase description */}
      {journey.phases[journey.current_phase]?.description && (
        <p className="text-xs text-[#8B97A8] leading-relaxed mb-3">
          {journey.phases[journey.current_phase].description}
        </p>
      )}

      {/* Details link */}
      <Link
        href={`/journey/${journey.id}`}
        className="inline-flex items-center gap-1 text-xs font-medium text-[#60A5FA] hover:text-[#93C5FD] transition-colors"
      >
        View Details <ChevronRight className="w-3 h-3" />
      </Link>
    </div>
  );
}
