'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Activity, AlertTriangle, HeartPulse } from 'lucide-react';
import { sharingService } from '@/services/sharing';
import type { SharedHealthSummary } from '@/types';

// ── Small UI helpers ──────────────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      className="rounded-xl p-5"
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.07)',
      }}
    >
      <h2 className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: '#526380' }}>
        {title}
      </h2>
      {children}
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 py-1.5 border-b last:border-b-0" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
      <span className="text-sm" style={{ color: '#526380' }}>{label}</span>
      <span className="text-sm font-medium text-right" style={{ color: '#C8D5E8' }}>{value}</span>
    </div>
  );
}

function Badge({ text, variant = 'default' }: { text: string; variant?: 'default' | 'warning' | 'teal' }) {
  const colors = {
    default: 'rgba(255,255,255,0.06)',
    warning: 'rgba(248,113,113,0.15)',
    teal: 'rgba(0,212,170,0.15)',
  };
  const textColors = { default: '#8B97A8', warning: '#F87171', teal: '#00D4AA' };
  return (
    <span
      className="text-[11px] font-medium px-2 py-0.5 rounded-full"
      style={{ backgroundColor: colors[variant], color: textColors[variant] }}
    >
      {text}
    </span>
  );
}

function calcAge(dob?: string): string {
  if (!dob) return '—';
  const d = new Date(dob);
  const now = new Date();
  let age = now.getFullYear() - d.getFullYear();
  if (now.getMonth() < d.getMonth() || (now.getMonth() === d.getMonth() && now.getDate() < d.getDate())) age--;
  return `${age} yrs`;
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function SharePage() {
  const params = useParams();
  const token = params?.token as string;

  const [data, setData] = useState<SharedHealthSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    sharingService
      .getPublicSummary(token)
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  // Dark base
  const bg = '#080B10';
  const text = '#E8EDF5';

  return (
    <div className="min-h-screen" style={{ backgroundColor: bg, color: text, fontFamily: 'system-ui, sans-serif' }}>
      {/* Header */}
      <div
        className="flex items-center gap-3 px-6 py-4 sticky top-0 z-10"
        style={{ backgroundColor: bg, borderBottom: '1px solid rgba(255,255,255,0.06)' }}
      >
        <div className="flex items-center justify-center w-8 h-8 rounded-lg" style={{ background: 'rgba(0,212,170,0.1)' }}>
          <Activity className="w-4 h-4" style={{ color: '#00D4AA' }} />
        </div>
        <span className="text-sm font-semibold" style={{ color: '#E8EDF5' }}>
          Health<span style={{ color: '#00D4AA' }}>AI</span>
        </span>
        <span className="ml-auto text-xs" style={{ color: '#526380' }}>
          Read-only health summary
        </span>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-8">
        {loading && (
          <div className="flex items-center justify-center py-24">
            <div className="w-8 h-8 rounded-full border-2 border-[#00D4AA] border-t-transparent animate-spin" />
          </div>
        )}

        {error && (
          <div
            className="flex items-start gap-3 p-4 rounded-xl"
            style={{ backgroundColor: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.2)' }}
          >
            <AlertTriangle className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: '#F87171' }} />
            <div>
              <p className="font-medium" style={{ color: '#F87171' }}>Unable to load health summary</p>
              <p className="text-sm mt-1" style={{ color: '#8B97A8' }}>{error}</p>
            </div>
          </div>
        )}

        {data && (
          <div className="space-y-4">
            {/* Title */}
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center" style={{ background: 'rgba(0,212,170,0.1)' }}>
                <HeartPulse className="w-6 h-6" style={{ color: '#00D4AA' }} />
              </div>
              <div>
                <h1 className="text-xl font-semibold" style={{ color: '#E8EDF5' }}>
                  {data.label ? `${data.label} — Health Summary` : 'Health Summary'}
                </h1>
                <p className="text-sm" style={{ color: '#526380' }}>
                  Generated {new Date(data.generated_at).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Profile */}
            {data.profile && (
              <Section title="Profile">
                <Row label="Age" value={calcAge(data.profile.date_of_birth as string)} />
                {data.profile.biological_sex != null ? (
                  <Row label="Biological Sex" value={String(data.profile.biological_sex)} />
                ) : null}
                {data.profile.weight_kg != null ? (
                  <Row label="Weight" value={`${Number(data.profile.weight_kg)} kg`} />
                ) : null}
                {data.conditions && data.conditions.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs mb-2" style={{ color: '#526380' }}>Conditions</p>
                    <div className="flex flex-wrap gap-1.5">
                      {data.conditions.map((c, i) => <Badge key={i} text={c} />)}
                    </div>
                  </div>
                )}
              </Section>
            )}

            {/* Medications */}
            {data.medications && data.medications.length > 0 && (
              <Section title="Active Medications">
                {data.medication_adherence_pct !== undefined && (
                  <div className="mb-3 flex items-center gap-2">
                    <span className="text-sm" style={{ color: '#526380' }}>30-day adherence</span>
                    <span
                      className="text-sm font-semibold px-2 py-0.5 rounded"
                      style={{
                        backgroundColor: data.medication_adherence_pct >= 80 ? 'rgba(0,212,170,0.15)' : 'rgba(248,113,113,0.15)',
                        color: data.medication_adherence_pct >= 80 ? '#00D4AA' : '#F87171',
                      }}
                    >
                      {data.medication_adherence_pct}%
                    </span>
                  </div>
                )}
                <div className="space-y-2">
                  {data.medications.map((m, i) => (
                    <div key={i} className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium" style={{ color: '#C8D5E8' }}>{m.name}</p>
                        {m.dosage && <p className="text-xs" style={{ color: '#526380' }}>{m.dosage}{m.frequency ? ` · ${m.frequency}` : ''}</p>}
                      </div>
                      {m.prescribed_by && <Badge text={`Rx: ${m.prescribed_by}`} variant="teal" />}
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* Lab Results */}
            {data.lab_results && data.lab_results.length > 0 && (
              <Section title="Recent Lab Results">
                <div className="space-y-2">
                  {data.lab_results.slice(0, 20).map((lab, i) => (
                    <div key={i} className="flex items-center justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm" style={{ color: '#C8D5E8' }}>{lab.test_name}</p>
                        <p className="text-xs" style={{ color: '#526380' }}>{lab.test_date}</p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="text-sm font-medium" style={{ color: lab.is_abnormal ? '#F87171' : '#C8D5E8' }}>
                          {lab.value !== undefined ? `${lab.value}${lab.unit ? ' ' + lab.unit : ''}` : '—'}
                        </span>
                        {lab.is_abnormal && <Badge text="Abnormal" variant="warning" />}
                        {lab.reference_range && (
                          <span className="text-[11px]" style={{ color: '#526380' }}>{lab.reference_range}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* Symptoms */}
            {data.symptoms && data.symptoms.length > 0 && (
              <Section title="Recent Symptoms (30 days)">
                {data.avg_symptom_severity !== undefined && (
                  <Row label="Avg severity" value={`${data.avg_symptom_severity} / 10`} />
                )}
                <div className="mt-3 space-y-2">
                  {data.symptoms.slice(0, 15).map((s, i) => (
                    <div key={i} className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm" style={{ color: '#C8D5E8' }}>{s.symptom_name}</p>
                        {s.notes && <p className="text-xs truncate" style={{ color: '#526380' }}>{s.notes}</p>}
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {s.severity !== undefined && (
                          <span
                            className="text-xs font-medium px-1.5 py-0.5 rounded"
                            style={{
                              backgroundColor: s.severity >= 7 ? 'rgba(248,113,113,0.15)' : s.severity >= 4 ? 'rgba(251,191,36,0.15)' : 'rgba(0,212,170,0.1)',
                              color: s.severity >= 7 ? '#F87171' : s.severity >= 4 ? '#FBB124' : '#00D4AA',
                            }}
                          >
                            {s.severity}/10
                          </span>
                        )}
                        <span className="text-xs" style={{ color: '#526380' }}>{s.date}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* Care Plans */}
            {data.care_plans && data.care_plans.length > 0 && (
              <Section title="Active Care Plans">
                <div className="space-y-2">
                  {data.care_plans.map((plan, i) => (
                    <div key={i} className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium" style={{ color: '#C8D5E8' }}>{plan.title}</p>
                        {plan.target_value !== undefined && (
                          <p className="text-xs" style={{ color: '#526380' }}>
                            Target: {plan.target_value} {plan.target_unit ?? ''}
                            {plan.target_date ? ` by ${plan.target_date}` : ''}
                          </p>
                        )}
                      </div>
                      {plan.source === 'doctor' && <Badge text="Doctor" variant="teal" />}
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* Insights */}
            {data.insights && data.insights.length > 0 && (
              <Section title="AI Insights">
                <div className="space-y-3">
                  {data.insights.map((ins, i) => (
                    <div key={i} className="border-b last:border-b-0 pb-3 last:pb-0" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
                      <p className="text-sm font-medium mb-1" style={{ color: '#C8D5E8' }}>{ins.title}</p>
                      {ins.summary && <p className="text-xs leading-relaxed" style={{ color: '#8B97A8' }}>{ins.summary}</p>}
                      <p className="text-[11px] mt-1.5" style={{ color: '#3D4F66' }}>
                        {new Date(ins.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* Footer */}
            <p className="text-center text-xs pt-4 pb-8" style={{ color: '#3D4F66' }}>
              This is a read-only snapshot shared securely via HealthAI. Data is current as of generation time.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
