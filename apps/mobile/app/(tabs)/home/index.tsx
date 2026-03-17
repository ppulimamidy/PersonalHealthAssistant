import { useState, useEffect } from 'react';
import { View, Text, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { api } from '@/services/api';
import { useAuthStore } from '@/stores/authStore';
import type { AIInsight } from '@/types';
import DailyCheckinModal, { shouldShowDailyCheckin } from '@/components/DailyCheckinModal';
import GettingStartedCard from '@/components/GettingStartedCard';
import { HealthRings, type RingData } from '@/components/HealthRings';

function scoreColor(score: number): string {
  if (score >= 80) return '#00D4AA';
  if (score >= 60) return '#6EE7B7';
  if (score >= 40) return '#F5A623';
  return '#F87171';
}

function trendIcon(trend?: string): string {
  if (trend === 'up') return 'trending-up';
  if (trend === 'down') return 'trending-down';
  return 'remove';
}

function trendColor(trend?: string): string {
  if (trend === 'up') return '#00D4AA';
  if (trend === 'down') return '#F87171';
  return '#526380';
}

function adherenceColor(pct: number): string {
  if (pct >= 80) return '#00D4AA';
  if (pct >= 50) return '#F5A623';
  return '#F87171';
}

function insightColor(type: string): string {
  if (type === 'alert') return '#F87171';
  if (type === 'recommendation') return '#F5A623';
  return '#6EE7B7';
}

function HealthScoreRing({ score, trend }: Readonly<{ score: number; trend?: string }>) {
  const color = scoreColor(score);
  const icon = trendIcon(trend);
  const iconColor = trendColor(trend);
  return (
    <View className="bg-surface-raised rounded-2xl p-6 mb-4 border border-surface-border">
      <View className="flex-row items-center justify-between">
        <View>
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-1">Health Score</Text>
          <Text className="font-display" style={{ fontSize: 52, color, lineHeight: 56 }}>
            {Math.round(score)}
          </Text>
          <View className="flex-row items-center mt-1 gap-1">
            <Ionicons name={icon as never} size={14} color={iconColor} />
            <Text style={{ color: iconColor, fontSize: 12 }}>vs yesterday</Text>
          </View>
        </View>
        <View className="items-end">
          <View className="w-24 h-24 rounded-full items-center justify-center border-4" style={{ borderColor: color, opacity: 0.15 + (score / 100) * 0.85 }}>
            <Text className="text-2xl font-display" style={{ color }}>{Math.round(score)}</Text>
          </View>
        </View>
      </View>
    </View>
  );
}

function QuickLogStrip() {
  return (
    <View className="flex-row gap-2 mb-4">
      <TouchableOpacity
        onPress={() => router.push('/(tabs)/log')}
        className="flex-1 bg-surface-raised border border-surface-border rounded-xl py-3 items-center"
        activeOpacity={0.7}
      >
        <Ionicons name="camera-outline" size={18} color="#6EE7B7" />
        <Text className="text-[#E8EDF5] text-[10px] mt-1 font-sansMedium">Scan Meal</Text>
      </TouchableOpacity>
      <TouchableOpacity
        onPress={() => router.push('/(tabs)/log/new-symptom')}
        className="flex-1 bg-surface-raised border border-surface-border rounded-xl py-3 items-center"
        activeOpacity={0.7}
      >
        <Ionicons name="body-outline" size={18} color="#F5A623" />
        <Text className="text-[#E8EDF5] text-[10px] mt-1 font-sansMedium">Symptom</Text>
      </TouchableOpacity>
      <TouchableOpacity
        onPress={() => router.push('/(tabs)/log/medications')}
        className="flex-1 bg-surface-raised border border-surface-border rounded-xl py-3 items-center"
        activeOpacity={0.7}
      >
        <Ionicons name="medkit-outline" size={18} color="#60A5FA" />
        <Text className="text-[#E8EDF5] text-[10px] mt-1 font-sansMedium">Log Meds</Text>
      </TouchableOpacity>
      <TouchableOpacity
        onPress={() => router.push('/(tabs)/log/lab-results')}
        className="flex-1 bg-surface-raised border border-surface-border rounded-xl py-3 items-center"
        activeOpacity={0.7}
      >
        <Ionicons name="flask-outline" size={18} color="#2DD4BF" />
        <Text className="text-[#E8EDF5] text-[10px] mt-1 font-sansMedium">Add Labs</Text>
      </TouchableOpacity>
    </View>
  );
}

function AdherenceStrip({ data }: Readonly<{ data?: { taken: number; total: number; streak: number } }>) {
  if (!data || data.total === 0) return null;
  const pct = Math.round((data.taken / data.total) * 100);
  const color = adherenceColor(pct);
  return (
    <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-4">
      <View className="flex-row items-center justify-between mb-2">
        <Text className="text-[#526380] text-xs uppercase tracking-wider">Today's Medications</Text>
        {data.streak > 0 && (
          <View className="flex-row items-center gap-1">
            <Ionicons name="flame" size={12} color="#F5A623" />
            <Text className="text-amber-500 text-xs">{data.streak}d streak</Text>
          </View>
        )}
      </View>
      <View className="flex-row items-center gap-3">
        <View className="flex-1 h-2 bg-surface rounded-full overflow-hidden">
          <View className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
        </View>
        <Text className="text-[#E8EDF5] text-sm font-sansMedium">
          {data.taken}/{data.total}
        </Text>
      </View>
      <TouchableOpacity onPress={() => router.push('/(tabs)/log/medications')} className="mt-2">
        <Text className="text-[#526380] text-xs">Tap to log →</Text>
      </TouchableOpacity>
    </View>
  );
}

function EmptyDashboard() {
  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-6 mb-4 items-center">
      <Ionicons name="stats-chart-outline" size={36} color="#526380" />
      <Text className="text-[#E8EDF5] font-sansMedium text-base mt-3 mb-1">Your dashboard is ready</Text>
      <Text className="text-[#526380] text-sm text-center leading-5">
        Log your first symptom, meal, or check-in to start seeing your health score and AI insights.
      </Text>
      <TouchableOpacity
        onPress={() => router.push('/(tabs)/home/checkin')}
        className="bg-primary-500/20 border border-primary-500/40 rounded-xl px-5 py-2.5 mt-4"
        activeOpacity={0.8}
      >
        <Text className="text-primary-500 font-sansMedium text-sm">Start with a check-in</Text>
      </TouchableOpacity>
    </View>
  );
}

