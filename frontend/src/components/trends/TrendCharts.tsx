'use client';

import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { api } from '@/services/api';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import { TrendingUp, Lock } from 'lucide-react';
import Link from 'next/link';
import type { TimelineEntry } from '@/types';

interface ChartDataPoint {
  date: string;
  label: string;
  sleep?: number;
  readiness?: number;
  activity?: number;
  rhr?: number;
  hrv?: number;
  steps?: number;
  sleepHours?: number;
  spo2?: number;
  respiratoryRate?: number;
  activeCals?: number;
  workoutMin?: number;
  vo2Max?: number;
  sources?: string[];
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function transformData(entries: TimelineEntry[]): ChartDataPoint[] {
  return [...entries]
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((entry) => {
      const raw = entry as unknown as Record<string, unknown>;
      const native = raw.native as Record<string, number> | undefined;
      return {
        date: entry.date,
        label: formatDate(entry.date),
        sleep: entry.sleep?.sleep_score,
        readiness: entry.readiness?.readiness_score,
        activity: entry.activity?.activity_score,
        rhr: entry.readiness?.resting_heart_rate,
        hrv: entry.readiness?.hrv_balance,
        steps: entry.activity?.steps,
        sleepHours: entry.sleep
          ? Math.round((entry.sleep.total_sleep_duration / 3600) * 10) / 10
          : undefined,
        spo2: native?.spo2,
        respiratoryRate: native?.respiratory_rate,
        activeCals: native?.active_calories ?? entry.activity?.active_calories,
        workoutMin: native?.workout_minutes,
        vo2Max: native?.vo2_max,
        sources: raw.sources as string[] | undefined,
      };
    });
}

function ScoreChart({ data, title }: { data: ChartDataPoint[]; title: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11 }}
                className="text-slate-500"
                interval="preserveStartEnd"
              />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--tooltip-bg, #1e293b)',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#f8fafc',
                  fontSize: '13px',
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="sleep"
                stroke="#6366f1"
                strokeWidth={2}
                dot={false}
                name="Sleep"
                connectNulls
              />
              <Line
                type="monotone"
                dataKey="readiness"
                stroke="#22c55e"
                strokeWidth={2}
                dot={false}
                name="Readiness"
                connectNulls
              />
              <Line
                type="monotone"
                dataKey="activity"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
                name="Activity"
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

function MetricChart({
  data,
  title,
  dataKey,
  color,
  unit,
  explanation,
}: {
  data: ChartDataPoint[];
  title: string;
  dataKey: keyof ChartDataPoint;
  color: string;
  unit?: string;
  explanation?: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11 }}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--tooltip-bg, #1e293b)',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#f8fafc',
                  fontSize: '13px',
                }}
                formatter={(value: number) =>
                  unit ? `${value.toLocaleString()} ${unit}` : value.toLocaleString()
                }
              />
              <Line
                type="monotone"
                dataKey={dataKey as string}
                stroke={color}
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        {explanation && (
          <p className="text-xs text-slate-500 dark:text-slate-400 italic mt-2 leading-relaxed">{explanation}</p>
        )}
      </CardContent>
    </Card>
  );
}

