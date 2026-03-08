'use client';

import { useState, useRef } from 'react';
import {
  X,
  Camera,
  Image as ImageIcon,
  FileText,
  File as FileIcon,
  Loader2,
  Sparkles,
  CheckCircle,
  Plus,
  Trash2,
  AlertCircle,
} from 'lucide-react';
import { labResultsService } from '@/services/labResults';
import { LabResultScanResult, CreateLabResultRequest } from '@/types';

interface LabResultScanModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApply: (prefill: CreateLabResultRequest) => void;
}

type Phase = 'upload' | 'review';

export function LabResultScanModal({ isOpen, onClose, onApply }: LabResultScanModalProps) {
  const [phase, setPhase] = useState<Phase>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<LabResultScanResult | null>(null);

  // Editable extraction state
  const [testType, setTestType] = useState('');
  const [testDate, setTestDate] = useState('');
  const [labName, setLabName] = useState('');
  const [orderingProvider, setOrderingProvider] = useState('');
  const [notes, setNotes] = useState('');
  const [biomarkers, setBiomarkers] = useState<
    Array<{ biomarker_code: string; biomarker_name: string; value: number; unit: string; reference_range?: string; status: string }>
  >([]);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const isImageFile = (file: File) => file.type.startsWith('image/');

  const isAcceptedFile = (file: File) =>
    file.type.startsWith('image/') ||
    file.type === 'application/pdf' ||
    file.name.endsWith('.pdf') ||
    file.type.includes('word') ||
    file.type.includes('officedocument') ||
    file.name.endsWith('.docx') ||
    file.name.endsWith('.doc');

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setScanError(null);
    // Only generate an image preview for image files
    if (isImageFile(file)) {
      setPreview(URL.createObjectURL(file));
    } else {
      setPreview(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && isAcceptedFile(file)) {
      handleFileSelect(file);
    }
  };

  const handleScan = async () => {
    if (!selectedFile) return;
    setScanning(true);
    setScanError(null);
    try {
      const result = await labResultsService.scanLabResultImage(selectedFile);
      setScanResult(result);

      // Pre-populate editable fields
      setTestType(result.test_type || '');
      setTestDate(result.test_date || new Date().toISOString().split('T')[0]);
      setLabName(result.lab_name || '');
      setOrderingProvider(result.ordering_provider || '');
      setNotes(result.notes || '');
      setBiomarkers(
        result.biomarkers.length > 0
          ? result.biomarkers.map(b => ({ ...b }))
          : [{ biomarker_code: '', biomarker_name: '', value: 0, unit: '', status: 'normal' }]
      );

      setPhase('review');
    } catch (err: any) {
      setScanError(err.response?.data?.detail || 'Failed to scan image. Please try again.');
    } finally {
      setScanning(false);
    }
  };

  const handleAddBiomarker = () => {
    setBiomarkers([
      ...biomarkers,
      { biomarker_code: '', biomarker_name: '', value: 0, unit: '', status: 'normal' },
    ]);
  };

  const handleRemoveBiomarker = (idx: number) => {
    setBiomarkers(biomarkers.filter((_, i) => i !== idx));
  };

  const handleBiomarkerChange = (idx: number, field: string, val: string | number) => {
    const updated = [...biomarkers];
    updated[idx] = { ...updated[idx], [field]: val };
    setBiomarkers(updated);
  };

  const handleApply = () => {
    if (!testType.trim()) return;
    const prefill: CreateLabResultRequest = {
      test_date: testDate || new Date().toISOString().split('T')[0],
      test_type: testType.trim(),
      lab_name: labName || undefined,
      ordering_provider: orderingProvider || undefined,
      notes: notes || undefined,
      biomarkers: biomarkers
        .filter(b => b.biomarker_name.trim())
        .map(b => ({
          biomarker_code: b.biomarker_code || b.biomarker_name.slice(0, 6).toUpperCase(),
          biomarker_name: b.biomarker_name,
          value: b.value,
          unit: b.unit,
          reference_range: b.reference_range,
        })),
    };
    onApply(prefill);
    handleClose();
  };

  const handleClose = () => {
    setPhase('upload');
    setSelectedFile(null);
    setPreview(null);
    setScanError(null);
    setScanResult(null);
    setBiomarkers([]);
    onClose();
  };

  const confidenceColor =
    (scanResult?.confidence ?? 0) >= 0.8
      ? 'text-emerald-500'
      : (scanResult?.confidence ?? 0) >= 0.5
      ? 'text-amber-500'
      : 'text-red-400';

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <Sparkles className="w-5 h-5 text-teal-500" />
            <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
              {phase === 'upload' ? 'Scan Lab Report' : 'Review Extracted Results'}
            </h2>
            {phase === 'review' && scanResult && (
              <span className={`text-xs font-medium ${confidenceColor}`}>
                {Math.round(scanResult.confidence * 100)}% confidence
              </span>
            )}
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {/* ── Upload Phase ── */}
          {phase === 'upload' && (
            <div className="p-6 space-y-5">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Upload your lab report — photo, PDF, or Word document. Claude AI will extract all biomarker values automatically.
              </p>

              {/* Drop zone */}
              <div
                onDrop={handleDrop}
                onDragOver={e => e.preventDefault()}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-xl p-8 text-center cursor-pointer hover:border-teal-500 dark:hover:border-teal-400 transition-colors"
              >
                {selectedFile ? (
                  preview ? (
                    /* Image preview */
                    <img
                      src={preview}
                      alt="Lab report preview"
                      className="max-h-48 mx-auto rounded-lg object-contain"
                    />
                  ) : (
                    /* PDF / Doc file indicator */
                    <div className="space-y-3">
                      {selectedFile.name.endsWith('.pdf') || selectedFile.type === 'application/pdf' ? (
                        <FileText className="w-14 h-14 text-red-400 mx-auto" />
                      ) : (
                        <FileIcon className="w-14 h-14 text-blue-400 mx-auto" />
                      )}
                      <p className="font-medium text-slate-700 dark:text-slate-300 text-sm truncate px-4">
                        {selectedFile.name}
                      </p>
                      <p className="text-xs text-slate-400">
                        {(selectedFile.size / 1024 / 1024).toFixed(1)} MB — click to change
                      </p>
                    </div>
                  )
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center justify-center gap-3">
                      <ImageIcon className="w-8 h-8 text-slate-400" />
                      <FileText className="w-8 h-8 text-slate-400" />
                      <FileIcon className="w-8 h-8 text-slate-400" />
                    </div>
                    <p className="text-slate-600 dark:text-slate-400">
                      Drag & drop your lab report here, or click to browse
                    </p>
                    <p className="text-xs text-slate-400">
                      Images (JPG, PNG) · PDF · Word (DOCX) — max 20 MB
                    </p>
                  </div>
                )}
              </div>

              {/* Buttons */}
              <div className="flex gap-3 flex-wrap">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center gap-2 px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                >
                  <ImageIcon className="w-4 h-4" />
                  Photo / PDF / Doc
                </button>
                <button
                  type="button"
                  onClick={() => cameraInputRef.current?.click()}
                  className="flex items-center gap-2 px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                >
                  <Camera className="w-4 h-4" />
                  Camera
                </button>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,application/pdf,.pdf,.docx,.doc,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword"
                className="hidden"
                onChange={e => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
              />
              <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                className="hidden"
                onChange={e => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
              />

              {scanError && (
                <div className="flex items-start gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                  <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
                  <p className="text-sm text-red-600 dark:text-red-400">{scanError}</p>
                </div>
              )}
            </div>
          )}

          {/* ── Review Phase ── */}
          {phase === 'review' && (
            <div className="p-6 space-y-5">
              {/* File thumbnail + meta row */}
              <div className="flex gap-4">
                {preview ? (
                  <img
                    src={preview}
                    alt="Lab report"
                    className="w-24 h-24 rounded-lg object-cover border border-slate-200 dark:border-slate-700 shrink-0"
                  />
                ) : selectedFile && (
                  <div className="w-24 h-24 rounded-lg border border-slate-200 dark:border-slate-700 flex flex-col items-center justify-center gap-1 bg-slate-50 dark:bg-slate-700/50 shrink-0">
                    {selectedFile.name.toLowerCase().endsWith('.pdf') || selectedFile.type === 'application/pdf' ? (
                      <FileText className="w-8 h-8 text-red-400" />
                    ) : (
                      <FileIcon className="w-8 h-8 text-blue-400" />
                    )}
                    <span className="text-xs text-slate-500 dark:text-slate-400 text-center px-1 leading-tight truncate w-full text-center">
                      {selectedFile.name.split('.').pop()?.toUpperCase()}
                    </span>
                  </div>
                )}
                <div className="flex-1 grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                      Test Type *
                    </label>
                    <input
                      value={testType}
                      onChange={e => setTestType(e.target.value)}
                      placeholder="e.g., Lipid Panel"
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-slate-100 focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                      Test Date
                    </label>
                    <input
                      type="date"
                      value={testDate}
                      onChange={e => setTestDate(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-slate-100 focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                      Lab Name
                    </label>
                    <input
                      value={labName}
                      onChange={e => setLabName(e.target.value)}
                      placeholder="e.g., Quest Diagnostics"
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-slate-100 focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                      Ordering Provider
                    </label>
                    <input
                      value={orderingProvider}
                      onChange={e => setOrderingProvider(e.target.value)}
                      placeholder="e.g., Dr. Smith"
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-slate-100 focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                </div>
              </div>

              {/* Biomarker table */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                    Biomarkers ({biomarkers.length} extracted)
                  </h3>
                  <button
                    type="button"
                    onClick={handleAddBiomarker}
                    className="flex items-center gap-1 text-xs text-teal-600 dark:text-teal-400 hover:text-teal-700"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Add row
                  </button>
                </div>

                <div className="rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 dark:bg-slate-700/50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-slate-500 dark:text-slate-400">Code</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-slate-500 dark:text-slate-400">Name</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-slate-500 dark:text-slate-400">Value</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-slate-500 dark:text-slate-400">Unit</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-slate-500 dark:text-slate-400">Ref Range</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-slate-500 dark:text-slate-400">Status</th>
                        <th className="px-1 py-2" />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                      {biomarkers.map((b, idx) => (
                        <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-700/30">
                          <td className="px-2 py-1.5">
                            <input
                              value={b.biomarker_code}
                              onChange={e => handleBiomarkerChange(idx, 'biomarker_code', e.target.value)}
                              className="w-16 px-2 py-1 text-xs border border-slate-200 dark:border-slate-600 rounded dark:bg-slate-700 dark:text-slate-100"
                              placeholder="CHOL"
                            />
                          </td>
                          <td className="px-2 py-1.5">
                            <input
                              value={b.biomarker_name}
                              onChange={e => handleBiomarkerChange(idx, 'biomarker_name', e.target.value)}
                              className="w-full min-w-[120px] px-2 py-1 text-xs border border-slate-200 dark:border-slate-600 rounded dark:bg-slate-700 dark:text-slate-100"
                              placeholder="Total Cholesterol"
                            />
                          </td>
                          <td className="px-2 py-1.5">
                            <input
                              type="number"
                              step="0.01"
                              value={b.value}
                              onChange={e => handleBiomarkerChange(idx, 'value', parseFloat(e.target.value) || 0)}
                              className="w-20 px-2 py-1 text-xs border border-slate-200 dark:border-slate-600 rounded dark:bg-slate-700 dark:text-slate-100"
                            />
                          </td>
                          <td className="px-2 py-1.5">
                            <input
                              value={b.unit}
                              onChange={e => handleBiomarkerChange(idx, 'unit', e.target.value)}
                              className="w-20 px-2 py-1 text-xs border border-slate-200 dark:border-slate-600 rounded dark:bg-slate-700 dark:text-slate-100"
                              placeholder="mg/dL"
                            />
                          </td>
                          <td className="px-2 py-1.5">
                            <input
                              value={b.reference_range || ''}
                              onChange={e => handleBiomarkerChange(idx, 'reference_range', e.target.value)}
                              className="w-28 px-2 py-1 text-xs border border-slate-200 dark:border-slate-600 rounded dark:bg-slate-700 dark:text-slate-100"
                              placeholder="100-199"
                            />
                          </td>
                          <td className="px-2 py-1.5">
                            <select
                              value={b.status}
                              onChange={e => handleBiomarkerChange(idx, 'status', e.target.value)}
                              className="px-2 py-1 text-xs border border-slate-200 dark:border-slate-600 rounded dark:bg-slate-700 dark:text-slate-100"
                            >
                              <option value="normal">Normal</option>
                              <option value="borderline">Borderline</option>
                              <option value="abnormal">Abnormal</option>
                              <option value="critical">Critical</option>
                            </select>
                          </td>
                          <td className="px-1 py-1.5">
                            {biomarkers.length > 1 && (
                              <button
                                type="button"
                                onClick={() => handleRemoveBiomarker(idx)}
                                className="text-slate-400 hover:text-red-500 transition-colors"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Notes
                </label>
                <textarea
                  value={notes}
                  onChange={e => setNotes(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-700 dark:text-slate-100 focus:ring-2 focus:ring-teal-500"
                  placeholder="Any additional notes..."
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between gap-3">
          {phase === 'upload' ? (
            <>
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleScan}
                disabled={!selectedFile || scanning}
                className="flex items-center gap-2 px-5 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {scanning ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Extracting…
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Extract Results
                  </>
                )}
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => setPhase('upload')}
                className="px-4 py-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                ← Rescan
              </button>
              <button
                type="button"
                onClick={handleApply}
                disabled={!testType.trim()}
                className="flex items-center gap-2 px-5 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <CheckCircle className="w-4 h-4" />
                Use These Results
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
