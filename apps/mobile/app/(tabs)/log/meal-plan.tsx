/**
 * Meal Plan screen — AI-generated weekly meal plan personalized
 * to the user's health context, goals, and dietary preferences.
 */

import { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format, addDays, startOfWeek } from 'date-fns';
import { api } from '@/services/api';
import GroceryListSheet from '@/components/GroceryListSheet';

// ─── Types ────────────────────────────────────────────────────────────────────

interface MealIngredient {
  name: string;
  portion?: string;
  unit?: string;
}

interface PlannedMeal {
  meal_type: string;
  name: string;
  ingredients: MealIngredient[];
  macros: { calories: number; protein_g: number; carbs_g: number; fat_g: number };
  prep_time_min?: number;
  notes?: string;
}

interface PlanDay {
  date: string;
  meals: PlannedMeal[];
}

interface MealPlan {
  days: PlanDay[];
}

// ─── Meal Card ────────────────────────────────────────────────────────────────

const MEAL_ICONS: Record<string, string> = {
  breakfast: 'sunny-outline',
  lunch: 'restaurant-outline',
  dinner: 'moon-outline',
  snack: 'cafe-outline',
};

const MEAL_COLORS: Record<string, string> = {
  breakfast: '#F5A623',
  lunch: '#00D4AA',
  dinner: '#818CF8',
  snack: '#60A5FA',
};