export function TrendCharts() {
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState<14 | 30 | 60 | 90>(30);
  const [explanations, setExplanations] = useState<Record<string, string>>({});
  const tier = useSubscriptionStore((s) => s.getTier());
  const isPro = tier === 'pro' || tier === 'pro_plus';

  useEffect(() => {
    setLoading(true);
    api
      .get(`/api/v1/health/timeline?days=${range}&source_priority=auto`)
      .then(({ data: resp }) => {
        const entries = Array.isArray(resp) ? resp : (resp?.entries ?? []);
        setData(transformData(entries));
      })
      .catch(() => {})
      .finally(() => setLoading(false));

    // Fetch trend explanations
    api.get('/api/v1/insights-intelligence/trend-explanations')
      .then(({ data: resp }) => {
        const map: Record<string, string> = {};
        for (const m of resp?.metrics ?? []) {
          if (m.explanation) {
            map[m.metric] = m.explanation;
            map[m.label] = m.explanation;
          }
        }
        setExplanations(map);
      })
      .catch(() => {});
  }, [range]);

  if (!isPro) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-6">
          <Lock className="w-8 h-8 text-slate-400" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
          Trend Analysis is a Pro feature
        </h2>
        <p className="text-slate-500 dark:text-slate-400 max-w-md mb-6">
          Visualize your sleep, readiness, and activity trends over 30 days.
          Upgrade to Pro or Pro+ to unlock.
        </p>
        <Link href="/pricing">
          <Button>
            <TrendingUp className="w-4 h-4 mr-2" />
            Upgrade to unlock
          </Button>
        </Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-pulse text-slate-400">Loading trend data...</div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-20 text-slate-500 dark:text-slate-400">
        No data available. Connect a wearable device and sync to see trends.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Range selector */}
      <div className="flex items-center gap-2">
        {([14, 30, 60, 90] as const).map((d) => (
          <Button
            key={d}
            variant={range === d ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setRange(d)}
          >
            {d}d
          </Button>
        ))}
      </div>

      {/* Source badges */}
      {data.length > 0 && (() => {
        const allSources = new Set(data.flatMap((d) => d.sources ?? []));
        if (allSources.size === 0) return null;
        const BADGES: Record<string, { label: string; color: string }> = {
          oura: { label: '⊙ Oura Ring', color: '#818CF8' },
          healthkit: { label: '🍎 Apple Health', color: '#F87171' },
          health_connect: { label: '💚 Health Connect', color: '#34D399' },
          dexcom: { label: '📊 Dexcom', color: '#1E88E5' },
          whoop: { label: '🟢 WHOOP', color: '#2DD4BF' },
          garmin: { label: '🔵 Garmin', color: '#0EA5E9' },
          fitbit: { label: '💙 Fitbit', color: '#6366F1' },
        };
        return (
          <div className="flex items-center gap-3 text-xs">
            <span className="text-[#526380]">Sources:</span>
            {Array.from(allSources).map((s) => {
              const b = BADGES[s];
              return b ? <span key={s} style={{ color: b.color }}>{b.label}</span> : null;
            })}
          </div>
        );
      })()}

      {/* Main scores chart */}
      <ScoreChart data={data} title="Health Scores Overview" />

      {/* Core metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <MetricChart data={data} title="Sleep Duration" dataKey="sleepHours" color="#6366f1" unit="hrs" explanation={explanations['sleep'] || explanations['Sleep Score']} />
        <MetricChart data={data} title="Daily Steps" dataKey="steps" color="#f59e0b" unit="steps" explanation={explanations['steps'] || explanations['Daily Steps']} />
        <MetricChart data={data} title="Resting Heart Rate" dataKey="rhr" color="#ef4444" unit="bpm" explanation={explanations['resting_heart_rate'] || explanations['Resting HR']} />
        <MetricChart data={data} title="HRV Balance" dataKey="hrv" color="#22c55e" explanation={explanations['hrv_sdnn'] || explanations['HRV']} />
      </div>

      {/* Extended vitals & activity */}
      <h3 className="text-sm font-semibold text-[#526380] uppercase tracking-wider mt-2">Vitals & Activity</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <MetricChart data={data} title="SpO₂" dataKey="spo2" color="#60A5FA" unit="%" explanation={explanations['spo2'] || explanations['SpO₂']} />
        <MetricChart data={data} title="Respiratory Rate" dataKey="respiratoryRate" color="#A78BFA" unit="/min" explanation={explanations['respiratory_rate'] || explanations['Respiratory Rate']} />
        <MetricChart data={data} title="Active Calories" dataKey="activeCals" color="#FB923C" unit="kcal" explanation={explanations['active_calories'] || explanations['Active Calories']} />
        <MetricChart data={data} title="Workouts" dataKey="workoutMin" color="#F59E0B" unit="min" explanation={explanations['workout_minutes'] || explanations['Workouts']} />
        <MetricChart data={data} title="VO₂ Max" dataKey="vo2Max" color="#2DD4BF" unit="mL/kg/min" explanation={explanations['vo2_max'] || explanations['VO₂ Max']} />
      </div>
    </div>
  );
}
