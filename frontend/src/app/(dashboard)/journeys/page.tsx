'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { Target, CheckCircle2, XCircle, Pause } from 'lucide-react';
import { api } from '@/services/api';
import { format } from 'date-fns';

interface JourneyOverview {
  id: string;
  title: string;
  goal_type: string;
  status: string;
  total_phases: number;
  progress_pct: number;
  days_active: number;
  started_at: string;
  completed_at: string | null;
}

const STATUS_CONFIG: Record<string, { icon: typeof CheckCircle2; color: string; label: string }> = {
  active: { icon: Target, color: '#60A5FA', label: 'Active' },
  completed: { icon: CheckCircle2, color: '#00D4AA', label: 'Completed' },
  paused: { icon: Pause, color: '#F5A623', label: 'Paused' },
  abandoned: { icon: XCircle, color: '#F87171', label: 'Abandoned' },
};

export default function JourneysPage() {
  const { data: journeys, isLoading } = useQuery<JourneyOverview[]>({
    queryKey: ['journeys'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/journeys');
      return data;
    },
  });

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[#E8EDF5]">My Journeys</h1>
        <p className="text-sm text-[#526380] mt-1">Your health improvement programs</p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2].map((i) => <div key={i} className="h-24 bg-white/5 rounded-xl animate-pulse" />)}
        </div>
      ) : !journeys?.length ? (
        <div
          className="rounded-xl p-8 text-center"
          style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
        >
          <Target className="w-10 h-10 text-[#526380] mx-auto mb-3" />
          <p className="text-sm text-[#E8EDF5] font-medium">No journeys yet</p>
          <p className="text-xs text-[#526380] mt-1">Start a health journey from your specialist agent or the Ask AI tab.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {journeys.map((j) => {
            const cfg = STATUS_CONFIG[j.status] || STATUS_CONFIG.active;
            const Icon = cfg.icon;
            return (
              <Link
                key={j.id}
                href={`/journey/${j.id}`}
                className="block rounded-xl p-4 transition-all hover:scale-[1.01]"
                style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-5 h-5 flex-shrink-0" style={{ color: cfg.color }} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-[#E8EDF5] truncate">{j.title}</span>
                      <span
                        className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: `${cfg.color}15`, color: cfg.color }}
                      >
                        {cfg.label}
                      </span>
                    </div>
                    <p className="text-xs text-[#526380] mt-0.5">
                      {j.total_phases} phases · {j.days_active}d · {Math.round(j.progress_pct)}% complete
                      {j.started_at && ` · Started ${format(new Date(j.started_at), 'MMM d')}`}
                    </p>
                  </div>
                </div>
                {/* Progress bar */}
                <div className="h-1 rounded-full bg-white/5 mt-3 overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${j.progress_pct}%`, backgroundColor: cfg.color }} />
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