function ProviderHomeCards() {
  return (
    <View className="mb-4 gap-3">
      <Text className="text-[#526380] text-xs uppercase tracking-wider mb-1">Provider Tools</Text>
      <TouchableOpacity
        onPress={() => router.push('/(tabs)/profile/patients')}
        className="flex-row items-center bg-surface-raised border border-surface-border rounded-xl p-4"
        activeOpacity={0.7}
      >
        <View className="w-10 h-10 rounded-xl bg-indigo-500/15 items-center justify-center mr-3">
          <Ionicons name="people-outline" size={20} color="#818CF8" />
        </View>
        <View className="flex-1">
          <Text className="text-[#E8EDF5] font-sansMedium">My Patients</Text>
          <Text className="text-[#526380] text-xs mt-0.5">View patient roster</Text>
        </View>
        <Ionicons name="chevron-forward" size={16} color="#526380" />
      </TouchableOpacity>
      <TouchableOpacity
        onPress={() => router.push('/(tabs)/insights/doctor-prep')}
        className="flex-row items-center bg-surface-raised border border-surface-border rounded-xl p-4"
        activeOpacity={0.7}
      >
        <View className="w-10 h-10 rounded-xl bg-primary-500/15 items-center justify-center mr-3">
          <Ionicons name="document-text-outline" size={20} color="#00D4AA" />
        </View>
        <View className="flex-1">
          <Text className="text-[#E8EDF5] font-sansMedium">Visit Prep</Text>
          <Text className="text-[#526380] text-xs mt-0.5">Prepare for your next appointment</Text>
        </View>
        <Ionicons name="chevron-forward" size={16} color="#526380" />
      </TouchableOpacity>
    </View>
  );
}

