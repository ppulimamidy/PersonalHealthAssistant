'use client';

import { useState } from 'react';
import { X, Plus, Trash2 } from 'lucide-react';
import { labResultsService } from '@/services/labResults';
import { CreateLabResultRequest } from '@/types';

interface AddLabResultModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function AddLabResultModal({ isOpen, onClose, onSuccess }: AddLabResultModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<CreateLabResultRequest>({
    test_date: new Date().toISOString().split('T')[0],
    test_type: '',
    test_category: '',
    lab_name: '',
    ordering_provider: '',
    biomarkers: [
      {
        biomarker_code: '',
        biomarker_name: '',
        value: 0,
        unit: '',
      },
    ],
    notes: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await labResultsService.createLabResult(formData);
      onSuccess();
      onClose();
      resetForm();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create lab result');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      test_date: new Date().toISOString().split('T')[0],
      test_type: '',
      test_category: '',
      lab_name: '',
      ordering_provider: '',
      biomarkers: [
        {
          biomarker_code: '',
          biomarker_name: '',
          value: 0,
          unit: '',
        },
      ],
      notes: '',
    });
    setError(null);
  };

  const addBiomarker = () => {
    setFormData({
      ...formData,
      biomarkers: [
        ...formData.biomarkers,
        {
          biomarker_code: '',
          biomarker_name: '',
          value: 0,
          unit: '',
        },
      ],
    });
  };

  const removeBiomarker = (index: number) => {
    setFormData({
      ...formData,
      biomarkers: formData.biomarkers.filter((_, i) => i !== index),
    });
  };

  const updateBiomarker = (index: number, field: string, value: any) => {
    const updated = [...formData.biomarkers];
    updated[index] = { ...updated[index], [field]: value };
    setFormData({ ...formData, biomarkers: updated });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 p-6 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            Add Lab Result
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Test Date *
              </label>
              <input
                type="date"
                required
                value={formData.test_date}
                onChange={(e) => setFormData({ ...formData, test_date: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-slate-700 dark:text-slate-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Test Type *
              </label>
              <input
                type="text"
                required
                placeholder="e.g., Lipid Panel, CBC"
                value={formData.test_type}
                onChange={(e) => setFormData({ ...formData, test_type: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-slate-700 dark:text-slate-100"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Test Category
              </label>
              <input
                type="text"
                placeholder="e.g., Cardiovascular"
                value={formData.test_category}
                onChange={(e) => setFormData({ ...formData, test_category: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-slate-700 dark:text-slate-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Lab Name
              </label>
              <input
                type="text"
                placeholder="e.g., Quest Diagnostics"
                value={formData.lab_name}
                onChange={(e) => setFormData({ ...formData, lab_name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-slate-700 dark:text-slate-100"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Ordering Provider
            </label>
            <input
              type="text"
              placeholder="e.g., Dr. Smith"
              value={formData.ordering_provider}
              onChange={(e) => setFormData({ ...formData, ordering_provider: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-slate-700 dark:text-slate-100"
            />
          </div>

          {/* Biomarkers */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Biomarkers *
              </label>
              <button
                type="button"
                onClick={addBiomarker}
                className="flex items-center gap-1 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
              >
                <Plus className="w-4 h-4" />
                Add Biomarker
              </button>
            </div>

            <div className="space-y-4">
              {formData.biomarkers.map((biomarker, index) => (
                <div
                  key={index}
                  className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                      Biomarker {index + 1}
                    </span>
                    {formData.biomarkers.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeBiomarker(index)}
                        className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <input
                      type="text"
                      required
                      placeholder="Code (e.g., CHOL)"
                      value={biomarker.biomarker_code}
                      onChange={(e) => updateBiomarker(index, 'biomarker_code', e.target.value)}
                      className="px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-slate-700 dark:text-slate-100"
                    />
                    <input
                      type="text"
                      required
                      placeholder="Name (e.g., Total Cholesterol)"
                      value={biomarker.biomarker_name}
                      onChange={(e) => updateBiomarker(index, 'biomarker_name', e.target.value)}
                      className="px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-slate-700 dark:text-slate-100"
                    />
                    <input
                      type="number"
                      step="0.01"
                      required
                      placeholder="Value"
                      value={biomarker.value}
                      onChange={(e) => updateBiomarker(index, 'value', parseFloat(e.target.value))}
                      className="px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-slate-700 dark:text-slate-100"
                    />
                    <input
                      type="text"
                      required
                      placeholder="Unit (e.g., mg/dL)"
                      value={biomarker.unit}
                      onChange={(e) => updateBiomarker(index, 'unit', e.target.value)}
                      className="px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-slate-700 dark:text-slate-100"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Notes
            </label>
            <textarea
              rows={3}
              placeholder="Additional notes about this lab result..."
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-slate-700 dark:text-slate-100"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-700">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Adding...' : 'Add Lab Result'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
