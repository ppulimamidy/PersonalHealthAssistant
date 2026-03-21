/**
 * Phase 4: Timeline screen.
 * Scrollable date-by-date health diary.
 * Data: GET /api/v1/health/timeline?days=30
 */

import { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format, isToday, isYesterday } from 'date-fns';
import { api } from '@/services/api';
import {
  loadDataSourcePrefs,
  toApiPriority,
  type SourceOption,
} from '@/utils/dataSourcePrefs';

// ─── Types ────────────────────────────────────────────────────────────────────

interface AltMetrics {
  source: string;
  steps?: number;
  sleep_hours?: number;
  resting_heart_rate?: number;
  hrv_ms?: number;
}

interface TimelineEntry {
  date: string;
  sources?: string[];
  alt_metrics?: AltMetrics;
  sleep?: {
    sleep_score?: number;
    total_sleep_duration?: number;
    sleep_efficiency?: number;
    deep_sleep_duration?: number;
  };
  readiness?: {
    readiness_score?: number;
    hrv_balance?: number;
    resting_heart_rate?: number;
    recovery_index?: number;
  };
  activity?: {
    steps?: number;
    activity_score?: number;
    active_calories?: number;
  };
}

interface SymptomAction {
  type: string;
  severity?: number;
  mood?: string;
  stress_level?: number;
}

interface AdherenceAction {
  taken: number;
  total: number;
  medications: string[];
}

interface ExperimentAction {
  title: string;
  day_number?: number;
  adhered?: boolean;
  status?: string;
}

interface JourneyEvent {
  title: string;
  event: string;
  phase: string;
  phase_number: number;
}

interface MedicalRecordAction {
  type: string;
  title: string;
}

interface DayActions {
  symptoms?: SymptomAction[];
  adherence?: AdherenceAction;
  experiments?: ExperimentAction[];
  journey_events?: JourneyEvent[];
  medical_records?: MedicalRecordAction[];
}

type ActionsMap = Record<string, DayActions>;

const DAY_OPTIONS = [7, 14, 30] as const;

// ─── Score Ring (compact) ─────────────────────────────────────────────────────

function ScoreChip({ value, label, color }: Readonly<{ value: number; label: string; color: string }>) {
  return (
    <View className="items-center flex-1">
      <Text className="font-display text-lg" style={{ color }}>
        {Math.round(value)}
      </Text>
      <Text className="text-[#526380] text-xs">{label}</Text>
    </View>
  );
}

// ─── Action Overlay ───────────────────────────────────────────────────────────

