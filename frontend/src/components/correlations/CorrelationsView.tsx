'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { CorrelationCard } from './CorrelationCard';
import { CausalGraphView } from './CausalGraphView';
import { correlationsService } from '@/services/correlations';
import { billingService } from '@/services/billing';
import { healthConditionsService } from '@/services/healthConditions';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import { Zap, RefreshCw, AlertTriangle, Lock, GitBranch } from 'lucide-react';
import type { CorrelationCategory } from '@/types';

const CONDITION_HINTS: Record<string, string> = {
  'Type 2 Diabetes': 'glycemic load and carb intake → HRV and recovery (2-day lag)',
  'Hypertension': 'sodium intake → resting heart rate and HRV',
  'Hypothyroidism': 'caloric intake → temperature deviation and readiness',
  'Anxiety Disorder': 'sugar intake and meal timing → HRV and sleep efficiency',
  'Insomnia': 'evening meal timing and caffeine → sleep score and deep sleep',
  'IBS': 'fiber and fat intake → next-day readiness',
  'PCOS': 'glycemic load → temperature deviation and HRV balance',
  'Rheumatoid Arthritis': 'anti-inflammatory foods → readiness and recovery score',
};

type FilterTab = 'all' | CorrelationCategory;
type ViewMode = 'correlations' | 'causal';

const TABS: { value: FilterTab; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'nutrition_sleep', label: 'Sleep' },
  { value: 'nutrition_readiness', label: 'Recovery' },
  { value: 'nutrition_activity', label: 'Activity' },
];

export function CorrelationsView() {
  const [activeTab, setActiveTab] = useState<FilterTab>('all');
  const [days, setDays] = useState<7 | 14>(14);
  const [viewMode, setViewMode] = useState<ViewMode>('correlations');
  const queryClient = useQueryClient();
  const setSubscription = useSubscriptionStore((s) => s.setSubscription);
  const canUse = useSubscriptionStore((s) => s.canUseFeature('correlations'));

  // Refetch subscription on mount to ensure fresh tier/usage data
  const { data: freshSub, isLoading: isRefreshingSub } = useQuery({
    queryKey: ['subscription-check'],
    queryFn: () => billingService.getSubscription(),
    staleTime: 0, // Always fetch fresh
    retry: 1,
  });

  // Update store when fresh subscription arrives
  useEffect(() => {
    if (freshSub) {
      setSubscription(freshSub);
    }
  }, [freshSub, setSubscription]);

  const { data, isLoading, error } = useQuery({
    queryKey: ['correlations', days],
    queryFn: () => correlationsService.getCorrelations(days),
    staleTime: 1000 * 60 * 5,
    enabled: canUse,
  });

  const { data: conditionsData } = useQuery({
    queryKey: ['conditions'],
    queryFn: healthConditionsService.listConditions,
    staleTime: 5 * 60 * 1000,
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
  if (isRefreshingSub) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Zap className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Triggers &amp; Causes
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
            Triggers &amp; Causes
          </h1>
        </div>
        <Card>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Lock className="w-12 h-12 text-slate-300 dark:text-slate-600 mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                Unlock Triggers &amp; Causes
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
            Triggers &amp; Causes
          </h1>
        </div>
        <div className="flex items-center gap-2">
          {/* View mode toggle */}
          <div className="flex rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
            <button
              onClick={() => setViewMode('correlations')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors ${
                viewMode === 'correlations'
                  ? 'bg-primary-600 text-white'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
              }`}
            >
              <Zap className="w-3 h-3" />
              Patterns
            </button>
            <button
              onClick={() => setViewMode('causal')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors ${
                viewMode === 'causal'
                  ? 'bg-primary-600 text-white'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
              }`}
            >
              <GitBranch className="w-3 h-3" />
              Causes
            </button>
          </div>
          {/* Period toggle (correlations only) */}
          {viewMode === 'correlations' && (
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
          )}
          {viewMode === 'correlations' && (
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
          )}
        </div>
      </div>

      {/* Causal graph view */}
      {viewMode === 'causal' && <CausalGraphView />}

      {/* Correlations content */}
      {viewMode === 'correlations' && <>

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
            {data.days_with_data ?? data.oura_days_available} days of data
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
      {data && data.correlations.length === 0 && !isLoading && (() => {
        const userConditions = conditionsData ?? [];
        const matchedCondition = userConditions.find(
          (c: { condition_name: string }) => CONDITION_HINTS[c.condition_name]
        );
        const matchedHint = matchedCondition ? CONDITION_HINTS[matchedCondition.condition_name] : null;
        return (
          <Card>
            <CardContent>
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Zap className="w-12 h-12 text-slate-300 dark:text-slate-600 mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                  Not enough data yet
                </h3>
                {matchedHint ? (
                  <>
                    <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md">
                      Since you have <strong className="text-slate-300">{matchedCondition!.condition_name}</strong>, we&apos;ll analyze:
                    </p>
                    <p className="text-sm text-primary-400 mt-1 max-w-md">{matchedHint}</p>
                    <div className="mt-5 w-full max-w-xs">
                      <div className="flex justify-between text-xs text-slate-500 mb-1.5">
                        <span>Nutrition days logged</span>
                        <span>{data.nutrition_days_available}/5</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-slate-700">
                        <div
                          className="h-full rounded-full bg-primary-500 transition-all"
                          style={{ width: `${Math.min(100, (data.nutrition_days_available / 5) * 100)}%` }}
                        />
                      </div>
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md">
                    {data.summary ||
                      `Log meals and wear your Oura ring for at least 5 overlapping days to discover nutrition-health correlations.`}
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })()}

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

      {/* Data sources footnote */}
      {data && (data.data_sources_used?.length > 0 || data.oura_days_available > 0) && (
        <p className="text-xs text-slate-400 dark:text-slate-500 pt-2 border-t border-slate-100 dark:border-slate-800">
          <span className="font-medium">Data sources used: </span>
          {data.data_sources_used?.length > 0
            ? data.data_sources_used.join(', ')
            : ['Oura Ring', data.nutrition_days_available > 0 ? 'Nutrition Logs' : null].filter(Boolean).join(', ')
          }
          {data.days_with_data > 0 && ` · ${data.days_with_data} days`}
        </p>
      )}

      </>}
    </div>
  );
}
