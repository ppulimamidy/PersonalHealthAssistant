'use client';

import { useState, useEffect } from 'react';
import { MetaAnalysisReport } from '@/types';
import { specialistAgentsService } from '@/services/specialistAgents';
import { MetaAnalysisView } from '@/components/specialist-agents/MetaAnalysisView';
import { ResearchView } from '@/components/research/ResearchView';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';

type Tab = 'ai-analysis' | 'literature';

export default function ResearchPage() {
  const [activeTab, setActiveTab] = useState<Tab>('ai-analysis');
  const [report, setReport] = useState<MetaAnalysisReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadCachedReport();
  }, []);

  const loadCachedReport = async () => {
    try {
      const cachedReport = await specialistAgentsService.getCachedMetaAnalysis();
      if (cachedReport) setReport(cachedReport);
    } catch {
      // No cached report — expected on first visit
    }
  };

  const generateNewReport = async () => {
    setIsLoading(true);
    try {
      const newReport = await specialistAgentsService.generateMetaAnalysis(30);
      setReport(newReport);
      toast.success('Analysis complete');
    } catch (error: any) {
      const message =
        error?.response?.data?.detail || 'Failed to generate analysis. Please try again.';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: 'ai-analysis', label: 'AI Analysis' },
    { id: 'literature', label: 'Literature Search' },
  ];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#E8EDF5] mb-1">Research</h1>
        <p className="text-sm" style={{ color: '#526380' }}>
          Evidence-based insights and scientific literature for your health patterns
        </p>
      </div>

      {/* Tab switcher */}
      <div className="flex gap-1 mb-6 p-1 rounded-lg bg-[#0D1117] border border-white/5 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'px-4 py-1.5 rounded-md text-sm font-medium transition-all duration-150',
              activeTab === tab.id
                ? 'bg-[#00D4AA]/15 text-[#00D4AA]'
                : 'text-[#526380] hover:text-[#8B97A8]'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'ai-analysis' && (
        <MetaAnalysisView
          report={report}
          onRefresh={generateNewReport}
          isLoading={isLoading}
        />
      )}
      {activeTab === 'literature' && <ResearchView />}
    </div>
  );
}
