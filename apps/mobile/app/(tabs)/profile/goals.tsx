/**
 * Goals Management Screen — CRUD for health goals with live progress.
 */

import { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, TextInput,
  Modal, ActivityIndicator, Alert,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api } from '@/services/api';

interface Goal {
  id: string;
  goal_text: string;
  category: string;
  status: string;
  due_date?: string;
  notes?: string;
  source?: string;
  is_pinned?: boolean;
}

interface SuggestedGoal {
  text: string;
  category: string;
  reason: string;
}

const CATEGORIES = [
  { key: 'weight', label: 'Weight', icon: 'scale-outline' },
  { key: 'exercise', label: 'Exercise', icon: 'barbell-outline' },
  { key: 'diet', label: 'Diet', icon: 'nutrition-outline' },
  { key: 'sleep', label: 'Sleep', icon: 'moon-outline' },
  { key: 'lab_result', label: 'Lab Result', icon: 'flask-outline' },
  { key: 'medication', label: 'Medication', icon: 'medkit-outline' },
  { key: 'mental_health', label: 'Mental Health', icon: 'happy-outline' },
  { key: 'general', label: 'General', icon: 'flag-outline' },
] as const;

const CAT_COLORS: Record<string, string> = {
  weight: '#F5A623', exercise: '#6EE7B7', diet: '#F5A623', sleep: '#818CF8',
  lab_result: '#60A5FA', medication: '#EC4899', mental_health: '#A78BFA', general: '#00D4AA',
};

// ─── Goal Card ────────────────────────────────────────────────────────────────

function GoalCard({ goal, onComplete, onDelete }: Readonly<{
  goal: Goal;
  onComplete: (id: string) => void;
  onDelete: (id: string) => void;
}>) {
  const color = CAT_COLORS[goal.category] ?? '#526380';
  const catInfo = CATEGORIES.find((c) => c.key === goal.category);
  const isAchieved = goal.status === 'achieved';

  const daysLeft = goal.due_date
    ? Math.ceil((new Date(goal.due_date).getTime() - Date.now()) / 86400000)
    : null;

  return (
    <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2">
      <View className="flex-row items-start gap-3">
        <View className="w-8 h-8 rounded-lg items-center justify-center mt-0.5" style={{ backgroundColor: `${color}15` }}>
          <Ionicons name={(catInfo?.icon ?? 'flag-outline') as never} size={16} color={color} />
        </View>
        <View className="flex-1">
          <Text className="text-[#E8EDF5] font-sansMedium text-sm leading-5" style={isAchieved ? { textDecorationLine: 'line-through', color: '#526380' } : {}}>
            {goal.goal_text}
          </Text>
          <View className="flex-row items-center gap-2 mt-1">
            <Text className="text-[10px] capitalize" style={{ color }}>{goal.category.replace('_', ' ')}</Text>
            {goal.source === 'doctor' && (
              <View className="bg-[#60A5FA12] rounded px-1.5 py-0.5">
                <Text className="text-[#60A5FA] text-[9px]">Doctor</Text>
              </View>
            )}
            {daysLeft != null && daysLeft > 0 && (
              <Text className="text-[#526380] text-[10px]">{daysLeft}d left</Text>
            )}
            {daysLeft != null && daysLeft <= 0 && goal.status === 'active' && (
              <Text className="text-[#F87171] text-[10px]">Overdue</Text>
            )}
          </View>
          {goal.notes && (
            <Text className="text-[#3D4F66] text-[10px] mt-1">{goal.notes}</Text>
          )}
        </View>
        {goal.status === 'active' && (
          <View className="flex-row gap-1">
            <TouchableOpacity onPress={() => onComplete(goal.id)} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
              <Ionicons name="checkmark-circle-outline" size={20} color="#6EE7B7" />
            </TouchableOpacity>
            <TouchableOpacity onPress={() => onDelete(goal.id)} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
              <Ionicons name="close-circle-outline" size={20} color="#F87171" />
            </TouchableOpacity>
          </View>
        )}
      </View>
    </View>
  );
}

// ─── Add Goal Modal ───────────────────────────────────────────────────────────

