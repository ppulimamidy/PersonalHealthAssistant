/**
 * Daily nutrition progress card — shows today's intake vs targets.
 * Displayed at the top of the nutrition screen.
 */

import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface MealSummary {
  meal_type: string;
  calories: number;
}

interface Props {
  meals: MealSummary[];
  totals: { calories: number; protein_g: number; carbs_g: number; fat_g: number };
  targets: { calories: number; protein_g: number; carbs_g: number; fat_g: number };
  remaining: { calories: number };
  progressPct: { calories: number; protein: number; carbs: number; fat: number };
}

const MEAL_TYPE_SHORT: Record<string, string> = {
  breakfast: 'B',
  lunch: 'L',
  dinner: 'D',
  snack: 'S',
};

function ProgressBar({ label, pct, color }: Readonly<{ label: string; pct: number; color: string }>) {
  return (
    <View className="flex-row items-center gap-2 mb-1">
      <Text className="text-[#526380] text-[10px] w-10">{label}</Text>
      <View className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
        <View className="h-full rounded-full" style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: color }} />
      </View>
      <Text className="text-[#526380] text-[10px] w-8 text-right">{pct}%</Text>
    </View>
  );
}

export default function DailyProgressCard({ meals, totals, targets, remaining, progressPct }: Readonly<Props>) {
  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
      {/* Header row */}
      <View className="flex-row items-center justify-between mb-3">
        <View className="flex-row items-center gap-1.5">
          <Ionicons name="nutrition-outline" size={14} color="#00D4AA" />
          <Text className="text-[#526380] text-xs uppercase tracking-wider">Today</Text>
        </View>
        <Text className="text-[#E8EDF5] text-sm font-display">
          {Math.round(totals.calories)} <Text className="text-[#526380] text-xs font-sans">/ {targets.calories} cal</Text>
        </Text>
      </View>

      {/* Progress bars */}
      <ProgressBar label="Protein" pct={progressPct.protein} color="#6EE7B7" />
      <ProgressBar label="Carbs" pct={progressPct.carbs} color="#60A5FA" />
      <ProgressBar label="Fat" pct={progressPct.fat} color="#F5A623" />

      {/* Meal chips + remaining */}
      <View className="flex-row items-center justify-between mt-2 pt-2 border-t border-surface-border">
        <View className="flex-row gap-1.5">
          {meals.map((m, i) => (
            <View key={i} className="flex-row items-center gap-0.5 bg-white/5 rounded-md px-1.5 py-0.5">
              <Text className="text-[#526380] text-[9px] font-sansMedium">
                {MEAL_TYPE_SHORT[m.meal_type] ?? m.meal_type[0]?.toUpperCase()}
              </Text>
              <Text className="text-[#8B9BB4] text-[9px]">{Math.round(m.calories)}</Text>
            </View>
          ))}
          {meals.length === 0 && (
            <Text className="text-[#3D4F66] text-[10px]">No meals logged yet</Text>
          )}
        </View>
        <Text className="text-[#526380] text-[10px]">
          ~{remaining.calories} cal left
        </Text>
      </View>
    </View>
  );
}
