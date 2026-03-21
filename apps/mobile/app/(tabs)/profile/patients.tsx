/**
 * Phase 5: Patients screen (Provider / Caregiver role only).
 * View health summaries of patients who have shared access with the current user.
 *
 * GET /api/v1/caregiver/managed       — list managed profiles
 * GET /api/v1/share/public/{token}   — per-patient summary (public, no auth)
 */

import { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, ActivityIndicator,
  FlatList, TextInput, Alert,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import * as Haptics from 'expo-haptics';
import { api } from '@/services/api';
import type { ManagedProfile, SharedHealthSummary } from '@/types';

// ─── Patient detail panel ──────────────────────────────────────────────────────

function PatientDetail({ shareToken, onClose }: { shareToken: string; onClose: () => void }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['patient-summary', shareToken],
    queryFn: async () => {
      const { data: resp } = await api.get(`/api/v1/share/public/${shareToken}`);
      return resp as SharedHealthSummary;
    },
  });

  const profile = data?.profile as Record<string, unknown> | undefined;
  const abnormalLabs = (data?.lab_results ?? []).filter((l) => l.is_abnormal).length;
  const highSymptoms = (data?.symptoms ?? []).filter((s) => (s.severity ?? 0) >= 7).length;

  function calcAge(dob?: unknown): string {
    if (typeof dob !== 'string') return '—';
    const d = new Date(dob);
    const now = new Date();
    let age = now.getFullYear() - d.getFullYear();
    if (now.getMonth() < d.getMonth() || (now.getMonth() === d.getMonth() && now.getDate() < d.getDate())) age--;
    return String(age);
  }

  const patientName = data?.label ?? 'Patient';

  return (
    <View className="flex-1 bg-obsidian-900">
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={onClose} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <View className="flex-1">
          <Text className="text-xl font-display text-[#E8EDF5]">{patientName}</Text>
          <Text className="text-[#526380] text-xs mt-0.5">Shared health summary · read-only</Text>
        </View>
      </View>

      {/* 6B: Viewing-as context banner */}
      <View className="mx-4 mt-3 flex-row items-center gap-2 bg-indigo-500/10 border border-indigo-500/25 rounded-xl px-3 py-2.5">
        <Ionicons name="eye-outline" size={15} color="#818CF8" />
        <Text className="text-indigo-400 text-xs flex-1">
          Viewing <Text className="font-sansMedium">{patientName}</Text>'s shared health data
        </Text>
      </View>

      {isLoading && (
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator color="#00D4AA" />
          <Text className="text-[#526380] text-sm mt-3">Loading patient data…</Text>
        </View>
      )}

      {isError && (
        <View className="flex-1 items-center justify-center px-8">
          <Ionicons name="alert-circle-outline" size={40} color="#F87171" />
          <Text className="text-[#F87171] font-sansMedium mt-3">Failed to load</Text>
          <Text className="text-[#526380] text-sm mt-1 text-center">
            The patient may have revoked access or the share token has expired.
          </Text>
        </View>
      )}

      {data && (
        <ScrollView className="flex-1" contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
          {/* Stat chips */}
          <View className="flex-row gap-2 mb-4">
            {[
              { label: 'Age', value: calcAge(profile?.date_of_birth), warn: false },
              { label: 'Adherence', value: data.medication_adherence_pct !== undefined ? `${data.medication_adherence_pct}%` : '—', warn: (data.medication_adherence_pct ?? 100) < 70 },
              { label: 'Abnormal Labs', value: abnormalLabs, warn: abnormalLabs > 0 },
              { label: 'High Symptoms', value: highSymptoms, warn: highSymptoms > 0 },
            ].map(({ label, value, warn }) => (
              <View key={label} className="flex-1 rounded-xl items-center py-3 px-2"
                style={{
                  backgroundColor: warn ? 'rgba(248,113,113,0.08)' : 'rgba(255,255,255,0.04)',
                  borderWidth: 1,
                  borderColor: warn ? 'rgba(248,113,113,0.2)' : 'rgba(255,255,255,0.06)',
                }}>
                <Text style={{ color: warn ? '#F87171' : '#00D4AA', fontSize: 18, fontWeight: '700' }}>
                  {value}
                </Text>
                <Text className="text-[#526380] text-[10px] mt-0.5 text-center">{label}</Text>
              </View>
            ))}
          </View>

          {/* Conditions */}
          {(data.conditions ?? []).length > 0 && (
            <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
              <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Conditions</Text>
              <View className="flex-row flex-wrap gap-2">
                {(data.conditions ?? []).map((c, i) => (
                  <View key={i} className="rounded-full px-2.5 py-1" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }}>
                    <Text className="text-[#C8D5E8] text-xs">{c}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Medications */}
          {(data.medications ?? []).length > 0 && (
            <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
              <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">
                Active Medications ({data.medications!.length})
              </Text>
              {data.medications!.slice(0, 8).map((m, i) => (
                <View key={i} className="flex-row items-center justify-between py-1.5"
                  style={{ borderTopWidth: i > 0 ? 1 : 0, borderTopColor: 'rgba(255,255,255,0.04)' }}>
                  <Text className="text-[#C8D5E8] text-sm">{m.name}</Text>
                  <Text className="text-[#526380] text-xs">{m.dosage}</Text>
                </View>
              ))}
              {data.medications!.length > 8 && (
                <Text className="text-[#3D4F66] text-xs mt-1">+{data.medications!.length - 8} more</Text>
              )}
            </View>
          )}

          {/* Abnormal labs */}
          {abnormalLabs > 0 && (
            <View className="bg-surface-raised border border-health-critical/20 rounded-2xl p-4 mb-3">
              <Text className="text-health-critical text-xs uppercase tracking-wider mb-2">
                Abnormal Lab Values
              </Text>
              {(data.lab_results ?? []).filter((l) => l.is_abnormal).slice(0, 8).map((lab, i) => (
                <View key={i} className="flex-row items-center justify-between py-1.5"
                  style={{ borderTopWidth: i > 0 ? 1 : 0, borderTopColor: 'rgba(255,255,255,0.04)' }}>
                  <Text className="text-[#C8D5E8] text-sm">{lab.test_name}</Text>
                  <Text className="text-health-critical text-sm font-sansMedium">
                    {lab.value} {lab.unit}
                  </Text>
                </View>
              ))}
            </View>
          )}

          {/* Recent symptoms */}
          {(data.symptoms ?? []).length > 0 && (
            <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
              <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Recent Symptoms</Text>
              {(data.symptoms ?? []).slice(0, 5).map((s, i) => (
                <View key={i} className="flex-row items-center justify-between py-1.5"
                  style={{ borderTopWidth: i > 0 ? 1 : 0, borderTopColor: 'rgba(255,255,255,0.04)' }}>
                  <Text className="text-[#C8D5E8] text-sm capitalize">{s.symptom_name}</Text>
                  <View className="flex-row items-center gap-2">
                    <Text style={{ color: (s.severity ?? 0) >= 7 ? '#F87171' : '#526380', fontSize: 13 }}>
                      Sev {s.severity}
                    </Text>
                  </View>
                </View>
              ))}
            </View>
          )}

          {/* Care plans */}
          {(data.care_plans ?? []).length > 0 && (
            <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
              <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Care Plans</Text>
              {(data.care_plans ?? []).slice(0, 3).map((cp, i) => (
                <View key={i} className="py-1.5"
                  style={{ borderTopWidth: i > 0 ? 1 : 0, borderTopColor: 'rgba(255,255,255,0.04)' }}>
                  <Text className="text-[#C8D5E8] text-sm">{cp.title}</Text>
                </View>
              ))}
            </View>
          )}
        </ScrollView>
      )}
    </View>
  );
}

// ─── Patient row ───────────────────────────────────────────────────────────────

function PatientRow({ profile, onPress }: { profile: ManagedProfile; onPress: () => void }) {
  const addedDate = format(new Date(profile.added_at), 'MMM d');

  return (
    <TouchableOpacity
      onPress={onPress}
      className="flex-row items-center bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3"
      activeOpacity={0.7}
    >
      <View className="w-12 h-12 rounded-full bg-primary-500/15 border border-primary-500/30 items-center justify-center mr-4">
        <Text className="text-primary-500 text-lg font-display">
          {(profile.display_name ?? 'P')[0].toUpperCase()}
        </Text>
      </View>
      <View className="flex-1">
        <Text className="text-[#E8EDF5] font-sansMedium">{profile.display_name ?? 'Patient'}</Text>
        <Text className="text-[#526380] text-xs mt-0.5">
          {profile.relationship ?? 'Patient'} · Added {addedDate}
        </Text>
      </View>
      <Ionicons name="chevron-forward" size={16} color="#526380" />
    </TouchableOpacity>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

export default function PatientsScreen() {
  const queryClient = useQueryClient();
  const [selectedToken, setSelectedToken] = useState<string | null>(null);
  const [addInput, setAddInput] = useState('');
  const [adding, setAdding] = useState(false);

  async function handleAddPatient() {
    const raw = addInput.trim();
    if (!raw) return;
    // Parse token from URL or use raw
    const token = raw.includes('/share/') ? raw.split('/share/')[1].split(/[/?#]/)[0] : raw;
    if (!token) return;
    setAdding(true);
    try {
      await api.post('/api/v1/caregiver/managed', { token });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setAddInput('');
      queryClient.invalidateQueries({ queryKey: ['managed-profiles'] });
    } catch {
      Alert.alert('Error', 'Could not add patient. Check the share code or URL.');
    } finally {
      setAdding(false);
    }
  }

  const { data: profiles = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['managed-profiles'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/caregiver/managed');
      return (Array.isArray(data) ? data : (data?.profiles ?? [])) as ManagedProfile[];
    },
  });

  if (selectedToken) {
    return <PatientDetail shareToken={selectedToken} onClose={() => setSelectedToken(null)} />;
  }

  return (
    <View className="flex-1 bg-obsidian-900">
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <View className="flex-1">
          <Text className="text-xl font-display text-[#E8EDF5]">Patients</Text>
          <Text className="text-[#526380] text-xs mt-0.5">Shared health summaries</Text>
        </View>
      </View>

      {/* Add patient input */}
      <View className="px-4 py-3 border-b border-surface-border">
        <View className="flex-row gap-2">
          <TextInput
            value={addInput}
            onChangeText={setAddInput}
            placeholder="Paste share code or URL..."
            placeholderTextColor="#3D4F66"
            onSubmitEditing={handleAddPatient}
            returnKeyType="done"
            className="flex-1 bg-surface-raised border border-surface-border rounded-xl px-3 py-2.5 text-[#E8EDF5] text-sm"
          />
          <TouchableOpacity
            onPress={handleAddPatient}
            disabled={adding || !addInput.trim()}
            className="bg-primary-500 rounded-xl px-4 items-center justify-center"
            activeOpacity={0.8}
          >
            {adding ? (
              <ActivityIndicator color="#080B10" size="small" />
            ) : (
              <Ionicons name="add" size={18} color="#080B10" />
            )}
          </TouchableOpacity>
        </View>
      </View>

      {isLoading && (
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator color="#00D4AA" />
        </View>
      )}

      {isError && (
        <View className="flex-1 items-center justify-center px-8">
          <Ionicons name="people-outline" size={48} color="#526380" />
          <Text className="text-[#E8EDF5] font-sansMedium mt-4">Access Restricted</Text>
          <Text className="text-[#526380] text-sm text-center mt-2">
            This screen is available to users with caregiver or provider access.
          </Text>
          <TouchableOpacity onPress={() => refetch()} className="mt-4 px-4 py-2.5 rounded-xl bg-surface-raised border border-surface-border">
            <Text className="text-[#E8EDF5] text-sm">Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {!isLoading && !isError && (
        <FlatList
          data={profiles}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
          renderItem={({ item }) => (
            <PatientRow
              profile={item}
              onPress={() => setSelectedToken(item.share_token)}
            />
          )}
          ListEmptyComponent={
            <View className="items-center py-16">
              <Ionicons name="people-outline" size={48} color="#526380" />
              <Text className="text-[#E8EDF5] font-sansMedium mt-4">No Patients Yet</Text>
              <Text className="text-[#526380] text-sm text-center mt-2 px-4">
                Patients appear here when they share their health summary with you.
                Ask them to generate a share link from their Settings screen.
              </Text>
            </View>
          }
        />
      )}
    </View>
  );
}