function PlannedMealCard({ meal, onLog }: Readonly<{ meal: PlannedMeal; onLog: () => void }>) {
  const [expanded, setExpanded] = useState(false);
  const color = MEAL_COLORS[meal.meal_type] ?? '#526380';
  const icon = MEAL_ICONS[meal.meal_type] ?? 'restaurant-outline';

  return (
    <TouchableOpacity
      onPress={() => setExpanded((e) => !e)}
      className="bg-surface-raised border border-surface-border rounded-xl p-3 mb-2"
      activeOpacity={0.8}
    >
      <View className="flex-row items-center gap-2">
        <Ionicons name={icon as never} size={14} color={color} />
        <Text className="text-xs uppercase tracking-wider font-sansMedium" style={{ color }}>
          {meal.meal_type}
        </Text>
        {meal.prep_time_min ? (
          <Text className="text-[#3D4F66] text-[10px] ml-auto">{meal.prep_time_min}min</Text>
        ) : null}
      </View>
      <Text className="text-[#E8EDF5] font-sansMedium text-sm mt-1">{meal.name}</Text>

      {/* Macros */}
      <View className="flex-row gap-3 mt-1">
        <Text className="text-[#8B9BB4] text-[10px]">{Math.round(meal.macros?.calories ?? 0)} cal</Text>
        <Text className="text-[#6EE7B7] text-[10px]">P {Math.round(meal.macros?.protein_g ?? 0)}g</Text>
        <Text className="text-[#60A5FA] text-[10px]">C {Math.round(meal.macros?.carbs_g ?? 0)}g</Text>
        <Text className="text-[#F5A623] text-[10px]">F {Math.round(meal.macros?.fat_g ?? 0)}g</Text>
      </View>

      {/* Expanded: ingredients + log */}
      {expanded && (
        <View className="mt-2 pt-2 border-t border-surface-border">
          {meal.ingredients?.map((ing, i) => (
            <Text key={i} className="text-[#526380] text-xs leading-5">
              {ing.portion ? `${ing.portion} ` : ''}{ing.name}
            </Text>
          ))}
          {meal.notes && (
            <Text className="text-[#3D4F66] text-[10px] mt-1 italic">{meal.notes}</Text>
          )}
          <TouchableOpacity
            onPress={onLog}
            className="mt-2 bg-primary-500/15 border border-primary-500/30 rounded-lg py-1.5 flex-row items-center justify-center gap-1"
            activeOpacity={0.7}
          >
            <Ionicons name="add-circle-outline" size={14} color="#00D4AA" />
            <Text className="text-[#00D4AA] text-xs font-sansMedium">Log this meal</Text>
          </TouchableOpacity>
        </View>
      )}
    </TouchableOpacity>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function MealPlanScreen() {
  const queryClient = useQueryClient();
  const monday = startOfWeek(new Date(), { weekStartsOn: 1 });
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(monday, i));
  const [selectedDay, setSelectedDay] = useState(0);
  const [showGrocery, setShowGrocery] = useState(false);
  const [groceryCategories, setGroceryCategories] = useState<any[]>([]);
  const [groceryLoading, setGroceryLoading] = useState(false);

  const { data: plan, isLoading } = useQuery<MealPlan | null>({
    queryKey: ['meal-plan'],
    queryFn: async () => {
      try {
        const { data } = await api.post('/api/v1/nutrition-ai/meal-plan', { days: 7 });
        return data as MealPlan;
      } catch { return null; }
    },
    staleTime: 10 * 60 * 1000, // 10 min
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/api/v1/nutrition-ai/meal-plan', { days: 7 });
      return data as MealPlan;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['meal-plan'], data);
    },
  });

  async function fetchGroceryList() {
    setGroceryLoading(true);
    setShowGrocery(true);
    try {
      const { data } = await api.post('/api/v1/nutrition-ai/meal-plan/grocery-list');
      setGroceryCategories(data?.categories ?? []);
    } catch {
      setGroceryCategories([]);
    } finally {
      setGroceryLoading(false);
    }
  }

  const dayPlan = plan?.days?.[selectedDay];
  const dayMeals = dayPlan?.meals ?? [];
  const dayTotals = dayMeals.reduce(
    (acc, m) => ({
      calories: acc.calories + (m.macros?.calories ?? 0),
      protein_g: acc.protein_g + (m.macros?.protein_g ?? 0),
      carbs_g: acc.carbs_g + (m.macros?.carbs_g ?? 0),
      fat_g: acc.fat_g + (m.macros?.fat_g ?? 0),
    }),
    { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 },
  );

  return (
    <>
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <View className="flex-1">
          <Text className="text-xl font-display text-[#E8EDF5]">Meal Plan</Text>
          <Text className="text-[#526380] text-xs mt-0.5">Personalized to your health</Text>
        </View>
        <TouchableOpacity
          onPress={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="flex-row items-center gap-1 px-3 py-1.5 rounded-lg"
          style={{ backgroundColor: '#00D4AA15', borderWidth: 1, borderColor: '#00D4AA30' }}
          activeOpacity={0.7}
        >
          <Ionicons
            name={generateMutation.isPending ? 'hourglass-outline' : 'refresh-outline'}
            size={14}
            color="#00D4AA"
          />
          <Text className="text-[#00D4AA] text-xs font-sansMedium">
            {plan ? 'Regenerate' : 'Generate'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Day selector */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} className="px-4 py-3">
        <View className="flex-row gap-1.5">
          {weekDays.map((d, i) => {
            const isSelected = selectedDay === i;
            const isToday = format(d, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd');
            return (
              <TouchableOpacity
                key={i}
                onPress={() => setSelectedDay(i)}
                className="items-center px-3 py-2 rounded-xl"
                style={{
                  backgroundColor: isSelected ? '#00D4AA18' : 'transparent',
                  borderWidth: 1,
                  borderColor: isSelected ? '#00D4AA' : isToday ? '#1E2A3B' : 'transparent',
                }}
                activeOpacity={0.7}
              >
                <Text className="text-[10px] font-sansMedium" style={{ color: isSelected ? '#00D4AA' : '#526380' }}>
                  {format(d, 'EEE')}
                </Text>
                <Text className="text-sm font-display" style={{ color: isSelected ? '#E8EDF5' : '#526380' }}>
                  {format(d, 'd')}
                </Text>
                {isToday && <View className="w-1 h-1 rounded-full bg-[#00D4AA] mt-0.5" />}
              </TouchableOpacity>
            );
          })}
        </View>
      </ScrollView>

      <View className="px-6">
        {isLoading || generateMutation.isPending ? (
          <View className="items-center py-16">
            <ActivityIndicator color="#00D4AA" size="large" />
            <Text className="text-[#526380] text-sm mt-3">
              {generateMutation.isPending ? 'Generating your personalized plan...' : 'Loading...'}
            </Text>
            <Text className="text-[#3D4F66] text-xs mt-1">
              Analyzing your health data, goals, and preferences
            </Text>
          </View>
        ) : !plan ? (
          <View className="items-center py-16">
            <Ionicons name="calendar-outline" size={44} color="#526380" />
            <Text className="text-[#E8EDF5] font-sansMedium text-base mt-3">No meal plan yet</Text>
            <Text className="text-[#526380] text-sm mt-1 text-center leading-5 px-4">
              Generate a personalized 7-day meal plan based on your health conditions, goals, medications, and dietary preferences.
            </Text>
            <TouchableOpacity
              onPress={() => generateMutation.mutate()}
              className="mt-4 bg-primary-500 rounded-xl px-6 py-2.5 flex-row items-center gap-1.5"
              activeOpacity={0.8}
            >
              <Ionicons name="sparkles" size={16} color="#080B10" />
              <Text className="text-obsidian-900 font-sansMedium text-sm">Generate My Plan</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <>
            {/* Day totals */}
            <View className="bg-surface-raised border border-surface-border rounded-xl p-3 mb-3 flex-row items-center justify-between">
              <Text className="text-[#526380] text-xs">{format(weekDays[selectedDay], 'EEEE, MMM d')}</Text>
              <View className="flex-row gap-3">
                <Text className="text-[#E8EDF5] text-xs font-sansMedium">{Math.round(dayTotals.calories)} cal</Text>
                <Text className="text-[#6EE7B7] text-[10px]">P {Math.round(dayTotals.protein_g)}g</Text>
                <Text className="text-[#60A5FA] text-[10px]">C {Math.round(dayTotals.carbs_g)}g</Text>
                <Text className="text-[#F5A623] text-[10px]">F {Math.round(dayTotals.fat_g)}g</Text>
              </View>
            </View>

            {/* Meals */}
            {dayMeals.length > 0 ? (
              dayMeals.map((meal, i) => (
                <PlannedMealCard
                  key={i}
                  meal={meal}
                  onLog={() => {
                    router.back();
                  }}
                />
              ))
            ) : (
              <View className="items-center py-8">
                <Text className="text-[#526380] text-sm">No meals planned for this day</Text>
              </View>
            )}

            {/* Grocery list button */}
            <TouchableOpacity
              onPress={fetchGroceryList}
              disabled={groceryLoading}
              className="mt-2 mb-4 bg-surface-raised border border-surface-border rounded-xl p-3 flex-row items-center justify-center gap-2"
              activeOpacity={0.7}
            >
              <Ionicons name={groceryLoading ? 'hourglass-outline' : 'cart-outline'} size={16} color="#00D4AA" />
              <Text className="text-[#00D4AA] font-sansMedium text-sm">
                {groceryLoading ? 'Building grocery list...' : 'View Grocery List'}
              </Text>
            </TouchableOpacity>
          </>
        )}
      </View>
    </ScrollView>

    <GroceryListSheet
      visible={showGrocery}
      categories={groceryCategories}
      onClose={() => setShowGrocery(false)}
    />
    </>
  );
}
