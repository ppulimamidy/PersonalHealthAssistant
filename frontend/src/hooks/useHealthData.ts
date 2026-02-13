'use client';

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ouraService } from '@/services/oura';
import { insightsService } from '@/services/insights';
import { useHealthStore } from '@/stores/healthStore';

export function useHealthData() {
  const { selectedTimeRange, setTimeline, setInsights } = useHealthStore();

  const timelineQuery = useQuery({
    queryKey: ['timeline', selectedTimeRange],
    queryFn: () => ouraService.getTimeline(selectedTimeRange),
  });

  const insightsQuery = useQuery({
    queryKey: ['insights'],
    queryFn: insightsService.getInsights,
  });

  useEffect(() => {
    if (timelineQuery.data) setTimeline(timelineQuery.data);
  }, [timelineQuery.data, setTimeline]);

  useEffect(() => {
    if (insightsQuery.data) setInsights(insightsQuery.data);
  }, [insightsQuery.data, setInsights]);

  return {
    timeline: timelineQuery.data,
    insights: insightsQuery.data,
    isLoading: timelineQuery.isLoading || insightsQuery.isLoading,
    refetchTimeline: timelineQuery.refetch,
    refetchInsights: insightsQuery.refetch,
  };
}
