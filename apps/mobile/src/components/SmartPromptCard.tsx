import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

interface SmartPrompt {
  type: string;
  title: string;
  body: string;
  action: string;
  priority: number;
}

interface DataCompleteness {
  score: number;
  level: string;
}

const ACTION_ROUTES: Record<string, string> = {
  devices: '/(tabs)/profile/devices',
  medications: '/(tabs)/log/medications',
  cycle: '/(tabs)/log/cycle',
  'lab-results': '/(tabs)/log/lab-results',
  nutrition: '/(tabs)/log',
  symptoms: '/(tabs)/log/new-symptom',
  chat: '/(tabs)/chat',
};

export default function SmartPromptCard() {
  const queryClient = useQueryClient();

  const { data: completeness } = useQuery<DataCompleteness>({
    queryKey: ['data-completeness'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/onboarding/data-completeness');
      return data;
    },
    staleTime: 5 * 60_000,
  });

  const { data: prompt } = useQuery<SmartPrompt | null>({
    queryKey: ['smart-prompt'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/onboarding/smart-prompt');
      return data || null;
    },
    staleTime: 5 * 60_000,
  });

  const dismissMutation = useMutation({
    mutationFn: async (type: string) => {
      await api.post(`/api/v1/onboarding/smart-prompt/${type}/dismiss`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['smart-prompt'] }),
  });

  if (!prompt) return null;

  const route = ACTION_ROUTES[prompt.action] || '/(tabs)/home';

  return (
    <View
      className="rounded-2xl p-4 mb-4"
      style={{ backgroundColor: 'rgba(0,212,170,0.04)', borderWidth: 1, borderColor: 'rgba(0,212,170,0.12)' }}
    >
      {/* Action prompt */}
      <View className="flex-row items-start gap-3">
        <View className="w-8 h-8 rounded-lg items-center justify-center" style={{ backgroundColor: 'rgba(0,212,170,0.1)' }}>
          <Ionicons name="medkit-outline" size={16} color="#00D4AA" />
        </View>
        <View className="flex-1">
          <Text className="text-sm font-sansMedium text-[#E8EDF5]">{prompt.title}</Text>
          <Text className="text-xs text-[#526380] mt-0.5">{prompt.body}</Text>
          <TouchableOpacity
            onPress={() => router.push(route as never)}
            className="flex-row items-center gap-1 mt-2"
          >
            <Text className="text-xs font-sansMedium" style={{ color: '#00D4AA' }}>Get started</Text>
            <Ionicons name="chevron-forward" size={12} color="#00D4AA" />
          </TouchableOpacity>
        </View>
        <TouchableOpacity
          onPress={() => dismissMutation.mutate(prompt.type)}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Ionicons name="close" size={14} color="#3D4F66" />
        </TouchableOpacity>
      </View>

      {/* Data completeness bar */}
      {completeness && completeness.score < 80 && (
        <View className="mt-3 pt-3" style={{ borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.04)' }}>
          <View className="flex-row items-center justify-between mb-1">
            <Text className="text-[10px] text-[#526380]">Your health picture</Text>
            <Text className="text-[10px] text-[#526380]">{completeness.score}%</Text>
          </View>
          <View className="h-1 rounded-full" style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}>
            <View className="h-1 rounded-full" style={{ width: `${completeness.score}%`, backgroundColor: '#00D4AA' }} />
          </View>
        </View>
      )}
    </View>
  );
}
