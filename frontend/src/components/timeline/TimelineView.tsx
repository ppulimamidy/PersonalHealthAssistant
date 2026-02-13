'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { HealthScoreRing } from '@/components/ui/HealthScoreRing';
import { Button } from '@/components/ui/Button';
import { ouraService } from '@/services/oura';
import { useHealthStore } from '@/stores/healthStore';
import { formatDate, formatDuration } from '@/lib/utils';
import { Moon, Footprints, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import type { TimelineEntry } from '@/types';

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

  const { data: timeline, isLoading, refetch } = useQuery({
    queryKey: ['timeline', selectedTimeRange],
    queryFn: () => ouraService.getTimeline(selectedTimeRange),
  });

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
              onClick={() => setTimeRange(7)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedTimeRange === 7
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              7 Days
            </button>
            <button
              onClick={() => setTimeRange(30)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedTimeRange === 30
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              30 Days
            </button>
          </div>
          <Button onClick={() => refetch()} variant="outline">
            Sync Data
          </Button>
        </div>
      </div>

      {/* Timeline */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : timeline && timeline.length > 0 ? (
        <div>
          {timeline.map((entry) => (
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
