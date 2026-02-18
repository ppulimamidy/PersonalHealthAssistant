'use client';

import { UserMedicationAlert } from '@/types';
import { Card, CardContent } from '@/components/ui/Card';
import { AlertTriangle, AlertCircle, Info, CheckCircle, X } from 'lucide-react';

interface InteractionAlertCardProps {
  alert: UserMedicationAlert;
  onAcknowledge?: () => void;
  onDismiss?: () => void;
}

export function InteractionAlertCard({
  alert,
  onAcknowledge,
  onDismiss,
}: InteractionAlertCardProps) {
  const getSeverityIcon = () => {
    switch (alert.severity) {
      case 'critical':
        return <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400" />;
      case 'high':
        return <AlertTriangle className="w-6 h-6 text-orange-600 dark:text-orange-400" />;
      case 'moderate':
        return <AlertTriangle className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />;
      case 'low':
        return <Info className="w-6 h-6 text-blue-600 dark:text-blue-400" />;
    }
  };

  const getSeverityColor = () => {
    switch (alert.severity) {
      case 'critical':
        return 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800';
      case 'high':
        return 'bg-orange-50 border-orange-200 dark:bg-orange-900/20 dark:border-orange-800';
      case 'moderate':
        return 'bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800';
      case 'low':
        return 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800';
    }
  };

  const getSeverityTextColor = () => {
    switch (alert.severity) {
      case 'critical':
        return 'text-red-900 dark:text-red-100';
      case 'high':
        return 'text-orange-900 dark:text-orange-100';
      case 'moderate':
        return 'text-yellow-900 dark:text-yellow-100';
      case 'low':
        return 'text-blue-900 dark:text-blue-100';
    }
  };

  const getSeverityBadgeColor = () => {
    switch (alert.severity) {
      case 'critical':
        return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300';
      case 'high':
        return 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300';
      case 'moderate':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300';
      case 'low':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300';
    }
  };

  if (alert.is_dismissed) return null;

  return (
    <Card className={`border-2 ${getSeverityColor()} ${alert.is_acknowledged ? 'opacity-60' : ''}`}>
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className="flex-shrink-0 mt-1">{getSeverityIcon()}</div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4 mb-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-semibold uppercase ${getSeverityBadgeColor()}`}
                  >
                    {alert.severity}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-400 capitalize">
                    {alert.alert_type.replace(/_/g, ' ')}
                  </span>
                </div>
                <h3 className={`text-lg font-semibold ${getSeverityTextColor()}`}>
                  {alert.title}
                </h3>
              </div>

              {/* Dismiss button */}
              {onDismiss && !alert.is_acknowledged && (
                <button
                  onClick={onDismiss}
                  className="flex-shrink-0 p-1 hover:bg-white/50 dark:hover:bg-slate-700/50 rounded transition-colors"
                  aria-label="Dismiss"
                >
                  <X className="w-5 h-5 text-slate-500 dark:text-slate-400" />
                </button>
              )}
            </div>

            <p className={`text-sm ${getSeverityTextColor()} mb-3`}>
              {alert.description}
            </p>

            {/* Recommendation */}
            <div className={`p-3 rounded-lg ${alert.severity === 'critical' ? 'bg-white/50 dark:bg-slate-800/50' : 'bg-white/30 dark:bg-slate-800/30'} mb-3`}>
              <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-1">
                Recommendation:
              </p>
              <p className="text-sm text-slate-700 dark:text-slate-300">
                {alert.recommendation}
              </p>
            </div>

            {/* Affected substances */}
            {alert.medication_name && alert.interacts_with && (
              <div className="flex items-center gap-2 flex-wrap mb-3">
                <span className="text-xs px-2 py-1 rounded bg-white/50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300">
                  {alert.medication_name}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">+</span>
                <span className="text-xs px-2 py-1 rounded bg-white/50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300">
                  {alert.interacts_with}
                </span>
              </div>
            )}

            {/* Actions */}
            {!alert.is_acknowledged && onAcknowledge && (
              <button
                onClick={onAcknowledge}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                  alert.severity === 'critical'
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : alert.severity === 'high'
                    ? 'bg-orange-600 hover:bg-orange-700 text-white'
                    : 'bg-slate-600 hover:bg-slate-700 dark:bg-slate-700 dark:hover:bg-slate-600 text-white'
                }`}
              >
                <CheckCircle className="w-4 h-4" />
                I Understand
              </button>
            )}

            {alert.is_acknowledged && (
              <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                <CheckCircle className="w-4 h-4" />
                Acknowledged
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
