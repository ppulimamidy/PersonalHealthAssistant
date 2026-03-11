'use client';

import { TrendingUp, TrendingDown, Minus, Brain } from 'lucide-react';
import type { InterventionOutcome } from '@/types';

interface OutcomeCardProps {
  outcome: InterventionOutcome;
  title?: string;
}

function DeltaRow({ metric, pct }: { metric: string; pct: number }) {
  const label = metric.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  const isPositive = pct > 2;
  const isNegative = pct < -2;
  const Icon = isPositive ? TrendingUp : isNegative ? TrendingDown : Minus;
  const color = isPositive ? '#00D4AA' : isNegative ? '#F87171' : '#526380';

  return (
    <div
      className="flex items-center justify-between p-2.5 rounded-lg"
      style={{ backgroundColor: 'rgba(255,255,255,0.03)' }}
    >
      <div className="flex items-center gap-2">
        <Icon className="w-3.5 h-3.5 flex-shrink-0" style={{ color }} />
        <span className="text-xs text-[#8B97A8]">{label}</span>
      </div>
      <span className="text-xs font-semibold" style={{ color }}>
        {isPositive ? '+' : ''}{pct.toFixed(1)}%
      </span>
    </div>
  );
}

export function OutcomeCard({ outcome, title = 'Intervention Outcome' }: OutcomeCardProps) {
  const deltaPairs = Object.entries(outcome.outcome_delta).filter(([, v]) => Math.abs(v) > 0.5);
  const improvements = deltaPairs.filter(([, v]) => v > 2).length;
  const declines = deltaPairs.filter(([, v]) => v < -2).length;

  return (
    <div
      className="rounded-xl border p-4"
      style={{
        backgroundColor: '#0E1520',
        borderColor: 'rgba(0,212,170,0.15)',
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: '#00D4AA18' }}
        >
          <Brain className="w-4 h-4" style={{ color: '#00D4AA' }} />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-[#E8EDF5]">{title}</h3>
          <p className="text-xs text-[#526380]">
            {outcome.adherence_pct.toFixed(0)}% adherence · completed{' '}
            {new Date(outcome.completed_at).toLocaleDateString()}
          </p>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <div
          className="rounded-lg p-2 text-center"
          style={{ backgroundColor: 'rgba(255,255,255,0.03)' }}
        >
          <div className="text-base font-bold" style={{ color: '#00D4AA' }}>
            {improvements}
          </div>
          <div className="text-[10px] text-[#526380]">Improved</div>
        </div>
        <div
          className="rounded-lg p-2 text-center"
          style={{ backgroundColor: 'rgba(255,255,255,0.03)' }}
        >
          <div className="text-base font-bold text-[#F87171]">{declines}</div>
          <div className="text-[10px] text-[#526380]">Declined</div>
        </div>
        <div
          className="rounded-lg p-2 text-center"
          style={{ backgroundColor: 'rgba(255,255,255,0.03)' }}
        >
          <div className="text-base font-bold text-[#8B97A8]">
            {deltaPairs.length - improvements - declines}
          </div>
          <div className="text-[10px] text-[#526380]">Neutral</div>
        </div>
      </div>

      {/* AI summary */}
      {outcome.summary && (
        <div
          className="rounded-lg p-3 mb-3 text-xs text-[#8B97A8] leading-relaxed italic"
          style={{ backgroundColor: '#00D4AA0D', borderLeft: '2px solid #00D4AA30' }}
        >
          {outcome.summary}
        </div>
      )}

      {/* Deltas */}
      {deltaPairs.length > 0 && (
        <div className="space-y-1.5">
          {deltaPairs
            .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
            .map(([metric, pct]) => (
              <DeltaRow key={metric} metric={metric} pct={pct} />
            ))}
        </div>
      )}

      {deltaPairs.length === 0 && (
        <p className="text-xs text-[#526380] text-center py-2">
          Insufficient data to measure metric changes.
        </p>
      )}

      {/* Memory note */}
      <p className="text-[10px] text-[#3D4F66] mt-3 text-center">
        Outcome stored in AI memory · future correlations use this as a personalised prior
      </p>
    </div>
  );
}
