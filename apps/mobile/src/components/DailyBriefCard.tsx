/**
 * Daily Brief Card — synthesized morning health narrative on the home screen.
 * Combines sleep, wearable, nutrition, meds, experiments, labs, symptoms, cycle.
 */

import { View, Text, TouchableOpacity } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/services/api';

const SOURCE_ICONS: Record<string, { icon: string; color: string }> = {
  Sleep: { icon: 'moon-outline', color: '#818CF8' },
  HRV: { icon: 'pulse-outline', color: '#F87171' },
  Steps: { icon: 'footsteps-outline', color: '#6EE7B7' },
  "Yesterday's intake": { icon: 'nutrition-outline', color: '#F5A623' },
  Experiment: { icon: 'flask-outline', color: '#2DD4BF' },
  Journey: { icon: 'flag-outline', color: '#818CF8' },
  Meds: { icon: 'medkit-outline', color: '#60A5FA' },
  Lab: { icon: 'document-text-outline', color: '#F87171' },
  Symptoms: { icon: 'alert-circle-outline', color: '#F5A623' },
  Cycle: { icon: 'ellipse-outline', color: '#EC4899' },
  Health: { icon: 'heart-outline', color: '#00D4AA' },
  Conditions: { icon: 'body-outline', color: '#526380' },
};

export default function DailyBriefCard() {
  const { data } = useQuery({
    queryKey: ['daily-brief'],
    queryFn: async () => {
      try {
        const { data: resp } = await api.get('/api/v1/health-brief/daily');
        return resp;
      } catch {
        return null;
      }
    },
    staleTime: 4 * 60 * 60_000, // 4 hours
  });

  if (!data?.brief) return null;

  const sources = (data.data_sources_used ?? []) as string[];

  return (
    <View className="mb-4 rounded-2xl p-4 overflow-hidden" style={{ backgroundColor: '#0D2118', borderWidth: 1, borderColor: '#00D4AA15' }}>
      {/* Header */}
      <View className="flex-row items-center gap-1.5 mb-2">
        <Ionicons name="sparkles" size={14} color="#00D4AA" />
        <Text className="text-[#00D4AA] text-xs font-sansMedium uppercase tracking-wider">
          Your Daily Brief
        </Text>
      </View>

      {/* Brief text */}
      <Text className="text-[#C8D6E5] text-sm leading-6">
        {data.brief}
      </Text>

      {/* Data source icons */}
      {sources.length > 0 && (
        <View className="flex-row items-center gap-2 mt-3 pt-2 border-t border-white/5">
          <Text className="text-[#3D4F66] text-[9px]">Based on</Text>
          {sources.slice(0, 7).map((src, i) => {
            const config = SOURCE_ICONS[src] ?? { icon: 'ellipse-outline', color: '#3D4F66' };
            return (
              <Ionicons key={i} name={config.icon as never} size={11} color={config.color} />
            );
          })}
        </View>
      )}
    </View>
  );
}
