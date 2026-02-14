import { create } from 'zustand';
import type { TimelineEntry, AIInsight, DoctorPrepReport } from '@/types';

interface HealthState {
  timeline: TimelineEntry[];
  insights: AIInsight[];
  selectedTimeRange: 14 | 30;
  currentReport: DoctorPrepReport | null;
  isLoading: boolean;
  setTimeline: (timeline: TimelineEntry[]) => void;
  setInsights: (insights: AIInsight[]) => void;
  setTimeRange: (range: 14 | 30) => void;
  setCurrentReport: (report: DoctorPrepReport | null) => void;
  setLoading: (loading: boolean) => void;
}

export const useHealthStore = create<HealthState>((set) => ({
  timeline: [],
  insights: [],
  selectedTimeRange: 14,
  currentReport: null,
  isLoading: false,
  setTimeline: (timeline) => set({ timeline }),
  setInsights: (insights) => set({ insights }),
  setTimeRange: (selectedTimeRange) => set({ selectedTimeRange }),
  setCurrentReport: (currentReport) => set({ currentReport }),
  setLoading: (isLoading) => set({ isLoading }),
}));
