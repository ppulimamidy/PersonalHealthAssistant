'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Lightbulb, Beaker, X, ChevronRight } from 'lucide-react';
import { api } from '@/services/api';

interface FoodSuggestion {
  name: string;
  reason: string;
  category: string;
}

interface PersonalHistory {
  status: string;
  times_tried: number;
  avg_effect: number;
  confidence: number;
}

interface TopRecommendation {
  pattern: string;
  title: string;
  description: string;
  evidence: {
    signals: string[];
    severity: string;
    data_points: number;
  };
  suggested_duration: number;
  expected_improvement: string | null;
  foods: FoodSuggestion[];
  category: string;
  severity: string;
  personal_history: PersonalHistory | null;
  cycle_guidance: { phase: string; cycle_day: number | null; note: string | null } | null;
}

export function RecommendationCard() {
  const queryClient = useQueryClient();
  const [dismissed, setDismissed] = useState(false);

  const { data: rec, isLoading } = useQuery<TopRecommendation | null>({
    queryKey: ['top-recommendation'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/recommendations/top');
      return data || null;
    },
    staleTime: 5 * 60_000,
  });

  const startMutation = useMutation({
    mutationFn: async (rec: TopRecommendation) => {
      const { data } = await api.post('/api/v1/interventions/from-recommendation', {
        recommendation_pattern: rec.pattern,
        title: rec.title,
        description: rec.description,
        duration_days: rec.suggested_duration,
        evidence: rec.evidence,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['top-recommendation'] });
      queryClient.invalidateQueries({ queryKey: ['active-intervention'] });
    },
  });

  const dismissMutation = useMutation({
    mutationFn: async (pattern: string) => {
      await api.post(`/api/v1/recommendations/${pattern}/dismiss`, { reason: 'not_now' });
    },
    onSuccess: () => {
      setDismissed(true);
    },
  });

  if (isLoading || !rec || dismissed) return null;

  const severityColor =
    rec.severity === 'high' ? '#F87171' : rec.severity === 'moderate' ? '#F5A623' : '#6EE7B7';

  const ph = rec.personal_history;
  const historyBadge = ph?.status === 'proven'
    ? { label: `Worked for you (${ph.times_tried}x)`, color: '#00D4AA', bg: 'rgba(0,212,170,0.12)' }
    : ph?.status === 'inconclusive' && ph.times_tried > 0
    ? { label: `Tried ${ph.times_tried}x — worth retesting`, color: '#F5A623', bg: 'rgba(245,166,35,0.12)' }
    : !ph || ph.times_tried === 0
    ? { label: 'New — untested', color: '#60A5FA', bg: 'rgba(96,165,250,0.12)' }
    : null;

  return (
    <div
      className="rounded-xl p-5"
      style={{
        backgroundColor: 'rgba(0,212,170,0.04)',
        border: '1px solid rgba(0,212,170,0.15)',
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: 'rgba(0,212,170,0.12)' }}
          >
            <Lightbulb className="w-4 h-4 text-[#00D4AA]" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-[#00D4AA]">
              Suggested for You
            </p>
          </div>
        </div>
        <button
          onClick={() => dismissMutation.mutate(rec.pattern)}
          className="text-[#3D4F66] hover:text-[#526380] transition-colors p-1"
          aria-label="Dismiss"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Personal history badge */}
      {historyBadge && (
        <span
          className="inline-block text-[10px] font-medium px-2 py-0.5 rounded-full mb-2"
          style={{ backgroundColor: historyBadge.bg, color: historyBadge.color }}
        >
          {historyBadge.label}
        </span>
      )}

      {/* Title + description */}
      <h3 className="text-sm font-semibold text-[#E8EDF5] mb-1">{rec.title}</h3>
      <p className="text-xs text-[#8B97A8] leading-relaxed mb-3">{rec.description}</p>

      {/* Evidence */}
      <div
        className="rounded-lg p-3 mb-3"
        style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}
      >
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#526380] mb-1.5">
          Why this recommendation
        </p>
        <div className="space-y-1">
          {rec.evidence.signals.map((signal, i) => (
            <div key={i} className="flex items-center gap-2">
              <span
                className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: severityColor }}
              />
              <span className="text-xs text-[#8B97A8]">{signal}</span>
            </div>
          ))}
        </div>
        <p className="text-[10px] text-[#3D4F66] mt-2">
          Based on {rec.evidence.data_points} days of data
        </p>
      </div>

      {/* Expected improvement */}
      {rec.expected_improvement && (
        <p className="text-xs text-[#6EE7B7] mb-3 flex items-center gap-1.5">
          <Beaker className="w-3.5 h-3.5 flex-shrink-0" />
          {rec.expected_improvement}
        </p>
      )}

      {/* Top food suggestions */}
      {rec.foods.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {rec.foods.slice(0, 4).map((f) => (
            <span
              key={f.name}
              className="text-[10px] px-2 py-1 rounded-full text-[#8B97A8]"
              style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
              title={f.reason}
            >
              {f.name}
            </span>
          ))}
        </div>
      )}

      {/* Cycle guidance */}
      {rec.cycle_guidance?.note && (
        <p className="text-[10px] text-[#A78BFA] mb-3 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#A78BFA] flex-shrink-0" />
          {rec.cycle_guidance.note}
        </p>
      )}

      {/* CTAs */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => startMutation.mutate(rec)}
          disabled={startMutation.isPending}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all hover:opacity-90 disabled:opacity-50"
          style={{ backgroundColor: '#00D4AA', color: '#080B10' }}
        >
          {startMutation.isPending ? (
            'Starting...'
          ) : (
            <>
              Try This ({rec.suggested_duration} days)
              <ChevronRight className="w-3.5 h-3.5" />
            </>
          )}
        </button>
        <button
          onClick={() => dismissMutation.mutate(rec.pattern)}
          className="text-xs text-[#526380] hover:text-[#8B97A8] transition-colors"
        >
          Not now
        </button>
      </div>
    </div>
  );
}
