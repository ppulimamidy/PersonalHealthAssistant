/**
 * Post-log insight card — appears after logging a meal.
 * Shows macro summary + AI insight + quick action chips.
 */

import { useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, Animated } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface MacroSummary {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

interface Props {
  insight: string;
  macros: MacroSummary;
  quickActions: string[];
  onAction: (action: string) => void;
  onDismiss: () => void;
}

const ACTION_ICONS: Record<string, string> = {
  'Suggest next meal': 'restaurant-outline',
  'Ask nutrition coach': 'chatbubble-outline',
  'Check experiment fit': 'flask-outline',
  'Healthier swap ideas': 'swap-horizontal-outline',
};

export default function NutritionInsightCard({ insight, macros, quickActions, onAction, onDismiss }: Readonly<Props>) {
  const slideAnim = useRef(new Animated.Value(80)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(slideAnim, { toValue: 0, useNativeDriver: true, tension: 50, friction: 9 }),
      Animated.timing(fadeAnim, { toValue: 1, duration: 300, useNativeDriver: true }),
    ]).start();
  }, []);

  const total = macros.protein_g + macros.carbs_g + macros.fat_g || 1;
  const proteinPct = (macros.protein_g / total) * 100;
  const carbsPct = (macros.carbs_g / total) * 100;
  const fatPct = (macros.fat_g / total) * 100;

  return (
    <Animated.View
      style={{ transform: [{ translateY: slideAnim }], opacity: fadeAnim }}
      className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3"
    >
      {/* Dismiss */}
      <TouchableOpacity onPress={onDismiss} className="absolute top-3 right-3 z-10" hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
        <Ionicons name="close" size={16} color="#526380" />
      </TouchableOpacity>

      {/* Macro summary bar */}
      <View className="flex-row items-center gap-2 mb-2">
        <Ionicons name="sparkles" size={14} color="#00D4AA" />
        <Text className="text-[#526380] text-xs uppercase tracking-wider">AI Insight</Text>
      </View>

      <View className="flex-row h-2 rounded-full overflow-hidden mb-2">
        <View style={{ width: `${proteinPct}%`, backgroundColor: '#6EE7B7' }} />
        <View style={{ width: `${carbsPct}%`, backgroundColor: '#60A5FA' }} />
        <View style={{ width: `${fatPct}%`, backgroundColor: '#F5A623' }} />
      </View>

      <View className="flex-row justify-between mb-3">
        <Text className="text-[#E8EDF5] text-xs font-sansMedium">{Math.round(macros.calories)} cal</Text>
        <View className="flex-row gap-3">
          <Text className="text-[#6EE7B7] text-[10px]">P {Math.round(macros.protein_g)}g</Text>
          <Text className="text-[#60A5FA] text-[10px]">C {Math.round(macros.carbs_g)}g</Text>
          <Text className="text-[#F5A623] text-[10px]">F {Math.round(macros.fat_g)}g</Text>
        </View>
      </View>

      {/* AI insight */}
      <Text className="text-[#8B9BB4] text-sm leading-5 mb-3" style={{ fontStyle: 'italic' }}>
        {insight}
      </Text>

      {/* Quick action chips */}
      <View className="flex-row flex-wrap gap-2">
        {quickActions.map((action) => (
          <TouchableOpacity
            key={action}
            onPress={() => onAction(action)}
            className="flex-row items-center gap-1 px-3 py-1.5 rounded-lg"
            style={{ backgroundColor: '#00D4AA15', borderWidth: 1, borderColor: '#00D4AA30' }}
            activeOpacity={0.7}
          >
            <Ionicons name={(ACTION_ICONS[action] ?? 'arrow-forward') as never} size={12} color="#00D4AA" />
            <Text className="text-[#00D4AA] text-xs font-sansMedium">{action}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </Animated.View>
  );
}
