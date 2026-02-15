'use client';

import { useState } from 'react';
import { Check, X } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { billingService } from '@/services/billing';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import type { SubscriptionTier } from '@/types';

interface PricingTier {
  id: SubscriptionTier;
  name: string;
  price: string;
  period: string;
  description: string;
  features: { text: string; included: boolean }[];
  popular?: boolean;
  cta: string;
}

const tiers: PricingTier[] = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    period: 'forever',
    description: 'Get started with basic health tracking',
    cta: 'Current Plan',
    features: [
      { text: 'Oura Ring data sync', included: true },
      { text: 'Health timeline view', included: true },
      { text: '3 AI insights per week', included: true },
      { text: '5 meal photo scans per week', included: true },
      { text: 'Doctor prep reports', included: false },
      { text: 'PDF export', included: false },
      { text: 'Weekly health reports', included: false },
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '$9.99',
    period: '/month',
    description: 'Unlimited insights and nutrition tracking',
    popular: true,
    cta: 'Upgrade to Pro',
    features: [
      { text: 'Everything in Free', included: true },
      { text: 'Unlimited AI insights', included: true },
      { text: 'Unlimited meal photo scans', included: true },
      { text: 'Daily health score', included: true },
      { text: 'Doctor prep reports', included: false },
      { text: 'PDF export', included: false },
      { text: 'Priority AI analysis', included: false },
    ],
  },
  {
    id: 'pro_plus',
    name: 'Pro+',
    price: '$19.99',
    period: '/month',
    description: 'Full access with doctor-ready reports',
    cta: 'Upgrade to Pro+',
    features: [
      { text: 'Everything in Pro', included: true },
      { text: 'Doctor prep reports', included: true },
      { text: 'PDF export & printing', included: true },
      { text: 'Trend analysis', included: true },
      { text: 'Priority AI analysis', included: true },
      { text: 'Email health summaries', included: true },
      { text: 'Early access to new features', included: true },
    ],
  },
];

export function PricingTable() {
  const [loading, setLoading] = useState<string | null>(null);
  const currentTier = useSubscriptionStore((s) => s.getTier());

  const handleUpgrade = async (tier: SubscriptionTier) => {
    if (tier === 'free' || tier === currentTier) return;
    setLoading(tier);
    try {
      const url = await billingService.createCheckoutSession(tier as 'pro' | 'pro_plus');
      window.location.href = url;
    } catch {
      setLoading(null);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
      {tiers.map((tier) => {
        const isCurrent = tier.id === currentTier;
        const isPopular = tier.popular;

        return (
          <div
            key={tier.id}
            className={`relative rounded-2xl border p-6 flex flex-col ${
              isPopular
                ? 'border-primary-500 ring-2 ring-primary-500 dark:border-primary-400 dark:ring-primary-400'
                : 'border-slate-200 dark:border-slate-700'
            } bg-white dark:bg-slate-800`}
          >
            {isPopular && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary-500 text-white text-xs font-semibold px-3 py-1 rounded-full">
                Most Popular
              </div>
            )}

            <div className="mb-4">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{tier.name}</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{tier.description}</p>
            </div>

            <div className="mb-6">
              <span className="text-4xl font-bold text-slate-900 dark:text-white">{tier.price}</span>
              <span className="text-slate-500 dark:text-slate-400 ml-1">{tier.period}</span>
            </div>

            <ul className="space-y-3 mb-8 flex-1">
              {tier.features.map((feature, i) => (
                <li key={i} className="flex items-start gap-2">
                  {feature.included ? (
                    <Check className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                  ) : (
                    <X className="w-4 h-4 text-slate-300 dark:text-slate-600 mt-0.5 shrink-0" />
                  )}
                  <span
                    className={`text-sm ${
                      feature.included
                        ? 'text-slate-700 dark:text-slate-300'
                        : 'text-slate-400 dark:text-slate-500'
                    }`}
                  >
                    {feature.text}
                  </span>
                </li>
              ))}
            </ul>

            <Button
              variant={isCurrent ? 'outline' : isPopular ? 'primary' : 'secondary'}
              size="md"
              className="w-full"
              disabled={isCurrent || tier.id === 'free'}
              isLoading={loading === tier.id}
              onClick={() => handleUpgrade(tier.id)}
            >
              {isCurrent ? 'Current Plan' : tier.cta}
            </Button>
          </div>
        );
      })}
    </div>
  );
}
