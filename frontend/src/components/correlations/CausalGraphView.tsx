'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { correlationsService } from '@/services/correlations';
import { useAuth } from '@/hooks/useAuth';
import { ArrowRight, Info, AlertCircle } from 'lucide-react';
import type { CausalGraph, CausalEdge } from '@/types';

export function CausalGraphView() {
  const { user, isLoading: isAuthLoading } = useAuth(true);
  const [days, setDays] = useState<7 | 14>(14);

  const { data, isLoading, error, refetch } = useQuery({
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
            wearable to see how nutrition causally affects your health metrics.
          </p>
        </CardContent>
      </Card>
    );
  }

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

  const getEvidenceBadge = (evidence: string[]) => {
    if (evidence.includes('granger_causality')) {
      return (
        <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs rounded font-medium">
          Granger Causality Confirmed
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
            Causal Graph
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Directional relationships showing how nutrition causally affects health metrics
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

      {/* Info Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-slate-700 dark:text-slate-300">
                This graph shows <strong>causal relationships</strong> detected using advanced
                statistical analysis (Granger causality testing). Causality score combines
                correlation strength, temporal precedence, and predictive power.
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs rounded">
                  Granger Causality: X predicts Y
                </span>
                <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs rounded">
                  Temporal Precedence: X precedes Y
                </span>
                <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs rounded">
                  Correlation: X relates to Y
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Causal Edges */}
      <div className="space-y-3">
        {graph.edges.map((edge: CausalEdge, idx: number) => (
          <Card key={idx} className={`border ${getStrengthColor(edge.strength)}`}>
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
                    Nutrition
                  </div>
                </div>

                {/* Arrow */}
                <div className="flex flex-col items-center gap-1">
                  <ArrowRight className={`w-8 h-8 ${edge.strength === 'strong' ? 'text-red-600' : edge.strength === 'moderate' ? 'text-yellow-600' : 'text-blue-600'}`} />
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
                    Health Metric
                  </div>
                </div>

                {/* Metadata */}
                <div className="flex flex-col gap-2 min-w-[200px]">
                  <div className="text-xs text-slate-700 dark:text-slate-300">
                    <strong>Causality Score:</strong> {(edge.causality_score * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-slate-700 dark:text-slate-300">
                    <strong>Correlation:</strong> {edge.correlation > 0 ? '+' : ''}{(edge.correlation * 100).toFixed(0)}%
                  </div>
                  {edge.granger_p_value !== null && edge.granger_p_value !== undefined && (
                    <div className="text-xs text-slate-700 dark:text-slate-300">
                      <strong>Granger p-value:</strong> {edge.granger_p_value.toFixed(3)}
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
                  {edge.evidence.map(e => e.replace(/_/g, ' ')).join(', ')}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Footer */}
      <Card>
        <CardContent className="pt-6">
          <div className="text-sm text-slate-600 dark:text-slate-400">
            <strong>Note:</strong> Causal relationships are inferred using statistical methods and
            should be interpreted carefully. Consult with healthcare professionals before making
            significant dietary changes.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
