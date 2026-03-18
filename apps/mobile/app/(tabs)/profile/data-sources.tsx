/**
 * Data Sources settings screen.
 *
 * Users often wear multiple devices (e.g. Oura Ring + Apple Watch) that
 * track the same metrics with different methodologies. Rather than silently
 * picking one source, this screen lets the user control which source is
 * authoritative per metric — or use "Auto" heuristics.
 *
 * Stored in AsyncStorage; passed as ?source_priority=... to the timeline API.
 */

import { useState, useEffect, useCallback } from 'react';
import { View, Text, ScrollView, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import {
  loadDataSourcePrefs,
  saveDataSourcePrefs,
  type SourceOption,
  type DataSourcePrefs,
  DEFAULT_PREFS,
} from '@/utils/dataSourcePrefs';

// ─── Config ───────────────────────────────────────────────────────────────────

interface MetricConfig {
  key: keyof DataSourcePrefs;
  label: string;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  color: string;
  autoHeuristic: string; // explains what "Auto" picks for this metric
}

const METRICS: MetricConfig[] = [
  {
    key: 'steps',
    label: 'Steps',
    icon: 'footsteps-outline',
    color: '#6EE7B7',
    autoHeuristic: 'Prefers Apple Health or Garmin — wrist-worn step counting is generally more accurate than a ring.',
  },
  {
    key: 'sleep',
    label: 'Sleep',
    icon: 'moon-outline',
    color: '#818CF8',
    autoHeuristic: 'Prefers Oura or WHOOP — detailed sleep staging (light/deep/REM) and dedicated sleep sensors.',
  },
  {
    key: 'hrv',
    label: 'HRV',
    icon: 'pulse-outline',
    color: '#00D4AA',
    autoHeuristic: 'Prefers Oura — overnight HRV from a ring is less prone to motion artifact.',
  },
  {
    key: 'heart_rate',
    label: 'Resting Heart Rate',
    icon: 'heart-outline',
    color: '#F87171',
    autoHeuristic: 'Prefers Oura — overnight resting HR is more stable than a daytime wrist reading.',
  },
  {
    key: 'respiratory_rate',
    label: 'Respiratory Rate',
    icon: 'cellular-outline',
    color: '#A78BFA',
    autoHeuristic: 'Prefers Apple Health / wearable — nighttime respiratory rate from a wrist or ring sensor.',
  },
  {
    key: 'active_calories',
    label: 'Active Calories',
    icon: 'flame-outline',
    color: '#FB923C',
    autoHeuristic: 'Prefers Apple Health — Apple Watch active energy is the gold standard for calorie tracking.',
  },
  {
    key: 'workouts',
    label: 'Workouts',
    icon: 'barbell-outline',
    color: '#F59E0B',
    autoHeuristic: 'Prefers Apple Health / Health Connect — uses GPS and motion sensors to detect workout type and duration.',
  },
  {
    key: 'vo2_max',
    label: 'VO₂ Max',
    icon: 'speedometer-outline',
    color: '#34D399',
    autoHeuristic: 'Prefers Apple Health or Garmin — both estimate VO₂ max during outdoor runs and walks.',
  },
  {
    key: 'glucose',
    label: 'Glucose',
    icon: 'water-outline',
    color: '#F472B6',
    autoHeuristic: 'Prefers Dexcom — most accurate dedicated CGM with continuous 5-minute interval readings.',
  },
  {
    key: 'strain_recovery',
    label: 'Strain / Recovery',
    icon: 'fitness-outline',
    color: '#FBBF24',
    autoHeuristic: 'Prefers WHOOP — dedicated recovery tracker with proprietary strain and recovery scores.',
  },
  {
    key: 'body_battery',
    label: 'Body Battery',
    icon: 'battery-half-outline',
    color: '#22D3EE',
    autoHeuristic: 'Garmin only — Body Battery is a proprietary Garmin metric combining HRV, stress, and activity.',
  },
];

const SOURCE_OPTIONS: Array<{ value: SourceOption; label: string; sub: string }> = [
  { value: 'auto',           label: 'Auto',                  sub: 'Smart default — see note below' },
  { value: 'oura',           label: 'Oura Ring',             sub: 'Always use Oura when available' },
  { value: 'healthkit',      label: 'Apple Health',          sub: 'Always use Apple Health / Watch' },
  { value: 'health_connect', label: 'Google Health Connect', sub: 'Always use Android Health Connect' },
  { value: 'dexcom',         label: 'Dexcom CGM',            sub: 'Use Dexcom for glucose metrics' },
  { value: 'whoop',          label: 'WHOOP',                 sub: 'Use WHOOP for strain and recovery' },
  { value: 'garmin',         label: 'Garmin',                sub: 'Use Garmin for activity and body battery' },
  { value: 'fitbit',         label: 'Fitbit',                sub: 'Use Fitbit for activity and sleep' },
];

// ─── Metric Card ──────────────────────────────────────────────────────────────

function MetricSourceCard({
  metric,
  value,
  onChange,
}: Readonly<{
  metric: MetricConfig;
  value: SourceOption;
  onChange: (v: SourceOption) => void;
}>) {
  const autoOpt = SOURCE_OPTIONS.find((o) => o.value === 'auto') ?? SOURCE_OPTIONS[0];
  const selectedLabel = SOURCE_OPTIONS.find((o) => o.value === value)?.label ?? value;

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
      {/* Header */}
      <View className="flex-row items-center mb-3">
        <View
          className="w-9 h-9 rounded-xl items-center justify-center mr-3"
          style={{ backgroundColor: `${metric.color}18` }}
        >
          <Ionicons name={metric.icon} size={18} color={metric.color} />
        </View>
        <View className="flex-1">
          <Text className="text-[#E8EDF5] font-sansMedium text-sm">{metric.label}</Text>
          <Text className="text-[#526380] text-xs mt-0.5">
            Current: <Text style={{ color: metric.color }}>{selectedLabel}</Text>
          </Text>
        </View>
      </View>

      {/* Options */}
      <View className="gap-2">
        {SOURCE_OPTIONS.map((opt) => {
          const active = value === opt.value;
          return (
            <TouchableOpacity
              key={opt.value}
              onPress={() => onChange(opt.value)}
              className="flex-row items-center rounded-xl px-3 py-2.5"
              style={{
                backgroundColor: active ? `${metric.color}12` : 'transparent',
                borderWidth: 1,
                borderColor: active ? metric.color : '#1E2A3B',
              }}
              activeOpacity={0.7}
            >
              <View
                className="w-4 h-4 rounded-full border-2 items-center justify-center mr-3"
                style={{ borderColor: active ? metric.color : '#3A4A5C' }}
              >
                {active && (
                  <View
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: metric.color }}
                  />
                )}
              </View>
              <View className="flex-1">
                <Text className="text-[#E8EDF5] text-sm font-sansMedium">{opt.label}</Text>
                <Text className="text-[#526380] text-xs mt-0.5">{opt.sub}</Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Auto heuristic note */}
      {value === 'auto' && (
        <View className="mt-3 flex-row gap-2 bg-[#1E2A3B] rounded-xl px-3 py-2">
          <Ionicons name="information-circle-outline" size={14} color="#526380" style={{ marginTop: 1 }} />
          <Text className="text-[#526380] text-xs leading-4 flex-1">{autoOpt.sub}: {metric.autoHeuristic}</Text>
        </View>
      )}
    </View>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function DataSourcesScreen() {
  const [prefs, setPrefs] = useState<DataSourcePrefs>(DEFAULT_PREFS);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadDataSourcePrefs().then(setPrefs);
  }, []);

  const handleChange = useCallback((key: keyof DataSourcePrefs, val: SourceOption) => {
    setPrefs((p: DataSourcePrefs) => ({ ...p, [key]: val }));
    setSaved(false);
  }, []);

  const handleSave = useCallback(async () => {
    await saveDataSourcePrefs(prefs);
    setSaved(true);
  }, [prefs]);

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 48 }}>
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <Text className="text-xl font-display text-[#E8EDF5] flex-1">Data Sources</Text>
      </View>

      <View className="px-6 pt-5">
        {/* Explainer */}
        <View className="bg-[#1E2A3B] rounded-2xl px-4 py-4 mb-5">
          <Text className="text-[#E8EDF5] text-sm font-sansMedium mb-1">Why this matters</Text>
          <Text className="text-[#526380] text-xs leading-5">
            Different devices measure the same metrics with different methodologies.
            Apple Watch step counting tends to be more accurate than a ring. Oura's
            sleep staging uses dedicated sensors not available in Apple Health.{'\n\n'}
            When both sources have data for the same day, you choose which one your
            insights are built from — or run as a{' '}
            <Text className="text-[#00D4AA]">self-experiment</Text> to compare them.
          </Text>
        </View>

        <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3">
          Per-Metric Priority
        </Text>

        {METRICS.map((m) => (
          <MetricSourceCard
            key={String(m.key)}
            metric={m}
            value={prefs[m.key]}
            onChange={(v) => handleChange(m.key, v)}
          />
        ))}

        {/* When both sources have data, show alt */}
        <View className="bg-surface-raised border border-surface-border rounded-2xl px-4 py-4 mb-5">
          <View className="flex-row items-center gap-2 mb-2">
            <Ionicons name="git-compare-outline" size={16} color="#00D4AA" />
            <Text className="text-[#E8EDF5] text-sm font-sansMedium">Side-by-side comparison</Text>
          </View>
          <Text className="text-[#526380] text-xs leading-5">
            When both sources have data for the same day, the non-primary value is
            shown below the primary one in the Timeline view. This lets you validate
            accuracy or run structured self-experiments.
          </Text>
        </View>

        {/* Save button */}
        <TouchableOpacity
          onPress={handleSave}
          className="rounded-xl py-3.5 items-center mb-3"
          style={{ backgroundColor: saved ? '#1E2A3B' : '#00D4AA' }}
          activeOpacity={0.8}
        >
          <Text
            className="font-sansMedium text-sm"
            style={{ color: saved ? '#6EE7B7' : '#080B10' }}
          >
            {saved ? '✓ Preferences Saved' : 'Save Preferences'}
          </Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}
