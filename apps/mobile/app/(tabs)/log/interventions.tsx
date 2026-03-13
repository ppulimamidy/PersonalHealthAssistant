/**
 * Phase 5: N-of-1 Interventions / Experiments screen.
 * Try a dietary or lifestyle change for a set number of days and measure
 * whether it actually moves your health metrics.
 *
 * GET    /api/v1/interventions               list all
 * POST   /api/v1/interventions               start new
 * POST   /api/v1/interventions/{id}/checkin  daily adherence log
 * POST   /api/v1/interventions/{id}/complete complete + get outcome
 * PATCH  /api/v1/interventions/{id}/abandon  abandon
 */

import { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, ActivityIndicator,
  Modal, TextInput, Alert,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { format, differenceInDays, parseISO } from 'date-fns';
import { api } from '@/services/api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { ActiveIntervention, InterventionOutcome, InterventionPattern } from '@/types';

// ─── Constants ─────────────────────────────────────────────────────────────────

type Tab = 'active' | 'completed' | 'all';

const PATTERN_OPTIONS: Array<{ value: InterventionPattern; label: string; description: string }> = [
  { value: 'overtraining',    label: 'Overtraining Recovery',  description: 'Anti-inflammatory + magnesium-rich foods to support recovery' },
  { value: 'inflammation',    label: 'Inflammation Reduction', description: 'Lower glycemic load, omega-3 focus' },
  { value: 'poor_recovery',   label: 'Recovery Boost',         description: 'Protein-forward + recovery-focused nutrition' },
  { value: 'sleep_disruption', label: 'Sleep Optimisation',   description: 'Earlier dinner window + sleep-promoting foods' },
];

// ─── Helpers ───────────────────────────────────────────────────────────────────

function progressPercent(iv: ActiveIntervention): number {
  const total = iv.duration_days;
  const elapsed = differenceInDays(new Date(), parseISO(iv.started_at));
  return Math.min(100, Math.round((Math.max(0, elapsed) / total) * 100));
}

// ─── Start Modal ───────────────────────────────────────────────────────────────

function StartModal({ onClose, onStarted }: {
  onClose: () => void;
  onStarted: (iv: ActiveIntervention) => void;
}) {
  const [pattern, setPattern] = useState<InterventionPattern>('poor_recovery');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [duration, setDuration] = useState(7);
  const [showPatterns, setShowPatterns] = useState(false);

  const { mutate: start, isPending, error } = useMutation({
    mutationFn: async () => {
      if (!title.trim()) throw new Error('Please enter a title for this experiment');
      const { data } = await api.post('/api/v1/interventions', {
        recommendation_pattern: pattern,
        title: title.trim(),
        description: description.trim() || undefined,
        duration_days: duration,
      });
      return data as ActiveIntervention;
    },
    onSuccess: (iv) => {
      onStarted(iv);
    },
    onError: (err: Error) => {
      Alert.alert('Error', err.message || 'Failed to start experiment');
    },
  });

  const selectedPattern = PATTERN_OPTIONS.find((o) => o.value === pattern)!;

  return (
    <Modal visible animationType="slide" transparent>
      <View className="flex-1 justify-end bg-black/60">
        <View className="bg-obsidian-900 rounded-t-3xl p-6 border-t border-surface-border">
          <View className="flex-row items-center mb-4">
            <Text className="text-[#E8EDF5] font-display text-lg flex-1">Start an Experiment</Text>
            <TouchableOpacity onPress={onClose}>
              <Ionicons name="close" size={22} color="#526380" />
            </TouchableOpacity>
          </View>
          <Text className="text-[#526380] text-sm leading-5 mb-5">
            Try something for a week and measure whether it actually moves your numbers.
          </Text>

          {/* Pattern selector */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Pattern</Text>
          <TouchableOpacity
            onPress={() => setShowPatterns((v) => !v)}
            className="flex-row items-center bg-surface-raised border border-surface-border rounded-xl px-4 py-3 mb-1"
          >
            <Text className="text-[#E8EDF5] text-sm flex-1">{selectedPattern.label}</Text>
            <Ionicons name={showPatterns ? 'chevron-up' : 'chevron-down'} size={16} color="#526380" />
          </TouchableOpacity>
          {showPatterns && (
            <View className="bg-surface-raised border border-surface-border rounded-xl mb-4 overflow-hidden">
              {PATTERN_OPTIONS.map((opt) => (
                <TouchableOpacity
                  key={opt.value}
                  onPress={() => { setPattern(opt.value); setShowPatterns(false); }}
                  className="px-4 py-3 border-b border-surface-border"
                  style={opt.value === pattern ? { backgroundColor: 'rgba(0,212,170,0.06)' } : {}}
                >
                  <Text style={{ color: opt.value === pattern ? '#00D4AA' : '#E8EDF5', fontSize: 14 }}>
                    {opt.label}
                  </Text>
                  <Text className="text-[#526380] text-xs mt-0.5">{opt.description}</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
          {!showPatterns && (
            <Text className="text-[#526380] text-xs mb-4 -mt-0.5">{selectedPattern.description}</Text>
          )}

          {/* Title */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Title</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] text-sm mb-4"
            placeholder="e.g. Lower carbs after 6pm for 7 days"
            placeholderTextColor="#3D4F66"
            value={title}
            onChangeText={setTitle}
          />

          {/* Notes */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">
            Notes <Text className="normal-case font-normal">(optional)</Text>
          </Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] text-sm mb-4"
            placeholder="What specific change are you testing?"
            placeholderTextColor="#3D4F66"
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={2}
            style={{ minHeight: 60, textAlignVertical: 'top' }}
          />

          {/* Duration */}
          <View className="flex-row items-center justify-between mb-6">
            <Text className="text-[#526380] text-xs uppercase tracking-wider">Duration</Text>
            <View className="flex-row items-center gap-3">
              {[3, 5, 7, 14, 21].map((d) => (
                <TouchableOpacity
                  key={d}
                  onPress={() => setDuration(d)}
                  className="w-9 h-9 rounded-xl items-center justify-center"
                  style={{ backgroundColor: duration === d ? 'rgba(0,212,170,0.15)' : 'rgba(255,255,255,0.04)' }}
                >
                  <Text style={{ color: duration === d ? '#00D4AA' : '#526380', fontSize: 13 }}>{d}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <TouchableOpacity
            onPress={() => start()}
            disabled={isPending}
            className="bg-primary-500 rounded-2xl py-4 items-center"
            activeOpacity={0.8}
          >
            {isPending ? <ActivityIndicator color="#080B10" /> : (
              <Text className="text-obsidian-900 font-sansMedium">Start {duration}-Day Trial</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

// ─── Intervention card ─────────────────────────────────────────────────────────

function InterventionCard({
  iv, onCheckin, onComplete, onAbandon, isLoading,
}: {
  iv: ActiveIntervention;
  onCheckin?: (id: string, adhered: boolean) => void;
  onComplete?: (id: string) => void;
  onAbandon?: (id: string) => void;
  isLoading?: boolean;
}) {
  const progress = progressPercent(iv);
  const isActive = iv.status === 'active';
  const statusColor = iv.status === 'completed' ? '#6EE7B7' : iv.status === 'abandoned' ? '#526380' : '#00D4AA';
  const adherencePct = iv.duration_days > 0
    ? Math.round((iv.adherence_days / iv.duration_days) * 100)
    : 0;

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3"
      style={{ opacity: isLoading ? 0.6 : 1 }}>
      <View className="flex-row items-start justify-between mb-2">
        <View className="flex-1 mr-3">
          <Text className="text-[#E8EDF5] font-sansMedium leading-5">{iv.title}</Text>
          {iv.description && (
            <Text className="text-[#526380] text-sm mt-0.5" numberOfLines={2}>{iv.description}</Text>
          )}
        </View>
        <View className="rounded-full px-2.5 py-1" style={{ backgroundColor: `${statusColor}18` }}>
          <Text style={{ color: statusColor, fontSize: 11, fontWeight: '500' }}>
            {iv.status.toUpperCase()}
          </Text>
        </View>
      </View>

      {/* Progress bar (active only) */}
      {isActive && (
        <View className="mb-3">
          <View className="flex-row items-center justify-between mb-1.5">
            <Text className="text-[#526380] text-xs">Day progress</Text>
            <Text className="text-[#526380] text-xs">{progress}%</Text>
          </View>
          <View className="h-1.5 bg-surface-border rounded-full overflow-hidden">
            <View className="h-full rounded-full bg-primary-500" style={{ width: `${progress}%` }} />
          </View>
        </View>
      )}

      {/* Meta */}
      <View className="flex-row gap-3 mb-3">
        <Text className="text-[#526380] text-xs">
          <Text className="text-[#8B97A8]">{iv.duration_days}d trial</Text>
        </Text>
        <Text className="text-[#526380] text-xs">
          {format(parseISO(iv.started_at), 'MMM d')} → {format(parseISO(iv.ends_at), 'MMM d')}
        </Text>
        {isActive && (
          <Text className="text-[#526380] text-xs ml-auto">
            {adherencePct}% adherence
          </Text>
        )}
      </View>

      {/* Actions */}
      {isActive && onCheckin && onComplete && onAbandon && (
        <View className="flex-row gap-2 pt-3 border-t border-surface-border">
          <TouchableOpacity
            onPress={() => onCheckin(iv.id, true)}
            className="flex-1 py-2 rounded-xl items-center"
            style={{ backgroundColor: 'rgba(0,212,170,0.12)' }}
          >
            <Text className="text-primary-500 text-xs font-sansMedium">✓ Adhered</Text>
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => onCheckin(iv.id, false)}
            className="flex-1 py-2 rounded-xl items-center"
            style={{ backgroundColor: 'rgba(255,255,255,0.04)' }}
          >
            <Text className="text-[#526380] text-xs">✗ Skipped</Text>
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => Alert.alert('Complete Trial', 'Finish this experiment and see results?', [
              { text: 'Cancel', style: 'cancel' },
              { text: 'Complete', onPress: () => onComplete(iv.id) },
            ])}
            className="px-3 py-2 rounded-xl items-center"
            style={{ backgroundColor: 'rgba(110,231,183,0.1)' }}
          >
            <Ionicons name="checkmark-done-outline" size={16} color="#6EE7B7" />
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => Alert.alert('Abandon Trial', 'Stop this experiment without recording an outcome?', [
              { text: 'Cancel', style: 'cancel' },
              { text: 'Abandon', style: 'destructive', onPress: () => onAbandon(iv.id) },
            ])}
            className="px-3 py-2 rounded-xl items-center"
            style={{ backgroundColor: 'rgba(248,113,113,0.08)' }}
          >
            <Ionicons name="trash-outline" size={16} color="#F87171" />
          </TouchableOpacity>
        </View>
      )}

      {/* Outcome delta */}
      {iv.outcome_delta && Object.keys(iv.outcome_delta).length > 0 && (
        <View className="mt-3 pt-3 border-t border-surface-border">
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Outcome</Text>
          <View className="flex-row flex-wrap gap-2">
            {Object.entries(iv.outcome_delta).map(([metric, delta]) => {
              const pct = Math.round(delta);
              const positive = pct > 0;
              const color = positive ? '#6EE7B7' : '#F87171';
              return (
                <View key={metric} className="rounded-lg px-2.5 py-1.5"
                  style={{ backgroundColor: `${color}12` }}>
                  <Text style={{ color, fontSize: 11, fontWeight: '500' }}>
                    {positive ? '+' : ''}{pct}% {metric.replace(/_/g, ' ')}
                  </Text>
                </View>
              );
            })}
          </View>
        </View>
      )}
    </View>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

export default function InterventionsScreen() {
  const [tab, setTab] = useState<Tab>('active');
  const [showModal, setShowModal] = useState(false);
  const queryClient = useQueryClient();

  const { data: interventions = [], isLoading } = useQuery({
    queryKey: ['interventions'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/interventions/');
      return (Array.isArray(data) ? data : (data?.interventions ?? [])) as ActiveIntervention[];
    },
  });

  const { mutate: checkin, variables: checkinVars, isPending: isCheckinPending } = useMutation({
    mutationFn: async ({ id, adhered }: { id: string; adhered: boolean }) => {
      await api.post(`/api/v1/interventions/${id}/checkin`, { adhered });
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['interventions'] }),
  });

  const { mutate: complete, variables: completeVars, isPending: isCompletePending } = useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.post(`/api/v1/interventions/${id}/complete`);
      return data as InterventionOutcome;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['interventions'] }),
  });

  const { mutate: abandon, variables: abandonVars, isPending: isAbandonPending } = useMutation({
    mutationFn: async (id: string) => {
      await api.patch(`/api/v1/interventions/${id}/abandon`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['interventions'] }),
  });

  const filtered = interventions.filter((iv) => {
    if (tab === 'active')    return iv.status === 'active';
    if (tab === 'completed') return iv.status === 'completed';
    return true;
  });

  const activeCount    = interventions.filter((iv) => iv.status === 'active').length;
  const completedCount = interventions.filter((iv) => iv.status === 'completed').length;

  const busyId = checkinVars?.id ?? completeVars ?? abandonVars;

  return (
    <View className="flex-1 bg-obsidian-900">
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <View className="flex-row items-center gap-2 flex-1">
          <Ionicons name="flask-outline" size={20} color="#00D4AA" />
          <Text className="text-xl font-display text-[#E8EDF5]">Experiments</Text>
        </View>
        <TouchableOpacity
          onPress={() => setShowModal(true)}
          className="flex-row items-center gap-1.5 bg-primary-500 rounded-xl px-3 py-2"
          activeOpacity={0.8}
        >
          <Ionicons name="add" size={18} color="#080B10" />
          <Text className="text-obsidian-900 text-sm font-sansMedium">New</Text>
        </TouchableOpacity>
      </View>

      {/* Tab bar */}
      <View className="flex-row px-6 pt-3 pb-1 gap-2">
        {([
          { key: 'active',    label: `Active (${activeCount})` },
          { key: 'completed', label: `Done (${completedCount})` },
          { key: 'all',       label: 'All' },
        ] as const).map(({ key, label }) => (
          <TouchableOpacity
            key={key}
            onPress={() => setTab(key)}
            className="rounded-xl px-3 py-1.5"
            style={{
              backgroundColor: tab === key ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.04)',
            }}
          >
            <Text style={{ color: tab === key ? '#00D4AA' : '#526380', fontSize: 13, fontWeight: tab === key ? '600' : '400' }}>
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView className="flex-1 px-6" contentContainerStyle={{ paddingTop: 12, paddingBottom: 40 }}>
        {isLoading ? (
          <View className="items-center py-16">
            <ActivityIndicator color="#00D4AA" />
          </View>
        ) : filtered.length === 0 ? (
          <View className="items-center py-16">
            <Ionicons name="flask-outline" size={48} color="#526380" />
            <Text className="text-[#E8EDF5] font-sansMedium mt-4">
              {tab === 'active' ? 'No Active Experiments' : 'Nothing here yet'}
            </Text>
            <Text className="text-[#526380] text-sm text-center mt-2">
              {tab === 'active'
                ? 'Try something for a week and see if it moves your numbers.'
                : 'Complete an experiment to see its outcome here.'}
            </Text>
            {tab === 'active' && (
              <TouchableOpacity
                onPress={() => setShowModal(true)}
                className="mt-4 px-4 py-2.5 rounded-xl"
                style={{ backgroundColor: 'rgba(0,212,170,0.12)' }}
              >
                <Text className="text-primary-500 text-sm font-sansMedium">Start your first experiment</Text>
              </TouchableOpacity>
            )}
          </View>
        ) : (
          filtered.map((iv) => (
            <InterventionCard
              key={iv.id}
              iv={iv}
              isLoading={(busyId === iv.id && (isCheckinPending || isCompletePending || isAbandonPending))}
              onCheckin={iv.status === 'active' ? (id, adhered) => checkin({ id, adhered }) : undefined}
              onComplete={iv.status === 'active' ? complete : undefined}
              onAbandon={iv.status === 'active' ? abandon : undefined}
            />
          ))
        )}

        <Text className="text-[#3D4F66] text-xs text-center mt-4 leading-4 px-4">
          Experiments are for personal learning only. Always consult your healthcare provider before
          making significant dietary or lifestyle changes.
        </Text>
      </ScrollView>

      {showModal && (
        <StartModal
          onClose={() => setShowModal(false)}
          onStarted={(iv) => {
            setShowModal(false);
            queryClient.setQueryData<ActiveIntervention[]>(['interventions'], (prev = []) => [iv, ...prev]);
            setTab('active');
          }}
        />
      )}
    </View>
  );
}
