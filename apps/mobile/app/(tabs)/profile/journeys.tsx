import { View, Text, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { api } from '@/services/api';

interface JourneyOverview {
  id: string;
  title: string;
  goal_type: string;
  status: string;
  total_phases: number;
  progress_pct: number;
  days_active: number;
  started_at: string;
}

const STATUS_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  active: { icon: 'flag-outline', color: '#60A5FA', label: 'Active' },
  completed: { icon: 'checkmark-circle', color: '#00D4AA', label: 'Completed' },
  paused: { icon: 'pause-circle', color: '#F5A623', label: 'Paused' },
  abandoned: { icon: 'close-circle', color: '#F87171', label: 'Abandoned' },
};

export default function JourneysScreen() {
  const { data: journeys, isLoading } = useQuery<JourneyOverview[]>({
    queryKey: ['journeys'],
    queryFn: async () => { const { data } = await api.get('/api/v1/journeys'); return data; },
  });

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ padding: 16, paddingTop: 56, paddingBottom: 32 }}>
      <Text className="text-2xl font-display text-[#E8EDF5] mb-1">My Journeys</Text>
      <Text className="text-sm text-[#526380] mb-6">Your health improvement programs</Text>

      {isLoading ? (
        <ActivityIndicator color="#00D4AA" className="mt-10" />
      ) : !journeys?.length ? (
        <View className="rounded-2xl p-6 items-center" style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}>
          <Ionicons name="flag-outline" size={36} color="#526380" />
          <Text className="text-[#E8EDF5] font-sansMedium text-base mt-3 mb-1">No journeys yet</Text>
          <Text className="text-[#526380] text-sm text-center leading-5">
            Start a health journey from your specialist agent or the Ask AI tab.
          </Text>
        </View>
      ) : (
        journeys.map((j) => {
          const cfg = STATUS_CONFIG[j.status] || STATUS_CONFIG.active;
          return (
            <TouchableOpacity
              key={j.id}
              onPress={() => router.push(`/(tabs)/profile/journey?id=${j.id}` as never)}
              className="rounded-xl p-4 mb-2"
              style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}
              activeOpacity={0.7}
            >
              <View className="flex-row items-center gap-3">
                <Ionicons name={cfg.icon as never} size={20} color={cfg.color} />
                <View className="flex-1">
                  <View className="flex-row items-center gap-2">
                    <Text className="text-sm font-sansMedium text-[#E8EDF5] flex-1" numberOfLines={1}>{j.title}</Text>
                    <View className="rounded-full px-1.5 py-0.5" style={{ backgroundColor: `${cfg.color}15` }}>
                      <Text className="text-[8px] font-bold uppercase" style={{ color: cfg.color }}>{cfg.label}</Text>
                    </View>
                  </View>
                  <Text className="text-xs text-[#526380] mt-0.5">
                    {j.total_phases} phases · {j.days_active}d · {Math.round(j.progress_pct)}%
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={16} color="#3D4F66" />
              </View>
              <View className="h-1 rounded-full mt-3" style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}>
                <View className="h-1 rounded-full" style={{ width: `${j.progress_pct}%`, backgroundColor: cfg.color }} />
              </View>
            </TouchableOpacity>
          );
        })
      )}
    </ScrollView>
  );
}
