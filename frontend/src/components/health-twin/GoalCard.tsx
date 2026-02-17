'use client';

import { HealthTwinGoal } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Target, TrendingUp, CheckCircle, Circle } from 'lucide-react';

interface GoalCardProps {
  goal: HealthTwinGoal;
  onUpdateMilestone?: (milestoneIndex: number, completed: boolean) => void;
}

export function GoalCard({ goal, onUpdateMilestone }: GoalCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400';
      case 'achieved':
        return 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400';
      case 'abandoned':
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
      default:
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  const progress = ((goal.current_value / goal.target_value) * 100).toFixed(0);
  const completedMilestones = goal.milestones.filter(m => m.completed).length;
  const totalMilestones = goal.milestones.length;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${getStatusColor(goal.status)}`}>
                {goal.status}
              </span>
            </div>
            <CardTitle className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {goal.goal_description}
            </CardTitle>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 capitalize">
              {goal.goal_type.replace(/_/g, ' ')}
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-600 dark:text-slate-400">Progress</span>
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              {progress}%
            </span>
          </div>
          <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-600 transition-all duration-300"
              style={{ width: `${Math.min(parseFloat(progress), 100)}%` }}
            />
          </div>
          <div className="flex items-center justify-between mt-2 text-xs text-slate-500 dark:text-slate-400">
            <span>Current: {goal.current_value.toFixed(1)}</span>
            <span>Target: {goal.target_value.toFixed(1)}</span>
          </div>
        </div>

        {/* Success Probability */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">Success Probability</p>
            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {Math.round(goal.success_probability * 100)}%
            </p>
          </div>
          {goal.estimated_timeline_days && (
            <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
              <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">Estimated Timeline</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                {goal.estimated_timeline_days} days
              </p>
            </div>
          )}
        </div>

        {/* Milestones */}
        {goal.milestones.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
                Milestones
              </h4>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {completedMilestones}/{totalMilestones} completed
              </span>
            </div>
            <div className="space-y-2">
              {goal.milestones.map((milestone, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-2 hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded transition-colors"
                >
                  <button
                    onClick={() => onUpdateMilestone?.(idx, !milestone.completed)}
                    className="mt-0.5 flex-shrink-0"
                  >
                    {milestone.completed ? (
                      <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                    ) : (
                      <Circle className="w-5 h-5 text-slate-400 dark:text-slate-600" />
                    )}
                  </button>
                  <div className="flex-1">
                    <p className={`text-sm ${milestone.completed ? 'line-through text-slate-500 dark:text-slate-400' : 'text-slate-700 dark:text-slate-300'}`}>
                      {milestone.milestone}
                    </p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-slate-500 dark:text-slate-400">
                      <span>Target: {milestone.target_value}</span>
                      {milestone.target_date && (
                        <span>• {new Date(milestone.target_date).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Strategies */}
        {goal.strategies.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-primary-600" />
              Strategies
            </h4>
            <ul className="space-y-1">
              {goal.strategies.map((strategy, idx) => (
                <li key={idx} className="text-sm text-slate-600 dark:text-slate-400 flex items-start gap-2">
                  <span className="text-primary-600 dark:text-primary-400 mt-1">•</span>
                  {strategy}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
