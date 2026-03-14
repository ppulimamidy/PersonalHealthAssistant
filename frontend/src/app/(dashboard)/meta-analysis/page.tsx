'use client';

import { useState, useEffect } from 'react';
import { MetaAnalysisReport } from '@/types';
import { specialistAgentsService } from '@/services/specialistAgents';
import { MetaAnalysisView } from '@/components/specialist-agents/MetaAnalysisView';
import toast from 'react-hot-toast';

export default function MetaAnalysisPage() {
  const [report, setReport] = useState<MetaAnalysisReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadCachedReport();
  }, []);

  const loadCachedReport = async () => {
    try {
      const cachedReport = await specialistAgentsService.getCachedMetaAnalysis();
      if (cachedReport) {
        setReport(cachedReport);
      }
    } catch {
      // No cached report available — that's expected on first visit
    }
  };

  const generateNewReport = async () => {
    setIsLoading(true);
    try {
      const newReport = await specialistAgentsService.generateMetaAnalysis(30);
      setReport(newReport);
      toast.success('Meta-Analysis Complete');
    } catch (error: any) {
      const message =
        error?.response?.data?.detail ||
        'Failed to generate analysis. Please try again.';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#E8EDF5] mb-1">
          Research Evidence
        </h1>
        <p className="text-sm" style={{ color: '#526380' }}>
          What the science says about your patterns
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
