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
  Cpu,
} from 'lucide-react';
import { useState } from 'react';
import type { AIInsight, CorrelatedInsight, MetricDelta, InsightFollowUp } from '@/types';
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

// ── 30-day delta strip ────────────────────────────────────────────────────────

function MetricDeltaStrip() {
  const { data: deltas } = useQuery({
    queryKey: ['insights-delta'],
    queryFn: insightsService.getDelta,
    staleTime: 5 * 60_000,
  });

  if (!deltas || deltas.length === 0) return null;

  const fmtVal = (m: MetricDelta) => {
    if (m.metric === 'steps') return Math.round(m.current).toLocaleString();
    return m.current.toFixed(1);
  };
  const fmtDelta = (m: MetricDelta) => {
    const sign = m.delta > 0 ? '+' : '';
    if (m.metric === 'steps') return `${sign}${Math.round(m.delta).toLocaleString()}`;
    return `${sign}${m.delta.toFixed(1)}`;
  };
  const deltaColor = (dir: MetricDelta['direction']) =>
    dir === 'up' ? '#00D4AA' : dir === 'down' ? '#F87171' : '#526380';
  const arrowIcon = (dir: MetricDelta['direction']) =>
    dir === 'up' ? '↑' : dir === 'down' ? '↓' : '→';

  return (
    <div
      className="rounded-xl p-4 mb-6"
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      <p className="text-xs font-semibold text-[#526380] mb-3 uppercase tracking-wide">
        What changed in 30 days?
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {deltas.map((m) => (
          <div key={m.metric} className="text-center">
            <p className="text-[10px] text-[#526380] mb-1">{m.label}</p>
            <p className="text-lg font-bold text-[#E8EDF5]">{fmtVal(m)}</p>
            <p
              className="text-xs font-semibold mt-0.5"
              style={{ color: deltaColor(m.direction) }}
            >
              {arrowIcon(m.direction)} {fmtDelta(m)} {m.unit}
            </p>
            <p className="text-[10px] text-[#3D4F66] mt-0.5">
              was {m.metric === 'steps' ? Math.round(m.previous).toLocaleString() : m.previous.toFixed(1)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── 30-day follow-ups ─────────────────────────────────────────────────────────

function FollowUpsSection() {
  const { data: followups } = useQuery({
    queryKey: ['insights-followups'],
    queryFn: insightsService.getFollowups,
    staleTime: 10 * 60_000,
  });

  if (!followups || followups.length === 0) return null;

  const dirColor = (dir: InsightFollowUp['direction']) =>
    dir === 'better' ? '#00D4AA' : dir === 'worse' ? '#F87171' : '#526380';
  const dirIcon = (dir: InsightFollowUp['direction'], delta: number | null) => {
    if (dir === 'better') return '↑ Better';
    if (dir === 'worse')  return '↓ Worse';
    if (dir === 'stable') return '→ Stable';
    return delta != null ? `${delta > 0 ? '+' : ''}${delta}` : '—';
  };

  return (
    <div className="mb-8">
      <h2 className="text-sm font-semibold text-[#8B97A8] mb-1 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-[#00D4AA] inline-block" />
        30-day follow-ups
      </h2>
      <p className="text-xs text-[#526380] mb-3">How did these findings change from last month?</p>
      <div className="space-y-3">
        {followups.map((fu) => (
          <div
            key={fu.metric_key}
            className="rounded-xl px-4 py-3 flex items-center gap-4"
            style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
          >
            {/* Original finding */}
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-[#C8D5E8] truncate">{fu.original_title}</p>
              <p className="text-[10px] text-[#526380] mt-0.5">
                {fu.label} · {fu.original_date ? new Date(fu.original_date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '~30d ago'}
              </p>
            </div>
            {/* Before → After */}
            <div className="flex items-center gap-2 flex-shrink-0 text-right">
              <span className="text-xs text-[#3D4F66]">
                {fu.original_value != null ? fu.original_value : '—'}
              </span>
              <span className="text-[10px] text-[#3D4F66]">→</span>
              <span className="text-sm font-bold text-[#E8EDF5]">
                {fu.current_value != null ? fu.current_value : '—'}
              </span>
              <span
                className="text-xs font-semibold px-2 py-0.5 rounded-full"
                style={{ color: dirColor(fu.direction), backgroundColor: `${dirColor(fu.direction)}1A` }}
              >
                {dirIcon(fu.direction, fu.delta)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
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

  const sortedCorrelated = [...(correlatedInsights ?? [])].sort(
    (a, b) => (b.confidence ?? 0) - (a.confidence ?? 0)
  );

  return (
    <div>
      {/* Top Insight Hero — most actionable recommendation at a glance */}
      {sortedCorrelated[0] && (
        <div
          className="p-5 rounded-xl mb-6"
          style={{ backgroundColor: 'rgba(0,212,170,0.05)', border: '1px solid rgba(0,212,170,0.15)' }}
        >
          <p className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: '#00D4AA' }}>
            Top Recommendation
          </p>
          <p className="text-lg font-semibold text-slate-100">{sortedCorrelated[0].title}</p>
          <p className="text-sm mt-1" style={{ color: '#8B97A8' }}>{sortedCorrelated[0].recommendation}</p>
        </div>
      )}

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

      {/* 30-day follow-ups (resurface old findings with delta) */}
      <FollowUpsSection />

      {/* 30-day metric delta strip */}
      <MetricDeltaStrip />

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
      ) : (
        <div className="flex items-center gap-3 p-4 rounded-lg border border-slate-200 dark:border-slate-700 text-sm text-slate-500 dark:text-slate-400">
          <Cpu className="w-4 h-4 flex-shrink-0 text-slate-400 dark:text-slate-500" />
          <span>
            AI insights require wearable data.{' '}
            <Link href="/devices" className="text-primary-600 dark:text-primary-400 hover:underline">
              Connect a Wearable Device →
            </Link>
          </span>
        </div>
      )}

      {/* About insights — demoted to bottom */}
      <div
        className="rounded-lg p-4 mt-6"
        style={{ backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}
      >
        <div className="flex items-start gap-3">
          <Info className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#526380' }} />
          <p className="text-xs" style={{ color: '#526380' }}>
            Correlated insights use all available data—supplements, symptoms, trends, nutrition, medications, labs, health conditions, goals, doctor notes, and research. AI insights use your wearable and activity data. This is not medical advice; follow up with your doctor if you have questions.
          </p>
        </div>
      </div>

      {/* Doctor Prep CTA */}
      <div
        className="p-6 rounded-xl flex items-center justify-between gap-4 mt-6"
        style={{ backgroundColor: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.15)' }}
      >
        <div>
          <p className="font-semibold text-slate-100">Ready to discuss with your doctor?</p>
          <p className="text-sm mt-1" style={{ color: '#8B97A8' }}>
            Generate a structured report with your key findings, trends, and questions to ask.
          </p>
        </div>
        <Link
          href="/doctor-prep?autogenerate=1&days=30"
          className="flex-shrink-0 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap"
          style={{ backgroundColor: '#00D4AA', color: '#080B10' }}
        >
          Doctor Prep Report →
        </Link>
      </div>
    </div>
  );
}
