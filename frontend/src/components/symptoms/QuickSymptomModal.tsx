'use client';

import { useState } from 'react';
import Link from 'next/link';
import { X } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { symptomsService } from '@/services/symptoms';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

const SYMPTOM_TYPES = [
  { value: 'pain', label: 'Pain' },
  { value: 'fatigue', label: 'Fatigue' },
  { value: 'nausea', label: 'Nausea' },
  { value: 'headache', label: 'Headache' },
  { value: 'digestive', label: 'Digestive' },
  { value: 'mental_health', label: 'Mental Health' },
  { value: 'respiratory', label: 'Respiratory' },
  { value: 'skin', label: 'Skin' },
  { value: 'other', label: 'Other' },
];

function severityLabel(v: number) {
  if (v <= 3) return 'Mild';
  if (v <= 6) return 'Moderate';
  return 'Severe';
}

function severityColor(v: number) {
  if (v <= 3) return '#00D4AA';
  if (v <= 6) return '#FBB124';
  return '#F87171';
}

export function QuickSymptomModal({ isOpen, onClose }: Props) {
  const queryClient = useQueryClient();
  const [symptomType, setSymptomType] = useState('pain');
  const [severity, setSeverity] = useState(5);
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await symptomsService.createSymptom({
        symptom_type: symptomType,
        severity,
        symptom_date: new Date().toISOString().slice(0, 10),
      });
      toast.success('Symptom logged');
      queryClient.invalidateQueries({ queryKey: ['symptoms'] });
      onClose();
    } catch {
      toast.error('Failed to log symptom');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className="relative w-full max-w-sm rounded-2xl p-6"
        style={{ backgroundColor: '#0E1219', border: '1px solid rgba(255,255,255,0.08)' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-[#E8EDF5]">Quick Log Symptom</h2>
          <button
            onClick={onClose}
            className="text-[#3D4F66] hover:text-[#526380] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Symptom type */}
        <div className="mb-5">
          <label className="block text-xs font-medium text-[#8B97A8] mb-2">Symptom type</label>
          <select
            value={symptomType}
            onChange={(e) => setSymptomType(e.target.value)}
            className="w-full px-3 py-2.5 rounded-lg text-sm text-[#E8EDF5] outline-none"
            style={{
              backgroundColor: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            {SYMPTOM_TYPES.map(({ value, label }) => (
              <option key={value} value={value} style={{ backgroundColor: '#0E1219' }}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* Severity slider */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-medium text-[#8B97A8]">Severity</label>
            <span className="text-xs font-bold" style={{ color: severityColor(severity) }}>
              {severity}/10 — {severityLabel(severity)}
            </span>
          </div>
          {/* Gradient track */}
          <div className="relative h-2 rounded-full mb-3"
            style={{ background: 'linear-gradient(to right, #00D4AA, #FBB124, #F87171)' }}>
            <input
              type="range"
              min={1}
              max={10}
              value={severity}
              onChange={(e) => setSeverity(Number(e.target.value))}
              className="absolute inset-0 w-full opacity-0 cursor-pointer h-full"
              style={{ height: '100%' }}
            />
            {/* Thumb indicator */}
            <div
              className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-white shadow transition-all"
              style={{
                left: `calc(${((severity - 1) / 9) * 100}% - 8px)`,
                backgroundColor: severityColor(severity),
              }}
            />
          </div>
          <div className="flex justify-between text-[10px]" style={{ color: '#3D4F66' }}>
            <span>Mild</span>
            <span>Moderate</span>
            <span>Severe</span>
          </div>
        </div>

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="w-full py-2.5 rounded-lg text-sm font-semibold transition-opacity"
          style={{ backgroundColor: '#00D4AA', color: '#080B10', opacity: submitting ? 0.7 : 1 }}
        >
          {submitting ? 'Logging…' : 'Log Symptom'}
        </button>

        {/* Footer link */}
        <Link
          href="/symptoms"
          className="block text-center text-xs mt-3"
          style={{ color: '#526380' }}
          onClick={onClose}
        >
          Add more detail →
        </Link>
      </div>
    </div>
  );
}
