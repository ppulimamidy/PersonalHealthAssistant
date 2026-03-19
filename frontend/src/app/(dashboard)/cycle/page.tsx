'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Calendar, Droplets, Sun, Activity } from 'lucide-react';
import { api } from '@/services/api';
import { format, subDays } from 'date-fns';

interface CycleInfo {
  current_phase: { phase: string; cycle_day: number | null; days_until_next_period: number | null; confidence: string };
  avg_cycle_length: number | null;
  last_period_start: string | null;
  cycles_tracked: number;
  is_regular: boolean | null;
}

interface CycleHistory {
  cycles: Array<{ cycle_number: number; start_date: string; end_date: string | null; length_days: number | null; ovulation_date: string | null }>;
  avg_length: number | null;
  shortest: number | null;
  longest: number | null;
  is_regular: boolean | null;
}

const PHASE_COLORS: Record<string, string> = {
  menstrual: '#F87171', follicular: '#6EE7B7', ovulation: '#F5A623', luteal: '#A78BFA', unknown: '#526380',
};
const PHASE_LABELS: Record<string, string> = {
  menstrual: 'Menstrual', follicular: 'Follicular', ovulation: 'Ovulation', luteal: 'Luteal', unknown: 'Unknown',
};
const SYMPTOM_OPTIONS = [
  'cramps', 'bloating', 'headache', 'fatigue', 'mood_changes',
  'breast_tenderness', 'acne', 'back_pain', 'nausea', 'hot_flashes',
];

