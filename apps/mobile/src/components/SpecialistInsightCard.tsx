import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { router } from 'expo-router';
import { api } from '@/services/api';

interface JourneyOverview {
  specialist_agent_id: string | null;
  current_phase: number;
  phases: Array<{ name: string; checkpoints?: Array<{ action: string }> }>;
}

const SPECIALIST_NAMES: Record<string, string> = {
  endocrinologist: 'Endocrinologist',
  diabetologist: 'Diabetologist',
  metabolic_coach: 'Metabolic Coach',
  cardiologist: 'Cardiologist',
  gi_specialist: 'GI Specialist',
  womens_health: "Women's Health",
  sleep_specialist: 'Sleep Specialist',
  exercise_physiologist: 'Exercise Physiologist',
  behavioral_health: 'Behavioral Health',
  health_coach: 'Health Coach',
};

export default function SpecialistInsightCard() {
  const { data: journey } = useQuery<JourneyOverview | null>({
    queryKey: ['active-journey'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/journeys/active');
      return data || null;
    },
    staleTime: 60_000,
  });

  if (!journey?.specialist_agent_id) return null;

  const name = SPECIALIST_NAMES[journey.specialist_agent_id] || 'Specialist';
  const currentPhase = journey.phases[journey.current_phase];
  const checkpoint = currentPhase?.checkpoints?.[0];

  return (
    <View
      className="rounded-2xl p-4 mb-4"
      style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}
    >
      <View className="flex-row items-start gap-3">
        <View className="w-7 h-7 rounded-lg items-center justify-center" style={{ backgroundColor: 'rgba(0,212,170,0.08)' }}>
          <Ionicons name="medkit-outline" size={14} color="#00D4AA" />
        </View>
        <View className="flex-1">
          <Text className="text-xs font-sansMedium" style={{ color: '#00D4AA' }}>Your {name}</Text>
          <Text className="text-xs text-[#8B97A8] mt-1">
            {checkpoint ? `Upcoming: ${checkpoint.action}` : `Monitoring your ${currentPhase?.name || 'current phase'} progress.`}
          </Text>
        </View>
        <TouchableOpacity
          onPress={() => router.push(`/(tabs)/chat?agent=${journey.specialist_agent_id}` as never)}
          className="flex-row items-center gap-1 px-3 py-1.5 rounded-lg"
          style={{ borderWidth: 1, borderColor: 'rgba(0,212,170,0.2)' }}
          activeOpacity={0.7}
        >
          <Ionicons name="chatbubble-outline" size={12} color="#00D4AA" />
          <Text className="text-xs font-sansMedium" style={{ color: '#00D4AA' }}>Chat</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
