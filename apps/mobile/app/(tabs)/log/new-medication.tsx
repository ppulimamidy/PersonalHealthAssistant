import { useState } from 'react';
import {
  View, Text, ScrollView, TextInput, TouchableOpacity,
  KeyboardAvoidingView, Platform, ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api } from '@/services/api';

const ROUTES = ['oral', 'topical', 'injection', 'inhaled'] as const;
const FREQUENCIES = [
  'Once daily', 'Twice daily', 'Three times daily',
  'Every 8 hours', 'Every 12 hours', 'Once weekly', 'As needed',
];

export default function NewMedicationScreen() {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [name, setName] = useState('');
  const [genericName, setGenericName] = useState('');
  const [dosage, setDosage] = useState('');
  const [frequency, setFrequency] = useState('');
  const [customFrequency, setCustomFrequency] = useState('');
  const [route, setRoute] = useState<typeof ROUTES[number]>('oral');
  const [indication, setIndication] = useState('');
  const [prescribingDoctor, setPrescribingDoctor] = useState('');
  const [notes, setNotes] = useState('');

  const effectiveFrequency = frequency === 'custom' ? customFrequency : frequency;

  async function handleSubmit() {
    if (!name.trim()) { setError('Medication name is required'); return; }
    if (!dosage.trim()) { setError('Dosage is required'); return; }
    if (!effectiveFrequency.trim()) { setError('Frequency is required'); return; }

    setError('');
    setLoading(true);
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      await api.post('/api/v1/medications', {
        medication_name: name.trim(),
        generic_name: genericName.trim() || undefined,
        dosage: dosage.trim(),
        frequency: effectiveFrequency.trim(),
        route,
        indication: indication.trim() || undefined,
        prescribing_doctor: prescribingDoctor.trim() || undefined,
        notes: notes.trim() || undefined,
        is_active: true,
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['medications'] });
      router.back();
    } catch {
      setError('Failed to save medication. Please try again.');
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      className="flex-1 bg-obsidian-900"
    >
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <Text className="text-xl font-display text-[#E8EDF5] flex-1">Add Medication</Text>
        <TouchableOpacity
          onPress={handleSubmit}
          disabled={loading}
          className="bg-primary-500 px-4 py-2 rounded-xl"
        >
          {loading
            ? <ActivityIndicator size="small" color="#080B10" />
            : <Text className="text-obsidian-900 font-sansMedium text-sm">Save</Text>
          }
        </TouchableOpacity>
      </View>

      <ScrollView
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={{ padding: 24, paddingBottom: 48 }}
      >
        {error ? (
          <View className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 mb-5">
            <Text className="text-red-400 text-sm">{error}</Text>
          </View>
        ) : null}

        {/* Medication Name */}
        <View className="mb-5">
          <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
            Medication Name *
          </Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
            placeholder="e.g. Metformin, Lisinopril"
            placeholderTextColor="#526380"
            value={name}
            onChangeText={setName}
            autoCapitalize="words"
          />
        </View>

        {/* Generic Name */}
        <View className="mb-5">
          <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
            Generic Name (optional)
          </Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
            placeholder="e.g. metformin hydrochloride"
            placeholderTextColor="#526380"
            value={genericName}
            onChangeText={setGenericName}
            autoCapitalize="words"
          />
        </View>

        {/* Dosage */}
        <View className="mb-5">
          <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
            Dosage *
          </Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
            placeholder="e.g. 500mg, 10mg/5ml"
            placeholderTextColor="#526380"
            value={dosage}
            onChangeText={setDosage}
          />
        </View>

        {/* Frequency */}
        <View className="mb-5">
          <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
            Frequency *
          </Text>
          <View className="flex-row flex-wrap gap-2 mb-2">
            {FREQUENCIES.map((f) => (
              <TouchableOpacity
                key={f}
                onPress={() => setFrequency(f)}
                className={`px-3 py-2 rounded-lg border ${
                  frequency === f
                    ? 'bg-primary-500/20 border-primary-500/60'
                    : 'bg-surface-raised border-surface-border'
                }`}
              >
                <Text className={`text-sm ${frequency === f ? 'text-primary-500' : 'text-[#E8EDF5]'}`}>
                  {f}
                </Text>
              </TouchableOpacity>
            ))}
            <TouchableOpacity
              onPress={() => setFrequency('custom')}
              className={`px-3 py-2 rounded-lg border ${
                frequency === 'custom'
                  ? 'bg-primary-500/20 border-primary-500/60'
                  : 'bg-surface-raised border-surface-border'
              }`}
            >
              <Text className={`text-sm ${frequency === 'custom' ? 'text-primary-500' : 'text-[#E8EDF5]'}`}>
                Custom…
              </Text>
            </TouchableOpacity>
          </View>
          {frequency === 'custom' && (
            <TextInput
              className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
              placeholder="Describe frequency..."
              placeholderTextColor="#526380"
              value={customFrequency}
              onChangeText={setCustomFrequency}
            />
          )}
        </View>

        {/* Route */}
        <View className="mb-5">
          <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
            Route of Administration
          </Text>
          <View className="flex-row gap-2">
            {ROUTES.map((r) => (
              <TouchableOpacity
                key={r}
                onPress={() => setRoute(r)}
                className={`flex-1 py-2.5 rounded-xl border items-center ${
                  route === r
                    ? 'bg-primary-500/20 border-primary-500/60'
                    : 'bg-surface-raised border-surface-border'
                }`}
              >
                <Text className={`text-xs capitalize ${route === r ? 'text-primary-500' : 'text-[#E8EDF5]'}`}>
                  {r}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Indication */}
        <View className="mb-5">
          <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
            What is it for? (optional)
          </Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
            placeholder="e.g. Type 2 diabetes, blood pressure"
            placeholderTextColor="#526380"
            value={indication}
            onChangeText={setIndication}
            autoCapitalize="sentences"
          />
        </View>

        {/* Prescribing Doctor */}
        <View className="mb-5">
          <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
            Prescribing Doctor (optional)
          </Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
            placeholder="e.g. Dr. Sarah Smith"
            placeholderTextColor="#526380"
            value={prescribingDoctor}
            onChangeText={setPrescribingDoctor}
            autoCapitalize="words"
          />
        </View>

        {/* Notes */}
        <View className="mb-5">
          <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
            Notes (optional)
          </Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
            placeholder="Any additional notes..."
            placeholderTextColor="#526380"
            value={notes}
            onChangeText={setNotes}
            multiline
            numberOfLines={3}
            textAlignVertical="top"
            style={{ minHeight: 80 }}
          />
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
