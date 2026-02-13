'use client';

import { cn, getHealthStatus } from '@/lib/utils';

interface HealthScoreRingProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  showLabel?: boolean;
}

export function HealthScoreRing({
  score,
  size = 'md',
  label,
  showLabel = true
}: HealthScoreRingProps) {
  const status = getHealthStatus(score);

  const sizes = {
    sm: { ring: 60, stroke: 4, text: 'text-sm' },
    md: { ring: 80, stroke: 6, text: 'text-lg' },
    lg: { ring: 120, stroke: 8, text: 'text-2xl' },
  };

  const { ring, stroke, text } = sizes[size];
  const radius = (ring - stroke) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;

  const statusColors = {
    excellent: '#22c55e',
    good: '#84cc16',
    moderate: '#eab308',
    poor: '#f97316',
    critical: '#ef4444',
  };

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: ring, height: ring }}>
        <svg className="transform -rotate-90" width={ring} height={ring}>
          <circle
            cx={ring / 2}
            cy={ring / 2}
            r={radius}
            fill="none"
            className="stroke-slate-200 dark:stroke-slate-700"
            strokeWidth={stroke}
          />
          <circle
            cx={ring / 2}
            cy={ring / 2}
            r={radius}
            fill="none"
            stroke={statusColors[status]}
            strokeWidth={stroke}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={cn('font-bold text-slate-900 dark:text-slate-100', text)}>{score}</span>
        </div>
      </div>
      {showLabel && label && (
        <span className="mt-2 text-sm text-slate-600 dark:text-slate-400">{label}</span>
      )}
    </div>
  );
}
