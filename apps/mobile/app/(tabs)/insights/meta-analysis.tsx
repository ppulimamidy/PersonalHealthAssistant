/**
 * Phase 5: Meta-Analysis Report screen.
 * Comprehensive health analysis by specialist AI agents across all domains.
 * 4 tabs: Overview, Specialists, Patterns, Protocol.
 *
 * GET /api/v1/specialist-agents/meta-analysis/cached
 * POST /api/v1/specialist-agents/meta-analysis/generate (body: { days: 30 })
 */

import { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, ActivityIndicator,
  Alert,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { api } from '@/services/api';
import FirstVisitBanner from '@/components/FirstVisitBanner';
import type {
  MetaAnalysisReport, SpecialistInsight, CrossSystemPattern,
  EvidenceBasedRecommendation,
} from '@/types';

// ─── Tab types ─────────────────────────────────────────────────────────────────

type Tab = 'overview' | 'specialists' | 'patterns' | 'protocol';

const TABS: Array<{ key: Tab; label: string; icon: React.ComponentProps<typeof Ionicons>['name'] }> = [
  { key: 'overview',    label: 'Overview',    icon: 'stats-chart-outline' },
  { key: 'specialists', label: 'Specialists', icon: 'people-outline' },
  { key: 'patterns',    label: 'Patterns',    icon: 'git-network-outline' },
  { key: 'protocol',    label: 'Action Plan', icon: 'clipboard-outline' },
];

// ─── Priority / evidence helpers ──────────────────────────────────────────────

const PRIORITY_CONFIG: Record<string, { color: string; bg: string }> = {
  critical: { color: '#F87171', bg: 'rgba(248,113,113,0.1)' },
  high:     { color: '#F5A623', bg: 'rgba(245,166,35,0.1)' },
  medium:   { color: '#6EE7B7', bg: 'rgba(110,231,183,0.1)' },
  low:      { color: '#526380', bg: 'rgba(82,99,128,0.1)' },
};

const STRENGTH_COLOR: Record<string, string> = {
  strong:   '#F87171',
  moderate: '#F5A623',
  weak:     '#60A5FA',
};

// ─── Sub-components ────────────────────────────────────────────────────────────

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <View className="flex-1 bg-surface-raised border border-surface-border rounded-2xl p-4 items-center">
      <Text className="text-[#526380] text-xs uppercase tracking-wider mb-1" numberOfLines={1}>{label}</Text>
      <Text className="text-[#E8EDF5] text-2xl font-display">{value}</Text>
      {sub && <Text className="text-[#526380] text-xs mt-1">{sub}</Text>}
    </View>
  );
}

