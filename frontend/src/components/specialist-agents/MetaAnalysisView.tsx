'use client';

import { useState } from 'react';
import { MetaAnalysisReport } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { SpecialistInsightCard } from './SpecialistInsightCard';
import { CrossSystemPatternCard } from './CrossSystemPatternCard';
import { EvidenceBasedRecommendationCard } from './EvidenceBasedRecommendationCard';
import { Button } from '@/components/ui/Button';
import {
  Brain,
  TrendingUp,
  AlertCircle,
  Target,
  RefreshCw,
  Calendar,
  CheckCircle,
  Loader2,
} from 'lucide-react';

interface MetaAnalysisViewProps {
  report: MetaAnalysisReport | null;
  onRefresh: () => void;
  isLoading?: boolean;
}

export function MetaAnalysisView({ report, onRefresh, isLoading }: MetaAnalysisViewProps) {
  const [selectedTab, setSelectedTab] = useState<'overview' | 'specialists' | 'patterns' | 'protocol'>('overview');

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <Loader2 className="w-12 h-12 text-primary-600 animate-spin" />
        <p className="text-lg font-medium text-slate-700 dark:text-slate-300">
          Analyzing health data with specialist agents...
        </p>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          This may take 30-60 seconds
        </p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <Brain className="w-16 h-16 text-slate-300 dark:text-slate-700" />
        <h3 className="text-xl font-semibold text-slate-700 dark:text-slate-300">
          No Meta-Analysis Available
        </h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 text-center max-w-md">
          Generate a comprehensive health meta-analysis by having our specialist agents analyze your data across all health domains.
        </p>
        <Button onClick={onRefresh} className="mt-4">
          <Brain className="w-4 h-4 mr-2" />
          Generate Meta-Analysis
        </Button>
      </div>
    );
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 dark:text-green-400';
    if (confidence >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-orange-600 dark:text-orange-400';
  };

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Analysis Period</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {report.analysis_period_days} days
                </p>
              </div>
              <Calendar className="w-8 h-8 text-slate-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Specialists</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {report.specialist_insights.length}
                </p>
              </div>
              <Brain className="w-8 h-8 text-primary-600 dark:text-primary-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Confidence</p>
                <p className={`text-2xl font-bold ${getConfidenceColor(report.overall_confidence)}`}>
                  {Math.round(report.overall_confidence * 100)}%
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Data Quality</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {Math.round(report.data_completeness * 100)}%
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Refresh Button */}
      <div className="flex justify-end">
        <Button onClick={onRefresh} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          Regenerate Analysis
        </Button>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 dark:border-slate-700">
        <nav className="flex gap-4">
          <button
            onClick={() => setSelectedTab('overview')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              selectedTab === 'overview'
                ? 'border-primary-600 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setSelectedTab('specialists')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              selectedTab === 'specialists'
                ? 'border-primary-600 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Specialist Insights ({report.specialist_insights.length})
          </button>
          <button
            onClick={() => setSelectedTab('patterns')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              selectedTab === 'patterns'
                ? 'border-primary-600 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Cross-System Patterns ({report.cross_system_patterns.length})
          </button>
          <button
            onClick={() => setSelectedTab('protocol')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              selectedTab === 'protocol'
                ? 'border-primary-600 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Recommended Protocol ({report.recommended_protocol.length})
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {selectedTab === 'overview' && (
        <div className="space-y-6">
          {/* Primary Diagnosis */}
          <Card className="border-2 border-red-200 dark:border-red-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                Primary Diagnosis
                <span className={`text-sm font-medium ml-2 ${getConfidenceColor(report.primary_diagnosis.confidence)}`}>
                  ({Math.round(report.primary_diagnosis.confidence * 100)}% confidence)
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                {report.primary_diagnosis.diagnosis}
              </p>

              <div>
                <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Systems Involved:
                </h4>
                <div className="flex flex-wrap gap-2">
                  {report.primary_diagnosis.systems_involved.map((system, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 rounded-full bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm font-medium capitalize"
                    >
                      {system}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Causal Chain:
                </h4>
                <div className="flex items-center gap-2 overflow-x-auto pb-2">
                  {report.primary_diagnosis.causal_chain.map((step, idx) => (
                    <div key={idx} className="flex items-center gap-2 flex-shrink-0">
                      <div className="px-3 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-sm text-slate-700 dark:text-slate-300 whitespace-nowrap">
                        {step}
                      </div>
                      {idx < report.primary_diagnosis.causal_chain.length - 1 && (
                        <span className="text-slate-400 dark:text-slate-600">→</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Secondary Diagnoses */}
          {report.secondary_diagnoses.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
                Secondary Diagnoses
              </h3>
              <div className="grid gap-4">
                {report.secondary_diagnoses.map((diagnosis, idx) => (
                  <Card key={idx}>
                    <CardContent className="pt-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <p className="font-semibold text-slate-900 dark:text-slate-100 mb-2">
                            {diagnosis.diagnosis}
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {diagnosis.systems_involved.map((system, sysIdx) => (
                              <span
                                key={sysIdx}
                                className="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs capitalize"
                              >
                                {system}
                              </span>
                            ))}
                          </div>
                        </div>
                        <span className={`text-sm font-medium ${getConfidenceColor(diagnosis.confidence)}`}>
                          {Math.round(diagnosis.confidence * 100)}%
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Top Recommendations Preview */}
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
              <Target className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              Top Priority Actions
            </h3>
            <div className="space-y-3">
              {report.recommended_protocol.slice(0, 3).map((rec, idx) => (
                <EvidenceBasedRecommendationCard key={idx} recommendation={rec} rank={idx + 1} />
              ))}
            </div>
            {report.recommended_protocol.length > 3 && (
              <Button
                onClick={() => setSelectedTab('protocol')}
                variant="outline"
                className="w-full mt-4"
              >
                View All {report.recommended_protocol.length} Recommendations
              </Button>
            )}
          </div>
        </div>
      )}

      {selectedTab === 'specialists' && (
        <div className="grid gap-6">
          {report.specialist_insights.map((insight, idx) => (
            <SpecialistInsightCard key={idx} insight={insight} />
          ))}
        </div>
      )}

      {selectedTab === 'patterns' && (
        <div className="space-y-6">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Cross-system patterns reveal how different aspects of your health interact and influence each other.
          </p>
          <div className="grid gap-4">
            {report.cross_system_patterns.map((pattern, idx) => (
              <CrossSystemPatternCard key={idx} pattern={pattern} />
            ))}
          </div>
          {report.cross_system_patterns.length === 0 && (
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-slate-500 dark:text-slate-400">
                  No significant cross-system patterns detected in this analysis period.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {selectedTab === 'protocol' && (
        <div className="space-y-6">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Evidence-based recommendations prioritized by impact and supported by clinical research.
          </p>
          <div className="space-y-4">
            {report.recommended_protocol.map((rec, idx) => (
              <EvidenceBasedRecommendationCard key={idx} recommendation={rec} rank={idx + 1} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
