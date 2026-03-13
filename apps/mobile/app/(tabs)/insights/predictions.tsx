/**
 * Phase 4: Predictions screen.
 * Tabs: Predictions / Risks / Trends
 * Data: GET /api/v1/predictions/predictions, /risks, /trends
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

// ─── Types ────────────────────────────────────────────────────────────────────

interface HealthPrediction {
  id: string;
  metric_name: string;
  prediction_date: string;
  prediction_horizon_days: number;
  predicted_value: number;
  confidence_score: number;
  prediction_range?: { lower: number; upper: number };
  contributing_factors: Array<{ factor: string; value: string }>;
  recommendations: Array<{ priority: string; action: string }>;
  status: string;
}

interface RiskFactor { factor: string; impact_score: number; description: string }

interface HealthRisk {
  id: string;
  risk_type: string;
  risk_level: 'low' | 'moderate' | 'high' | 'critical';
  risk_score: number;
  risk_window_end: string;
  contributing_factors: RiskFactor[];
  early_warning_signs: string[];
  recommendations: Array<{ priority: string; action: string }>;
  confidence_score: number;
}

interface HealthTrend {
  id: string;
  metric_name: string;
  trend_type: 'improving' | 'declining' | 'stable' | 'fluctuating';
  percent_change: number;
  average_value: number;
  slope: number;
  anomalies: Array<{ date: string; value: number; z_score: number }>;
  forecast_7d?: number;
  forecast_14d?: number;
  interpretation: string;
  significance: string;
}

type Tab = 'predictions' | 'risks' | 'trends';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const RISK_COLOR: Record<string, string> = {
  low:      '#6EE7B7',
  moderate: '#F5A623',
  high:     '#F87171',
  critical: '#EF4444',
};

const TREND_ICON: Record<string, React.ComponentProps<typeof Ionicons>['name']> = {
  improving:   'trending-up',
  declining:   'trending-down',
  stable:      'remove',
  fluctuating: 'analytics-outline',
};

const TREND_COLOR: Record<string, string> = {
  improving:   '#6EE7B7',
  declining:   '#F87171',
  stable:      '#526380',
  fluctuating: '#F5A623',
};

// ─── Predictions Tab ──────────────────────────────────────────────────────────

function PredictionsTab() {
  const { data, isLoading } = useQuery<{ predictions: HealthPrediction[] }>({
    queryKey: ['predictions'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/predictions/predictions?days=30');
      return resp;
    },
  });

  const preds = data?.predictions ?? [];

  if (isLoading) return <ActivityIndicator color="#00D4AA" className="mt-8" />;

  if (preds.length === 0) {
    return (
      <View className="items-center py-12">
        <Ionicons name="telescope-outline" size={40} color="#526380" />
        <Text className="text-[#526380] text-base mt-3">No predictions yet</Text>
        <Text className="text-[#526380] text-sm mt-1 text-center">
          At least 14 days of health data required
        </Text>
      </View>
    );
  }

  return (
    <>
      {preds.map((p) => (
        <View key={p.id} className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
          <View className="flex-row items-start justify-between mb-2">
            <View className="flex-1">
              <Text className="text-[#E8EDF5] font-sansMedium text-sm capitalize">
                {p.metric_name.replace(/_/g, ' ')}
              </Text>
              <Text className="text-[#526380] text-xs mt-0.5">
                {p.prediction_horizon_days}-day forecast ·{' '}
                {format(new Date(p.prediction_date), 'MMM d')}
              </Text>
            </View>
            <View className="items-end">
              <Text className="font-display text-2xl text-primary-500">
                {p.predicted_value.toFixed(0)}
              </Text>
              <Text className="text-[#526380] text-xs">
                {Math.round(p.confidence_score * 100)}% confidence
              </Text>
            </View>
          </View>

          {p.prediction_range && (
            <View className="bg-surface rounded-lg px-3 py-1.5 mb-2 flex-row justify-between">
              <Text className="text-[#526380] text-xs">
                Range: {p.prediction_range.lower.toFixed(0)} – {p.prediction_range.upper.toFixed(0)}
              </Text>
            </View>
          )}

          {p.contributing_factors.length > 0 && (
            <View className="flex-row flex-wrap gap-1.5 mt-1">
              {p.contributing_factors.slice(0, 3).map((f, i) => (
                <View key={i} className="bg-surface border border-surface-border rounded-full px-2 py-0.5">
                  <Text className="text-[#526380] text-xs">{f.factor}</Text>
                </View>
              ))}
            </View>
          )}

          {p.recommendations.length > 0 && (
            <View className="mt-2 pt-2 border-t border-surface-border">
              <Text className="text-[#526380] text-xs leading-4">{p.recommendations[0].action}</Text>
            </View>
          )}
        </View>
      ))}
    </>
  );
}

// ─── Risks Tab ────────────────────────────────────────────────────────────────

function RisksTab() {
  const { data, isLoading } = useQuery<{ risks: HealthRisk[]; overall_risk_level: string }>({
    queryKey: ['risks'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/predictions/risks');
      return resp;
    },
  });

  const risks = data?.risks ?? [];
  const overall = data?.overall_risk_level ?? 'low';

  if (isLoading) return <ActivityIndicator color="#00D4AA" className="mt-8" />;

  return (
    <>
      {/* Overall risk badge */}
      <View
        className="rounded-xl px-4 py-3 mb-4 flex-row items-center gap-3"
        style={{ backgroundColor: `${RISK_COLOR[overall] ?? '#6EE7B7'}15`, borderWidth: 1, borderColor: `${RISK_COLOR[overall] ?? '#6EE7B7'}40` }}
      >
        <Ionicons name="shield-outline" size={18} color={RISK_COLOR[overall] ?? '#6EE7B7'} />
        <View>
          <Text className="text-[#E8EDF5] font-sansMedium text-sm">Overall Risk</Text>
          <Text className="text-xs capitalize font-sansMedium" style={{ color: RISK_COLOR[overall] ?? '#6EE7B7' }}>
            {overall}
          </Text>
        </View>
      </View>

      {risks.length === 0 ? (
        <View className="items-center py-8">
          <Ionicons name="checkmark-circle-outline" size={36} color="#6EE7B7" />
          <Text className="text-[#6EE7B7] text-base mt-2">No active risks detected</Text>
        </View>
      ) : (
        risks.map((r) => {
          const rColor = RISK_COLOR[r.risk_level] ?? '#526380';
          return (
            <View key={r.id} className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
              <View className="flex-row items-center justify-between mb-2">
                <View className="flex-row items-center gap-2 flex-1">
                  <View className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: rColor }} />
                  <Text className="text-[#E8EDF5] font-sansMedium text-sm capitalize flex-1">
                    {r.risk_type.replace(/_/g, ' ')}
                  </Text>
                </View>
                <View className="px-2 py-0.5 rounded-full" style={{ backgroundColor: `${rColor}20` }}>
                  <Text className="text-xs capitalize font-sansMedium" style={{ color: rColor }}>
                    {r.risk_level}
                  </Text>
                </View>
              </View>

              {/* Risk score bar */}
              <View className="h-1 bg-surface rounded-full overflow-hidden mb-2">
                <View className="h-full rounded-full" style={{ width: `${r.risk_score * 100}%`, backgroundColor: rColor }} />
              </View>

              {r.early_warning_signs.length > 0 && (
                <View className="mb-2">
                  {r.early_warning_signs.slice(0, 2).map((s, i) => (
                    <View key={i} className="flex-row items-start gap-1.5 mb-1">
                      <Ionicons name="alert-circle-outline" size={12} color="#F5A623" style={{ marginTop: 1 }} />
                      <Text className="text-[#526380] text-xs flex-1 leading-4">{s}</Text>
                    </View>
                  ))}
                </View>
              )}

              {r.recommendations.length > 0 && (
                <Text className="text-[#526380] text-xs leading-4">
                  💡 {r.recommendations[0].action}
                </Text>
              )}
            </View>
          );
        })
      )}
    </>
  );
}

