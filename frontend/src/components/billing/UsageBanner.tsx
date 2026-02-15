'use client';

import { useState } from 'react';
import { X, Zap } from 'lucide-react';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import Link from 'next/link';

interface UsageBannerProps {
  feature: 'ai_insights' | 'nutrition_scans' | 'doctor_prep' | 'pdf_export';
  featureLabel?: string;
}

export function UsageBanner({ feature, featureLabel }: UsageBannerProps) {
  const [dismissed, setDismissed] = useState(false);
  const subscription = useSubscriptionStore((s) => s.subscription);

  if (dismissed || !subscription) return null;

  const usage = subscription.usage[feature];
  if (!usage || usage.limit === -1) return null;

  // Only show when user has used more than half their limit
  if (usage.used < Math.ceil(usage.limit / 2)) return null;

  const label = featureLabel || feature.replace(/_/g, ' ');
  const remaining = Math.max(0, usage.limit - usage.used);

  return (
    <div className="mb-4 flex items-center justify-between gap-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 px-4 py-3">
      <div className="flex items-center gap-2 text-sm text-amber-800 dark:text-amber-200">
        <Zap className="w-4 h-4" />
        <span>
          {remaining === 0
            ? `You've used all ${usage.limit} ${label} this week.`
            : `${usage.used} of ${usage.limit} ${label} used this week.`}
        </span>
        <Link
          href="/pricing"
          className="font-medium underline hover:no-underline"
        >
          Upgrade for unlimited
        </Link>
      </div>
      <button onClick={() => setDismissed(true)} className="text-amber-500 hover:text-amber-700">
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
