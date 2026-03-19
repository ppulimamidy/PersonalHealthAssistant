import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { router } from 'expo-router';
import { api } from '@/services/api';

interface JourneyOverview {
  id: string;
  title: string;
  goal_type: string;
  specialist_agent_id: string | null;
  phases: Array<{ name: string; status: string; description?: string }>;
  current_phase: number;
  status: string;
  total_phases: number;
  progress_pct: number;
  current_phase_name: string | null;
  days_active: number;
}

export default function GoalJourneyCard() {
  const { data: journey, isLoading } = useQuery<JourneyOverview | null>({
    queryKey: ['active-journey'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/journeys/active');
      return data || null;
    },
    staleTime: 60_000,
  });

  if (isLoading || !journey) return null;

  const completedPhases = journey.phases.filter((p) => p.status === 'completed').length;

  return (
    <View
      className="rounded-2xl p-4 mb-4"
      style={{ backgroundColor: 'rgba(96,165,250,0.04)', borderWidth: 1, borderColor: 'rgba(96,165,250,0.15)' }}
    >
      {/* Header */}
      <View className="flex-row items-center justify-between mb-3">
        <View className="flex-row items-center gap-2">
          <View className="w-7 h-7 rounded-lg items-center justify-center" style={{ backgroundColor: 'rgba(96,165,250,0.12)' }}>
            <Ionicons name="flag-outline" size={14} color="#60A5FA" />
          </View>
          <Text className="text-[10px] font-bold uppercase tracking-wider" style={{ color: '#60A5FA' }}>
            Health Journey
          </Text>
        </View>
        <Text className="text-[10px] text-[#526380]">{journey.days_active}d active</Text>
      </View>

      {/* Title */}
      <Text className="text-sm font-sansMedium text-[#E8EDF5] mb-1">{journey.title}</Text>
      <Text className="text-xs text-[#526380] mb-3">
        Phase {journey.current_phase + 1} of {journey.total_phases}
        {journey.current_phase_name && ` · ${journey.current_phase_name}`}
      </Text>

      {/* Phase stepper */}
      <View className="flex-row gap-1 mb-3">
        {journey.phases.map((phase, i) => {
          const color =
            phase.status === 'completed' ? '#00D4AA'
            : phase.status === 'active' ? '#60A5FA'
            : phase.status === 'skipped' ? '#3D4F66'
            : '#1E2A3B';
          return <View key={i} className="flex-1 h-1.5 rounded-full" style={{ backgroundColor: color }} />;
        })}
      </View>

      {/* Stats */}
      <View className="flex-row items-center gap-4 mb-3">
        <View className="flex-row items-center gap-1.5">
          <Text className="text-[10px] text-[#526380] uppercase tracking-wider">Progress</Text>
          <Text className="text-xs font-sansMedium text-[#E8EDF5]">{Math.round(journey.progress_pct)}%</Text>
        </View>
        <View className="flex-row items-center gap-1.5">
          <Text className="text-[10px] text-[#526380] uppercase tracking-wider">Phases</Text>
          <Text className="text-xs font-sansMedium text-[#E8EDF5]">{completedPhases}/{journey.total_phases}</Text>
        </View>
      </View>

      {/* Details link */}
      <TouchableOpacity
        onPress={() => router.push(`/(tabs)/profile/journey?id=${journey.id}` as never)}
        className="flex-row items-center gap-1"
      >
        <Text className="text-xs font-sansMedium" style={{ color: '#60A5FA' }}>View Details</Text>
        <Ionicons name="chevron-forward" size={12} color="#60A5FA" />
      </TouchableOpacity>
    </View>
  );
}
