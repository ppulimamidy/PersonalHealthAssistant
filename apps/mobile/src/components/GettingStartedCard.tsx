/**
 * GettingStartedCard — onboarding progress card shown on the home screen.
 * Disappears permanently when all 5 steps are complete or when dismissed.
 *
 * Steps are checked against real API data — no extra requests beyond what the
 * home screen already fetches. Each step links to the relevant screen.
 */

import { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { useAuthStore } from '@/stores/authStore';

const DISMISSED_KEY = 'getting_started_dismissed';

type Step = {
  key: string;
  label: string;
  route: string;
  done: boolean;
};

export default function GettingStartedCard() {
  const [dismissed, setDismissed] = useState<boolean | null>(null);
  const { profile } = useAuthStore();

  useEffect(() => {
    AsyncStorage.getItem(DISMISSED_KEY).then((v) => setDismissed(v === 'true')).catch(() => setDismissed(false));
  }, []);

  const { data: symptoms } = useQuery({
    queryKey: ['symptoms', 'count'],
    queryFn: async () => { const { data } = await api.get('/api/v1/symptoms?limit=1'); return data; },
    staleTime: 5 * 60 * 1000,
  });

  const { data: meals } = useQuery({
    queryKey: ['meals', 'count'],
    queryFn: async () => { const { data } = await api.get('/api/v1/nutrition/meals?limit=1'); return data; },
    staleTime: 5 * 60 * 1000,
  });

  const { data: convs } = useQuery({
    queryKey: ['conversations', 'count'],
    queryFn: async () => { const { data } = await api.get('/api/v1/agents/conversations'); return data; },
    staleTime: 5 * 60 * 1000,
  });

  const { data: checkins } = useQuery({
    queryKey: ['checkins', 'count'],
    queryFn: async () => { const { data } = await api.get('/api/v1/checkins?limit=1'); return data; },
    staleTime: 5 * 60 * 1000,
  });

  if (dismissed === null) return null;
  if (dismissed) return null;

  const symptomCount = Array.isArray(symptoms) ? symptoms.length : (symptoms?.symptoms?.length ?? symptoms?.total ?? 0);
  const mealCount = Array.isArray(meals) ? meals.length : (meals?.meals?.length ?? meals?.total ?? 0);
  const convCount = Array.isArray(convs) ? convs.length : (convs?.conversations?.length ?? convs?.total ?? 0);
  const checkinCount = Array.isArray(checkins) ? checkins.length : (checkins?.checkins?.length ?? checkins?.total ?? 0);

  const steps: Step[] = [
    { key: 'profile',   label: 'Complete your health profile', route: '/(tabs)/profile/health',        done: Boolean(profile?.onboarding_completed_at) },
    { key: 'checkin',   label: 'Do your first check-in',       route: '/(tabs)/home/checkin',          done: checkinCount > 0 },
    { key: 'symptom',   label: 'Log a symptom',                route: '/(tabs)/log/new-symptom',       done: symptomCount > 0 },
    { key: 'meal',      label: 'Log a meal',                   route: '/(tabs)/log/nutrition',         done: mealCount > 0 },
    { key: 'agent',     label: 'Ask Vitalix a question',       route: '/(tabs)/chat',                  done: convCount > 0 },
  ];

  const completedCount = steps.filter((s) => s.done).length;

  // Auto-hide when all done
  if (completedCount === steps.length) {
    AsyncStorage.setItem(DISMISSED_KEY, 'true').catch(() => {});
    return null;
  }

  const progressPct = Math.round((completedCount / steps.length) * 100);

  function dismiss() {
    AsyncStorage.setItem(DISMISSED_KEY, 'true').catch(() => {});
    setDismissed(true);
  }

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-5 mb-4">
      {/* Header row */}
      <View className="flex-row items-center justify-between mb-3">
        <View>
          <Text className="text-[#E8EDF5] font-sansMedium text-base">Getting Started</Text>
          <Text className="text-[#526380] text-xs mt-0.5">{completedCount}/{steps.length} complete</Text>
        </View>
        <TouchableOpacity onPress={dismiss} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
          <Ionicons name="close" size={18} color="#526380" />
        </TouchableOpacity>
      </View>

      {/* Progress bar */}
      <View className="h-1.5 bg-surface rounded-full overflow-hidden mb-4">
        <View className="h-full rounded-full bg-primary-500" style={{ width: `${progressPct}%` }} />
      </View>

      {/* Steps */}
      {steps.map((step) => (
        <TouchableOpacity
          key={step.key}
          onPress={() => !step.done && router.push(step.route as never)}
          disabled={step.done}
          activeOpacity={step.done ? 1 : 0.7}
          className="flex-row items-center gap-3 py-2"
        >
          {step.done ? (
            <Ionicons name="checkmark-circle" size={20} color="#00D4AA" />
          ) : (
            <View className="w-5 h-5 rounded-full border-2 border-[#3A4A5C]" />
          )}
          <Text
            className="flex-1 text-sm font-sansMedium"
            style={{ color: step.done ? '#526380' : '#E8EDF5' }}
          >
            {step.label}
          </Text>
          {!step.done && <Ionicons name="chevron-forward" size={14} color="#526380" />}
        </TouchableOpacity>
      ))}
    </View>
  );
}
