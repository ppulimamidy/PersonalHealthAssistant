import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import Slider from '@react-native-community/slider';
import { router } from 'expo-router';
import { useQueryClient } from '@tanstack/react-query';
import * as Haptics from 'expo-haptics';
import { api } from '@/services/api';

export default function WeeklyCheckinScreen() {
  const [energy, setEnergy] = useState(5);
  const [mood, setMood] = useState(5);
  const [pain, setPain] = useState(3);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  async function handleSubmit() {
    setLoading(true);
    setError(null);
    try {
      await api.post('/api/v1/checkins', {
        energy: Math.round(energy),
        mood: Math.round(mood),
        pain: Math.round(pain),
        notes: notes.trim() || null,
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['checkin'] });
      router.back();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save check-in');
    } finally {
      setLoading(false);
    }
  }

  function SliderRow({ label, value, onChange, color }: {
    label: string; value: number; onChange: (v: number) => void; color: string;
  }) {
    return (
      <View className="mb-6">
        <View className="flex-row justify-between mb-2">
          <Text className="text-[#E8EDF5] font-sansMedium">{label}</Text>
          <Text className="text-primary-500 font-sansMedium text-lg">{Math.round(value)}/10</Text>
        </View>
        <Slider
          minimumValue={0}
          maximumValue={10}
          step={1}
          value={value}
          onValueChange={onChange}
          minimumTrackTintColor={color}
          maximumTrackTintColor="#232C3A"
          thumbTintColor={color}
        />
        <View className="flex-row justify-between mt-1">
          <Text className="text-[#526380] text-xs">Low</Text>
          <Text className="text-[#526380] text-xs">High</Text>
        </View>
      </View>
    );
  }

  return (
    <View className="flex-1 bg-obsidian-900">
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ padding: 24, paddingTop: 56 }}
        keyboardShouldPersistTaps="handled"
      >
        <Text className="text-2xl font-display text-[#E8EDF5] mb-1">Weekly Check-in</Text>
        <Text className="text-[#526380] mb-8">How have you been feeling this week?</Text>

        <SliderRow label="Energy" value={energy} onChange={setEnergy} color="#00D4AA" />
        <SliderRow label="Mood" value={mood} onChange={setMood} color="#6EE7B7" />
        <SliderRow label="Pain" value={pain} onChange={setPain} color="#F87171" />

        <View className="mt-2">
          <Text className="text-sm text-[#526380] mb-2">Notes (optional)</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] text-base"
            value={notes}
            onChangeText={setNotes}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
            placeholderTextColor="#526380"
            placeholder="Any specific observations this week..."
          />
        </View>

        {error && <Text className="text-health-critical text-sm mt-4">{error}</Text>}
      </ScrollView>

      <View className="px-6 pb-10 pt-4 border-t border-surface-border">
        <TouchableOpacity
          onPress={handleSubmit}
          disabled={loading}
          className="bg-primary-500 rounded-xl py-4 items-center"
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator color="#080B10" />
          ) : (
            <Text className="text-obsidian-900 font-sansMedium text-base">Save Check-in</Text>
          )}
        </TouchableOpacity>
        <TouchableOpacity onPress={() => router.back()} className="items-center mt-3 py-2">
          <Text className="text-[#526380] text-sm">Cancel</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
