/**
 * Phase 4: Health Twin screen. Pro+ only.
 * Shows digital twin profile, what-if simulations, and health goals.
 *
 * GET /api/v1/health-twin/profile
 * GET /api/v1/health-twin/simulations
 * GET /api/v1/health-twin/goals
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
import FirstVisitBanner from '@/components/FirstVisitBanner';

// ─── Types ────────────────────────────────────────────────────────────────────

interface HealthTwinProfile {
  health_age: number;
  chronological_age: number;
  health_age_trend: 'improving' | 'stable' | 'declining';
  resilience_score: number;
  adaptability_score: number;
  recovery_capacity: number;
  health_trajectory: 'improving' | 'stable' | 'declining';
  projected_health_age_1y: number;
  protective_factors: Array<{ name: string; benefit: string }>;
  risk_factors: Array<{ name: string; severity: string }>;
  last_calibrated_at: string;
}

interface HealthTwinSimulation {
  id: string;
  simulation_name: string;
  simulation_type: string;
  confidence_score: number;
  health_age_impact: number;
  success_probability: number;
  estimated_effort: 'low' | 'medium' | 'high';
  warnings: string[];
  recommendations: string[];
  status: string;
  created_at: string;
}

interface HealthTwinGoal {
  id: string;
  goal_name: string;
  goal_type: string;
  current_value: number;
  target_value: number;
  progress_percentage: number;
  predicted_success_probability: number;
  status: 'not_started' | 'in_progress' | 'achieved' | 'abandoned';
  estimated_timeline_days?: number;
}

type Tab = 'profile' | 'simulations' | 'goals';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const TRAJECTORY_COLOR: Record<string, string> = {
  improving: '#6EE7B7',
  stable:    '#526380',
  declining: '#F87171',
};

const EFFORT_COLOR: Record<string, string> = {
  low:    '#6EE7B7',
  medium: '#F5A623',
  high:   '#F87171',
};

const GOAL_STATUS_COLOR: Record<string, string> = {
  not_started: '#526380',
  in_progress: '#F5A623',
  achieved:    '#6EE7B7',
  abandoned:   '#F87171',
};

// ─── Profile Tab ──────────────────────────────────────────────────────────────

function ProfileTab() {
  const { data: profile, isLoading } = useQuery<HealthTwinProfile>({
    queryKey: ['health-twin-profile'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/health-twin/profile');
      return resp;
    },
  });

  if (isLoading) return <ActivityIndicator color="#00D4AA" className="mt-8" />;

  if (!profile) {
    return (
      <View className="items-center py-12">
        <Ionicons name="person-outline" size={40} color="#526380" />
        <Text className="text-[#526380] text-base mt-3">No profile available</Text>
      </View>
    );
  }

  const ageDiff = profile.health_age - profile.chronological_age;
  const ageColor = ageDiff < 0 ? '#6EE7B7' : ageDiff > 3 ? '#F87171' : '#F5A623';
  const trajectoryColor = TRAJECTORY_COLOR[profile.health_age_trend] ?? '#526380';

  return (
    <>
      {/* Biological age card */}
      <View className="bg-surface-raised border border-surface-border rounded-2xl p-5 mb-4">
        <View className="flex-row items-center justify-between mb-4">
          <View>
            <Text className="text-[#526380] text-xs uppercase tracking-wider mb-1">Biological Age</Text>
            <Text className="font-display text-5xl" style={{ color: ageColor }}>
              {profile.health_age.toFixed(1)}
            </Text>
            <Text className="text-[#526380] text-sm mt-0.5">
              Chronological: {profile.chronological_age}
              {' · '}
              <Text style={{ color: ageColor }}>
                {ageDiff < 0 ? `${Math.abs(ageDiff).toFixed(1)} yrs younger` : `${ageDiff.toFixed(1)} yrs older`}
              </Text>
            </Text>
          </View>
          <View className="items-center">
            <View
              className="w-16 h-16 rounded-full items-center justify-center border-2"
              style={{ borderColor: trajectoryColor }}
            >
              <Ionicons
                name={profile.health_trajectory === 'improving' ? 'trending-up' : profile.health_trajectory === 'declining' ? 'trending-down' : 'remove'}
                size={28}
                color={trajectoryColor}
              />
            </View>
            <Text className="text-xs mt-1 capitalize" style={{ color: trajectoryColor }}>
              {profile.health_trajectory}
            </Text>
          </View>
        </View>

        <View className="flex-row gap-3 mb-3 pt-3 border-t border-surface-border">
          <ScoreBar label="Resilience" value={profile.resilience_score} color="#818CF8" />
          <ScoreBar label="Recovery" value={profile.recovery_capacity} color="#6EE7B7" />
          <ScoreBar label="Adaptability" value={profile.adaptability_score} color="#F5A623" />
        </View>

        <Text className="text-[#526380] text-xs">
          1y projected: {profile.projected_health_age_1y.toFixed(1)} yrs ·{' '}
          Calibrated {format(new Date(profile.last_calibrated_at), 'MMM d')}
        </Text>
      </View>

      {/* Protective factors */}
      {profile.protective_factors.length > 0 && (
        <View className="mb-4">
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Protective Factors</Text>
          {profile.protective_factors.map((f, i) => (
            <View key={i} className="flex-row items-start gap-2 mb-1.5">
              <Ionicons name="shield-checkmark-outline" size={14} color="#6EE7B7" style={{ marginTop: 2 }} />
              <View className="flex-1">
                <Text className="text-[#E8EDF5] text-sm font-sansMedium">{f.name}</Text>
                {f.benefit && <Text className="text-[#526380] text-xs">{f.benefit}</Text>}
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Risk factors */}
      {profile.risk_factors.length > 0 && (
        <View className="mb-4">
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Risk Factors</Text>
          {profile.risk_factors.map((f, i) => (
            <View key={i} className="flex-row items-start gap-2 mb-1.5">
              <Ionicons name="warning-outline" size={14} color="#F5A623" style={{ marginTop: 2 }} />
              <Text className="text-[#E8EDF5] text-sm flex-1">{f.name}</Text>
              <Text className="text-xs capitalize" style={{ color: f.severity === 'high' ? '#F87171' : '#F5A623' }}>
                {f.severity}
              </Text>
            </View>
          ))}
        </View>
      )}
    </>
  );
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View className="flex-1 items-center">
      <Text className="font-display text-xl" style={{ color }}>{Math.round(value)}</Text>
      <View className="w-full h-1 bg-surface rounded-full overflow-hidden mt-1">
        <View className="h-full rounded-full" style={{ width: `${value}%`, backgroundColor: color }} />
      </View>
      <Text className="text-[#526380] text-xs mt-1">{label}</Text>
    </View>
  );
}

// ─── Simulations Tab ──────────────────────────────────────────────────────────

function SimulationsTab() {
  const { data, isLoading } = useQuery<{ simulations: HealthTwinSimulation[] }>({
    queryKey: ['health-twin-simulations'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/health-twin/simulations');
      return resp;
    },
  });

  const sims = data?.simulations ?? [];

  if (isLoading) return <ActivityIndicator color="#00D4AA" className="mt-8" />;

  if (sims.length === 0) {
    return (
      <View className="items-center py-12">
        <Ionicons name="flask-outline" size={40} color="#526380" />
        <Text className="text-[#526380] text-base mt-3">No simulations yet</Text>
        <Text className="text-[#526380] text-sm mt-1 text-center">
          Create what-if scenarios via the web app to see projections
        </Text>
      </View>
    );
  }

  return (
    <>
      {sims.map((s) => (
        <View key={s.id} className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
          <View className="flex-row items-start justify-between mb-2">
            <View className="flex-1 mr-3">
              <Text className="text-[#E8EDF5] font-sansMedium text-sm">{s.simulation_name}</Text>
              <Text className="text-[#526380] text-xs mt-0.5 capitalize">
                {s.simulation_type.replace(/_/g, ' ')}
              </Text>
            </View>
            <View className="items-end">
              {s.health_age_impact !== 0 && (
                <Text
                  className="font-display text-xl"
                  style={{ color: s.health_age_impact < 0 ? '#6EE7B7' : '#F87171' }}
                >
                  {s.health_age_impact < 0 ? '' : '+'}{s.health_age_impact.toFixed(1)}y
                </Text>
              )}
            </View>
          </View>

          <View className="flex-row gap-4 mb-2">
            <View>
              <Text className="text-[#526380] text-xs">Success prob.</Text>
              <Text className="text-[#E8EDF5] font-sansMedium text-sm">
                {Math.round(s.success_probability * 100)}%
              </Text>
            </View>
            <View>
              <Text className="text-[#526380] text-xs">Confidence</Text>
              <Text className="text-[#E8EDF5] font-sansMedium text-sm">
                {Math.round(s.confidence_score * 100)}%
              </Text>
            </View>
            <View>
              <Text className="text-[#526380] text-xs">Effort</Text>
              <Text className="font-sansMedium text-sm capitalize" style={{ color: EFFORT_COLOR[s.estimated_effort] ?? '#526380' }}>
                {s.estimated_effort}
              </Text>
            </View>
          </View>

          {s.recommendations.length > 0 && (
            <Text className="text-[#526380] text-xs leading-4">💡 {s.recommendations[0]}</Text>
          )}
        </View>
      ))}
    </>
  );
}

// ─── Goals Tab ────────────────────────────────────────────────────────────────

function GoalsTab() {
  const { data, isLoading } = useQuery<{ goals: HealthTwinGoal[] }>({
    queryKey: ['health-twin-goals'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/health-twin/goals');
      return resp;
    },
  });

  const goals = data?.goals ?? [];

  if (isLoading) return <ActivityIndicator color="#00D4AA" className="mt-8" />;

  if (goals.length === 0) {
    return (
      <View className="items-center py-12">
        <Ionicons name="flag-outline" size={40} color="#526380" />
        <Text className="text-[#526380] text-base mt-3">No health goals yet</Text>
        <Text className="text-[#526380] text-sm mt-1 text-center">
          Set goals via the web app to track them here
        </Text>
      </View>
    );
  }

  return (
    <>
      {goals.map((g) => {
        const pct = Math.min(g.progress_percentage, 100);
        const statusColor = GOAL_STATUS_COLOR[g.status] ?? '#526380';
        return (
          <View key={g.id} className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
            <View className="flex-row items-center justify-between mb-2">
              <Text className="text-[#E8EDF5] font-sansMedium text-sm flex-1">{g.goal_name}</Text>
              <View className="px-2 py-0.5 rounded-full" style={{ backgroundColor: `${statusColor}20` }}>
                <Text className="text-xs capitalize" style={{ color: statusColor }}>
                  {g.status.replace(/_/g, ' ')}
                </Text>
              </View>
            </View>

            <View className="h-2 bg-surface rounded-full overflow-hidden mb-2">
              <View
                className="h-full rounded-full"
                style={{ width: `${pct}%`, backgroundColor: statusColor }}
              />
            </View>

            <View className="flex-row justify-between">
              <Text className="text-[#526380] text-xs">{Math.round(pct)}% complete</Text>
              <Text className="text-[#526380] text-xs">
                {g.current_value.toFixed(1)} → {g.target_value.toFixed(1)}
              </Text>
              <Text className="text-[#526380] text-xs">
                {Math.round(g.predicted_success_probability * 100)}% success
              </Text>
            </View>
          </View>
        );
      })}
    </>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

const TABS: Array<{ id: Tab; label: string; icon: React.ComponentProps<typeof Ionicons>['name'] }> = [
  { id: 'profile', label: 'Profile', icon: 'person-outline' },
  { id: 'simulations', label: 'Simulations', icon: 'flask-outline' },
  { id: 'goals', label: 'Goals', icon: 'flag-outline' },
];

export default function HealthTwinScreen() {
  const [tab, setTab] = useState<Tab>('profile');

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <View className="flex-1">
          <Text className="text-xl font-display text-[#E8EDF5]">Simulate Changes</Text>
          <Text className="text-[#526380] text-xs mt-0.5">What if you changed something?</Text>
        </View>
        <View className="bg-indigo-400/20 border border-indigo-400/30 rounded-full px-2.5 py-1">
          <Text className="text-indigo-400 text-xs font-sansMedium">Preview</Text>
        </View>
      </View>

      {/* Coming Soon banner */}
      <View className="mx-6 mt-4 px-4 py-3 rounded-xl bg-indigo-400/5 border border-indigo-400/15">
        <Text className="text-indigo-400 text-xs font-sansMedium">Coming Soon — Preview Mode</Text>
        <Text className="text-[#526380] text-[11px] mt-1">
          Health Twin simulations are under development. Below is a preview of how it will look with your data.
        </Text>
      </View>

      <FirstVisitBanner
        screenKey="simulate_changes"
        text="Adjust variables like sleep or diet to see how your health score might respond."
      />

      {/* Tabs */}
      <View className="flex-row px-6 pt-4 gap-2">
        {TABS.map((t) => (
          <TouchableOpacity
            key={t.id}
            onPress={() => setTab(t.id)}
            className="flex-1 py-2.5 rounded-xl items-center border flex-row justify-center gap-1.5"
            style={{
              backgroundColor: tab === t.id ? '#818CF820' : 'transparent',
              borderColor: tab === t.id ? '#818CF8' : '#1E2A3B',
            }}
          >
            <Ionicons name={t.icon} size={14} color={tab === t.id ? '#818CF8' : '#526380'} />
            <Text
              className="text-xs font-sansMedium"
              style={{ color: tab === t.id ? '#818CF8' : '#526380' }}
            >
              {t.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <View className="px-6 pt-4">
        {tab === 'profile' && <ProfileTab />}
        {tab === 'simulations' && <SimulationsTab />}
        {tab === 'goals' && <GoalsTab />}
      </View>
    </ScrollView>
  );
}
