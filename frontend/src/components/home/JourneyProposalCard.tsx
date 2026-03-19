'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Flag, Play } from 'lucide-react';
import { api } from '@/services/api';

interface JourneyProposalData {
  journey_key: string;
  specialist: { agent_type: string; agent_name: string; specialty: string };
  journey: { title: string; phases: Array<{ name: string }>; total_phases: number };
}

export function JourneyProposalCard() {
  const queryClient = useQueryClient();

  const { data: proposal } = useQuery<JourneyProposalData | null>({
    queryKey: ['journey-proposal'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/onboarding/journey-proposal');
      return data || null;
    },
    staleTime: 60_000,
  });

  const startMutation = useMutation({
    mutationFn: async () => {
      await api.post('/api/v1/onboarding/start-journey', {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journey-proposal'] });
      queryClient.invalidateQueries({ queryKey: ['active-journey'] });
      queryClient.invalidateQueries({ queryKey: ['active-intervention'] });
    },
  });

  if (!proposal) return null;

  return (
    <div
      className="rounded-xl p-5"
      style={{ backgroundColor: 'rgba(96,165,250,0.04)', border: '1px solid rgba(96,165,250,0.15)' }}
    >
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(96,165,250,0.12)' }}>
          <Flag className="w-4 h-4 text-[#60A5FA]" />
        </div>
        <span className="text-xs font-semibold uppercase tracking-wider text-[#60A5FA]">Journey Ready</span>
      </div>

      <h3 className="text-sm font-semibold text-[#E8EDF5] mb-1">
        Your {proposal.specialist.agent_name} has a plan
      </h3>

      <div
        className="rounded-lg p-3 mb-4"
        style={{ backgroundColor: 'rgba(96,165,250,0.04)', border: '1px solid rgba(96,165,250,0.08)' }}
      >
        <p className="text-xs font-semibold text-[#60A5FA] mb-2">{proposal.journey.title}</p>
        {proposal.journey.phases.map((phase, i) => (
          <div key={i} className="flex items-center gap-2 mb-1">
            <div className="w-4 h-4 rounded-full flex items-center justify-center" style={{ backgroundColor: 'rgba(96,165,250,0.1)' }}>
              <span className="text-[8px] font-bold text-[#60A5FA]">{i + 1}</span>
            </div>
            <span className="text-xs text-[#8B97A8]">{phase.name}</span>
          </div>
        ))}
      </div>

      <button
        onClick={() => startMutation.mutate()}
        disabled={startMutation.isPending}
        className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all hover:opacity-90 disabled:opacity-50"
        style={{ backgroundColor: '#60A5FA', color: '#080B10' }}
      >
        {startMutation.isPending ? 'Starting...' : (
          <>
            <Play className="w-3.5 h-3.5" /> Start My Journey
          </>
        )}
      </button>
    </div>
  );
}
