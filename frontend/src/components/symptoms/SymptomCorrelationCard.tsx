'use client';

import { SymptomCorrelation } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { TrendingUp, TrendingDown, AlertTriangle, Utensils, Activity } from 'lucide-react';

interface SymptomCorrelationCardProps {
  correlation: SymptomCorrelation;
}

export function SymptomCorrelationCard({ correlation }: SymptomCorrelationCardProps) {
  const getEffectIcon = () => {
    switch (correlation.effect_type) {
      case 'positive':
        return <TrendingUp className="w-5 h-5 text-red-600 dark:text-red-400" />;
      case 'negative':
        return <TrendingDown className="w-5 h-5 text-green-600 dark:text-green-400" />;
      case 'neutral':
        return null;
    }
  };

  const getEffectColor = () => {
    // For symptoms, positive correlation = worse (symptom increases with variable)
    switch (correlation.effect_type) {
      case 'positive':
        return 'text-red-600 dark:text-red-400';
      case 'negative':
        return 'text-green-600 dark:text-green-400';
      case 'neutral':
        return 'text-slate-600 dark:text-slate-400';
    }
  };

  const getTypeIcon = () => {
    switch (correlation.correlation_type) {
      case 'symptom_nutrition':
        return <Utensils className="w-5 h-5 text-orange-600 dark:text-orange-400" />;
      case 'symptom_oura':
        return <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />;
      default:
        return null;
    }
  };

  const getTypeLabel = () => {
    switch (correlation.correlation_type) {
      case 'symptom_nutrition':
        return 'Nutrition';
      case 'symptom_oura':
        return 'Vitals';
      case 'symptom_medication':
        return 'Medication';
      default:
        return 'Other';
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
            <div className="flex items-center gap-2 mb-2">
              {getTypeIcon()}
              <span className="text-xs text-slate-500 dark:text-slate-400 capitalize">
                {getTypeLabel()} • {correlation.lag_days === 0 ? 'Same day' : `${correlation.lag_days} day lag`}
              </span>
            </div>
            <CardTitle className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {correlation.correlated_variable_label} → {correlation.symptom_type}
            </CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {getEffectIcon()}
            {correlation.trigger_identified && (
              <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Effect Description */}
        <p className="text-sm text-slate-700 dark:text-slate-300">
          {correlation.effect_description}
        </p>

        {/* Trigger Alert */}
        {correlation.trigger_identified && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-sm font-semibold text-red-900 dark:text-red-200 mb-1">
                  Potential Trigger Identified
                </p>
                <p className="text-sm text-red-800 dark:text-red-300">
                  Confidence: {correlation.trigger_confidence ? Math.round(correlation.trigger_confidence * 100) : 0}%
                </p>
              </div>
            </div>
          </div>
        )}

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
            {isSignificant && (
              <span className="text-xs px-2 py-1 rounded-full font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400">
                Statistically Significant
              </span>
            )}
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
