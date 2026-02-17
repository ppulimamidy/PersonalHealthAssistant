'use client';

import { BiomarkerTrend } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { format } from 'date-fns';

interface BiomarkerTrendChartProps {
  trend: BiomarkerTrend;
}

export function BiomarkerTrendChart({ trend }: BiomarkerTrendChartProps) {
  const getTrendIcon = () => {
    switch (trend.trend_direction) {
      case 'improving':
        return <TrendingUp className="w-5 h-5 text-green-600" />;
      case 'declining':
        return <TrendingDown className="w-5 h-5 text-red-600" />;
      case 'stable':
        return <Minus className="w-5 h-5 text-slate-600" />;
    }
  };

  const getTrendColor = () => {
    switch (trend.trend_direction) {
      case 'improving':
        return 'text-green-600 dark:text-green-400';
      case 'declining':
        return 'text-red-600 dark:text-red-400';
      case 'stable':
        return 'text-slate-600 dark:text-slate-400';
    }
  };

  const chartData = trend.data_points.map((point) => ({
    date: format(new Date(point.test_date), 'MMM d'),
    fullDate: format(new Date(point.test_date), 'MMM d, yyyy'),
    value: point.value,
    status: point.status,
  }));

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal':
        return '#10b981'; // green
      case 'borderline':
        return '#f59e0b'; // yellow
      case 'abnormal':
        return '#f97316'; // orange
      case 'critical':
        return '#ef4444'; // red
      default:
        return '#64748b'; // slate
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {trend.biomarker_name}
            </CardTitle>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              {trend.biomarker_code} • {trend.unit}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {getTrendIcon()}
            <span className={`text-sm font-medium capitalize ${getTrendColor()}`}>
              {trend.trend_direction}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
              <XAxis
                dataKey="date"
                className="text-slate-600 dark:text-slate-400"
                tick={{ fontSize: 12 }}
              />
              <YAxis
                className="text-slate-600 dark:text-slate-400"
                tick={{ fontSize: 12 }}
                label={{ value: trend.unit, angle: -90, position: 'insideLeft', fontSize: 12 }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-white dark:bg-slate-800 p-3 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700">
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                          {data.fullDate}
                        </p>
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          Value: <span className="font-semibold">{data.value} {trend.unit}</span>
                        </p>
                        <p className="text-xs mt-1 capitalize" style={{ color: getStatusColor(data.status) }}>
                          Status: {data.status}
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={(props: any) => {
                  const { cx, cy, payload } = props;
                  return (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={4}
                      fill={getStatusColor(payload.status)}
                      stroke="white"
                      strokeWidth={2}
                    />
                  );
                }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Statistics */}
        {(trend.percent_change !== undefined || trend.statistical_significance !== undefined) && (
          <div className="mt-4 grid grid-cols-2 gap-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            {trend.percent_change !== undefined && (
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400">Change</p>
                <p className={`text-lg font-semibold ${trend.percent_change >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {trend.percent_change >= 0 ? '+' : ''}{trend.percent_change.toFixed(1)}%
                </p>
              </div>
            )}
            {trend.statistical_significance !== undefined && (
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400">Significance</p>
                <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  p = {trend.statistical_significance.toFixed(3)}
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
