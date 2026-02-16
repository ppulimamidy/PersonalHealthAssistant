'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { symptomsService } from '@/services/symptoms';
import { useAuth } from '@/hooks/useAuth';
import { Plus, FileText, Edit, Trash2, AlertCircle, TrendingUp, Calendar } from 'lucide-react';
import type { SymptomJournalEntry, CreateSymptomRequest } from '@/types';

export function SymptomsView() {
  const { user, isLoading: isAuthLoading } = useAuth(true);
  const queryClient = useQueryClient();

  const [showForm, setShowForm] = useState(false);
  const [editingSymptom, setEditingSymptom] = useState<SymptomJournalEntry | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'journal' | 'analytics'>('journal');

  // Fetch symptoms
  const { data: symptomsData, isLoading: symptomsLoading } = useQuery({
    queryKey: ['symptoms', 30],
    queryFn: () => symptomsService.getSymptoms({ days: 30 }),
    enabled: Boolean(user) && !isAuthLoading,
  });

  // Fetch analytics
  const { data: analyticsData, isLoading: analyticsLoading } = useQuery({
    queryKey: ['symptom-analytics', 30],
    queryFn: () => symptomsService.getAnalytics(30),
    enabled: Boolean(user) && !isAuthLoading && viewMode === 'analytics',
  });

  const symptoms = symptomsData?.symptoms ?? [];

  // Delete mutation
  const deleteSymptomMutation = useMutation({
    mutationFn: (id: string) => symptomsService.deleteSymptom(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['symptoms'] });
      queryClient.invalidateQueries({ queryKey: ['symptom-analytics'] });
      setError(null);
    },
    onError: (e: unknown) => {
      const msg = e instanceof Error ? e.message : 'Failed to delete symptom';
      setError(msg);
    },
  });

  const getSeverityLabel = (severity: number) => {
    if (severity <= 3) return { label: 'Mild', color: 'text-green-600 dark:text-green-400' };
    if (severity <= 6) return { label: 'Moderate', color: 'text-yellow-600 dark:text-yellow-400' };
    return { label: 'Severe', color: 'text-red-600 dark:text-red-400' };
  };

  if (isAuthLoading || symptomsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-slate-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Symptom Journal
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            Track symptoms, identify patterns, and correlate with lifestyle factors
          </p>
        </div>
        <Button
          onClick={() => {
            setShowForm(true);
            setEditingSymptom(null);
          }}
        >
          <Plus className="w-4 h-4 mr-1" />
          Log Symptom
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-800 dark:text-red-200">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* View Tabs */}
      <div className="flex gap-2 border-b border-slate-200 dark:border-slate-700">
        <button
          onClick={() => setViewMode('journal')}
          className={`px-4 py-2 font-medium transition-colors ${
            viewMode === 'journal'
              ? 'text-primary-600 dark:text-primary-400 border-b-2 border-primary-600 dark:border-primary-400'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          <FileText className="w-4 h-4 inline mr-1" />
          Journal
        </button>
        <button
          onClick={() => setViewMode('analytics')}
          className={`px-4 py-2 font-medium transition-colors ${
            viewMode === 'analytics'
              ? 'text-primary-600 dark:text-primary-400 border-b-2 border-primary-600 dark:border-primary-400'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          <TrendingUp className="w-4 h-4 inline mr-1" />
          Analytics
        </button>
      </div>

      {/* Journal View */}
      {viewMode === 'journal' && (
        <Card>
          <CardHeader>
            <CardTitle>Symptom Entries (Last 30 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            {symptoms.length === 0 ? (
              <div className="text-center py-12 text-slate-500 dark:text-slate-400">
                <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium mb-2">No symptoms logged yet</p>
                <p className="text-sm">
                  Start tracking your symptoms to identify patterns and triggers
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {symptoms.map((symptom) => {
                  const severityInfo = getSeverityLabel(symptom.severity);
                  return (
                    <div
                      key={symptom.id}
                      className="flex items-start justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="font-semibold text-slate-900 dark:text-slate-100 capitalize">
                            {symptom.symptom_type.replace(/_/g, ' ')}
                          </div>
                          <div className={`text-sm font-medium ${severityInfo.color}`}>
                            {severityInfo.label} ({symptom.severity}/10)
                          </div>
                          <div className="flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400">
                            <Calendar className="w-4 h-4" />
                            {new Date(symptom.symptom_date).toLocaleDateString()}
                          </div>
                        </div>
                        {symptom.location && (
                          <div className="text-sm text-slate-600 dark:text-slate-400 mb-1">
                            Location: {symptom.location}
                          </div>
                        )}
                        {symptom.triggers && symptom.triggers.length > 0 && (
                          <div className="text-sm text-slate-600 dark:text-slate-400 mb-1">
                            Triggers: {symptom.triggers.join(', ')}
                          </div>
                        )}
                        {symptom.notes && (
                          <div className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                            {symptom.notes}
                          </div>
                        )}
                        {symptom.mood && (
                          <div className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                            Mood: {symptom.mood}
                            {symptom.stress_level && ` • Stress: ${symptom.stress_level}/10`}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setEditingSymptom(symptom);
                            setShowForm(true);
                          }}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            if (confirm('Delete this symptom entry?')) {
                              deleteSymptomMutation.mutate(symptom.id);
                            }
                          }}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Analytics View */}
      {viewMode === 'analytics' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {analyticsLoading ? (
            <div className="col-span-2 text-center py-12 text-slate-500">
              Loading analytics...
            </div>
          ) : analyticsData ? (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Overview</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">Total Entries</div>
                      <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                        {analyticsData.total_entries}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">Average Severity</div>
                      <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                        {analyticsData.average_severity.toFixed(1)}/10
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Severity Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-green-600 dark:text-green-400">Mild (1-3)</span>
                      <span className="font-semibold">{analyticsData.severity_distribution.mild}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-yellow-600 dark:text-yellow-400">
                        Moderate (4-6)
                      </span>
                      <span className="font-semibold">{analyticsData.severity_distribution.moderate}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-red-600 dark:text-red-400">Severe (7-10)</span>
                      <span className="font-semibold">{analyticsData.severity_distribution.severe}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {analyticsData.symptom_types.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Most Common Symptoms</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analyticsData.symptom_types.slice(0, 5).map((st) => (
                        <div key={st.symptom_type} className="flex justify-between items-center">
                          <span className="text-sm text-slate-700 dark:text-slate-300 capitalize">
                            {st.symptom_type.replace(/_/g, ' ')}
                          </span>
                          <span className="font-semibold">{st.count}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {analyticsData.most_common_triggers.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Common Triggers</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analyticsData.most_common_triggers.slice(0, 5).map((trigger) => (
                        <div key={trigger.trigger} className="flex justify-between items-center">
                          <span className="text-sm text-slate-700 dark:text-slate-300">
                            {trigger.trigger}
                          </span>
                          <span className="font-semibold">{trigger.count}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <div className="col-span-2 text-center py-12 text-slate-500 dark:text-slate-400">
              No data available yet. Start logging symptoms to see analytics.
            </div>
          )}
        </div>
      )}

      {/* Form Modal */}
      {showForm && (
        <SymptomForm
          symptom={editingSymptom}
          onClose={() => {
            setShowForm(false);
            setEditingSymptom(null);
          }}
          onSuccess={() => {
            setShowForm(false);
            setEditingSymptom(null);
            queryClient.invalidateQueries({ queryKey: ['symptoms'] });
            queryClient.invalidateQueries({ queryKey: ['symptom-analytics'] });
          }}
        />
      )}
    </div>
  );
}

// Symptom Form Component
function SymptomForm({
  symptom,
  onClose,
  onSuccess,
}: {
  symptom: SymptomJournalEntry | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState<CreateSymptomRequest>({
    symptom_date: symptom?.symptom_date ?? new Date().toISOString().split('T')[0],
    symptom_type: symptom?.symptom_type ?? 'pain',
    severity: symptom?.severity ?? 5,
    location: symptom?.location,
    duration_minutes: symptom?.duration_minutes,
    triggers: symptom?.triggers ?? [],
    associated_symptoms: symptom?.associated_symptoms ?? [],
    medications_taken: symptom?.medications_taken ?? [],
    notes: symptom?.notes,
    mood: symptom?.mood,
    stress_level: symptom?.stress_level,
    sleep_hours_previous_night: symptom?.sleep_hours_previous_night,
  });

  const [triggerInput, setTriggerInput] = useState('');

  const mutation = useMutation({
    mutationFn: (data: CreateSymptomRequest) =>
      symptom
        ? symptomsService.updateSymptom(symptom.id, data)
        : symptomsService.createSymptom(data),
    onSuccess,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  const addTrigger = () => {
    if (triggerInput.trim()) {
      setFormData({
        ...formData,
        triggers: [...(formData.triggers ?? []), triggerInput.trim()],
      });
      setTriggerInput('');
    }
  };

  const removeTrigger = (index: number) => {
    setFormData({
      ...formData,
      triggers: formData.triggers?.filter((_, i) => i !== index),
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4">
            {symptom ? 'Edit Symptom' : 'Log Symptom'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Date *
                </label>
                <input
                  type="date"
                  value={formData.symptom_date}
                  onChange={(e) => setFormData({ ...formData, symptom_date: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Symptom Type *
                </label>
                <select
                  value={formData.symptom_type}
                  onChange={(e) => setFormData({ ...formData, symptom_type: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                  required
                >
                  <option value="pain">Pain</option>
                  <option value="fatigue">Fatigue</option>
                  <option value="nausea">Nausea</option>
                  <option value="headache">Headache</option>
                  <option value="digestive">Digestive</option>
                  <option value="mental_health">Mental Health</option>
                  <option value="respiratory">Respiratory</option>
                  <option value="skin">Skin</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Severity: {formData.severity}/10 *
              </label>
              <input
                type="range"
                min="1"
                max="10"
                value={formData.severity}
                onChange={(e) => setFormData({ ...formData, severity: parseInt(e.target.value) })}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mt-1">
                <span>Mild</span>
                <span>Moderate</span>
                <span>Severe</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Location
                </label>
                <input
                  type="text"
                  placeholder="e.g., Lower back, Head"
                  value={formData.location ?? ''}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Duration (minutes)
                </label>
                <input
                  type="number"
                  value={formData.duration_minutes ?? ''}
                  onChange={(e) =>
                    setFormData({ ...formData, duration_minutes: parseInt(e.target.value) || undefined })
                  }
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Triggers
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={triggerInput}
                  onChange={(e) => setTriggerInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTrigger())}
                  placeholder="e.g., Stress, Spicy food"
                  className="flex-1 px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                />
                <Button type="button" onClick={addTrigger} size="sm">
                  Add
                </Button>
              </div>
              {formData.triggers && formData.triggers.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {formData.triggers.map((trigger, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-1 px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded text-sm"
                    >
                      <span>{trigger}</span>
                      <button
                        type="button"
                        onClick={() => removeTrigger(index)}
                        className="text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Mood
                </label>
                <select
                  value={formData.mood ?? ''}
                  onChange={(e) => setFormData({ ...formData, mood: e.target.value || undefined })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                >
                  <option value="">Select mood...</option>
                  <option value="happy">Happy</option>
                  <option value="anxious">Anxious</option>
                  <option value="stressed">Stressed</option>
                  <option value="sad">Sad</option>
                  <option value="neutral">Neutral</option>
                  <option value="irritable">Irritable</option>
                  <option value="energetic">Energetic</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Stress Level (1-10)
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={formData.stress_level ?? ''}
                  onChange={(e) =>
                    setFormData({ ...formData, stress_level: parseInt(e.target.value) || undefined })
                  }
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                />
              </div>
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

            <div className="flex gap-3 pt-4">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? 'Saving...' : symptom ? 'Update' : 'Log Symptom'}
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
