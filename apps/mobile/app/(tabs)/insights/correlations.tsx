/**
 * Phase 4: Correlations screen.
 * Shows nutrition ↔ health metric correlations with strength indicators.
 * Data: GET /api/v1/correlations?days=30
 */

import { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/services/api';
import { MiniLineChart } from '@/components/MiniLineChart';
import FirstVisitBanner from '@/components/FirstVisitBanner';

// ─── Types ────────────────────────────────────────────────────────────────────

interface DataPoint {
  date: string;
  a_value: number;
  b_value: number;
}

interface Correlation {
  id: string;
  metric_a_label: string;
  metric_b_label: string;
  correlation_coefficient: number;
  p_value: number;
  sample_size: number;
  lag_days: number;
  effect_description: string;
  strength: 'strong' | 'moderate' | 'weak';
  direction: 'positive' | 'negative';
  category: string;
  data_points: DataPoint[];
}

interface CorrelationResults {
  correlations: Correlation[];
  summary: string | null;
  data_quality_score: number;
  oura_days_available: number;
  nutrition_days_available: number;
  days_with_data?: number;
  data_sources_used?: string[];
}

const DAY_OPTIONS = [14, 30] as const;

// ─── Correlation Card ─────────────────────────────────────────────────────────

const STRENGTH_COLOR: Record<string, string> = {
  strong:   '#6EE7B7',
  moderate: '#F5A623',
  weak:     '#526380',
};

function CoefficientBar({ r }: { r: number }) {
  const pct = Math.abs(r) * 100;
  const color = r > 0 ? '#6EE7B7' : '#F87171';

  return (
    <View className="flex-row items-center gap-2">
      {/* Negative side */}
      <View className="flex-1 h-1.5 bg-surface rounded-full overflow-hidden flex-row justify-end">
        {r < 0 && (
          <View className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: '#F87171' }} />
        )}
      </View>
      {/* Center marker */}
      <View className="w-px h-3 bg-[#526380]" />
      {/* Positive side */}
      <View className="flex-1 h-1.5 bg-surface rounded-full overflow-hidden">
        {r > 0 && (
          <View className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: '#6EE7B7' }} />
        )}
      </View>
    </View>
  );
}

