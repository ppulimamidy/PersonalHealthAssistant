'use client';

import { SymptomTriggerPattern } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { AlertTriangle, CheckCircle, XCircle, TrendingUp } from 'lucide-react';

interface TriggerPatternCardProps {
  pattern: SymptomTriggerPattern;
  onValidate?: (validated: boolean) => void;
}

export function TriggerPatternCard({ pattern, onValidate }: TriggerPatternCardProps) {
  const getPatternTypeLabel = () => {
    switch (pattern.pattern_type) {
      case 'food_trigger':
        return 'Food Trigger';
      case 'medication_side_effect':
        return 'Medication Side Effect';
      case 'stress_trigger':
        return 'Stress Trigger';
      case 'sleep_trigger':
        return 'Sleep Trigger';
      case 'activity_trigger':
        return 'Activity Trigger';
      case 'weather_trigger':
        return 'Weather Trigger';
      case 'multi_factor':
        return 'Multi-Factor Pattern';
      default:
        return pattern.pattern_type;
    }
  };

  const getPatternColor = () => {
    if (pattern.pattern_strength >= 0.7) {
      return 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400';
    } else if (pattern.pattern_strength >= 0.5) {
      return 'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400';
    } else {
      return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400';
    }
  };

  return (
    <Card className="border-2 border-orange-200 dark:border-orange-800">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-orange-600 dark:text-orange-400" />
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {getPatternTypeLabel()}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${getPatternColor()}`}>
                {Math.round(pattern.pattern_strength * 100)}% strength
              </span>
            </div>
            <CardTitle className="text-lg font-semibold text-slate-900 dark:text-slate-100 capitalize">
              {pattern.symptom_type} Pattern
            </CardTitle>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Pattern Description */}
        <p className="text-sm text-slate-700 dark:text-slate-300">
          {pattern.pattern_description}
        </p>

        {/* Trigger Variables */}
        <div>
          <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Contributing Factors:
          </h4>
          <div className="space-y-2">
            {pattern.trigger_variables.map((tv, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2 bg-slate-50 dark:bg-slate-800/50 rounded"
              >
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                  <span className="text-sm text-slate-700 dark:text-slate-300">{tv.label}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-500 dark:text-slate-400">
                    r = {tv.coefficient.toFixed(2)}
                  </span>
                  <span className="text-slate-500 dark:text-slate-400">
                    p = {tv.p_value.toFixed(3)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        {pattern.recommendations.length > 0 && (
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-2">
              Recommendations:
            </p>
            <ul className="space-y-1">
              {pattern.recommendations.map((rec, idx) => (
                <li key={idx} className="text-sm text-blue-800 dark:text-blue-300 flex items-start gap-2">
                  <span className="text-blue-600 dark:text-blue-400 mt-1">•</span>
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Validation Stats */}
        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400">Observed</p>
            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {pattern.times_observed} times
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400">Validated</p>
            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {pattern.times_validated} / {pattern.times_observed}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400">Confidence</p>
            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {Math.round(pattern.confidence_score * 100)}%
            </p>
          </div>
        </div>

        {/* Validation Actions */}
        {onValidate && !pattern.user_acknowledged && (
          <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
              Have you experienced this pattern?
            </p>
            <div className="flex items-center gap-3">
              <button
                onClick={() => onValidate(true)}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                <CheckCircle className="w-4 h-4" />
                Yes, I've noticed this
              </button>
              <button
                onClick={() => onValidate(false)}
                className="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-700 dark:bg-slate-700 dark:hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                <XCircle className="w-4 h-4" />
                No, doesn't match
              </button>
            </div>
          </div>
        )}

        {pattern.user_acknowledged && (
          <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
            <CheckCircle className="w-4 h-4" />
            You've acknowledged this pattern
          </div>
        )}
      </CardContent>
    </Card>
  );
}
