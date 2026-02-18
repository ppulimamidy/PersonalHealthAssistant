'use client';

import { SpecialistInsight } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import {
  Brain,
  Moon,
  Utensils,
  Activity,
  Heart,
  Zap,
  Stethoscope,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

interface SpecialistInsightCardProps {
  insight: SpecialistInsight;
}

export function SpecialistInsightCard({ insight }: SpecialistInsightCardProps) {
  const getSpecialistIcon = () => {
    const iconClass = 'w-6 h-6';
    switch (insight.specialist_name.toLowerCase()) {
      case 'sleep':
        return <Moon className={iconClass} />;
      case 'nutrition':
        return <Utensils className={iconClass} />;
      case 'metabolic':
        return <Zap className={iconClass} />;
      case 'cardiovascular':
        return <Heart className={iconClass} />;
      case 'mental health':
        return <Brain className={iconClass} />;
      case 'movement':
        return <Activity className={iconClass} />;
      case 'endocrine':
        return <Stethoscope className={iconClass} />;
      default:
        return <Stethoscope className={iconClass} />;
    }
  };

  const getSpecialistColor = () => {
    switch (insight.specialist_name.toLowerCase()) {
      case 'sleep':
        return 'text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20';
      case 'nutrition':
        return 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20';
      case 'metabolic':
        return 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20';
      case 'cardiovascular':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20';
      case 'mental health':
        return 'text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-900/20';
      case 'movement':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20';
      case 'endocrine':
        return 'text-pink-600 dark:text-pink-400 bg-pink-50 dark:bg-pink-900/20';
      default:
        return 'text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900/20';
    }
  };

  const getConfidenceBadge = () => {
    const score = Math.round(insight.confidence_score * 100);
    if (score >= 80) {
      return 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400';
    } else if (score >= 60) {
      return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400';
    } else {
      return 'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400';
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${getSpecialistColor()}`}>
              {getSpecialistIcon()}
            </div>
            <div>
              <CardTitle className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                {insight.specialist_name} Specialist
              </CardTitle>
              <div className="flex items-center gap-2 mt-1">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${getConfidenceBadge()}`}>
                  {Math.round(insight.confidence_score * 100)}% confidence
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Data quality: {Math.round(insight.data_quality * 100)}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Findings */}
        {insight.findings.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              Key Findings
            </h4>
            <ul className="space-y-1.5">
              {insight.findings.map((finding, idx) => (
                <li key={idx} className="text-sm text-slate-600 dark:text-slate-400 flex items-start gap-2">
                  <span className="text-blue-500 dark:text-blue-400 mt-1">•</span>
                  <span>{finding}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Concerns */}
        {insight.concerns.length > 0 && (
          <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
            <h4 className="text-sm font-semibold text-orange-900 dark:text-orange-200 mb-2 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Areas of Concern
            </h4>
            <ul className="space-y-1.5">
              {insight.concerns.map((concern, idx) => (
                <li key={idx} className="text-sm text-orange-800 dark:text-orange-300 flex items-start gap-2">
                  <span className="text-orange-600 dark:text-orange-400 mt-1">•</span>
                  <span>{concern}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommendations */}
        {insight.recommendations.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Specialist Recommendations
            </h4>
            <div className="space-y-2">
              {insight.recommendations.slice(0, 3).map((rec, idx) => (
                <div
                  key={idx}
                  className="p-2.5 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700"
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                      {rec.action}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${
                      rec.priority === 'critical' ? 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400' :
                      rec.priority === 'high' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400' :
                      rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400' :
                      'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
                    }`}>
                      {rec.priority}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400">
                    {rec.rationale}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
