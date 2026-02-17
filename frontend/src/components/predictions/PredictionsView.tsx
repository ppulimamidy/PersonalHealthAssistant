'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { predictionsService } from '@/services/predictions';
import { useAuth } from '@/hooks/useAuth';
import { PredictionCard } from './PredictionCard';
import { RiskCard } from './RiskCard';
import { TrendCard } from './TrendCard';
import {
  TrendingUp,
  AlertCircle,
  Activity,
  Sparkles,
  RefreshCw
} from 'lucide-react';

type Tab = 'predictions' | 'risks' | 'trends';

export function PredictionsView() {
  const { user, isLoading: isAuthLoading } = useAuth(true);
  const [activeTab, setActiveTab] = useState<Tab>('predictions');
  const [days, setDays] = useState(30);

  // Fetch predictions
  const {
    data: predictions,
    isLoading: predictionsLoading,
    refetch: refetchPredictions
  } = useQuery({
    queryKey: ['predictions', days],
    queryFn: () => predictionsService.getPredictions(days),
    enabled: Boolean(user) && !isAuthLoading && activeTab === 'predictions',
  });

  // Fetch risks
  const {
    data: risks,
    isLoading: risksLoading,
    refetch: refetchRisks
  } = useQuery({
    queryKey: ['risks'],
    queryFn: () => predictionsService.getRisks(),
    enabled: Boolean(user) && !isAuthLoading && activeTab === 'risks',
  });

  // Fetch trends
  const {
    data: trends,
    isLoading: trendsLoading,
    refetch: refetchTrends
  } = useQuery({
    queryKey: ['trends', days],
    queryFn: () => predictionsService.getTrends(days),
    enabled: Boolean(user) && !isAuthLoading && activeTab === 'trends',
  });

  const handleRefresh = () => {
    if (activeTab === 'predictions') refetchPredictions();
    else if (activeTab === 'risks') refetchRisks();
    else if (activeTab === 'trends') refetchTrends();
  };

  if (isAuthLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-slate-500">Loading...</div>
      </div>
    );
  }

  const isLoading = predictionsLoading || risksLoading || trendsLoading;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Sparkles className="w-7 h-7 text-primary-600 dark:text-primary-400" />
          Predictive Health Intelligence
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          AI-powered predictions, risk assessments, and trend analysis for your health metrics
        </p>
      </div>

      {/* Data Quality Indicator */}
      {predictions && (
        <Card className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                <div>
                  <div className="text-sm font-medium text-slate-900 dark:text-slate-100">
                    Data Quality: {(predictions.data_quality_score * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-slate-600 dark:text-slate-400">
                    Based on {predictions.days_of_data} days of data
                  </div>
                </div>
              </div>
              <Button
                onClick={handleRefresh}
                variant="outline"
                size="sm"
                disabled={isLoading}
              >
                <RefreshCw className={`w-4 h-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-700">
        <button
          onClick={() => setActiveTab('predictions')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'predictions'
              ? 'border-primary-600 dark:border-primary-400 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Predictions
          </div>
        </button>
        <button
          onClick={() => setActiveTab('risks')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'risks'
              ? 'border-primary-600 dark:border-primary-400 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            Risk Assessment
          </div>
        </button>
        <button
          onClick={() => setActiveTab('trends')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'trends'
              ? 'border-primary-600 dark:border-primary-400 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Trends
          </div>
        </button>
      </div>

      {/* Period Selector (for predictions and trends) */}
      {(activeTab === 'predictions' || activeTab === 'trends') && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-600 dark:text-slate-400">Analysis Period:</span>
          <div className="flex gap-2">
            {[14, 30, 60, 90].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                  days === d
                    ? 'bg-primary-600 dark:bg-primary-400 text-white'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                {d} days
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 mx-auto mb-4 text-primary-600 dark:text-primary-400 animate-spin" />
            <p className="text-slate-600 dark:text-slate-400">
              Generating {activeTab}...
            </p>
          </div>
        </div>
      ) : (
        <div>
          {/* Predictions Tab */}
          {activeTab === 'predictions' && (
            <div>
              {predictions && predictions.predictions.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {predictions.predictions.map((prediction) => (
                    <PredictionCard key={prediction.id} prediction={prediction} />
                  ))}
                </div>
              ) : (
                <Card>
                  <CardContent className="py-12 text-center">
                    <TrendingUp className="w-16 h-16 mx-auto mb-4 text-slate-400 dark:text-slate-600" />
                    <p className="text-slate-600 dark:text-slate-400">
                      {predictions && predictions.days_of_data < 14
                        ? `Need at least 14 days of data to generate predictions. Currently have ${predictions.days_of_data} days.`
                        : 'No predictions available yet. Check back after collecting more health data.'}
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Risks Tab */}
          {activeTab === 'risks' && (
            <div>
              {risks && risks.risks.length > 0 ? (
                <div>
                  {/* Overall Risk Level Banner */}
                  <Card className={`mb-6 ${
                    risks.overall_risk_level === 'critical' ? 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800' :
                    risks.overall_risk_level === 'high' ? 'bg-orange-50 dark:bg-orange-900/10 border-orange-200 dark:border-orange-800' :
                    risks.overall_risk_level === 'moderate' ? 'bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-800' :
                    'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800'
                  }`}>
                    <CardContent className="py-4">
                      <div className="flex items-center gap-3">
                        <AlertCircle className="w-6 h-6" />
                        <div>
                          <div className="font-semibold text-slate-900 dark:text-slate-100">
                            Overall Risk Level: {risks.overall_risk_level.toUpperCase()}
                          </div>
                          <div className="text-sm text-slate-600 dark:text-slate-400">
                            {risks.risks.length} active risk {risks.risks.length === 1 ? 'assessment' : 'assessments'}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {risks.risks.map((risk) => (
                      <RiskCard key={risk.id} risk={risk} />
                    ))}
                  </div>
                </div>
              ) : (
                <Card>
                  <CardContent className="py-12 text-center">
                    <AlertCircle className="w-16 h-16 mx-auto mb-4 text-green-400 dark:text-green-600" />
                    <p className="text-slate-600 dark:text-slate-400">
                      No active health risks detected. Great job maintaining your health!
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Trends Tab */}
          {activeTab === 'trends' && (
            <div>
              {trends && trends.trends.length > 0 ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {trends.trends.map((trend) => (
                    <TrendCard key={trend.id} trend={trend} />
                  ))}
                </div>
              ) : (
                <Card>
                  <CardContent className="py-12 text-center">
                    <Activity className="w-16 h-16 mx-auto mb-4 text-slate-400 dark:text-slate-600" />
                    <p className="text-slate-600 dark:text-slate-400">
                      No trend data available. Collect at least 7 days of health data to see trends.
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