function ActionOverlay({ actions }: Readonly<{ actions?: DayActions }>) {
  if (!actions) return null;
  const { symptoms, adherence, experiments, journey_events, medical_records } = actions;
  const hasAny = (symptoms?.length ?? 0) > 0 || adherence || (experiments?.length ?? 0) > 0 || (journey_events?.length ?? 0) > 0 || (medical_records?.length ?? 0) > 0;
  if (!hasAny) return null;

  return (
    <View className="mt-2 pt-2 border-t border-surface-border">
      {/* Journey events */}
      {journey_events && journey_events.length > 0 && journey_events.map((je, i) => (
        <View key={`je-${i}`} className="flex-row items-center gap-1.5 mb-1">
          <Ionicons name="flag-outline" size={12} color="#818CF8" />
          <Text className="text-[#818CF8] text-xs font-sansMedium">
            {je.phase} {je.event === 'phase_complete' ? 'completed' : 'started'}
          </Text>
          <Text className="text-[#3D4F66] text-xs">· {je.title}</Text>
        </View>
      ))}

      {/* Experiments */}
      {experiments && experiments.length > 0 && experiments.map((exp, i) => (
        <View key={`exp-${i}`} className="flex-row items-center gap-1.5 mb-1">
          <Ionicons name="flask-outline" size={12} color="#2DD4BF" />
          <Text className="text-[#2DD4BF] text-xs font-sansMedium">
            Day {exp.day_number}: {exp.title}
          </Text>
          {exp.adhered != null && (
            <View className="rounded-full px-1.5 py-0.5" style={{ backgroundColor: exp.adhered ? '#00D4AA20' : '#F8717120' }}>
              <Text className="text-[9px]" style={{ color: exp.adhered ? '#00D4AA' : '#F87171' }}>
                {exp.adhered ? '✓' : '✗'}
              </Text>
            </View>
          )}
        </View>
      ))}

      {/* Symptoms */}
      {symptoms && symptoms.length > 0 && (
        <View className="flex-row items-center gap-1.5 mb-1 flex-wrap">
          <Ionicons name="alert-circle-outline" size={12} color="#F5A623" />
          {symptoms.map((s, i) => {
            const sevColor = (s.severity ?? 0) >= 7 ? '#F87171' : (s.severity ?? 0) >= 4 ? '#F5A623' : '#6EE7B7';
            return (
              <View key={`sym-${i}`} className="flex-row items-center gap-1">
                <View className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: sevColor }} />
                <Text className="text-[#8B9BB4] text-xs">
                  {s.type}{s.severity != null ? ` · ${s.severity}/10` : ''}
                </Text>
              </View>
            );
          })}
        </View>
      )}

      {/* Medication adherence */}
      {adherence && adherence.total > 0 && (() => {
        const pct = adherence.taken / adherence.total;
        const color = pct >= 0.8 ? '#00D4AA' : pct >= 0.5 ? '#F5A623' : '#F87171';
        return (
          <View className="flex-row items-center gap-1.5 mb-1">
            <Ionicons name="medkit-outline" size={12} color={color} />
            <Text className="text-xs" style={{ color }}>
              {adherence.taken}/{adherence.total} meds taken
            </Text>
            {adherence.medications.length > 0 && (
              <Text className="text-[#3D4F66] text-[10px]">
                · {adherence.medications.slice(0, 3).join(', ')}{adherence.medications.length > 3 ? '…' : ''}
              </Text>
            )}
          </View>
        );
      })()}

      {/* Medical records */}
      {medical_records && medical_records.length > 0 && medical_records.map((rec, i) => {
        const iconMap: Record<string, { icon: string; color: string }> = {
          pathology: { icon: 'cut-outline', color: '#F87171' },
          genomic: { icon: 'code-working-outline', color: '#818CF8' },
          imaging: { icon: 'scan-outline', color: '#60A5FA' },
        };
        const cfg = iconMap[rec.type] ?? { icon: 'document-outline', color: '#526380' };
        return (
          <View key={`rec-${i}`} className="flex-row items-center gap-1.5 mb-1">
            <Ionicons name={cfg.icon as never} size={12} color={cfg.color} />
            <Text className="text-xs" style={{ color: cfg.color }}>{rec.title}</Text>
          </View>
        );
      })}
    </View>
  );
}

// ─── Timeline Day Card ────────────────────────────────────────────────────────

