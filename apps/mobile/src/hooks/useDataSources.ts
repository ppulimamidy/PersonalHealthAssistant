/**
 * useDataSources — shared hook for knowing what health data the user has.
 *
 * Reads /api/v1/health-data/sync-watermark to know which sources
 * have synced data. Screens can use this to conditionally show/hide
 * sections (e.g., hide Glucose tab when no CGM, show manual-entry
 * prompts when no wearable).
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';

export type SourceId =
  | 'oura'
  | 'healthkit'
  | 'health_connect'
  | 'dexcom'
  | 'whoop'
  | 'garmin'
  | 'fitbit'
  | 'polar'
  | 'samsung';

interface SourceWatermarks {
  [source: string]: string | null; // ISO timestamp or null
}

/** What metric categories each source provides */
const SOURCE_CAPABILITIES: Record<string, string[]> = {
  oura: ['sleep', 'recovery', 'activity', 'hrv', 'temperature'],
  healthkit: ['sleep', 'activity', 'heart_rate', 'workouts', 'vo2_max', 'spo2'],
  health_connect: ['sleep', 'activity', 'heart_rate', 'workouts', 'vo2_max'],
  dexcom: ['glucose'],
  whoop: ['sleep', 'recovery', 'strain', 'hrv'],
  garmin: ['sleep', 'activity', 'heart_rate', 'vo2_max', 'body_battery', 'stress'],
  fitbit: ['sleep', 'activity', 'heart_rate', 'spo2'],
  polar: ['sleep', 'activity', 'heart_rate', 'hrv'],
  samsung: ['sleep', 'activity', 'heart_rate'],
};

export function useDataSources() {
  const { data: watermarks, isLoading } = useQuery<SourceWatermarks>({
    queryKey: ['data-sources-watermarks'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/health-data/sync-watermark');
      return data ?? {};
    },
    staleTime: 5 * 60 * 1000, // 5 min cache
  });

  const connectedSources = Object.keys(watermarks ?? {}) as SourceId[];

  /** All metric categories the user has data for */
  const availableCategories = new Set<string>();
  for (const src of connectedSources) {
    for (const cap of SOURCE_CAPABILITIES[src] ?? []) {
      availableCategories.add(cap);
    }
  }

  return {
    isLoading,
    /** List of source IDs that have synced at least once */
    connectedSources,
    /** Watermarks keyed by source */
    watermarks: watermarks ?? {},
    /** Check if a specific source is connected */
    hasSource: (src: SourceId) => connectedSources.includes(src),
    /** Check if a metric category is available from any source */
    hasCategory: (cat: string) => availableCategories.has(cat),
    /** True if user has any wearable connected */
    hasWearable: connectedSources.length > 0,
    /** True if user has CGM data (Dexcom, etc.) */
    hasCGM: connectedSources.some((s) => SOURCE_CAPABILITIES[s]?.includes('glucose')),
    /** True if user has sleep data from any source */
    hasSleep: availableCategories.has('sleep'),
    /** True if user has HRV data */
    hasHRV: availableCategories.has('hrv'),
    /** True if user has glucose data */
    hasGlucose: availableCategories.has('glucose'),
  };
}
