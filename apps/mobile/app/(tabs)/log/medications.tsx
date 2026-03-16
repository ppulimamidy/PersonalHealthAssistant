import { useState } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, RefreshControl, ActivityIndicator,
  Modal, ScrollView, TextInput, Alert, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import * as Haptics from 'expo-haptics';
import { api } from '@/services/api';
import type { Medication } from '@/types';

interface Supplement {
  id: string;
  supplement_name: string;
  brand?: string;
  dosage: string;
  frequency: string;
  form: string;
  purpose?: string;
  is_active: boolean;
}

const ROUTES = ['oral', 'topical', 'injection', 'inhaled'] as const;
const FREQUENCIES = [
  'Once daily', 'Twice daily', 'Three times daily',
  'Every 8 hours', 'Every 12 hours', 'Once weekly', 'As needed',
];

// ─── Edit Modal ──────────────────────────────────────────────────────────────

interface EditModalProps {
  med: Medication | null;
  onClose: () => void;
  onSaved: () => void;
}

function EditMedicationModal({ med, onClose, onSaved }: EditModalProps) {
  const [name, setName] = useState(med?.medication_name ?? '');
  const [dosage, setDosage] = useState(med?.dosage ?? '');
  const [frequency, setFrequency] = useState(() => {
    const f = med?.frequency ?? '';
    return FREQUENCIES.includes(f) ? f : f ? 'custom' : '';
  });
  const [customFrequency, setCustomFrequency] = useState(() => {
    const f = med?.frequency ?? '';
    return FREQUENCIES.includes(f) ? '' : f;
  });
  const [route, setRoute] = useState<typeof ROUTES[number]>(
    (med?.route as typeof ROUTES[number]) ?? 'oral'
  );
  const [indication, setIndication] = useState(med?.indication ?? '');
  const [prescribingDoctor, setPrescribingDoctor] = useState(med?.prescribing_doctor ?? '');
  const [notes, setNotes] = useState(med?.notes ?? '');
  const [isActive, setIsActive] = useState(med?.is_active ?? true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const effectiveFrequency = frequency === 'custom' ? customFrequency : frequency;

  async function handleSave() {
    if (!name.trim()) { setError('Medication name is required'); return; }
    if (!dosage.trim()) { setError('Dosage is required'); return; }
    if (!effectiveFrequency.trim()) { setError('Frequency is required'); return; }

    setError('');
    setLoading(true);
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      await api.put(`/api/v1/medications/medications/${med!.id}`, {
        medication_name: name.trim(),
        dosage: dosage.trim(),
        frequency: effectiveFrequency.trim(),
        route,
        indication: indication.trim() || undefined,
        prescribing_doctor: prescribingDoctor.trim() || undefined,
        notes: notes.trim() || undefined,
        is_active: isActive,
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      onSaved();
    } catch {
      setError('Failed to update medication. Please try again.');
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal visible={!!med} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        className="flex-1 bg-obsidian-900"
      >
        {/* Header */}
        <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
          <TouchableOpacity onPress={onClose} className="mr-4 p-1">
            <Ionicons name="close" size={24} color="#E8EDF5" />
          </TouchableOpacity>
          <Text className="text-xl font-display text-[#E8EDF5] flex-1">Edit Medication</Text>
          <TouchableOpacity
            onPress={handleSave}
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

          {/* Active toggle */}
          <TouchableOpacity
            onPress={() => setIsActive((v) => !v)}
            className={`flex-row items-center justify-between px-4 py-3 rounded-xl border ${
              isActive
                ? 'bg-primary-500/10 border-primary-500/30'
                : 'bg-surface-raised border-surface-border'
            }`}
          >
            <Text className="text-[#E8EDF5] font-sansMedium">Active medication</Text>
            <View className={`w-12 h-6 rounded-full items-center justify-center ${isActive ? 'bg-primary-500' : 'bg-surface-border'}`}>
              <View className={`w-5 h-5 rounded-full bg-white absolute ${isActive ? 'right-0.5' : 'left-0.5'}`} />
            </View>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </Modal>
  );
}

// ─── Adherence Row ────────────────────────────────────────────────────────────

interface AdherenceRowProps {
  med: Medication;
  onLog: (id: string, taken: boolean) => void;
  onEdit: (med: Medication) => void;
  onDelete: (med: Medication) => void;
}

function AdherenceRow({ med, onLog, onEdit, onDelete }: AdherenceRowProps) {
  return (
    <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-3">
      {/* Top row: name + actions */}
      <View className="flex-row items-start justify-between mb-3">
        <View className="flex-1 mr-3">
          <Text className="text-[#E8EDF5] font-sansMedium">{med.medication_name}</Text>
          {med.dosage ? <Text className="text-[#526380] text-sm mt-0.5">{med.dosage}</Text> : null}
          {med.frequency ? <Text className="text-[#526380] text-xs mt-0.5">{med.frequency}</Text> : null}
          {med.indication ? (
            <Text className="text-[#526380] text-xs mt-1 italic">{med.indication}</Text>
          ) : null}
        </View>
        <View className="flex-row gap-1">
          <TouchableOpacity
            onPress={() => onEdit(med)}
            className="bg-surface border border-surface-border rounded-lg p-2"
          >
            <Ionicons name="pencil-outline" size={14} color="#526380" />
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => onDelete(med)}
            className="bg-surface border border-surface-border rounded-lg p-2"
          >
            <Ionicons name="trash-outline" size={14} color="#EF4444" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Bottom row: Taken / Skip */}
      <View className="flex-row gap-2">
        <TouchableOpacity
          onPress={() => onLog(med.id, true)}
          className="flex-1 bg-primary-500/20 border border-primary-500/50 rounded-lg py-2 items-center"
        >
          <Text className="text-primary-500 text-sm font-sansMedium">Taken</Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={() => onLog(med.id, false)}
          className="flex-1 bg-surface border border-surface-border rounded-lg py-2 items-center"
        >
          <Text className="text-[#526380] text-sm">Skip</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ─── Main Screen ──────────────────────────────────────────────────────────────

export default function MedicationsScreen() {
  const queryClient = useQueryClient();
  const [editingMed, setEditingMed] = useState<Medication | null>(null);

  const { data: medications, isLoading, refetch } = useQuery({
    queryKey: ['medications'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/medications');
      return (resp?.medications ?? resp ?? []) as Medication[];
    },
  });

  const { data: supplements, isLoading: supLoading } = useQuery({
    queryKey: ['supplements'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/supplements');
      return (Array.isArray(resp) ? resp : (resp?.supplements ?? [])) as Supplement[];
    },
  });

  const deleteSupMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/supplements/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['supplements'] }),
  });

  const { data: streaks } = useQuery({
    queryKey: ['adherence', 'streaks'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/adherence/streaks');
      return resp;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/medications/medications/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['medications'] }),
  });

  async function handleLog(medicationId: string, wasTaken: boolean) {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      await api.post('/api/v1/adherence/log', {
        medication_id: medicationId,
        was_taken: wasTaken,
        taken_at: new Date().toISOString(),
      });
      queryClient.invalidateQueries({ queryKey: ['adherence'] });
    } catch {
      // Silent fail — non-critical
    }
  }

  function handleDelete(med: Medication) {
    Alert.alert(
      'Delete Medication',
      `Remove "${med.medication_name}" from your medications?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
            deleteMutation.mutate(med.id);
          },
        },
      ]
    );
  }

  const medsList = Array.isArray(medications) ? medications : [];
  const active = medsList.filter((m) => m.is_active);
  const inactive = medsList.filter((m) => !m.is_active);

  return (
    <View className="flex-1 bg-obsidian-900">
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4">
        <View className="flex-1">
          <Text className="text-2xl font-display text-[#E8EDF5]">Medications</Text>
          {streaks?.current_streak > 0 && (
            <View className="flex-row items-center mt-2 bg-amber-500/10 border border-amber-500/30 rounded-xl px-4 py-2 self-start">
              <Ionicons name="flame" size={16} color="#F5A623" />
              <Text className="text-amber-500 text-sm ml-2 font-sansMedium">
                {streaks.current_streak} day streak
              </Text>
            </View>
          )}
        </View>
        <TouchableOpacity
          onPress={() => router.push('/(tabs)/log/new-medication')}
          className="bg-primary-500 rounded-xl px-4 py-2 flex-row items-center gap-1"
        >
          <Ionicons name="add" size={18} color="#080B10" />
          <Text className="text-obsidian-900 font-sansMedium text-sm">Add</Text>
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <ActivityIndicator color="#00D4AA" className="mt-10" />
      ) : (
        <ScrollView
          contentContainerStyle={{ padding: 16, paddingTop: 4, paddingBottom: 40 }}
          refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor="#00D4AA" />}
        >
          {medsList.length === 0 && (
            <View className="items-center py-12">
              <Ionicons name="medical-outline" size={48} color="#526380" />
              <Text className="text-[#526380] mt-4 text-center">No medications added yet</Text>
              <TouchableOpacity
                onPress={() => router.push('/(tabs)/log/new-medication')}
                className="mt-4 bg-primary-500/20 border border-primary-500/40 rounded-xl px-5 py-3"
              >
                <Text className="text-primary-500 font-sansMedium">Add your first medication</Text>
              </TouchableOpacity>
            </View>
          )}

          {active.length > 0 && (
            <>
              <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-3 mt-1">
                Active ({active.length})
              </Text>
              {active.map((med) => (
                <AdherenceRow
                  key={med.id}
                  med={med}
                  onLog={handleLog}
                  onEdit={setEditingMed}
                  onDelete={handleDelete}
                />
              ))}
            </>
          )}

          {inactive.length > 0 && (
            <>
              <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-3 mt-4">
                Inactive ({inactive.length})
              </Text>
              {inactive.map((med) => (
                <AdherenceRow
                  key={med.id}
                  med={med}
                  onLog={handleLog}
                  onEdit={setEditingMed}
                  onDelete={handleDelete}
                />
              ))}
            </>
          )}

          {/* ── Supplements ──────────────────────────────────────── */}
          <View className="mt-6 pt-4 border-t border-surface-border">
            <View className="flex-row items-center justify-between mb-3">
              <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider">
                Supplements {supplements?.length ? `(${supplements.length})` : ''}
              </Text>
            </View>
            {supLoading && <ActivityIndicator color="#00D4AA" size="small" />}
            {!supLoading && (!supplements || supplements.length === 0) && (
              <Text className="text-[#3A4A5C] text-sm mb-2">No supplements added yet.</Text>
            )}
            {supplements?.map((sup) => (
              <View
                key={sup.id}
                className="bg-surface-raised border border-surface-border rounded-xl p-3 mb-2 flex-row items-center"
              >
                <View className="w-9 h-9 rounded-lg items-center justify-center mr-3" style={{ backgroundColor: '#6EE7B718' }}>
                  <Ionicons name="leaf-outline" size={18} color="#6EE7B7" />
                </View>
                <View className="flex-1">
                  <Text className="text-[#E8EDF5] text-sm font-sansMedium">{sup.supplement_name}</Text>
                  <Text className="text-[#526380] text-xs mt-0.5">
                    {sup.dosage}{sup.frequency ? ` · ${sup.frequency}` : ''}{sup.brand ? ` · ${sup.brand}` : ''}
                  </Text>
                  {sup.purpose ? (
                    <Text className="text-[#3A4A5C] text-[10px] mt-0.5">{sup.purpose}</Text>
                  ) : null}
                </View>
                <TouchableOpacity
                  onPress={() => {
                    Alert.alert('Delete Supplement', `Remove "${sup.supplement_name}"?`, [
                      { text: 'Cancel', style: 'cancel' },
                      { text: 'Delete', style: 'destructive', onPress: () => deleteSupMutation.mutate(sup.id) },
                    ]);
                  }}
                  className="p-2"
                >
                  <Ionicons name="trash-outline" size={16} color="#526380" />
                </TouchableOpacity>
              </View>
            ))}
          </View>
        </ScrollView>
      )}

      <EditMedicationModal
        med={editingMed}
        onClose={() => setEditingMed(null)}
        onSaved={() => {
          setEditingMed(null);
          queryClient.invalidateQueries({ queryKey: ['medications'] });
        }}
      />
    </View>
  );
}
