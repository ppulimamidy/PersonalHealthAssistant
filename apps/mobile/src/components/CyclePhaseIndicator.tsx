/**
 * Cycle Phase Indicator — small badge on home screen showing current phase.
 * Tappable to reveal phase expectations tooltip.
 */

import { useState } from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/services/api';

const PHASE_COLORS: Record<string, string> = {
  menstrual: '#F87171',
  follicular: '#6EE7B7',
  ovulation: '#F5A623',
  luteal: '#A78BFA',
};

const PHASE_ICONS: Record<string, string> = {
  menstrual: 'water-outline',
  follicular: 'sunny-outline',
  ovulation: 'star-outline',
  luteal: 'moon-outline',
};

export default function CyclePhaseIndicator() {
  const [showTip, setShowTip] = useState(false);

  const { data } = useQuery({
    queryKey: ['cycle-context'],
    queryFn: async () => {
      try {
        const { data: resp } = await api.get('/api/v1/cycle/context');
        return resp;
      } catch { return null; }
    },
    staleTime: 10 * 60_000,
  });

  if (!data?.has_cycle_data || !data.phase) return null;

  const color = PHASE_COLORS[data.phase] ?? '#526380';
  const icon = PHASE_ICONS[data.phase] ?? 'ellipse-outline';
  const expectations = data.phase_expectations ?? {};

  return (
    <View>
      <TouchableOpacity
        onPress={() => setShowTip((s) => !s)}
        className="flex-row items-center gap-1 self-start rounded-lg px-2 py-1"
        style={{ backgroundColor: `${color}15`, borderWidth: 1, borderColor: `${color}30` }}
        activeOpacity={0.7}
      >
        <Ionicons name={icon as never} size={12} color={color} />
        <Text className="text-[11px] font-sansMedium capitalize" style={{ color }}>
          {data.phase}
        </Text>
        <Text className="text-[10px]" style={{ color: `${color}90` }}>
          · Day {data.cycle_day}
        </Text>
        <Ionicons name="information-circle-outline" size={10} color={`${color}70`} />
      </TouchableOpacity>

      {showTip && (
        <View className="mt-2 bg-[#1E2A3B] rounded-xl p-3 mb-2">
          <View className="flex-row items-center gap-1.5 mb-2">
            <Ionicons name={icon as never} size={14} color={color} />
            <Text className="text-xs font-sansMedium capitalize" style={{ color }}>
              {data.phase} Phase — Day {data.cycle_day}
            </Text>
          </View>

          {Object.entries(expectations).slice(0, 5).map(([key, value]) => (
            <View key={key} className="flex-row items-start gap-1.5 mb-1">
              <Text className="text-[#526380] text-[10px] w-12 capitalize">{key}</Text>
              <Text className="text-[#8B9BB4] text-[10px] flex-1 leading-4">{String(value)}</Text>
            </View>
          ))}

          {data.nutrition_guidance && (
            <View className="mt-1.5 pt-1.5 border-t border-surface-border">
              <Text className="text-[#6EE7B7] text-[10px] font-sansMedium mb-0.5">Nutrition</Text>
              <Text className="text-[#8B9BB4] text-[10px] leading-4">{data.nutrition_guidance}</Text>
            </View>
          )}
          {data.exercise_guidance && (
            <View className="mt-1">
              <Text className="text-[#60A5FA] text-[10px] font-sansMedium mb-0.5">Exercise</Text>
              <Text className="text-[#8B9BB4] text-[10px] leading-4">{data.exercise_guidance}</Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
}