// ─── Trends Tab ───────────────────────────────────────────────────────────────

function TrendsTab() {
  const { data, isLoading } = useQuery<{ trends: HealthTrend[] }>({
    queryKey: ['health-trends'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/predictions/trends?days=30');
      return resp;
    },
  });

  const trends = data?.trends ?? [];

  if (isLoading) return <ActivityIndicator color="#00D4AA" className="mt-8" />;

  return (
    <>
      {trends.length === 0 ? (
        <View className="items-center py-12">
          <Ionicons name="analytics-outline" size={40} color="#526380" />
          <Text className="text-[#526380] text-base mt-3">No trend analysis available</Text>
        </View>
      ) : (
        trends.map((t) => {
          const tColor = TREND_COLOR[t.trend_type] ?? '#526380';
          const icon = TREND_ICON[t.trend_type] ?? 'analytics-outline';
          return (
            <View key={t.id} className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
              <View className="flex-row items-center justify-between mb-2">
                <Text className="text-[#E8EDF5] font-sansMedium text-sm capitalize flex-1">
                  {t.metric_name.replace(/_/g, ' ')}
                </Text>
                <View className="flex-row items-center gap-1.5">
                  <Ionicons name={icon} size={16} color={tColor} />
                  <Text className="text-sm capitalize font-sansMedium" style={{ color: tColor }}>
                    {t.trend_type}
                  </Text>
                </View>
              </View>

              <View className="flex-row gap-4 mb-2">
                <View>
                  <Text className="text-[#526380] text-xs">Avg</Text>
                  <Text className="text-[#E8EDF5] font-sansMedium text-sm">
                    {t.average_value.toFixed(1)}
                  </Text>
                </View>
                {t.percent_change !== 0 && (
                  <View>
                    <Text className="text-[#526380] text-xs">Change</Text>
                    <Text className="font-sansMedium text-sm" style={{ color: tColor }}>
                      {t.percent_change > 0 ? '+' : ''}{t.percent_change.toFixed(1)}%
                    </Text>
                  </View>
                )}
                {t.forecast_7d != null && (
                  <View>
                    <Text className="text-[#526380] text-xs">7d forecast</Text>
                    <Text className="text-[#E8EDF5] font-sansMedium text-sm">
                      {t.forecast_7d.toFixed(1)}
                    </Text>
                  </View>
                )}
                {t.anomalies.length > 0 && (
                  <View>
                    <Text className="text-[#526380] text-xs">Anomalies</Text>
                    <Text className="text-amber-500 font-sansMedium text-sm">{t.anomalies.length}</Text>
                  </View>
                )}
              </View>

              {t.interpretation && (
                <Text className="text-[#526380] text-xs leading-4">{t.interpretation}</Text>
              )}
            </View>
          );
        })
      )}
    </>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

const TABS: Array<{ id: Tab; label: string }> = [
  { id: 'predictions', label: 'Predictions' },
  { id: 'risks', label: 'Risks' },
  { id: 'trends', label: 'Trends' },
];

export default function PredictionsScreen() {
  const [tab, setTab] = useState<Tab>('predictions');

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <Text className="text-xl font-display text-[#E8EDF5]">Predictions</Text>
      </View>

      {/* Tabs */}
      <View className="flex-row px-6 pt-4 gap-2">
        {TABS.map((t) => (
          <TouchableOpacity
            key={t.id}
            onPress={() => setTab(t.id)}
            className="flex-1 py-2.5 rounded-xl items-center border"
            style={{
              backgroundColor: tab === t.id ? '#00D4AA20' : 'transparent',
              borderColor: tab === t.id ? '#00D4AA' : '#1E2A3B',
            }}
          >
            <Text
              className="text-sm font-sansMedium"
              style={{ color: tab === t.id ? '#00D4AA' : '#526380' }}
            >
              {t.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <View className="px-6 pt-4">
        {tab === 'predictions' && <PredictionsTab />}
        {tab === 'risks' && <RisksTab />}
        {tab === 'trends' && <TrendsTab />}
      </View>
    </ScrollView>
  );
}
