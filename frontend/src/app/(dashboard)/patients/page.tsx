'use client';

import { useState, useEffect } from 'react';
import {
  Users, Search, HeartPulse, Pill, FlaskConical, AlertTriangle,
  Target, ChevronDown, ChevronUp, CheckCircle, X, UserPlus,
  Clock, ChevronRight, Bell, TrendingUp, TrendingDown, FileText,
} from 'lucide-react';
import { sharingService } from '@/services/sharing';
import { carePlansService } from '@/services/carePlans';
import { caregiverService } from '@/services/caregiver';
import type { SharedHealthSummary, ManagedProfile, PatientAlert } from '@/types';
import { useAuthStore } from '@/stores/authStore';
import Link from 'next/link';
import toast from 'react-hot-toast';

// ── Stat chip ─────────────────────────────────────────────────────────────────

function StatChip({ label, value, warn }: { label: string; value: string | number; warn?: boolean }) {
  return (
    <div
      className="flex flex-col items-center px-3 py-2 rounded-lg"
      style={{
        backgroundColor: warn ? 'rgba(248,113,113,0.08)' : 'rgba(255,255,255,0.04)',
        border: `1px solid ${warn ? 'rgba(248,113,113,0.2)' : 'rgba(255,255,255,0.06)'}`,
      }}
    >
      <span className="text-lg font-semibold" style={{ color: warn ? '#F87171' : '#00D4AA' }}>
        {value}
      </span>
      <span className="text-[11px] mt-0.5" style={{ color: '#526380' }}>{label}</span>
    </div>
  );
}

// ── Patient summary panel ─────────────────────────────────────────────────────