function DayCard({ entry, actions, daySummary }: Readonly<{ entry: TimelineEntry; actions?: DayActions; daySummary?: string }>) {
  const d = new Date(entry.date);
  let dateLabel = format(d, 'EEE, MMM d');
  if (isToday(d)) dateLabel = 'Today';
  else if (isYesterday(d)) dateLabel = 'Yesterday';

  const sleep = entry.sleep?.sleep_score;
  const readiness = entry.readiness?.readiness_score;
  const activity = entry.activity?.activity_score;
  const steps = entry.activity?.steps;
  const hr = entry.readiness?.resting_heart_rate;
  const hrv = entry.readiness?.hrv_balance;

  const sleepHrs = entry.sleep?.total_sleep_duration
    ? (entry.sleep.total_sleep_duration / 3600).toFixed(1)
    : null;

  const topScore = Math.max(sleep ?? 0, readiness ?? 0, activity ?? 0);
  let topColor = '#F87171';
  if (topScore >= 80) topColor = '#6EE7B7';
  else if (topScore >= 60) topColor = '#F5A623';

  let sleepColor = '#F87171';
  if (sleep == null || sleep >= 80) sleepColor = '#818CF8';
  else if (sleep >= 60) sleepColor = '#F5A623';

  let readinessColor = '#F87171';
  if (readiness == null || readiness >= 80) readinessColor = '#6EE7B7';
  else if (readiness >= 60) readinessColor = '#F5A623';

  let activityColor = '#F87171';
  if (activity == null || activity >= 60) activityColor = '#F5A623';

  const sourceLabels: Record<string, string> = {
    oura: 'Oura Ring',
    healthkit: 'Apple Health',
    health_connect: 'Health Connect',
    dexcom: 'Dexcom CGM',
    whoop: 'WHOOP',
    garmin: 'Garmin',
    fitbit: 'Fitbit',
    polar: 'Polar',
    samsung: 'Samsung Health',
  };

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
      {/* Date row */}
      <View className="flex-row items-center justify-between mb-3">
        <Text className="text-[#E8EDF5] font-sansMedium text-sm">{dateLabel}</Text>
        <View className="flex-row items-center gap-2">
          {entry.sources && entry.sources.length > 0 && (
            <View className="flex-row gap-1">
              {entry.sources.map((s) => (
                <View key={s} className="bg-[#1E2A3B] rounded-full px-1.5 py-0.5">
                  <Text className="text-[#526380] text-[9px]">{sourceLabels[s] ?? s}</Text>
                </View>
              ))}
            </View>
          )}
          <View
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: topScore > 0 ? topColor : '#1E2A3B' }}
          />
        </View>
      </View>

      {/* Day summary */}
      {daySummary ? (
        <Text className="text-[#526380] text-[11px] mb-2 leading-4" style={{ fontStyle: 'italic' }}>
          {daySummary}
        </Text>
      ) : null}

      {/* Scores row */}
      {(sleep != null || readiness != null || activity != null) && (
        <View className="flex-row mb-3 pb-3 border-b border-surface-border">
          {sleep != null && <ScoreChip value={sleep} label="Sleep" color={sleepColor} />}
          {readiness != null && <ScoreChip value={readiness} label="Readiness" color={readinessColor} />}
          {activity != null && <ScoreChip value={activity} label="Activity" color={activityColor} />}
        </View>
      )}

      {/* Detail row */}
      <View className="flex-row flex-wrap gap-3">
        {sleepHrs != null && (
          <View className="flex-row items-center gap-1">
            <Ionicons name="moon-outline" size={12} color="#526380" />
            <Text className="text-[#526380] text-xs">{sleepHrs}h sleep</Text>
          </View>
        )}
        {steps != null && (
          <View className="flex-row items-center gap-1">
            <Ionicons name="footsteps-outline" size={12} color="#526380" />
            <Text className="text-[#526380] text-xs">{steps.toLocaleString()} steps</Text>
          </View>
        )}
        {hr != null && (
          <View className="flex-row items-center gap-1">
            <Ionicons name="heart-outline" size={12} color="#526380" />
            <Text className="text-[#526380] text-xs">{hr} bpm</Text>
          </View>
        )}
        {hrv != null && (
          <View className="flex-row items-center gap-1">
            <Ionicons name="pulse-outline" size={12} color="#526380" />
            <Text className="text-[#526380] text-xs">HRV {hrv}</Text>
          </View>
        )}
      </View>

      {/* User actions overlay */}
      <ActionOverlay actions={actions} />

      {/* Alt source comparison — side-by-side */}
      {entry.alt_metrics && (() => {
        const alt = entry.alt_metrics;
        const SOURCE_NAMES: Record<string, string> = { oura: 'Oura', healthkit: 'Apple', health_connect: 'HC' };
        const altLabel = SOURCE_NAMES[alt.source] ?? alt.source;
        const primarySource = entry.sources?.find((s) => s !== alt.source);
        const primaryLabel = primarySource ? (SOURCE_NAMES[primarySource] ?? primarySource) : 'Primary';
        const comparisons: { label: string; primary: string; secondary: string }[] = [];
        if (alt.steps != null && steps != null) {
          comparisons.push({ label: 'Steps', primary: steps.toLocaleString(), secondary: alt.steps.toLocaleString() });
        }
        if (alt.sleep_hours != null && sleepHrs != null) {
          comparisons.push({ label: 'Sleep', primary: `${sleepHrs}h`, secondary: `${alt.sleep_hours.toFixed(1)}h` });
        }
        if (alt.resting_heart_rate != null && hr != null) {
          comparisons.push({ label: 'RHR', primary: `${hr}`, secondary: `${alt.resting_heart_rate}` });
        }
        if (alt.hrv_ms != null && hrv != null) {
          comparisons.push({ label: 'HRV', primary: `${hrv}`, secondary: `${alt.hrv_ms.toFixed(0)}` });
        }
        if (comparisons.length === 0) return null;
        return (
          <View className="mt-2 pt-2 border-t border-surface-border">
            <View className="flex-row items-center justify-between mb-1.5">
              <Text className="text-[#3A4A5C] text-[10px]">Source comparison</Text>
              <View className="flex-row gap-3">
                <Text className="text-[#526380] text-[10px] font-sansMedium">{primaryLabel}</Text>
                <Text className="text-[#3D4F66] text-[10px] font-sansMedium">{altLabel}</Text>
              </View>
            </View>
            {comparisons.map((cmp) => (
              <View key={cmp.label} className="flex-row items-center justify-between mb-0.5">
                <Text className="text-[#3D4F66] text-xs flex-1">{cmp.label}</Text>
                <View className="flex-row gap-3">
                  <Text className="text-[#8B9BB4] text-xs font-sansMedium w-14 text-right">{cmp.primary}</Text>
                  <Text className="text-[#3D4F66] text-xs w-14 text-right">{cmp.secondary}</Text>
                </View>
              </View>
            ))}
          </View>
        );
      })()}
    </View>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

