'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Heart, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { checkinsService } from '@/services/checkins';
import { useAuthStore } from '@/stores/authStore';

const SNOOZE_KEY = 'weekly-checkin-snoozed';

function snoozed(): boolean {
  try {
    const val = sessionStorage.getItem(SNOOZE_KEY);
    if (!val) return false;
    // snoozed stores the ISO date of the snooze — clear after 24h
    return (Date.now() - new Date(val).getTime()) < 24 * 60 * 60 * 1000;
  } catch { return false; }
}

function snooze() {
  try { sessionStorage.setItem(SNOOZE_KEY, new Date().toISOString()); } catch { /* ignore */ }
}

// ── Slider ────────────────────────────────────────────────────────────────────

interface SliderProps {
  label: string;
  value: number;
  onChange: (v: number) => void;
  lowLabel: string;
  highLabel: string;
  trackColor: string;
}

function Slider({ label, value, onChange, lowLabel, highLabel, trackColor }: SliderProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-[#8B97A8]">{label}</span>
        <span
          className="text-lg font-bold tabular-nums"
          style={{ color: trackColor }}
        >
          {value}
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={10}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
        style={{
          background: `linear-gradient(to right, ${trackColor} ${value * 10}%, rgba(255,255,255,0.08) ${value * 10}%)`,
          accentColor: trackColor,
        }}
      />
      <div className="flex justify-between mt-1">
        <span className="text-[10px] text-[#3D4F66]">{lowLabel}</span>
        <span className="text-[10px] text-[#3D4F66]">{highLabel}</span>
      </div>
    </div>
  );
}

// ── Modal ─────────────────────────────────────────────────────────────────────

export function WeeklyCheckinModal() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [energy, setEnergy] = useState(7);
  const [mood, setMood] = useState(7);
  const [pain, setPain] = useState(2);
  const [notes, setNotes] = useState('');

  const { data: status } = useQuery({
    queryKey: ['checkin-status'],
    queryFn: checkinsService.getStatus,
    staleTime: 5 * 60_000,
    enabled: !!user,
  });

  useEffect(() => {
    if (status?.should_prompt && !snoozed()) {
      // Slight delay so the page finishes loading first
      const t = setTimeout(() => setOpen(true), 3000);
      return () => clearTimeout(t);
    }
  }, [status]);

  const submitMutation = useMutation({
    mutationFn: () => checkinsService.createCheckin({ energy, mood, pain, notes: notes.trim() || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['checkin-status'] });
      toast.success('Check-in saved — thanks for the update!');
      setOpen(false);
    },
    onError: () => toast.error('Could not save check-in'),
  });

  const handleDismiss = () => {
    snooze();
    setOpen(false);
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4"
      onClick={handleDismiss}
    >
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-sm rounded-2xl p-6 shadow-2xl"
        style={{
          backgroundColor: '#0D1117',
          border: '1px solid rgba(255,255,255,0.10)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-pink-500/15 flex items-center justify-center">
              <Heart className="w-4 h-4 text-pink-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-[#E8EDF5]">Weekly Check-in</h2>
              <p className="text-[10px] text-[#526380]">
                {status?.days_since_last != null
                  ? `Last check-in ${status.days_since_last} days ago`
                  : 'How are you feeling?'}
              </p>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            className="text-[#526380] hover:text-[#8B97A8] transition-colors"
            aria-label="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="text-xs text-[#526380] mb-5 mt-1">
          Rate your energy, mood, and pain on a scale of 0–10. Takes 15 seconds.
        </p>

        <div className="space-y-5">
          <Slider
            label="Energy"
            value={energy}
            onChange={setEnergy}
            lowLabel="Exhausted"
            highLabel="Full energy"
            trackColor="#00D4AA"
          />
          <Slider
            label="Mood"
            value={mood}
            onChange={setMood}
            lowLabel="Very low"
            highLabel="Excellent"
            trackColor="#818CF8"
          />
          <Slider
            label="Pain / Discomfort"
            value={pain}
            onChange={setPain}
            lowLabel="None"
            highLabel="Severe"
            trackColor="#F87171"
          />
        </div>

        {/* Optional notes */}
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Anything notable? (optional)"
          rows={2}
          className="mt-4 w-full rounded-lg px-3 py-2 text-xs text-[#C8D5E8] placeholder-[#3D4F66] outline-none resize-none"
          style={{
            backgroundColor: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.07)',
          }}
        />

        {/* Actions */}
        <div className="flex gap-3 mt-4">
          <button
            onClick={handleDismiss}
            className="flex-1 py-2.5 rounded-lg text-xs font-medium text-[#526380] hover:text-[#8B97A8] transition-colors"
            style={{ backgroundColor: 'rgba(255,255,255,0.04)' }}
          >
            Remind me later
          </button>
          <button
            onClick={() => submitMutation.mutate()}
            disabled={submitMutation.isPending}
            className="flex-1 py-2.5 rounded-lg text-xs font-semibold text-[#080B10] bg-[#00D4AA] hover:bg-[#00BF99] disabled:opacity-50 transition-colors flex items-center justify-center gap-1.5"
          >
            {submitMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
            Save check-in
          </button>
        </div>
      </div>
    </div>
  );
}
