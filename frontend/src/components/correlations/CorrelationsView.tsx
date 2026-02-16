'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { CorrelationCard } from './CorrelationCard';
import { correlationsService } from '@/services/correlations';
import { billingService } from '@/services/billing';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import { Zap, RefreshCw, AlertTriangle, Lock } from 'lucide-react';
import type { CorrelationCategory } from '@/types';

type FilterTab = 'all' | CorrelationCategory;

const TABS: { value: FilterTab; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'nutrition_sleep', label: 'Sleep' },
  { value: 'nutrition_readiness', label: 'Recovery' },
  { value: 'nutrition_activity', label: 'Activity' },
];

export function CorrelationsView() {
  const [activeTab, setActiveTab] = useState<FilterTab>('all');
  const [days, setDays] = useState<7 | 14>(14);
  const [subscriptionFetched, setSubscriptionFetched] = useState(false);
  const queryClient = useQueryClient();
  const setSubscription = useSubscriptionStore((s) => s.setSubscription);
  const canUse = useSubscriptionStore((s) => s.canUseFeature('correlations'));

  // Refetch subscription on mount so Pro/Pro+ unlock is correct after upgrade (don't trust persisted state)
  useEffect(() => {
    billingService
      .getSubscription()
      .then((data) => {
        setSubscription(data);
        setSubscriptionFetched(true);
      })
      .catch(() => setSubscriptionFetched(true));
  }, [setSubscription]);

  const { data, isLoading, error } = useQuery({
    queryKey: ['correlations', days],
    queryFn: () => correlationsService.getCorrelations(days),
    staleTime: 1000 * 60 * 5,
    enabled: canUse,
  });

  const refreshMutation = useMutation({
    mutationFn: () => correlationsService.refreshCorrelations(days),
    onSuccess: (newData) => {
      queryClient.setQueryData(['correlations', days], newData);
    },
  });

  const filtered =
    activeTab === 'all'
      ? data?.correlations ?? []
      : (data?.correlations ?? []).filter((c) => c.category === activeTab);

  // Wait for subscription refetch before showing gate (avoids showing gate from stale persisted data after upgrade)
  if (!subscriptionFetched) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Zap className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Metabolic Intelligence
          </h1>
        </div>
        <Card>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <p className="text-sm text-slate-500 dark:text-slate-400">Checking access…</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Pro gate
  if (!canUse) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Zap className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Metabolic Intelligence
          </h1>
        </div>
        <Card>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Lock className="w-12 h-12 text-slate-300 dark:text-slate-600 mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                Unlock Metabolic Intelligence
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mb-4">
                Discover how your nutrition affects your sleep, recovery, and performance.
                Upgrade to Pro to access correlation analysis.
              </p>
              <Button onClick={() => useSubscriptionStore.getState().setShowUpgradeModal(true)}>
                Upgrade to Pro
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Zap className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Metabolic Intelligence
          </h1>
        </div>
        <div className="flex items-center gap-2">
          {/* Period toggle */}
          <div className="flex rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
            {([7, 14] as const).map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                  days === d
                    ? 'bg-primary-600 text-white'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
          >
            <RefreshCw
              className={`w-4 h-4 ${refreshMutation.isPending ? 'animate-spin' : ''}`}
            />
          </Button>
        </div>
      </div>

      {/* Data quality bar */}
      {data && (
        <div className="flex items-center gap-3 text-sm">
          <div className="flex-1 h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-500 rounded-full transition-all"
              style={{ width: `${Math.round(data.data_quality_score * 100)}%` }}
            />
          </div>
          <span className="text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap">
            {data.oura_days_available} Oura / {data.nutrition_days_available} nutrition
            days
          </span>
        </div>
      )}

      {/* AI Summary */}
      {data?.summary && (
        <Card>
          <CardContent>
            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
              {data.summary}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent>
                <div className="animate-pulse space-y-3">
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
                  <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
                  <div className="h-32 bg-slate-200 dark:bg-slate-700 rounded" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Error state */}
      {error && (
        <Card>
          <CardContent>
            <div className="flex items-center gap-3 text-red-600 dark:text-red-400">
              <AlertTriangle className="w-5 h-5" />
              <p className="text-sm">Failed to load correlations. Please try again.</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty / insufficient data state */}
      {data && data.correlations.length === 0 && !isLoading && (
        <Card>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Zap className="w-12 h-12 text-slate-300 dark:text-slate-600 mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                Not enough data yet
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md">
                {data.summary ||
                  `Log meals and wear your Oura ring for at least 5 overlapping days to discover nutrition-health correlations.`}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filter tabs + results */}
      {data && data.correlations.length > 0 && (
        <>
          <div className="flex gap-1 border-b border-slate-200 dark:border-slate-700">
            {TABS.map((tab) => {
              const count =
                tab.value === 'all'
                  ? data.correlations.length
                  : data.correlations.filter((c) => c.category === tab.value).length;
              return (
                <button
                  key={tab.value}
                  onClick={() => setActiveTab(tab.value)}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.value
                      ? 'border-primary-600 text-primary-600 dark:text-primary-400 dark:border-primary-400'
                      : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
                  }`}
                >
                  {tab.label}
                  {count > 0 && (
                    <span className="ml-1.5 text-xs opacity-60">({count})</span>
                  )}
                </button>
              );
            })}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {filtered.map((c) => (
              <CorrelationCard key={c.id} correlation={c} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
