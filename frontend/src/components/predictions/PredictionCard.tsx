'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { TrendingUp, TrendingDown, Activity, AlertCircle } from 'lucide-react';
import type { HealthPrediction } from '@/types';

interface PredictionCardProps {
  prediction: HealthPrediction;
}

export function PredictionCard({ prediction }: PredictionCardProps) {
  const getMetricIcon = () => {
    if (prediction.metric_name.includes('sleep')) {
      return '😴';
    } else if (prediction.metric_name.includes('readiness') || prediction.metric_name.includes('recovery')) {
      return '💪';
    } else if (prediction.metric_name.includes('hrv')) {
      return '❤️';
    }
    return '📊';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 dark:text-green-400';
    if (confidence >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-orange-600 dark:text-orange-400';
  };

  const getTrendIcon = () => {
    const currentValue = prediction.actual_value || 75; // Default baseline
    const predictedValue = prediction.predicted_value;

    if (predictedValue > currentValue) {
      return <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />;
    } else if (predictedValue < currentValue) {
      return <TrendingDown className="w-5 h-5 text-red-600 dark:text-red-400" />;
    }
    return <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) return 'Today';
    if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';

    const daysAhead = Math.round((date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    if (daysAhead <= 7) return `In ${daysAhead} days`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{getMetricIcon()}</span>
            <div>
              <CardTitle className="text-lg">
                {prediction.metric_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </CardTitle>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {formatDate(prediction.prediction_date)}
              </p>
            </div>
          </div>
          {getTrendIcon()}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Predicted Value */}
        <div className="text-center py-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
          <div className="text-4xl font-bold text-primary-600 dark:text-primary-400">
            {prediction.predicted_value.toFixed(0)}
          </div>
          <div className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Predicted Value
          </div>
          {prediction.prediction_range && (
            <div className="text-xs text-slate-500 dark:text-slate-500 mt-1">
              Range: {prediction.prediction_range.lower.toFixed(0)} - {prediction.prediction_range.upper.toFixed(0)}
            </div>
          )}
        </div>

        {/* Confidence */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-600 dark:text-slate-400">Confidence:</span>
          <span className={`font-semibold ${getConfidenceColor(prediction.confidence_score)}`}>
            {(prediction.confidence_score * 100).toFixed(0)}%
          </span>
        </div>

        {/* Contributing Factors */}
        {prediction.contributing_factors && prediction.contributing_factors.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Key Factors:
            </div>
            <div className="space-y-1">
              {prediction.contributing_factors.slice(0, 3).map((factor, idx) => (
                <div
                  key={idx}
                  className="text-xs text-slate-600 dark:text-slate-400 flex items-start gap-2"
                >
                  <span className="text-primary-500">•</span>
                  <span>{factor.factor}: {factor.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {prediction.recommendations && prediction.recommendations.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Recommendations:
            </div>
            <div className="space-y-1">
              {prediction.recommendations.slice(0, 2).map((rec, idx) => (
                <div
                  key={idx}
                  className="text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 p-2 rounded"
                >
                  {rec.action}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Model Info */}
        <div className="pt-3 border-t border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-500">
            <span>Model: {prediction.model_type}</span>
            <span className="capitalize">{prediction.status}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
