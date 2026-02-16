'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { medicationsService } from '@/services/medications';
import { useAuth } from '@/hooks/useAuth';
import { Plus, Pill, Edit, Trash2, AlertCircle } from 'lucide-react';
import type { Medication, Supplement, CreateMedicationRequest, CreateSupplementRequest } from '@/types';

export function MedicationsView() {
  const { user, isLoading: isAuthLoading } = useAuth(true);
  const queryClient = useQueryClient();

  const [showMedForm, setShowMedForm] = useState(false);
  const [showSuppForm, setShowSuppForm] = useState(false);
  const [editingMed, setEditingMed] = useState<Medication | null>(null);
  const [editingSupp, setEditingSupp] = useState<Supplement | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch medications
  const { data: medsData, isLoading: medsLoading } = useQuery({
    queryKey: ['medications'],
    queryFn: () => medicationsService.getMedications(),
    enabled: Boolean(user) && !isAuthLoading,
  });

  // Fetch supplements
  const { data: suppsData, isLoading: suppsLoading } = useQuery({
    queryKey: ['supplements'],
    queryFn: () => medicationsService.getSupplements(),
    enabled: Boolean(user) && !isAuthLoading,
  });

  const medications = medsData?.medications ?? [];
  const supplements = suppsData?.supplements ?? [];

  // Delete mutations
  const deleteMedMutation = useMutation({
    mutationFn: (id: string) => medicationsService.deleteMedication(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['medications'] });
      setError(null);
    },
    onError: (e: unknown) => {
      const msg = e instanceof Error ? e.message : 'Failed to delete medication';
      setError(msg);
    },
  });

  const deleteSuppMutation = useMutation({
    mutationFn: (id: string) => medicationsService.deleteSupplement(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['supplements'] });
      setError(null);
    },
    onError: (e: unknown) => {
      const msg = e instanceof Error ? e.message : 'Failed to delete supplement';
      setError(msg);
    },
  });

  if (isAuthLoading || medsLoading || suppsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-slate-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          Medications & Supplements
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          Track your medications, supplements, and adherence
        </p>
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
            <Button
              onClick={() => {
                setShowMedForm(true);
                setEditingMed(null);
              }}
              size="sm"
            >
              <Plus className="w-4 h-4 mr-1" />
              Add Medication
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {medications.length === 0 ? (
            <div className="text-center py-8 text-slate-500 dark:text-slate-400">
              No medications tracked yet. Click "Add Medication" to get started.
            </div>
          ) : (
            <div className="space-y-3">
              {medications.map((med) => (
                <div
                  key={med.id}
                  className="flex items-center justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  <div className="flex-1">
                    <div className="font-semibold text-slate-900 dark:text-slate-100">
                      {med.medication_name}
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                      {med.dosage} • {med.frequency}
                      {med.indication && ` • ${med.indication}`}
                    </div>
                    {!med.is_active && (
                      <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        (Inactive)
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setEditingMed(med);
                        setShowMedForm(true);
                      }}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        if (confirm(`Delete ${med.medication_name}?`)) {
                          deleteMedMutation.mutate(med.id);
                        }
                      }}
                    >
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
            <Button
              onClick={() => {
                setShowSuppForm(true);
                setEditingSupp(null);
              }}
              size="sm"
            >
              <Plus className="w-4 h-4 mr-1" />
              Add Supplement
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {supplements.length === 0 ? (
            <div className="text-center py-8 text-slate-500 dark:text-slate-400">
              No supplements tracked yet. Click "Add Supplement" to get started.
            </div>
          ) : (
            <div className="space-y-3">
              {supplements.map((supp) => (
                <div
                  key={supp.id}
                  className="flex items-center justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  <div className="flex-1">
                    <div className="font-semibold text-slate-900 dark:text-slate-100">
                      {supp.supplement_name}
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                      {supp.dosage} • {supp.frequency}
                      {supp.purpose && ` • ${supp.purpose}`}
                    </div>
                    {!supp.is_active && (
                      <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        (Inactive)
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setEditingSupp(supp);
                        setShowSuppForm(true);
                      }}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        if (confirm(`Delete ${supp.supplement_name}?`)) {
                          deleteSuppMutation.mutate(supp.id);
                        }
                      }}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modals would go here - for now keeping it simple */}
      {showMedForm && (
        <MedicationForm
          medication={editingMed}
          onClose={() => {
            setShowMedForm(false);
            setEditingMed(null);
          }}
          onSuccess={() => {
            setShowMedForm(false);
            setEditingMed(null);
            queryClient.invalidateQueries({ queryKey: ['medications'] });
          }}
        />
      )}

      {showSuppForm && (
        <SupplementForm
          supplement={editingSupp}
          onClose={() => {
            setShowSuppForm(false);
            setEditingSupp(null);
          }}
          onSuccess={() => {
            setShowSuppForm(false);
            setEditingSupp(null);
            queryClient.invalidateQueries({ queryKey: ['supplements'] });
          }}
        />
      )}
    </div>
  );
}

// Medication Form Component
function MedicationForm({
  medication,
  onClose,
  onSuccess,
}: {
  medication: Medication | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState<CreateMedicationRequest>({
    medication_name: medication?.medication_name ?? '',
    dosage: medication?.dosage ?? '',
    frequency: medication?.frequency ?? '',
    route: medication?.route ?? 'oral',
    indication: medication?.indication,
    prescribing_doctor: medication?.prescribing_doctor,
    notes: medication?.notes,
    is_active: medication?.is_active ?? true,
  });

  const mutation = useMutation({
    mutationFn: (data: CreateMedicationRequest) =>
      medication
        ? medicationsService.updateMedication(medication.id, data)
        : medicationsService.createMedication(data),
    onSuccess,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4">
            {medication ? 'Edit Medication' : 'Add Medication'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Medication Name *
              </label>
              <input
                type="text"
                value={formData.medication_name}
                onChange={(e) => setFormData({ ...formData, medication_name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Dosage *
                </label>
                <input
                  type="text"
                  placeholder="e.g., 10mg"
                  value={formData.dosage}
                  onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Frequency *
                </label>
                <input
                  type="text"
                  placeholder="e.g., twice daily"
                  value={formData.frequency}
                  onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                What is it for?
              </label>
              <input
                type="text"
                value={formData.indication ?? ''}
                onChange={(e) => setFormData({ ...formData, indication: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Prescribing Doctor
              </label>
              <input
                type="text"
                value={formData.prescribing_doctor ?? ''}
                onChange={(e) => setFormData({ ...formData, prescribing_doctor: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Notes
              </label>
              <textarea
                value={formData.notes ?? ''}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="w-4 h-4"
              />
              <label htmlFor="is_active" className="text-sm text-slate-700 dark:text-slate-300">
                Currently taking this medication
              </label>
            </div>
            <div className="flex gap-3 pt-4">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? 'Saving...' : medication ? 'Update' : 'Add'}
              </Button>
              <Button type="button" variant="outline" onClick={onClose} className="flex-1">
                Cancel
              </Button>
            </div>
            {mutation.isError && (
              <div className="text-sm text-red-600 dark:text-red-400">
                {mutation.error instanceof Error ? mutation.error.message : 'Failed to save'}
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}

// Supplement Form Component
function SupplementForm({
  supplement,
  onClose,
  onSuccess,
}: {
  supplement: Supplement | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState<CreateSupplementRequest>({
    supplement_name: supplement?.supplement_name ?? '',
    dosage: supplement?.dosage ?? '',
    frequency: supplement?.frequency ?? '',
    form: supplement?.form ?? 'capsule',
    purpose: supplement?.purpose,
    brand: supplement?.brand,
    notes: supplement?.notes,
    is_active: supplement?.is_active ?? true,
  });

  const mutation = useMutation({
    mutationFn: (data: CreateSupplementRequest) =>
      supplement
        ? medicationsService.updateSupplement(supplement.id, data)
        : medicationsService.createSupplement(data),
    onSuccess,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4">
            {supplement ? 'Edit Supplement' : 'Add Supplement'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Supplement Name *
              </label>
              <input
                type="text"
                value={formData.supplement_name}
                onChange={(e) => setFormData({ ...formData, supplement_name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Dosage *
                </label>
                <input
                  type="text"
                  placeholder="e.g., 1000mg"
                  value={formData.dosage}
                  onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Frequency *
                </label>
                <input
                  type="text"
                  placeholder="e.g., once daily"
                  value={formData.frequency}
                  onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Brand
              </label>
              <input
                type="text"
                value={formData.brand ?? ''}
                onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Purpose
              </label>
              <input
                type="text"
                value={formData.purpose ?? ''}
                onChange={(e) => setFormData({ ...formData, purpose: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Notes
              </label>
              <textarea
                value={formData.notes ?? ''}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="supp_is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="w-4 h-4"
              />
              <label htmlFor="supp_is_active" className="text-sm text-slate-700 dark:text-slate-300">
                Currently taking this supplement
              </label>
            </div>
            <div className="flex gap-3 pt-4">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? 'Saving...' : supplement ? 'Update' : 'Add'}
              </Button>
              <Button type="button" variant="outline" onClick={onClose} className="flex-1">
                Cancel
              </Button>
            </div>
            {mutation.isError && (
              <div className="text-sm text-red-600 dark:text-red-400">
                {mutation.error instanceof Error ? mutation.error.message : 'Failed to save'}
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
