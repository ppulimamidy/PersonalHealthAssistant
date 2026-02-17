'use client';

import { useState, useEffect } from 'react';
import { Plus, TrendingUp, AlertCircle, FileText } from 'lucide-react';
import { labResultsService } from '@/services/labResults';
import { LabResult, BiomarkerTrend, LabInsight } from '@/types';
import { LabResultCard } from '@/components/lab-results/LabResultCard';
import { BiomarkerTrendChart } from '@/components/lab-results/BiomarkerTrendChart';
import { AddLabResultModal } from '@/components/lab-results/AddLabResultModal';

export default function LabResultsPage() {
  const [loading, setLoading] = useState(true);
  const [labResults, setLabResults] = useState<LabResult[]>([]);
  const [trends, setTrends] = useState<BiomarkerTrend[]>([]);
  const [insights, setInsights] = useState<LabInsight[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'results' | 'trends' | 'insights'>('results');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [resultsData, trendsData, insightsData] = await Promise.all([
        labResultsService.getLabResults(),
        labResultsService.getBiomarkerTrends(),
        labResultsService.getLabInsights(),
      ]);

      setLabResults(resultsData.lab_results || []);
      setTrends(trendsData.trends || []);
      setInsights(insightsData.insights || []);
    } catch (error) {
      console.error('Error loading lab data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledgeInsight = async (insightId: string) => {
    try {
      await labResultsService.acknowledgeInsight(insightId);
      setInsights(insights.map(i =>
        i.id === insightId ? { ...i, is_acknowledged: true } : i
      ));
    } catch (error) {
      console.error('Error acknowledging insight:', error);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'low':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400';
      default:
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            Lab Results
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2">
            Track and analyze your laboratory test results
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Add Lab Result
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200 dark:border-slate-700">
        <button
          onClick={() => setActiveTab('results')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            activeTab === 'results'
              ? 'border-primary-600 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Lab Results ({labResults.length})
          </div>
        </button>
        <button
          onClick={() => setActiveTab('trends')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            activeTab === 'trends'
              ? 'border-primary-600 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Trends ({trends.length})
          </div>
        </button>
        <button
          onClick={() => setActiveTab('insights')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            activeTab === 'insights'
              ? 'border-primary-600 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            Insights ({insights.filter(i => !i.is_acknowledged).length})
          </div>
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'results' && (
        <div className="space-y-4">
          {labResults.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">
                No lab results yet
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-4">
                Add your first lab result to start tracking your biomarkers
              </p>
              <button
                onClick={() => setShowAddModal(true)}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                Add Lab Result
              </button>
            </div>
          ) : (
            <div className="grid gap-4">
              {labResults.map((result) => (
                <LabResultCard
                  key={result.id}
                  labResult={result}
                  onClick={() => {
                    // TODO: Open detail modal
                  }}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'trends' && (
        <div className="space-y-6">
          {trends.length === 0 ? (
            <div className="text-center py-12">
              <TrendingUp className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">
                No trends available
              </h3>
              <p className="text-slate-600 dark:text-slate-400">
                Add multiple lab results with the same biomarkers to see trends
              </p>
            </div>
          ) : (
            <div className="grid gap-6">
              {trends.map((trend, idx) => (
                <BiomarkerTrendChart key={idx} trend={trend} />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'insights' && (
        <div className="space-y-4">
          {insights.length === 0 ? (
            <div className="text-center py-12">
              <AlertCircle className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">
                No insights available
              </h3>
              <p className="text-slate-600 dark:text-slate-400">
                Add lab results to generate AI-powered insights
              </p>
            </div>
          ) : (
            <div className="grid gap-4">
              {insights.map((insight) => (
                <div
                  key={insight.id}
                  className={`p-6 rounded-lg border ${
                    insight.is_acknowledged
                      ? 'bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700'
                      : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 shadow-sm'
                  }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${getPriorityColor(insight.priority)}`}>
                          {insight.priority}
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-400 capitalize">
                          {insight.insight_type}
                        </span>
                      </div>
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                        {insight.title}
                      </h3>
                      <p className="text-slate-600 dark:text-slate-400 mt-2">
                        {insight.description}
                      </p>
                    </div>
                    {!insight.is_acknowledged && (
                      <button
                        onClick={() => handleAcknowledgeInsight(insight.id)}
                        className="px-3 py-1 text-sm text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors"
                      >
                        Acknowledge
                      </button>
                    )}
                  </div>

                  {insight.recommendations.length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Recommendations:
                      </h4>
                      <ul className="space-y-1">
                        {insight.recommendations.map((rec, idx) => (
                          <li key={idx} className="text-sm text-slate-600 dark:text-slate-400 flex items-start gap-2">
                            <span className="text-primary-600 dark:text-primary-400 mt-1">•</span>
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {insight.biomarkers_involved.length > 0 && (
                    <div className="mt-4 flex items-center gap-2 flex-wrap">
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        Biomarkers:
                      </span>
                      {insight.biomarkers_involved.map((biomarker, idx) => (
                        <span
                          key={idx}
                          className="text-xs px-2 py-1 rounded bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300"
                        >
                          {biomarker}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Add Lab Result Modal */}
      <AddLabResultModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={loadData}
      />
    </div>
  );
}
