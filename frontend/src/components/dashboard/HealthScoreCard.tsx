'use client';

import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';
import { HealthScoreRing } from '@/components/ui/HealthScoreRing';
import { healthScoreService } from '@/services/healthScore';
import type { DailyHealthScore } from '@/types';

export function HealthScoreCard() {
  const [data, setData] = useState<DailyHealthScore | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    healthScoreService
      .getScore()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <Card className="mb-6">
        <CardContent className="py-8 flex items-center justify-center">
          <div className="animate-pulse text-slate-400">Loading health score...</div>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.score === null) {
    return null;
  }

  const TrendIcon =
    data.trend === 'up' ? TrendingUp : data.trend === 'down' ? TrendingDown : Minus;
  const trendColor =
    data.trend === 'up'
      ? 'text-green-500'
      : data.trend === 'down'
        ? 'text-red-500'
        : 'text-slate-400';

  return (
    <Card className="mb-6">
      <CardContent className="py-6">
        <div className="flex items-center gap-8">
          {/* Main score ring */}
          <div className="flex flex-col items-center">
            <HealthScoreRing score={Math.round(data.score)} size="lg" label="Health Score" />
            <div className={`flex items-center gap-1 mt-2 ${trendColor}`}>
              <TrendIcon className="w-4 h-4" />
              <span className="text-sm font-medium">
                {data.change_from_yesterday > 0 ? '+' : ''}
                {data.change_from_yesterday} from yesterday
              </span>
            </div>
          </div>

          {/* Breakdown rings */}
          <div className="flex gap-6">
            {data.breakdown.sleep && (
              <div className="flex flex-col items-center">
                <HealthScoreRing score={Math.round(data.breakdown.sleep.score)} size="sm" />
                <span className="text-xs text-slate-500 dark:text-slate-400 mt-1">Sleep</span>
                <span className="text-xs text-slate-400 dark:text-slate-500">40%</span>
              </div>
            )}
            {data.breakdown.readiness && (
              <div className="flex flex-col items-center">
                <HealthScoreRing score={Math.round(data.breakdown.readiness.score)} size="sm" />
                <span className="text-xs text-slate-500 dark:text-slate-400 mt-1">Readiness</span>
                <span className="text-xs text-slate-400 dark:text-slate-500">35%</span>
              </div>
            )}
            {data.breakdown.activity && (
              <div className="flex flex-col items-center">
                <HealthScoreRing score={Math.round(data.breakdown.activity.score)} size="sm" />
                <span className="text-xs text-slate-500 dark:text-slate-400 mt-1">Activity</span>
                <span className="text-xs text-slate-400 dark:text-slate-500">25%</span>
              </div>
            )}
          </div>

          {/* Date */}
          <div className="ml-auto text-right">
            <p className="text-xs text-slate-400 dark:text-slate-500">
              {data.date || 'Today'}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
