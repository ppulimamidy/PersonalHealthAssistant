'use client';

import { useEffect } from 'react';
import { CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import { billingService } from '@/services/billing';
import Link from 'next/link';

export default function BillingSuccessPage() {
  const setSubscription = useSubscriptionStore((s) => s.setSubscription);

  useEffect(() => {
    // Refresh subscription data after successful checkout
    billingService
      .getSubscription()
      .then(setSubscription)
      .catch(() => {});
  }, [setSubscription]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-6">
      <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-6">
        <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
      </div>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
        Welcome to Pro!
      </h1>
      <p className="text-slate-600 dark:text-slate-400 max-w-md mb-8">
        Your subscription is active. You now have access to unlimited insights,
        nutrition scans, and more.
      </p>
      <div className="flex gap-4">
        <Link href="/timeline">
          <Button>Go to Timeline</Button>
        </Link>
        <Link href="/settings">
          <Button variant="outline">Manage Subscription</Button>
        </Link>
      </div>
    </div>
  );
}