export default function CyclePage() {
  const queryClient = useQueryClient();
  const [selectedDate, setSelectedDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [symptoms, setSymptoms] = useState<string[]>([]);

  const { data: cycleInfo } = useQuery<CycleInfo>({
    queryKey: ['cycle', 'current'],
    queryFn: async () => { const { data } = await api.get('/api/v1/cycle/current'); return data; },
  });

  const { data: history } = useQuery<CycleHistory>({
    queryKey: ['cycle', 'history'],
    queryFn: async () => { const { data } = await api.get('/api/v1/cycle/history'); return data; },
  });

  const logEvent = useMutation({
    mutationFn: async (params: { event_type: string; flow_intensity?: string }) => {
      await api.post('/api/v1/cycle/log', {
        event_type: params.event_type,
        event_date: selectedDate,
        flow_intensity: params.flow_intensity,
        symptoms: params.event_type === 'symptom' ? symptoms : [],
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cycle'] });
      setSymptoms([]);
    },
  });

  const phase = cycleInfo?.current_phase;
  const phaseColor = PHASE_COLORS[phase?.phase ?? 'unknown'];
  const dates = Array.from({ length: 7 }, (_, i) => format(subDays(new Date(), i), 'yyyy-MM-dd'));

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[#E8EDF5]">Cycle Tracking</h1>
        <p className="text-sm text-[#526380] mt-1">Log your cycle for phase-aware experiments</p>
      </div>

      {/* Current phase */}
      {phase && phase.phase !== 'unknown' && (
        <div className="rounded-xl p-4" style={{ backgroundColor: `${phaseColor}08`, border: `1px solid ${phaseColor}25` }}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: phaseColor }}>
              {PHASE_LABELS[phase.phase]} Phase
            </span>
            <span className="text-[10px]" style={{ color: phaseColor }}>{phase.confidence} confidence</span>
          </div>
          {phase.cycle_day && <p className="text-xl font-bold text-[#E8EDF5]">Day {phase.cycle_day}</p>}
          <div className="flex gap-4 mt-2 text-xs text-[#526380]">
            {cycleInfo?.avg_cycle_length && <span>Avg cycle: {cycleInfo.avg_cycle_length}d</span>}
            {phase.days_until_next_period != null && <span>~{phase.days_until_next_period}d until next period</span>}
            <span>{cycleInfo?.cycles_tracked ?? 0} cycles tracked</span>
          </div>
        </div>
      )}

      {/* Date selector */}
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#526380] mb-2">Date</p>
        <div className="flex gap-2">
          {dates.map((d) => {
            const isSelected = d === selectedDate;
            return (
              <button
                key={d}
                onClick={() => setSelectedDate(d)}
                className="flex flex-col items-center px-3 py-2 rounded-xl transition-all"
                style={{
                  backgroundColor: isSelected ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${isSelected ? 'rgba(0,212,170,0.3)' : 'rgba(255,255,255,0.06)'}`,
                }}
              >
                <span className="text-[10px]" style={{ color: isSelected ? '#00D4AA' : '#526380' }}>
                  {format(new Date(d + 'T12:00:00'), 'EEE')}
                </span>
                <span className="text-sm font-medium" style={{ color: isSelected ? '#00D4AA' : '#E8EDF5' }}>
                  {format(new Date(d + 'T12:00:00'), 'd')}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Quick log buttons */}
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#526380] mb-2">Log Event</p>
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => logEvent.mutate({ event_type: 'period_start', flow_intensity: 'medium' })}
            className="flex flex-col items-center gap-1.5 p-4 rounded-xl transition-all hover:scale-[1.02]"
            style={{ backgroundColor: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.2)' }}
          >
            <Droplets className="w-5 h-5 text-red-400" />
            <span className="text-xs font-medium text-red-400">Period Start</span>
          </button>
          <button
            onClick={() => logEvent.mutate({ event_type: 'period_end' })}
            className="flex flex-col items-center gap-1.5 p-4 rounded-xl transition-all hover:scale-[1.02]"
            style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
          >
            <Activity className="w-5 h-5 text-[#8B97A8]" />
            <span className="text-xs font-medium text-[#8B97A8]">Period End</span>
          </button>
          <button
            onClick={() => logEvent.mutate({ event_type: 'ovulation' })}
            className="flex flex-col items-center gap-1.5 p-4 rounded-xl transition-all hover:scale-[1.02]"
            style={{ backgroundColor: 'rgba(245,166,35,0.08)', border: '1px solid rgba(245,166,35,0.2)' }}
          >
            <Sun className="w-5 h-5 text-amber-400" />
            <span className="text-xs font-medium text-amber-400">Ovulation</span>
          </button>
        </div>
      </div>

      {/* Symptoms */}
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#526380] mb-2">Symptoms</p>
        <div className="flex flex-wrap gap-2">
          {SYMPTOM_OPTIONS.map((s) => {
            const sel = symptoms.includes(s);
            return (
              <button
                key={s}
                onClick={() => setSymptoms(sel ? symptoms.filter((x) => x !== s) : [...symptoms, s])}
                className="px-3 py-1.5 rounded-full text-xs transition-all"
                style={{
                  backgroundColor: sel ? 'rgba(167,139,250,0.12)' : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${sel ? 'rgba(167,139,250,0.3)' : 'rgba(255,255,255,0.06)'}`,
                  color: sel ? '#A78BFA' : '#8B97A8',
                }}
              >
                {s.replace(/_/g, ' ')}
              </button>
            );
          })}
        </div>
        {symptoms.length > 0 && (
          <button
            onClick={() => logEvent.mutate({ event_type: 'symptom' })}
            className="mt-3 px-4 py-2 rounded-lg text-sm font-medium"
            style={{ backgroundColor: '#A78BFA', color: '#080B10' }}
          >
            Log {symptoms.length} Symptom{symptoms.length > 1 ? 's' : ''}
          </button>
        )}
      </div>

      {/* Cycle history */}
      {history && history.cycles.length > 0 && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#526380] mb-2">Cycle History</p>
          <div className="space-y-2">
            {history.cycles.map((c) => (
              <div
                key={c.cycle_number}
                className="flex items-center justify-between rounded-xl p-3"
                style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
              >
                <div>
                  <p className="text-xs font-medium text-[#E8EDF5]">
                    {format(new Date(c.start_date + 'T12:00:00'), 'MMM d')}
                    {c.end_date ? ` — ${format(new Date(c.end_date + 'T12:00:00'), 'MMM d')}` : ''}
                  </p>
                  {c.ovulation_date && (
                    <p className="text-[10px] text-[#F5A623] mt-0.5">
                      Ovulation: {format(new Date(c.ovulation_date + 'T12:00:00'), 'MMM d')}
                    </p>
                  )}
                </div>
                <span className="text-xs font-medium text-[#526380]">
                  {c.length_days ? `${c.length_days}d` : '—'}
                </span>
              </div>
            ))}
          </div>
          {history.avg_length && (
            <p className="text-[10px] text-[#3D4F66] mt-2">
              Average: {history.avg_length}d · Range: {history.shortest}–{history.longest}d
              {history.is_regular != null && (history.is_regular ? ' · Regular' : ' · Irregular')}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
