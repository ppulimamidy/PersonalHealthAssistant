'use client';

import { useState, useEffect } from 'react';
import { MetaAnalysisReport } from '@/types';
import { specialistAgentsService } from '@/services/specialistAgents';
import { MetaAnalysisView } from '@/components/specialist-agents/MetaAnalysisView';
import { useToast } from '@/components/ui/use-toast';

export default function MetaAnalysisPage() {
  const [report, setReport] = useState<MetaAnalysisReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadCachedReport();
  }, []);

  const loadCachedReport = async () => {
    try {
      const cachedReport = await specialistAgentsService.getCachedMetaAnalysis();
      if (cachedReport) {
        setReport(cachedReport);
      }
    } catch (error) {
      // No cached report available, that's okay
      console.error('Error loading cached report:', error);
    }
  };

  const generateNewReport = async () => {
    setIsLoading(true);
    try {
      const newReport = await specialistAgentsService.generateMetaAnalysis(30);
      setReport(newReport);
      toast({
        title: 'Meta-Analysis Complete',
        description: 'Your comprehensive health analysis has been generated.',
        variant: 'success',
      });
    } catch (error: any) {
      console.error('Error generating meta-analysis:', error);
      toast({
        title: 'Analysis Failed',
        description: error.response?.data?.detail || 'Failed to generate meta-analysis. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-2">
          Meta-Analysis Report
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          Comprehensive health analysis by specialist AI agents across all domains
        </p>
      </div>

      <MetaAnalysisView
        report={report}
        onRefresh={generateNewReport}
        isLoading={isLoading}
      />
    </div>
  );
}
