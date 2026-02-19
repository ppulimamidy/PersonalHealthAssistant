'use client';

import Link from 'next/link';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { insightsService } from '@/services/insights';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Lightbulb,
  ChevronRight,
  RefreshCw,
  Info,
  Link2,
} from 'lucide-react';
import { useState } from 'react';
import type { AIInsight, CorrelatedInsight } from '@/types';
import { cn } from '@/lib/utils';

function InsightCard({ insight }: { insight: AIInsight }) {
  const [showExplanation, setShowExplanation] = useState(false);

  const typeIcons = {
    trend: TrendingUp,
    recommendation: Lightbulb,
    alert: AlertTriangle,
  };

  const typeColors = {
    trend: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-800',
    recommendation: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 border-green-200 dark:border-green-800',
    alert: 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-800',
  };

  const categoryColors = {
    sleep: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300',
    activity: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300',
    readiness: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300',
    general: 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300',
  };

  const Icon = typeIcons[insight.type];

  return (
    <Card className={cn('border-l-4', typeColors[insight.type])}>
      <div className="flex items-start gap-4">
        <div className={cn('p-2 rounded-lg', typeColors[insight.type].split(' ')[0])}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', categoryColors[insight.category])}>
              {insight.category}
            </span>
            <span className="text-xs text-slate-400 dark:text-slate-500">
              {Math.round(insight.confidence * 100)}% confidence
            </span>
          </div>
          <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-1">{insight.title}</h3>
          <p className="text-sm text-slate-600 dark:text-slate-300">{insight.summary}</p>

          {/* Data Points */}
          {insight.data_points && insight.data_points.length > 0 && (
            <div className="flex gap-4 mt-3">
              {insight.data_points.slice(0, 3).map((point, idx) => (
                <div key={idx} className="flex items-center gap-1 text-sm">
                  {point.trend === 'up' ? (
                    <TrendingUp className="w-4 h-4 text-green-500" />
                  ) : point.trend === 'down' ? (
                    <TrendingDown className="w-4 h-4 text-red-500" />
                  ) : null}
                  <span className="text-slate-500 dark:text-slate-400">{point.metric}:</span>
                  <span className="font-medium dark:text-slate-200">{point.value}</span>
                </div>
              ))}
            </div>
          )}

          {/* Explainability Section */}
          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className="flex items-center gap-1 mt-4 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
          >
            <Info className="w-4 h-4" />
            {showExplanation ? 'Hide' : 'Why am I seeing this?'}
            <ChevronRight className={cn('w-4 h-4 transition-transform', showExplanation && 'rotate-90')} />
          </button>

          {showExplanation && (
            <div className="mt-3 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">How we determined this insight:</h4>
              <p className="text-sm text-slate-600 dark:text-slate-400">{insight.explanation}</p>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

const DISCLAIMER = 'This is not medical advice. If you have questions, follow up with your doctor.';

function CorrelatedInsightCard({ insight }: { insight: CorrelatedInsight }) {
  const isGeneric = insight.recommendation.toLowerCase().includes("don't have enough personal data");
  const typeLabel =
    insight.insight_type === 'medication_alert'
      ? 'Medication'
      : insight.insight_type === 'correlation'
        ? 'Correlation'
        : insight.insight_type === 'causation'
          ? 'Causation'
          : insight.insight_type === 'supplement'
            ? 'Supplement'
            : 'Pattern';
  return (
    <Card className="border-l-4 border-primary-500 dark:border-primary-600">
      <CardContent className="pt-5">
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900/40 dark:text-primary-300">
            {typeLabel}
          </span>
          {isGeneric && (
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
              General guidance
            </span>
          )}
          {insight.factors_considered.length > 0 && (
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Factors: {insight.factors_considered.join(', ')}
            </span>
          )}
        </div>
        <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2">{insight.title}</h3>
        <div className="space-y-2 text-sm">
          <div>
            <span className="font-medium text-slate-700 dark:text-slate-300">Recommendation: </span>
            <span className="text-slate-600 dark:text-slate-400">{insight.recommendation}</span>
          </div>
          <div>
            <span className="font-medium text-slate-700 dark:text-slate-300">Evidence: </span>
            <span className="text-slate-600 dark:text-slate-400">{insight.evidence}</span>
          </div>
        </div>
        {insight.confidence > 0 && (
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
            {Math.round(insight.confidence * 100)}% confidence
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export function InsightsView() {
  const { data: insights, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['insights'],
    queryFn: insightsService.getInsights,
  });

  const queryClient = useQueryClient();
  const { data: correlatedInsights, isLoading: correlatedLoading } = useQuery({
    queryKey: ['insights', 'correlated'],
    queryFn: insightsService.getCorrelatedInsights,
  });

  const topInsights = (insights ?? [])
    .slice()
    .sort((a, b) => {
      const typeWeight = (t: AIInsight['type']) => (t === 'alert' ? 3 : t === 'trend' ? 2 : 1);
      const w = typeWeight(b.type) - typeWeight(a.type);
      if (w !== 0) return w;
      return (b.confidence ?? 0) - (a.confidence ?? 0);
    })
    .slice(0, 3);

  const handleRefresh = async () => {
    await insightsService.refreshInsights();
    refetch();
    queryClient.invalidateQueries({ queryKey: ['insights'] });
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">AI Insights</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Personalized health insights based on your data
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/doctor-prep?autogenerate=1&days=30">
            <Button>
              Prepare Doctor Visit (30 days)
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
          <Button onClick={handleRefresh} variant="outline" isLoading={isRefetching}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh Insights
          </Button>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
          <div>
            <h4 className="font-medium text-blue-900 dark:text-blue-100">About insights</h4>
            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
              Correlated insights use all available data—supplements, symptoms, trends, nutrition, medications, labs, health conditions, goals, doctor notes, and research—for evidence-based recommendations. When we have your data we personalize; when we don’t, we label it general guidance. AI insights use your wearable and activity data. This is not medical advice; follow up with your doctor if you have questions.
            </p>
          </div>
        </div>
      </div>

      {/* Correlated insights: recommendation + evidence */}
      {correlatedLoading ? (
        <div className="flex items-center justify-center h-32 mb-6">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600" />
        </div>
      ) : correlatedInsights && correlatedInsights.length > 0 ? (
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
            <Link2 className="w-5 h-5" />
            Correlated insights
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
            Recommendation and evidence from your medications, supplements, symptoms, nutrition, vitals, labs, conditions, goals, and research when available.
          </p>
          <div className="space-y-4">
            {correlatedInsights.map((insight) => (
              <CorrelatedInsightCard key={insight.id} insight={insight} />
            ))}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-4 italic">
            {DISCLAIMER}
          </p>
        </div>
      ) : null}

      {/* AI Insights (trends, alerts) */}
      <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">AI insights</h2>
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : topInsights && topInsights.length > 0 ? (
        <div className="space-y-4">
          {topInsights.map((insight) => (
            <InsightCard key={insight.id} insight={insight} />
          ))}
        </div>
      ) : !correlatedInsights?.length ? (
        <Card className="text-center py-12">
          <Lightbulb className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <p className="text-slate-500 dark:text-slate-400">No insights available yet.</p>
          <p className="text-sm text-slate-400 dark:text-slate-500 mt-2">
            We need more data to generate personalized insights. Connect your device, log symptoms, or add medications to see correlated insights.
          </p>
        </Card>
      ) : null}
    </div>
  );
}
