'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { ChevronDown, ChevronUp, TrendingUp, TrendingDown } from 'lucide-react';
import type { Correlation } from '@/types';

const STRENGTH_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  strong: {
    bg: 'bg-purple-100 dark:bg-purple-900/30',
    text: 'text-purple-700 dark:text-purple-300',
    dot: '#8b5cf6',
  },
  moderate: {
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    text: 'text-blue-700 dark:text-blue-300',
    dot: '#3b82f6',
  },
  weak: {
    bg: 'bg-slate-100 dark:bg-slate-700',
    text: 'text-slate-600 dark:text-slate-400',
    dot: '#94a3b8',
  },
};

interface CorrelationCardProps {
  correlation: Correlation;
}

export function CorrelationCard({ correlation: c }: CorrelationCardProps) {
  const [expanded, setExpanded] = useState(false);
  const colors = STRENGTH_COLORS[c.strength] || STRENGTH_COLORS.weak;

  return (
    <Card className="overflow-hidden">
      <div className="p-4 space-y-3">
        {/* Header row */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900 dark:text-slate-100 leading-snug">
              {c.effect_description || `${c.metric_a_label} vs ${c.metric_b_label}`}
            </p>
            <div className="flex items-center gap-2 mt-1.5">
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colors.bg} ${colors.text}`}
              >
                {c.strength}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                r = {c.correlation_coefficient > 0 ? '+' : ''}
                {c.correlation_coefficient.toFixed(2)}
              </span>
              {c.lag_days > 0 && (
                <span className="text-xs text-slate-400 dark:text-slate-500">
                  next-day
                </span>
              )}
            </div>
          </div>
          <div className="flex-shrink-0">
            {c.direction === 'negative' ? (
              <TrendingDown className="w-5 h-5 text-red-500" />
            ) : (
              <TrendingUp className="w-5 h-5 text-green-500" />
            )}
          </div>
        </div>

        {/* Metric labels */}
        <div className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
          <span className="font-medium">{c.metric_a_label}</span>
          <span>→</span>
          <span className="font-medium">{c.metric_b_label}</span>
        </div>

        {/* Mini chart */}
        {c.data_points.length > 0 && (
          <div className="h-32 -mx-2">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e2e8f0"
                  className="dark:stroke-slate-700"
                />
                <XAxis
                  dataKey="a_value"
                  type="number"
                  tick={{ fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                  name={c.metric_a_label}
                />
                <YAxis
                  dataKey="b_value"
                  type="number"
                  tick={{ fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                  name={c.metric_b_label}
                />
                <Tooltip
                  content={({ payload }) => {
                    if (!payload || payload.length === 0) return null;
                    const d = payload[0]?.payload;
                    if (!d) return null;
                    return (
                      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg px-3 py-2 text-xs shadow-lg">
                        <p className="text-slate-500 dark:text-slate-400">
                          {d.date}
                        </p>
                        <p className="text-slate-900 dark:text-slate-100">
                          {c.metric_a_label}: {d.a_value}
                        </p>
                        <p className="text-slate-900 dark:text-slate-100">
                          {c.metric_b_label}: {d.b_value}
                        </p>
                      </div>
                    );
                  }}
                />
                <Scatter data={c.data_points} fill={colors.dot} r={4} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Expand/collapse */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-primary-600 dark:text-primary-400 hover:underline"
        >
          {expanded ? (
            <>
              <ChevronUp className="w-3 h-3" /> Less detail
            </>
          ) : (
            <>
              <ChevronDown className="w-3 h-3" /> More detail
            </>
          )}
        </button>

        {expanded && (
          <div className="text-xs text-slate-500 dark:text-slate-400 space-y-1 pt-1 border-t border-slate-100 dark:border-slate-700">
            <p>
              <strong>Sample size:</strong> {c.sample_size} days
            </p>
            <p>
              <strong>p-value:</strong> {c.p_value.toFixed(4)}
            </p>
            <p>
              <strong>Lag:</strong>{' '}
              {c.lag_days === 0 ? 'Same day' : `${c.lag_days}-day delay`}
            </p>
            <p>
              <strong>Category:</strong>{' '}
              {c.category.replace('nutrition_', 'Nutrition → ').replace('_', ' ')}
            </p>
          </div>
        )}
      </div>
    </Card>
  );
}
