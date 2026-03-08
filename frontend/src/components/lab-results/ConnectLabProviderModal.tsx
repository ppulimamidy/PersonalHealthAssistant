'use client';

import { useState, useEffect } from 'react';
import { X, Link2, Clock, CheckCircle2, ChevronRight } from 'lucide-react';
import { labResultsService } from '@/services/labResults';
import { LabProvider } from '@/types';

interface ConnectLabProviderModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Static fallback provider list (shown while loading or on error)
const FALLBACK_PROVIDERS: LabProvider[] = [
  {
    id: 'labcorp',
    name: 'LabCorp',
    description: 'Access your LabCorp results directly. Covers hundreds of diagnostic tests.',
    is_available: false,
    data_types: ['Blood panels', 'Urinalysis', 'Genetic tests', 'Pathology'],
  },
  {
    id: 'quest',
    name: 'Quest Diagnostics',
    description: 'Connect your Quest Diagnostics account to auto-import lab results.',
    is_available: false,
    data_types: ['Comprehensive metabolic', 'Lipid panels', 'CBC', 'Hormone panels'],
  },
  {
    id: 'health_gorilla',
    name: 'Health Gorilla',
    description: 'Aggregated lab data from hundreds of labs via Health Gorilla network.',
    is_available: false,
    data_types: ['All major lab types', 'Multi-lab aggregation'],
  },
  {
    id: 'labcorp_ondemand',
    name: 'LabCorp On Demand',
    description: 'Order and receive direct-to-consumer lab tests without a doctor\'s order.',
    is_available: false,
    data_types: ['Direct-to-consumer panels', 'Wellness tests'],
  },
];

const PROVIDER_ICONS: Record<string, string> = {
  labcorp: '🧪',
  quest: '🔬',
  health_gorilla: '🦅',
  labcorp_ondemand: '📦',
};

export function ConnectLabProviderModal({ isOpen, onClose }: ConnectLabProviderModalProps) {
  const [providers, setProviders] = useState<LabProvider[]>(FALLBACK_PROVIDERS);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    labResultsService
      .getLabProviders()
      .then(data => setProviders(data.length ? data : FALLBACK_PROVIDERS))
      .catch(() => setProviders(FALLBACK_PROVIDERS));
  }, [isOpen]);

  const handleConnect = async (provider: LabProvider) => {
    if (provider.is_available) return; // handle live connection in future
    setConnecting(provider.id);
    try {
      const res = await labResultsService.connectLabProvider(provider.id);
      setToast(res.message);
      setTimeout(() => setToast(null), 4000);
    } catch {
      setToast('Failed to reach provider. Please try again.');
      setTimeout(() => setToast(null), 4000);
    } finally {
      setConnecting(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl max-w-lg w-full max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <Link2 className="w-5 h-5 text-teal-500" />
            <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
              Connect Lab Provider
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Connect to your lab provider to automatically import lab results. We're building
            integrations with the most popular providers.
          </p>

          {providers.map(provider => (
            <div
              key={provider.id}
              className="relative p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-teal-400 dark:hover:border-teal-500 transition-colors"
            >
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div className="w-12 h-12 rounded-xl bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-2xl shrink-0">
                  {PROVIDER_ICONS[provider.id] ?? '🏥'}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-sm">
                      {provider.name}
                    </h3>
                    {!provider.is_available && (
                      <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">
                        <Clock className="w-3 h-3" />
                        Coming soon
                      </span>
                    )}
                    {provider.is_available && (
                      <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300">
                        <CheckCircle2 className="w-3 h-3" />
                        Available
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">
                    {provider.description}
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {provider.data_types.map(dt => (
                      <span
                        key={dt}
                        className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400"
                      >
                        {dt}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Action */}
                <button
                  onClick={() => handleConnect(provider)}
                  disabled={connecting === provider.id}
                  className={`shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    provider.is_available
                      ? 'bg-teal-600 text-white hover:bg-teal-700'
                      : 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600'
                  } disabled:opacity-50`}
                >
                  {connecting === provider.id ? (
                    'Notifying…'
                  ) : provider.is_available ? (
                    <>Connect <ChevronRight className="w-3 h-3" /></>
                  ) : (
                    'Notify me'
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Toast */}
        {toast && (
          <div className="mx-6 mb-4 p-3 rounded-lg bg-teal-50 dark:bg-teal-900/20 border border-teal-200 dark:border-teal-800 text-sm text-teal-700 dark:text-teal-300">
            {toast}
          </div>
        )}

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors text-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
