'use client';

import { LabResult, Biomarker } from '@/types';
import { format } from 'date-fns';
import {
  X,
  Calendar,
  Building,
  User,
  FileText,
  ExternalLink,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react';

interface LabResultDetailModalProps {
  labResult: LabResult | null;
  isOpen: boolean;
  onClose: () => void;
}

function statusIcon(status: Biomarker['status']) {
  switch (status) {
    case 'normal':
      return <CheckCircle className="w-4 h-4 text-emerald-500" />;
    case 'borderline':
      return <AlertTriangle className="w-4 h-4 text-amber-500" />;
    case 'abnormal':
      return <AlertCircle className="w-4 h-4 text-orange-500" />;
    case 'critical':
      return <AlertCircle className="w-4 h-4 text-red-500" />;
    default:
      return <Minus className="w-4 h-4 text-slate-400" />;
  }
}

function statusBadge(status: Biomarker['status']) {
  const base = 'text-xs px-2 py-0.5 rounded-full font-medium';
  switch (status) {
    case 'normal':
      return `${base} bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400`;
    case 'borderline':
      return `${base} bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400`;
    case 'abnormal':
      return `${base} bg-orange-50 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400`;
    case 'critical':
      return `${base} bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400`;
    default:
      return `${base} bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300`;
  }
}

function RangeBar({ biomarker }: { biomarker: Biomarker }) {
  // Parse reference_range like "70–99" or "3.5-5.0"
  const match = biomarker.reference_range?.match(/^([\d.]+)\s*[–\-]\s*([\d.]+)$/);
  if (!match) return null;

  const low = parseFloat(match[1]);
  const high = parseFloat(match[2]);
  const value = biomarker.value;

  // Position needle: clamp to [0, 100]%
  const range = high - low;
  const padded = range * 0.2; // 20% padding on each side
  const displayMin = low - padded;
  const displayMax = high + padded;
  const displayRange = displayMax - displayMin;
  const pct = Math.min(100, Math.max(0, ((value - displayMin) / displayRange) * 100));

  const normalLeft = ((low - displayMin) / displayRange) * 100;
  const normalWidth = (range / displayRange) * 100;

  return (
    <div className="mt-2">
      <div className="relative h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-visible">
        {/* Normal zone */}
        <div
          className="absolute h-full rounded-full bg-emerald-200 dark:bg-emerald-900/50"
          style={{ left: `${normalLeft}%`, width: `${normalWidth}%` }}
        />
        {/* Needle */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full border-2 border-white dark:border-slate-900 shadow"
          style={{
            left: `${pct}%`,
            transform: 'translate(-50%, -50%)',
            backgroundColor:
              biomarker.status === 'normal'
                ? '#10b981'
                : biomarker.status === 'borderline'
                ? '#f59e0b'
                : biomarker.status === 'critical'
                ? '#ef4444'
                : '#f97316',
          }}
        />
      </div>
      <div className="flex justify-between text-xs text-slate-400 mt-1">
        <span>{low}</span>
        <span>Ref: {biomarker.reference_range}</span>
        <span>{high}</span>
      </div>
    </div>
  );
}

export function LabResultDetailModal({ labResult, isOpen, onClose }: LabResultDetailModalProps) {
  if (!isOpen || !labResult) return null;

  const abnormal = labResult.biomarkers.filter(
    (b) => b.status === 'abnormal' || b.status === 'critical'
  );
  const borderline = labResult.biomarkers.filter((b) => b.status === 'borderline');
  const normal = labResult.biomarkers.filter((b) => b.status === 'normal');

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Panel */}
      <div
        className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl shadow-2xl"
        style={{
          backgroundColor: 'rgba(10, 14, 20, 0.97)',
          border: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        {/* Header */}
        <div
          className="sticky top-0 z-10 flex items-start justify-between p-6 pb-4"
          style={{
            backgroundColor: 'rgba(10, 14, 20, 0.97)',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
          }}
        >
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-semibold text-slate-100 truncate">
              {labResult.test_type}
            </h2>
            {labResult.test_category && (
              <p className="text-sm text-slate-400 mt-0.5">{labResult.test_category}</p>
            )}
            <div className="flex items-center gap-4 mt-2 text-sm text-slate-400">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                {format(new Date(labResult.test_date), 'MMMM d, yyyy')}
              </span>
              {labResult.lab_name && (
                <span className="flex items-center gap-1">
                  <Building className="w-3.5 h-3.5" />
                  {labResult.lab_name}
                </span>
              )}
              {labResult.ordering_provider && (
                <span className="flex items-center gap-1">
                  <User className="w-3.5 h-3.5" />
                  {labResult.ordering_provider}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="ml-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Status summary pills */}
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-sm text-slate-400">
              {labResult.biomarkers.length} biomarkers
            </span>
            {abnormal.length > 0 && (
              <span className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-red-900/30 text-red-400 border border-red-900/50">
                <AlertCircle className="w-3 h-3" />
                {abnormal.length} abnormal
              </span>
            )}
            {borderline.length > 0 && (
              <span className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-amber-900/30 text-amber-400 border border-amber-900/50">
                <AlertTriangle className="w-3 h-3" />
                {borderline.length} borderline
              </span>
            )}
            {normal.length > 0 && (
              <span className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-emerald-900/30 text-emerald-400 border border-emerald-900/50">
                <CheckCircle className="w-3 h-3" />
                {normal.length} normal
              </span>
            )}
          </div>

          {/* AI Summary */}
          {labResult.ai_summary && (
            <div
              className="p-4 rounded-xl"
              style={{
                backgroundColor: 'rgba(0, 212, 170, 0.06)',
                border: '1px solid rgba(0, 212, 170, 0.15)',
              }}
            >
              <div className="flex items-start gap-2">
                <FileText className="w-4 h-4 text-teal-400 mt-0.5 shrink-0" />
                <div>
                  <p className="text-xs font-medium text-teal-400 mb-1">AI Summary</p>
                  <p className="text-sm text-slate-300 leading-relaxed">{labResult.ai_summary}</p>
                </div>
              </div>
            </div>
          )}

          {/* Anomaly alert */}
          {labResult.anomaly_detected && labResult.anomaly_message && (
            <div
              className="p-4 rounded-xl"
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.06)',
                border: '1px solid rgba(239, 68, 68, 0.2)',
              }}
            >
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
                <p className="text-sm text-red-300">{labResult.anomaly_message}</p>
              </div>
            </div>
          )}

          {/* Biomarkers — out-of-range first */}
          <div>
            <h3 className="text-sm font-medium text-slate-300 mb-3">Biomarker Results</h3>
            <div className="space-y-3">
              {[...abnormal, ...borderline, ...normal].map((biomarker, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl"
                  style={{
                    backgroundColor:
                      biomarker.status === 'critical'
                        ? 'rgba(239, 68, 68, 0.04)'
                        : biomarker.status === 'abnormal'
                        ? 'rgba(249, 115, 22, 0.04)'
                        : biomarker.status === 'borderline'
                        ? 'rgba(245, 158, 11, 0.04)'
                        : 'rgba(255,255,255,0.02)',
                    border:
                      biomarker.status === 'critical'
                        ? '1px solid rgba(239, 68, 68, 0.15)'
                        : biomarker.status === 'abnormal'
                        ? '1px solid rgba(249, 115, 22, 0.15)'
                        : biomarker.status === 'borderline'
                        ? '1px solid rgba(245, 158, 11, 0.12)'
                        : '1px solid rgba(255,255,255,0.05)',
                  }}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      {statusIcon(biomarker.status)}
                      <span className="text-sm font-medium text-slate-200">
                        {biomarker.biomarker_name}
                      </span>
                      {biomarker.biomarker_code && biomarker.biomarker_code !== biomarker.biomarker_name && (
                        <span className="text-xs text-slate-500">({biomarker.biomarker_code})</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-base font-semibold text-slate-100">
                        {biomarker.value}
                        <span className="text-xs font-normal text-slate-400 ml-1">
                          {biomarker.unit}
                        </span>
                      </span>
                      <span className={statusBadge(biomarker.status)}>{biomarker.status}</span>
                    </div>
                  </div>

                  <RangeBar biomarker={biomarker} />

                  {biomarker.interpretation && (
                    <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                      {biomarker.interpretation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Notes */}
          {labResult.notes && (
            <div>
              <h3 className="text-sm font-medium text-slate-300 mb-2">Notes</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{labResult.notes}</p>
            </div>
          )}

          {/* Flags */}
          {labResult.flags && labResult.flags.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-slate-300 mb-2">Flags</h3>
              <div className="flex flex-wrap gap-2">
                {labResult.flags.map((flag, idx) => (
                  <span
                    key={idx}
                    className="text-xs px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 border border-slate-700"
                  >
                    {flag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* PDF link */}
          {labResult.pdf_url && (
            <a
              href={labResult.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-teal-400 hover:text-teal-300 transition-colors"
            >
              <FileText className="w-4 h-4" />
              View original PDF report
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
