/**
 * Health Profile screen — 4 tabs matching the web app:
 *   1. Conditions  — full CRUD (existing)
 *   2. Questionnaire — adaptive Q&A → POST /api/v1/health-questionnaire
 *   3. Recommendations — patterns + AI summary → GET /api/v1/recommendations
 *   4. Recovery Plan — AI nutrition plan → GET /api/v1/recommendations/recovery-plan
 */

import { useState, useCallback } from 'react';
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

interface HealthQuestion {
  id: string;
  question: string;
  type: 'single_choice' | 'multi_choice' | 'text' | 'scale';
  category: string;
  options?: Array<{ value: string; label: string }>;
  scale_min?: number;
  scale_max?: number;
  required: boolean;
}

interface FoodSuggestion {
  name: string;
  reason: string;
  category: string;
}

interface PatternDetection {
  pattern: string;
  label: string;
  severity: string;
  signals: string[];
  food_suggestions: FoodSuggestion[];
}

interface Recommendation {
  id: string;
  title: string;
  description: string;
  priority: string;
  category: string;
  foods: FoodSuggestion[];
  rationale: string;
}

interface RecommendationsResponse {
  patterns_detected: PatternDetection[];
  recommendations: Recommendation[];
  ai_summary?: string;
  data_quality: string;
}

interface RecoveryPlan {
  title: string;
  overview: string;
  key_focus_areas: string[];
  foods_to_emphasize: FoodSuggestion[];
  foods_to_limit: string[];
  generated_at: string;
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
  mental_health: 'brain-outline' as never,
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

const PATTERN_COLOR: Record<string, string> = {
  overtraining: '#F5A623',
  inflammation: '#F87171',
  poor_recovery: '#818CF8',
  sleep_disruption: '#60A5FA',
};

const PRIORITY_COLOR: Record<string, string> = {
  high: '#F87171',
  medium: '#F5A623',
  low: '#6EE7B7',
};

const TABS = [
  { key: 'conditions',      label: 'Conditions',   icon: 'heart-outline' as const },
  { key: 'questionnaire',   label: 'Questionnaire', icon: 'clipboard-outline' as const },
  { key: 'recommendations', label: 'Recommendations', icon: 'sparkles' as never },
  { key: 'recovery',        label: 'Recovery',      icon: 'leaf-outline' as const },
];

// ─── Shared ───────────────────────────────────────────────────────────────────

function SectionLabel({ children }: Readonly<{ children: string }>) {
  return (
    <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3 mt-2">{children}</Text>
  );
}

// ─── Add/Edit Condition Modal ─────────────────────────────────────────────────

function ConditionModal({
  visible, editing, onClose, onSaved,
}: Readonly<{
  visible: boolean;
  editing: Condition | null;
  onClose: () => void;
  onSaved: () => void;
}>) {
  const [conditionName, setConditionName] = useState(editing?.condition_name ?? '');
  const [category, setCategory] = useState(editing?.condition_category ?? 'other');
  const [severity, setSeverity] = useState<'mild' | 'moderate' | 'severe'>((editing?.severity as never) ?? 'moderate');
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
    setSeverity((editing?.severity as never) ?? 'moderate');
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
                    onPress={() => { setConditionName(item.label); setCategory(item.category); setShowCatalog(false); }}
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
                  style={{ backgroundColor: selected ? `${color}20` : 'transparent', borderColor: selected ? color : '#1E2A3B' }}
                >
                  <Text className="text-sm capitalize font-sansMedium" style={{ color: selected ? color : '#526380' }}>
                    {sev}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Diagnosed Date (optional)</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] mb-5"
            value={diagnosedDate}
            onChangeText={setDiagnosedDate}
            placeholder="YYYY-MM-DD"
            placeholderTextColor="#526380"
            keyboardType="numbers-and-punctuation"
          />

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

          {error ? <Text className="text-health-critical text-sm mb-4">{error}</Text> : null}
          <View style={{ height: 40 }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </Modal>
  );
}

// ─── Condition Card ───────────────────────────────────────────────────────────

