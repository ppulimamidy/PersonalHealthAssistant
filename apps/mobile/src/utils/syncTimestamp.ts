/**
 * Incremental sync timestamp helpers.
 *
 * Stores the last successful sync time per resource in AsyncStorage.
 * The mobile API client passes since_timestamp to backend list endpoints
 * to avoid re-downloading all data on every app open.
 *
 * Key format: sync_ts_{resourceKey}
 * Value format: ISO 8601 UTC string, e.g. "2026-03-11T10:00:00.000Z"
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const PREFIX = 'sync_ts_';

export async function getSyncTimestamp(key: string): Promise<string | null> {
  try {
    return await AsyncStorage.getItem(`${PREFIX}${key}`);
  } catch {
    return null;
  }
}

export async function setSyncTimestamp(key: string, ts: string): Promise<void> {
  try {
    await AsyncStorage.setItem(`${PREFIX}${key}`, ts);
  } catch {
    // Non-critical — silent fail
  }
}

export async function clearSyncTimestamp(key: string): Promise<void> {
  try {
    await AsyncStorage.removeItem(`${PREFIX}${key}`);
  } catch {
    // Non-critical
  }
}

export async function clearAllSyncTimestamps(): Promise<void> {
  try {
    const keys = await AsyncStorage.getAllKeys();
    const syncKeys = keys.filter((k) => k.startsWith(PREFIX));
    await AsyncStorage.multiRemove(syncKeys);
  } catch {
    // Non-critical
  }
}
