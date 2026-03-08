'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ClipboardCheck, Plus, X, CheckCircle2, Loader2, Stethoscope, User } from 'lucide-react';
import toast from 'react-hot-toast';
import { carePlansService } from '@/services/carePlans';
import type { CarePlan, CarePlanMetricType, CreateCarePlanRequest } from '@/types';

// ── Metric config ─────────────────────────────────────────────────────────────

const METRIC_OPTIONS: { value: CarePlanMetricType; label: string; unit: string }[] = [
  { value: 'general',              label: 'General',             unit: '' },
  { value: 'weight',               label: 'Weight',              unit: 'kg' },
  { value: 'steps',                label: 'Daily Steps',         unit: 'steps/day' },
  { value: 'sleep_score',          label: 'Sleep Score',         unit: 'pts' },
  { value: 'medication_adherence', label: 'Med. Adherence',      unit: '%' },
  { value: 'symptom_severity',     label: 'Symptom Severity',    unit: '/10' },
  { value: 'calories',             label: 'Daily Calories',      unit: 'kcal/day' },
  { value: 'lab_result',           label: 'Lab Result',          unit: '' },
];

const LOWER_IS_BETTER: CarePlanMetricType[] = ['symptom_severity'];

function computeProgress(plan: CarePlan, ouraSteps?: number, ouraSlpScore?: number): number | null {
  let current = plan.current_value;

  // Override with live Oura data when available
  if (plan.metric_type === 'steps' && ouraSteps != null) current = ouraSteps;
  if (plan.metric_type === 'sleep_score' && ouraSlpScore != null) current = ouraSlpScore;

  if (plan.target_value == null || current == null) return null;

  if (LOWER_IS_BETTER.includes(plan.metric_type)) {
    // Progress = how much below target we are; 100% = at or below target
    return current <= plan.target_value ? 100 : Math.round((plan.target_value / current) * 100);
  }
  return Math.min(100, Math.round((current / plan.target_value) * 100));
}

function fmtCurrent(plan: CarePlan, ouraSteps?: number, ouraSlpScore?: number): string {
  let current = plan.current_value;
  if (plan.metric_type === 'steps' && ouraSteps != null) current = ouraSteps;
  if (plan.metric_type === 'sleep_score' && ouraSlpScore != null) current = ouraSlpScore;
  if (current == null) return '—';
  if (plan.metric_type === 'steps') return Math.round(current).toLocaleString();
  if (plan.metric_type === 'medication_adherence') return `${Math.round(current)}%`;
  if (plan.metric_type === 'symptom_severity') return current.toFixed(1) + '/10';
  return String(current);
}

// ── Add Care Plan Modal ────────────────────────────────────────────────────────

function AddCarePlanModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState('');
  const [metricType, setMetricType] = useState<CarePlanMetricType>('general');
  const [targetValue, setTargetValue] = useState('');
  const [targetUnit, setTargetUnit] = useState('');
  const [targetDate, setTargetDate] = useState('');
  const [source, setSource] = useState<'self' | 'doctor'>('self');
  const [notes, setNotes] = useState('');

  // Auto-fill unit when metric changes
  const handleMetricChange = (mt: CarePlanMetricType) => {
    setMetricType(mt);
    const opt = METRIC_OPTIONS.find((o) => o.value === mt);
    if (opt?.unit) setTargetUnit(opt.unit);
    else setTargetUnit('');
  };

  const createMutation = useMutation({
    mutationFn: (payload: CreateCarePlanRequest) => carePlansService.createPlan(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['care-plans'] });
      toast.success('Care plan added');
      onClose();
    },
    onError: () => toast.error('Failed to add care plan'),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    createMutation.mutate({
      title: title.trim(),
      metric_type: metricType,
      target_value: targetValue ? parseFloat(targetValue) : undefined,
      target_unit: targetUnit.trim() || undefined,
      target_date: targetDate || undefined,
      source,
      notes: notes.trim() || undefined,
    });
  };

  const showTarget = metricType !== 'general';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-md rounded-2xl p-6 shadow-2xl"
        style={{ backgroundColor: '#0D1117', border: '1px solid rgba(255,255,255,0.10)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-500/15 flex items-center justify-center">
              <ClipboardCheck className="w-4 h-4 text-blue-400" />
            </div>
            <h2 className="text-base font-semibold text-[#E8EDF5]">New Care Plan Item</h2>
          </div>
          <button onClick={onClose} className="text-[#526380] hover:text-[#8B97A8] transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-xs font-medium text-[#8B97A8] mb-1.5">Plan / target</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Reduce LDL to 100 mg/dL, Walk 8k steps daily…"
              className="w-full rounded-lg px-3 py-2.5 text-sm text-[#E8EDF5] placeholder-[#3D4F66] outline-none"
              style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
              autoFocus
            />
          </div>

          {/* Metric type */}
          <div>
            <label className="block text-xs font-medium text-[#8B97A8] mb-1.5">Track metric</label>
            <select
              value={metricType}
              onChange={(e) => handleMetricChange(e.target.value as CarePlanMetricType)}
              className="w-full rounded-lg px-3 py-2.5 text-sm text-[#E8EDF5] outline-none appearance-none"
              style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
            >
              {METRIC_OPTIONS.map((o) => (
                <option key={o.value} value={o.value} style={{ backgroundColor: '#0D1117' }}>{o.label}</option>
              ))}
            </select>
          </div>

          {/* Target value + unit */}
          {showTarget && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-[#8B97A8] mb-1.5">Target value</label>
                <input
                  type="number"
                  value={targetValue}
                  onChange={(e) => setTargetValue(e.target.value)}
                  placeholder="e.g. 100"
                  step="any"
                  className="w-full rounded-lg px-3 py-2.5 text-sm text-[#E8EDF5] placeholder-[#3D4F66] outline-none"
                  style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#8B97A8] mb-1.5">Unit</label>
                <input
                  type="text"
                  value={targetUnit}
                  onChange={(e) => setTargetUnit(e.target.value)}
                  placeholder="e.g. mg/dL"
                  className="w-full rounded-lg px-3 py-2.5 text-sm text-[#E8EDF5] placeholder-[#3D4F66] outline-none"
                  style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                />
              </div>
            </div>
          )}

          {/* Source + Target date row */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#8B97A8] mb-1.5">Set by</label>
              <div className="flex rounded-lg overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
                {(['self', 'doctor'] as const).map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setSource(s)}
                    className={`flex-1 py-2 text-xs font-medium transition-colors flex items-center justify-center gap-1.5 ${
                      source === s
                        ? 'bg-[#00D4AA]/20 text-[#00D4AA]'
                        : 'text-[#526380] hover:text-[#8B97A8]'
                    }`}
                    style={{ backgroundColor: source === s ? undefined : 'rgba(255,255,255,0.02)' }}
                  >
                    {s === 'self' ? <User className="w-3 h-3" /> : <Stethoscope className="w-3 h-3" />}
                    {s === 'self' ? 'Me' : 'Doctor'}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-[#8B97A8] mb-1.5">
                Target date <span className="text-[#3D4F66]">(optional)</span>
              </label>
              <input
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                className="w-full rounded-lg px-3 py-2.5 text-sm text-[#E8EDF5] outline-none"
                style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', colorScheme: 'dark' }}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-lg text-sm font-medium text-[#526380] hover:text-[#8B97A8] transition-colors"
              style={{ backgroundColor: 'rgba(255,255,255,0.04)' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!title.trim() || createMutation.isPending}
              className="flex-1 py-2.5 rounded-lg text-sm font-semibold text-[#080B10] bg-[#00D4AA] hover:bg-[#00BF99] disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
            >
              {createMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              Add to plan
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Plan row ──────────────────────────────────────────────────────────────────

interface PlanRowProps {
  plan: CarePlan;
  ouraSteps?: number;
  ouraSlpScore?: number;
}

function PlanRow({ plan, ouraSteps, ouraSlpScore }: PlanRowProps) {
  const queryClient = useQueryClient();

  const completeMutation = useMutation({
    mutationFn: () => carePlansService.updatePlan(plan.id, { status: 'completed' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['care-plans'] });
      toast.success('Care plan completed! 🎉');
    },
    onError: () => toast.error('Could not update plan'),
  });

  const deleteMutation = useMutation({
    mutationFn: () => carePlansService.deletePlan(plan.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['care-plans'] }),
    onError: () => toast.error('Could not delete plan'),
  });

  const progress = computeProgress(plan, ouraSteps, ouraSlpScore);
  const current = fmtCurrent(plan, ouraSteps, ouraSlpScore);
  const metricLabel = METRIC_OPTIONS.find((o) => o.value === plan.metric_type)?.label ?? plan.metric_type;
  const progressColor = progress == null ? '#526380' : progress >= 80 ? '#00D4AA' : progress >= 50 ? '#FBBF24' : '#F87171';

  return (
    <div className="flex items-start gap-3 group">
      <button
        onClick={() => completeMutation.mutate()}
        disabled={completeMutation.isPending}
        className="mt-0.5 flex-shrink-0 text-[#3D4F66] hover:text-[#00D4AA] transition-colors"
        aria-label="Mark completed"
      >
        {completeMutation.isPending
          ? <Loader2 className="w-4 h-4 animate-spin text-[#00D4AA]" />
          : <CheckCircle2 className="w-4 h-4" />}
      </button>

      <div className="flex-1 min-w-0">
        {/* Title + source badge */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <p className="text-sm text-[#C8D5E8] leading-snug">{plan.title}</p>
          {plan.source === 'doctor' && (
            <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 flex items-center gap-0.5">
              <Stethoscope className="w-2.5 h-2.5" />Dr
            </span>
          )}
        </div>

        {/* Progress bar when we have target + current */}
        {plan.target_value != null && (
          <div className="mt-1.5">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-[#3D4F66]">{metricLabel}</span>
              <span className="text-[10px]" style={{ color: progressColor }}>
                {current} → {plan.target_value}{plan.target_unit ? ` ${plan.target_unit}` : ''}
                {progress != null ? ` · ${progress}%` : ''}
              </span>
            </div>
            <div className="h-1 w-full rounded-full bg-white/5 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${progress ?? 0}%`, backgroundColor: progressColor }}
              />
            </div>
          </div>
        )}

        {/* Metadata row */}
        <div className="flex items-center gap-2 mt-1 flex-wrap">
          {plan.metric_type !== 'general' && plan.target_value == null && (
            <span className="text-[10px] text-[#3D4F66] bg-white/5 px-1.5 py-0.5 rounded-md">{metricLabel}</span>
          )}
          {plan.target_date && (
            <span className="text-[10px] text-[#3D4F66]">
              by {new Date(plan.target_date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </span>
          )}
        </div>
      </div>

      <button
        onClick={() => deleteMutation.mutate()}
        disabled={deleteMutation.isPending}
        className="mt-0.5 flex-shrink-0 opacity-0 group-hover:opacity-100 text-[#3D4F66] hover:text-[#F87171] transition-all"
        aria-label="Remove plan"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

// ── Care Plan Panel ────────────────────────────────────────────────────────────

interface CarePlanPanelProps {
  /** 7-day avg steps from Oura timeline (optional — used for steps progress) */
  ouraSteps?: number;
  /** Latest sleep score from Oura timeline (optional) */
  ouraSlpScore?: number;
}

export function CarePlanPanel({ ouraSteps, ouraSlpScore }: CarePlanPanelProps) {
  const [showModal, setShowModal] = useState(false);

  const { data: plans = [], isLoading } = useQuery({
    queryKey: ['care-plans'],
    queryFn: () => carePlansService.listPlans('active'),
    staleTime: 60_000,
  });

  if (isLoading) return null;

  if (plans.length === 0) {
    return (
      <>
        {showModal && <AddCarePlanModal onClose={() => setShowModal(false)} />}
        <div
          className="rounded-xl px-5 py-4 flex items-center justify-between"
          style={{ backgroundColor: 'rgba(255,255,255,0.02)', border: '1px dashed rgba(255,255,255,0.08)' }}
        >
          <div className="flex items-center gap-3">
            <ClipboardCheck className="w-4 h-4 text-[#3D4F66]" />
            <p className="text-sm text-[#3D4F66]">No care plan yet — add a measurable target</p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="text-xs font-medium text-[#00D4AA] hover:text-[#00BF99] transition-colors flex-shrink-0 ml-4"
          >
            + Add plan
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      {showModal && <AddCarePlanModal onClose={() => setShowModal(false)} />}
      <div
        className="rounded-xl p-5"
        style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ClipboardCheck className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-[#8B97A8]">Care Plan</h2>
            <span className="text-xs text-[#3D4F66] bg-white/5 px-1.5 py-0.5 rounded-full">{plans.length}</span>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="w-6 h-6 rounded-md bg-blue-500/10 hover:bg-blue-500/20 flex items-center justify-center transition-colors"
            aria-label="Add care plan item"
          >
            <Plus className="w-3.5 h-3.5 text-blue-400" />
          </button>
        </div>

        <div className="space-y-4">
          {plans.map((plan) => (
            <PlanRow
              key={plan.id}
              plan={plan}
              ouraSteps={ouraSteps}
              ouraSlpScore={ouraSlpScore}
            />
          ))}
        </div>
      </div>
    </>
  );
}
