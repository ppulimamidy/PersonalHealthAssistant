'use client';

import { HealthTwinProfile as HealthTwinProfileType } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { TrendingUp, TrendingDown, Minus, Heart, Activity, Zap } from 'lucide-react';

interface HealthTwinProfileProps {
  profile: HealthTwinProfileType;
  onRefresh: () => void;
  refreshing: boolean;
}

export function HealthTwinProfileCard({ profile, onRefresh, refreshing }: HealthTwinProfileProps) {
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />;
      case 'declining':
        return <TrendingDown className="w-5 h-5 text-red-600 dark:text-red-400" />;
      case 'stable':
        return <Minus className="w-5 h-5 text-slate-600 dark:text-slate-400" />;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving':
        return 'text-green-600 dark:text-green-400';
      case 'declining':
        return 'text-red-600 dark:text-red-400';
      case 'stable':
        return 'text-slate-600 dark:text-slate-400';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 dark:text-green-400';
    if (score >= 60) return 'text-yellow-600 dark:text-yellow-400';
    if (score >= 40) return 'text-orange-600 dark:text-orange-400';
    return 'text-red-600 dark:text-red-400';
  };

  const ageDifference = profile.health_age - profile.chronological_age;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            Your Health Twin Profile
          </CardTitle>
          <button
            onClick={onRefresh}
            disabled={refreshing}
            className="px-3 py-1 text-sm text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors disabled:opacity-50"
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Health Age */}
        <div className="p-6 bg-gradient-to-br from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Health Age</p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold text-slate-900 dark:text-slate-100">
                  {Math.round(profile.health_age)}
                </span>
                <span className="text-lg text-slate-500 dark:text-slate-400">years</span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Chronological Age</p>
              <p className="text-2xl font-semibold text-slate-700 dark:text-slate-300">
                {profile.chronological_age}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {getTrendIcon(profile.health_age_trend)}
            <span className={`text-sm font-medium capitalize ${getTrendColor(profile.health_age_trend)}`}>
              {profile.health_age_trend}
            </span>
            {ageDifference !== 0 && (
              <span className={`text-sm ${ageDifference > 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
                ({ageDifference > 0 ? '+' : ''}{ageDifference.toFixed(1)} years)
              </span>
            )}
          </div>
        </div>

        {/* Core Scores */}
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Heart className="w-5 h-5 text-red-500" />
              <p className="text-xs text-slate-600 dark:text-slate-400">Resilience</p>
            </div>
            <p className={`text-2xl font-bold ${getScoreColor(profile.resilience_score)}`}>
              {Math.round(profile.resilience_score)}
            </p>
          </div>

          <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-5 h-5 text-yellow-500" />
              <p className="text-xs text-slate-600 dark:text-slate-400">Adaptability</p>
            </div>
            <p className={`text-2xl font-bold ${getScoreColor(profile.adaptability_score)}`}>
              {Math.round(profile.adaptability_score)}
            </p>
          </div>

          <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-5 h-5 text-blue-500" />
              <p className="text-xs text-slate-600 dark:text-slate-400">Recovery</p>
            </div>
            <p className={`text-2xl font-bold ${getScoreColor(profile.recovery_capacity)}`}>
              {Math.round(profile.recovery_capacity)}
            </p>
          </div>
        </div>

        {/* Age Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Metabolic Age</p>
            <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
              {Math.round(profile.metabolic_age)} years
            </p>
          </div>
          <div className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Biological Age Factors</p>
            <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
              {Object.keys(profile.biological_age_factors).length} tracked
            </p>
          </div>
        </div>

        {/* Recent Changes */}
        {profile.recent_changes && profile.recent_changes.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
              Recent Changes
            </h4>
            <div className="space-y-2">
              {profile.recent_changes.slice(0, 5).map((change, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                      {change.metric}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {new Date(change.date).toLocaleDateString()}
                    </p>
                  </div>
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    {change.change}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
