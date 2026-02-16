'use client';

import { useEffect, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import { CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import { billingService } from '@/services/billing';
import Link from 'next/link';

const POLL_INTERVAL_MS = 2000;
const MAX_POLL_ATTEMPTS = 10;

export default function BillingSuccessPage() {
  const searchParams = useSearchParams();
  const setSubscription = useSubscriptionStore((s) => s.setSubscription);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    let attempt = 0;
    let confirmDone = false;

    const scheduleNext = () => {
      if (!mounted.current || attempt >= MAX_POLL_ATTEMPTS) return;
      attempt += 1;
      setTimeout(runPoll, attempt === 1 ? 0 : POLL_INTERVAL_MS);
    };

    const runPoll = async () => {
      if (!mounted.current) return;
      // On first run, confirm checkout with Stripe session_id so backend activates subscription (works when webhook has not run)
      const sessionId = searchParams.get('session_id');
      if (sessionId && !confirmDone) {
        confirmDone = true;
        try {
          await billingService.confirmCheckoutSession(sessionId);
        } catch {
          // Ignore (e.g. already confirmed by webhook)
        }
      }
      try {
        const data = await billingService.getSubscription();
        setSubscription(data);
        if (data.tier === 'free' && attempt < MAX_POLL_ATTEMPTS) scheduleNext();
      } catch {
        if (attempt < MAX_POLL_ATTEMPTS) scheduleNext();
      }
    };

    scheduleNext();

    return () => {
      mounted.current = false;
    };
  }, [setSubscription, searchParams]);

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
      <div className="flex flex-wrap gap-4 justify-center">
        <Link href="/correlations">
          <Button>Open Metabolic AI</Button>
        </Link>
        <Link href="/timeline">
          <Button variant="outline">Go to Timeline</Button>
        </Link>
        <Link href="/settings">
          <Button variant="outline">Manage Subscription</Button>
        </Link>
      </div>
    </div>
  );
}
