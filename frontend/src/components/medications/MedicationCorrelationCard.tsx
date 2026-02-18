'use client';

import { MedicationVitalsCorrelation } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { TrendingUp, TrendingDown, Minus, Activity, AlertCircle } from 'lucide-react';

interface MedicationCorrelationCardProps {
  correlation: MedicationVitalsCorrelation;
}

export function MedicationCorrelationCard({ correlation }: MedicationCorrelationCardProps) {
  const getEffectIcon = () => {
    switch (correlation.effect_type) {
      case 'positive':
        return <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />;
      case 'negative':
        return <TrendingDown className="w-5 h-5 text-red-600 dark:text-red-400" />;
      case 'neutral':
        return <Minus className="w-5 h-5 text-slate-600 dark:text-slate-400" />;
    }
  };

  const getEffectColor = () => {
    switch (correlation.effect_type) {
      case 'positive':
        return 'text-green-600 dark:text-green-400';
      case 'negative':
        return 'text-red-600 dark:text-red-400';
      case 'neutral':
        return 'text-slate-600 dark:text-slate-400';
    }
  };

  const getMagnitudeColor = () => {
    switch (correlation.effect_magnitude) {
      case 'large':
        return 'bg-purple-100 text-purple-700 dark:bg-purple-900/20 dark:text-purple-400';
      case 'moderate':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400';
      case 'small':
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
      default:
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  const isSignificant = correlation.p_value < 0.05 && Math.abs(correlation.correlation_coefficient) >= 0.3;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-1">
              {correlation.medication_name} → {correlation.vital_label}
            </CardTitle>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {correlation.lag_hours}h after dose • {correlation.days_analyzed} days analyzed
            </p>
          </div>
          <div className="flex items-center gap-2">
            {getEffectIcon()}
            <span className={`text-sm font-medium capitalize ${getEffectColor()}`}>
              {correlation.effect_type}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Effect Description */}
        <p className="text-sm text-slate-700 dark:text-slate-300">
          {correlation.effect_description}
        </p>

        {/* Statistics */}
        <div className="grid grid-cols-3 gap-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Correlation</p>
            <p className={`text-lg font-semibold ${getEffectColor()}`}>
              {correlation.correlation_coefficient >= 0 ? '+' : ''}
              {correlation.correlation_coefficient.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Significance</p>
            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              p = {correlation.p_value.toFixed(3)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Sample Size</p>
            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              n = {correlation.sample_size}
            </p>
          </div>
        </div>

        {/* Effect Magnitude */}
        {correlation.effect_magnitude && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 dark:text-slate-400">Effect Size:</span>
            <span className={`text-xs px-2 py-1 rounded-full font-medium capitalize ${getMagnitudeColor()}`}>
              {correlation.effect_magnitude}
            </span>
          </div>
        )}

        {/* Statistical Significance Badge */}
        {isSignificant && (
          <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <Activity className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
            <p className="text-sm text-blue-900 dark:text-blue-200">
              <span className="font-semibold">Statistically significant</span> correlation detected
            </p>
          </div>
        )}

        {/* Clinical Significance */}
        {correlation.clinical_significance && (
          <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
            <p className="text-sm font-medium text-purple-900 dark:text-purple-200 mb-1">
              Clinical Note:
            </p>
            <p className="text-sm text-purple-800 dark:text-purple-300">
              {correlation.clinical_significance}
            </p>
          </div>
        )}

        {/* Recommendation */}
        {correlation.recommendation && (
          <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <p className="text-sm font-medium text-green-900 dark:text-green-200 mb-1">
              Recommendation:
            </p>
            <p className="text-sm text-green-800 dark:text-green-300">
              {correlation.recommendation}
            </p>
          </div>
        )}

        {/* Optimal Timing */}
        {correlation.optimal_timing_window && (
          <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
            <AlertCircle className="w-4 h-4" />
            <span>Optimal timing: {correlation.optimal_timing_window}</span>
          </div>
        )}

        {/* Data Quality */}
        <div className="pt-3 border-t border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
            <span>Data Quality:</span>
            <div className="flex items-center gap-2">
              <div className="w-24 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary-600 transition-all"
                  style={{ width: `${correlation.data_quality_score * 100}%` }}
                />
              </div>
              <span>{Math.round(correlation.data_quality_score * 100)}%</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
