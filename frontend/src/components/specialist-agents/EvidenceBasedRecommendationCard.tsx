'use client';

import { EvidenceBasedRecommendation } from '@/types';
import { Card, CardContent } from '@/components/ui/Card';
import { Target, TrendingUp, BookOpen, Gauge } from 'lucide-react';

interface EvidenceBasedRecommendationCardProps {
  recommendation: EvidenceBasedRecommendation;
  rank: number;
}

export function EvidenceBasedRecommendationCard({
  recommendation,
  rank,
}: EvidenceBasedRecommendationCardProps) {
  const getPriorityColor = () => {
    switch (recommendation.priority) {
      case 'critical':
        return 'border-red-500 bg-red-50 dark:bg-red-900/20';
      case 'high':
        return 'border-orange-500 bg-orange-50 dark:bg-orange-900/20';
      case 'medium':
        return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
      case 'low':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-900/20';
      default:
        return 'border-slate-500 bg-slate-50 dark:bg-slate-900/20';
    }
  };

  const getEvidenceBadge = () => {
    switch (recommendation.evidence_level) {
      case 'strong':
        return 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400';
      case 'moderate':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400';
      case 'limited':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'theoretical':
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
      default:
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  const getDifficultyColor = () => {
    switch (recommendation.implementation_difficulty) {
      case 'easy':
        return 'text-green-600 dark:text-green-400';
      case 'moderate':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'difficult':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-slate-600 dark:text-slate-400';
    }
  };

  const getImpactWidth = () => {
    return `${recommendation.estimated_impact * 100}%`;
  };

  return (
    <Card className={`border-l-4 ${getPriorityColor()}`}>
      <CardContent className="pt-4 space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 flex-1">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-600 text-white font-bold text-sm flex-shrink-0">
              {rank}
            </div>
            <div className="flex-1">
              <h4 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-1">
                {recommendation.action}
              </h4>
              <div className="flex flex-wrap items-center gap-2">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${
                  recommendation.priority === 'critical' ? 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400' :
                  recommendation.priority === 'high' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400' :
                  recommendation.priority === 'medium' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400' :
                  'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
                }`}>
                  {recommendation.priority} priority
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${getEvidenceBadge()}`}>
                  {recommendation.evidence_level} evidence
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Rationale */}
        <div className="pl-11">
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
            {recommendation.rationale}
          </p>

          {/* Expected Benefit */}
          <div className="flex items-start gap-2 p-2.5 bg-green-50 dark:bg-green-900/20 rounded-lg mb-3">
            <Target className="w-4 h-4 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs font-medium text-green-900 dark:text-green-200 mb-0.5">
                Expected Benefit
              </p>
              <p className="text-xs text-green-800 dark:text-green-300">
                {recommendation.expected_benefit}
              </p>
            </div>
          </div>

          {/* Impact & Difficulty */}
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div>
              <div className="flex items-center gap-1.5 mb-1.5">
                <TrendingUp className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                  Estimated Impact
                </span>
              </div>
              <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary-600 transition-all"
                  style={{ width: getImpactWidth() }}
                />
              </div>
              <span className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {Math.round(recommendation.estimated_impact * 100)}%
              </span>
            </div>
            <div>
              <div className="flex items-center gap-1.5 mb-1.5">
                <Gauge className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                  Difficulty
                </span>
              </div>
              <p className={`text-sm font-semibold capitalize ${getDifficultyColor()}`}>
                {recommendation.implementation_difficulty}
              </p>
            </div>
          </div>

          {/* Citations */}
          {recommendation.citations.length > 0 && (
            <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-1.5 mb-1.5">
                <BookOpen className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                  Research Citations
                </span>
              </div>
              <ul className="space-y-1">
                {recommendation.citations.map((citation, idx) => (
                  <li key={idx} className="text-xs text-slate-600 dark:text-slate-400 flex items-start gap-1.5">
                    <span className="text-slate-400 dark:text-slate-500 flex-shrink-0">[{idx + 1}]</span>
                    <span className="italic">{citation}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
