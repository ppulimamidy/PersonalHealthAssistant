'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react';
import type { HealthTrend } from '@/types';

interface TrendCardProps {
  trend: HealthTrend;
}

export function TrendCard({ trend }: TrendCardProps) {
  const getTrendIcon = () => {
    switch (trend.trend_type) {
      case 'improving':
        return <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />;
      case 'declining':
        return <TrendingDown className="w-5 h-5 text-red-600 dark:text-red-400" />;
      case 'stable':
        return <Minus className="w-5 h-5 text-blue-600 dark:text-blue-400" />;
      default:
        return <Activity className="w-5 h-5 text-orange-600 dark:text-orange-400" />;
    }
  };

  const getTrendColor = () => {
    switch (trend.trend_type) {
      case 'improving':
        return 'text-green-600 dark:text-green-400';
      case 'declining':
        return 'text-red-600 dark:text-red-400';
      case 'stable':
        return 'text-blue-600 dark:text-blue-400';
      default:
        return 'text-orange-600 dark:text-orange-400';
    }
  };

  const getSignificanceBadge = () => {
    const colors = {
      clinically_significant: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
      notable: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300',
      minor: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
      noise: 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400',
    };

    return (
      <span className={`text-xs px-2 py-1 rounded-full font-medium ${colors[trend.significance as keyof typeof colors] || colors.noise}`}>
        {trend.significance.replace(/_/g, ' ')}
      </span>
    );
  };

  const getMetricEmoji = () => {
    if (trend.metric_name.includes('sleep')) return '😴';
    if (trend.metric_name.includes('readiness')) return '💪';
    if (trend.metric_name.includes('hrv')) return '❤️';
    if (trend.metric_name.includes('heart') || trend.metric_name.includes('resting')) return '💓';
    if (trend.metric_name.includes('steps')) return '🚶';
    return '📊';
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{getMetricEmoji()}</span>
            <div>
              <CardTitle className="text-lg">
                {trend.metric_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </CardTitle>
              <div className="flex items-center gap-2 mt-1">
                {getSignificanceBadge()}
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {trend.window_days} days
                </span>
              </div>
            </div>
          </div>
          {getTrendIcon()}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Interpretation */}
        <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded-lg">
          <p className="text-sm text-slate-700 dark:text-slate-300">
            {trend.interpretation}
          </p>
        </div>

        {/* Statistics Grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-700">
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Average</div>
            <div className="text-lg font-bold text-slate-900 dark:text-slate-100">
              {trend.average_value.toFixed(1)}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-700">
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Change</div>
            <div className={`text-lg font-bold ${getTrendColor()}`}>
              {trend.percent_change > 0 ? '+' : ''}{trend.percent_change.toFixed(1)}%
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-700">
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Trend Strength</div>
            <div className="text-lg font-bold text-slate-900 dark:text-slate-100">
              {(trend.r_squared * 100).toFixed(0)}%
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-700">
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Variability</div>
            <div className="text-lg font-bold text-slate-900 dark:text-slate-100">
              ±{trend.std_deviation.toFixed(1)}
            </div>
          </div>
        </div>

        {/* Forecasts */}
        {(trend.forecast_7d || trend.forecast_14d || trend.forecast_30d) && (
          <div className="space-y-2">
            <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Forecasts:
            </div>
            <div className="grid grid-cols-3 gap-2">
              {trend.forecast_7d && (
                <div className="text-center p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
                  <div className="text-xs text-slate-600 dark:text-slate-400">7 days</div>
                  <div className="text-sm font-bold text-blue-700 dark:text-blue-300">
                    {trend.forecast_7d.toFixed(0)}
                  </div>
                </div>
              )}
              {trend.forecast_14d && (
                <div className="text-center p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
                  <div className="text-xs text-slate-600 dark:text-slate-400">14 days</div>
                  <div className="text-sm font-bold text-blue-700 dark:text-blue-300">
                    {trend.forecast_14d.toFixed(0)}
                  </div>
                </div>
              )}
              {trend.forecast_30d && (
                <div className="text-center p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
                  <div className="text-xs text-slate-600 dark:text-slate-400">30 days</div>
                  <div className="text-sm font-bold text-blue-700 dark:text-blue-300">
                    {trend.forecast_30d.toFixed(0)}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Anomalies */}
        {trend.anomalies && trend.anomalies.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Anomalies Detected: {trend.anomalies.length}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400">
              Unusual data points identified in the trend
            </div>
          </div>
        )}

        {/* Detected Patterns */}
        {trend.detected_patterns && trend.detected_patterns.length > 0 && (
          <div className="space-y-1">
            <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Patterns:
            </div>
            <div className="flex flex-wrap gap-1">
              {trend.detected_patterns.map((pattern, idx) => (
                <span
                  key={idx}
                  className="text-xs px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded"
                >
                  {pattern.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Meta Info */}
        <div className="pt-3 border-t border-slate-200 dark:border-slate-700">
          <div className="text-xs text-slate-500 dark:text-slate-500">
            Analysis: {new Date(trend.analysis_start_date).toLocaleDateString()} - {new Date(trend.analysis_end_date).toLocaleDateString()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
