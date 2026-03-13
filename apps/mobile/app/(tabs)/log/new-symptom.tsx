import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { router } from 'expo-router';
import { useQueryClient } from '@tanstack/react-query';
import * as Haptics from 'expo-haptics';
import { api } from '@/services/api';

const SYMPTOM_TYPES = ['headache', 'fatigue', 'nausea', 'pain', 'dizziness', 'shortness_of_breath', 'anxiety', 'insomnia', 'other'];

export default function NewSymptomScreen() {
  const [symptomType, setSymptomType] = useState('');
  const [customType, setCustomType] = useState('');
  const [severity, setSeverity] = useState(5);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  async function handleSave() {
    const type = symptomType === 'other' ? customType.trim() : symptomType;
    if (!type) { setError('Please select a symptom type'); return; }
    setLoading(true);
    setError(null);
    try {
      await api.post('/api/v1/symptoms/journal', {
        symptom_type: type,
        severity,
        notes: notes.trim() || null,
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['symptoms'] });
      router.back();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setLoading(false);
    }
  }

  return (
    <View className="flex-1 bg-obsidian-900">
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ padding: 24, paddingTop: 56 }}
        keyboardShouldPersistTaps="handled"
      >
        <Text className="text-2xl font-display text-[#E8EDF5] mb-1">Log Symptom</Text>
        <Text className="text-[#526380] mb-8">What are you experiencing?</Text>

        {/* Type picker */}
        <Text className="text-sm text-[#526380] mb-3">Symptom Type</Text>
        <View className="flex-row flex-wrap gap-2 mb-6">
          {SYMPTOM_TYPES.map((type) => (
            <TouchableOpacity
              key={type}
              onPress={() => setSymptomType(type)}
              className={`px-4 py-2 rounded-full border ${
                symptomType === type ? 'bg-primary-500/20 border-primary-500' : 'bg-surface-raised border-surface-border'
              }`}
            >
              <Text className={`capitalize text-sm ${symptomType === type ? 'text-primary-500' : 'text-[#E8EDF5]'}`}>
                {type.replace('_', ' ')}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {symptomType === 'other' && (
          <View className="mb-6">
            <Text className="text-sm text-[#526380] mb-1">Describe symptom</Text>
            <TextInput
              className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
              value={customType}
              onChangeText={setCustomType}
              placeholder="e.g. joint stiffness"
              placeholderTextColor="#526380"
            />
          </View>
        )}

        {/* Severity */}
        <Text className="text-sm text-[#526380] mb-3">Severity</Text>
        <View className="flex-row gap-2 mb-6">
          {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => {
            const isSelected = severity === n;
            const color = n >= 8 ? '#F87171' : n >= 5 ? '#F5A623' : '#6EE7B7';
            return (
              <TouchableOpacity
                key={n}
                onPress={() => setSeverity(n)}
                className="flex-1 rounded-lg py-2 items-center border"
                style={{
                  borderColor: isSelected ? color : '#232C3A',
                  backgroundColor: isSelected ? `${color}20` : '#12161D',
                }}
              >
                <Text style={{ color: isSelected ? color : '#526380', fontWeight: '600', fontSize: 13 }}>{n}</Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Notes */}
        <Text className="text-sm text-[#526380] mb-1">Notes (optional)</Text>
        <TextInput
          className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
          value={notes}
          onChangeText={setNotes}
          multiline
          numberOfLines={3}
          textAlignVertical="top"
          placeholderTextColor="#526380"
          placeholder="Additional context, triggers, duration..."
        />

        {error && <Text className="text-health-critical text-sm mt-4">{error}</Text>}
      </ScrollView>

      <View className="px-6 pb-10 pt-4 border-t border-surface-border gap-3">
        <TouchableOpacity
          onPress={handleSave}
          disabled={loading}
          className="bg-primary-500 rounded-xl py-4 items-center"
          activeOpacity={0.8}
        >
          {loading ? <ActivityIndicator color="#080B10" /> : (
            <Text className="text-obsidian-900 font-sansMedium text-base">Save Symptom</Text>
          )}
        </TouchableOpacity>
        <TouchableOpacity onPress={() => router.back()} className="items-center py-2">
          <Text className="text-[#526380] text-sm">Cancel</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
