'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Activity, AlertTriangle, HeartPulse, TrendingUp, TrendingDown, FlaskConical, UserPlus, CheckCircle2, Sparkles, Stethoscope, Pill, Microscope, Dna, ScanLine, ShieldCheck, Watch, Apple, FileText, MessageSquare, Calendar, BookOpen } from 'lucide-react';
import { sharingService } from '@/services/sharing';
import { supabase } from '@/lib/supabase';
import { api } from '@/services/api';
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
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [addedToPatients, setAddedToPatients] = useState(false);
  const [addingToPatients, setAddingToPatients] = useState(false);

  useEffect(() => {
    if (!token) return;
    sharingService
      .getPublicSummary(token)
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));

    // Check if user is authenticated (for "Add to Patients" CTA)
    supabase.auth.getSession().then(({ data: { session } }) => {
      setIsAuthenticated(Boolean(session?.user));
    });
  }, [token]);

  async function handleAddToPatients() {
    setAddingToPatients(true);
    try {
      await api.post('/api/v1/caregiver/managed', { token });
      setAddedToPatients(true);
    } catch {
      // Might already be linked or other error
      setAddedToPatients(true);
    } finally {
      setAddingToPatients(false);
    }
  }

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
        <span className="ml-auto flex items-center gap-3">
          <span className="text-xs" style={{ color: '#526380' }}>Read-only health summary</span>
          {isAuthenticated && !addedToPatients && (
            <button
              onClick={handleAddToPatients}
              disabled={addingToPatients}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
              style={{ backgroundColor: 'rgba(0,212,170,0.15)', color: '#00D4AA', border: '1px solid rgba(0,212,170,0.3)' }}
            >
              <UserPlus style={{ width: 14, height: 14 }} />
              {addingToPatients ? 'Adding...' : 'Add to My Patients'}
            </button>
          )}
          {addedToPatients && (
            <span className="flex items-center gap-1 text-xs" style={{ color: '#6EE7B7' }}>
              <CheckCircle2 style={{ width: 14, height: 14 }} />
              Added
            </span>
          )}
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

            {/* Experiments */}
            {data.interventions && data.interventions.length > 0 && (
              <Section title="Personal Experiments (90 days)">
                <p className="text-xs mb-4 leading-relaxed" style={{ color: '#526380' }}>
                  Self-tracked experiments testing the effect of dietary and lifestyle changes on health metrics. Patient-observed · not clinically verified.
                </p>
                <div className="space-y-4">
                  {data.interventions.map((iv, i) => {
                    const deltaPairs = Object.entries(iv.outcome_delta || {}).filter(([, v]) => Math.abs(v) > 1);
                    const pattern = iv.recommendation_pattern?.replace(/_/g, ' ') ?? '';
                    return (
                      <div
                        key={i}
                        className="rounded-lg p-3"
                        style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}
                      >
                        <div className="flex items-start gap-2 mb-2">
                          <FlaskConical className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: '#00D4AA' }} />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium" style={{ color: '#C8D5E8' }}>{iv.title}</p>
                            <p className="text-xs capitalize mt-0.5" style={{ color: '#526380' }}>
                              {pattern} · {iv.duration_days}d trial · {iv.adherence_pct.toFixed(0)}% adherence
                              {iv.completed_at ? ` · completed ${new Date(iv.completed_at).toLocaleDateString()}` : ''}
                            </p>
                          </div>
                        </div>
                        {iv.outcome_summary && (
                          <p className="text-xs leading-relaxed mb-2 italic" style={{ color: '#8B97A8' }}>
                            {iv.outcome_summary}
                          </p>
                        )}
                        {deltaPairs.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-1">
                            {deltaPairs
                              .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
                              .slice(0, 6)
                              .map(([metric, pct]) => {
                                const isPos = pct > 0;
                                const label = metric.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
                                return (
                                  <span
                                    key={metric}
                                    className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full"
                                    style={{
                                      backgroundColor: isPos ? 'rgba(0,212,170,0.12)' : 'rgba(248,113,113,0.12)',
                                      color: isPos ? '#00D4AA' : '#F87171',
                                    }}
                                  >
                                    {isPos
                                      ? <TrendingUp className="w-2.5 h-2.5" />
                                      : <TrendingDown className="w-2.5 h-2.5" />
                                    }
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
              </Section>
            )}

            {/* Medical Records */}
            {data.medical_records && data.medical_records.length > 0 && (
              <Section title="Medical Records">
                <div className="space-y-3">
                  {data.medical_records.map((rec, i) => {
                    const typeColor = rec.record_type === 'genomic' ? '#818CF8' : rec.record_type === 'pathology' ? '#F87171' : '#60A5FA';
                    const TypeIcon = rec.record_type === 'genomic' ? Dna : rec.record_type === 'pathology' ? Microscope : ScanLine;
                    return (
                      <div key={i} className="border-b last:border-b-0 pb-3 last:pb-0" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
                        <div className="flex items-center gap-2 mb-1">
                          <TypeIcon className="w-3.5 h-3.5" style={{ color: typeColor }} />
                          <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: typeColor }}>
                            {rec.record_type}
                          </span>
                          {rec.report_date && <span className="text-[11px] ml-auto" style={{ color: '#3D4F66' }}>{rec.report_date}</span>}
                        </div>
                        <p className="text-sm font-medium" style={{ color: '#C8D5E8' }}>{rec.title}</p>
                        {rec.ai_summary && <p className="text-xs mt-1 leading-relaxed italic" style={{ color: '#8B97A8' }}>{rec.ai_summary}</p>}
                      </div>
                    );
                  })}
                </div>
              </Section>
            )}

            {/* AI Medication Recommendations */}
            {data.medication_recommendations && data.medication_recommendations.length > 0 && (
              <Section title="AI Treatment Recommendations">
                {data.medication_recommendations_summary && (
                  <div className="flex items-start gap-2 mb-4 p-3 rounded-lg" style={{ backgroundColor: 'rgba(0,212,170,0.05)', border: '1px solid rgba(0,212,170,0.1)' }}>
                    <Sparkles className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#00D4AA' }} />
                    <p className="text-xs leading-relaxed" style={{ color: '#8B97A8' }}>{data.medication_recommendations_summary}</p>
                  </div>
                )}
                <div className="space-y-3">
                  {data.medication_recommendations.map((rec, i) => {
                    const priorityColor = rec.priority === 'high' ? '#F87171' : rec.priority === 'medium' ? '#FBBF24' : '#60A5FA';
                    const evidenceColor = rec.evidence_level === 'strong' ? '#6EE7B7' : rec.evidence_level === 'moderate' ? '#FBBF24' : '#60A5FA';
                    const CatIcon = rec.category === 'prescription' ? Stethoscope : rec.category === 'supplement' ? FlaskConical : Pill;
                    return (
                      <div key={i} className="rounded-lg p-3" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <div className="flex items-start gap-2.5">
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ backgroundColor: `${priorityColor}15` }}>
                            <CatIcon className="w-4 h-4" style={{ color: priorityColor }} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-sm font-medium" style={{ color: '#C8D5E8' }}>{rec.name}</span>
                              <Badge text={rec.priority === 'high' ? 'High Priority' : rec.priority === 'medium' ? 'Medium' : 'Low'} variant={rec.priority === 'high' ? 'warning' : 'default'} />
                              <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ backgroundColor: `${evidenceColor}15`, color: evidenceColor }}>
                                {rec.evidence_level} evidence
                              </span>
                              {rec.discuss_with_doctor && (
                                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ backgroundColor: 'rgba(168,85,247,0.12)', color: '#C084FC' }}>
                                  Rx — discuss with doctor
                                </span>
                              )}
                            </div>
                            <p className="text-xs mt-1 leading-relaxed" style={{ color: '#8B97A8' }}>{rec.rationale}</p>
                            {(rec.efficacy || rec.estimated_cost) && (
                              <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1.5">
                                {rec.efficacy && (
                                  <span className="text-[11px]" style={{ color: '#6EE7B7' }}>Efficacy: {rec.efficacy}</span>
                                )}
                                {rec.estimated_cost && (
                                  <span className="text-[11px]" style={{ color: '#8B97A8' }}>Cost: {rec.estimated_cost}</span>
                                )}
                              </div>
                            )}
                            {rec.relevant_data && (
                              <p className="text-[11px] mt-1" style={{ color: '#526380' }}>Based on: {rec.relevant_data}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="flex items-start gap-2 mt-4 p-3 rounded-lg" style={{ backgroundColor: 'rgba(251,191,36,0.05)', border: '1px solid rgba(251,191,36,0.1)' }}>
                  <ShieldCheck className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#FBBF24' }} />
                  <p className="text-[11px] leading-relaxed" style={{ color: '#526380' }}>
                    AI-generated suggestions for clinical discussion. Not a substitute for professional medical advice.
                  </p>
                </div>
              </Section>
            )}

            {/* Wearable Health Data */}
            {data.wearable_data && data.wearable_data.length > 0 && (
              <Section title="Wearable Health Data">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {data.wearable_data.map((m: any, i: number) => {
                    const trendIcon = m.trend === 'up' ? TrendingUp : m.trend === 'down' ? TrendingDown : null;
                    const trendColor = m.trend === 'up' ? '#6EE7B7' : m.trend === 'down' ? '#F87171' : '#526380';
                    return (
                      <div key={i} className="rounded-lg p-3" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <div className="flex items-center gap-1.5 mb-1">
                          <Watch className="w-3 h-3" style={{ color: '#818CF8' }} />
                          <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: '#818CF8' }}>
                            {(m.metric || '').replace(/_/g, ' ')}
                          </span>
                        </div>
                        <p className="text-lg font-medium" style={{ color: '#E8EDF5' }}>
                          {m.latest_value ?? m.value ?? m.score ?? '—'}{m.unit ? ` ${m.unit}` : ''}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          {m.avg_30d != null && <span className="text-[11px]" style={{ color: '#526380' }}>30d avg: {Math.round(m.avg_30d)}</span>}
                          {trendIcon && (() => { const TIcon = trendIcon; return <TIcon className="w-3 h-3" style={{ color: trendColor }} />; })()}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Section>
            )}

            {/* Specialist Recommendations */}
            {data.specialist_recs && data.specialist_recs.length > 0 && (
              <Section title="Specialist AI Recommendations">
                <div className="space-y-3">
                  {data.specialist_recs.map((rec: any, i: number) => (
                    <div key={i} className="border-b last:border-b-0 pb-3 last:pb-0" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
                      <div className="flex items-center gap-2 mb-1">
                        <MessageSquare className="w-3.5 h-3.5" style={{ color: '#00D4AA' }} />
                        <span className="text-sm font-medium" style={{ color: '#C8D5E8' }}>{rec.agent_name}</span>
                        {rec.last_updated && <span className="text-[11px] ml-auto" style={{ color: '#3D4F66' }}>{new Date(rec.last_updated).toLocaleDateString()}</span>}
                      </div>
                      <p className="text-xs leading-relaxed" style={{ color: '#8B97A8' }}>{rec.summary}</p>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* Nutrition & Meals */}
            {data.nutrition && data.nutrition.length > 0 && (
              <Section title="Nutrition & Meals (14 days)">
                <div className="space-y-2">
                  {data.nutrition.slice(0, 20).map((meal: any, i: number) => (
                    <div key={i} className="flex items-center justify-between gap-2 border-b last:border-b-0 pb-2 last:pb-0" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
                      <div className="flex items-center gap-2">
                        <Apple className="w-3.5 h-3.5" style={{ color: '#6EE7B7' }} />
                        <div>
                          <span className="text-sm" style={{ color: '#C8D5E8' }}>
                            {meal.meal_type}{meal.food_items?.length ? ` · ${Array.isArray(meal.food_items) ? meal.food_items.map((f: any) => typeof f === 'string' ? f : f.name || f.food_name || '').filter(Boolean).slice(0, 3).join(', ') : ''}` : ''}
                          </span>
                          <p className="text-[11px]" style={{ color: '#526380' }}>{meal.date}</p>
                        </div>
                      </div>
                      {meal.calories != null && (
                        <span className="text-xs whitespace-nowrap" style={{ color: '#8B97A8' }}>
                          {Math.round(meal.calories)} cal · {Math.round(meal.protein_g ?? 0)}P / {Math.round(meal.carbs_g ?? 0)}C / {Math.round(meal.fat_g ?? 0)}F
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* Cycle Tracking */}
            {data.cycle_tracking && data.cycle_tracking.length > 0 && (
              <Section title="Menstrual Cycle Data">
                <div className="space-y-2">
                  {data.cycle_tracking.map((c: any, i: number) => (
                    <div key={i} className="flex items-center justify-between border-b last:border-b-0 pb-2 last:pb-0" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
                      <div className="flex items-center gap-2">
                        <Calendar className="w-3.5 h-3.5" style={{ color: '#F9A8D4' }} />
                        <span className="text-sm" style={{ color: '#C8D5E8' }}>{c.cycle_start}{c.cycle_end ? ` — ${c.cycle_end}` : ''}</span>
                      </div>
                      <div className="flex gap-3">
                        {c.cycle_length && <span className="text-xs" style={{ color: '#8B97A8' }}>{c.cycle_length}d cycle</span>}
                        {c.period_length && <span className="text-xs" style={{ color: '#F9A8D4' }}>{c.period_length}d period</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* Clinical Research */}
            {data.clinical_research && (
              <Section title="Clinical Research">
                {Array.isArray((data.clinical_research?.personalized_topics as any)?.topics) && ((data.clinical_research?.personalized_topics as any).topics as any[]).length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: '#818CF8' }}>Personalized Research Topics</p>
                    <div className="space-y-2">
                      {((data.clinical_research?.personalized_topics as any).topics as any[]).map((t: any, i: number) => (
                        <div key={i} className="rounded-lg p-3" style={{ backgroundColor: 'rgba(129,140,248,0.05)', border: '1px solid rgba(129,140,248,0.1)' }}>
                          <div className="flex items-center gap-2 mb-1">
                            <BookOpen className="w-3.5 h-3.5" style={{ color: '#818CF8' }} />
                            <span className="text-sm font-medium" style={{ color: '#C8D5E8' }}>{t.title}</span>
                          </div>
                          {t.description && <p className="text-xs leading-relaxed" style={{ color: '#8B97A8' }}>{t.description}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {data.clinical_research.saved_reports && data.clinical_research.saved_reports.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: '#526380' }}>Saved Research Reports</p>
                    <div className="space-y-2">
                      {data.clinical_research.saved_reports.map((r: any, i: number) => (
                        <div key={i} className="flex items-center justify-between border-b last:border-b-0 pb-2 last:pb-0" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
                          <span className="text-sm" style={{ color: '#C8D5E8' }}>{r.query}</span>
                          <span className="text-[11px]" style={{ color: '#3D4F66' }}>{r.created_at ? new Date(r.created_at).toLocaleDateString() : ''}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Section>
            )}

            {/* Doctor Prep Report */}
            {data.doctor_prep && (
              <Section title="Visit Prep Report">
                <div className="flex items-start gap-2 p-3 rounded-lg mb-3" style={{ backgroundColor: 'rgba(0,212,170,0.05)', border: '1px solid rgba(0,212,170,0.1)' }}>
                  <FileText className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#00D4AA' }} />
                  <p className="text-xs leading-relaxed" style={{ color: '#8B97A8' }}>
                    A comprehensive health report was generated for this patient. Key data points from the report are included throughout other sections above.
                  </p>
                </div>
                {(data.doctor_prep as any)?.summary?.concerns?.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: '#F5A623' }}>Concerns</p>
                    <ul className="space-y-1">
                      {((data.doctor_prep as any).summary.concerns as string[]).map((c, i) => (
                        <li key={i} className="text-xs flex items-start gap-1.5" style={{ color: '#8B97A8' }}>
                          <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" style={{ color: '#F5A623' }} />
                          {c}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {(data.doctor_prep as any)?.summary?.improvements?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: '#6EE7B7' }}>Positive Progress</p>
                    <ul className="space-y-1">
                      {((data.doctor_prep as any).summary.improvements as string[]).map((imp, i) => (
                        <li key={i} className="text-xs flex items-start gap-1.5" style={{ color: '#8B97A8' }}>
                          <CheckCircle2 className="w-3 h-3 mt-0.5 shrink-0" style={{ color: '#6EE7B7' }} />
                          {imp}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
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
