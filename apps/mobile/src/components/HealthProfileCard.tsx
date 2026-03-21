/**
 * Health Profile Card — rich summary on profile screen showing
 * conditions, goals, specialists at a glance with [+] actions.
 */

import { View, Text, TouchableOpacity } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { api } from '@/services/api';

export default function HealthProfileCard() {
  const { data } = useQuery({
    queryKey: ['health-summary'],
    queryFn: async () => {
      try {
        const { data: resp } = await api.get('/api/v1/profile-intelligence/health-summary');
        return resp;
      } catch { return null; }
    },
    staleTime: 2 * 60_000,
  });

  return (
    <TouchableOpacity
      onPress={() => router.push('/(tabs)/profile/health')}
      className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3"
      activeOpacity={0.7}
    >
      {/* Header */}
      <View className="flex-row items-center justify-between mb-3">
        <View className="flex-row items-center gap-2">
          <Ionicons name="heart-outline" size={16} color="#00D4AA" />
          <Text className="text-[#E8EDF5] font-sansMedium text-sm">My Health Profile</Text>
        </View>
        <Ionicons name="chevron-forward" size={14} color="#526380" />
      </View>

      {/* Conditions */}
      <View className="flex-row items-center justify-between mb-2">
        <View className="flex-row items-center gap-1.5 flex-1">
          <Text className="text-[#526380] text-xs">Conditions:</Text>
          {data?.conditions?.length ? (
            <Text className="text-[#8B9BB4] text-xs flex-1" numberOfLines={1}>
              {data.conditions.map((c: any) => c.name).join(', ')}
            </Text>
          ) : (
            <Text className="text-[#3D4F66] text-xs">None added</Text>
          )}
        </View>
        <TouchableOpacity
          onPress={(e) => { e.stopPropagation(); router.push('/(tabs)/profile/health'); }}
          className="bg-[#00D4AA15] rounded-full w-6 h-6 items-center justify-center"
          activeOpacity={0.7}
        >
          <Ionicons name="add" size={14} color="#00D4AA" />
        </TouchableOpacity>
      </View>

      {/* Goals */}
      <View className="flex-row items-center justify-between mb-2">
        <View className="flex-row items-center gap-1.5">
          <Text className="text-[#526380] text-xs">Goals:</Text>
          <Text className="text-[#8B9BB4] text-xs">
            {data?.active_goals_count ?? 0} active
          </Text>
        </View>
        <TouchableOpacity
          onPress={(e) => { e.stopPropagation(); router.push('/(tabs)/profile/goals'); }}
          className="bg-[#00D4AA15] rounded-full w-6 h-6 items-center justify-center"
          activeOpacity={0.7}
        >
          <Ionicons name="add" size={14} color="#00D4AA" />
        </TouchableOpacity>
      </View>

      {/* Specialists */}
      {data?.specialists?.length > 0 && (
        <View className="flex-row items-center gap-1.5 mb-2">
          <Text className="text-[#526380] text-xs">Specialists:</Text>
          <View className="flex-row gap-1 flex-1 flex-wrap">
            {data.specialists.slice(0, 3).map((s: any, i: number) => (
              <View key={i} className="flex-row items-center gap-0.5 bg-white/5 rounded-md px-1.5 py-0.5">
                <Ionicons name={s.icon as never} size={10} color={s.color} />
                <Text className="text-[10px]" style={{ color: s.color }}>{s.name}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Hint */}
      {data?.hint && (
        <View className="mt-1 pt-2 border-t border-surface-border">
          <View className="flex-row items-center gap-1.5">
            <Ionicons name="bulb-outline" size={12} color="#F5A623" />
            <Text className="text-[#F5A623] text-[10px] flex-1">{data.hint}</Text>
          </View>
        </View>
      )}
    </TouchableOpacity>
  );
}
