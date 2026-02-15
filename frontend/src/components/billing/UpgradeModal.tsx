'use client';

import { X } from 'lucide-react';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import { PricingTable } from './PricingTable';

export function UpgradeModal() {
  const show = useSubscriptionStore((s) => s.showUpgradeModal);
  const setShow = useSubscriptionStore((s) => s.setShowUpgradeModal);

  if (!show) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={() => setShow(false)} />
      <div className="relative bg-white dark:bg-slate-900 rounded-2xl shadow-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto p-8">
        <button
          onClick={() => setShow(false)}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
        >
          <X className="w-6 h-6" />
        </button>

        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Upgrade Your Plan
          </h2>
          <p className="text-slate-500 dark:text-slate-400 mt-2">
            Unlock unlimited access to all health features
          </p>
        </div>

        <PricingTable />
      </div>
    </div>
  );
}
