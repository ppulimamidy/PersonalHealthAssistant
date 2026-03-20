/**
 * Proactive meal suggestion card — shows an AI-suggested meal
 * based on the user's full health context + remaining daily budget.
 */

import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Ingredient {
  name: string;
  portion?: string;
  unit?: string;
}

interface Props {
  mealName: string;
  ingredients: Ingredient[];
  macros: { calories: number; protein_g: number; carbs_g: number; fat_g: number };
  rationale: string;
  onLogThis: () => void;
  onSomethingElse: () => void;
  onDismiss: () => void;
}

export default function ProactiveSuggestionCard({
  mealName,
  ingredients,
  macros,
  rationale,
  onLogThis,
  onSomethingElse,
  onDismiss,
}: Readonly<Props>) {
  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
      {/* Header */}
      <View className="flex-row items-center justify-between mb-2">
        <View className="flex-row items-center gap-1.5">
          <Ionicons name="sparkles" size={14} color="#F5A623" />
          <Text className="text-[#F5A623] text-xs uppercase tracking-wider font-sansMedium">
            Suggested for you
          </Text>
        </View>
        <TouchableOpacity onPress={onDismiss} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
          <Ionicons name="close" size={16} color="#526380" />
        </TouchableOpacity>
      </View>

      {/* Meal name */}
      <Text className="text-[#E8EDF5] font-sansMedium text-base leading-6 mb-2">
        {mealName}
      </Text>

      {/* Ingredient pills */}
      {ingredients.length > 0 && (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} className="mb-2 -mx-1">
          <View className="flex-row gap-1.5 px-1">
            {ingredients.map((ing, i) => (
              <View key={i} className="bg-white/5 rounded-lg px-2 py-1">
                <Text className="text-[#8B9BB4] text-[10px]">
                  {ing.portion ? `${ing.portion} ` : ''}{ing.name}
                </Text>
              </View>
            ))}
          </View>
        </ScrollView>
      )}

      {/* Macro line */}
      <View className="flex-row gap-3 mb-2">
        <Text className="text-[#E8EDF5] text-xs font-sansMedium">{Math.round(macros.calories)} cal</Text>
        <Text className="text-[#6EE7B7] text-[10px]">P {Math.round(macros.protein_g)}g</Text>
        <Text className="text-[#60A5FA] text-[10px]">C {Math.round(macros.carbs_g)}g</Text>
        <Text className="text-[#F5A623] text-[10px]">F {Math.round(macros.fat_g)}g</Text>
      </View>

      {/* Rationale */}
      {rationale ? (
        <Text className="text-[#526380] text-xs leading-4 mb-3" numberOfLines={2}>
          {rationale}
        </Text>
      ) : null}

      {/* CTAs */}
      <View className="flex-row gap-2">
        <TouchableOpacity
          onPress={onLogThis}
          className="flex-1 bg-primary-500 rounded-xl py-2 flex-row items-center justify-center gap-1"
          activeOpacity={0.8}
        >
          <Ionicons name="add-circle-outline" size={14} color="#080B10" />
          <Text className="text-obsidian-900 font-sansMedium text-xs">Log this meal</Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={onSomethingElse}
          className="flex-1 bg-surface border border-surface-border rounded-xl py-2 flex-row items-center justify-center gap-1"
          activeOpacity={0.8}
        >
          <Ionicons name="refresh-outline" size={14} color="#526380" />
          <Text className="text-[#526380] font-sansMedium text-xs">Something else</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
