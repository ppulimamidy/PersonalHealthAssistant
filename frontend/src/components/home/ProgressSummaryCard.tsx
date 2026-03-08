'use client';

import type { AdherenceStats, PersonalizedHealthScore } from '@/types';

interface MetricTile {
  label: string;
  current: number | null;
  prev: number | null;
  invertTrend?: boolean; // true = lower is better (e.g. symptom severity)
}

function TrendArrow({
  delta,
  invertTrend = false,
}: {
  delta: number;
  invertTrend?: boolean;
}) {
  const goodDelta = invertTrend ? -delta : delta;
  const arrow = goodDelta > 2 ? '↑' : goodDelta < -2 ? '↓' : '→';
  const color =
    goodDelta > 2 ? '#00D4AA' : goodDelta < -2 ? '#F87171' : '#526380';
  return (
    <span className="text-lg font-bold" style={{ color }}>
      {arrow}
    </span>
  );
}

interface ProgressSummaryCardProps {
  timeline?: Array<{ sleep?: { sleep_score: number } }>;
  symptomsData?: { symptoms?: Array<{ severity?: number }> };
  adherenceStats?: AdherenceStats;
  healthScore?: PersonalizedHealthScore;
}

function splitHalf<T>(arr: T[]): [T[], T[]] {
  const mid = Math.floor(arr.length / 2);
  return [arr.slice(0, mid), arr.slice(mid)];
}

function avg(nums: number[]): number | null {
  if (!nums.length) return null;
  return nums.reduce((a, b) => a + b, 0) / nums.length;
}

export function ProgressSummaryCard({
  timeline,
  symptomsData,
  adherenceStats,
  healthScore,
}: ProgressSummaryCardProps) {
  const tiles: MetricTile[] = [];

  // Sleep avg (last 7 vs prev 7 from 14-day timeline)
  const sleepScores = (timeline || [])
    .map((d) => d.sleep?.sleep_score)
    .filter((s): s is number => s != null);
  if (sleepScores.length >= 4) {
    const [prev, cur] = splitHalf(sleepScores.slice().reverse());
    tiles.push({ label: 'Sleep', current: avg(cur), prev: avg(prev) });
  }

  // Symptom severity (last 14d vs prev 14d — split symptoms array in half)
  const symptoms = symptomsData?.symptoms ?? [];
  const severities = symptoms
    .map((s) => s.severity)
    .filter((s): s is number => s != null);
  if (severities.length >= 4) {
    const [prev, cur] = splitHalf(severities);
    tiles.push({ label: 'Symptoms', current: avg(cur), prev: avg(prev), invertTrend: true });
  }

  // Medication adherence
  if (
    adherenceStats &&
    typeof adherenceStats === 'object' &&
    'total_scheduled' in adherenceStats &&
    (adherenceStats as any).total_scheduled > 0
  ) {
    const rate = (adherenceStats as any).adherence_rate ?? 0;
    tiles.push({ label: 'Adherence', current: rate, prev: null });
  }

  // Health score trend
  if (healthScore?.score_value != null) {
    tiles.push({ label: 'Health Score', current: healthScore.score_value, prev: null });
  }

  // Hide if fewer than 2 tiles have sufficient data
  const tilesWithData = tiles.filter(
    (t) => t.current != null && (t.prev != null || t.label === 'Adherence' || t.label === 'Health Score')
  );
  if (tilesWithData.length < 2) return null;

  return (
    <div
      className="rounded-xl p-5"
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      <h2 className="text-sm font-semibold text-[#8B97A8] mb-4">Am I Improving?</h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {tilesWithData.map((tile) => {
          const delta =
            tile.current != null && tile.prev != null
              ? tile.current - tile.prev
              : null;
          return (
            <div
              key={tile.label}
              className="rounded-lg p-3 flex flex-col gap-1"
              style={{ backgroundColor: 'rgba(255,255,255,0.03)' }}
            >
              <span className="text-xs text-[#526380]">{tile.label}</span>
              <div className="flex items-end gap-1">
                <span className="text-xl font-bold text-[#E8EDF5]">
                  {tile.current != null ? Math.round(tile.current) : '—'}
                  {tile.label === 'Adherence' ? '%' : ''}
                </span>
                {delta != null && (
                  <TrendArrow delta={delta} invertTrend={tile.invertTrend} />
                )}
              </div>
              {tile.prev != null && (
                <span className="text-[10px] text-[#3D4F66]">
                  prev {Math.round(tile.prev)}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
