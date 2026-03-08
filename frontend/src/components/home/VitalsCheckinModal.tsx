'use client';

import { useState, useEffect } from 'react';
import { X, Scale, Stethoscope, Pill, ChevronRight } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { api } from '@/services/api';
import toast from 'react-hot-toast';

const SNOOZE_KEY = 'vitals-checkin-snoozed';
const SNOOZE_DAYS = 7;
const CHECKIN_INTERVAL_DAYS = 30;

function daysSince(isoStr?: string): number {
  if (!isoStr) return Infinity;
  return (Date.now() - new Date(isoStr).getTime()) / (1000 * 60 * 60 * 24);
}

function isSnoozed(): boolean {
  try {
    const val = localStorage.getItem(SNOOZE_KEY);
    if (!val) return false;
    return (Date.now() - Number(val)) / (1000 * 60 * 60 * 24) < SNOOZE_DAYS;
  } catch { return false; }
}

function snooze() {
  try { localStorage.setItem(SNOOZE_KEY, String(Date.now())); } catch { /* ignore */ }
}

// ── Step dot indicator ────────────────────────────────────────────────────────

function StepDots({ total, current }: { total: number; current: number }) {
  return (
    <div className="flex items-center justify-center gap-1.5 mb-5">
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} className="rounded-full transition-all duration-300"
          style={{
            width: i === current ? 16 : 6,
            height: 6,
            backgroundColor: i <= current ? '#00D4AA' : 'rgba(255,255,255,0.12)',
          }} />
      ))}
    </div>
  );
}

// ── Main modal ────────────────────────────────────────────────────────────────