function CaregiverHomeCards() {
  const { data: sharingData } = useQuery({
    queryKey: ['sharing', 'links'],
    queryFn: async () => {
      try {
        const { data: resp } = await api.get('/api/v1/sharing/links');
        return resp;
      } catch { return null; }
    },
    staleTime: 5 * 60 * 1000,
  });

  const hasSharing = Array.isArray(sharingData)
    ? sharingData.length > 0
    : (sharingData?.links?.length ?? 0) > 0;

  if (hasSharing) return null;

  return (
    <TouchableOpacity
      onPress={() => router.push('/(tabs)/profile/sharing')}
      className="bg-indigo-500/10 border border-indigo-500/30 rounded-xl p-4 mb-4"
      activeOpacity={0.8}
    >
      <View className="flex-row items-center gap-2 mb-1">
        <Ionicons name="link-outline" size={18} color="#818CF8" />
        <Text className="text-indigo-400 font-sansMedium">Connect with your care recipient</Text>
      </View>
      <Text className="text-[#526380] text-sm ml-7">
        Set up sharing so you can monitor their health data
      </Text>
    </TouchableOpacity>
  );
}

function RecentInsights({ insights }: Readonly<{ insights: AIInsight[] }>) {
  if (!insights.length) return null;
  return (
    <View className="mb-4">
      <View className="flex-row items-center justify-between mb-2">
        <Text className="text-[#526380] text-xs uppercase tracking-wider">Latest Insights</Text>
        <TouchableOpacity onPress={() => router.push('/(tabs)/insights')}>
          <Text className="text-primary-500 text-xs">See all</Text>
        </TouchableOpacity>
      </View>
      {insights.slice(0, 2).map((insight) => {
        const color = insightColor(insight.type);
        return (
          <View key={insight.id} className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2">
            <View className="flex-row items-start gap-3">
              <View className="rounded-lg p-1.5 mt-0.5" style={{ backgroundColor: `${color}20` }}>
                <Ionicons name="bulb-outline" size={14} color={color} />
              </View>
              <View className="flex-1">
                <Text className="text-[#E8EDF5] text-sm font-sansMedium leading-5" numberOfLines={2}>
                  {insight.title}
                </Text>
                <Text className="text-[#526380] text-xs mt-1" numberOfLines={2}>
                  {insight.summary}
                </Text>
              </View>
            </View>
          </View>
        );
      })}
    </View>
  );
}

