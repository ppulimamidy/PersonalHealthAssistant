/**
 * My Specialists Section — shows active specialists with chat/consult actions.
 */

import { View, Text, TouchableOpacity } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { api } from '@/services/api';

export default function MySpecialistsSection() {
  const { data } = useQuery({
    queryKey: ['my-specialists'],
    queryFn: async () => {
      try {
        const { data: resp } = await api.get('/api/v1/profile-intelligence/my-specialists');
        return resp?.specialists ?? [];
      } catch { return []; }
    },
    staleTime: 5 * 60_000,
  });

  if (!data || data.length === 0) return null;

  return (
    <View className="mb-3">
      <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2 px-1">My Specialists</Text>
      {data.map((spec: any, i: number) => (
        <View
          key={spec.type ?? i}
          className="bg-surface-raised border border-surface-border rounded-xl p-3 mb-2 flex-row items-center"
        >
          <View className="w-10 h-10 rounded-xl items-center justify-center mr-3" style={{ backgroundColor: `${spec.color}15` }}>
            <Ionicons name={spec.icon as never} size={18} color={spec.color} />
          </View>
          <View className="flex-1">
            <Text className="text-[#E8EDF5] font-sansMedium text-sm">{spec.name}</Text>
            <Text className="text-[#526380] text-[10px] mt-0.5">
              For: {(spec.for_conditions ?? [spec.for_condition]).join(', ')}
            </Text>
            {spec.monitored_metrics?.length > 0 && (
              <Text className="text-[#3D4F66] text-[9px] mt-0.5">
                Monitors: {spec.monitored_metrics.slice(0, 3).join(', ')}
              </Text>
            )}
          </View>
          <View className="flex-row gap-1.5">
            <TouchableOpacity
              onPress={() => router.push({
                pathname: '/(tabs)/chat/[conversationId]',
                params: { conversationId: 'new', agentType: spec.type },
              } as never)}
              className="bg-[#00D4AA15] rounded-lg px-2.5 py-1.5"
              activeOpacity={0.7}
            >
              <Text className="text-[#00D4AA] text-[10px] font-sansMedium">Chat</Text>
            </TouchableOpacity>
          </View>
        </View>
      ))}
    </View>
  );
}
