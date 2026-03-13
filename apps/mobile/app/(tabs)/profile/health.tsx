/**
 * Health Profile screen — view + full CRUD for health conditions.
 *
 * GET    /api/v1/health-conditions
 * GET    /api/v1/health-conditions/catalog
 * POST   /api/v1/health-conditions
 * PUT    /api/v1/health-conditions/{id}
 * DELETE /api/v1/health-conditions/{id}
 */

import { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, ActivityIndicator,
  Modal, TextInput, KeyboardAvoidingView, Platform, Alert,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api } from '@/services/api';
import { useAuthStore } from '@/stores/authStore';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Condition {
  id: string;
  condition_name: string;
  condition_category: string;
  severity: string;
  diagnosed_date?: string;
  notes?: string;
  is_active: boolean;
}

interface CatalogItem {
  key: string;
  label: string;
  category: string;
  tracked_variable_count: number;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const SEVERITY_COLOR: Record<string, string> = {
  mild: '#6EE7B7',
  moderate: '#F5A623',
  severe: '#F87171',
};

const CATEGORY_ICON: Record<string, React.ComponentProps<typeof Ionicons>['name']> = {
  metabolic: 'cellular-outline',
  cardiovascular: 'heart-outline',
  autoimmune: 'shield-outline',
  digestive: 'nutrition-outline',
  mental_health: 'brain-outline' as any,
  other: 'medical-outline',
};

const CATEGORIES = [
  { key: 'metabolic', label: 'Metabolic' },
  { key: 'cardiovascular', label: 'Cardiovascular' },
  { key: 'autoimmune', label: 'Autoimmune' },
  { key: 'digestive', label: 'Digestive' },
  { key: 'mental_health', label: 'Mental Health' },
  { key: 'other', label: 'Other' },
];

const SEVERITIES = ['mild', 'moderate', 'severe'] as const;

// ─── Add/Edit Condition Modal ─────────────────────────────────────────────────

function ConditionModal({
  visible,
  editing,
  onClose,
  onSaved,
}: {
  visible: boolean;
  editing: Condition | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [conditionName, setConditionName] = useState(editing?.condition_name ?? '');
  const [category, setCategory] = useState(editing?.condition_category ?? 'other');
  const [severity, setSeverity] = useState<'mild' | 'moderate' | 'severe'>(
    (editing?.severity as any) ?? 'moderate',
  );
  const [diagnosedDate, setDiagnosedDate] = useState(editing?.diagnosed_date ?? '');
  const [notes, setNotes] = useState(editing?.notes ?? '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalogFilter, setCatalogFilter] = useState('');
  const [showCatalog, setShowCatalog] = useState(false);

  const { data: catalog = [] } = useQuery<CatalogItem[]>({
    queryKey: ['conditions-catalog'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/health-conditions/catalog');
      return Array.isArray(data) ? data : [];
    },
    enabled: visible,
  });

  const filteredCatalog = catalog.filter((c) =>
    c.label.toLowerCase().includes(catalogFilter.toLowerCase()),
  );

  function reset() {
    setConditionName(editing?.condition_name ?? '');
    setCategory(editing?.condition_category ?? 'other');
    setSeverity((editing?.severity as any) ?? 'moderate');
    setDiagnosedDate(editing?.diagnosed_date ?? '');
    setNotes(editing?.notes ?? '');
    setError(null);
    setShowCatalog(false);
    setCatalogFilter('');
  }

  function handleClose() { reset(); onClose(); }

  async function handleSave() {
    if (!conditionName.trim()) { setError('Condition name is required.'); return; }
    setSaving(true);
    setError(null);
    try {
      const body = {
        condition_name: conditionName.trim(),
        condition_category: category,
        severity,
        diagnosed_date: diagnosedDate.trim() || undefined,
        notes: notes.trim() || undefined,
        is_active: true,
      };
      if (editing) {
        await api.put(`/api/v1/health-conditions/${editing.id}`, body);
      } else {
        await api.post('/api/v1/health-conditions', body);
      }
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      reset();
      onSaved();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to save condition');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={handleClose}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} className="flex-1 bg-obsidian-900">
        <View className="flex-row items-center justify-between px-6 pt-14 pb-4 border-b border-surface-border">
          <TouchableOpacity onPress={handleClose}>
            <Text className="text-[#526380] font-sansMedium">Cancel</Text>
          </TouchableOpacity>
          <Text className="text-[#E8EDF5] font-sansMedium text-base">
            {editing ? 'Edit Condition' : 'Add Condition'}
          </Text>
          <TouchableOpacity onPress={handleSave} disabled={saving}>
            {saving ? <ActivityIndicator size="small" color="#00D4AA" /> : (
              <Text className="text-primary-500 font-sansMedium">Save</Text>
            )}
          </TouchableOpacity>
        </View>

        <ScrollView className="flex-1 px-6 pt-5" keyboardShouldPersistTaps="handled">
          {/* Condition name with catalog picker */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Condition Name *</Text>
          <View className="flex-row gap-2 mb-1">
            <TextInput
              className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] flex-1"
              value={conditionName}
              onChangeText={setConditionName}
              placeholder="e.g. Type 2 Diabetes"
              placeholderTextColor="#526380"
            />
            <TouchableOpacity
              onPress={() => setShowCatalog((v) => !v)}
              className="bg-surface-raised border border-surface-border rounded-xl px-3 items-center justify-center"
            >
              <Ionicons name="list" size={18} color="#00D4AA" />
            </TouchableOpacity>
          </View>

          {/* Catalog picker */}
          {showCatalog && (
            <View className="bg-surface border border-surface-border rounded-xl mb-4 overflow-hidden">
              <View className="px-3 py-2 border-b border-surface-border">
                <TextInput
                  className="text-[#E8EDF5] text-sm"
                  value={catalogFilter}
                  onChangeText={setCatalogFilter}
                  placeholder="Search conditions…"
                  placeholderTextColor="#526380"
                />
              </View>
              <ScrollView style={{ maxHeight: 200 }} nestedScrollEnabled>
                {filteredCatalog.slice(0, 30).map((item) => (
                  <TouchableOpacity
                    key={item.key}
                    onPress={() => {
                      setConditionName(item.label);
                      setCategory(item.category);
                      setShowCatalog(false);
                    }}
                    className="px-4 py-2.5 border-b border-surface-border"
                    style={{ borderBottomWidth: 0.5 }}
                  >
                    <Text className="text-[#E8EDF5] text-sm">{item.label}</Text>
                    <Text className="text-[#526380] text-xs capitalize">{item.category.replace('_', ' ')}</Text>
                  </TouchableOpacity>
                ))}
                {filteredCatalog.length === 0 && (
                  <Text className="text-[#526380] text-sm px-4 py-3">No matches</Text>
                )}
              </ScrollView>
            </View>
          )}

          {/* Category */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mt-3 mb-2">Category</Text>
          <View className="flex-row flex-wrap gap-2 mb-5">
            {CATEGORIES.map((cat) => (
              <TouchableOpacity
                key={cat.key}
                onPress={() => setCategory(cat.key)}
                className="px-3 py-2 rounded-xl border"
                style={{
                  backgroundColor: category === cat.key ? 'rgba(0,212,170,0.12)' : 'transparent',
                  borderColor: category === cat.key ? '#00D4AA' : '#1E2A3B',
                }}
              >
                <Text className="text-xs font-sansMedium" style={{ color: category === cat.key ? '#00D4AA' : '#526380' }}>
                  {cat.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Severity */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Severity</Text>
          <View className="flex-row gap-2 mb-5">
            {SEVERITIES.map((sev) => {
              const color = SEVERITY_COLOR[sev];
              const selected = severity === sev;
              return (
                <TouchableOpacity
                  key={sev}
                  onPress={() => setSeverity(sev)}
                  className="flex-1 py-2.5 rounded-xl border items-center"
                  style={{
                    backgroundColor: selected ? `${color}20` : 'transparent',
                    borderColor: selected ? color : '#1E2A3B',
                  }}
                >
                  <Text className="text-sm capitalize font-sansMedium" style={{ color: selected ? color : '#526380' }}>
                    {sev}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Diagnosed date */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Diagnosed Date (optional)</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] mb-5"
            value={diagnosedDate}
            onChangeText={setDiagnosedDate}
            placeholder="YYYY-MM-DD"
            placeholderTextColor="#526380"
            keyboardType="numbers-and-punctuation"
          />

          {/* Notes */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Notes (optional)</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] mb-5"
            value={notes}
            onChangeText={setNotes}
            placeholder="Any relevant details…"
            placeholderTextColor="#526380"
            multiline
            numberOfLines={3}
          />

          {error && <Text className="text-health-critical text-sm mb-4">{error}</Text>}
          <View style={{ height: 40 }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </Modal>
  );
}

// ─── Condition Card ───────────────────────────────────────────────────────────

function ConditionCard({
  condition,
  onEdit,
  onDelete,
  onToggleActive,
}: {
  condition: Condition;
  onEdit: () => void;
  onDelete: () => void;
  onToggleActive: () => void;
}) {
  const sevColor = SEVERITY_COLOR[condition.severity] ?? '#526380';
  const icon = CATEGORY_ICON[condition.condition_category] ?? 'medical-outline';

  return (
    <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2">
      <View className="flex-row items-center gap-3">
        <View className="w-10 h-10 rounded-xl bg-surface items-center justify-center">
          <Ionicons name={icon} size={18} color={condition.is_active ? '#526380' : '#2D3A4D'} />
        </View>
        <View className="flex-1">
          <Text className="text-[#E8EDF5] font-sansMedium" style={{ opacity: condition.is_active ? 1 : 0.5 }}>
            {condition.condition_name}
          </Text>
          <Text className="text-[#526380] text-xs mt-0.5 capitalize">
            {condition.condition_category.replace('_', ' ')}
            {condition.diagnosed_date ? ` · ${condition.diagnosed_date}` : ''}
          </Text>
        </View>
        <View className="px-2.5 py-1 rounded-lg" style={{ backgroundColor: `${sevColor}20` }}>
          <Text className="text-xs capitalize font-sansMedium" style={{ color: sevColor }}>
            {condition.severity}
          </Text>
        </View>
      </View>

      {condition.notes && (
        <Text className="text-[#526380] text-xs mt-2 leading-4" numberOfLines={2}>{condition.notes}</Text>
      )}

      {/* Actions */}
      <View className="flex-row gap-2 mt-3 pt-3 border-t border-surface-border">
        <TouchableOpacity
          onPress={onEdit}
          className="flex-row items-center gap-1 px-3 py-1.5 rounded-lg bg-surface border border-surface-border"
        >
          <Ionicons name="pencil-outline" size={13} color="#526380" />
          <Text className="text-[#526380] text-xs">Edit</Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={onToggleActive}
          className="flex-row items-center gap-1 px-3 py-1.5 rounded-lg bg-surface border border-surface-border"
        >
          <Ionicons name={condition.is_active ? 'pause-outline' : 'play-outline'} size={13} color="#526380" />
          <Text className="text-[#526380] text-xs">{condition.is_active ? 'Mark Inactive' : 'Mark Active'}</Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={onDelete}
          className="flex-row items-center gap-1 px-3 py-1.5 rounded-lg"
          style={{ backgroundColor: 'rgba(248,113,113,0.08)', borderWidth: 1, borderColor: 'rgba(248,113,113,0.2)' }}
        >
          <Ionicons name="trash-outline" size={13} color="#F87171" />
          <Text style={{ color: '#F87171', fontSize: 12 }}>Delete</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

export default function HealthProfileScreen() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const name = (user?.user_metadata?.full_name as string | undefined) ?? user?.email ?? 'User';
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Condition | null>(null);
  const [showInactive, setShowInactive] = useState(false);

  const { data: conditions = [], isLoading: condLoading } = useQuery<Condition[]>({
    queryKey: ['health-conditions'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/health-conditions');
      return (Array.isArray(resp) ? resp : (resp?.conditions ?? [])) as Condition[];
    },
  });

  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/profile/checkin');
      return resp;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/health-conditions/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['health-conditions'] }),
    onError: () => Alert.alert('Error', 'Could not delete condition'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, unknown> }) =>
      api.put(`/api/v1/health-conditions/${id}`, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['health-conditions'] }),
  });

  const handleSaved = () => {
    setShowModal(false);
    setEditing(null);
    queryClient.invalidateQueries({ queryKey: ['health-conditions'] });
  };

  function confirmDelete(id: string, name: string) {
    Alert.alert('Delete Condition', `Remove "${name}"?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: () => deleteMutation.mutate(id) },
    ]);
  }

  const activeConditions = conditions.filter((c) => c.is_active);
  const inactiveConditions = conditions.filter((c) => !c.is_active);

  return (
    <>
      <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 32 }}>
        {/* Header */}
        <View className="flex-row items-center justify-between px-6 pt-14 pb-4 border-b border-surface-border">
          <View className="flex-row items-center gap-3">
            <TouchableOpacity onPress={() => router.back()} className="p-1">
              <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
            </TouchableOpacity>
            <Text className="text-xl font-display text-[#E8EDF5]">Health Profile</Text>
          </View>
          <TouchableOpacity
            onPress={() => { setEditing(null); setShowModal(true); }}
            className="bg-primary-500 rounded-xl px-3 py-2 flex-row items-center gap-1"
            activeOpacity={0.8}
          >
            <Ionicons name="add" size={16} color="#080B10" />
            <Text className="text-obsidian-900 font-sansMedium text-sm">Add</Text>
          </TouchableOpacity>
        </View>

        <View className="px-6 pt-6">
          {/* Profile card */}
          <View className="bg-surface-raised border border-surface-border rounded-2xl p-5 mb-5">
            <View className="flex-row items-center gap-4">
              <View className="w-16 h-16 rounded-full bg-primary-500/20 border border-primary-500/40 items-center justify-center">
                <Text className="text-primary-500 text-2xl font-display">{name[0]?.toUpperCase()}</Text>
              </View>
              <View className="flex-1">
                <Text className="text-[#E8EDF5] text-lg font-sansMedium">{name}</Text>
                <Text className="text-[#526380] text-sm">{user?.email}</Text>
              </View>
            </View>
            {(profile?.weight_kg || profile?.height_cm) && (
              <View className="flex-row gap-4 mt-4 pt-4 border-t border-surface-border">
                {profile?.weight_kg && (
                  <View className="flex-1 items-center">
                    <Text className="text-[#E8EDF5] font-sansMedium">{profile.weight_kg} kg</Text>
                    <Text className="text-[#526380] text-xs mt-0.5">Weight</Text>
                  </View>
                )}
                {profile?.height_cm && (
                  <View className="flex-1 items-center">
                    <Text className="text-[#E8EDF5] font-sansMedium">{profile.height_cm} cm</Text>
                    <Text className="text-[#526380] text-xs mt-0.5">Height</Text>
                  </View>
                )}
                {profile?.weight_kg && profile?.height_cm && (
                  <View className="flex-1 items-center">
                    <Text className="text-[#E8EDF5] font-sansMedium">
                      {(profile.weight_kg / Math.pow(profile.height_cm / 100, 2)).toFixed(1)}
                    </Text>
                    <Text className="text-[#526380] text-xs mt-0.5">BMI</Text>
                  </View>
                )}
              </View>
            )}
          </View>

          {/* Active Conditions */}
          <View className="mb-5">
            <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3">
              Active Conditions ({activeConditions.length})
            </Text>
            {condLoading ? (
              <ActivityIndicator color="#00D4AA" />
            ) : activeConditions.length === 0 ? (
              <TouchableOpacity
                onPress={() => { setEditing(null); setShowModal(true); }}
                className="bg-surface-raised border border-dashed border-surface-border rounded-xl p-5 items-center"
              >
                <Ionicons name="add-circle-outline" size={28} color="#526380" />
                <Text className="text-[#526380] text-sm mt-2">Add your first health condition</Text>
              </TouchableOpacity>
            ) : (
              activeConditions.map((condition) => (
                <ConditionCard
                  key={condition.id}
                  condition={condition}
                  onEdit={() => { setEditing(condition); setShowModal(true); }}
                  onDelete={() => confirmDelete(condition.id, condition.condition_name)}
                  onToggleActive={() => updateMutation.mutate({ id: condition.id, body: { is_active: false } })}
                />
              ))
            )}
          </View>

          {/* Inactive toggle */}
          {inactiveConditions.length > 0 && (
            <TouchableOpacity
              onPress={() => setShowInactive((v) => !v)}
              className="flex-row items-center gap-2 mb-3"
            >
              <Ionicons name={showInactive ? 'chevron-up' : 'chevron-down'} size={14} color="#526380" />
              <Text className="text-[#526380] text-xs uppercase tracking-wider">
                Inactive ({inactiveConditions.length})
              </Text>
            </TouchableOpacity>
          )}
          {showInactive && inactiveConditions.map((condition) => (
            <ConditionCard
              key={condition.id}
              condition={condition}
              onEdit={() => { setEditing(condition); setShowModal(true); }}
              onDelete={() => confirmDelete(condition.id, condition.condition_name)}
              onToggleActive={() => updateMutation.mutate({ id: condition.id, body: { is_active: true } })}
            />
          ))}

          {/* Goals */}
          {profile?.health_goals?.length > 0 && (
            <View className="mb-5">
              <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3">Health Goals</Text>
              <View className="flex-row flex-wrap gap-2">
                {(profile.health_goals as string[]).map((goal) => (
                  <View key={goal} className="bg-primary-500/10 border border-primary-500/30 rounded-full px-3 py-1.5">
                    <Text className="text-primary-500 text-xs font-sansMedium">{goal}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}
        </View>
      </ScrollView>

      <ConditionModal
        visible={showModal}
        editing={editing}
        onClose={() => { setShowModal(false); setEditing(null); }}
        onSaved={handleSaved}
      />
    </>
  );
}
