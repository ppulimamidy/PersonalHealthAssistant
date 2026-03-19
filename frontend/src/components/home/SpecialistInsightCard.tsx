'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { Stethoscope, MessageCircle } from 'lucide-react';
import { api } from '@/services/api';

interface JourneyOverview {
  id: string;
  specialist_agent_id: string | null;
  current_phase: number;
  phases: Array<{ name: string; checkpoints?: Array<{ action: string }> }>;
}

const SPECIALIST_NAMES: Record<string, string> = {
  endocrinologist: 'Endocrinologist',
  diabetologist: 'Diabetologist',
  metabolic_coach: 'Metabolic Coach',
  cardiologist: 'Cardiologist',
  gi_specialist: 'GI Specialist',
  womens_health: "Women's Health",
  sleep_specialist: 'Sleep Specialist',
  exercise_physiologist: 'Exercise Physiologist',
  behavioral_health: 'Behavioral Health',
  rheumatologist: 'Rheumatologist',
  pulmonologist: 'Pulmonologist',
  neurologist: 'Neurologist',
  oncology_support: 'Oncology Support',
  health_coach: 'Health Coach',
};

export function SpecialistInsightCard() {
  const { data: journey } = useQuery<JourneyOverview | null>({
    queryKey: ['active-journey'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/journeys/active');
      return data || null;
    },
    staleTime: 60_000,
  });

  if (!journey?.specialist_agent_id) return null;

  const specialistName = SPECIALIST_NAMES[journey.specialist_agent_id] || 'Specialist';
  const currentPhase = journey.phases[journey.current_phase];
  const nextCheckpoint = currentPhase?.checkpoints?.[0];

  return (
    <div
      className="rounded-xl p-4"
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      <div className="flex items-start gap-3">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: 'rgba(0,212,170,0.08)' }}
        >
          <Stethoscope className="w-4 h-4 text-[#00D4AA]" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-[#00D4AA]">Your {specialistName}</p>
          {nextCheckpoint ? (
            <p className="text-xs text-[#8B97A8] mt-1 leading-relaxed">
              Upcoming: {nextCheckpoint.action}
            </p>
          ) : (
            <p className="text-xs text-[#8B97A8] mt-1">
              Monitoring your {currentPhase?.name || 'current phase'} progress.
            </p>
          )}
        </div>
        <Link
          href="/agents"
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-[#00D4AA] transition-colors hover:bg-[#00D4AA]/10"
          style={{ border: '1px solid rgba(0,212,170,0.2)' }}
        >
          <MessageCircle className="w-3 h-3" /> Chat
        </Link>
      </div>
    </div>
  );
}
