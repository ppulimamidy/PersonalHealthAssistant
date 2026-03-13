import { View, Text, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { api } from '@/services/api';
import { useAuthStore } from '@/stores/authStore';
import type { AIInsight } from '@/types';

function HealthScoreRing({ score, trend }: { score: number; trend?: string }) {
  const color = score >= 80 ? '#00D4AA' : score >= 60 ? '#6EE7B7' : score >= 40 ? '#F5A623' : '#F87171';
  const trendIcon = trend === 'up' ? 'trending-up' : trend === 'down' ? 'trending-down' : 'remove';
  const trendColor = trend === 'up' ? '#00D4AA' : trend === 'down' ? '#F87171' : '#526380';
  return (
    <View className="bg-surface-raised rounded-2xl p-6 mb-4 border border-surface-border">
      <View className="flex-row items-center justify-between">
        <View>
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-1">Health Score</Text>
          <Text className="font-display" style={{ fontSize: 52, color, lineHeight: 56 }}>
            {Math.round(score)}
          </Text>
          <View className="flex-row items-center mt-1 gap-1">
            <Ionicons name={trendIcon as any} size={14} color={trendColor} />
            <Text style={{ color: trendColor, fontSize: 12 }}>vs yesterday</Text>
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
    <View className="flex-row gap-3 mb-4">
      <TouchableOpacity
        onPress={() => router.push('/(tabs)/log/new-symptom')}
        className="flex-1 bg-surface-raised border border-surface-border rounded-xl py-3 items-center"
        activeOpacity={0.7}
      >
        <Ionicons name="body-outline" size={20} color="#F5A623" />
        <Text className="text-[#E8EDF5] text-xs mt-1.5 font-sansMedium">Symptom</Text>
      </TouchableOpacity>
      <TouchableOpacity
        onPress={() => router.push('/(tabs)/log')}
        className="flex-1 bg-surface-raised border border-surface-border rounded-xl py-3 items-center"
        activeOpacity={0.7}
      >
        <Ionicons name="restaurant-outline" size={20} color="#6EE7B7" />
        <Text className="text-[#E8EDF5] text-xs mt-1.5 font-sansMedium">Meal</Text>
      </TouchableOpacity>
      <TouchableOpacity
        onPress={() => router.push('/(tabs)/chat')}
        className="flex-1 bg-primary-500/10 border border-primary-500/30 rounded-xl py-3 items-center"
        activeOpacity={0.7}
      >
        <Ionicons name="chatbubble-ellipses-outline" size={20} color="#00D4AA" />
        <Text className="text-primary-500 text-xs mt-1.5 font-sansMedium">Ask AI</Text>
      </TouchableOpacity>
    </View>
  );
}

function AdherenceStrip({ data }: { data?: { taken: number; total: number; streak: number } }) {
  if (!data || data.total === 0) return null;
  const pct = data.total > 0 ? Math.round((data.taken / data.total) * 100) : 0;
  const color = pct >= 80 ? '#00D4AA' : pct >= 50 ? '#F5A623' : '#F87171';
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

function RecentInsights({ insights }: { insights: AIInsight[] }) {
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
        const color = insight.type === 'alert' ? '#F87171' : insight.type === 'recommendation' ? '#F5A623' : '#6EE7B7';
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
  const { user } = useAuthStore();

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

  const healthScore = data?.health_score?.score ?? null;
  const healthTrend = data?.health_score?.trend;
  const insights: AIInsight[] = Array.isArray(data?.insights)
    ? data.insights
    : (data?.insights?.insights ?? []);
  const firstName = (user?.user_metadata?.full_name as string | undefined)?.split(' ')[0] ?? 'there';
  const greeting = new Date().getHours() < 12 ? 'Good morning' : new Date().getHours() < 18 ? 'Good afternoon' : 'Good evening';

  return (
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

      {/* Health Score */}
      {healthScore !== null && (
        <HealthScoreRing score={healthScore} trend={healthTrend} />
      )}

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
  );
}
