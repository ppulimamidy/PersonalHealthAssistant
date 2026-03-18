/**
 * Phase 5: Causal Graph screen.
 * Shows directional cause-effect relationships between nutrition and health metrics,
 * detected via Granger causality testing.
 *
 * GET /api/v1/correlations/causal-graph?days=14
 */

import { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { api } from '@/services/api';
import type { CausalGraph, CausalEdge } from '@/types';
import FirstVisitBanner from '@/components/FirstVisitBanner';

// ─── Strength helpers ──────────────────────────────────────────────────────────

const STRENGTH_CONFIG: Record<CausalEdge['strength'], { color: string; label: string; bg: string }> = {
  strong:   { color: '#F87171', label: 'Strong',   bg: 'rgba(248,113,113,0.1)' },
  moderate: { color: '#F5A623', label: 'Moderate', bg: 'rgba(245,166,35,0.1)' },
  weak:     { color: '#60A5FA', label: 'Weak',     bg: 'rgba(96,165,250,0.1)' },
};

// ─── Edge Card ─────────────────────────────────────────────────────────────────

function EdgeCard({ edge, index }: { readonly edge: CausalEdge; readonly index: number }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = STRENGTH_CONFIG[edge.strength] ?? STRENGTH_CONFIG.weak;
  const dir = edge.correlation >= 0 ? '+' : '–';
  const isGranger = edge.evidence.includes('granger_causality');
  const lagSuffix = edge.optimal_lag_days === 1 ? 'day' : 'days';

  return (
    <TouchableOpacity
      onPress={() => setExpanded((v) => !v)}
      className="bg-surface-raised border border-surface-border rounded-2xl mb-3 overflow-hidden"
      activeOpacity={0.85}
    >
      {/* Rank badge */}
      <View className="absolute top-3 right-3 w-6 h-6 rounded-full items-center justify-center"
        style={{ backgroundColor: 'rgba(255,255,255,0.06)' }}>
        <Text className="text-[#526380] text-xs">{index + 1}</Text>
      </View>

      <View className="p-4">
        {/* Cause → Effect row */}
        <View className="flex-row items-center gap-2 mb-3 pr-8">
          <View className="flex-1 rounded-lg px-3 py-2" style={{ backgroundColor: 'rgba(255,255,255,0.04)' }}>
            <Text className="text-[#526380] text-[10px] uppercase tracking-wider mb-0.5">Cause</Text>
            <Text className="text-[#E8EDF5] text-sm font-sansMedium" numberOfLines={2}>{edge.from_label}</Text>
          </View>

          <View className="items-center gap-0.5">
            <Ionicons name="arrow-forward" size={18} color={cfg.color} />
            {edge.optimal_lag_days > 0 && (
              <Text style={{ color: cfg.color, fontSize: 10 }}>+{edge.optimal_lag_days}d</Text>
            )}
          </View>

          <View className="flex-1 rounded-lg px-3 py-2" style={{ backgroundColor: 'rgba(255,255,255,0.04)' }}>
            <Text className="text-[#526380] text-[10px] uppercase tracking-wider mb-0.5">Effect</Text>
            <Text className="text-[#E8EDF5] text-sm font-sansMedium" numberOfLines={2}>{edge.to_label}</Text>
          </View>
        </View>

        {/* Score chips */}
        <View className="flex-row items-center gap-2 flex-wrap">
          <View className="rounded-full px-2.5 py-1" style={{ backgroundColor: cfg.bg }}>
            <Text style={{ color: cfg.color, fontSize: 11, fontWeight: '500' }}>{cfg.label}</Text>
          </View>
          <Text className="text-[#526380] text-xs">
            Confidence {(edge.causality_score * 100).toFixed(0)}%
          </Text>
          <Text className="text-[#526380] text-xs">
            Linked {dir}{Math.abs(edge.correlation * 100).toFixed(0)}%
          </Text>
          {isGranger && (
            <View className="rounded-full px-2 py-0.5 bg-purple-500/15">
              <Text className="text-purple-400 text-[10px] font-medium">AI Verified</Text>
            </View>
          )}
          <TouchableOpacity onPress={() => setExpanded((v) => !v)} className="ml-auto">
            <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={14} color="#526380" />
          </TouchableOpacity>
        </View>

        {/* Expanded details */}
        {expanded && (
          <View className="mt-3 pt-3 border-t border-surface-border gap-1.5">
            {edge.granger_p_value != null && (
              <Text className="text-[#526380] text-xs">
                <Text className="text-[#8B97A8]">Statistical significance: </Text>
                {edge.granger_p_value.toFixed(4)}
                {edge.granger_p_value < 0.05 ? '  (significant)' : '  (marginal)'}
              </Text>
            )}
            <Text className="text-[#526380] text-xs">
              <Text className="text-[#8B97A8]">Evidence: </Text>
              {edge.evidence.map((e) => e.replaceAll('_', ' ')).join(', ')}
            </Text>
            {edge.optimal_lag_days > 0 && (
              <Text className="text-[#526380] text-xs">
                <Text className="text-[#8B97A8]">Lag: </Text>
                Effect appears {edge.optimal_lag_days} {lagSuffix} after cause
              </Text>
            )}
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

export default function CausalGraphScreen() {
  const [days, setDays] = useState<14 | 30 | 0>(0);
  const [infoOpen, setInfoOpen] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['causal-graph', days],
    queryFn: async () => {
      const { data: resp } = await api.get(`/api/v1/correlations/causal-graph?days=${days}`);
      return resp as CausalGraph;
    },
  });

  const topEdge = data?.edges[0];
  const patternCount = data?.edges.length ?? 0;
  const patternSuffix = patternCount === 1 ? '' : 's';
  const lagDays = topEdge?.optimal_lag_days ?? 0;
  const lagUnit = lagDays === 1 ? 'day' : 'days';
  const lagText = lagDays > 0 ? ` ${lagDays} ${lagUnit} later` : ' the same day';

  return (
    <View className="flex-1 bg-obsidian-900">
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <View className="flex-1">
          <Text className="text-xl font-display text-[#E8EDF5]">Triggers &amp; Causes</Text>
          <Text className="text-[#526380] text-xs mt-0.5">What&apos;s most likely driving your symptoms</Text>
        </View>
        {/* Day selector */}
        <View className="flex-row gap-1 bg-surface-raised border border-surface-border rounded-xl p-1">
          {([14, 30, 0] as const).map((d) => {
            let label: string;
            if (d === 0) {
              label = days === 0 && data ? `All · ${data.days_with_data ?? 0}d` : 'All';
            } else {
              label = `${d}d`;
            }
            return (
              <TouchableOpacity
                key={d}
                onPress={() => setDays(d)}
                className="px-3 py-1.5 rounded-lg"
                style={{ backgroundColor: days === d ? 'rgba(0,212,170,0.12)' : 'transparent' }}
              >
                <Text style={{ color: days === d ? '#00D4AA' : '#526380', fontSize: 12, fontWeight: '500' }}>
                  {label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Outer tab switcher: Patterns / Causes */}
      <View className="flex-row mx-4 mt-3 mb-1 p-1 rounded-xl gap-1"
        style={{ backgroundColor: 'rgba(255,255,255,0.04)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}>
        {([
          { label: 'Patterns', icon: 'analytics-outline' as const },
          { label: 'Causes',   icon: 'git-branch-outline' as const },
        ] as const).map((t) => (
          <TouchableOpacity
            key={t.label}
            onPress={() => {
              if (t.label === 'Patterns') router.back();
            }}
            className="flex-1 flex-row items-center justify-center gap-1.5 py-2 rounded-lg"
            style={{
              backgroundColor: t.label === 'Causes' ? 'rgba(0,212,170,0.12)' : 'transparent',
              borderWidth: t.label === 'Causes' ? 1 : 0,
              borderColor: 'rgba(0,212,170,0.2)',
            }}
            activeOpacity={0.7}
          >
            <Ionicons name={t.icon} size={14} color={t.label === 'Causes' ? '#00D4AA' : '#526380'} />
            <Text className="text-sm font-sansMedium" style={{ color: t.label === 'Causes' ? '#00D4AA' : '#526380' }}>
              {t.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FirstVisitBanner
        screenKey="root_causes"
        text="This shows which factors most influence your symptoms, ranked by strength of connection."
      />
      <ScrollView className="flex-1" contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
        {/* Info explainer */}
        <TouchableOpacity
          onPress={() => setInfoOpen((v) => !v)}
          className="bg-surface-raised border border-surface-border rounded-2xl mb-4 overflow-hidden"
          activeOpacity={0.8}
        >
          <View className="flex-row items-center px-4 py-3 gap-2">
            <Ionicons name="information-circle-outline" size={16} color="#526380" />
            <Text className="text-[#526380] text-sm flex-1">How does this work?</Text>
            <Ionicons name={infoOpen ? 'chevron-up' : 'chevron-down'} size={14} color="#526380" />
          </View>
          {infoOpen && (
            <View className="px-4 pb-4 pt-0">
              <Text className="text-[#526380] text-xs leading-5">
                Causal relationships are detected using{' '}
                <Text className="text-[#8B97A8]">Granger causality testing</Text> — a statistical method that checks
                whether knowing X today helps predict Y tomorrow. A relationship is causal if X consistently precedes
                and predicts Y, not just correlates with it.
              </Text>
              <View className="flex-row flex-wrap gap-2 mt-3">
                {[
                  { label: 'Granger ✓', color: '#A78BFA', bg: 'rgba(167,139,250,0.12)' },
                  { label: 'Temporal', color: '#60A5FA', bg: 'rgba(96,165,250,0.12)' },
                  { label: 'Correlation', color: '#6EE7B7', bg: 'rgba(110,231,183,0.12)' },
                ].map((tag) => (
                  <View key={tag.label} className="rounded-full px-2.5 py-1" style={{ backgroundColor: tag.bg }}>
                    <Text style={{ color: tag.color, fontSize: 11 }}>{tag.label}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}
        </TouchableOpacity>

        {isLoading && (
          <View className="items-center py-16">
            <ActivityIndicator color="#00D4AA" />
            <Text className="text-[#526380] text-sm mt-3">Analyzing causal patterns…</Text>
          </View>
        )}

        {isError && (
          <View className="bg-health-critical/10 border border-health-critical/30 rounded-2xl p-4 items-center">
            <Ionicons name="alert-circle-outline" size={32} color="#F87171" />
            <Text className="text-[#F87171] font-sansMedium mt-2">Failed to load</Text>
            <TouchableOpacity onPress={() => refetch()} className="mt-3 px-4 py-2 bg-surface-raised rounded-xl">
              <Text className="text-[#E8EDF5] text-sm">Retry</Text>
            </TouchableOpacity>
          </View>
        )}

        {!isLoading && !isError && data && (
          <>
            {data.edges.length === 0 ? (
              <View className="items-center py-16">
                <Ionicons name="git-network-outline" size={48} color="#526380" />
                <Text className="text-[#E8EDF5] font-sansMedium mt-4">No Causal Patterns Found</Text>
                <Text className="text-[#526380] text-sm text-center mt-2 px-6">
                  Keep logging meals and syncing your connected devices. Patterns emerge after 7+ days of data.
                </Text>
              </View>
            ) : (
              <>
                {/* Summary banner */}
                <View className="rounded-2xl p-4 mb-4"
                  style={{ backgroundColor: 'rgba(0,212,170,0.06)', borderWidth: 1, borderColor: 'rgba(0,212,170,0.15)' }}>
                  <Text className="text-primary-500 text-xs font-semibold uppercase tracking-wider mb-1">
                    {patternCount} causal pattern{patternSuffix} detected
                  </Text>
                  {topEdge && (
                    <Text className="text-[#E8EDF5] text-sm leading-5">
                      When your <Text className="font-semibold">{topEdge.from_label}</Text> is high,
                      your <Text className="font-semibold">{topEdge.to_label}</Text> tends to{' '}
                      {topEdge.correlation >= 0 ? 'increase' : 'decrease'}
                      {lagText}.
                    </Text>
                  )}
                </View>

                {data.edges.map((edge, i) => (
                  <EdgeCard key={`${edge.from_metric}-${edge.to_metric}`} edge={edge} index={i} />
                ))}

                {data.computed_at && (
                  <Text className="text-[#3D4F66] text-xs text-center mt-2">
                    Computed {format(new Date(data.computed_at), 'MMM d, h:mm a')}
                  </Text>
                )}

                {/* Data sources footnote */}
                {data.data_sources_used && data.data_sources_used.length > 0 && (
                  <View className="mt-4 pt-4 border-t border-surface-border">
                    <Text className="text-[#3D4F66] text-xs leading-4">
                      <Text className="text-[#526380]">Data sources: </Text>
                      {data.data_sources_used.join(', ')}
                    </Text>
                  </View>
                )}
              </>
            )}
          </>
        )}

        {/* Disclaimer */}
        <Text className="text-[#3D4F66] text-xs text-center mt-6 leading-4 px-4">
          Causal relationships are statistical inferences. Consult your healthcare provider before making
          significant lifestyle changes.
        </Text>
      </ScrollView>
    </View>
  );
}
