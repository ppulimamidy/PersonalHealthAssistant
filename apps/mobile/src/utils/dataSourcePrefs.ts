/**
 * Data source preference utilities.
 * Shared between the Data Sources settings screen and the insights screens.
 * Kept outside app/ so route files don't get imported as navigation modules.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

export type SourceOption = 'auto' | 'oura' | 'healthkit' | 'health_connect';

export interface DataSourcePrefs {
  steps: SourceOption;
  sleep: SourceOption;
  hrv: SourceOption;
  heart_rate: SourceOption;
}

export const DEFAULT_PREFS: DataSourcePrefs = {
  steps: 'auto',
  sleep: 'auto',
  hrv: 'auto',
  heart_rate: 'auto',
};

const STORAGE_KEY = '@vitalix/data_source_prefs';

export async function loadDataSourcePrefs(): Promise<DataSourcePrefs> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    return raw ? { ...DEFAULT_PREFS, ...JSON.parse(raw) } : DEFAULT_PREFS;
  } catch {
    return DEFAULT_PREFS;
  }
}

export async function saveDataSourcePrefs(prefs: DataSourcePrefs): Promise<void> {
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
}

/**
 * Derives a single ?source_priority= value to pass to the timeline API.
 * When all metrics agree on one source we pass that; otherwise "auto".
 */
export function toApiPriority(prefs: DataSourcePrefs): SourceOption {
  const vals = Object.values(prefs) as SourceOption[];
  const nonAuto = vals.filter((v) => v !== 'auto');
  if (nonAuto.length === 0) return 'auto';
  const first = nonAuto[0];
  return nonAuto.every((v) => v === first) ? first : 'auto';
}
