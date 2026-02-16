'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { healthConditionsService } from '@/services/healthConditions';
import { X, Search, Plus } from 'lucide-react';
import type { ConditionCatalogItem } from '@/types';

interface AddConditionModalProps {
  open: boolean;
  onClose: () => void;
}

export function AddConditionModal({ open, onClose }: AddConditionModalProps) {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [customName, setCustomName] = useState('');
  const [category, setCategory] = useState('other');
  const [severity, setSeverity] = useState('moderate');
  const [notes, setNotes] = useState('');

  const { data: catalog } = useQuery<ConditionCatalogItem[]>({
    queryKey: ['condition-catalog'],
    queryFn: () => healthConditionsService.getCatalog(),
    enabled: open,
    staleTime: 1000 * 60 * 60,
  });

  const addMutation = useMutation({
    mutationFn: (data: {
      condition_name: string;
      condition_category: string;
      severity: string;
      notes?: string;
    }) => healthConditionsService.addCondition(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['health-conditions'] });
      onClose();
      resetForm();
    },
  });

  const resetForm = () => {
    setSearch('');
    setSelectedKey(null);
    setCustomName('');
    setCategory('other');
    setSeverity('moderate');
    setNotes('');
  };

  if (!open) return null;

  const filtered = catalog?.filter(
    (c) =>
      c.label.toLowerCase().includes(search.toLowerCase()) ||
      c.category.toLowerCase().includes(search.toLowerCase()),
  );

  const handleSelect = (item: ConditionCatalogItem) => {
    setSelectedKey(item.key);
    setCustomName(item.label);
    setCategory(item.category);
  };

  const handleSubmit = () => {
    const name = customName.trim();
    if (!name) return;
    addMutation.mutate({
      condition_name: name,
      condition_category: category,
      severity,
      notes: notes.trim() || undefined,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-md mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Add Health Condition
          </h3>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {/* Search catalog */}
          {!selectedKey && (
            <>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search conditions..."
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div className="max-h-48 overflow-y-auto space-y-1">
                {filtered?.map((item) => (
                  <button
                    key={item.key}
                    onClick={() => handleSelect(item)}
                    className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                  >
                    <span className="text-sm font-medium text-slate-800 dark:text-slate-200">
                      {item.label}
                    </span>
                    <span className="ml-2 text-xs text-slate-400 capitalize">{item.category}</span>
                    <span className="ml-1 text-[10px] text-slate-400">
                      ({item.tracked_variable_count} variables)
                    </span>
                  </button>
                ))}

                {/* Custom option */}
                <button
                  onClick={() => {
                    setSelectedKey('custom');
                    setCustomName(search);
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors flex items-center gap-2"
                >
                  <Plus className="w-4 h-4 text-primary-500" />
                  <span className="text-sm text-primary-600 dark:text-primary-400">
                    Add custom: &quot;{search || 'Enter name...'}&quot;
                  </span>
                </button>
              </div>
            </>
          )}

          {/* Selected condition form */}
          {selectedKey && (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                  Condition Name
                </label>
                <input
                  type="text"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200"
                  >
                    <option value="metabolic">Metabolic</option>
                    <option value="cardiovascular">Cardiovascular</option>
                    <option value="autoimmune">Autoimmune</option>
                    <option value="digestive">Digestive</option>
                    <option value="mental_health">Mental Health</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Severity
                  </label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200"
                  >
                    <option value="mild">Mild</option>
                    <option value="moderate">Moderate</option>
                    <option value="severe">Severe</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                  Notes (optional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                  placeholder="Any additional notes..."
                />
              </div>

              <button
                onClick={() => {
                  setSelectedKey(null);
                  setCustomName('');
                }}
                className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
              >
                &larr; Back to search
              </button>
            </>
          )}
        </div>

        {/* Footer */}
        {selectedKey && (
          <div className="px-5 py-4 border-t border-slate-200 dark:border-slate-700 flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!customName.trim() || addMutation.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {addMutation.isPending ? 'Adding...' : 'Add Condition'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
