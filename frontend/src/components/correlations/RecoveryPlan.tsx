'use client';

import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { Apple, AlertCircle, Calendar, Target, XCircle } from 'lucide-react';
import { recommendationsService } from '@/services/recommendations';
import type { RecoveryPlan as RecoveryPlanType } from '@/types';

export function RecoveryPlanView() {
  const { data: plan, isLoading, error } = useQuery<RecoveryPlanType>({
    queryKey: ['recovery-plan'],
    queryFn: () => recommendationsService.getRecoveryPlan(),
    staleTime: 1000 * 60 * 30,
  });

  if (isLoading) {
    return (
      <Card className="animate-pulse">
        <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4" />
        <div className="space-y-3">
          <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-full" />
          <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-2/3" />
        </div>
      </Card>
    );
  }

  if (error || !plan) {
    return (
      <Card>
        <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
          <AlertCircle className="w-5 h-5" />
          <span className="text-sm">Unable to generate recovery plan. Log more data to get started.</span>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
          {plan.title}
        </h3>
        <p className="text-sm text-slate-600 dark:text-slate-300">{plan.overview}</p>
      </Card>

      {/* Daily Plan */}
      {plan.daily_plan.length > 0 && (
        <Card>
          <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-primary-500" />
            Daily Plan
          </h4>
          <div className="space-y-3">
            {plan.daily_plan.map((day, i) => (
              <div key={i} className="flex gap-3 items-start">
                <div className="shrink-0 w-16 text-xs font-semibold text-primary-600 dark:text-primary-400 pt-0.5">
                  {day.day}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{day.focus}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{day.meals}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Focus areas + foods */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Foods to emphasize */}
        {plan.foods_to_emphasize.length > 0 && (
          <Card>
            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3 flex items-center gap-2">
              <Apple className="w-4 h-4 text-emerald-500" />
              Foods to Emphasize
            </h4>
            <div className="space-y-2">
              {plan.foods_to_emphasize.map((f, i) => (
                <div key={i} className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                  <div>
                    <span className="text-sm text-slate-800 dark:text-slate-200">{f.name}</span>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{f.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Foods to limit */}
        {plan.foods_to_limit.length > 0 && (
          <Card>
            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3 flex items-center gap-2">
              <XCircle className="w-4 h-4 text-red-500" />
              Foods &amp; Habits to Limit
            </h4>
            <div className="space-y-2">
              {plan.foods_to_limit.map((item, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
                  <span className="text-sm text-slate-700 dark:text-slate-300">{item}</span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Key focus areas */}
      {plan.key_focus_areas.length > 0 && (
        <Card>
          <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3 flex items-center gap-2">
            <Target className="w-4 h-4 text-primary-500" />
            Key Focus Areas
          </h4>
          <div className="flex flex-wrap gap-2">
            {plan.key_focus_areas.map((area, i) => (
              <span
                key={i}
                className="text-xs px-2.5 py-1 rounded-full bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400"
              >
                {area}
              </span>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
