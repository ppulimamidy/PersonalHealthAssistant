'use client';

import { useState, useEffect, useCallback } from 'react';
import { Plus, FlaskConical, RefreshCw } from 'lucide-react';
import { InterventionCard } from '@/components/interventions/InterventionCard';
import { OutcomeCard } from '@/components/interventions/OutcomeCard';
import { interventionsService } from '@/services/interventions';
import type { ActiveIntervention, InterventionOutcome, InterventionPattern } from '@/types';

const PATTERN_OPTIONS: Array<{ value: InterventionPattern; label: string; description: string }> = [
  {
    value: 'overtraining',
    label: 'Overtraining Recovery',
    description: 'Anti-inflammatory + magnesium-rich foods to support recovery',
  },
  {
    value: 'inflammation',
    label: 'Inflammation Reduction',
    description: 'Lower glycemic load, omega-3 focus',
  },
  {
    value: 'poor_recovery',
    label: 'Recovery Boost',
    description: 'Protein-forward + recovery-focused nutrition',
  },
  {
    value: 'sleep_disruption',
    label: 'Sleep Optimisation',
    description: 'Earlier dinner window + sleep-promoting foods',
  },
];

type Tab = 'active' | 'completed' | 'all';

function StartInterventionModal({
  onClose,
  onStarted,
}: {
  onClose: () => void;
  onStarted: (iv: ActiveIntervention) => void;
}) {
  const [pattern, setPattern] = useState<InterventionPattern>('poor_recovery');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [duration, setDuration] = useState(7);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStart = async () => {
    if (!title.trim()) {
      setError('Please enter a title for this experiment');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const iv = await interventionsService.start({
        recommendation_pattern: pattern,
        title: title.trim(),
        description: description.trim() || undefined,
        duration_days: duration,
      });
      onStarted(iv);
    } catch {
      setError('Failed to start intervention. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div
        className="w-full max-w-md rounded-2xl border p-6"
        style={{ backgroundColor: '#0C1219', borderColor: 'rgba(255,255,255,0.08)' }}
      >
        <h2 className="text-base font-semibold text-[#E8EDF5] mb-1">Start an Experiment</h2>
        <p className="text-xs text-[#526380] mb-5 leading-relaxed">
          Pick something to try — like eating less sugar at night — and we'll measure whether it actually moves your health metrics.
        </p>

        {/* Pattern */}
        <label className="block text-xs font-medium text-[#8B97A8] mb-1.5">Pattern</label>
        <select
          className="w-full rounded-lg px-3 py-2 text-sm text-[#E8EDF5] mb-4 outline-none"
          style={{ backgroundColor: '#131B27', border: '1px solid rgba(255,255,255,0.08)' }}
          value={pattern}
          onChange={(e) => setPattern(e.target.value as InterventionPattern)}
        >
          {PATTERN_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>

        {/* Description hint */}
        {PATTERN_OPTIONS.find((o) => o.value === pattern) && (
          <p className="text-xs text-[#526380] -mt-2 mb-4">
            {PATTERN_OPTIONS.find((o) => o.value === pattern)!.description}
          </p>
        )}

        {/* Title */}
        <label className="block text-xs font-medium text-[#8B97A8] mb-1.5">Title</label>
        <input
          className="w-full rounded-lg px-3 py-2 text-sm text-[#E8EDF5] placeholder-[#3D4F66] mb-4 outline-none"
          style={{ backgroundColor: '#131B27', border: '1px solid rgba(255,255,255,0.08)' }}
          placeholder="e.g. Lower carbs after 6pm for 7 days"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />

        {/* Description */}
        <label className="block text-xs font-medium text-[#8B97A8] mb-1.5">
          Notes <span className="font-normal text-[#3D4F66]">(optional)</span>
        </label>
        <textarea
          className="w-full rounded-lg px-3 py-2 text-sm text-[#E8EDF5] placeholder-[#3D4F66] mb-4 outline-none resize-none"
          style={{ backgroundColor: '#131B27', border: '1px solid rgba(255,255,255,0.08)' }}
          rows={2}
          placeholder="What specific dietary change are you testing?"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />

        {/* Duration */}
        <label className="block text-xs font-medium text-[#8B97A8] mb-1.5">
          Duration: {duration} days
        </label>
        <input
          type="range"
          min={3}
          max={21}
          value={duration}
          onChange={(e) => setDuration(Number(e.target.value))}
          className="w-full mb-5 accent-[#00D4AA]"
        />

        {error && (
          <p className="text-xs text-[#F87171] mb-3">{error}</p>
        )}

        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 py-2 rounded-lg text-sm text-[#526380] hover:text-[#8B97A8] transition-colors"
            style={{ backgroundColor: 'rgba(255,255,255,0.04)' }}
          >
            Cancel
          </button>
          <button
            onClick={handleStart}
            disabled={loading}
            className="flex-1 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
            style={{ backgroundColor: '#00D4AA', color: '#080B10' }}
          >
            {loading ? 'Starting…' : 'Start Trial'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function InterventionsPage() {
  const [tab, setTab] = useState<Tab>('active');
  const [interventions, setInterventions] = useState<ActiveIntervention[]>([]);
  const [latestOutcome, setLatestOutcome] = useState<InterventionOutcome | null>(null);
  const [latestOutcomeTitle, setLatestOutcomeTitle] = useState<string>('');
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchInterventions = useCallback(async () => {
    setLoading(true);
    try {
      const all = await interventionsService.list();
      setInterventions(all);
    } catch {
      setInterventions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInterventions();
  }, [fetchInterventions]);

  const handleCheckin = async (id: string, adhered: boolean) => {
    setActionLoading(id);
    try {
      await interventionsService.checkin(id, adhered);
      await fetchInterventions();
    } finally {
      setActionLoading(null);
    }
  };

  const handleComplete = async (id: string) => {
    setActionLoading(id);
    try {
      const title = interventions.find((iv) => iv.id === id)?.title || 'Intervention';
      const outcome = await interventionsService.complete(id);
      setLatestOutcome(outcome);
      setLatestOutcomeTitle(title);
      await fetchInterventions();
    } finally {
      setActionLoading(null);
    }
  };

  const handleAbandon = async (id: string) => {
    setActionLoading(id);
    try {
      await interventionsService.abandon(id);
      await fetchInterventions();
    } finally {
      setActionLoading(null);
    }
  };

  const handleStarted = async (iv: ActiveIntervention) => {
    setShowModal(false);
    setInterventions((prev) => [iv, ...prev]);
  };

  const filtered = interventions.filter((iv) => {
    if (tab === 'active') return iv.status === 'active';
    if (tab === 'completed') return iv.status === 'completed';
    return true;
  });

  const activeCount = interventions.filter((iv) => iv.status === 'active').length;
  const completedCount = interventions.filter((iv) => iv.status === 'completed').length;

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <FlaskConical className="w-5 h-5" style={{ color: '#00D4AA' }} />
            <h1 className="text-lg font-semibold text-[#E8EDF5]">Experiments</h1>
          </div>
          <p className="text-sm text-[#526380] leading-snug">
            Try something for a week and see if it actually moves your numbers.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 text-sm font-medium px-3 py-2 rounded-lg transition-all flex-shrink-0"
          style={{ backgroundColor: '#00D4AA', color: '#080B10' }}
        >
          <Plus className="w-4 h-4" />
          New Experiment
        </button>
      </div>

      {/* Latest outcome card */}
      {latestOutcome && (
        <div className="mb-6">
          <OutcomeCard outcome={latestOutcome} title={latestOutcomeTitle} />
        </div>
      )}

      {/* Tabs */}
      <div
        className="flex items-center gap-0 rounded-lg p-0.5 mb-5 w-fit"
        style={{ backgroundColor: 'rgba(255,255,255,0.04)' }}
      >
        {([
          { key: 'active', label: `Active (${activeCount})` },
          { key: 'completed', label: `Completed (${completedCount})` },
          { key: 'all', label: 'All' },
        ] as const).map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className="text-xs font-medium px-3 py-1.5 rounded-md transition-all"
            style={
              tab === key
                ? { backgroundColor: '#00D4AA18', color: '#00D4AA' }
                : { color: '#526380' }
            }
          >
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <RefreshCw className="w-5 h-5 text-[#526380] animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16">
          <FlaskConical className="w-10 h-10 mx-auto mb-3 opacity-20" style={{ color: '#00D4AA' }} />
          <p className="text-sm text-[#526380]">
            {tab === 'active'
              ? 'No active experiments. Start one from a recommendation.'
              : 'No experiments in this category yet.'}
          </p>
          {tab === 'active' && (
            <button
              onClick={() => setShowModal(true)}
              className="mt-4 text-xs font-medium px-4 py-2 rounded-lg transition-all"
              style={{ backgroundColor: '#00D4AA18', color: '#00D4AA' }}
            >
              Start your first experiment
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((iv) => (
            <div key={iv.id} className={actionLoading === iv.id ? 'opacity-60 pointer-events-none' : ''}>
              <InterventionCard
                intervention={iv}
                onCheckin={iv.status === 'active' ? handleCheckin : undefined}
                onComplete={iv.status === 'active' ? handleComplete : undefined}
                onAbandon={iv.status === 'active' ? handleAbandon : undefined}
              />
            </div>
          ))}
        </div>
      )}

      {/* Disclaimer */}
      <p className="text-[10px] text-[#3D4F66] text-center mt-8 leading-relaxed">
        Experiments are for personal learning only. Outcomes are shared with your care team
        via your existing share links. Always consult your healthcare provider before changing
        your diet or supplementation.
      </p>

      {showModal && (
        <StartInterventionModal onClose={() => setShowModal(false)} onStarted={handleStarted} />
      )}
    </div>
  );
}