export default function HomeScreen() {
  const { user, profile } = useAuthStore();
  const userRole = profile?.user_role ?? 'patient';
  const [showDailyCheckin, setShowDailyCheckin] = useState(false);

  useEffect(() => {
    shouldShowDailyCheckin().then((show) => { if (show) setShowDailyCheckin(true); }).catch(() => {});
  }, []);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['batch', 'home'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/batch', {
        params: { resources: 'health_score,insights', days: '7' },
      });
      return resp;
    },
    staleTime: 5 * 60 * 1000,
  });

  const { data: checkinStatus } = useQuery({
    queryKey: ['checkin', 'status'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/checkins/status');
      return resp;
    },
  });

  const { data: adherenceData } = useQuery({
    queryKey: ['adherence', 'today'],
    queryFn: async () => {
      try {
        const [streakResp, medsResp] = await Promise.all([
          api.get('/api/v1/adherence/streaks'),
          api.get('/api/v1/medications'),
        ]);
        const meds = (medsResp.data?.medications ?? medsResp.data ?? []) as Array<{ is_active: boolean }>;
        return {
          taken: 0, // today's log not separately exposed — show total active as total
          total: meds.filter((m) => m.is_active).length,
          streak: streakResp.data?.current_streak ?? 0,
        };
      } catch {
        return null;
      }
    },
  });

  const { data: summaries } = useQuery({
    queryKey: ['health-summaries'],
    queryFn: async () => {
      try {
        const { data: resp } = await api.get('/api/v1/health-data/summaries');
        return resp as Record<string, { latest_value: number | null; avg_30d: number | null }>;
      } catch {
        return null;
      }
    },
    staleTime: 5 * 60 * 1000,
  });

  const healthScore = data?.health_score?.score ?? null;
  const healthTrend = data?.health_score?.trend;
  const insights: AIInsight[] = Array.isArray(data?.insights)
    ? data.insights
    : (data?.insights?.insights ?? []);
  const hasAnyData = healthScore !== null || insights.length > 0 || (adherenceData?.total ?? 0) > 0;
  const fullName = (user?.user_metadata?.full_name as string | undefined)
    ?? (user?.user_metadata?.name as string | undefined);
  const firstName = fullName?.split(' ')[0] ?? user?.email?.split('@')[0] ?? 'there';
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  return (
    <>
    <ScrollView
      className="flex-1 bg-obsidian-900"
      contentContainerStyle={{ padding: 16, paddingTop: 56, paddingBottom: 32 }}
      refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor="#00D4AA" />}
    >
      {/* Greeting */}
      <View className="mb-5">
        <Text className="text-2xl font-display text-[#E8EDF5]">{greeting}, {firstName}</Text>
        <Text className="text-[#526380] text-sm mt-1">{format(new Date(), 'EEEE, MMMM d')}</Text>
      </View>

      {/* Role-specific quick-access cards */}
      {userRole === 'provider' && <ProviderHomeCards />}
      {userRole === 'caregiver' && <CaregiverHomeCards />}

      {/* Getting started checklist — shown to new users until all 5 steps done */}
      <GettingStartedCard />

      {/* Health Rings + Score */}
      {summaries && Object.keys(summaries).length > 0 ? (() => {
        const sleepVal = summaries.sleep?.latest_value ?? 0;
        const hrvVal = summaries.hrv_sdnn?.latest_value ?? 0;
        const stepsVal = summaries.steps?.latest_value ?? 0;
        const hrvGoal = Math.max((summaries.hrv_sdnn?.avg_30d ?? 50) * 1.1, 50);
        const sleepPct = Math.min(sleepVal / 8, 1);
        const hrvPct = Math.min(hrvVal / hrvGoal, 1);
        const stepsPct = Math.min(stepsVal / 8000, 1);
        const computed = Math.round(sleepPct * 35 + hrvPct * 30 + stepsPct * 25 + stepsPct * 10);
        const score = healthScore ?? (computed > 0 ? computed : null);
        const recoveryVal = healthScore ?? computed ?? 0;

        return (
        <>
          <TouchableOpacity
            onPress={() => router.push('/(tabs)/insights/trends')}
            activeOpacity={0.85}
            className="bg-surface-raised rounded-2xl p-5 mb-4 border border-surface-border items-center"
          >
            <HealthRings
              data={{
                sleep:    { value: sleepVal, goal: 8 },
                heart:    { value: hrvVal, goal: hrvGoal },
                activity: { value: stepsVal, goal: 8000 },
                recovery: { value: recoveryVal, goal: 100 },
                overallScore: score,
              }}
              size={180}
            />
            <Text className="text-[#526380] text-[10px] mt-2">Tap rings to see trends</Text>
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => router.push('/(tabs)/chat')}
            activeOpacity={0.7}
            className="mb-4 self-center flex-row items-center gap-1.5 px-4 py-2 rounded-lg"
            style={{ borderWidth: 1, borderColor: 'rgba(0,212,170,0.2)' }}
          >
            <Ionicons name="sparkles" size={14} color="#00D4AA" />
            <Text className="text-[#00D4AA] text-xs font-sansMedium">Ask AI about my health</Text>
          </TouchableOpacity>
        </>
        );
      })() : healthScore !== null ? (
        <HealthScoreRing score={healthScore} trend={healthTrend} />
      ) : null}

      {/* Empty state for brand-new users */}
      {!isLoading && !hasAnyData && <EmptyDashboard />}

      {/* Check-in prompt */}
      {checkinStatus?.should_prompt && (
        <TouchableOpacity
          onPress={() => router.push('/(tabs)/home/checkin')}
          className="bg-primary-500/10 border border-primary-500/30 rounded-xl p-4 mb-4"
          activeOpacity={0.8}
        >
          <View className="flex-row items-center gap-2">
            <Ionicons name="clipboard-outline" size={18} color="#00D4AA" />
            <Text className="text-primary-500 font-sansMedium">Time for your weekly check-in</Text>
          </View>
          <Text className="text-[#526380] text-sm mt-1 ml-7">Rate your mood, energy, and pain levels</Text>
        </TouchableOpacity>
      )}

      {/* Quick Log */}
      <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Quick Log</Text>
      <QuickLogStrip />

      {/* Adherence Strip */}
      <AdherenceStrip data={adherenceData ?? undefined} />

      {/* Recent Insights */}
      <RecentInsights insights={insights} />
    </ScrollView>

    <DailyCheckinModal
      visible={showDailyCheckin}
      onDismiss={() => setShowDailyCheckin(false)}
    />
    </>
  );
}