function OverviewTab({ report }: { report: MetaAnalysisReport }) {
  return (
    <View className="gap-4">
      {/* Stat cards */}
      <View className="flex-row gap-3">
        <StatCard label="Period" value={`${report.analysis_period_days}d`} />
        <StatCard label="Confidence" value={`${(report.overall_confidence * 100).toFixed(0)}%`} />
        <StatCard label="Data" value={`${(report.data_completeness * 100).toFixed(0)}%`} sub="completeness" />
      </View>

      {/* Primary diagnosis */}
      <View className="bg-surface-raised border border-surface-border rounded-2xl p-4">
        <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Primary Finding</Text>
        <Text className="text-[#E8EDF5] font-sansMedium text-base mb-2">{report.primary_diagnosis.diagnosis}</Text>
        <View className="flex-row flex-wrap gap-2 mb-3">
          {report.primary_diagnosis.systems_involved.map((s) => (
            <View key={s} className="rounded-full px-2.5 py-1 bg-primary-500/10">
              <Text className="text-primary-500 text-xs">{s}</Text>
            </View>
          ))}
        </View>
        <Text className="text-[#526380] text-xs">
          Confidence: {(report.primary_diagnosis.confidence * 100).toFixed(0)}%
        </Text>
        {report.primary_diagnosis.causal_chain.length > 0 && (
          <View className="mt-3 pt-3 border-t border-surface-border">
            <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">How This Connects</Text>
            <View className="gap-1">
              {report.primary_diagnosis.causal_chain.map((step, i) => (
                <View key={i} className="flex-row items-start gap-2">
                  <Text className="text-primary-500 text-xs mt-0.5">{i + 1}.</Text>
                  <Text className="text-[#8B97A8] text-xs leading-4 flex-1">{step}</Text>
                </View>
              ))}
            </View>
          </View>
        )}
      </View>

      {/* Secondary diagnoses */}
      {report.secondary_diagnoses.length > 0 && (
        <View className="bg-surface-raised border border-surface-border rounded-2xl p-4">
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3">Secondary Findings</Text>
          {report.secondary_diagnoses.map((d, i) => (
            <View key={i} className={i > 0 ? 'mt-3 pt-3 border-t border-surface-border' : ''}>
              <Text className="text-[#E8EDF5] text-sm font-sansMedium">{d.diagnosis}</Text>
              <View className="flex-row flex-wrap gap-1.5 mt-1">
                {d.systems_involved.map((s) => (
                  <View key={s} className="rounded-full px-2 py-0.5" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }}>
                    <Text className="text-[#526380] text-[10px]">{s}</Text>
                  </View>
                ))}
                <Text className="text-[#526380] text-xs ml-auto">{(d.confidence * 100).toFixed(0)}%</Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Evidence quality */}
      <View className="bg-surface-raised border border-surface-border rounded-2xl p-4">
        <Text className="text-[#526380] text-xs uppercase tracking-wider mb-1">Evidence Quality</Text>
        <Text className="text-[#E8EDF5] font-sansMedium capitalize">{report.evidence_quality}</Text>
        <Text className="text-[#526380] text-xs mt-1">
          Generated {format(new Date(report.generated_at), 'MMM d, yyyy h:mm a')}
        </Text>
      </View>
    </View>
  );
}

function SpecialistsTab({ insights }: { insights: SpecialistInsight[] }) {
  const [expanded, setExpanded] = useState<number | null>(0);

  return (
    <View className="gap-3">
      {insights.map((insight, i) => (
        <TouchableOpacity
          key={i}
          onPress={() => setExpanded(expanded === i ? null : i)}
          className="bg-surface-raised border border-surface-border rounded-2xl overflow-hidden"
          activeOpacity={0.85}
        >
          <View className="flex-row items-center p-4 gap-3">
            <View className="w-10 h-10 rounded-xl bg-primary-500/10 items-center justify-center">
              <Ionicons name="person-outline" size={20} color="#00D4AA" />
            </View>
            <View className="flex-1">
              <Text className="text-[#E8EDF5] font-sansMedium">{insight.specialist_name}</Text>
              <Text className="text-[#526380] text-xs mt-0.5">
                {insight.findings.length} finding{insight.findings.length !== 1 ? 's' : ''} ·{' '}
                {(insight.confidence_score * 100).toFixed(0)}% confidence
              </Text>
            </View>
            <Ionicons name={expanded === i ? 'chevron-up' : 'chevron-down'} size={16} color="#526380" />
          </View>

          {expanded === i && (
            <View className="px-4 pb-4 border-t border-surface-border pt-3 gap-3">
              {insight.findings.length > 0 && (
                <View>
                  <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Findings</Text>
                  {insight.findings.map((f, fi) => (
                    <View key={fi} className="flex-row items-start gap-2 mb-1.5">
                      <Ionicons name="checkmark-circle-outline" size={14} color="#6EE7B7" style={{ marginTop: 1 }} />
                      <Text className="text-[#8B97A8] text-sm leading-5 flex-1">{f}</Text>
                    </View>
                  ))}
                </View>
              )}
              {insight.concerns.length > 0 && (
                <View>
                  <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Concerns</Text>
                  {insight.concerns.map((c, ci) => (
                    <View key={ci} className="flex-row items-start gap-2 mb-1.5">
                      <Ionicons name="alert-circle-outline" size={14} color="#F5A623" style={{ marginTop: 1 }} />
                      <Text className="text-[#8B97A8] text-sm leading-5 flex-1">{c}</Text>
                    </View>
                  ))}
                </View>
              )}
              <Text className="text-[#526380] text-xs">
                Data quality: {(insight.data_quality * 100).toFixed(0)}%
              </Text>
            </View>
          )}
        </TouchableOpacity>
      ))}
    </View>
  );
}

function PatternsTab({ patterns }: { patterns: CrossSystemPattern[] }) {
  const PATTERN_ICONS: Record<string, React.ComponentProps<typeof Ionicons>['name']> = {
    causal_chain:           'git-branch-outline',
    feedback_loop:          'refresh-outline',
    synergistic_effect:     'add-circle-outline',
    antagonistic_interaction: 'remove-circle-outline',
  };

  return (
    <View className="gap-3">
      {patterns.length === 0 && (
        <View className="items-center py-12">
          <Ionicons name="git-network-outline" size={40} color="#526380" />
          <Text className="text-[#526380] text-sm mt-3">No cross-system patterns detected</Text>
        </View>
      )}
      {patterns.map((p, i) => (
        <View key={i} className="bg-surface-raised border border-surface-border rounded-2xl p-4">
          <View className="flex-row items-start gap-3 mb-3">
            <View className="w-9 h-9 rounded-xl items-center justify-center"
              style={{ backgroundColor: `${STRENGTH_COLOR[p.strength] ?? '#526380'}18` }}>
              <Ionicons name={PATTERN_ICONS[p.pattern_type] ?? 'git-network-outline'} size={18}
                color={STRENGTH_COLOR[p.strength] ?? '#526380'} />
            </View>
            <View className="flex-1">
              <Text className="text-[#E8EDF5] text-sm font-sansMedium">
                {p.pattern_type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              </Text>
              <View className="flex-row flex-wrap gap-1.5 mt-1">
                {p.systems_involved.map((s) => (
                  <View key={s} className="rounded-full px-2 py-0.5 bg-primary-500/10">
                    <Text className="text-primary-500 text-[10px]">{s}</Text>
                  </View>
                ))}
              </View>
            </View>
            <View className="rounded-full px-2 py-0.5"
              style={{ backgroundColor: `${STRENGTH_COLOR[p.strength] ?? '#526380'}18` }}>
              <Text style={{ color: STRENGTH_COLOR[p.strength] ?? '#526380', fontSize: 10, fontWeight: '500' }}>
                {p.strength}
              </Text>
            </View>
          </View>
          <Text className="text-[#8B97A8] text-sm leading-5">{p.pattern_description}</Text>
          {p.clinical_significance && (
            <View className="mt-3 pt-3 border-t border-surface-border">
              <Text className="text-[#526380] text-xs">
                <Text className="text-[#8B97A8]">Significance: </Text>{p.clinical_significance}
              </Text>
            </View>
          )}
        </View>
      ))}
    </View>
  );
}

function ProtocolTab({ recommendations }: { recommendations: EvidenceBasedRecommendation[] }) {
  const sorted = [...recommendations].sort((a, b) => b.estimated_impact - a.estimated_impact);

  return (
    <View className="gap-3">
      {sorted.length === 0 && (
        <View className="items-center py-12">
          <Ionicons name="clipboard-outline" size={40} color="#526380" />
          <Text className="text-[#526380] text-sm mt-3">No action items yet</Text>
        </View>
      )}
      {sorted.map((rec, i) => {
        const cfg = PRIORITY_CONFIG[rec.priority] ?? PRIORITY_CONFIG.low;
        return (
          <View key={i} className="bg-surface-raised border border-surface-border rounded-2xl p-4">
            <View className="flex-row items-start justify-between gap-2 mb-2">
              <Text className="text-[#E8EDF5] font-sansMedium flex-1 leading-5">{rec.action}</Text>
              <View className="rounded-full px-2.5 py-1 flex-shrink-0" style={{ backgroundColor: cfg.bg }}>
                <Text style={{ color: cfg.color, fontSize: 11, fontWeight: '500' }}>
                  {rec.priority.toUpperCase()}
                </Text>
              </View>
            </View>
            <Text className="text-[#526380] text-sm leading-5 mb-3">{rec.rationale}</Text>
            <View className="flex-row flex-wrap gap-2 mb-2">
              <View className="flex-row items-center gap-1 rounded-full px-2.5 py-1" style={{ backgroundColor: 'rgba(255,255,255,0.04)' }}>
                <Ionicons name="library-outline" size={11} color="#526380" />
                <Text className="text-[#526380] text-xs">{rec.evidence_level}</Text>
              </View>
              <View className="flex-row items-center gap-1 rounded-full px-2.5 py-1" style={{ backgroundColor: 'rgba(255,255,255,0.04)' }}>
                <Ionicons name="flash-outline" size={11} color="#526380" />
                <Text className="text-[#526380] text-xs">{rec.implementation_difficulty}</Text>
              </View>
              <View className="flex-row items-center gap-1 rounded-full px-2.5 py-1" style={{ backgroundColor: 'rgba(0,212,170,0.06)' }}>
                <Ionicons name="trending-up-outline" size={11} color="#00D4AA" />
                <Text className="text-primary-500 text-xs">Impact {(rec.estimated_impact * 100).toFixed(0)}%</Text>
              </View>
            </View>
            {rec.expected_benefit && (
              <Text className="text-[#526380] text-xs leading-4">
                <Text className="text-[#8B97A8]">Expected: </Text>{rec.expected_benefit}
              </Text>
            )}
          </View>
        );
      })}
    </View>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

export default function MetaAnalysisScreen() {
  const [tab, setTab] = useState<Tab>('overview');
  const queryClient = useQueryClient();

  const { data: report, isLoading } = useQuery({
    queryKey: ['meta-analysis', 'latest'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/specialist-agents/meta-analysis/latest');
      return resp as MetaAnalysisReport | null;
    },
  });

  const { mutate: generate, isPending: isGenerating } = useMutation({
    mutationFn: async () => {
      const { data: resp } = await api.post('/api/v1/specialist-agents/meta-analysis', { days: 30 });
      return resp as MetaAnalysisReport;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['meta-analysis', 'latest'], data);
    },
    onError: () => {
      Alert.alert('Analysis Failed', 'Could not generate meta-analysis. Please try again.');
    },
  });

  return (
    <View className="flex-1 bg-obsidian-900">
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <View className="flex-1">
          <Text className="text-xl font-display text-[#E8EDF5]">Research</Text>
          <Text className="text-[#526380] text-xs mt-0.5">Evidence-based insights for your patterns</Text>
        </View>
        <TouchableOpacity
          onPress={() => generate()}
          disabled={isGenerating}
          className="flex-row items-center gap-1.5 rounded-xl px-3 py-2"
          style={{ backgroundColor: isGenerating ? 'rgba(0,212,170,0.06)' : 'rgba(0,212,170,0.12)' }}
          activeOpacity={0.7}
        >
          {isGenerating ? (
            <ActivityIndicator size="small" color="#00D4AA" />
          ) : (
            <Ionicons name="refresh-outline" size={16} color="#00D4AA" />
          )}
          <Text className="text-primary-500 text-xs font-sansMedium">
            {isGenerating ? 'Analyzing…' : 'Regenerate'}
          </Text>
        </TouchableOpacity>
      </View>

      <FirstVisitBanner
        screenKey="research_evidence"
        text="We match your health patterns against published medical studies relevant to your conditions."
      />

      {/* Outer tab switcher: AI Analysis / Literature Search */}
      <View className="flex-row mx-4 mt-3 mb-1 p-1 rounded-xl gap-1"
        style={{ backgroundColor: 'rgba(255,255,255,0.04)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}>
        {([
          { label: 'AI Analysis',       icon: 'analytics-outline' as const },
          { label: 'Literature Search', icon: 'library-outline'   as const },
        ] as const).map((t) => (
          <TouchableOpacity
            key={t.label}
            onPress={() => {
              if (t.label === 'Literature Search') {
                router.push('/(tabs)/insights/research');
              }
            }}
            className="flex-1 flex-row items-center justify-center gap-1.5 py-2 rounded-lg"
            style={{
              backgroundColor: t.label === 'AI Analysis' ? 'rgba(0,212,170,0.12)' : 'transparent',
              borderWidth: t.label === 'AI Analysis' ? 1 : 0,
              borderColor: 'rgba(0,212,170,0.2)',
            }}
            activeOpacity={0.7}
          >
            <Ionicons name={t.icon} size={14} color={t.label === 'AI Analysis' ? '#00D4AA' : '#526380'} />
            <Text className="text-sm font-sansMedium" style={{ color: t.label === 'AI Analysis' ? '#00D4AA' : '#526380' }}>
              {t.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Loading / empty state */}
      {isLoading && (
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator color="#00D4AA" />
          <Text className="text-[#526380] text-sm mt-3">Loading report…</Text>
        </View>
      )}

      {isGenerating && (
        <View className="mx-6 mt-4 rounded-2xl p-4 flex-row items-center gap-3"
          style={{ backgroundColor: 'rgba(0,212,170,0.06)', borderWidth: 1, borderColor: 'rgba(0,212,170,0.15)' }}>
          <ActivityIndicator size="small" color="#00D4AA" />
          <View>
            <Text className="text-primary-500 font-sansMedium text-sm">Analyzing your patterns…</Text>
            <Text className="text-[#526380] text-xs mt-0.5">This may take 30–60 seconds</Text>
          </View>
        </View>
      )}

      {!isLoading && !report && !isGenerating && (
        <View className="flex-1 items-center justify-center px-8">
          <View className="w-20 h-20 rounded-full bg-primary-500/10 items-center justify-center mb-5">
            <Ionicons name="analytics-outline" size={40} color="#00D4AA" />
          </View>
          <Text className="text-[#E8EDF5] text-lg font-sansMedium text-center mb-2">No Report Yet</Text>
          <Text className="text-[#526380] text-sm text-center leading-5 mb-6">
            Generate a comprehensive health analysis across all domains — sleep, nutrition, activity, mental health, and more.
          </Text>
          <TouchableOpacity
            onPress={() => generate()}
            className="bg-primary-500 rounded-2xl px-6 py-3.5"
            activeOpacity={0.8}
          >
            <Text className="text-obsidian-900 font-sansMedium">Generate Meta-Analysis</Text>
          </TouchableOpacity>
          <Text className="text-[#3D4F66] text-xs text-center mt-3">Takes ~30–60 seconds</Text>
        </View>
      )}

      {!isLoading && report && (
        <>
          {/* Tab bar */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 12, gap: 8 }}
          >
            {TABS.map((t) => (
              <TouchableOpacity
                key={t.key}
                onPress={() => setTab(t.key)}
                className="flex-row items-center gap-1.5 rounded-xl px-3 py-2"
                style={{
                  backgroundColor: tab === t.key ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.04)',
                  borderWidth: 1,
                  borderColor: tab === t.key ? 'rgba(0,212,170,0.25)' : 'rgba(255,255,255,0.06)',
                }}
                activeOpacity={0.7}
              >
                <Ionicons name={t.icon} size={14} color={tab === t.key ? '#00D4AA' : '#526380'} />
                <Text style={{ color: tab === t.key ? '#00D4AA' : '#526380', fontSize: 13, fontWeight: '500' }}>
                  {t.label}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          <ScrollView className="flex-1" contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
            {tab === 'overview'    && <OverviewTab report={report} />}
            {tab === 'specialists' && <SpecialistsTab insights={report.specialist_insights} />}
            {tab === 'patterns'    && <PatternsTab patterns={report.cross_system_patterns} />}
            {tab === 'protocol'    && <ProtocolTab recommendations={report.recommended_protocol} />}
          </ScrollView>
        </>
      )}
    </View>
  );
}
