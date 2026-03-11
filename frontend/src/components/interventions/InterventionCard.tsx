'use client';

import { useState } from 'react';
import { CheckCircle, XCircle, Clock, Activity, ChevronDown, ChevronUp, Zap } from 'lucide-react';
import type { ActiveIntervention } from '@/types';

const PATTERN_META: Record<string, { label: string; color: string; icon: string }> = {
  overtraining:     { label: 'Overtraining Recovery', color: '#F59E0B', icon: '🏋️' },
  inflammation:     { label: 'Inflammation Reduction', color: '#EF4444', icon: '🔥' },
  poor_recovery:    { label: 'Recovery Boost',         color: '#3B82F6', icon: '💙' },
  sleep_disruption: { label: 'Sleep Optimisation',     color: '#8B5CF6', icon: '🌙' },
};

const STATUS_META: Record<string, { label: string; color: string }> = {
  active:    { label: 'Active', color: '#00D4AA' },
  completed: { label: 'Completed', color: '#3B82F6' },
  abandoned: { label: 'Abandoned', color: '#6B7280' },
};

interface InterventionCardProps {
  intervention: ActiveIntervention;
  onCheckin?: (id: string, adhered: boolean) => void;
  onComplete?: (id: string) => void;
  onAbandon?: (id: string) => void;
}

function MetricDelta({ metric, pct }: { metric: string; pct: number }) {
  const isPositive = pct > 0;
  const label = metric.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  return (
    <div className="flex items-center justify-between py-1 border-b border-white/5 last:border-0">
      <span className="text-xs text-[#8B97A8]">{label}</span>
      <span
        className="text-xs font-semibold"
        style={{ color: isPositive ? '#00D4AA' : '#F87171' }}
      >
        {isPositive ? '+' : ''}{pct.toFixed(1)}%
      </span>
    </div>
  );
}

export function InterventionCard({
  intervention: iv,
  onCheckin,
  onComplete,
  onAbandon,
}: InterventionCardProps) {
  const [expanded, setExpanded] = useState(false);
  const meta = PATTERN_META[iv.recommendation_pattern] || {
    label: iv.recommendation_pattern,
    color: '#00D4AA',
    icon: '🧪',
  };
  const statusMeta = STATUS_META[iv.status] || STATUS_META.active;
  const adherencePct = iv.adherence_pct ?? 0;
  const daysRemaining = iv.days_remaining ?? 0;
  const hasDelta = iv.outcome_delta && Object.keys(iv.outcome_delta).length > 0;
  const deltaPairs = hasDelta ? Object.entries(iv.outcome_delta!) : [];

  return (
    <div
      className="rounded-xl border transition-all duration-150 hover:border-white/10"
      style={{
        backgroundColor: '#0E1520',
        borderColor: 'rgba(255,255,255,0.06)',
      }}
    >
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center text-base flex-shrink-0"
            style={{ backgroundColor: `${meta.color}18` }}
          >
            {meta.icon}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-medium" style={{ color: meta.color }}>
                {meta.label}
              </span>
              <span
                className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded"
                style={{
                  backgroundColor: `${statusMeta.color}18`,
                  color: statusMeta.color,
                }}
              >
                {statusMeta.label}
              </span>
            </div>
            <h3 className="text-sm font-semibold text-[#E8EDF5] mt-0.5 leading-tight">
              {iv.title}
            </h3>
            {iv.description && (
              <p className="text-xs text-[#526380] mt-1 leading-snug">{iv.description}</p>
            )}
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 text-[#526380] hover:text-[#8B97A8] transition-colors flex-shrink-0"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>

        {/* Progress bar */}
        <div className="mt-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-[#526380]">Adherence</span>
            <span className="text-xs font-medium text-[#8B97A8]">
              {iv.adherence_days}/{iv.duration_days} days
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${Math.min(100, adherencePct)}%`,
                backgroundColor: adherencePct >= 70 ? '#00D4AA' : adherencePct >= 40 ? '#F59E0B' : '#EF4444',
              }}
            />
          </div>
        </div>

        {/* Footer stats */}
        <div className="flex items-center gap-4 mt-3">
          {iv.status === 'active' && (
            <div className="flex items-center gap-1.5 text-xs text-[#526380]">
              <Clock className="w-3.5 h-3.5" />
              <span>{daysRemaining}d remaining</span>
            </div>
          )}
          <div className="flex items-center gap-1.5 text-xs text-[#526380]">
            <Activity className="w-3.5 h-3.5" />
            <span>{iv.data_sources.join(', ')}</span>
          </div>
          {hasDelta && (
            <div className="flex items-center gap-1.5 text-xs" style={{ color: '#00D4AA' }}>
              <Zap className="w-3.5 h-3.5" />
              <span>Outcome measured</span>
            </div>
          )}
        </div>
      </div>

      {/* Expanded: outcome delta or checkin history */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-white/5 pt-3">
          {/* Outcome deltas */}
          {hasDelta && (
            <div className="mb-4">
              <p className="text-xs font-medium text-[#526380] uppercase tracking-wider mb-2">
                Outcome vs Baseline
              </p>
              <div>
                {deltaPairs.map(([metric, pct]) => (
                  <MetricDelta key={metric} metric={metric} pct={pct} />
                ))}
              </div>
            </div>
          )}

          {/* AI summary */}
          {iv.outcome_delta && (
            <div
              className="rounded-lg p-3 mb-4 text-xs text-[#8B97A8] leading-relaxed"
              style={{ backgroundColor: '#00D4AA0D' }}
            >
              Outcomes written to AI memory — your next correlation analysis will use these as personalised priors.
            </div>
          )}

          {/* Action buttons */}
          {iv.status === 'active' && (
            <div className="flex items-center gap-2 flex-wrap">
              {onCheckin && (
                <>
                  <button
                    onClick={() => onCheckin(iv.id, true)}
                    className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-medium transition-all"
                    style={{ backgroundColor: '#00D4AA18', color: '#00D4AA' }}
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    Followed today
                  </button>
                  <button
                    onClick={() => onCheckin(iv.id, false)}
                    className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-medium transition-all text-[#8B97A8] hover:text-[#C8D5E8]"
                    style={{ backgroundColor: 'rgba(255,255,255,0.04)' }}
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    Skipped today
                  </button>
                </>
              )}
              {onComplete && daysRemaining === 0 && (
                <button
                  onClick={() => onComplete(iv.id)}
                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-medium transition-all"
                  style={{ backgroundColor: '#3B82F618', color: '#3B82F6' }}
                >
                  <Zap className="w-3.5 h-3.5" />
                  See results
                </button>
              )}
              {onAbandon && (
                <button
                  onClick={() => onAbandon(iv.id)}
                  className="text-xs px-3 py-1.5 rounded-lg text-[#526380] hover:text-[#F87171] transition-colors"
                  style={{ backgroundColor: 'rgba(255,255,255,0.03)' }}
                >
                  Abandon
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
