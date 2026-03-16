'use client';

/**
 * Health Rings — 4 concentric SVG rings for web dashboard.
 *
 * Outer:     Sleep (hours vs goal)
 * Mid-outer: Heart (HRV vs baseline)
 * Mid-inner: Activity (steps vs goal)
 * Inner:     Recovery (readiness score vs 100)
 *
 * Center shows overall health score.
 */

export interface RingData {
  sleep: { value: number; goal: number };
  heart: { value: number; goal: number };
  activity: { value: number; goal: number };
  recovery: { value: number; goal: number };
  overallScore: number | null;
}

interface RingConfig {
  key: keyof Omit<RingData, 'overallScore'>;
  label: string;
  color: string;
  trackColor: string;
  unit: string;
  formatValue: (v: number) => string;
  helpTip: string;
}

const RINGS: RingConfig[] = [
  {
    key: 'sleep',
    label: 'Sleep',
    color: '#818CF8',
    trackColor: 'rgba(129,140,248,0.08)',
    unit: 'h',
    formatValue: (v) => v.toFixed(1),
    helpTip: 'Total sleep duration last night. Goal is 7-9 hours for most adults. Good sleep improves recovery, focus, and immune function.',
  },
  {
    key: 'heart',
    label: 'Heart',
    color: '#F87171',
    trackColor: 'rgba(248,113,113,0.08)',
    unit: 'ms',
    formatValue: (v) => Math.round(v).toString(),
    helpTip: 'Heart Rate Variability (HRV) in milliseconds. Higher is generally better — it indicates your nervous system is adaptable and resilient to stress.',
  },
  {
    key: 'activity',
    label: 'Activity',
    color: '#6EE7B7',
    trackColor: 'rgba(110,231,183,0.08)',
    unit: '',
    formatValue: (v) => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : Math.round(v).toString(),
    helpTip: 'Daily step count from your phone or wearable. 8,000+ steps/day is associated with lower risk of heart disease and improved mood.',
  },
  {
    key: 'recovery',
    label: 'Recovery',
    color: '#F59E0B',
    trackColor: 'rgba(245,158,11,0.08)',
    unit: '',
    formatValue: (v) => Math.round(v).toString(),
    helpTip: 'How ready your body is to perform today (0-100). Based on sleep quality, HRV, and resting heart rate. Higher means you\'re well-recovered.',
  },
];

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}

export function HealthRings({
  data,
  size = 200,
}: {
  data: RingData;
  size?: number;
}) {
  const cx = size / 2;
  const cy = size / 2;
  const strokeWidth = 10;
  const gap = 4;

  return (
    <div className="flex flex-col items-center">
      <div style={{ width: size, height: size, position: 'relative' }}>
        <svg width={size} height={size}>
          {RINGS.map((ring, i) => {
            const radius = cx - strokeWidth / 2 - i * (strokeWidth + gap);
            if (radius <= 0) return null;
            const circumference = 2 * Math.PI * radius;
            const ringData = data[ring.key];
            const progress = clamp01(ringData.value / (ringData.goal || 1));
            const dashOffset = circumference * (1 - progress);

            return (
              <g key={ring.key}>
                {/* Track */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={radius}
                  stroke={ring.trackColor}
                  strokeWidth={strokeWidth}
                  fill="none"
                />
                {/* Progress arc */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={radius}
                  stroke={ring.color}
                  strokeWidth={strokeWidth}
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  strokeDashoffset={dashOffset}
                  transform={`rotate(-90 ${cx} ${cy})`}
                  style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
                />
              </g>
            );
          })}
        </svg>

        {/* Center score */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-center"
        >
          <span className="text-3xl font-bold text-[#E8EDF5]">
            {data.overallScore != null ? Math.round(data.overallScore) : '—'}
          </span>
          <span className="text-[10px] text-[#526380] -mt-0.5">Health Score</span>
        </div>
      </div>

      {/* Legend — hover for help */}
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 mt-3">
        {RINGS.map((ring) => {
          const rd = data[ring.key];
          const pct = Math.round(clamp01(rd.value / (rd.goal || 1)) * 100);
          return (
            <div key={ring.key} className="relative group flex items-center gap-1 cursor-help">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: ring.color }} />
              <span className="text-[10px] text-[#526380]">
                {ring.label} {ring.formatValue(rd.value)}{ring.unit} ({pct}%)
              </span>
              {/* Tooltip on hover */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 px-3 py-2 rounded-lg bg-[#0F1720] border border-[#1E2A3B] text-xs text-[#8B97A8] leading-relaxed opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 pointer-events-none z-50 shadow-lg">
                <div className="flex items-center gap-1.5 mb-1">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: ring.color }} />
                  <span className="text-[#E8EDF5] font-medium">{ring.label}</span>
                </div>
                {ring.helpTip}
                <div className="absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 bg-[#0F1720] border-r border-b border-[#1E2A3B] rotate-45 -mt-1" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
