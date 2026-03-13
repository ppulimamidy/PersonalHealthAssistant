import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { router } from 'expo-router';
import * as Haptics from 'expo-haptics';
import { api } from '@/services/api';

const GOAL_OPTIONS = [
  'Improve sleep quality',
  'Manage chronic condition',
  'Lose weight',
  'Reduce stress',
  'Improve fitness',
  'Track medications',
  'Understand lab results',
  'Prepare for doctor visits',
];

export default function OnboardingScreen() {
  const [step, setStep] = useState(1);
  const [weightKg, setWeightKg] = useState('');
  const [heightCm, setHeightCm] = useState('');
  const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  function toggleGoal(goal: string) {
    setSelectedGoals((prev) =>
      prev.includes(goal) ? prev.filter((g) => g !== goal) : [...prev, goal]
    );
  }

  async function handleFinish() {
    setLoading(true);
    try {
      await api.patch('/api/v1/profile/checkin', {
        weight_kg: weightKg ? parseFloat(weightKg) : undefined,
        height_cm: heightCm ? parseFloat(heightCm) : undefined,
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.replace('/(tabs)/home');
    } catch {
      router.replace('/(tabs)/home'); // Non-blocking — continue even if save fails
    } finally {
      setLoading(false);
    }
  }

  return (
    <View className="flex-1 bg-obsidian-900">
      {/* Progress indicator */}
      <View className="flex-row gap-2 px-6 pt-16 pb-6">
        {[1, 2].map((s) => (
          <View
            key={s}
            className={`h-1 flex-1 rounded-full ${s <= step ? 'bg-primary-500' : 'bg-surface-border'}`}
          />
        ))}
      </View>

      <ScrollView className="flex-1 px-6" keyboardShouldPersistTaps="handled">
        {step === 1 && (
          <View>
            <Text className="text-2xl font-display text-[#E8EDF5] mb-2">Personal Details</Text>
            <Text className="text-[#526380] mb-8">Help us personalise your health insights</Text>

            <View className="gap-4">
              <View>
                <Text className="text-sm text-[#526380] mb-1">Weight (kg) — optional</Text>
                <TextInput
                  className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] text-base"
                  value={weightKg}
                  onChangeText={setWeightKg}
                  keyboardType="decimal-pad"
                  placeholderTextColor="#526380"
                  placeholder="70"
                />
              </View>
              <View>
                <Text className="text-sm text-[#526380] mb-1">Height (cm) — optional</Text>
                <TextInput
                  className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] text-base"
                  value={heightCm}
                  onChangeText={setHeightCm}
                  keyboardType="decimal-pad"
                  placeholderTextColor="#526380"
                  placeholder="170"
                />
              </View>
            </View>
          </View>
        )}

        {step === 2 && (
          <View>
            <Text className="text-2xl font-display text-[#E8EDF5] mb-2">Your Goals</Text>
            <Text className="text-[#526380] mb-8">Select all that apply</Text>
            <View className="flex-row flex-wrap gap-2">
              {GOAL_OPTIONS.map((goal) => {
                const selected = selectedGoals.includes(goal);
                return (
                  <TouchableOpacity
                    key={goal}
                    onPress={() => toggleGoal(goal)}
                    className={`px-4 py-2 rounded-full border ${
                      selected
                        ? 'bg-primary-500/20 border-primary-500'
                        : 'bg-surface-raised border-surface-border'
                    }`}
                  >
                    <Text className={selected ? 'text-primary-500' : 'text-[#E8EDF5]'} style={{ fontSize: 14 }}>
                      {goal}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>
        )}
      </ScrollView>

      {/* Bottom actions */}
      <View className="px-6 pb-10 pt-4 gap-3">
        {step < 2 ? (
          <TouchableOpacity
            onPress={() => setStep((s) => s + 1)}
            className="bg-primary-500 rounded-xl py-4 items-center"
            activeOpacity={0.8}
          >
            <Text className="text-obsidian-900 font-sansMedium text-base">Continue</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            onPress={handleFinish}
            disabled={loading}
            className="bg-primary-500 rounded-xl py-4 items-center"
            activeOpacity={0.8}
          >
            {loading ? (
              <ActivityIndicator color="#080B10" />
            ) : (
              <Text className="text-obsidian-900 font-sansMedium text-base">Get Started</Text>
            )}
          </TouchableOpacity>
        )}
        <TouchableOpacity
          onPress={() => step > 1 ? setStep((s) => s - 1) : router.replace('/(tabs)/home')}
          className="items-center py-2"
        >
          <Text className="text-[#526380] text-sm">{step > 1 ? 'Back' : 'Skip for now'}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