export function VitalsCheckinModal() {
  const { profile, setProfile } = useAuthStore();
  const [visible, setVisible] = useState(false);
  const [step, setStep] = useState(0); // 0=weight, 1=diagnoses, 2=medications

  // Step 0 — weight
  const [weight, setWeight] = useState<number | ''>('');
  const [weightUnit, setWeightUnit] = useState<'lb' | 'kg'>('lb');

  // Step 1 — diagnoses
  const [hasNewDiagnosis, setHasNewDiagnosis] = useState<null | boolean>(null);
  const [diagnosisText, setDiagnosisText] = useState('');

  // Step 2 — medications
  const [hasNewMeds, setHasNewMeds] = useState<null | boolean>(null);
  const [medsText, setMedsText] = useState('');

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const needsCheckin = !profile?.last_checkin_at || daysSince(profile.last_checkin_at) > CHECKIN_INTERVAL_DAYS;
    if (needsCheckin && !isSnoozed()) {
      if (profile?.weight_kg != null) {
        setWeight(Math.round(profile.weight_kg * 2.20462));
        setWeightUnit('lb');
      }
      const t = setTimeout(() => setVisible(true), 800);
      return () => clearTimeout(t);
    }
  }, [profile?.last_checkin_at, profile?.weight_kg]);

  const handleDismiss = () => { snooze(); setVisible(false); };

  const handleNext = () => setStep((s) => s + 1);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      const weightKg =
        typeof weight === 'number' && weight > 0
          ? weightUnit === 'lb' ? Math.round((weight / 2.20462) * 10) / 10 : weight
          : undefined;

      const newConditions = hasNewDiagnosis && diagnosisText.trim()
        ? diagnosisText.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined;

      const newMedications = hasNewMeds && medsText.trim()
        ? medsText.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined;

      const { data } = await api.patch('/api/v1/profile/checkin', {
        weight_kg: weightKg,
        new_conditions: newConditions,
        new_medications: newMedications,
      });

      setProfile({
        ...profile,
        ...(weightKg != null ? { weight_kg: weightKg } : {}),
        last_checkin_at: data.last_checkin_at,
      });

      const parts: string[] = ['Check-in saved'];
      if (newConditions?.length) parts.push(`${newConditions.length} condition(s) added`);
      if (newMedications?.length) parts.push(`${newMedications.length} medication(s) added`);
      toast.success(parts.join(' · '));
      setVisible(false);
    } catch {
      toast.error('Failed to save check-in');
    } finally {
      setSaving(false);
    }
  };

  if (!visible) return null;

  const STEPS = [
    { icon: Scale, label: 'Weight' },
    { icon: Stethoscope, label: 'Diagnoses' },
    { icon: Pill, label: 'Medications' },
  ];
  const CurrentIcon = STEPS[step].icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60" onClick={handleDismiss} />

      <div className="relative rounded-2xl p-6 w-full max-w-sm shadow-2xl z-10"
        style={{ backgroundColor: '#0D1520', border: '1px solid rgba(255,255,255,0.1)' }}>

        <button onClick={handleDismiss}
          className="absolute top-4 right-4 text-[#526380] hover:text-[#8B97A8] transition-colors">
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-[#00D4AA]/10 flex items-center justify-center">
            <CurrentIcon className="w-5 h-5 text-[#00D4AA]" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-[#E8EDF5]">Monthly Check-In</h2>
            <p className="text-xs text-[#526380]">{STEPS[step].label} — step {step + 1} of 3</p>
          </div>
        </div>

        <StepDots total={3} current={step} />

        {/* Step 0 — Weight */}
        {step === 0 && (
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-[#8B97A8] mb-1.5">Current weight</label>
              <div className="flex gap-2">
                <input type="number" value={weight}
                  onChange={(e) => setWeight(e.target.value === '' ? '' : Number(e.target.value))}
                  min={1} placeholder={weightUnit === 'lb' ? '160' : '72'}
                  className="flex-1 px-3 py-2 rounded-lg text-sm text-[#E8EDF5] bg-white/5 border border-white/10 focus:outline-none focus:border-[#00D4AA]/50" />
                <select value={weightUnit} onChange={(e) => setWeightUnit(e.target.value as 'lb' | 'kg')}
                  className="w-16 px-2 py-2 rounded-lg text-sm text-[#E8EDF5] bg-white/5 border border-white/10 focus:outline-none">
                  <option value="lb">lb</option>
                  <option value="kg">kg</option>
                </select>
              </div>
            </div>
            <button onClick={handleNext}
              className="w-full py-2.5 rounded-lg text-sm font-semibold flex items-center justify-center gap-1.5 text-[#080B10] bg-[#00D4AA] hover:bg-[#00C49A] transition-colors">
              Next <ChevronRight className="w-4 h-4" />
            </button>
            <button onClick={handleDismiss} className="w-full text-xs text-[#526380] text-center hover:text-[#8B97A8]">
              Remind me later
            </button>
          </div>
        )}

        {/* Step 1 — Diagnoses */}
        {step === 1 && (
          <div className="space-y-4">
            <p className="text-sm text-[#C8D5E8]">Any new diagnoses since your last check-in?</p>
            <div className="flex gap-2">
              {[true, false].map((v) => (
                <button key={String(v)} onClick={() => setHasNewDiagnosis(v)}
                  className="flex-1 py-2 rounded-lg text-sm font-medium transition-colors"
                  style={{
                    backgroundColor: hasNewDiagnosis === v ? (v ? 'rgba(0,212,170,0.15)' : 'rgba(255,255,255,0.08)') : 'rgba(255,255,255,0.05)',
                    border: `1px solid ${hasNewDiagnosis === v ? (v ? 'rgba(0,212,170,0.4)' : 'rgba(255,255,255,0.2)') : 'rgba(255,255,255,0.1)'}`,
                    color: hasNewDiagnosis === v ? '#E8EDF5' : '#526380',
                  }}>
                  {v ? 'Yes' : 'No'}
                </button>
              ))}
            </div>
            {hasNewDiagnosis === true && (
              <input type="text" value={diagnosisText} onChange={(e) => setDiagnosisText(e.target.value)}
                placeholder="e.g. Hypertension, Type 2 Diabetes (comma-separated)"
                className="w-full px-3 py-2 rounded-lg text-sm text-[#E8EDF5] bg-white/5 border border-white/10 focus:outline-none focus:border-[#00D4AA]/50" />
            )}
            <div className="flex gap-2">
              <button onClick={() => setStep(0)}
                className="flex-1 py-2.5 rounded-lg text-sm text-[#526380] bg-white/5 hover:bg-white/8 transition-colors">
                Back
              </button>
              <button onClick={handleNext} disabled={hasNewDiagnosis === null}
                className="flex-1 py-2.5 rounded-lg text-sm font-semibold flex items-center justify-center gap-1.5 text-[#080B10] bg-[#00D4AA] hover:bg-[#00C49A] disabled:opacity-40 transition-colors">
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 2 — Medications */}
        {step === 2 && (
          <div className="space-y-4">
            <p className="text-sm text-[#C8D5E8]">Any medication changes since your last check-in?</p>
            <div className="flex gap-2">
              {[true, false].map((v) => (
                <button key={String(v)} onClick={() => setHasNewMeds(v)}
                  className="flex-1 py-2 rounded-lg text-sm font-medium transition-colors"
                  style={{
                    backgroundColor: hasNewMeds === v ? (v ? 'rgba(0,212,170,0.15)' : 'rgba(255,255,255,0.08)') : 'rgba(255,255,255,0.05)',
                    border: `1px solid ${hasNewMeds === v ? (v ? 'rgba(0,212,170,0.4)' : 'rgba(255,255,255,0.2)') : 'rgba(255,255,255,0.1)'}`,
                    color: hasNewMeds === v ? '#E8EDF5' : '#526380',
                  }}>
                  {v ? 'Yes' : 'No'}
                </button>
              ))}
            </div>
            {hasNewMeds === true && (
              <input type="text" value={medsText} onChange={(e) => setMedsText(e.target.value)}
                placeholder="e.g. Metformin, Lisinopril (comma-separated)"
                className="w-full px-3 py-2 rounded-lg text-sm text-[#E8EDF5] bg-white/5 border border-white/10 focus:outline-none focus:border-[#00D4AA]/50" />
            )}
            <div className="flex gap-2">
              <button onClick={() => setStep(1)}
                className="flex-1 py-2.5 rounded-lg text-sm text-[#526380] bg-white/5 hover:bg-white/8 transition-colors">
                Back
              </button>
              <button onClick={handleSubmit} disabled={saving || hasNewMeds === null}
                className="flex-1 py-2.5 rounded-lg text-sm font-semibold text-[#080B10] bg-[#00D4AA] hover:bg-[#00C49A] disabled:opacity-40 transition-colors">
                {saving ? 'Saving…' : 'Done ✓'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
