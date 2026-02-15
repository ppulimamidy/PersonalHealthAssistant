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
import { ouraService } from '@/services/oura';
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
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function transformData(entries: TimelineEntry[]): ChartDataPoint[] {
  return [...entries]
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((entry) => ({
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
    }));
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
}: {
  data: ChartDataPoint[];
  title: string;
  dataKey: keyof ChartDataPoint;
  color: string;
  unit?: string;
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
      </CardContent>
    </Card>
  );
}

export function TrendCharts() {
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState<14 | 30>(30);
  const tier = useSubscriptionStore((s) => s.getTier());
  const isPro = tier === 'pro' || tier === 'pro_plus';

  useEffect(() => {
    setLoading(true);
    ouraService
      .getTimeline(range)
      .then((entries) => setData(transformData(entries)))
      .catch(() => {})
      .finally(() => setLoading(false));
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
        No data available. Connect your Oura Ring and sync to see trends.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Range selector */}
      <div className="flex items-center gap-2">
        <Button
          variant={range === 14 ? 'primary' : 'outline'}
          size="sm"
          onClick={() => setRange(14)}
        >
          14 days
        </Button>
        <Button
          variant={range === 30 ? 'primary' : 'outline'}
          size="sm"
          onClick={() => setRange(30)}
        >
          30 days
        </Button>
      </div>

      {/* Main scores chart */}
      <ScoreChart data={data} title="Health Scores Overview" />

      {/* Detail charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <MetricChart
          data={data}
          title="Sleep Duration"
          dataKey="sleepHours"
          color="#6366f1"
          unit="hrs"
        />
        <MetricChart
          data={data}
          title="Daily Steps"
          dataKey="steps"
          color="#f59e0b"
          unit="steps"
        />
        <MetricChart
          data={data}
          title="Resting Heart Rate"
          dataKey="rhr"
          color="#ef4444"
          unit="bpm"
        />
        <MetricChart
          data={data}
          title="HRV Balance"
          dataKey="hrv"
          color="#22c55e"
        />
      </div>
    </div>
  );
}
