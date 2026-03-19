import { View, Text, TouchableOpacity, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

interface JourneyProposalData {
  journey_key: string;
  specialist: { agent_type: string; agent_name: string; specialty: string };
  journey: { title: string; phases: Array<{ name: string }>; total_phases: number };
}

export default function JourneyProposalCard() {
  const queryClient = useQueryClient();

  const { data: proposal } = useQuery<JourneyProposalData | null>({
    queryKey: ['journey-proposal'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/onboarding/journey-proposal');
      return data || null;
    },
    staleTime: 60_000,
  });

  const startMutation = useMutation({
    mutationFn: async () => {
      await api.post('/api/v1/onboarding/start-journey', {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journey-proposal'] });
      queryClient.invalidateQueries({ queryKey: ['active-journey'] });
      queryClient.invalidateQueries({ queryKey: ['active-intervention'] });
    },
  });

  if (!proposal) return null;

  return (
    <View
      className="rounded-2xl p-4 mb-4"
      style={{ backgroundColor: 'rgba(96,165,250,0.04)', borderWidth: 1, borderColor: 'rgba(96,165,250,0.15)' }}
    >
      <View className="flex-row items-center gap-2 mb-2">
        <View className="w-7 h-7 rounded-lg items-center justify-center" style={{ backgroundColor: 'rgba(96,165,250,0.12)' }}>
          <Ionicons name="flag-outline" size={14} color="#60A5FA" />
        </View>
        <Text className="text-[10px] font-bold uppercase tracking-wider" style={{ color: '#60A5FA' }}>
          Journey Ready
        </Text>
      </View>

      <Text className="text-sm font-sansMedium text-[#E8EDF5] mb-1">
        Your {proposal.specialist.agent_name} has a plan
      </Text>

      {/* Phase preview */}
      <View className="rounded-lg p-3 mb-3" style={{ backgroundColor: 'rgba(96,165,250,0.04)', borderWidth: 1, borderColor: 'rgba(96,165,250,0.08)' }}>
        <Text className="text-xs font-sansMedium mb-2" style={{ color: '#60A5FA' }}>{proposal.journey.title}</Text>
        {proposal.journey.phases.map((phase, i) => (
          <View key={i} className="flex-row items-center gap-2 mb-1">
            <View className="w-4 h-4 rounded-full items-center justify-center" style={{ backgroundColor: 'rgba(96,165,250,0.1)' }}>
              <Text className="text-[7px] font-bold" style={{ color: '#60A5FA' }}>{i + 1}</Text>
            </View>
            <Text className="text-xs text-[#8B97A8]">{phase.name}</Text>
          </View>
        ))}
      </View>

      <TouchableOpacity
        onPress={() => startMutation.mutate()}
        disabled={startMutation.isPending}
        className="flex-row items-center justify-center gap-1.5 py-2.5 rounded-xl"
        style={{ backgroundColor: '#60A5FA', opacity: startMutation.isPending ? 0.6 : 1 }}
        activeOpacity={0.85}
      >
        {startMutation.isPending ? (
          <ActivityIndicator size="small" color="#080B10" />
        ) : (
          <>
            <Ionicons name="play" size={14} color="#080B10" />
            <Text className="text-sm font-sansMedium" style={{ color: '#080B10' }}>Start My Journey</Text>
          </>
        )}
      </TouchableOpacity>
    </View>
  );
}