type SummariesMap = Record<string, string>;

function TimelineBody({ isLoading, entries, actionsMap, summariesMap }: Readonly<{ isLoading: boolean; entries: TimelineEntry[]; actionsMap: ActionsMap; summariesMap: SummariesMap }>) {
  if (isLoading) return <ActivityIndicator color="#00D4AA" className="mt-10" />;
  if (entries.length === 0) {
    return (
      <View className="items-center py-16">
        <Ionicons name="calendar-outline" size={44} color="#526380" />
        <Text className="text-[#526380] text-base mt-3">No timeline data yet</Text>
        <Text className="text-[#526380] text-sm mt-1 text-center leading-5 px-4">
          Connect Apple Health, Oura, or another device to see your day-by-day health story
        </Text>
        <TouchableOpacity
          onPress={() => router.push('/(tabs)/profile/data-sources')}
          className="mt-4 flex-row items-center gap-1.5 px-4 py-2 rounded-lg"
          style={{ backgroundColor: '#00D4AA15', borderWidth: 1, borderColor: '#00D4AA30' }}
          activeOpacity={0.7}
        >
          <Ionicons name="link-outline" size={14} color="#00D4AA" />
          <Text className="text-[#00D4AA] text-xs font-sansMedium">Connect a device</Text>
        </TouchableOpacity>
      </View>
    );
  }
  return <>{entries.map((entry) => <DayCard key={entry.date} entry={entry} actions={actionsMap[entry.date]} daySummary={summariesMap[entry.date]} />)}</>;
}

export default function TimelineScreen() {
  const [days, setDays] = useState<7 | 14 | 30>(14);
  const [sourcePriority, setSourcePriority] = useState<SourceOption>('auto');

  useEffect(() => {
    loadDataSourcePrefs().then((p) => setSourcePriority(toApiPriority(p)));
  }, []);

  const { data, isLoading } = useQuery<{ entries: TimelineEntry[] }>({
    queryKey: ['health-timeline', days, sourcePriority],
    queryFn: async () => {
      const { data: resp } = await api.get(
        `/api/v1/health/timeline?days=${days}&source_priority=${sourcePriority}`
      );
      return { entries: Array.isArray(resp) ? resp : (resp?.entries ?? []) };
    },
  });

  const { data: actionsData } = useQuery<ActionsMap>({
    queryKey: ['timeline-actions', days],
    queryFn: async () => {
      const { data: resp } = await api.get(`/api/v1/timeline-actions?days=${days}`);
      return (resp ?? {}) as ActionsMap;
    },
    staleTime: 30_000,
  });

  const { data: summariesData } = useQuery<SummariesMap>({
    queryKey: ['day-summaries', days],
    queryFn: async () => {
      try {
        const { data: resp } = await api.get(`/api/v1/insights-intelligence/day-summaries?days=${days}`);
        const map: SummariesMap = {};
        for (const s of resp?.summaries ?? []) {
          if (s.date && s.summary) map[s.date] = s.summary;
        }
        return map;
      } catch { return {}; }
    },
    staleTime: 5 * 60_000,
  });

  const rawEntries = Array.isArray(data) ? data : (data?.entries ?? []);
  const entries = [...rawEntries].sort((a, b) => b.date.localeCompare(a.date)); // most recent first
  const actionsMap: ActionsMap = actionsData ?? {};
  const summariesMap: SummariesMap = summariesData ?? {};

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <Text className="text-xl font-display text-[#E8EDF5] flex-1">Timeline</Text>
        <View className="flex-row gap-1">
          {DAY_OPTIONS.map((d) => (
            <TouchableOpacity
              key={d}
              onPress={() => setDays(d)}
              className="px-2.5 py-1 rounded-lg"
              style={{
                backgroundColor: days === d ? '#00D4AA20' : 'transparent',
                borderWidth: 1,
                borderColor: days === d ? '#00D4AA' : '#1E2A3B',
              }}
            >
              <Text className="text-xs font-sansMedium" style={{ color: days === d ? '#00D4AA' : '#526380' }}>
                {d}d
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View className="px-6 pt-5">
        <TimelineBody isLoading={isLoading} entries={entries} actionsMap={actionsMap} summariesMap={summariesMap} />
      </View>
    </ScrollView>
  );
}
