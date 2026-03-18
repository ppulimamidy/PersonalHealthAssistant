'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { correlationsService } from '@/services/correlations';
import { useAuth } from '@/hooks/useAuth';
import { ArrowRight, Info, AlertCircle, ChevronDown } from 'lucide-react';
import type { CausalGraph, CausalEdge } from '@/types';

// ── Plain-language summary ─────────────────────────────────────────────────────

function PlainLanguageSummary({ edges }: { readonly edges: CausalEdge[] }) {
  if (!edges.length) return null;
  const top = edges[0];
  const dir = top.correlation >= 0 ? 'increase' : 'decrease';
  const lagSuffix = top.optimal_lag_days === 1 ? 'day' : 'days';
  const lag =
    top.optimal_lag_days > 0
      ? `${top.optimal_lag_days} ${lagSuffix} later`
      : 'the same day';
  const moreSuffix = edges.length > 2 ? 's' : '';
  return (
    <div
      className="p-4 rounded-xl"
      style={{ backgroundColor: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.15)' }}
    >
      <p className="text-xs font-semibold uppercase mb-1" style={{ color: '#00D4AA' }}>
        {edges.length} causal pattern{edges.length === 1 ? '' : 's'} detected
      </p>
      <p className="text-sm text-slate-200">
        When your <strong>{top.from_label}</strong> is high, your{' '}
        <strong>{top.to_label}</strong> tends to {dir} {lag}.
        {edges.length > 1 && ` (+\u00a0${edges.length - 1} more pattern${moreSuffix} below)`}
      </p>
    </div>
  );
}

// ── Node type → human-readable category ───────────────────────────────────────

const NODE_TYPE_LABEL: Record<string, string> = {
  nutrition: 'Nutrition',
  health: 'Health Metric',
  wearable: 'Wearable',
  medical: 'Medical',
  symptom: 'Symptom',
  medication: 'Medication',
  lab: 'Lab Result',
};

// ── Main component ─────────────────────────────────────────────────────────────

export function CausalGraphView() {
  const { user, isLoading: isAuthLoading } = useAuth(true);
  const [days, setDays] = useState<7 | 14>(14);
  const [infoOpen, setInfoOpen] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ['causal-graph', days],
    queryFn: () => correlationsService.getCausalGraph(days),
    enabled: Boolean(user) && !isAuthLoading,
  });

  if (isAuthLoading || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-slate-500">Loading causal graph...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <div className="flex items-center gap-2 text-red-800 dark:text-red-200">
          <AlertCircle className="w-5 h-5" />
          <span>Failed to load causal graph. Try refreshing.</span>
        </div>
      </div>
    );
  }

  const graph = data as CausalGraph;

  if (!graph || graph.edges.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <Info className="w-12 h-12 mx-auto mb-4 text-slate-400 dark:text-slate-600" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
            No Causal Relationships Found
          </h3>
          <p className="text-slate-600 dark:text-slate-400 max-w-md mx-auto">
            Not enough data to detect causal relationships. Keep logging meals and syncing your
            connected devices to see how your lifestyle causally affects your health.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Build node-type lookup from the nodes list
  const nodeTypeMap = Object.fromEntries(
    graph.nodes.map((n) => [n.id, n.type])
  );

  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case 'strong':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
      case 'moderate':
        return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800';
      case 'weak':
        return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800';
      default:
        return 'text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700';
    }
  };

  const getArrowColor = (strength: string) => {
    if (strength === 'strong') return 'text-red-600';
    if (strength === 'moderate') return 'text-yellow-600';
    return 'text-blue-600';
  };

  const getEvidenceBadge = (evidence: string[]) => {
    if (evidence.includes('granger_causality')) {
      return (
        <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs rounded font-medium">
          AI Verified
        </span>
      );
    }
    if (evidence.includes('temporal_precedence')) {
      return (
        <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs rounded font-medium">
          Temporal Precedence
        </span>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
            Causes
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            What&apos;s most likely driving your symptoms
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={days === 7 ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setDays(7)}
          >
            7 Days
          </Button>
          <Button
            variant={days === 14 ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setDays(14)}
          >
            14 Days
          </Button>
        </div>
      </div>

      {/* Plain-language summary */}
      <PlainLanguageSummary edges={graph.edges} />

      {/* Info Card — collapsible */}
      <div
        className="rounded-xl overflow-hidden"
        style={{ border: '1px solid rgba(255,255,255,0.06)' }}
      >
        <button
          className="w-full flex items-center justify-between px-4 py-3 text-left"
          style={{ backgroundColor: 'rgba(255,255,255,0.02)' }}
          onClick={() => setInfoOpen((v) => !v)}
        >
          <div className="flex items-center gap-2 text-sm" style={{ color: '#8B97A8' }}>
            <Info className="w-4 h-4" />
            <span>What does this mean?</span>
          </div>
          <ChevronDown
            className="w-4 h-4 transition-transform"
            style={{ color: '#526380', transform: infoOpen ? 'rotate(180deg)' : 'none' }}
          />
        </button>
        {infoOpen && (
          <div className="px-4 pb-4 pt-2" style={{ backgroundColor: 'rgba(255,255,255,0.02)' }}>
            <p className="text-sm text-slate-400">
              These patterns show what factors most influence how you feel. The AI checks whether
              something happening today (like eating a certain food or taking a medication) consistently
              leads to a health change days later — not just a coincidence.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <span className="px-2 py-1 bg-purple-900/30 text-purple-300 text-xs rounded">
                AI Verified: consistently predicts outcome
              </span>
              <span className="px-2 py-1 bg-blue-900/30 text-blue-300 text-xs rounded">
                Time-based: cause comes before effect
              </span>
              <span className="px-2 py-1 bg-green-900/30 text-green-300 text-xs rounded">
                Correlation: X relates to Y
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Causal Edges */}
      <div className="space-y-3">
        {graph.edges.map((edge: CausalEdge) => (
          <Card
            key={`${edge.from_metric}-${edge.to_metric}`}
            className={`border ${getStrengthColor(edge.strength)}`}
          >
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                {/* From Node */}
                <div className="flex-1">
                  <div className="text-xs text-slate-500 dark:text-slate-400 uppercase mb-1">
                    Cause
                  </div>
                  <div className="font-semibold text-slate-900 dark:text-slate-100">
                    {edge.from_label}
                  </div>
                  <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                    {NODE_TYPE_LABEL[nodeTypeMap[edge.from_metric] ?? ''] ?? 'Input'}
                  </div>
                </div>

                {/* Arrow */}
                <div className="flex flex-col items-center gap-1">
                  <ArrowRight className={`w-8 h-8 ${getArrowColor(edge.strength)}`} />
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    {edge.optimal_lag_days > 0 ? `+${edge.optimal_lag_days}d` : 'same day'}
                  </div>
                </div>

                {/* To Node */}
                <div className="flex-1">
                  <div className="text-xs text-slate-500 dark:text-slate-400 uppercase mb-1">
                    Effect
                  </div>
                  <div className="font-semibold text-slate-900 dark:text-slate-100">
                    {edge.to_label}
                  </div>
                  <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                    {NODE_TYPE_LABEL[nodeTypeMap[edge.to_metric] ?? ''] ?? 'Health Metric'}
                  </div>
                </div>

                {/* Metadata */}
                <div className="flex flex-col gap-2 min-w-[200px]">
                  <div className="text-xs text-slate-700 dark:text-slate-300">
                    <strong>Confidence:</strong> {(edge.causality_score * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-slate-700 dark:text-slate-300">
                    <strong>Correlation:</strong> {edge.correlation > 0 ? '+' : ''}{(edge.correlation * 100).toFixed(0)}%
                  </div>
                  {edge.granger_p_value != null && (
                    <div className="text-xs text-slate-700 dark:text-slate-300">
                      <strong>Statistical significance:</strong> {edge.granger_p_value.toFixed(3)}
                    </div>
                  )}
                  <div className="mt-1">
                    {getEvidenceBadge(edge.evidence)}
                  </div>
                </div>
              </div>

              {/* Evidence List */}
              <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                <div className="text-xs text-slate-600 dark:text-slate-400">
                  <strong>Evidence types:</strong>{' '}
                  {edge.evidence.map((e) => e.replaceAll('_', ' ')).join(', ')}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Data sources footnote */}
      {graph.data_sources_used && graph.data_sources_used.length > 0 && (
        <p className="text-xs text-slate-400 dark:text-slate-500 pt-2 border-t border-slate-100 dark:border-slate-800">
          <span className="font-medium">Data sources used: </span>
          {graph.data_sources_used.join(', ')}
        </p>
      )}

      {/* Disclaimer */}
      <Card>
        <CardContent className="pt-6">
          <div className="text-sm text-slate-600 dark:text-slate-400">
            <strong>Note:</strong> Causal relationships are inferred using statistical methods and
            should be interpreted carefully. Consult with healthcare professionals before making
            significant lifestyle changes.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