function PatientSummaryPanel({ data }: { data: SharedHealthSummary }) {
  const profile = data.profile as Record<string, unknown> | undefined;
  const abnormalLabs = (data.lab_results ?? []).filter((l) => l.is_abnormal).length;
  const highSymptoms = (data.symptoms ?? []).filter((s) => (s.severity ?? 0) >= 7).length;

  function calcAge(dob?: unknown): string {
    if (typeof dob !== 'string') return '—';
    const d = new Date(dob);
    const now = new Date();
    let age = now.getFullYear() - d.getFullYear();
    if (now.getMonth() < d.getMonth() || (now.getMonth() === d.getMonth() && now.getDate() < d.getDate())) age--;
    return `${age}`;
  }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-4 gap-3">
        <StatChip label="Age" value={calcAge(profile?.date_of_birth)} />
        <StatChip
          label="Adherence"
          value={data.medication_adherence_pct !== undefined ? `${data.medication_adherence_pct}%` : '—'}
          warn={(data.medication_adherence_pct ?? 100) < 70}
        />
        <StatChip label="Abnormal Labs" value={abnormalLabs} warn={abnormalLabs > 0} />
        <StatChip label="High Symptoms" value={highSymptoms} warn={highSymptoms > 0} />
      </div>

      {data.conditions && data.conditions.length > 0 && (
        <div>
          <p className="text-xs font-medium mb-2" style={{ color: '#526380' }}>CONDITIONS</p>
          <div className="flex flex-wrap gap-1.5">
            {data.conditions.map((c, i) => (
              <span key={i} className="text-xs px-2 py-0.5 rounded-full"
                style={{ backgroundColor: 'rgba(255,255,255,0.06)', color: '#C8D5E8' }}>
                {c}
              </span>
            ))}
          </div>
        </div>
      )}

      {data.medications && data.medications.length > 0 && (
        <div>
          <p className="text-xs font-medium mb-2 flex items-center gap-1.5" style={{ color: '#526380' }}>
            <Pill className="w-3.5 h-3.5" /> ACTIVE MEDICATIONS ({data.medications.length})
          </p>
          <div className="space-y-1.5">
            {data.medications.slice(0, 6).map((m, i) => (
              <div key={i} className="flex items-start justify-between gap-2">
                <span className="text-sm" style={{ color: '#C8D5E8' }}>{m.name}</span>
                <span className="text-xs flex-shrink-0" style={{ color: '#526380' }}>{m.dosage}</span>
              </div>
            ))}
            {data.medications.length > 6 && (
              <p className="text-xs" style={{ color: '#3D4F66' }}>+{data.medications.length - 6} more</p>
            )}
          </div>
        </div>
      )}

      {abnormalLabs > 0 && (
        <div>
          <p className="text-xs font-medium mb-2 flex items-center gap-1.5" style={{ color: '#F87171' }}>
            <FlaskConical className="w-3.5 h-3.5" /> ABNORMAL LAB VALUES
          </p>
          <div className="space-y-1.5">
            {(data.lab_results ?? []).filter((l) => l.is_abnormal).slice(0, 6).map((lab, i) => (
              <div key={i} className="flex items-center justify-between gap-2">
                <span className="text-sm" style={{ color: '#C8D5E8' }}>{lab.test_name}</span>
                <span className="text-sm font-medium" style={{ color: '#F87171' }}>
                  {lab.value} {lab.unit}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.insights && data.insights.length > 0 && (
        <div>
          <p className="text-xs font-medium mb-2" style={{ color: '#526380' }}>RECENT INSIGHTS</p>
          <div className="space-y-2">
            {data.insights.slice(0, 3).map((ins, i) => (
              <div key={i}>
                <p className="text-sm font-medium" style={{ color: '#C8D5E8' }}>{ins.title}</p>
                {ins.summary && (
                  <p className="text-xs mt-0.5 line-clamp-2" style={{ color: '#8B97A8' }}>{ins.summary}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Experiments */}
      {data.interventions && data.interventions.length > 0 && (
        <div>
          <p className="text-xs font-medium mb-2 flex items-center gap-1.5" style={{ color: '#526380' }}>
            <FlaskConical className="w-3.5 h-3.5" /> EXPERIMENTS ({data.interventions.length})
          </p>
          <p className="text-[11px] mb-2 leading-snug" style={{ color: '#3D4F66' }}>
            Patient-observed · not clinically verified
          </p>
          <div className="space-y-2">
            {data.interventions.map((iv, i) => {
              const deltaPairs = Object.entries(iv.outcome_delta || {}).filter(([, v]) => Math.abs(v) > 1);
              return (
                <div
                  key={i}
                  className="rounded-lg p-3"
                  style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <p className="text-sm font-medium leading-snug" style={{ color: '#C8D5E8' }}>{iv.title}</p>
                    <span
                      className="text-[10px] font-semibold px-1.5 py-0.5 rounded flex-shrink-0"
                      style={{
                        backgroundColor: iv.adherence_pct >= 70 ? 'rgba(0,212,170,0.12)' : 'rgba(251,191,36,0.1)',
                        color: iv.adherence_pct >= 70 ? '#00D4AA' : '#FBB124',
                      }}
                    >
                      {iv.adherence_pct.toFixed(0)}% adhered
                    </span>
                  </div>
                  <p className="text-xs capitalize mb-1.5" style={{ color: '#526380' }}>
                    {iv.recommendation_pattern?.replace(/_/g, ' ')} · {iv.duration_days}d
                    {iv.completed_at ? ` · ${new Date(iv.completed_at).toLocaleDateString()}` : ''}
                  </p>
                  {iv.outcome_summary && (
                    <p className="text-xs italic mb-1.5 leading-snug" style={{ color: '#8B97A8' }}>
                      {iv.outcome_summary}
                    </p>
                  )}
                  {deltaPairs.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {deltaPairs
                        .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
                        .slice(0, 4)
                        .map(([metric, pct]) => {
                          const isPos = pct > 0;
                          const label = metric.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
                          return (
                            <span
                              key={metric}
                              className="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-full"
                              style={{
                                backgroundColor: isPos ? 'rgba(0,212,170,0.1)' : 'rgba(248,113,113,0.1)',
                                color: isPos ? '#00D4AA' : '#F87171',
                              }}
                            >
                              {isPos ? <TrendingUp className="w-2.5 h-2.5" /> : <TrendingDown className="w-2.5 h-2.5" />}
                              {label} {isPos ? '+' : ''}{pct.toFixed(1)}%
                            </span>
                          );
                        })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {data.care_plans && data.care_plans.length > 0 && (
        <div>
          <p className="text-xs font-medium mb-3 flex items-center gap-1.5" style={{ color: '#526380' }}>
            <Target className="w-3.5 h-3.5" /> CARE PLAN PROGRESS
          </p>
          <div className="space-y-3">
            {data.care_plans.map((plan, i) => {
              const hasProgress = plan.current_value != null && plan.target_value != null;
              const lowerIsBetter = plan.metric_type === 'symptom_severity';
              let pct = 0; let onTrack = false;
              if (hasProgress) {
                if (lowerIsBetter) {
                  const baseline = 8;
                  pct = Math.min(100, Math.max(0, Math.round(((baseline - plan.current_value!) / (baseline - plan.target_value!)) * 100)));
                  onTrack = plan.current_value! <= plan.target_value!;
                } else {
                  pct = Math.min(100, Math.round((plan.current_value! / plan.target_value!) * 100));
                  onTrack = pct >= 90;
                }
              }
              return (
                <div key={i}>
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="text-sm" style={{ color: '#C8D5E8' }}>{plan.title}</span>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {plan.source === 'doctor' && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded"
                          style={{ backgroundColor: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}>Rx</span>
                      )}
                      {hasProgress && (
                        <span className="text-xs" style={{ color: onTrack ? '#00D4AA' : '#F87171' }}>
                          {plan.current_value?.toFixed(1)} / {plan.target_value} {plan.target_unit}
                        </span>
                      )}
                      {plan.target_date && (
                        <span className="text-xs" style={{ color: '#3D4F66' }}>by {plan.target_date}</span>
                      )}
                    </div>
                  </div>
                  {hasProgress && (
                    <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }}>
                      <div className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${pct}%`, backgroundColor: onTrack ? '#00D4AA' : pct > 50 ? '#FBB124' : '#F87171' }} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <PreAppointmentSummary data={data} />

      <p className="text-xs pt-2" style={{ color: '#3D4F66' }}>
        Summary generated {new Date(data.generated_at).toLocaleString()}
      </p>
    </div>
  );
}

// ── Pre-appointment summary ───────────────────────────────────────────────────

function PreAppointmentSummary({ data }: { data: SharedHealthSummary }) {
  const lines: string[] = [];
  if (data.medication_adherence_pct !== undefined) {
    const p = data.medication_adherence_pct;
    lines.push(p >= 85 ? `Medication adherence is strong at ${p}% over 30 days.`
      : p >= 60 ? `Medication adherence is moderate at ${p}% — worth discussing barriers.`
      : `Medication adherence is low at ${p}% — review regimen.`);
  }
  const abnormal = (data.lab_results ?? []).filter((l) => l.is_abnormal);
  if (abnormal.length > 0)
    lines.push(`${abnormal.length} abnormal lab value(s): ${abnormal.slice(0, 3).map((l) => l.test_name).join(', ')}.`);
  if (data.avg_symptom_severity !== undefined) {
    const sev = data.avg_symptom_severity;
    const hi = (data.symptoms ?? []).filter((s) => (s.severity ?? 0) >= 7).length;
    lines.push(sev >= 6
      ? `Avg symptom severity ${sev}/10 over 30 days${hi > 0 ? ` (${hi} high-severity events)` : ''} — warrants attention.`
      : `Avg symptom severity ${sev}/10 over 30 days.`);
  }
  if (data.care_plans && data.care_plans.length > 0) {
    const dr = data.care_plans.filter((p) => p.source === 'doctor').length;
    lines.push(`${data.care_plans.length} active care plan(s)${dr > 0 ? ` (${dr} provider-prescribed)` : ''}.`);
  }
  if (data.conditions && data.conditions.length > 0)
    lines.push(`Known conditions: ${data.conditions.slice(0, 4).join(', ')}.`);
  if (data.interventions && data.interventions.length > 0) {
    const improvements = data.interventions.flatMap((iv) =>
      Object.values(iv.outcome_delta || {}).filter((v) => v > 3)
    ).length;
    lines.push(
      `${data.interventions.length} completed experiment(s)${improvements > 0 ? ` — ${improvements} positive metric shift(s) observed` : ''}.`
    );
  }
  if (lines.length === 0) return null;
  return (
    <div className="p-4 rounded-xl mt-1"
      style={{ backgroundColor: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.12)' }}>
      <p className="text-xs font-semibold mb-2" style={{ color: '#00D4AA' }}>PRE-APPOINTMENT SUMMARY</p>
      <ul className="space-y-1.5">
        {lines.map((line, i) => (
          <li key={i} className="flex items-start gap-2">
            <span className="mt-1.5 w-1 h-1 rounded-full flex-shrink-0" style={{ backgroundColor: '#00D4AA' }} />
            <p className="text-sm leading-relaxed" style={{ color: '#C8D5E8' }}>{line}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ── Suggest care plan ─────────────────────────────────────────────────────────

const METRIC_OPTIONS = [
  { value: 'general', label: 'General goal' },
  { value: 'weight', label: 'Weight (kg)' },
  { value: 'medication_adherence', label: 'Medication adherence (%)' },
  { value: 'symptom_severity', label: 'Symptom severity (1-10)' },
  { value: 'calories', label: 'Daily calories' },
  { value: 'steps', label: 'Daily steps' },
  { value: 'sleep_score', label: 'Sleep score' },
  { value: 'lab_result', label: 'Lab result value' },
];

function SuggestCarePlanPanel({ shareToken, onSuccess }: { shareToken: string; onSuccess: () => void }) {
  const [open, setOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', metric_type: 'general', target_value: '', target_unit: '', target_date: '', notes: '' });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) return;
    setSubmitting(true);
    try {
      await carePlansService.suggestPlanForPatient({
        share_token: shareToken, title: form.title.trim(),
        description: form.description || undefined, metric_type: form.metric_type,
        target_value: form.target_value ? parseFloat(form.target_value) : undefined,
        target_unit: form.target_unit || undefined, target_date: form.target_date || undefined,
        notes: form.notes || undefined,
      });
      setSubmitted(true); setOpen(false);
      toast.success('Care plan suggested to patient');
      onSuccess();
    } catch { toast.error('Failed to suggest care plan'); }
    finally { setSubmitting(false); }
  };

  return (
    <div className="rounded-xl mt-4"
      style={{ backgroundColor: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.15)' }}>
      <button type="button" onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 text-left">
        <div className="flex items-center gap-2.5">
          <Target className="w-4 h-4" style={{ color: '#00D4AA' }} />
          <span className="text-sm font-medium" style={{ color: '#00D4AA' }}>
            {submitted ? 'Suggest another care plan' : 'Suggest a Care Plan'}
          </span>
          {submitted && <CheckCircle className="w-3.5 h-3.5" style={{ color: '#00D4AA' }} />}
        </div>
        {open ? <ChevronUp className="w-4 h-4" style={{ color: '#526380' }} />
               : <ChevronDown className="w-4 h-4" style={{ color: '#526380' }} />}
      </button>

      {open && (
        <form onSubmit={handleSubmit} className="px-4 pb-4 space-y-3">
          <input type="text" required placeholder="Goal title e.g. Reduce LDL to 100 mg/dL"
            value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-[#00D4AA]"
            style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#E8EDF5' }} />
          <div className="grid grid-cols-2 gap-3">
            <select value={form.metric_type} onChange={(e) => setForm({ ...form, metric_type: e.target.value })}
              className="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-[#00D4AA]"
              style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#E8EDF5' }}>
              {METRIC_OPTIONS.map((o) => <option key={o.value} value={o.value} style={{ backgroundColor: '#0F1923' }}>{o.label}</option>)}
            </select>
            <input type="date" value={form.target_date} onChange={(e) => setForm({ ...form, target_date: e.target.value })}
              className="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-[#00D4AA]"
              style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#E8EDF5' }} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input type="number" step="0.01" placeholder="Target value"
              value={form.target_value} onChange={(e) => setForm({ ...form, target_value: e.target.value })}
              className="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-[#00D4AA]"
              style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#E8EDF5' }} />
            <input type="text" placeholder="Unit e.g. mg/dL"
              value={form.target_unit} onChange={(e) => setForm({ ...form, target_unit: e.target.value })}
              className="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-[#00D4AA]"
              style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#E8EDF5' }} />
          </div>
          <textarea rows={2} placeholder="Clinical notes (optional)…"
            value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })}
            className="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-[#00D4AA] resize-none"
            style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#E8EDF5' }} />
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={() => setOpen(false)}
              className="px-3 py-1.5 text-sm rounded-lg" style={{ color: '#526380' }}>Cancel</button>
            <button type="submit" disabled={submitting || !form.title.trim()}
              className="px-4 py-1.5 text-sm font-medium rounded-lg disabled:opacity-40"
              style={{ backgroundColor: '#00D4AA', color: '#080B10' }}>
              {submitting ? 'Suggesting…' : 'Suggest Plan'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

// ── Roster sidebar ────────────────────────────────────────────────────────────

function RosterSidebar({
  roster,
  activeId,
  onSelect,
  onRemove,
  onAddNew,
}: {
  roster: ManagedProfile[];
  activeId: string | null;
  onSelect: (p: ManagedProfile) => void;
  onRemove: (id: string) => void;
  onAddNew: () => void;
}) {
  return (
    <div className="flex flex-col h-full" style={{ minWidth: 0 }}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold" style={{ color: '#526380' }}>
          ROSTER ({roster.length})
        </p>
        <button onClick={onAddNew}
          className="flex items-center gap-1 text-xs px-2 py-1 rounded-lg transition-colors"
          style={{ color: '#00D4AA', backgroundColor: 'rgba(0,212,170,0.08)' }}>
          <UserPlus className="w-3 h-3" /> Add
        </button>
      </div>

      {roster.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-center flex-1">
          <Users className="w-8 h-8 mb-2" style={{ color: '#3D4F66' }} />
          <p className="text-xs" style={{ color: '#526380' }}>No patients yet</p>
          <p className="text-xs mt-1" style={{ color: '#3D4F66' }}>Add one using their share code</p>
        </div>
      ) : (
        <div className="space-y-1 flex-1 overflow-y-auto">
          {roster.map((p) => {
            const isActive = p.id === activeId;
            return (
              <div key={p.id}
                className="flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer group transition-colors"
                style={{
                  backgroundColor: isActive ? 'rgba(0,212,170,0.1)' : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${isActive ? 'rgba(0,212,170,0.25)' : 'rgba(255,255,255,0.05)'}`,
                }}
                onClick={() => onSelect(p)}
              >
                <div
                  className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-semibold"
                  style={{ backgroundColor: isActive ? 'rgba(0,212,170,0.2)' : 'rgba(255,255,255,0.06)', color: isActive ? '#00D4AA' : '#526380' }}
                >
                  {(p.display_name || p.label || 'P').charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate font-medium" style={{ color: isActive ? '#00D4AA' : '#C8D5E8' }}>
                    {p.display_name || p.label || 'Patient'}
                  </p>
                  {p.relationship && (
                    <p className="text-[10px] truncate" style={{ color: '#526380' }}>{p.relationship}</p>
                  )}
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{ color: '#526380' }} />
                  <button
                    onClick={(e) => { e.stopPropagation(); onRemove(p.id); }}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:text-red-400"
                    style={{ color: '#526380' }}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Add-patient token input ────────────────────────────────────────────────────

function AddPatientPanel({
  onFound,
  onCancel,
  showCancel,
}: {
  onFound: (data: SharedHealthSummary, token: string) => void;
  onCancel: () => void;
  showCancel: boolean;
}) {
  const [tokenInput, setTokenInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLookup = async () => {
    const t = tokenInput.trim();
    if (!t) return;
    setLoading(true); setError(null);
    try {
      const token = t.includes('/share/') ? t.split('/share/')[1].split('/')[0] : t;
      const data = await sharingService.getPublicSummary(token);
      onFound(data, token);
      setTokenInput('');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Share code not found');
    } finally { setLoading(false); }
  };

  return (
    <div className="p-4 rounded-xl" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
      <p className="text-sm font-medium mb-3" style={{ color: '#C8D5E8' }}>Enter patient share code</p>
      <div className="flex gap-2">
        <input type="text" value={tokenInput}
          onChange={(e) => setTokenInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleLookup()}
          placeholder="Paste share code or URL…"
          className="flex-1 px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#00D4AA]"
          style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#E8EDF5' }} />
        <button onClick={handleLookup} disabled={loading || !tokenInput.trim()}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-40"
          style={{ backgroundColor: '#00D4AA', color: '#080B10' }}>
          {loading
            ? <div className="w-4 h-4 rounded-full border-2 border-[#080B10] border-t-transparent animate-spin" />
            : <Search className="w-4 h-4" />}
          View
        </button>
      </div>
      {error && <p className="text-sm mt-2" style={{ color: '#F87171' }}>{error}</p>}
      {showCancel && (
        <button onClick={onCancel} className="mt-2 text-xs" style={{ color: '#526380' }}>← Back to roster</button>
      )}
    </div>
  );
}

// ── Alerts banner ─────────────────────────────────────────────────────────────

function AlertsBanner({
  alerts,
  onSelectPatient,
}: {
  alerts: PatientAlert[];
  onSelectPatient: (managedId: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  if (alerts.length === 0) return null;

  const criticalCount = alerts.filter((a) => a.severity === 'critical').length;
  const hasCritical = criticalCount > 0;

  return (
    <div className="mb-5 rounded-xl overflow-hidden"
      style={{
        backgroundColor: hasCritical ? 'rgba(248,113,113,0.06)' : 'rgba(251,191,36,0.05)',
        border: `1px solid ${hasCritical ? 'rgba(248,113,113,0.25)' : 'rgba(251,191,36,0.2)'}`,
      }}>
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 text-left"
      >
        <div className="flex items-center gap-2.5">
          <Bell className="w-4 h-4 flex-shrink-0" style={{ color: hasCritical ? '#F87171' : '#FBB124' }} />
          <span className="text-sm font-medium" style={{ color: hasCritical ? '#F87171' : '#FBB124' }}>
            {alerts.length} patient{alerts.length !== 1 ? 's have' : ' has'} out-of-range metrics
            {criticalCount > 0 && ` · ${criticalCount} critical`}
          </span>
        </div>
        {expanded
          ? <ChevronUp className="w-4 h-4" style={{ color: '#526380' }} />
          : <ChevronDown className="w-4 h-4" style={{ color: '#526380' }} />}
      </button>

      {expanded && (
        <div className="px-4 pb-3 space-y-2">
          {alerts.map((alert, i) => (
            <button
              key={i}
              type="button"
              onClick={() => onSelectPatient(alert.managed_id)}
              className="w-full flex items-center justify-between gap-3 px-3 py-2 rounded-lg text-left transition-colors hover:bg-white/5"
              style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <div className="flex items-center gap-2 min-w-0">
                <div
                  className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: alert.severity === 'critical' ? '#F87171' : '#FBB124' }}
                />
                <span className="text-sm font-medium truncate" style={{ color: '#C8D5E8' }}>
                  {alert.patient_label}
                </span>
                <span className="text-xs truncate" style={{ color: '#526380' }}>
                  — {alert.metric_name}
                </span>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {alert.current_value != null && (
                  <span className="text-xs tabular-nums"
                    style={{ color: alert.severity === 'critical' ? '#F87171' : '#FBB124' }}>
                    {alert.current_value}
                    {alert.target_value != null && <span style={{ color: '#526380' }}> / {alert.target_value}</span>}
                  </span>
                )}
                <span
                  className="text-[10px] px-1.5 py-0.5 rounded font-medium uppercase"
                  style={{
                    backgroundColor: alert.severity === 'critical' ? 'rgba(248,113,113,0.15)' : 'rgba(251,191,36,0.1)',
                    color: alert.severity === 'critical' ? '#F87171' : '#FBB124',
                  }}>
                  {alert.severity}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function PatientsPage() {
  const profile = useAuthStore((s) => s.profile);
  const isProvider = profile?.user_role === 'provider' || profile?.user_role === 'caregiver';

  // Roster state
  const [roster, setRoster] = useState<ManagedProfile[]>([]);
  const [rosterLoading, setRosterLoading] = useState(true);
  const [activeRosterId, setActiveRosterId] = useState<string | null>(null);
  const [showAddPanel, setShowAddPanel] = useState(false);

  // Patient panel state
  const [patientData, setPatientData] = useState<SharedHealthSummary | null>(null);
  const [activeToken, setActiveToken] = useState('');
  const [savingToRoster, setSavingToRoster] = useState(false);

  // Alerts state
  const [alerts, setAlerts] = useState<PatientAlert[]>([]);

  // Load roster + alerts on mount
  useEffect(() => {
    if (!isProvider) { setRosterLoading(false); return; }
    caregiverService.listManaged()
      .then((items) => {
        setRoster(items);
        if (items.length === 0) setShowAddPanel(true);
      })
      .catch(() => { /* no-op */ })
      .finally(() => setRosterLoading(false));
    caregiverService.getAlerts().then(setAlerts).catch(() => {});
  }, [isProvider]);

  const handleRosterSelect = async (p: ManagedProfile) => {
    setActiveRosterId(p.id);
    setActiveToken(p.share_token);
    setShowAddPanel(false);
    try {
      const data = await sharingService.getPublicSummary(p.share_token);
      setPatientData(data);
    } catch {
      toast.error('Failed to load patient data');
    }
  };

  const handleRemoveFromRoster = async (id: string) => {
    try {
      await caregiverService.unlinkProfile(id);
      setRoster((prev) => prev.filter((p) => p.id !== id));
      if (activeRosterId === id) { setPatientData(null); setActiveRosterId(null); setShowAddPanel(true); }
      toast.success('Removed from roster');
    } catch { toast.error('Failed to remove patient'); }
  };

  const handlePatientFound = (data: SharedHealthSummary, token: string) => {
    setPatientData(data);
    setActiveToken(token);
    setActiveRosterId(null); // not yet in roster
  };

  const handleSaveToRoster = async () => {
    if (!activeToken || !patientData) return;
    setSavingToRoster(true);
    try {
      const managed = await caregiverService.linkProfile({
        token: activeToken,
        relationship: 'patient',
        display_name: patientData.label || 'Patient',
      });
      setRoster((prev) => [...prev, managed]);
      setActiveRosterId(managed.id);
      setShowAddPanel(false);
      toast.success('Patient saved to roster');
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      if (msg?.includes('already')) {
        toast('Already in your roster');
      } else {
        toast.error('Failed to save to roster');
      }
    } finally { setSavingToRoster(false); }
  };

  const isInRoster = roster.some((p) => p.share_token === activeToken);

  const handleAlertSelectPatient = (managedId: string) => {
    const managed = roster.find((p) => p.id === managedId);
    if (managed) handleRosterSelect(managed);
  };

  return (
    <div className="h-full">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: '#E8EDF5' }}>
          {profile?.user_role === 'caregiver' ? 'Family' : 'Patients'}
        </h1>
        <p className="mt-1 text-sm" style={{ color: '#526380' }}>
          {profile?.user_role === 'caregiver'
            ? 'Manage health summaries for family members you support'
            : 'View and manage your patient panel'}
        </p>
      </div>

      {!isProvider && (
        <div className="flex items-start gap-3 p-4 rounded-xl mb-6"
          style={{ backgroundColor: 'rgba(251,191,36,0.06)', border: '1px solid rgba(251,191,36,0.2)' }}>
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: '#FBB124' }} />
          <p className="text-sm" style={{ color: '#C8D5E8' }}>
            This page is designed for healthcare providers and caregivers. Set your account role to{' '}
            <strong>Provider</strong> or <strong>Caregiver</strong> in{' '}
            <Link href="/settings" className="underline" style={{ color: '#00D4AA' }}>Settings</Link>.
          </p>
        </div>
      )}

      {/* Out-of-range alerts banner */}
      {isProvider && alerts.length > 0 && (
        <AlertsBanner alerts={alerts} onSelectPatient={handleAlertSelectPatient} />
      )}

      {/* Two-column layout for providers */}
      {isProvider && (
        <div className="flex gap-5 min-h-[60vh]">
          {/* Left: Roster sidebar */}
          <div className="flex-shrink-0 w-64">
            <div className="p-4 rounded-xl h-full"
              style={{ backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
              {rosterLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-12 rounded-lg animate-pulse"
                      style={{ backgroundColor: 'rgba(255,255,255,0.05)' }} />
                  ))}
                </div>
              ) : (
                <RosterSidebar
                  roster={roster}
                  activeId={activeRosterId}
                  onSelect={handleRosterSelect}
                  onRemove={handleRemoveFromRoster}
                  onAddNew={() => { setShowAddPanel(true); setPatientData(null); setActiveRosterId(null); }}
                />
              )}
            </div>
          </div>

          {/* Right: Patient panel */}
          <div className="flex-1 min-w-0 space-y-4">
            {/* Add patient panel */}
            {(showAddPanel || !patientData) && (
              <AddPatientPanel
                onFound={handlePatientFound}
                onCancel={() => setShowAddPanel(false)}
                showCancel={roster.length > 0 && showAddPanel}
              />
            )}

            {/* Patient data */}
            {patientData && (
              <div className="rounded-xl p-5"
                style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
                {/* Header */}
                <div className="mb-5 pb-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                  {/* 6B: Viewing-as banner */}
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg mb-3"
                    style={{ backgroundColor: 'rgba(129,140,248,0.08)', border: '1px solid rgba(129,140,248,0.2)' }}>
                    <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: '#818CF8' }}>
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    <span className="text-xs" style={{ color: '#818CF8' }}>
                      Viewing <strong>{patientData.label || 'Patient'}</strong>'s shared health data — read-only
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                        style={{ background: 'rgba(0,212,170,0.1)' }}>
                        <HeartPulse className="w-5 h-5" style={{ color: '#00D4AA' }} />
                      </div>
                      <div>
                        <h2 className="font-semibold" style={{ color: '#E8EDF5' }}>
                          {patientData.label || 'Patient Summary'}
                        </h2>
                        <p className="text-xs flex items-center gap-1.5 mt-0.5" style={{ color: '#526380' }}>
                          <Clock className="w-3 h-3" />
                          {new Date(patientData.generated_at).toLocaleString()}
                        </p>
                      </div>
                    </div>

                    {/* Save to roster button (if not yet saved) */}
                    {!isInRoster && (
                      <button onClick={handleSaveToRoster} disabled={savingToRoster}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium disabled:opacity-40 transition-colors"
                        style={{ backgroundColor: 'rgba(0,212,170,0.1)', color: '#00D4AA', border: '1px solid rgba(0,212,170,0.2)' }}>
                        <UserPlus className="w-3.5 h-3.5" />
                        {savingToRoster ? 'Saving…' : 'Save to roster'}
                      </button>
                    )}
                  </div>

                  {/* 6E: Visit Prep shortcut */}
                  <Link href="/doctor-prep"
                    className="flex items-center gap-2 mt-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors hover:brightness-110"
                    style={{ backgroundColor: 'rgba(0,212,170,0.08)', color: '#00D4AA', border: '1px solid rgba(0,212,170,0.2)' }}>
                    <FileText className="w-4 h-4" />
                    Generate Visit Prep Report
                    <ChevronRight className="w-3.5 h-3.5 ml-auto" />
                  </Link>
                </div>

                <PatientSummaryPanel data={patientData} />

                {isProvider && activeToken && patientData.permissions.includes('care_plans') && (
                  <SuggestCarePlanPanel
                    shareToken={activeToken}
                    onSuccess={() => {
                      sharingService.getPublicSummary(activeToken).then(setPatientData).catch(() => {});
                    }}
                  />
                )}
              </div>
            )}

            {/* Empty right-col state */}
            {!patientData && !showAddPanel && (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
                  style={{ background: 'rgba(0,212,170,0.08)' }}>
                  <Users className="w-8 h-8" style={{ color: '#00D4AA' }} />
                </div>
                <p className="text-sm" style={{ color: '#526380' }}>
                  Select a patient from the roster or add a new one
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Non-provider fallback */}
      {!isProvider && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
            style={{ background: 'rgba(0,212,170,0.08)' }}>
            <Users className="w-8 h-8" style={{ color: '#00D4AA' }} />
          </div>
          <p className="text-sm" style={{ color: '#526380' }}>
            Ask your patient to share their health data from Settings → Share with Care Team,
            then set your role to Provider to access the full panel.
          </p>
        </div>
      )}
    </div>
  );
}
