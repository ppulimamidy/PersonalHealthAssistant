'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { AlertTriangle, AlertCircle, Info, CheckCircle } from 'lucide-react';
import type { HealthRiskAssessment } from '@/types';

interface RiskCardProps {
  risk: HealthRiskAssessment;
}

export function RiskCard({ risk }: RiskCardProps) {
  const getRiskIcon = () => {
    switch (risk.risk_level) {
      case 'critical':
        return <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />;
      case 'high':
        return <AlertCircle className="w-6 h-6 text-orange-600 dark:text-orange-400" />;
      case 'moderate':
        return <Info className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />;
      default:
        return <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />;
    }
  };

  const getRiskColor = () => {
    switch (risk.risk_level) {
      case 'critical':
        return 'border-red-500 bg-red-50 dark:bg-red-900/10';
      case 'high':
        return 'border-orange-500 bg-orange-50 dark:bg-orange-900/10';
      case 'moderate':
        return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10';
      default:
        return 'border-green-500 bg-green-50 dark:bg-green-900/10';
    }
  };

  const getRiskBadgeColor = () => {
    switch (risk.risk_level) {
      case 'critical':
        return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200';
      case 'high':
        return 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-200';
      case 'moderate':
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200';
      default:
        return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200';
    }
  };

  const getCategoryEmoji = () => {
    switch (risk.risk_category) {
      case 'cardiovascular':
        return '❤️';
      case 'metabolic':
        return '🔥';
      case 'mental_health':
        return '🧠';
      case 'sleep':
        return '😴';
      case 'recovery':
        return '💪';
      default:
        return '⚕️';
    }
  };

  return (
    <Card className={`border-l-4 ${getRiskColor()} transition-all hover:shadow-lg`}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{getCategoryEmoji()}</span>
            <div>
              <CardTitle className="text-lg">
                {risk.risk_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </CardTitle>
              <div className="flex items-center gap-2 mt-1">
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${getRiskBadgeColor()}`}>
                  {risk.risk_level.toUpperCase()}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {(risk.risk_score * 100).toFixed(0)}% risk score
                </span>
              </div>
            </div>
          </div>
          {getRiskIcon()}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Contributing Factors */}
        {risk.contributing_factors && risk.contributing_factors.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              Risk Factors:
            </div>
            <div className="space-y-2">
              {risk.contributing_factors.map((factor, idx) => (
                <div key={idx} className="bg-white dark:bg-slate-800 p-3 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="flex items-start justify-between mb-1">
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                      {factor.factor}
                    </span>
                    <span className="text-xs text-orange-600 dark:text-orange-400 font-semibold">
                      {(factor.impact_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400">
                    {factor.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {risk.recommendations && risk.recommendations.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              Recommended Actions:
            </div>
            <div className="space-y-2">
              {risk.recommendations.map((rec, idx) => (
                <div
                  key={idx}
                  className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-3 rounded-lg"
                >
                  <div className="flex items-start gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                      rec.priority === 'high' || rec.priority === 'critical'
                        ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                        : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                    }`}>
                      {rec.priority}
                    </span>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-slate-900 dark:text-slate-100">
                        {rec.action}
                      </div>
                      {rec.rationale && (
                        <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                          {rec.rationale}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Early Warning Signs */}
        {risk.early_warning_signs && risk.early_warning_signs.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              Watch For:
            </div>
            <div className="grid grid-cols-1 gap-1">
              {risk.early_warning_signs.slice(0, 4).map((sign, idx) => (
                <div
                  key={idx}
                  className="text-xs text-slate-600 dark:text-slate-400 flex items-center gap-2"
                >
                  <AlertCircle className="w-3 h-3 text-orange-500" />
                  {sign}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Meta Info */}
        <div className="pt-3 border-t border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-500">
            <span>Confidence: {(risk.confidence_score * 100).toFixed(0)}%</span>
            <span>{new Date(risk.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
