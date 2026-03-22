'use client';

import { useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { medicationsService } from '@/services/medications';
import { useAuth } from '@/hooks/useAuth';
import {
  Plus, Pill, Edit, Trash2, AlertCircle,
  Camera, Upload, X, CheckCircle2, Loader2,
  Sparkles, Shield, Stethoscope, FlaskConical,
  ArrowRight, ShieldCheck, Share2, Link2, FileText,
} from 'lucide-react';
import { EmptyState } from '@/components/ui/EmptyState';
import { DailyAdherenceStrip } from './DailyAdherenceStrip';
import { AdherenceCalendar } from './AdherenceCalendar';
import { StreakBadges } from './StreakBadges';
import { api } from '@/services/api';
import type {
  Medication,
  Supplement,
  CreateMedicationRequest,
  CreateSupplementRequest,
  PrescriptionScanResult,
} from '@/types';
import toast from 'react-hot-toast';

// ── Shared input style ────────────────────────────────────────────────────────

const inputCls =
  'w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg ' +
  'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 ' +
  'focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors';

// ── Prescription Scan Modal ──────────────────────────────────────────────────

type ScanTarget = 'medication' | 'supplement';

function PrescriptionScanModal({
  target,
  onClose,
  onApply,
}: {
  target: ScanTarget;
  onClose: () => void;
  onApply: (result: PrescriptionScanResult) => void;
}) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<PrescriptionScanResult | null>(null);

  // Editable extracted fields — we merge scan result in, user can change anything
  const [name, setName] = useState('');
  const [genericName, setGenericName] = useState('');
  const [dosage, setDosage] = useState('');
  const [frequency, setFrequency] = useState('');
  const [route, setRoute] = useState('oral');
  const [indication, setIndication] = useState('');
  const [doctor, setDoctor] = useState('');
  const [pharmacy, setPharmacy] = useState('');
  const [rxNumber, setRxNumber] = useState('');
  const [notes, setNotes] = useState('');
  const [brand, setBrand] = useState('');
  const [form, setForm] = useState('capsule');
  const [purpose, setPurpose] = useState('');

  const scanMutation = useMutation({
    mutationFn: (f: File) => medicationsService.scanPrescription(f),
    onSuccess: (res) => {
      setResult(res);
      // Pre-populate editable state
      setName(res.medication_name ?? '');
      setGenericName(res.generic_name ?? '');
      setDosage(res.dosage ?? '');
      setFrequency(res.frequency ?? '');
      setRoute(res.route ?? 'oral');
      setIndication(res.indication ?? '');
      setDoctor(res.prescribing_doctor ?? '');
      setPharmacy(res.pharmacy ?? '');
      setRxNumber(res.prescription_number ?? '');
      setNotes(res.notes ?? '');
      setBrand(res.brand ?? '');
      setForm(res.form ?? 'capsule');
      setPurpose(res.purpose ?? '');
    },
    onError: (e: unknown) => {
      const msg = e instanceof Error ? e.message : 'Scan failed';
      toast.error(msg);
    },
  });

  const handleFile = (f: File) => {
    setFile(f);
    setResult(null);
    const url = URL.createObjectURL(f);
    setPreview(url);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f && f.type.startsWith('image/')) handleFile(f);
  };

  const handleApply = () => {
    if (!result) return;
    const isSupplement = result.is_supplement || target === 'supplement';
    onApply({
      ...result,
      is_supplement: isSupplement,
      medication_name: name,
      generic_name: genericName || undefined,
      dosage,
      frequency,
      route,
      indication: indication || undefined,
      prescribing_doctor: doctor || undefined,
      pharmacy: pharmacy || undefined,
      prescription_number: rxNumber || undefined,
      notes: notes || undefined,
      brand: brand || undefined,
      form: form || undefined,
      purpose: purpose || undefined,
    });
  };

  const confidencePct = result ? Math.round(result.confidence * 100) : 0;
  const confColor =
    confidencePct >= 80 ? 'text-green-600 dark:text-green-400' :
    confidencePct >= 50 ? 'text-yellow-600 dark:text-yellow-400' :
                          'text-red-600 dark:text-red-400';

  const isSupplement = result?.is_supplement || target === 'supplement';

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <Camera className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                Scan Prescription / Bottle
              </h2>
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* ── Phase 1: Upload ─────────────────────────────────────── */}
          {!result && (
            <>
              {/* Drop zone */}
              <div
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                onClick={() => !file && fileRef.current?.click()}
                className={`relative border-2 border-dashed rounded-xl overflow-hidden transition-colors cursor-pointer ${
                  file
                    ? 'border-primary-400 dark:border-primary-500'
                    : 'border-slate-300 dark:border-slate-600 hover:border-primary-400 dark:hover:border-primary-500'
                }`}
                style={{ minHeight: 200 }}
              >
                {preview ? (
                  <div className="relative">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={preview} alt="Preview" className="w-full max-h-64 object-contain bg-slate-100 dark:bg-slate-900" />
                    <button
                      onClick={(e) => { e.stopPropagation(); setFile(null); setPreview(null); }}
                      className="absolute top-2 right-2 w-7 h-7 rounded-full bg-black/50 flex items-center justify-center text-white hover:bg-black/70"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center gap-3 p-8 text-center">
                    <Upload className="w-10 h-10 text-slate-400" />
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                      Drop an image here or click to browse
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      Prescription label · Supplement bottle · Pill strip · Doctor's script
                    </p>
                  </div>
                )}
              </div>

              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                capture="environment"
                className="hidden"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
              />

              <div className="flex gap-3 mt-4">
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  onClick={() => { if (fileRef.current) { fileRef.current.removeAttribute('capture'); fileRef.current.click(); } }}
                >
                  <Upload className="w-4 h-4 mr-1.5" />
                  Gallery
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  onClick={() => { if (fileRef.current) { fileRef.current.setAttribute('capture', 'environment'); fileRef.current.click(); } }}
                >
                  <Camera className="w-4 h-4 mr-1.5" />
                  Camera
                </Button>
              </div>

              <div className="flex gap-3 mt-3">
                <Button type="button" variant="outline" onClick={onClose} className="flex-1">
                  Cancel
                </Button>
                <Button
                  type="button"
                  className="flex-1"
                  disabled={!file || scanMutation.isPending}
                  onClick={() => file && scanMutation.mutate(file)}
                >
                  {scanMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                      Extracting…
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-1.5" />
                      Extract Details
                    </>
                  )}
                </Button>
              </div>
            </>
          )}

          {/* ── Phase 2: Editable Results ───────────────────────────── */}
          {result && (
            <>
              {/* Preview + confidence banner */}
              <div className="flex items-start gap-3 mb-5 p-3 rounded-xl bg-slate-50 dark:bg-slate-700/50">
                {preview && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={preview} alt="Scan" className="w-16 h-16 object-cover rounded-lg flex-shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                    <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                      Extracted from image
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1">
                    <span className={`text-xs font-medium ${confColor}`}>
                      {confidencePct}% confidence
                    </span>
                    {result.image_type && result.image_type !== 'unknown' && (
                      <span className="text-xs text-slate-500 dark:text-slate-400 capitalize">
                        {result.image_type.replace(/_/g, ' ')}
                      </span>
                    )}
                    {isSupplement && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                        Supplement
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                    Review and correct the fields below before saving.
                  </p>
                </div>
                <button
                  onClick={() => { setResult(null); }}
                  className="text-slate-400 hover:text-slate-600 flex-shrink-0"
                  title="Rescan"
                >
                  <Camera className="w-4 h-4" />
                </button>
              </div>

              {/* Editable form */}
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    {isSupplement ? 'Supplement Name' : 'Medication Name'} *
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className={inputCls}
                    placeholder={isSupplement ? 'e.g., Vitamin D3' : 'e.g., Lisinopril'}
                  />
                </div>

                {!isSupplement && (
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Generic Name
                    </label>
                    <input
                      type="text"
                      value={genericName}
                      onChange={(e) => setGenericName(e.target.value)}
                      className={inputCls}
                      placeholder="e.g., lisinopril"
                    />
                  </div>
                )}

                {isSupplement && (
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Brand
                    </label>
                    <input
                      type="text"
                      value={brand}
                      onChange={(e) => setBrand(e.target.value)}
                      className={inputCls}
                      placeholder="e.g., Nature Made"
                    />
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Dosage *
                    </label>
                    <input
                      type="text"
                      value={dosage}
                      onChange={(e) => setDosage(e.target.value)}
                      className={inputCls}
                      placeholder="e.g., 10mg"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Frequency *
                    </label>
                    <input
                      type="text"
                      value={frequency}
                      onChange={(e) => setFrequency(e.target.value)}
                      className={inputCls}
                      placeholder="e.g., once daily"
                    />
                  </div>
                </div>

                {!isSupplement ? (
                  <>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                          Route
                        </label>
                        <select value={route} onChange={(e) => setRoute(e.target.value)} className={inputCls}>
                          <option value="oral">Oral</option>
                          <option value="topical">Topical</option>
                          <option value="injection">Injection</option>
                          <option value="inhaled">Inhaled</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                          Indication (what for)
                        </label>
                        <input
                          type="text"
                          value={indication}
                          onChange={(e) => setIndication(e.target.value)}
                          className={inputCls}
                          placeholder="e.g., hypertension"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                          Prescribing Doctor
                        </label>
                        <input
                          type="text"
                          value={doctor}
                          onChange={(e) => setDoctor(e.target.value)}
                          className={inputCls}
                          placeholder="Dr. Smith"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                          Pharmacy
                        </label>
                        <input
                          type="text"
                          value={pharmacy}
                          onChange={(e) => setPharmacy(e.target.value)}
                          className={inputCls}
                          placeholder="CVS, Walgreens…"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                        Rx / Prescription Number
                      </label>
                      <input
                        type="text"
                        value={rxNumber}
                        onChange={(e) => setRxNumber(e.target.value)}
                        className={inputCls}
                        placeholder="e.g., 1234567"
                      />
                    </div>
                  </>
                ) : (
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                        Form
                      </label>
                      <select value={form} onChange={(e) => setForm(e.target.value)} className={inputCls}>
                        <option value="capsule">Capsule</option>
                        <option value="tablet">Tablet</option>
                        <option value="powder">Powder</option>
                        <option value="liquid">Liquid</option>
                        <option value="gummy">Gummy</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                        Purpose
                      </label>
                      <input
                        type="text"
                        value={purpose}
                        onChange={(e) => setPurpose(e.target.value)}
                        className={inputCls}
                        placeholder="e.g., bone health"
                      />
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Notes / Instructions
                  </label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={2}
                    className={inputCls}
                    placeholder="Warnings, storage, food interactions…"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-5">
                <Button type="button" variant="outline" onClick={onClose} className="flex-1">
                  Cancel
                </Button>
                <Button
                  type="button"
                  className="flex-1"
                  disabled={!name.trim() || !dosage.trim() || !frequency.trim()}
                  onClick={handleApply}
                >
                  Use {isSupplement ? 'Supplement' : 'Medication'}
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main View ────────────────────────────────────────────────────────────────

function MedIntelligenceCards() {
  const { user } = useAuth();
  const { data: overview } = useQuery({
    queryKey: ['treatment-overview'],
    queryFn: async () => { try { const { data } = await api.get('/api/v1/med-intelligence/treatment-overview'); return data; } catch { return null; } },
    enabled: Boolean(user),
    staleTime: 2 * 60_000,
  });
  const { data: interactions } = useQuery({
    queryKey: ['med-interactions'],
    queryFn: async () => { try { const { data } = await api.get('/api/v1/med-intelligence/interactions'); return data; } catch { return null; } },
    enabled: Boolean(user),
    staleTime: 5 * 60_000,
  });

  const totalAlerts = (interactions?.drug_nutrient?.length ?? 0) + (interactions?.drug_food?.length ?? 0) + (interactions?.drug_drug?.length ?? 0);

  return (
    <>
      {overview && (
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-4 h-4 text-primary-500" />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Treatment Overview</span>
            </div>
            <div className="grid grid-cols-4 gap-3 mb-3">
              <div className="text-center p-2 rounded-lg bg-slate-50 dark:bg-slate-700/50">
                <div className="text-lg font-bold" style={{ color: (overview.adherence?.rate_pct ?? 0) >= 90 ? '#6EE7B7' : '#F5A623' }}>{overview.adherence?.rate_pct ?? 0}%</div>
                <div className="text-xs text-slate-500">Adherence</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-slate-50 dark:bg-slate-700/50">
                <div className="text-lg font-bold text-green-400">{overview.lab_validation?.improving ?? 0}</div>
                <div className="text-xs text-slate-500">Lab proven</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-slate-50 dark:bg-slate-700/50">
                <div className="text-lg font-bold" style={{ color: totalAlerts > 0 ? '#F5A623' : '#526380' }}>{totalAlerts}</div>
                <div className="text-xs text-slate-500">Alerts</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-slate-50 dark:bg-slate-700/50">
                <div className="text-lg font-bold" style={{ color: (overview.supplement_gaps ?? 0) > 0 ? '#F87171' : '#526380' }}>{overview.supplement_gaps ?? 0}</div>
                <div className="text-xs text-slate-500">Gaps</div>
              </div>
            </div>
            {overview.ai_summary && (
              <p className="text-sm text-slate-600 dark:text-slate-400 italic">{overview.ai_summary}</p>
            )}
          </CardContent>
        </Card>
      )}

      {totalAlerts > 0 && interactions && (
        <Card className="border-amber-500/30">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertCircle className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-semibold uppercase tracking-wider text-amber-500">Interaction Alerts ({totalAlerts})</span>
            </div>
            <div className="space-y-2">
              {(interactions.drug_nutrient ?? []).slice(0, 3).map((d: any, i: number) => (
                <div key={`dn-${i}`} className="flex items-center gap-2 text-xs">
                  <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: d.severity === 'high' ? '#F87171' : '#F5A623' }} />
                  <span className="text-slate-700 dark:text-slate-300">{d.medication} depletes {d.depletes}</span>
                  {d.covered_by_supplement ? (
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-green-500/10 text-green-500">Covered</span>
                  ) : (
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-red-500/10 text-red-500">Gap</span>
                  )}
                  {d.lab_status && <span className="text-slate-400">Lab: {d.lab_status}</span>}
                </div>
              ))}
              {(interactions.drug_food ?? []).slice(0, 2).map((d: any, i: number) => (
                <div key={`df-${i}`} className="flex items-center gap-2 text-xs">
                  <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                  <span className="text-slate-700 dark:text-slate-300">{d.medication} + {d.food}</span>
                  <span className="text-slate-400">{d.note}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
}

// ── AI Medication Recommendations (shown when no meds logged) ────────────

const PRIORITY_CONFIG = {
  high: { color: '#F87171', bg: 'bg-red-500/10', label: 'High Priority' },
  medium: { color: '#FBBF24', bg: 'bg-amber-500/10', label: 'Medium' },
  low: { color: '#60A5FA', bg: 'bg-blue-500/10', label: 'Low' },
} as const;

const CATEGORY_ICON = {
  prescription: Stethoscope,
  otc: Pill,
  supplement: FlaskConical,
} as const;

const EVIDENCE_BADGE = {
  strong: { label: 'Strong evidence', cls: 'bg-green-500/10 text-green-500' },
  moderate: { label: 'Moderate evidence', cls: 'bg-amber-500/10 text-amber-500' },
  emerging: { label: 'Emerging evidence', cls: 'bg-blue-500/10 text-blue-400' },
} as const;

interface Recommendation {
  name: string;
  category: 'prescription' | 'otc' | 'supplement';
  rationale: string;
  evidence_level: 'strong' | 'moderate' | 'emerging';
  priority: 'high' | 'medium' | 'low';
  discuss_with_doctor: boolean;
  relevant_data?: string;
  estimated_cost?: string;
  efficacy?: string;
}

function MedicationRecommendations({ onAddMedication }: { onAddMedication: () => void }) {
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [sharing, setSharing] = useState(false);
  const [copied, setCopied] = useState(false);

  async function handleShare() {
    setSharing(true);
    try {
      const { data: link } = await api.post('/api/v1/share/', {
        label: 'Treatment Recommendations for Provider',
        permissions: ['summary', 'medications', 'lab_results', 'intelligence'],
      });
      const url = `${window.location.origin}/share/${link.token}`;
      setShareUrl(url);
      await navigator.clipboard.writeText(url);
      setCopied(true);
      toast.success('Share link copied to clipboard');
      setTimeout(() => setCopied(false), 3000);
    } catch {
      toast.error('Failed to create share link');
    } finally {
      setSharing(false);
    }
  }

  const { data, isLoading } = useQuery({
    queryKey: ['med-recommendations'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/med-intelligence/recommendations');
      return data as {
        recommendations: Recommendation[];
        summary: string;
        disclaimer: string;
        data_sources: { conditions: number; lab_results: number; medical_records: number; symptoms: number };
      };
    },
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center py-12 gap-3">
        <Loader2 className="w-6 h-6 text-primary-500 animate-spin" />
        <p className="text-sm text-slate-400">Analyzing your health profile for recommendations...</p>
      </div>
    );
  }

  const recs = data?.recommendations ?? [];
  const summary = data?.summary ?? '';
  const disclaimer = data?.disclaimer ?? '';
  const sources = data?.data_sources;

  if (recs.length === 0) {
    return (
      <EmptyState
        icon={Pill}
        title="No medications yet"
        description={summary || 'Add your health conditions, lab results, or medical records to receive personalized medication recommendations.'}
        actionLabel="Add Medication"
        onAction={onAddMedication}
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      {summary && (
        <div className="p-4 rounded-xl bg-primary-500/5 border border-primary-500/10">
          <div className="flex items-start gap-2.5">
            <Sparkles className="w-4 h-4 text-primary-500 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{summary}</p>
              {sources && (
                <p className="text-xs text-slate-400 mt-2">
                  Based on {sources.conditions} condition{sources.conditions !== 1 ? 's' : ''}, {sources.lab_results} lab result{sources.lab_results !== 1 ? 's' : ''}, {sources.medical_records} medical record{sources.medical_records !== 1 ? 's' : ''}, {sources.symptoms} symptom{sources.symptoms !== 1 ? 's' : ''}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div className="space-y-3">
        {recs.map((rec, i) => {
          const priority = PRIORITY_CONFIG[rec.priority] ?? PRIORITY_CONFIG.low;
          const CatIcon = CATEGORY_ICON[rec.category] ?? Pill;
          const evidence = EVIDENCE_BADGE[rec.evidence_level] ?? EVIDENCE_BADGE.moderate;

          return (
            <div key={i} className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ backgroundColor: `${priority.color}15` }}>
                  <CatIcon className="w-4.5 h-4.5" style={{ color: priority.color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">{rec.name}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium uppercase tracking-wider" style={{ backgroundColor: `${priority.color}15`, color: priority.color }}>
                      {priority.label}
                    </span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${evidence.cls}`}>
                      {evidence.label}
                    </span>
                    {rec.discuss_with_doctor && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium bg-purple-500/10 text-purple-400">
                        Rx — discuss with doctor
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1.5 leading-relaxed">{rec.rationale}</p>
                  {(rec.efficacy || rec.estimated_cost) && (
                    <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
                      {rec.efficacy && (
                        <span className="text-[11px] text-emerald-500 dark:text-emerald-400 flex items-center gap-1">
                          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
                          {rec.efficacy}
                        </span>
                      )}
                      {rec.estimated_cost && (
                        <span className="text-[11px] text-slate-400 flex items-center gap-1">
                          <span className="font-medium">$</span>
                          {rec.estimated_cost}
                        </span>
                      )}
                    </div>
                  )}
                  {rec.relevant_data && (
                    <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
                      <ArrowRight className="w-3 h-3" />
                      {rec.relevant_data}
                    </p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Disclaimer */}
      <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-500/5 border border-amber-500/10">
        <ShieldCheck className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
        <p className="text-[11px] text-slate-400 leading-relaxed">{disclaimer}</p>
      </div>

      {/* Share with Provider */}
      <div className="flex gap-2">
        <button
          onClick={handleShare}
          disabled={sharing}
          className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-primary-500/10 border border-primary-500/20 text-sm font-medium text-primary-600 dark:text-primary-400 hover:bg-primary-500/20 transition-colors"
        >
          {sharing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : copied ? (
            <CheckCircle2 className="w-4 h-4" />
          ) : (
            <Share2 className="w-4 h-4" />
          )}
          {copied ? 'Link Copied!' : 'Share with Provider'}
        </button>
      </div>
      {shareUrl && (
        <div className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
          <Link2 className="w-4 h-4 text-slate-400 shrink-0" />
          <input
            readOnly
            value={shareUrl}
            className="flex-1 text-xs bg-transparent text-slate-500 dark:text-slate-400 outline-none"
            onClick={(e) => { (e.target as HTMLInputElement).select(); navigator.clipboard.writeText(shareUrl); setCopied(true); toast.success('Copied!'); }}
          />
        </div>
      )}

      {/* Still allow adding medications manually */}
      <button
        onClick={onAddMedication}
        className="w-full py-2.5 rounded-lg border border-dashed border-slate-300 dark:border-slate-600 text-sm text-slate-500 hover:text-primary-500 hover:border-primary-500 transition-colors"
      >
        <Plus className="w-4 h-4 inline mr-1" />
        Add a medication you're already taking
      </button>
    </div>
  );
}

export function MedicationsView() {
  const { user, isLoading: isAuthLoading } = useAuth(true);
  const queryClient = useQueryClient();

  const [showMedForm, setShowMedForm] = useState(false);
  const [showSuppForm, setShowSuppForm] = useState(false);
  const [editingMed, setEditingMed] = useState<Medication | null>(null);
  const [editingSupp, setEditingSupp] = useState<Supplement | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Scan modal state
  const [scanTarget, setScanTarget] = useState<ScanTarget>('medication');
  const [showScan, setShowScan] = useState(false);
  // Pre-fill from scan result
  const [scannedMedPrefill, setScannedMedPrefill] = useState<Partial<CreateMedicationRequest> | null>(null);
  const [scannedSuppPrefill, setScannedSuppPrefill] = useState<Partial<CreateSupplementRequest> | null>(null);

  const { data: medsData, isLoading: medsLoading } = useQuery({
    queryKey: ['medications'],
    queryFn: () => medicationsService.getMedications(),
    enabled: Boolean(user) && !isAuthLoading,
  });

  const { data: suppsData, isLoading: suppsLoading } = useQuery({
    queryKey: ['supplements'],
    queryFn: () => medicationsService.getSupplements(),
    enabled: Boolean(user) && !isAuthLoading,
  });

  const medications = medsData?.medications ?? [];
  const supplements = suppsData?.supplements ?? [];

  const deleteMedMutation = useMutation({
    mutationFn: (id: string) => medicationsService.deleteMedication(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['medications'] }); setError(null); },
    onError: (e: unknown) => setError(e instanceof Error ? e.message : 'Failed to delete medication'),
  });

  const deleteSuppMutation = useMutation({
    mutationFn: (id: string) => medicationsService.deleteSupplement(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['supplements'] }); setError(null); },
    onError: (e: unknown) => setError(e instanceof Error ? e.message : 'Failed to delete supplement'),
  });

  // When user clicks "Use Medication/Supplement" in the scan modal
  const handleScanApply = (result: PrescriptionScanResult) => {
    setShowScan(false);
    if (result.is_supplement || scanTarget === 'supplement') {
      setScannedSuppPrefill({
        supplement_name: result.medication_name ?? '',
        brand: result.brand,
        dosage: result.dosage ?? '',
        frequency: result.frequency ?? '',
        form: result.form ?? 'capsule',
        purpose: result.purpose ?? result.indication,
        notes: result.notes,
        is_active: true,
      });
      setEditingSupp(null);
      setShowSuppForm(true);
    } else {
      setScannedMedPrefill({
        medication_name: result.medication_name ?? '',
        generic_name: result.generic_name,
        dosage: result.dosage ?? '',
        frequency: result.frequency ?? '',
        route: result.route ?? 'oral',
        indication: result.indication,
        prescribing_doctor: result.prescribing_doctor,
        pharmacy: result.pharmacy,
        prescription_number: result.prescription_number,
        notes: result.notes,
        is_active: true,
      });
      setEditingMed(null);
      setShowMedForm(true);
    }
  };

  if (isAuthLoading || medsLoading || suppsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-slate-500">Loading…</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Medications & Supplements</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">Track your medications, supplements, and adherence</p>
      </div>

      {/* Treatment Intelligence */}
      <MedIntelligenceCards />

      {/* Daily adherence strip */}
      <DailyAdherenceStrip />

      {/* Streak badges + missed-dose pattern */}
      <StreakBadges />

      {/* 7-day adherence calendar */}
      <AdherenceCalendar />

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-800 dark:text-red-200">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Medications Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Pill className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <CardTitle>Medications</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => { setScanTarget('medication'); setShowScan(true); }}
              >
                <Camera className="w-4 h-4 mr-1.5" />
                Scan
              </Button>
              <Button
                size="sm"
                onClick={() => { setShowMedForm(true); setEditingMed(null); setScannedMedPrefill(null); }}
              >
                <Plus className="w-4 h-4 mr-1" />
                Add
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {medications.length === 0 ? (
            <MedicationRecommendations onAddMedication={() => { setShowMedForm(true); setEditingMed(null); setScannedMedPrefill(null); }} />
          ) : (
            <div className="space-y-3">
              {medications.map((med) => (
                <div
                  key={med.id}
                  className="flex items-center justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50"
                >
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-slate-900 dark:text-slate-100">{med.medication_name}</div>
                    <div className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
                      {med.dosage} · {med.frequency}
                      {med.route && med.route !== 'oral' && ` · ${med.route}`}
                      {med.indication && ` · ${med.indication}`}
                    </div>
                    {med.prescribing_doctor && (
                      <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Dr. {med.prescribing_doctor.replace(/^Dr\.?\s*/i, '')}</div>
                    )}
                    {!med.is_active && <div className="text-xs text-slate-400 mt-0.5">(Inactive)</div>}
                  </div>
                  <div className="flex items-center gap-2 ml-3">
                    <Button variant="outline" size="sm" onClick={() => { setEditingMed(med); setScannedMedPrefill(null); setShowMedForm(true); }}>
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => { if (confirm(`Delete ${med.medication_name}?`)) deleteMedMutation.mutate(med.id); }}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Supplements Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Pill className="w-5 h-5 text-green-600 dark:text-green-400" />
              <CardTitle>Supplements</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => { setScanTarget('supplement'); setShowScan(true); }}
              >
                <Camera className="w-4 h-4 mr-1.5" />
                Scan
              </Button>
              <Button
                size="sm"
                onClick={() => { setShowSuppForm(true); setEditingSupp(null); setScannedSuppPrefill(null); }}
              >
                <Plus className="w-4 h-4 mr-1" />
                Add
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {supplements.length === 0 ? (
            <div className="text-center py-8 text-slate-500 dark:text-slate-400">
              No supplements tracked yet.{' '}
              <button
                className="text-primary-600 dark:text-primary-400 hover:underline"
                onClick={() => { setScanTarget('supplement'); setShowScan(true); }}
              >
                Scan a bottle
              </button>
              {' '}or click <strong>Add</strong> to enter manually.
            </div>
          ) : (
            <div className="space-y-3">
              {supplements.map((supp) => (
                <div
                  key={supp.id}
                  className="flex items-center justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50"
                >
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-slate-900 dark:text-slate-100">{supp.supplement_name}</div>
                    <div className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
                      {supp.dosage} · {supp.frequency}
                      {supp.brand && ` · ${supp.brand}`}
                      {supp.purpose && ` · ${supp.purpose}`}
                    </div>
                    {!supp.is_active && <div className="text-xs text-slate-400 mt-0.5">(Inactive)</div>}
                  </div>
                  <div className="flex items-center gap-2 ml-3">
                    <Button variant="outline" size="sm" onClick={() => { setEditingSupp(supp); setScannedSuppPrefill(null); setShowSuppForm(true); }}>
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => { if (confirm(`Delete ${supp.supplement_name}?`)) deleteSuppMutation.mutate(supp.id); }}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modals */}
      {showScan && (
        <PrescriptionScanModal
          target={scanTarget}
          onClose={() => setShowScan(false)}
          onApply={handleScanApply}
        />
      )}

      {showMedForm && (
        <MedicationForm
          medication={editingMed}
          prefill={scannedMedPrefill}
          onClose={() => { setShowMedForm(false); setEditingMed(null); setScannedMedPrefill(null); }}
          onSuccess={() => {
            setShowMedForm(false);
            setEditingMed(null);
            setScannedMedPrefill(null);
            queryClient.invalidateQueries({ queryKey: ['medications'] });
          }}
        />
      )}

      {showSuppForm && (
        <SupplementForm
          supplement={editingSupp}
          prefill={scannedSuppPrefill}
          onClose={() => { setShowSuppForm(false); setEditingSupp(null); setScannedSuppPrefill(null); }}
          onSuccess={() => {
            setShowSuppForm(false);
            setEditingSupp(null);
            setScannedSuppPrefill(null);
            queryClient.invalidateQueries({ queryKey: ['supplements'] });
          }}
        />
      )}
    </div>
  );
}

// ── Medication Form ──────────────────────────────────────────────────────────

function MedicationForm({
  medication,
  prefill,
  onClose,
  onSuccess,
}: {
  medication: Medication | null;
  prefill?: Partial<CreateMedicationRequest> | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const initial: CreateMedicationRequest = {
    medication_name: prefill?.medication_name ?? medication?.medication_name ?? '',
    generic_name: prefill?.generic_name ?? medication?.generic_name,
    dosage: prefill?.dosage ?? medication?.dosage ?? '',
    frequency: prefill?.frequency ?? medication?.frequency ?? '',
    route: prefill?.route ?? medication?.route ?? 'oral',
    indication: prefill?.indication ?? medication?.indication,
    prescribing_doctor: prefill?.prescribing_doctor ?? medication?.prescribing_doctor,
    pharmacy: prefill?.pharmacy ?? medication?.pharmacy,
    prescription_number: prefill?.prescription_number ?? medication?.prescription_number,
    notes: prefill?.notes ?? medication?.notes,
    is_active: prefill?.is_active ?? medication?.is_active ?? true,
  };

  const [formData, setFormData] = useState<CreateMedicationRequest>(initial);
  const hasPrefill = !!prefill;

  const mutation = useMutation({
    mutationFn: (data: CreateMedicationRequest) =>
      medication
        ? medicationsService.updateMedication(medication.id, data)
        : medicationsService.createMedication(data),
    onSuccess,
  });

  const set = (patch: Partial<CreateMedicationRequest>) => setFormData((p) => ({ ...p, ...patch }));

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
              {medication ? 'Edit Medication' : hasPrefill ? 'Confirm Scanned Medication' : 'Add Medication'}
            </h2>
            {hasPrefill && (
              <span className="flex items-center gap-1 text-xs text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/20 px-2 py-1 rounded-full">
                <Sparkles className="w-3 h-3" />
                Auto-filled
              </span>
            )}
          </div>

          <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(formData); }} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Medication Name *</label>
              <input type="text" value={formData.medication_name} onChange={(e) => set({ medication_name: e.target.value })} className={inputCls} required />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Generic Name</label>
              <input type="text" value={formData.generic_name ?? ''} onChange={(e) => set({ generic_name: e.target.value })} className={inputCls} placeholder="e.g., atorvastatin" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Dosage *</label>
                <input type="text" placeholder="e.g., 10mg" value={formData.dosage} onChange={(e) => set({ dosage: e.target.value })} className={inputCls} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Frequency *</label>
                <input type="text" placeholder="e.g., twice daily" value={formData.frequency} onChange={(e) => set({ frequency: e.target.value })} className={inputCls} required />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Route</label>
                <select value={formData.route ?? 'oral'} onChange={(e) => set({ route: e.target.value })} className={inputCls}>
                  <option value="oral">Oral</option>
                  <option value="topical">Topical</option>
                  <option value="injection">Injection</option>
                  <option value="inhaled">Inhaled</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">What is it for?</label>
                <input type="text" value={formData.indication ?? ''} onChange={(e) => set({ indication: e.target.value })} className={inputCls} placeholder="e.g., hypertension" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Prescribing Doctor</label>
                <input type="text" value={formData.prescribing_doctor ?? ''} onChange={(e) => set({ prescribing_doctor: e.target.value })} className={inputCls} />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Pharmacy</label>
                <input type="text" value={formData.pharmacy ?? ''} onChange={(e) => set({ pharmacy: e.target.value })} className={inputCls} />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Rx / Prescription Number</label>
              <input type="text" value={formData.prescription_number ?? ''} onChange={(e) => set({ prescription_number: e.target.value })} className={inputCls} placeholder="e.g., 1234567" />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Notes</label>
              <textarea value={formData.notes ?? ''} onChange={(e) => set({ notes: e.target.value })} rows={2} className={inputCls} />
            </div>

            <div className="flex items-center gap-2">
              <input type="checkbox" id="is_active" checked={formData.is_active} onChange={(e) => set({ is_active: e.target.checked })} className="w-4 h-4" />
              <label htmlFor="is_active" className="text-sm text-slate-700 dark:text-slate-300">Currently taking this medication</label>
            </div>

            <div className="flex gap-3 pt-2">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? 'Saving…' : medication ? 'Update' : 'Save Medication'}
              </Button>
              <Button type="button" variant="outline" onClick={onClose} className="flex-1">Cancel</Button>
            </div>
            {mutation.isError && (
              <p className="text-sm text-red-600 dark:text-red-400">
                {mutation.error instanceof Error ? mutation.error.message : 'Failed to save'}
              </p>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}

// ── Supplement Form ──────────────────────────────────────────────────────────

function SupplementForm({
  supplement,
  prefill,
  onClose,
  onSuccess,
}: {
  supplement: Supplement | null;
  prefill?: Partial<CreateSupplementRequest> | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const initial: CreateSupplementRequest = {
    supplement_name: prefill?.supplement_name ?? supplement?.supplement_name ?? '',
    brand: prefill?.brand ?? supplement?.brand,
    dosage: prefill?.dosage ?? supplement?.dosage ?? '',
    frequency: prefill?.frequency ?? supplement?.frequency ?? '',
    form: prefill?.form ?? supplement?.form ?? 'capsule',
    purpose: prefill?.purpose ?? supplement?.purpose,
    notes: prefill?.notes ?? supplement?.notes,
    is_active: prefill?.is_active ?? supplement?.is_active ?? true,
  };

  const [formData, setFormData] = useState<CreateSupplementRequest>(initial);
  const hasPrefill = !!prefill;

  const mutation = useMutation({
    mutationFn: (data: CreateSupplementRequest) =>
      supplement
        ? medicationsService.updateSupplement(supplement.id, data)
        : medicationsService.createSupplement(data),
    onSuccess,
  });

  const set = (patch: Partial<CreateSupplementRequest>) => setFormData((p) => ({ ...p, ...patch }));

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
              {supplement ? 'Edit Supplement' : hasPrefill ? 'Confirm Scanned Supplement' : 'Add Supplement'}
            </h2>
            {hasPrefill && (
              <span className="flex items-center gap-1 text-xs text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/20 px-2 py-1 rounded-full">
                <Sparkles className="w-3 h-3" />
                Auto-filled
              </span>
            )}
          </div>

          <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(formData); }} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Supplement Name *</label>
              <input type="text" value={formData.supplement_name} onChange={(e) => set({ supplement_name: e.target.value })} className={inputCls} required />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Dosage *</label>
                <input type="text" placeholder="e.g., 1000mg" value={formData.dosage} onChange={(e) => set({ dosage: e.target.value })} className={inputCls} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Frequency *</label>
                <input type="text" placeholder="e.g., once daily" value={formData.frequency} onChange={(e) => set({ frequency: e.target.value })} className={inputCls} required />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Brand</label>
                <input type="text" value={formData.brand ?? ''} onChange={(e) => set({ brand: e.target.value })} className={inputCls} />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Form</label>
                <select value={formData.form ?? 'capsule'} onChange={(e) => set({ form: e.target.value })} className={inputCls}>
                  <option value="capsule">Capsule</option>
                  <option value="tablet">Tablet</option>
                  <option value="powder">Powder</option>
                  <option value="liquid">Liquid</option>
                  <option value="gummy">Gummy</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Purpose</label>
              <input type="text" value={formData.purpose ?? ''} onChange={(e) => set({ purpose: e.target.value })} className={inputCls} placeholder="e.g., immune support, bone health" />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Notes</label>
              <textarea value={formData.notes ?? ''} onChange={(e) => set({ notes: e.target.value })} rows={2} className={inputCls} />
            </div>

            <div className="flex items-center gap-2">
              <input type="checkbox" id="supp_is_active" checked={formData.is_active} onChange={(e) => set({ is_active: e.target.checked })} className="w-4 h-4" />
              <label htmlFor="supp_is_active" className="text-sm text-slate-700 dark:text-slate-300">Currently taking this supplement</label>
            </div>

            <div className="flex gap-3 pt-2">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? 'Saving…' : supplement ? 'Update' : 'Save Supplement'}
              </Button>
              <Button type="button" variant="outline" onClick={onClose} className="flex-1">Cancel</Button>
            </div>
            {mutation.isError && (
              <p className="text-sm text-red-600 dark:text-red-400">
                {mutation.error instanceof Error ? mutation.error.message : 'Failed to save'}
              </p>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
