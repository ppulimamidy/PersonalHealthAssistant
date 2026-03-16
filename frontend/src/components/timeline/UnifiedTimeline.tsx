'use client';

/**
 * Unified Health Timeline — merges Timeline (daily cards) + Trends (charts)
 * into a single scrollable page with three zones:
 *   Zone 1: Overview strip (baseline comparison + period selector)
 *   Zone 2: Trend charts (collapsible)
 *   Zone 3: Daily cards with 4+ rings and expandable details
 */

import Link from 'next/link';
import { useMemo, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { HealthScoreRing } from '@/components/ui/HealthScoreRing';
import { Button } from '@/components/ui/Button';
import { api } from '@/services/api';
import { formatDate, formatDuration } from '@/lib/utils';
import {
  Moon, Footprints, Zap, Heart, Wind, Droplets, Flame, Timer,
  ChevronDown, ChevronUp, TrendingUp, ChevronRight,
} from 'lucide-react';
import type { TimelineEntry } from '@/types';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function avgOf(values: number[]): number | null {
  if (!values.length) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function fmtDelta(delta: number, unit: string) {
  const sign = delta > 0 ? '+' : '';
  const precision = unit === 'bpm' ? 1 : 0;
  return `${sign}${delta.toFixed(precision)}${unit ? ` ${unit}` : ''}`;
}

function fmtShortDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

const SOURCE_LABELS: Record<string, { label: string; color: string }> = {
  oura:           { label: '⊙ Oura',           color: '#818CF8' },
  healthkit:      { label: '🍎 Apple Health',   color: '#F87171' },
  health_connect: { label: '💚 Health Connect', color: '#34D399' },
};

const RING_COLORS = {
  sleep:    '#818CF8',
  heart:    '#F87171',
  activity: '#6EE7B7',
  recovery: '#F59E0B',
};

const DAY_OPTIONS = [14, 30, 60, 90] as const;

// ─── Chart data transform ─────────────────────────────────────────────────────

interface ChartPoint {
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
  vo2Max?: number;
}

function toChartData(entries: TimelineEntry[]): ChartPoint[] {
  return [...entries]
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((e) => {
      const raw = e as unknown as Record<string, unknown>;
      const native = raw.native as Record<string, number> | undefined;
      return {
        date: e.date,
        label: fmtShortDate(e.date),
        sleep: e.sleep?.sleep_score,
        readiness: e.readiness?.readiness_score,
        activity: e.activity?.activity_score,
        rhr: e.readiness?.resting_heart_rate,
        hrv: e.readiness?.hrv_balance,
        steps: e.activity?.steps,
        sleepHours: e.sleep ? Math.round((e.sleep.total_sleep_duration / 3600) * 10) / 10 : undefined,
        spo2: native?.spo2,
        respiratoryRate: native?.respiratory_rate,
        activeCals: native?.active_calories ?? e.activity?.active_calories,
        vo2Max: native?.vo2_max,
      };
    });
}

// ─── Mini metric chart ────────────────────────────────────────────────────────

function MiniChart({
  data, dataKey, color, unit, title,
}: {
  data: ChartPoint[];
  dataKey: string;
  color: string;
  unit?: string;
  title: string;
}) {
  const hasData = data.some((d) => (d as unknown as Record<string, unknown>)[dataKey] != null);
  if (!hasData) return null;

  return (
    <Card>
      <CardHeader className="pb-1">
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-36">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-20" />
              <XAxis dataKey="label" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 10 }} width={40} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0F1720', border: '1px solid #1E2A3B', borderRadius: 8, color: '#E8EDF5', fontSize: 12 }}
                formatter={(value: number) => unit ? `${value.toLocaleString()} ${unit}` : value.toLocaleString()}
              />
              <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={false} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Daily card with 4 rings ──────────────────────────────────────────────────

function DailyCard({ entry }: { entry: TimelineEntry }) {
  const [expanded, setExpanded] = useState(false);
  const raw = entry as unknown as Record<string, unknown>;
  const native = raw.native as Record<string, number> | undefined;
  const sources = (raw.sources as string[]) ?? [];

  const sleepScore = entry.sleep?.sleep_score;
  const hrvScore = entry.readiness?.hrv_balance;
  const activityScore = entry.activity?.activity_score;
  const readinessScore = entry.readiness?.readiness_score;

  return (
    <Card className="mb-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-base font-semibold text-[#E8EDF5]">{formatDate(entry.date)}</p>
          {sources.length > 0 && (
            <div className="flex gap-1.5 mt-1">
              {sources.map((s) => {
                const info = SOURCE_LABELS[s];
                return info ? (
                  <span key={s} className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ color: info.color, backgroundColor: `${info.color}15`, border: `1px solid ${info.color}30` }}>
                    {info.label}
                  </span>
                ) : null;
              })}
            </div>
          )}
        </div>
        <div className="flex items-center gap-4">
          {sleepScore != null && (
            <div className="flex flex-col items-center">
              <HealthScoreRing score={sleepScore} size="sm" showLabel={false} />
              <span className="text-[9px] text-[#526380] mt-0.5">Sleep</span>
            </div>
          )}
          {hrvScore != null && (
            <div className="flex flex-col items-center">
              <div className="w-[52px] h-[52px] rounded-full flex items-center justify-center border-[3px]" style={{ borderColor: RING_COLORS.heart }}>
                <span className="text-sm font-bold" style={{ color: RING_COLORS.heart }}>{Math.round(hrvScore)}</span>
              </div>
              <span className="text-[9px] text-[#526380] mt-0.5">Heart</span>
            </div>
          )}
          {activityScore != null && (
            <div className="flex flex-col items-center">
              <HealthScoreRing score={activityScore} size="sm" showLabel={false} />
              <span className="text-[9px] text-[#526380] mt-0.5">Activity</span>
            </div>
          )}
          {readinessScore != null && (
            <div className="flex flex-col items-center">
              <div className="w-[52px] h-[52px] rounded-full flex items-center justify-center border-[3px]" style={{ borderColor: RING_COLORS.recovery }}>
                <span className="text-sm font-bold" style={{ color: RING_COLORS.recovery }}>{Math.round(readinessScore)}</span>
              </div>
              <span className="text-[9px] text-[#526380] mt-0.5">Recovery</span>
            </div>
          )}
          <button type="button" onClick={() => setExpanded((v) => !v)} className="text-[#526380] hover:text-[#E8EDF5] transition-colors">
            {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="mt-5 pt-5 border-t border-[#1E2A3B] grid grid-cols-2 md:grid-cols-4 gap-6">
          {/* Sleep */}
          {entry.sleep && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Moon className="w-4 h-4" style={{ color: RING_COLORS.sleep }} />
                <span className="text-xs font-semibold text-[#E8EDF5]">Sleep</span>
              </div>
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between"><span className="text-[#526380]">Duration</span><span className="text-[#E8EDF5]">{formatDuration(entry.sleep.total_sleep_duration)}</span></div>
                <div className="flex justify-between"><span className="text-[#526380]">Deep Sleep</span><span className="text-[#E8EDF5]">{formatDuration(entry.sleep.deep_sleep_duration)}</span></div>
                <div className="flex justify-between"><span className="text-[#526380]">REM Sleep</span><span className="text-[#E8EDF5]">{formatDuration(entry.sleep.rem_sleep_duration)}</span></div>
                <div className="flex justify-between"><span className="text-[#526380]">Efficiency</span><span className="text-[#E8EDF5]">{entry.sleep.sleep_efficiency}%</span></div>
              </div>
            </div>
          )}

          {/* Heart */}
          {entry.readiness && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Heart className="w-4 h-4" style={{ color: RING_COLORS.heart }} />
                <span className="text-xs font-semibold text-[#E8EDF5]">Heart</span>
              </div>
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between"><span className="text-[#526380]">HRV</span><span className="text-[#E8EDF5]">{entry.readiness.hrv_balance} ms</span></div>
                <div className="flex justify-between"><span className="text-[#526380]">Resting HR</span><span className="text-[#E8EDF5]">{entry.readiness.resting_heart_rate} bpm</span></div>
                {native?.spo2 != null && <div className="flex justify-between"><span className="text-[#526380]">SpO₂</span><span className="text-[#E8EDF5]">{native.spo2.toFixed(1)}%</span></div>}
                {native?.respiratory_rate != null && <div className="flex justify-between"><span className="text-[#526380]">Resp Rate</span><span className="text-[#E8EDF5]">{native.respiratory_rate.toFixed(1)}/min</span></div>}
                <div className="flex justify-between"><span className="text-[#526380]">Temp Dev</span><span className="text-[#E8EDF5]">{entry.readiness.temperature_deviation?.toFixed(1) ?? '—'}°</span></div>
              </div>
            </div>
          )}

          {/* Activity */}
          {entry.activity && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Footprints className="w-4 h-4" style={{ color: RING_COLORS.activity }} />
                <span className="text-xs font-semibold text-[#E8EDF5]">Activity</span>
              </div>
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between"><span className="text-[#526380]">Steps</span><span className="text-[#E8EDF5]">{entry.activity.steps?.toLocaleString()}</span></div>
                <div className="flex justify-between"><span className="text-[#526380]">Calories</span><span className="text-[#E8EDF5]">{native?.active_calories ?? entry.activity.active_calories} kcal</span></div>
                {native?.workout_minutes != null && <div className="flex justify-between"><span className="text-[#526380]">Workouts</span><span className="text-[#E8EDF5]">{native.workout_minutes} min</span></div>}
                {native?.vo2_max != null && <div className="flex justify-between"><span className="text-[#526380]">VO₂ Max</span><span className="text-[#E8EDF5]">{native.vo2_max.toFixed(1)}</span></div>}
                <div className="flex justify-between"><span className="text-[#526380]">High Activity</span><span className="text-[#E8EDF5]">{entry.activity.high_activity_time} min</span></div>
              </div>
            </div>
          )}

          {/* Recovery */}
          {entry.readiness && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Zap className="w-4 h-4" style={{ color: RING_COLORS.recovery }} />
                <span className="text-xs font-semibold text-[#E8EDF5]">Recovery</span>
              </div>
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between"><span className="text-[#526380]">Readiness</span><span className="text-[#E8EDF5]">{entry.readiness.readiness_score}</span></div>
                <div className="flex justify-between"><span className="text-[#526380]">Score</span><span className="text-[#E8EDF5]">{entry.sleep ? Math.round((entry.sleep.sleep_score * 0.4 + entry.readiness.readiness_score * 0.35 + (entry.activity?.activity_score ?? 0) * 0.25)) : '—'}</span></div>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

// ─── Baseline comparison strip ────────────────────────────────────────────────

interface BaselineMetric { label: string; recent: number | null; baseline: number | null; unit: string; lowerIsBetter?: boolean }

function BaselineStrip({ metrics }: { metrics: BaselineMetric[] }) {
  const valid = metrics.filter((m) => m.recent != null && m.baseline != null);
  if (valid.length === 0) return null;

  return (
    <Card className="mb-5">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-[#8B97A8]">What changed (recent vs baseline)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {valid.map((m) => {
            const delta = (m.recent ?? 0) - (m.baseline ?? 0);
            const isGood = m.lowerIsBetter ? delta < 0 : delta > 0;
            const color = Math.abs(delta) < 0.5 ? '#526380' : isGood ? '#6EE7B7' : '#F87171';
            return (
              <div key={m.label} className="rounded-xl p-3" style={{ backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
                <p className="text-[10px] text-[#526380] mb-1">{m.label}</p>
                <p className="text-lg font-bold" style={{ color }}>{fmtDelta(delta, m.unit)}</p>
                <p className="text-[10px] text-[#526380]">Recent: {m.recent?.toFixed(1)} · Baseline: {m.baseline?.toFixed(1)}</p>
              </div>
            );
          })}
        </div>
        <p className="text-[10px] text-[#3A4A5C] mt-3">This is not medical advice. Trends can change due to illness, stress, travel, training, or sleep disruption.</p>
      </CardContent>
    </Card>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export function UnifiedTimeline() {
  const [days, setDays] = useState<14 | 30 | 60 | 90>(30);
  const [showCharts, setShowCharts] = useState(true);

  const { data: entries, isLoading, refetch } = useQuery<TimelineEntry[]>({
    queryKey: ['unified-timeline', days],
    queryFn: async () => {
      const { data: resp } = await api.get(`/api/v1/health/timeline?days=${days}&source_priority=auto`);
      return Array.isArray(resp) ? resp : (resp?.entries ?? []);
    },
  });

  const timeline = entries ?? [];
  const chartData = useMemo(() => toChartData(timeline), [timeline]);

  // Compute baseline: compare first half vs second half of the period
  const baselineMetrics = useMemo<BaselineMetric[]>(() => {
    if (timeline.length < 7) return [];
    const mid = Math.floor(timeline.length / 2);
    const recent = timeline.slice(0, mid); // desc order: recent first
    const older = timeline.slice(mid);

    const pick = (entries: TimelineEntry[], fn: (e: TimelineEntry) => number | undefined) => {
      const vals = entries.map(fn).filter((v): v is number => v != null);
      return avgOf(vals);
    };

    return [
      { label: 'Sleep Score', recent: pick(recent, (e) => e.sleep?.sleep_score), baseline: pick(older, (e) => e.sleep?.sleep_score), unit: '' },
      { label: 'HRV', recent: pick(recent, (e) => e.readiness?.hrv_balance), baseline: pick(older, (e) => e.readiness?.hrv_balance), unit: 'ms' },
      { label: 'Steps', recent: pick(recent, (e) => e.activity?.steps), baseline: pick(older, (e) => e.activity?.steps), unit: '' },
      { label: 'Resting HR', recent: pick(recent, (e) => e.readiness?.resting_heart_rate), baseline: pick(older, (e) => e.readiness?.resting_heart_rate), unit: 'bpm', lowerIsBetter: true },
    ];
  }, [timeline]);

  // All sources across the period
  const allSources = useMemo(() => {
    const set = new Set<string>();
    for (const e of timeline) {
      const srcs = (e as unknown as Record<string, unknown>).sources as string[] | undefined;
      srcs?.forEach((s) => set.add(s));
    }
    return Array.from(set);
  }, [timeline]);

  return (
    <div>
      {/* Zone 1: Header + controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[#E8EDF5]">Health Timeline</h1>
          <p className="text-[#526380] text-sm mt-1">Your daily metrics and trends at a glance</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex rounded-lg p-0.5" style={{ backgroundColor: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
            {DAY_OPTIONS.map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  days === d ? 'bg-[#00D4AA] text-[#080B10]' : 'text-[#526380] hover:text-[#E8EDF5]'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
          <Button variant="outline" size="sm" onClick={() => setShowCharts((v) => !v)}>
            <TrendingUp className="w-3.5 h-3.5 mr-1" />
            {showCharts ? 'Hide' : 'Show'} Charts
          </Button>
          <Link href="/doctor-prep?autogenerate=1&days=30">
            <Button size="sm">Doctor Prep</Button>
          </Link>
          <Button variant="outline" size="sm" onClick={() => refetch()}>Sync</Button>
        </div>
      </div>

      {/* Sources */}
      {allSources.length > 0 && (
        <div className="flex items-center gap-3 text-xs mb-4">
          <span className="text-[#526380]">Sources:</span>
          {allSources.map((s) => {
            const info = SOURCE_LABELS[s];
            return info ? <span key={s} style={{ color: info.color }}>{info.label}</span> : null;
          })}
        </div>
      )}

      {/* Baseline strip */}
      <BaselineStrip metrics={baselineMetrics} />

      {/* Zone 2: Trend charts (collapsible) */}
      {showCharts && chartData.length > 0 && (
        <div className="mb-6 space-y-4">
          {/* Main scores chart */}
          <Card>
            <CardHeader><CardTitle className="text-sm">Health Scores</CardTitle></CardHeader>
            <CardContent>
              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" className="opacity-20" />
                    <XAxis dataKey="label" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} width={30} />
                    <Tooltip contentStyle={{ backgroundColor: '#0F1720', border: '1px solid #1E2A3B', borderRadius: 8, color: '#E8EDF5', fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Line type="monotone" dataKey="sleep" stroke={RING_COLORS.sleep} strokeWidth={2} dot={false} name="Sleep" connectNulls />
                    <Line type="monotone" dataKey="readiness" stroke={RING_COLORS.recovery} strokeWidth={2} dot={false} name="Readiness" connectNulls />
                    <Line type="monotone" dataKey="activity" stroke={RING_COLORS.activity} strokeWidth={2} dot={false} name="Activity" connectNulls />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Metric detail charts */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <MiniChart data={chartData} dataKey="sleepHours" color={RING_COLORS.sleep} unit="hrs" title="Sleep Duration" />
            <MiniChart data={chartData} dataKey="steps" color={RING_COLORS.activity} unit="steps" title="Daily Steps" />
            <MiniChart data={chartData} dataKey="rhr" color={RING_COLORS.heart} unit="bpm" title="Resting HR" />
            <MiniChart data={chartData} dataKey="hrv" color="#00D4AA" title="HRV" />
            <MiniChart data={chartData} dataKey="spo2" color="#60A5FA" unit="%" title="SpO₂" />
            <MiniChart data={chartData} dataKey="respiratoryRate" color="#A78BFA" unit="/min" title="Resp Rate" />
            <MiniChart data={chartData} dataKey="activeCals" color="#FB923C" unit="kcal" title="Active Cal" />
            <MiniChart data={chartData} dataKey="vo2Max" color="#2DD4BF" unit="mL/kg/min" title="VO₂ Max" />
          </div>
        </div>
      )}

      {/* Zone 3: Daily cards */}
      {isLoading && <div className="text-center py-12 text-[#526380]">Loading timeline...</div>}
      {!isLoading && timeline.length === 0 && (
        <Card>
          <div className="text-center py-12">
            <p className="text-[#526380]">No timeline data yet. Connect a device and sync to see your health timeline.</p>
          </div>
        </Card>
      )}
      {!isLoading && timeline.map((entry) => (
        <DailyCard key={entry.date} entry={entry} />
      ))}
    </div>
  );
}
