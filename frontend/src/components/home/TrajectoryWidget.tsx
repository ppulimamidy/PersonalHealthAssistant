'use client';

import { useQuery } from '@tanstack/react-query';
import { healthScoreService } from '@/services/healthScore';
import type { TrajectoryComponent } from '@/types';

// ── Arc meter helpers ─────────────────────────────────────────────────────────

const SIZE = 120;
const STROKE = 8;
const R = (SIZE - STROKE) / 2;
const CIRCUM = 2 * Math.PI * R;
// Arc spans 240° (120° each side from 6 o'clock → start at 210°, end at 330°)
const ARC_FRAC = 240 / 360;

function ArcMeter({ score, color }: { score: number; color: string }) {
  const cx = SIZE / 2;
  const cy = SIZE / 2;
  const startAngle = 150; // degrees — start bottom-left
  const start = polarToCartesian(cx, cy, R, startAngle);
  const end   = polarToCartesian(cx, cy, R, startAngle + 240);
  const trackPath = describeArc(cx, cy, R, startAngle, startAngle + 240);
  const filledDeg = (score / 100) * 240;
  const fillPath  = describeArc(cx, cy, R, startAngle, startAngle + filledDeg);

  return (
    <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
      {/* Track */}
      <path d={trackPath} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={STROKE} strokeLinecap="round" />
      {/* Fill */}
      {filledDeg > 0 && (
        <path d={fillPath} fill="none" stroke={color} strokeWidth={STROKE} strokeLinecap="round" />
      )}
      {/* Score text */}
      <text x={cx} y={cy - 4} textAnchor="middle" fill="#E8EDF5" fontSize="22" fontWeight="700" fontFamily="monospace">
        {Math.round(score)}
      </text>
      <text x={cx} y={cy + 14} textAnchor="middle" fill="#526380" fontSize="9" letterSpacing="1">
        / 100
      </text>
    </svg>
  );
}

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function describeArc(cx: number, cy: number, r: number, startDeg: number, endDeg: number) {
  const s = polarToCartesian(cx, cy, r, startDeg);
  const e = polarToCartesian(cx, cy, r, endDeg);
  const large = endDeg - startDeg > 180 ? 1 : 0;
  return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y}`;
}

// ── Component bar ─────────────────────────────────────────────────────────────

function ComponentBar({ comp }: { comp: TrajectoryComponent }) {
  const color = comp.available
    ? comp.score >= 80 ? '#00D4AA'
    : comp.score >= 55 ? '#FBBF24'
    : '#F87171'
    : '#3D4F66';

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] text-[#526380]">{comp.label}</span>
        <span className="text-[10px] font-semibold" style={{ color }}>
          {comp.available ? `${Math.round(comp.score)}` : '—'}
        </span>
      </div>
      <div className="h-1 w-full rounded-full bg-white/5 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${comp.available ? comp.score : 0}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

// ── Main widget ───────────────────────────────────────────────────────────────

export function TrajectoryWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ['trajectory'],
    queryFn: healthScoreService.getTrajectory,
    staleTime: 5 * 60_000,
  });

  if (isLoading || !data || data.direction === 'insufficient' || data.score == null) return null;

  const arcColor = data.score >= 80 ? '#00D4AA' : data.score >= 55 ? '#FBBF24' : '#F87171';
  const deltaLabel =
    data.delta_30d == null ? null
    : data.delta_30d > 0 ? `↑ +${data.delta_30d} vs last month`
    : data.delta_30d < 0 ? `↓ ${data.delta_30d} vs last month`
    : '→ stable vs last month';
  const deltaColor = data.delta_30d == null ? '#526380'
    : data.delta_30d > 3 ? '#00D4AA'
    : data.delta_30d < -3 ? '#F87171'
    : '#526380';

  return (
    <div
      className="rounded-xl p-5"
      style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
    >
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-sm font-semibold text-[#8B97A8]">Health Trajectory</h2>
        {data.data_quality === 'partial' && (
          <span className="text-[9px] text-[#3D4F66] bg-white/5 px-2 py-0.5 rounded-full">partial data</span>
        )}
      </div>

      <div className="flex items-center gap-6 mt-3">
        {/* Arc meter */}
        <div className="flex flex-col items-center flex-shrink-0">
          <ArcMeter score={data.score} color={arcColor} />
          {deltaLabel && (
            <p className="text-[9px] font-medium mt-1" style={{ color: deltaColor }}>
              {deltaLabel}
            </p>
          )}
        </div>

        {/* Component bars */}
        <div className="flex-1 space-y-2.5">
          {data.components.map((comp) => (
            <ComponentBar key={comp.name} comp={comp} />
          ))}
        </div>
      </div>
    </div>
  );
}
