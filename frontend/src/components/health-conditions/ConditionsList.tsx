'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { healthConditionsService } from '@/services/healthConditions';
import { AlertCircle, Trash2, Edit2, Activity, X, Check } from 'lucide-react';
import type { HealthCondition } from '@/types';

const CATEGORY_LABELS: Record<string, string> = {
  metabolic: 'Metabolic',
  cardiovascular: 'Cardiovascular',
  autoimmune: 'Autoimmune',
  digestive: 'Digestive',
  mental_health: 'Mental Health',
  other: 'Other',
};

const SEVERITY_STYLES: Record<string, string> = {
  mild: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  moderate: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  severe: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
};

export function ConditionsList() {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editNotes, setEditNotes] = useState('');

  const { data: conditions, isLoading } = useQuery<HealthCondition[]>({
    queryKey: ['health-conditions'],
    queryFn: () => healthConditionsService.listConditions(),
    staleTime: 1000 * 60 * 5,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => healthConditionsService.deleteCondition(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['health-conditions'] }),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<HealthCondition> }) =>
      healthConditionsService.updateCondition(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['health-conditions'] });
      setEditingId(null);
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2].map((i) => (
          <Card key={i} className="animate-pulse">
            <div className="h-5 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-2" />
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
          </Card>
        ))}
      </div>
    );
  }

  if (!conditions || conditions.length === 0) {
    return (
      <Card>
        <div className="text-center py-4">
          <Activity className="w-8 h-8 text-slate-300 dark:text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No health conditions tracked yet.
          </p>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
            Add conditions to get personalized variable tracking.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {conditions.map((c) => (
        <Card key={c.id} className="transition-all hover:shadow-md">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  {c.condition_name}
                </h4>
                <span className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded ${SEVERITY_STYLES[c.severity] || SEVERITY_STYLES.moderate}`}>
                  {c.severity}
                </span>
                {!c.is_active && (
                  <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-400">
                    Inactive
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {CATEGORY_LABELS[c.condition_category] || c.condition_category}
                {c.diagnosed_date && ` · Diagnosed ${c.diagnosed_date}`}
              </p>

              {/* Tracked variables */}
              {c.tracked_variables && c.tracked_variables.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {c.tracked_variables.slice(0, 5).map((v) => (
                    <span
                      key={v}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400"
                    >
                      {v.replace(/_/g, ' ')}
                    </span>
                  ))}
                  {c.tracked_variables.length > 5 && (
                    <span className="text-[10px] text-slate-400">+{c.tracked_variables.length - 5}</span>
                  )}
                </div>
              )}

              {/* Watch metrics */}
              {c.watch_metrics && c.watch_metrics.length > 0 && (
                <div className="mt-1.5">
                  {c.watch_metrics.map((m, i) => (
                    <p key={i} className="text-xs text-slate-500 dark:text-slate-400 flex items-start gap-1">
                      <AlertCircle className="w-3 h-3 text-amber-500 mt-0.5 shrink-0" />
                      {m}
                    </p>
                  ))}
                </div>
              )}

              {/* Notes editing */}
              {editingId === c.id ? (
                <div className="mt-2 flex items-center gap-2">
                  <input
                    type="text"
                    value={editNotes}
                    onChange={(e) => setEditNotes(e.target.value)}
                    className="flex-1 text-xs px-2 py-1 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200"
                    placeholder="Add notes..."
                  />
                  <button
                    onClick={() => updateMutation.mutate({ id: c.id, data: { notes: editNotes } })}
                    className="p-1 text-green-600 hover:text-green-700"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                  <button onClick={() => setEditingId(null)} className="p-1 text-slate-400 hover:text-slate-600">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                c.notes && (
                  <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400 italic">{c.notes}</p>
                )
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-1 ml-2">
              <button
                onClick={() => {
                  setEditingId(c.id);
                  setEditNotes(c.notes || '');
                }}
                className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                title="Edit notes"
              >
                <Edit2 className="w-4 h-4" />
              </button>
              <button
                onClick={() => {
                  if (confirm(`Remove ${c.condition_name}?`)) {
                    deleteMutation.mutate(c.id);
                  }
                }}
                className="p-1.5 text-slate-400 hover:text-red-500"
                title="Delete condition"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