function ConditionCard({
  condition, onEdit, onDelete, onToggleActive,
}: Readonly<{
  condition: Condition;
  onEdit: () => void;
  onDelete: () => void;
  onToggleActive: () => void;
}>) {
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
          <Text className="text-xs capitalize font-sansMedium" style={{ color: sevColor }}>{condition.severity}</Text>
        </View>
      </View>

      {condition.notes ? (
        <Text className="text-[#526380] text-xs mt-2 leading-4" numberOfLines={2}>{condition.notes}</Text>
      ) : null}

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

// ─── Tab: Conditions ──────────────────────────────────────────────────────────

function ConditionsTab({ profile }: Readonly<{ profile: Record<string, unknown> | undefined }>) {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Condition | null>(null);
  const [showInactive, setShowInactive] = useState(false);

  const { data: conditions = [], isLoading } = useQuery<Condition[]>({
    queryKey: ['health-conditions'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/health-conditions');
      return (Array.isArray(resp) ? resp : (resp?.conditions ?? [])) as Condition[];
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

  const handleSaved = useCallback(() => {
    setShowModal(false);
    setEditing(null);
    queryClient.invalidateQueries({ queryKey: ['health-conditions'] });
  }, [queryClient]);

  function confirmDelete(id: string, name: string) {
    Alert.alert('Delete Condition', `Remove "${name}"?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: () => deleteMutation.mutate(id) },
    ]);
  }

  const active   = conditions.filter((c) => c.is_active);
  const inactive = conditions.filter((c) => !c.is_active);

  return (
    <>
      <View className="flex-row justify-end mb-4">
        <TouchableOpacity
          onPress={() => { setEditing(null); setShowModal(true); }}
          className="bg-primary-500 rounded-xl px-3 py-2 flex-row items-center gap-1"
        >
          <Ionicons name="add" size={16} color="#080B10" />
          <Text className="text-obsidian-900 font-sansMedium text-sm">Add</Text>
        </TouchableOpacity>
      </View>

      <SectionLabel>Active Conditions ({active.length})</SectionLabel>
      {isLoading ? (
        <ActivityIndicator color="#00D4AA" />
      ) : active.length === 0 ? (
        <TouchableOpacity
          onPress={() => { setEditing(null); setShowModal(true); }}
          className="bg-surface-raised border border-dashed border-surface-border rounded-xl p-5 items-center mb-4"
        >
          <Ionicons name="add-circle-outline" size={28} color="#526380" />
          <Text className="text-[#526380] text-sm mt-2">Add your first health condition</Text>
        </TouchableOpacity>
      ) : (
        active.map((c) => (
          <ConditionCard
            key={c.id}
            condition={c}
            onEdit={() => { setEditing(c); setShowModal(true); }}
            onDelete={() => confirmDelete(c.id, c.condition_name)}
            onToggleActive={() => updateMutation.mutate({ id: c.id, body: { is_active: false } })}
          />
        ))
      )}

      {inactive.length > 0 && (
        <TouchableOpacity onPress={() => setShowInactive((v) => !v)} className="flex-row items-center gap-2 mb-3 mt-2">
          <Ionicons name={showInactive ? 'chevron-up' : 'chevron-down'} size={14} color="#526380" />
          <Text className="text-[#526380] text-xs uppercase tracking-wider">Inactive ({inactive.length})</Text>
        </TouchableOpacity>
      )}
      {showInactive && inactive.map((c) => (
        <ConditionCard
          key={c.id}
          condition={c}
          onEdit={() => { setEditing(c); setShowModal(true); }}
          onDelete={() => confirmDelete(c.id, c.condition_name)}
          onToggleActive={() => updateMutation.mutate({ id: c.id, body: { is_active: true } })}
        />
      ))}

      {Array.isArray(profile?.health_goals) && (profile.health_goals as string[]).length > 0 && (
        <View className="mt-2 mb-4">
          <SectionLabel>Health Goals</SectionLabel>
          <View className="flex-row flex-wrap gap-2">
            {(profile.health_goals as string[]).map((g) => (
              <View key={g} className="bg-primary-500/10 border border-primary-500/30 rounded-full px-3 py-1.5">
                <Text className="text-primary-500 text-xs font-sansMedium">{g}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      <ConditionModal
        visible={showModal}
        editing={editing}
        onClose={() => { setShowModal(false); setEditing(null); }}
        onSaved={handleSaved}
      />
    </>
  );
}

// ─── Tab: Questionnaire ───────────────────────────────────────────────────────

function QuestionnaireTab() {
  const queryClient = useQueryClient();
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [submitted, setSubmitted] = useState(false);

  const { data, isLoading, error } = useQuery<{ questions: HealthQuestion[]; profile_completed: boolean }>({
    queryKey: ['health-questionnaire'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/health-questionnaire');
      return resp;
    },
  });

  const submitMutation = useMutation({
    mutationFn: (ans: Record<string, unknown>) =>
      api.post('/api/v1/health-questionnaire', { answers: ans }),
    onSuccess: async () => {
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['health-questionnaire'] });
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
      setSubmitted(true);
    },
    onError: () => Alert.alert('Error', 'Could not save answers. Please try again.'),
  });

  function setAnswer(id: string, value: unknown) {
    setAnswers((prev) => ({ ...prev, [id]: value }));
  }

  function toggleMulti(id: string, value: string) {
    const current = (answers[id] as string[] | undefined) ?? [];
    const next = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value];
    setAnswer(id, next);
  }

  if (isLoading) return <ActivityIndicator color="#00D4AA" style={{ marginTop: 40 }} />;
  if (error) return (
    <View className="items-center py-10">
      <Ionicons name="alert-circle-outline" size={32} color="#526380" />
      <Text className="text-[#526380] mt-3 text-center">Could not load questionnaire</Text>
    </View>
  );

  if (submitted || data?.profile_completed) {
    return (
      <View className="items-center py-10">
        <View className="w-16 h-16 rounded-full bg-primary-500/20 items-center justify-center mb-4">
          <Ionicons name="checkmark-circle" size={36} color="#00D4AA" />
        </View>
        <Text className="text-[#E8EDF5] font-sansMedium text-lg mb-2">Profile Complete</Text>
        <Text className="text-[#526380] text-sm text-center mb-6">
          Your health profile is set up. Check the Recommendations tab for AI-powered guidance.
        </Text>
        <TouchableOpacity
          onPress={() => { setSubmitted(false); setAnswers({}); queryClient.invalidateQueries({ queryKey: ['health-questionnaire'] }); }}
          className="border border-surface-border rounded-xl px-5 py-2.5"
        >
          <Text className="text-[#526380] text-sm">Retake Questionnaire</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const questions = data?.questions ?? [];

  return (
    <>
      <Text className="text-[#526380] text-sm mb-5">
        Help us personalise your recommendations. Your answers are private and only used to tailor your insights.
      </Text>

      {questions.map((q) => (
        <View key={q.id} className="mb-6">
          <Text className="text-[#E8EDF5] font-sansMedium mb-3 leading-5">{q.question}</Text>

          {(q.type === 'single_choice' || q.type === 'multi_choice') && q.options && (
            <View className="flex-row flex-wrap gap-2">
              {q.options.map((opt) => {
                const isMulti = q.type === 'multi_choice';
                const selected = isMulti
                  ? ((answers[q.id] as string[] | undefined) ?? []).includes(opt.value)
                  : answers[q.id] === opt.value;
                return (
                  <TouchableOpacity
                    key={opt.value}
                    onPress={() => isMulti ? toggleMulti(q.id, opt.value) : setAnswer(q.id, opt.value)}
                    className="px-3 py-2 rounded-full border"
                    style={{
                      backgroundColor: selected ? 'rgba(0,212,170,0.15)' : 'rgba(255,255,255,0.03)',
                      borderColor: selected ? '#00D4AA' : '#1E2A3B',
                    }}
                  >
                    <Text className="text-sm" style={{ color: selected ? '#00D4AA' : '#8A9BB0' }}>
                      {opt.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          )}

          {q.type === 'text' && (
            <TextInput
              className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
              value={(answers[q.id] as string | undefined) ?? ''}
              onChangeText={(v) => setAnswer(q.id, v)}
              placeholder="Your answer…"
              placeholderTextColor="#526380"
              multiline
            />
          )}

          {q.type === 'scale' && (
            <View>
              <View className="flex-row justify-between mb-2">
                {Array.from({ length: (q.scale_max ?? 10) - (q.scale_min ?? 1) + 1 }, (_, i) => {
                  const val = (q.scale_min ?? 1) + i;
                  const selected = answers[q.id] === val;
                  return (
                    <TouchableOpacity
                      key={val}
                      onPress={() => setAnswer(q.id, val)}
                      className="w-9 h-9 rounded-xl items-center justify-center border"
                      style={{
                        backgroundColor: selected ? 'rgba(0,212,170,0.15)' : 'rgba(255,255,255,0.03)',
                        borderColor: selected ? '#00D4AA' : '#1E2A3B',
                      }}
                    >
                      <Text className="text-sm font-sansMedium" style={{ color: selected ? '#00D4AA' : '#526380' }}>
                        {val}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
              <View className="flex-row justify-between">
                <Text className="text-[#3A4A5C] text-xs">Low</Text>
                <Text className="text-[#3A4A5C] text-xs">High</Text>
              </View>
            </View>
          )}
        </View>
      ))}

      {questions.length > 0 && (
        <TouchableOpacity
          onPress={() => submitMutation.mutate(answers)}
          disabled={submitMutation.isPending}
          className="bg-primary-500 rounded-xl py-4 items-center mt-2 mb-6"
        >
          {submitMutation.isPending
            ? <ActivityIndicator color="#080B10" />
            : <Text className="text-obsidian-900 font-sansMedium">Save Answers</Text>}
        </TouchableOpacity>
      )}
    </>
  );
}

// ─── Tab: Recommendations ─────────────────────────────────────────────────────

function RecommendationsTab() {
  const { data, isLoading, error, refetch, isFetching } = useQuery<RecommendationsResponse>({
    queryKey: ['recommendations'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/recommendations');
      return resp;
    },
    staleTime: 15 * 60 * 1000,
  });

  if (isLoading) return <ActivityIndicator color="#00D4AA" style={{ marginTop: 40 }} />;

  if (error || !data) {
    return (
      <View className="items-center py-10">
        <Ionicons name="alert-circle-outline" size={32} color="#526380" />
        <Text className="text-[#526380] mt-3 text-center text-sm">Could not load recommendations</Text>
        <TouchableOpacity onPress={() => refetch()} className="mt-4 border border-surface-border rounded-xl px-4 py-2">
          <Text className="text-[#526380] text-sm">Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (data.data_quality === 'insufficient' || (data.patterns_detected.length === 0 && data.recommendations.length === 0)) {
    return (
      <View className="items-center py-10 px-4">
        <View className="w-16 h-16 rounded-full bg-surface-raised items-center justify-center mb-4">
          <Ionicons name="analytics-outline" size={32} color="#526380" />
        </View>
        <Text className="text-[#E8EDF5] font-sansMedium text-base mb-2">Not enough data yet</Text>
        <Text className="text-[#526380] text-sm text-center leading-5">
          Log meals, symptoms, and complete your weekly check-in to unlock personalised recommendations.
        </Text>
      </View>
    );
  }

  return (
    <>
      <View className="flex-row items-center justify-between mb-4">
        <Text className="text-[#526380] text-xs capitalize">
          Data quality: <Text style={{ color: data.data_quality === 'good' ? '#6EE7B7' : '#F5A623' }}>{data.data_quality}</Text>
        </Text>
        <TouchableOpacity onPress={() => refetch()} disabled={isFetching}>
          <Ionicons name="refresh-outline" size={18} color={isFetching ? '#3A4A5C' : '#526380'} />
        </TouchableOpacity>
      </View>

      {data.patterns_detected.length > 0 && (
        <>
          <SectionLabel>Patterns Detected</SectionLabel>
          {data.patterns_detected.map((p) => {
            const color = PATTERN_COLOR[p.pattern] ?? '#F5A623';
            const sevColor = SEVERITY_COLOR[p.severity] ?? '#F5A623';
            return (
              <View
                key={p.pattern}
                className="rounded-xl p-4 mb-3 border"
                style={{ backgroundColor: `${color}10`, borderColor: `${color}30` }}
              >
                <View className="flex-row items-center justify-between mb-1">
                  <Text className="font-sansMedium" style={{ color }}>{p.label}</Text>
                  <View className="px-2 py-0.5 rounded-full" style={{ backgroundColor: `${sevColor}20` }}>
                    <Text className="text-xs capitalize font-sansMedium" style={{ color: sevColor }}>{p.severity}</Text>
                  </View>
                </View>
                <View className="flex-row flex-wrap gap-1 mt-1">
                  {p.signals.map((s) => (
                    <View key={s} className="bg-surface-raised rounded px-2 py-0.5">
                      <Text className="text-[#526380] text-xs">{s}</Text>
                    </View>
                  ))}
                </View>
              </View>
            );
          })}
        </>
      )}

      {data.ai_summary ? (
        <>
          <SectionLabel>AI Summary</SectionLabel>
          <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-4">
            <View className="flex-row items-center gap-2 mb-2">
              <Ionicons name="sparkles" size={16} color="#00D4AA" />
              <Text className="text-primary-500 text-xs font-sansMedium uppercase tracking-wider">AI Analysis</Text>
            </View>
            <Text className="text-[#C8D5E8] text-sm leading-5">{data.ai_summary}</Text>
          </View>
        </>
      ) : null}

      {data.recommendations.length > 0 && (
        <>
          <SectionLabel>Recommendations</SectionLabel>
          {data.recommendations.map((rec) => {
            const priorityColor = PRIORITY_COLOR[rec.priority] ?? '#6EE7B7';
            return (
              <View key={rec.id} className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-3">
                <View className="flex-row items-start justify-between mb-1">
                  <Text className="text-[#E8EDF5] font-sansMedium flex-1 mr-2">{rec.title}</Text>
                  <View className="px-2 py-0.5 rounded-full" style={{ backgroundColor: `${priorityColor}20` }}>
                    <Text className="text-xs capitalize font-sansMedium" style={{ color: priorityColor }}>{rec.priority}</Text>
                  </View>
                </View>
                <Text className="text-[#526380] text-sm leading-5 mt-1">{rec.description}</Text>
                {rec.rationale ? (
                  <Text className="text-[#3A4A5C] text-xs leading-4 mt-2 italic">{rec.rationale}</Text>
                ) : null}
                {rec.foods.length > 0 && (
                  <View className="flex-row flex-wrap gap-1 mt-3 pt-3 border-t border-surface-border">
                    {rec.foods.slice(0, 4).map((f) => (
                      <View key={f.name} className="bg-surface rounded-lg px-2.5 py-1 flex-row items-center gap-1">
                        <Ionicons name="leaf-outline" size={11} color="#6EE7B7" />
                        <Text className="text-[#6EE7B7] text-xs">{f.name}</Text>
                      </View>
                    ))}
                  </View>
                )}
              </View>
            );
          })}
        </>
      )}
    </>
  );
}

// ─── Tab: Recovery Plan ───────────────────────────────────────────────────────

function RecoveryTab() {
  const { data, isLoading, error, refetch, isFetching } = useQuery<RecoveryPlan>({
    queryKey: ['recovery-plan'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/recommendations/recovery-plan');
      return resp;
    },
    staleTime: 30 * 60 * 1000,
  });

  if (isLoading) return <ActivityIndicator color="#00D4AA" style={{ marginTop: 40 }} />;

  if (error || !data) {
    return (
      <View className="items-center py-10 px-4">
        <View className="w-16 h-16 rounded-full bg-surface-raised items-center justify-center mb-4">
          <Ionicons name="leaf-outline" size={32} color="#526380" />
        </View>
        <Text className="text-[#E8EDF5] font-sansMedium text-base mb-2">Recovery Plan</Text>
        <Text className="text-[#526380] text-sm text-center leading-5">
          Log at least 5 meals and connect a wearable device to generate your personalised recovery nutrition plan.
        </Text>
        <TouchableOpacity onPress={() => refetch()} className="mt-4 border border-surface-border rounded-xl px-4 py-2">
          <Text className="text-[#526380] text-sm">Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <>
      <View className="flex-row items-center justify-between mb-4">
        <Text className="text-[#E8EDF5] font-sansMedium text-base flex-1 mr-3">{data.title}</Text>
        <TouchableOpacity onPress={() => refetch()} disabled={isFetching}>
          <Ionicons name="refresh-outline" size={18} color={isFetching ? '#3A4A5C' : '#526380'} />
        </TouchableOpacity>
      </View>

      <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-4">
        <Text className="text-[#C8D5E8] text-sm leading-5">{data.overview}</Text>
      </View>

      {data.key_focus_areas.length > 0 && (
        <>
          <SectionLabel>Key Focus Areas</SectionLabel>
          <View className="mb-4">
            {data.key_focus_areas.map((area) => (
              <View key={area} className="flex-row items-center gap-2 mb-2">
                <View className="w-1.5 h-1.5 rounded-full bg-primary-500" />
                <Text className="text-[#E8EDF5] text-sm">{area}</Text>
              </View>
            ))}
          </View>
        </>
      )}

      {data.foods_to_emphasize.length > 0 && (
        <>
          <SectionLabel>Foods to Emphasise</SectionLabel>
          <View className="mb-4">
            {data.foods_to_emphasize.map((f) => (
              <View key={f.name} className="bg-surface-raised border border-surface-border rounded-xl p-3 mb-2 flex-row items-start gap-3">
                <View className="w-8 h-8 rounded-lg bg-[#6EE7B7]/10 items-center justify-center mt-0.5">
                  <Ionicons name="leaf-outline" size={15} color="#6EE7B7" />
                </View>
                <View className="flex-1">
                  <Text className="text-[#E8EDF5] font-sansMedium text-sm">{f.name}</Text>
                  <Text className="text-[#526380] text-xs mt-0.5 leading-4">{f.reason}</Text>
                </View>
              </View>
            ))}
          </View>
        </>
      )}

      {data.foods_to_limit.length > 0 && (
        <>
          <SectionLabel>Foods to Limit</SectionLabel>
          <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-4">
            {data.foods_to_limit.map((f, i) => (
              <View key={f} className={`flex-row items-center gap-2 ${i > 0 ? 'mt-2' : ''}`}>
                <Ionicons name="remove-circle-outline" size={14} color="#F87171" />
                <Text className="text-[#C8D5E8] text-sm">{f}</Text>
              </View>
            ))}
          </View>
        </>
      )}
    </>
  );
}

// ─── Profile Card ─────────────────────────────────────────────────────────────

function ProfileCard({ profile }: Readonly<{ profile: Record<string, unknown> | undefined }>) {
  const { user } = useAuthStore();
  const name = (user?.user_metadata?.full_name as string | undefined) ?? user?.email ?? 'User';

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-5 mb-5">
      <View className="flex-row items-center gap-4">
        <View className="w-14 h-14 rounded-full bg-primary-500/20 border border-primary-500/40 items-center justify-center">
          <Text className="text-primary-500 text-xl font-display">{name[0]?.toUpperCase()}</Text>
        </View>
        <View className="flex-1">
          <Text className="text-[#E8EDF5] text-lg font-sansMedium">{name}</Text>
          <Text className="text-[#526380] text-sm">{user?.email}</Text>
        </View>
      </View>
      {(profile?.weight_kg != null || profile?.height_cm != null) && (
        <View className="flex-row gap-4 mt-4 pt-4 border-t border-surface-border">
          {profile?.weight_kg != null && (
            <View className="flex-1 items-center">
              <Text className="text-[#E8EDF5] font-sansMedium">{String(profile.weight_kg)} kg</Text>
              <Text className="text-[#526380] text-xs mt-0.5">Weight</Text>
            </View>
          )}
          {profile?.height_cm != null && (
            <View className="flex-1 items-center">
              <Text className="text-[#E8EDF5] font-sansMedium">{String(profile.height_cm)} cm</Text>
              <Text className="text-[#526380] text-xs mt-0.5">Height</Text>
            </View>
          )}
          {profile?.weight_kg != null && profile?.height_cm != null && (
            <View className="flex-1 items-center">
              <Text className="text-[#E8EDF5] font-sansMedium">
                {(Number(profile.weight_kg) / Math.pow(Number(profile.height_cm) / 100, 2)).toFixed(1)}
              </Text>
              <Text className="text-[#526380] text-xs mt-0.5">BMI</Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function HealthProfileScreen() {
  const [activeTab, setActiveTab] = useState('conditions');

  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/profile/checkin');
      return resp as Record<string, unknown>;
    },
  });

  return (
    <View className="flex-1 bg-obsidian-900">
      {/* Header */}
      <View className="flex-row items-center px-4 pt-14 pb-3 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="p-1 mr-3">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <Text className="text-xl font-display text-[#E8EDF5] flex-1">Health Profile</Text>
      </View>

      {/* Tab bar */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        className="border-b border-surface-border"
        contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 8, gap: 8 }}
      >
        {TABS.map((tab) => {
          const active = activeTab === tab.key;
          return (
            <TouchableOpacity
              key={tab.key}
              onPress={() => setActiveTab(tab.key)}
              className="flex-row items-center gap-1.5 px-3.5 py-2 rounded-full border"
              style={{
                backgroundColor: active ? 'rgba(0,212,170,0.12)' : 'transparent',
                borderColor: active ? '#00D4AA' : '#1E2A3B',
              }}
            >
              <Ionicons name={tab.icon} size={14} color={active ? '#00D4AA' : '#526380'} />
              <Text className="text-sm font-sansMedium" style={{ color: active ? '#00D4AA' : '#526380' }}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      {/* Content */}
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
        keyboardShouldPersistTaps="handled"
      >
        <ProfileCard profile={profile} />

        {activeTab === 'conditions'      && <ConditionsTab profile={profile} />}
        {activeTab === 'questionnaire'   && <QuestionnaireTab />}
        {activeTab === 'recommendations' && <RecommendationsTab />}
        {activeTab === 'recovery'        && <RecoveryTab />}
      </ScrollView>
    </View>
  );
}
