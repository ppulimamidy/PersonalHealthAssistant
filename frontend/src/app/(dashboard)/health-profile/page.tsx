'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { ConditionsList } from '@/components/health-conditions/ConditionsList';
import { AddConditionModal } from '@/components/health-conditions/AddConditionModal';
import { HealthQuestionnaire } from '@/components/health-conditions/HealthQuestionnaire';
import { RecommendationCard, PatternBanner } from '@/components/correlations/RecommendationCard';
import { RecoveryPlanView } from '@/components/correlations/RecoveryPlan';
import { recommendationsService } from '@/services/recommendations';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import {
  Plus,
  Lock,
  HeartPulse,
  Sparkles,
  ClipboardList,
  Salad,
} from 'lucide-react';
import type { RecommendationsResponse } from '@/types';

type Tab = 'conditions' | 'questionnaire' | 'recommendations' | 'recovery';

export default function HealthProfilePage() {
  const [tab, setTab] = useState<Tab>('conditions');
  const [showAddModal, setShowAddModal] = useState(false);
  const canUse = useSubscriptionStore((s) => s.canUseFeature('health_conditions'));

  const { data: recs } = useQuery<RecommendationsResponse>({
    queryKey: ['recommendations'],
    queryFn: () => recommendationsService.getRecommendations(),
    staleTime: 1000 * 60 * 15,
    enabled: tab === 'recommendations',
  });

  const tabs: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: 'conditions', label: 'Conditions', icon: HeartPulse },
    { key: 'questionnaire', label: 'Questionnaire', icon: ClipboardList },
    { key: 'recommendations', label: 'Recommendations', icon: Sparkles },
    { key: 'recovery', label: 'Recovery Plan', icon: Salad },
  ];

  if (!canUse) {
    return (
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6">
          Health Profile
        </h1>
        <Card>
          <div className="text-center py-10">
            <Lock className="w-10 h-10 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Pro+ Feature
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
              Track health conditions, get personalized questionnaires, and receive AI-powered
              nutrition recommendations.
            </p>
            <a
              href="/settings"
              className="inline-block mt-4 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700"
            >
              Upgrade to Pro+
            </a>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          Health Profile
        </h1>
        {tab === 'conditions' && (
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700"
          >
            <Plus className="w-4 h-4" />
            Add Condition
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === t.key
                ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <t.icon className="w-4 h-4" />
            <span className="hidden sm:inline">{t.label}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'conditions' && <ConditionsList />}

      {tab === 'questionnaire' && <HealthQuestionnaire />}

      {tab === 'recommendations' && (
        <div className="space-y-4">
          {/* Patterns */}
          {recs?.patterns_detected && recs.patterns_detected.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                Detected Patterns
              </h3>
              {recs.patterns_detected.map((p, i) => (
                <PatternBanner key={i} {...p} />
              ))}
            </div>
          )}

          {/* AI Summary */}
          {recs?.ai_summary && (
            <Card>
              <div className="flex items-start gap-2">
                <Sparkles className="w-4 h-4 text-primary-500 mt-0.5 shrink-0" />
                <p className="text-sm text-slate-700 dark:text-slate-300">{recs.ai_summary}</p>
              </div>
            </Card>
          )}

          {/* Recommendations */}
          {recs?.recommendations && recs.recommendations.length > 0 ? (
            <div className="space-y-3">
              {recs.recommendations.map((r) => (
                <RecommendationCard key={r.id} recommendation={r} />
              ))}
            </div>
          ) : (
            <Card>
              <div className="text-center py-6">
                <Sparkles className="w-8 h-8 text-slate-300 dark:text-slate-600 mx-auto mb-2" />
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Log more meals and wear your Oura ring to generate personalized recommendations.
                </p>
              </div>
            </Card>
          )}
        </div>
      )}

      {tab === 'recovery' && <RecoveryPlanView />}

      <AddConditionModal open={showAddModal} onClose={() => setShowAddModal(false)} />
    </div>
  );
}
