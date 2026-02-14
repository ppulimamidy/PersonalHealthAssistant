'use client';

import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { HealthScoreRing } from '@/components/ui/HealthScoreRing';
import { Button } from '@/components/ui/Button';
import { ouraService } from '@/services/oura';
import { useHealthStore } from '@/stores/healthStore';
import { formatDate, formatDuration } from '@/lib/utils';
import { Moon, Footprints, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import type { TimelineEntry } from '@/types';

type MetricKey = 'sleep_score' | 'readiness_score' | 'resting_heart_rate';

function avg(values: number[]): number | null {
  if (!values.length) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function formatDelta(delta: number, unit: string) {
  const sign = delta > 0 ? '+' : '';
  return `${sign}${delta.toFixed(unit === 'bpm' ? 1 : 0)}${unit ? ` ${unit}` : ''}`;
}

function TimelineCard({ entry }: { entry: TimelineEntry }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card className="mb-4">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div>
          <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            {formatDate(entry.date)}
          </p>
        </div>
        <div className="flex items-center gap-6">
          {entry.sleep && (
            <HealthScoreRing score={entry.sleep.sleep_score} size="sm" label="Sleep" />
          )}
          {entry.activity && (
            <HealthScoreRing score={entry.activity.activity_score} size="sm" label="Activity" />
          )}
          {entry.readiness && (
            <HealthScoreRing score={entry.readiness.readiness_score} size="sm" label="Readiness" />
          )}
          <button className="text-slate-400 dark:text-slate-500">
            {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-700 grid grid-cols-3 gap-6">
          {/* Sleep Details */}
          {entry.sleep && (
            <div>
              <div className="flex items-center mb-3">
                <Moon className="w-5 h-5 text-indigo-500 mr-2" />
                <h4 className="font-medium text-slate-900 dark:text-slate-100">Sleep</h4>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Duration</span>
                  <span className="font-medium dark:text-slate-200">{formatDuration(entry.sleep.total_sleep_duration)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Deep Sleep</span>
                  <span className="font-medium dark:text-slate-200">{formatDuration(entry.sleep.deep_sleep_duration)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 dark:text-slate-400">REM Sleep</span>
                  <span className="font-medium dark:text-slate-200">{formatDuration(entry.sleep.rem_sleep_duration)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Efficiency</span>
                  <span className="font-medium dark:text-slate-200">{entry.sleep.sleep_efficiency}%</span>
                </div>
              </div>
            </div>
          )}

          {/* Activity Details */}
          {entry.activity && (
            <div>
              <div className="flex items-center mb-3">
                <Footprints className="w-5 h-5 text-green-500 mr-2" />
                <h4 className="font-medium text-slate-900 dark:text-slate-100">Activity</h4>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Steps</span>
                  <span className="font-medium dark:text-slate-200">{entry.activity.steps.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Active Calories</span>
                  <span className="font-medium dark:text-slate-200">{entry.activity.active_calories} kcal</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 dark:text-slate-400">High Activity</span>
                  <span className="font-medium dark:text-slate-200">{entry.activity.high_activity_time} min</span>
                </div>
              </div>
            </div>
          )}

          {/* Readiness Details */}
          {entry.readiness && (
            <div>
              <div className="flex items-center mb-3">
                <Zap className="w-5 h-5 text-amber-500 mr-2" />
                <h4 className="font-medium text-slate-900 dark:text-slate-100">Readiness</h4>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500 dark:text-slate-400">HRV Balance</span>
                  <span className="font-medium dark:text-slate-200">{entry.readiness.hrv_balance}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Resting HR</span>
                  <span className="font-medium dark:text-slate-200">{entry.readiness.resting_heart_rate} bpm</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Temp Deviation</span>
                  <span className="font-medium dark:text-slate-200">{entry.readiness.temperature_deviation.toFixed(1)}°</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

export function TimelineView() {
  const { selectedTimeRange, setTimeRange } = useHealthStore();
  const [showBaseline, setShowBaseline] = useState(true);

  // Always fetch 30 days so we can show baseline vs recent.
  const { data: timeline30, isLoading, refetch } = useQuery({
    queryKey: ['timeline', 30],
    queryFn: () => ouraService.getTimeline(30),
  });

  const { timelineToShow, baseline } = useMemo(() => {
    const all = (timeline30 ?? []).slice();
    // API returns desc by date; keep that order.
    const recent = all.slice(0, 14);
    const baselineWindow = all.slice(0, 30);

    const pick = (entries: TimelineEntry[], key: MetricKey) => {
      const values: number[] = [];
      for (const e of entries) {
        if (key === 'sleep_score' && e.sleep) values.push(e.sleep.sleep_score);
        if (key === 'readiness_score' && e.readiness) values.push(e.readiness.readiness_score);
        if (key === 'resting_heart_rate' && e.readiness) values.push(e.readiness.resting_heart_rate);
      }
      return avg(values);
    };

    const recentSleep = pick(recent, 'sleep_score');
    const baseSleep = pick(baselineWindow, 'sleep_score');
    const recentReady = pick(recent, 'readiness_score');
    const baseReady = pick(baselineWindow, 'readiness_score');
    const recentRhr = pick(recent, 'resting_heart_rate');
    const baseRhr = pick(baselineWindow, 'resting_heart_rate');

    const timelineToShow = selectedTimeRange === 14 ? recent : baselineWindow;

    return {
      timelineToShow,
      baseline: {
        recentSleep,
        baseSleep,
        recentReady,
        baseReady,
        recentRhr,
        baseRhr,
      },
    };
  }, [timeline30, selectedTimeRange]);

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Health Timeline</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Your daily health metrics at a glance</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
            <button
              onClick={() => setTimeRange(14)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedTimeRange === 14
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              14 Days
            </button>
            <button
              onClick={() => setTimeRange(30)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedTimeRange === 30
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              30 Day Baseline
            </button>
          </div>
          <Button
            onClick={() => setShowBaseline((v) => !v)}
            variant="outline"
            title="Show baseline vs recent comparison"
          >
            {showBaseline ? 'Hide' : 'Show'} Baseline
          </Button>
          <Button onClick={() => refetch()} variant="outline">
            Sync Data
          </Button>
        </div>
      </div>

      {showBaseline && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>What changed (last 14 days vs 30-day baseline)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="text-slate-500 dark:text-slate-400">Sleep score</div>
                <div className="mt-1 font-semibold text-slate-900 dark:text-slate-100">
                  {baseline.recentSleep != null && baseline.baseSleep != null
                    ? formatDelta(baseline.recentSleep - baseline.baseSleep, '')
                    : '—'}
                </div>
                <div className="mt-1 text-slate-500 dark:text-slate-400">
                  Recent: {baseline.recentSleep?.toFixed(0) ?? '—'} · Baseline: {baseline.baseSleep?.toFixed(0) ?? '—'}
                </div>
              </div>

              <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="text-slate-500 dark:text-slate-400">Readiness score</div>
                <div className="mt-1 font-semibold text-slate-900 dark:text-slate-100">
                  {baseline.recentReady != null && baseline.baseReady != null
                    ? formatDelta(baseline.recentReady - baseline.baseReady, '')
                    : '—'}
                </div>
                <div className="mt-1 text-slate-500 dark:text-slate-400">
                  Recent: {baseline.recentReady?.toFixed(0) ?? '—'} · Baseline: {baseline.baseReady?.toFixed(0) ?? '—'}
                </div>
              </div>

              <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="text-slate-500 dark:text-slate-400">Resting heart rate</div>
                <div className="mt-1 font-semibold text-slate-900 dark:text-slate-100">
                  {baseline.recentRhr != null && baseline.baseRhr != null
                    ? formatDelta(baseline.recentRhr - baseline.baseRhr, 'bpm')
                    : '—'}
                </div>
                <div className="mt-1 text-slate-500 dark:text-slate-400">
                  Recent: {baseline.recentRhr?.toFixed(1) ?? '—'} · Baseline: {baseline.baseRhr?.toFixed(1) ?? '—'}
                </div>
              </div>
            </div>
            <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">
              This is not medical advice. Trends can change due to illness, stress, travel, training, or sleep disruption.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Timeline */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : timelineToShow && timelineToShow.length > 0 ? (
        <div>
          {timelineToShow.map((entry) => (
            <TimelineCard key={entry.date} entry={entry} />
          ))}
        </div>
      ) : (
        <Card className="text-center py-12">
          <p className="text-slate-500 dark:text-slate-400">No health data available yet.</p>
          <p className="text-sm text-slate-400 dark:text-slate-500 mt-2">
            Connect your Oura Ring to start tracking.
          </p>
        </Card>
      )}
    </div>
  );
}