function AddGoalModal({ visible, onClose, onSaved }: Readonly<{
  visible: boolean;
  onClose: () => void;
  onSaved: () => void;
}>) {
  const [category, setCategory] = useState('general');
  const [text, setText] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [notes, setNotes] = useState('');
  const [source, setSource] = useState<'user' | 'doctor'>('user');
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    if (!text.trim()) return;
    setSaving(true);
    try {
      await api.post('/api/v1/goals', {
        goal_text: text.trim(),
        category,
        due_date: dueDate || null,
        notes: notes.trim() || null,
        source,
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setText('');
      setNotes('');
      setDueDate('');
      onSaved();
      onClose();
    } catch {
      Alert.alert('Error', 'Failed to save goal');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet">
      <View className="flex-1 bg-obsidian-900">
        <View className="flex-row items-center justify-between px-6 pt-14 pb-4 border-b border-surface-border">
          <Text className="text-xl font-display text-[#E8EDF5]">Add Goal</Text>
          <TouchableOpacity onPress={onClose}>
            <Ionicons name="close" size={24} color="#526380" />
          </TouchableOpacity>
        </View>

        <ScrollView className="flex-1 px-6 pt-4" contentContainerStyle={{ paddingBottom: 40 }}>
          {/* Category */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Category</Text>
          <View className="flex-row flex-wrap gap-2 mb-5">
            {CATEGORIES.map((c) => {
              const selected = category === c.key;
              const clr = CAT_COLORS[c.key] ?? '#526380';
              return (
                <TouchableOpacity
                  key={c.key}
                  onPress={() => setCategory(c.key)}
                  className="flex-row items-center gap-1 px-3 py-1.5 rounded-lg"
                  style={{
                    backgroundColor: selected ? `${clr}18` : 'transparent',
                    borderWidth: 1,
                    borderColor: selected ? clr : '#1E2A3B',
                  }}
                  activeOpacity={0.7}
                >
                  <Ionicons name={c.icon as never} size={12} color={selected ? clr : '#526380'} />
                  <Text className="text-xs" style={{ color: selected ? clr : '#526380' }}>{c.label}</Text>
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Goal text */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-1">What's your goal?</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] text-sm mb-4"
            value={text}
            onChangeText={setText}
            placeholder="e.g., Get A1C below 6.5%, Walk 8k steps daily"
            placeholderTextColor="#3D4F66"
            multiline
          />

          {/* Due date */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-1">Due date (optional)</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] text-sm mb-4"
            value={dueDate}
            onChangeText={setDueDate}
            placeholder="YYYY-MM-DD"
            placeholderTextColor="#3D4F66"
          />

          {/* Source */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Source</Text>
          <View className="flex-row gap-2 mb-4">
            {(['user', 'doctor'] as const).map((s) => (
              <TouchableOpacity
                key={s}
                onPress={() => setSource(s)}
                className="flex-1 rounded-lg py-2 items-center"
                style={{
                  backgroundColor: source === s ? '#00D4AA18' : '#12161D',
                  borderWidth: 1,
                  borderColor: source === s ? '#00D4AA' : '#1E2A3B',
                }}
              >
                <Text className="text-xs" style={{ color: source === s ? '#00D4AA' : '#526380' }}>
                  {s === 'user' ? 'My Goal' : 'Doctor Recommended'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Notes */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-1">Notes (optional)</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] text-sm mb-4"
            value={notes}
            onChangeText={setNotes}
            placeholder="Additional context..."
            placeholderTextColor="#3D4F66"
            multiline
          />

          <TouchableOpacity
            onPress={handleSave}
            disabled={saving || !text.trim()}
            className="bg-primary-500 rounded-xl py-3.5 items-center"
            activeOpacity={0.8}
          >
            {saving ? <ActivityIndicator color="#080B10" /> : (
              <Text className="text-obsidian-900 font-sansMedium text-base">Save Goal</Text>
            )}
          </TouchableOpacity>
        </ScrollView>
      </View>
    </Modal>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function GoalsScreen() {
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);

  const { data: goals, isLoading } = useQuery<Goal[]>({
    queryKey: ['goals'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/goals');
      return (Array.isArray(data) ? data : (data?.goals ?? [])) as Goal[];
    },
  });

  const { data: suggested } = useQuery<SuggestedGoal[]>({
    queryKey: ['goals-suggested'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/api/v1/profile-intelligence/goals/suggested');
        return data?.suggestions ?? [];
      } catch { return []; }
    },
    staleTime: 10 * 60_000,
  });

  const completeMutation = useMutation({
    mutationFn: (id: string) => api.put(`/api/v1/goals/${id}`, { status: 'achieved' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['goals'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/goals/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['goals'] }),
  });

  const activeGoals = (goals ?? []).filter((g) => g.status === 'active');
  const achievedGoals = (goals ?? []).filter((g) => g.status === 'achieved');

  return (
    <>
      <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
        <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
          <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
            <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
          </TouchableOpacity>
          <Text className="text-xl font-display text-[#E8EDF5] flex-1">My Goals</Text>
          <TouchableOpacity
            onPress={() => setShowAdd(true)}
            className="bg-primary-500 rounded-xl px-3 py-1.5 flex-row items-center gap-1"
          >
            <Ionicons name="add" size={16} color="#080B10" />
            <Text className="text-obsidian-900 font-sansMedium text-xs">Add</Text>
          </TouchableOpacity>
        </View>

        <View className="px-6 pt-4">
          {isLoading ? (
            <ActivityIndicator color="#00D4AA" className="mt-8" />
          ) : (
            <>
              {/* Active goals */}
              {activeGoals.length > 0 && (
                <View className="mb-4">
                  <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">
                    Active ({activeGoals.length})
                  </Text>
                  {activeGoals.map((g) => (
                    <GoalCard
                      key={g.id}
                      goal={g}
                      onComplete={(id) => completeMutation.mutate(id)}
                      onDelete={(id) => Alert.alert('Delete Goal', 'Are you sure?', [
                        { text: 'Cancel' },
                        { text: 'Delete', style: 'destructive', onPress: () => deleteMutation.mutate(id) },
                      ])}
                    />
                  ))}
                </View>
              )}

              {/* Achieved */}
              {achievedGoals.length > 0 && (
                <View className="mb-4">
                  <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">
                    Achieved ({achievedGoals.length})
                  </Text>
                  {achievedGoals.map((g) => (
                    <GoalCard key={g.id} goal={g} onComplete={() => {}} onDelete={() => {}} />
                  ))}
                </View>
              )}

              {/* Suggested */}
              {suggested && suggested.length > 0 && (
                <View className="mb-4">
                  <Text className="text-[#F5A623] text-xs uppercase tracking-wider mb-2">
                    Suggested for You
                  </Text>
                  {suggested.map((s, i) => {
                    const color = CAT_COLORS[s.category] ?? '#526380';
                    return (
                      <TouchableOpacity
                        key={i}
                        onPress={() => { setShowAdd(true); }}
                        className="bg-surface-raised border border-surface-border rounded-xl p-3 mb-2 flex-row items-center gap-3"
                        activeOpacity={0.7}
                      >
                        <Ionicons name="add-circle-outline" size={18} color={color} />
                        <View className="flex-1">
                          <Text className="text-[#E8EDF5] text-sm">{s.text}</Text>
                          <Text className="text-[#526380] text-[10px] mt-0.5">{s.reason}</Text>
                        </View>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              )}

              {/* Empty state */}
              {activeGoals.length === 0 && achievedGoals.length === 0 && (
                <View className="items-center py-12">
                  <Ionicons name="flag-outline" size={44} color="#526380" />
                  <Text className="text-[#E8EDF5] font-sansMedium text-base mt-3">No goals yet</Text>
                  <Text className="text-[#526380] text-sm mt-1 text-center">
                    Set a health goal to track your progress with real data
                  </Text>
                  <TouchableOpacity
                    onPress={() => setShowAdd(true)}
                    className="mt-4 bg-primary-500 rounded-xl px-5 py-2.5"
                    activeOpacity={0.8}
                  >
                    <Text className="text-obsidian-900 font-sansMedium text-sm">Set Your First Goal</Text>
                  </TouchableOpacity>
                </View>
              )}
            </>
          )}
        </View>
      </ScrollView>

      <AddGoalModal
        visible={showAdd}
        onClose={() => setShowAdd(false)}
        onSaved={() => queryClient.invalidateQueries({ queryKey: ['goals'] })}
      />
    </>
  );
}