function CorrelationCard({ c }: { c: Correlation }) {
  const [expanded, setExpanded] = useState(false);
  const strColor = STRENGTH_COLOR[c.strength] ?? '#526380';
  const coeff = c.correlation_coefficient;

  const aVals = c.data_points?.map((d) => d.a_value) ?? [];
  const bVals = c.data_points?.map((d) => d.b_value) ?? [];

  return (
    <TouchableOpacity
      onPress={() => setExpanded((e) => !e)}
      className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3"
      activeOpacity={0.8}
    >
      {/* Header */}
      <View className="flex-row items-start justify-between mb-2">
        <View className="flex-1 mr-3">
          <Text className="text-[#E8EDF5] font-sansMedium text-sm leading-5">
            {c.metric_a_label}
            <Text className="text-[#526380]"> → </Text>
            {c.metric_b_label}
          </Text>
          {c.lag_days > 0 && (
            <Text className="text-[#526380] text-xs mt-0.5">{c.lag_days}-day lag</Text>
          )}
        </View>
        <View className="items-end">
          <Text className="font-display text-xl" style={{ color: coeff > 0 ? '#6EE7B7' : '#F87171' }}>
            {coeff > 0 ? '+' : ''}{coeff.toFixed(2)}
          </Text>
          <View className="px-2 py-0.5 rounded-full mt-0.5" style={{ backgroundColor: `${strColor}20` }}>
            <Text className="text-xs capitalize font-sansMedium" style={{ color: strColor }}>
              {c.strength}
            </Text>
          </View>
        </View>
      </View>

      <CoefficientBar r={coeff} />

      {c.effect_description && (
        <Text className="text-[#526380] text-xs mt-2 leading-4" numberOfLines={expanded ? undefined : 2}>
          {c.effect_description}
        </Text>
      )}

      {expanded && (
        <>
          <View className="mt-3 pt-3 border-t border-surface-border">
            <View className="flex-row gap-3 justify-between mb-1">
              <Text className="text-[#526380] text-xs">{c.metric_a_label}</Text>
              <Text className="text-[#526380] text-xs">{c.metric_b_label}</Text>
            </View>
            <View className="flex-row gap-3">
              {aVals.length >= 2 && (
                <View className="flex-1">
                  <MiniLineChart data={aVals} color="#818CF8" height={48} width={130} />
                </View>
              )}
              {bVals.length >= 2 && (
                <View className="flex-1">
                  <MiniLineChart data={bVals} color="#6EE7B7" height={48} width={130} />
                </View>
              )}
            </View>
          </View>
          <View className="flex-row gap-4 mt-2">
            <Text className="text-[#526380] text-xs">p={c.p_value < 0.001 ? '<0.001' : c.p_value.toFixed(3)}</Text>
            <Text className="text-[#526380] text-xs">n={c.sample_size}</Text>
          </View>
        </>
      )}

      <Ionicons
        name={expanded ? 'chevron-up' : 'chevron-down'}
        size={14}
        color="#526380"
        style={{ alignSelf: 'center', marginTop: 4 }}
      />
    </TouchableOpacity>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

type ViewTab = 'patterns' | 'causes';

export default function CorrelationsScreen() {
  const [days, setDays] = useState<14 | 30>(30);
  const [viewTab, setViewTab] = useState<ViewTab>('patterns');

  const { data, isLoading, refetch, isRefetching } = useQuery<CorrelationResults>({
    queryKey: ['correlations', days],
    queryFn: async () => {
      const { data: resp } = await api.get(`/api/v1/correlations?days=${days}`);
      return resp;
    },
  });

  const correlations = data?.correlations ?? [];

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <View className="flex-1">
          <Text className="text-xl font-display text-[#E8EDF5]">Triggers &amp; Causes</Text>
          <Text className="text-[#526380] text-xs mt-0.5">What's connected to how you feel</Text>
        </View>
        {viewTab === 'patterns' && (
          <>
            <View className="flex-row gap-1 mr-2">
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
            <TouchableOpacity onPress={() => refetch()} disabled={isRefetching}>
              <Ionicons name="refresh-outline" size={20} color={isRefetching ? '#526380' : '#00D4AA'} />
            </TouchableOpacity>
          </>
        )}
      </View>

      {/* Tab switcher */}
      <View className="flex-row mx-6 mt-4 mb-1 p-1 rounded-xl gap-1"
        style={{ backgroundColor: 'rgba(255,255,255,0.04)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}>
        {([
          { key: 'patterns' as ViewTab, label: 'Patterns', icon: 'analytics-outline' as const },
          { key: 'causes'   as ViewTab, label: 'Causes',   icon: 'git-branch-outline' as const },
        ] as const).map((t) => (
          <TouchableOpacity
            key={t.key}
            onPress={() => {
              if (t.key === 'causes') {
                router.push('/(tabs)/insights/causal-graph');
              } else {
                setViewTab(t.key);
              }
            }}
            className="flex-1 flex-row items-center justify-center gap-1.5 py-2 rounded-lg"
            style={{
              backgroundColor: viewTab === t.key ? 'rgba(0,212,170,0.12)' : 'transparent',
              borderWidth: viewTab === t.key ? 1 : 0,
              borderColor: 'rgba(0,212,170,0.2)',
            }}
            activeOpacity={0.7}
          >
            <Ionicons name={t.icon} size={14} color={viewTab === t.key ? '#00D4AA' : '#526380'} />
            <Text className="text-sm font-sansMedium" style={{ color: viewTab === t.key ? '#00D4AA' : '#526380' }}>
              {t.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FirstVisitBanner
        screenKey="symptom_triggers"
        text="We analyze your logs to find what correlates with you feeling better or worse."
      />

      <View className="px-6 pt-5">
        {/* Data quality */}
        {data && (
          <View className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 mb-4 flex-row items-center justify-between">
            <Text className="text-[#526380] text-xs">Data quality</Text>
            <View className="flex-row items-center gap-3">
              <Text className="text-[#526380] text-xs">
                {data.oura_days_available}d wearable · {data.nutrition_days_available}d nutrition
              </Text>
              <View
                className="w-2.5 h-2.5 rounded-full"
                style={{
                  backgroundColor:
                    data.data_quality_score >= 0.7 ? '#6EE7B7' :
                    data.data_quality_score >= 0.4 ? '#F5A623' : '#F87171',
                }}
              />
            </View>
          </View>
        )}

        {/* AI summary */}
        {data?.summary && (
          <View className="bg-primary-500/10 border border-primary-500/30 rounded-xl px-4 py-3 mb-4">
            <View className="flex-row items-center gap-2 mb-1.5">
              <Ionicons name="bulb-outline" size={14} color="#00D4AA" />
              <Text className="text-primary-500 text-xs font-sansMedium">AI Summary</Text>
            </View>
            <Text className="text-[#E8EDF5] text-sm leading-5">{data.summary}</Text>
          </View>
        )}

        {isLoading ? (
          <ActivityIndicator color="#00D4AA" className="mt-6" />
        ) : correlations.length === 0 ? (
          <View className="items-center py-16">
            <Ionicons name="git-branch-outline" size={44} color="#526380" />
            <Text className="text-[#526380] text-base mt-3">No correlations found</Text>
            <Text className="text-[#526380] text-sm mt-1 text-center">
              Log nutrition data and connect a wearable to discover patterns
            </Text>
          </View>
        ) : (
          correlations.map((c) => <CorrelationCard key={c.id} c={c} />)
        )}

        {/* Data sources footnote */}
        {data && (
          <View className="mt-4 pt-4 border-t border-surface-border">
            <Text className="text-[#3D4F66] text-xs leading-4">
              <Text className="text-[#526380]">Data sources: </Text>
              {data.data_sources_used && data.data_sources_used.length > 0
                ? data.data_sources_used.join(', ')
                : [
                    data.oura_days_available > 0 ? 'Oura Ring' : null,
                    data.nutrition_days_available > 0 ? 'Nutrition Logs' : null,
                  ].filter(Boolean).join(', ') || 'No data sources connected'
              }
              {(data.days_with_data ?? data.oura_days_available) > 0
                ? ` · ${data.days_with_data ?? data.oura_days_available} days analyzed`
                : ''}
            </Text>
          </View>
        )}
      </View>
    </ScrollView>
  );
}
