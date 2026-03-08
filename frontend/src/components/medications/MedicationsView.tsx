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
  Sparkles,
} from 'lucide-react';
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
            <div className="text-center py-8 text-slate-500 dark:text-slate-400">
              No medications tracked yet.{' '}
              <button
                className="text-primary-600 dark:text-primary-400 hover:underline"
                onClick={() => { setScanTarget('medication'); setShowScan(true); }}
              >
                Scan a prescription
              </button>
              {' '}or click <strong>Add</strong> to enter manually.
            </div>
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
