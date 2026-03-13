/**
 * Phase 3: Doctor Prep Report screen.
 *
 * Generates a comprehensive health report and allows PDF export via
 * expo-file-system + expo-sharing (share sheet).
 *
 * POST /api/v1/doctor-prep/generate
 * GET  /api/v1/doctor-prep/reports
 * GET  /api/v1/doctor-prep/reports/{id}/pdf  (streaming → downloaded to cache)
 */

import { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity,
  ActivityIndicator, Alert,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons as Icon } from '@expo/vector-icons';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import { format } from 'date-fns';
import { api } from '@/services/api';

// ─── Types ────────────────────────────────────────────────────────────────────

interface ReportSummary {
  id: string;
  generated_at: string;
  date_range: { start: string; end: string };
  summary?: {
    overall_health_score?: number;
    concerns?: string[];
    improvements?: string[];
  };
}

interface HealthReport extends ReportSummary {
  summary: {
    overall_health_score: number;
    key_metrics: Array<{ name: string; value: number | string; unit: string; status: string }>;
    trends: Array<{ metric: string; direction: string; percentage_change: number }>;
    concerns: string[];
    improvements: string[];
  };
  health_intelligence?: {
    sleep_score_trend?: string;
    hrv_trend?: string;
    nutrition_quality_score?: number;
    inflammation_risk?: string;
    stress_index?: number;
    personalized_actions?: string[];
  };
  condition_specific_notes?: string[];
  care_plan_progress?: Array<{
    title: string;
    target_value: number;
    target_unit: string;
    current_value?: number;
    progress_pct: number;
    on_track: boolean;
  }>;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const STATUS_COLOR: Record<string, string> = {
  excellent: '#6EE7B7',
  good:      '#00D4AA',
  moderate:  '#F5A623',
  poor:      '#F87171',
};

const DIRECTION_ICON: Record<string, string> = {
  improving: 'trending-up',
  declining: 'trending-down',
  stable:    'remove',
};

const DIRECTION_COLOR: Record<string, string> = {
  improving: '#6EE7B7',
  declining: '#F87171',
  stable:    '#526380',
};

function ScoreRing({ score }: { score: number }) {
  const color = score >= 80 ? '#6EE7B7' : score >= 60 ? '#F5A623' : '#F87171';
  return (
    <View className="items-center justify-center w-24 h-24 rounded-full border-4" style={{ borderColor: color }}>
      <Text className="text-3xl font-display" style={{ color }}>{Math.round(score)}</Text>
      <Text className="text-[#526380] text-xs">/ 100</Text>
    </View>
  );
}

// ─── Report Detail ────────────────────────────────────────────────────────────

function ReportDetail({ report }: { report: HealthReport }) {
  const [downloading, setDownloading] = useState(false);

  async function handleSharePDF() {
    const canShare = await Sharing.isAvailableAsync();
    if (!canShare) {
      Alert.alert('Not supported', 'Sharing is not available on this device.');
      return;
    }

    setDownloading(true);
    try {
      // Fetch the PDF — streaming download to cache
      const token = (await import('@/lib/supabase')).supabase.auth.getSession().then((s) => s.data.session?.access_token);
      const accessToken = await token;

      const apiBase = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8100';
      const url = `${apiBase}/api/v1/doctor-prep/reports/${report.id}/pdf`;
      const localUri = `${FileSystem.cacheDirectory}health-report-${report.id}.pdf`;

      const dl = await FileSystem.downloadAsync(url, localUri, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      if (dl.status !== 200) {
        throw new Error('PDF download failed');
      }

      await Sharing.shareAsync(dl.uri, {
        mimeType: 'application/pdf',
        dialogTitle: 'Share Health Report',
        UTI: 'com.adobe.pdf',
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Could not download PDF';
      Alert.alert('Export Error', msg);
    } finally {
      setDownloading(false);
    }
  }

  const { summary, health_intelligence: hi, condition_specific_notes, care_plan_progress } = report;

  return (
    <View>
      {/* Score + period */}
      <View className="bg-surface-raised border border-surface-border rounded-2xl p-5 mb-4">
        <View className="flex-row items-center gap-4 mb-4">
          <ScoreRing score={summary.overall_health_score} />
          <View className="flex-1">
            <Text className="text-[#E8EDF5] font-sansMedium text-base">Overall Health Score</Text>
            <Text className="text-[#526380] text-xs mt-1">
              {format(new Date(report.date_range.start), 'MMM d')} –{' '}
              {format(new Date(report.date_range.end), 'MMM d, yyyy')}
            </Text>
            <Text className="text-[#526380] text-xs mt-1">
              Generated {format(new Date(report.generated_at), 'MMM d, h:mm a')}
            </Text>
          </View>
        </View>

        <TouchableOpacity
          onPress={handleSharePDF}
          disabled={downloading}
          className="bg-primary-500 rounded-xl py-3 items-center flex-row justify-center gap-2"
          activeOpacity={0.8}
        >
          {downloading ? (
            <>
              <ActivityIndicator size="small" color="#080B10" />
              <Text className="text-obsidian-900 font-sansMedium">Preparing PDF…</Text>
            </>
          ) : (
            <>
              <Icon name="share-outline" size={18} color="#080B10" />
              <Text className="text-obsidian-900 font-sansMedium">Export & Share PDF</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      {/* Key metrics */}
      {summary.key_metrics?.length > 0 && (
        <View className="mb-4">
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Key Metrics</Text>
          <View className="flex-row flex-wrap gap-2">
            {summary.key_metrics.map((m, i) => {
              const color = STATUS_COLOR[m.status] ?? '#526380';
              return (
                <View key={i} className="bg-surface-raised border border-surface-border rounded-xl p-3 flex-1" style={{ minWidth: '45%' }}>
                  <Text className="text-[#526380] text-xs mb-1">{m.name}</Text>
                  <Text className="text-[#E8EDF5] font-sansMedium">
                    {m.value} <Text className="text-xs text-[#526380]">{m.unit}</Text>
                  </Text>
                  <View className="mt-1 px-2 py-0.5 rounded self-start" style={{ backgroundColor: `${color}20` }}>
                    <Text className="text-xs capitalize" style={{ color }}>{m.status}</Text>
                  </View>
                </View>
              );
            })}
          </View>
        </View>
      )}

      {/* Trends */}
      {summary.trends?.length > 0 && (
        <View className="mb-4">
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Trends</Text>
          <View className="bg-surface-raised border border-surface-border rounded-xl p-4 gap-3">
            {summary.trends.map((t, i) => {
              const color = DIRECTION_COLOR[t.direction] ?? '#526380';
              const iconName = (DIRECTION_ICON[t.direction] ?? 'remove') as any;
              return (
                <View key={i} className="flex-row items-center justify-between">
                  <Text className="text-[#E8EDF5] text-sm flex-1">{t.metric}</Text>
                  <View className="flex-row items-center gap-1.5">
                    <Icon name={iconName} size={16} color={color} />
                    <Text className="text-sm font-sansMedium capitalize" style={{ color }}>{t.direction}</Text>
                    {t.percentage_change !== 0 && (
                      <Text className="text-xs" style={{ color }}>
                        ({t.percentage_change > 0 ? '+' : ''}{t.percentage_change.toFixed(1)}%)
                      </Text>
                    )}
                  </View>
                </View>
              );
            })}
          </View>
        </View>
      )}

      {/* Concerns */}
      {summary.concerns?.length > 0 && (
        <View className="mb-4">
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Concerns</Text>
          <View className="bg-health-critical/10 border border-health-critical/30 rounded-xl p-4 gap-2">
            {summary.concerns.map((c, i) => (
              <View key={i} className="flex-row items-start gap-2">
                <Icon name="warning-outline" size={14} color="#F87171" style={{ marginTop: 1 }} />
                <Text className="text-[#E8EDF5] text-sm flex-1 leading-5">{c}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Improvements */}
      {summary.improvements?.length > 0 && (
        <View className="mb-4">
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Improvements</Text>
          <View className="bg-primary-500/10 border border-primary-500/30 rounded-xl p-4 gap-2">
            {summary.improvements.map((c, i) => (
              <View key={i} className="flex-row items-start gap-2">
                <Icon name="checkmark-circle-outline" size={14} color="#00D4AA" style={{ marginTop: 1 }} />
                <Text className="text-[#E8EDF5] text-sm flex-1 leading-5">{c}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Personalized actions */}
      {hi?.personalized_actions && hi.personalized_actions.length > 0 && (
        <View className="mb-4">
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">AI Recommendations</Text>
          <View className="bg-surface-raised border border-surface-border rounded-xl p-4 gap-2">
            {hi.personalized_actions.map((a, i) => (
              <View key={i} className="flex-row items-start gap-2">
                <Icon name="bulb-outline" size={14} color="#F5A623" style={{ marginTop: 1 }} />
                <Text className="text-[#E8EDF5] text-sm flex-1 leading-5">{a}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Care plan progress */}
      {care_plan_progress && care_plan_progress.length > 0 && (
        <View className="mb-4">
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Care Plan Progress</Text>
          <View className="gap-2">
            {care_plan_progress.map((p, i) => {
              const pct = Math.min(p.progress_pct, 100);
              const color = p.on_track ? '#6EE7B7' : '#F5A623';
              return (
                <View key={i} className="bg-surface-raised border border-surface-border rounded-xl p-4">
                  <View className="flex-row items-center justify-between mb-2">
                    <Text className="text-[#E8EDF5] text-sm font-sansMedium flex-1">{p.title}</Text>
                    <Text className="text-xs" style={{ color }}>{p.on_track ? 'On track' : 'Needs attention'}</Text>
                  </View>
                  <View className="h-1.5 bg-surface rounded-full overflow-hidden">
                    <View className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
                  </View>
                  <Text className="text-[#526380] text-xs mt-1">{Math.round(pct)}% complete</Text>
                </View>
              );
            })}
          </View>
        </View>
      )}
    </View>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

const DAY_OPTIONS = [7, 30, 90] as const;

export default function DoctorPrepScreen() {
  const queryClient = useQueryClient();
  const [days, setDays] = useState<7 | 30 | 90>(30);
  const [activeReport, setActiveReport] = useState<HealthReport | null>(null);

  const { data: reports, isLoading: listLoading } = useQuery<ReportSummary[]>({
    queryKey: ['doctor-prep-reports'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/doctor-prep/reports');
      return (data?.reports ?? data ?? []) as ReportSummary[];
    },
  });

  const generateMutation = useMutation({
    mutationFn: async (d: number) => {
      const { data } = await api.post('/api/v1/doctor-prep/generate', { days: d });
      return data as HealthReport;
    },
    onSuccess: (report) => {
      setActiveReport(report);
      queryClient.invalidateQueries({ queryKey: ['doctor-prep-reports'] });
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : 'Failed to generate report';
      Alert.alert('Generation Error', msg);
    },
  });

  async function loadReport(id: string) {
    try {
      const { data } = await api.get(`/api/v1/doctor-prep/reports/${id}`);
      setActiveReport(data as HealthReport);
    } catch {
      Alert.alert('Error', 'Could not load report');
    }
  }

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
      {/* Header */}
      <View className="flex-row items-center justify-between px-6 pt-14 pb-4 border-b border-surface-border">
        <Text className="text-xl font-display text-[#E8EDF5]">Doctor Prep</Text>
      </View>

      <View className="px-6 pt-5">
        {/* Generate card */}
        <View className="bg-surface-raised border border-surface-border rounded-2xl p-5 mb-5">
          <Text className="text-[#E8EDF5] font-sansMedium text-base mb-1">Generate Report</Text>
          <Text className="text-[#526380] text-sm mb-4 leading-5">
            Creates a comprehensive summary of your health data to share with your doctor.
          </Text>

          {/* Day range selector */}
          <View className="flex-row gap-2 mb-4">
            {DAY_OPTIONS.map((d) => (
              <TouchableOpacity
                key={d}
                onPress={() => setDays(d)}
                className="flex-1 py-2.5 rounded-xl items-center border"
                style={{
                  backgroundColor: days === d ? '#00D4AA20' : 'transparent',
                  borderColor: days === d ? '#00D4AA' : '#1E2A3B',
                }}
              >
                <Text
                  className="font-sansMedium text-sm"
                  style={{ color: days === d ? '#00D4AA' : '#526380' }}
                >
                  {d}d
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity
            onPress={() => generateMutation.mutate(days)}
            disabled={generateMutation.isPending}
            className="bg-primary-500 rounded-xl py-3.5 items-center flex-row justify-center gap-2"
            activeOpacity={0.8}
          >
            {generateMutation.isPending ? (
              <>
                <ActivityIndicator size="small" color="#080B10" />
                <Text className="text-obsidian-900 font-sansMedium">Generating…</Text>
              </>
            ) : (
              <>
                <Icon name="document-text-outline" size={18} color="#080B10" />
                <Text className="text-obsidian-900 font-sansMedium">Generate {days}-Day Report</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Active report */}
        {activeReport && <ReportDetail report={activeReport} />}

        {/* Previous reports */}
        {!activeReport && (
          <>
            <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3">Previous Reports</Text>
            {listLoading ? (
              <ActivityIndicator color="#00D4AA" />
            ) : !reports || reports.length === 0 ? (
              <View className="items-center py-8">
                <Icon name="document-outline" size={36} color="#526380" />
                <Text className="text-[#526380] text-sm mt-2 text-center">
                  No reports generated yet.{'\n'}Tap "Generate" to create your first report.
                </Text>
              </View>
            ) : (
              reports.slice(0, 10).map((r) => {
                const score = r.summary?.overall_health_score;
                const scoreColor = score != null
                  ? (score >= 80 ? '#6EE7B7' : score >= 60 ? '#F5A623' : '#F87171')
                  : '#526380';
                return (
                  <TouchableOpacity
                    key={r.id}
                    onPress={() => loadReport(r.id)}
                    className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2 flex-row items-center"
                    activeOpacity={0.8}
                  >
                    <View className="w-10 h-10 rounded-xl bg-primary-500/10 items-center justify-center mr-3">
                      <Icon name="document-text-outline" size={18} color="#00D4AA" />
                    </View>
                    <View className="flex-1">
                      <Text className="text-[#E8EDF5] font-sansMedium text-sm">
                        {format(new Date(r.date_range.start), 'MMM d')} –{' '}
                        {format(new Date(r.date_range.end), 'MMM d, yyyy')}
                      </Text>
                      <Text className="text-[#526380] text-xs mt-0.5">
                        Generated {format(new Date(r.generated_at), 'MMM d, yyyy')}
                      </Text>
                    </View>
                    {score != null && (
                      <Text className="font-display text-lg mr-2" style={{ color: scoreColor }}>
                        {Math.round(score)}
                      </Text>
                    )}
                    <Icon name="chevron-forward" size={16} color="#526380" />
                  </TouchableOpacity>
                );
              })
            )}
          </>
        )}

        {/* Back to list if viewing a report */}
        {activeReport && (
          <TouchableOpacity
            onPress={() => setActiveReport(null)}
            className="mt-2 py-3 items-center flex-row justify-center gap-2 border border-surface-border rounded-xl"
            activeOpacity={0.7}
          >
            <Icon name="list-outline" size={16} color="#526380" />
            <Text className="text-[#526380] font-sansMedium text-sm">View All Reports</Text>
          </TouchableOpacity>
        )}
      </View>
    </ScrollView>
  );
}
