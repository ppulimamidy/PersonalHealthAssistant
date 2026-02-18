'use client';

import { CrossSystemPattern } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { GitBranch, RefreshCw, Zap, AlertTriangle } from 'lucide-react';

interface CrossSystemPatternCardProps {
  pattern: CrossSystemPattern;
}

export function CrossSystemPatternCard({ pattern }: CrossSystemPatternCardProps) {
  const getPatternIcon = () => {
    const iconClass = 'w-5 h-5';
    switch (pattern.pattern_type) {
      case 'causal_chain':
        return <GitBranch className={iconClass} />;
      case 'feedback_loop':
        return <RefreshCw className={iconClass} />;
      case 'synergistic_effect':
        return <Zap className={iconClass} />;
      case 'antagonistic_interaction':
        return <AlertTriangle className={iconClass} />;
      default:
        return <GitBranch className={iconClass} />;
    }
  };

  const getPatternColor = () => {
    switch (pattern.pattern_type) {
      case 'causal_chain':
        return 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800';
      case 'feedback_loop':
        return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800';
      case 'synergistic_effect':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
      case 'antagonistic_interaction':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
      default:
        return 'text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900/20 border-slate-200 dark:border-slate-800';
    }
  };

  const getStrengthBadge = () => {
    switch (pattern.strength) {
      case 'strong':
        return 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400';
      case 'moderate':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'weak':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400';
      default:
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  const getPatternLabel = () => {
    switch (pattern.pattern_type) {
      case 'causal_chain':
        return 'Causal Chain';
      case 'feedback_loop':
        return 'Feedback Loop';
      case 'synergistic_effect':
        return 'Synergistic Effect';
      case 'antagonistic_interaction':
        return 'Antagonistic Interaction';
      default:
        return pattern.pattern_type;
    }
  };

  return (
    <Card className={`border-2 ${getPatternColor()}`}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${getPatternColor()}`}>
              {getPatternIcon()}
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <CardTitle className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  {getPatternLabel()}
                </CardTitle>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${getStrengthBadge()}`}>
                  {pattern.strength}
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {pattern.systems_involved.map((system, idx) => (
                  <span
                    key={idx}
                    className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 capitalize"
                  >
                    {system}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
            Pattern Description
          </h4>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {pattern.pattern_description}
          </p>
        </div>

        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-1.5">
            Clinical Significance
          </h4>
          <p className="text-sm text-blue-800 dark:text-blue-300">
            {pattern.clinical_significance}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
