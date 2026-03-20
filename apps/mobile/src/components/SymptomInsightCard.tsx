/**
 * Symptom Insight Card — appears after logging a symptom.
 * Shows frequency, severity trend, AI insight, likely triggers, quick actions.
 */

import { useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, Animated, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Trigger {
  source: string;
  label: string;
  confidence: number;
  detail: string;
}

interface Props {
  insight: string;
  frequencyThisWeek: number;
  severityTrend: string;
  likelyTriggers: Trigger[];
  quickActions: string[];
  onAction: (action: string) => void;
  onDismiss: () => void;
}

const SOURCE_ICONS: Record<string, string> = {
  symptom_nutrition: 'nutrition-outline',
  symptom_oura: 'pulse-outline',
  wearable: 'watch-outline',
  medication: 'medkit-outline',
  pattern: 'analytics-outline',
};

const TREND_CONFIG = {
  improving: { icon: 'trending-down', color: '#6EE7B7', label: 'Improving' },
  worsening: { icon: 'trending-up', color: '#F87171', label: 'Worsening' },
  stable: { icon: 'remove', color: '#526380', label: 'Stable' },
};

export default function SymptomInsightCard({
  insight, frequencyThisWeek, severityTrend, likelyTriggers, quickActions, onAction, onDismiss,
}: Readonly<Props>) {
  const slideAnim = useRef(new Animated.Value(80)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(slideAnim, { toValue: 0, useNativeDriver: true, tension: 50, friction: 9 }),
      Animated.timing(fadeAnim, { toValue: 1, duration: 300, useNativeDriver: true }),
    ]).start();
  }, []);

  const trend = TREND_CONFIG[severityTrend as keyof typeof TREND_CONFIG] ?? TREND_CONFIG.stable;

  return (
    <Animated.View
      style={{ transform: [{ translateY: slideAnim }], opacity: fadeAnim }}
      className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3"
    >
      <TouchableOpacity onPress={onDismiss} className="absolute top-3 right-3 z-10" hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
        <Ionicons name="close" size={16} color="#526380" />
      </TouchableOpacity>

      {/* Header: frequency + trend */}
      <View className="flex-row items-center gap-3 mb-2">
        <View className="flex-row items-center gap-1 bg-white/5 rounded-lg px-2 py-1">
          <Text className="text-[#E8EDF5] text-xs font-sansMedium">{frequencyThisWeek}x</Text>
          <Text className="text-[#526380] text-[10px]">this week</Text>
        </View>
        <View className="flex-row items-center gap-1">
          <Ionicons name={trend.icon as never} size={12} color={trend.color} />
          <Text className="text-[10px]" style={{ color: trend.color }}>{trend.label}</Text>
        </View>
      </View>

      {/* AI insight */}
      <Text className="text-[#8B9BB4] text-sm leading-5 mb-3" style={{ fontStyle: 'italic' }}>
        {insight}
      </Text>

      {/* Likely triggers */}
      {likelyTriggers.length > 0 && (
        <View className="mb-3">
          <Text className="text-[#526380] text-[10px] uppercase tracking-wider mb-1.5">Likely Triggers</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View className="flex-row gap-1.5">
              {likelyTriggers.map((t, i) => {
                const icon = SOURCE_ICONS[t.source] ?? 'help-circle-outline';
                const confColor = t.confidence >= 0.6 ? '#F87171' : t.confidence >= 0.4 ? '#F5A623' : '#526380';
                return (
                  <View key={i} className="flex-row items-center gap-1 bg-white/5 rounded-lg px-2 py-1">
                    <Ionicons name={icon as never} size={10} color={confColor} />
                    <Text className="text-[#8B9BB4] text-[10px]">{t.label}</Text>
                    <View className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: confColor }} />
                  </View>
                );
              })}
            </View>
          </ScrollView>
        </View>
      )}

      {/* Quick actions */}
      <View className="flex-row flex-wrap gap-2">
        {quickActions.map((action) => (
          <TouchableOpacity
            key={action}
            onPress={() => onAction(action)}
            className="flex-row items-center gap-1 px-3 py-1.5 rounded-lg"
            style={{ backgroundColor: '#00D4AA15', borderWidth: 1, borderColor: '#00D4AA30' }}
            activeOpacity={0.7}
          >
            <Text className="text-[#00D4AA] text-xs font-sansMedium">{action}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </Animated.View>
  );
}
