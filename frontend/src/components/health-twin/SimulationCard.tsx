'use client';

import { HealthTwinSimulation } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Brain, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

interface SimulationCardProps {
  simulation: HealthTwinSimulation;
  onClick?: () => void;
}

export function SimulationCard({ simulation, onClick }: SimulationCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400';
      case 'completed':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400';
      case 'draft':
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
      default:
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'lifestyle_change':
        return 'Lifestyle Change';
      case 'intervention':
        return 'Intervention';
      case 'risk_scenario':
        return 'Risk Scenario';
      case 'goal_projection':
        return 'Goal Projection';
      default:
        return type;
    }
  };

  const chartData = simulation.timeline_predictions.map((pred) => ({
    days: pred.days_from_now,
    healthAge: pred.predicted_health_age,
    ...pred.predicted_scores,
  }));

  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={onClick}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Brain className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {getTypeLabel(simulation.simulation_type)}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${getStatusColor(simulation.status)}`}>
                {simulation.status}
              </span>
            </div>
            <CardTitle className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {simulation.simulation_name}
            </CardTitle>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-500 dark:text-slate-400">Confidence</p>
            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {Math.round(simulation.confidence_score * 100)}%
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Timeline Chart */}
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
              <XAxis
                dataKey="days"
                className="text-slate-600 dark:text-slate-400"
                tick={{ fontSize: 12 }}
                label={{ value: 'Days from now', position: 'insideBottom', offset: -5, fontSize: 12 }}
              />
              <YAxis
                className="text-slate-600 dark:text-slate-400"
                tick={{ fontSize: 12 }}
                label={{ value: 'Health Age', angle: -90, position: 'insideLeft', fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line
                type="monotone"
                dataKey="healthAge"
                stroke="#3b82f6"
                strokeWidth={2}
                name="Health Age"
                dot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Predicted Outcomes */}
        <div>
          <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Predicted Outcomes
          </h4>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(simulation.predicted_outcomes).slice(0, 4).map(([key, value]) => (
              <div
                key={key}
                className="p-2 bg-slate-50 dark:bg-slate-800/50 rounded text-sm"
              >
                <p className="text-xs text-slate-500 dark:text-slate-400 capitalize">
                  {key.replace(/_/g, ' ')}
                </p>
                <p className="font-semibold text-slate-900 dark:text-slate-100">
                  {typeof value === 'number' ? value.toFixed(1) : value}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        {simulation.recommendations.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-600" />
              Recommendations
            </h4>
            <ul className="space-y-1">
              {simulation.recommendations.slice(0, 3).map((rec, idx) => (
                <li key={idx} className="text-sm text-slate-600 dark:text-slate-400 flex items-start gap-2">
                  <span className="text-primary-600 dark:text-primary-400 mt-1">•</span>
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Warnings */}
        {simulation.warnings.length > 0 && (
          <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-600 dark:text-yellow-400 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-900 dark:text-yellow-200 mb-1">
                  Warnings
                </p>
                <ul className="space-y-1">
                  {simulation.warnings.map((warning, idx) => (
                    <li key={idx} className="text-xs text-yellow-800 dark:text-yellow-300">
                      {warning}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
