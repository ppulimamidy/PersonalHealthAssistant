import { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format, subDays } from 'date-fns';
import { api } from '@/services/api';

interface CycleInfo {
  current_phase: { phase: string; cycle_day: number | null; days_until_next_period: number | null; confidence: string };
  avg_cycle_length: number | null;
  last_period_start: string | null;
  cycles_tracked: number;
  is_regular: boolean | null;
}

const PHASE_COLORS: Record<string, string> = {
  menstrual: '#F87171',
  follicular: '#6EE7B7',
  ovulation: '#F5A623',
  luteal: '#A78BFA',
  unknown: '#526380',
};

const PHASE_LABELS: Record<string, string> = {
  menstrual: 'Menstrual',
  follicular: 'Follicular',
  ovulation: 'Ovulation',
  luteal: 'Luteal',
  unknown: 'Unknown',
};

const FLOW_OPTIONS = ['light', 'medium', 'heavy', 'spotting'] as const;

const SYMPTOM_OPTIONS = [
  'cramps', 'bloating', 'headache', 'fatigue', 'mood_changes',
  'breast_tenderness', 'acne', 'back_pain', 'nausea', 'hot_flashes',
];

export default function CycleScreen() {
  const queryClient = useQueryClient();
  const [selectedDate, setSelectedDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [flow, setFlow] = useState<string | null>(null);
  const [symptoms, setSymptoms] = useState<string[]>([]);

  const { data: cycleInfo, isLoading } = useQuery<CycleInfo>({
    queryKey: ['cycle', 'current'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/cycle/current');
      return data;
    },
  });

  const logPeriodStart = useMutation({
    mutationFn: async () => {
      await api.post('/api/v1/cycle/log', {
        event_type: 'period_start',
        event_date: selectedDate,
        flow_intensity: flow || 'medium',
        symptoms,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cycle'] });
      Alert.alert('Logged', 'Period start recorded.');
      setFlow(null);
      setSymptoms([]);
    },
  });

  const logPeriodEnd = useMutation({
    mutationFn: async () => {
      await api.post('/api/v1/cycle/log', {
        event_type: 'period_end',
        event_date: selectedDate,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cycle'] });
      Alert.alert('Logged', 'Period end recorded.');
    },
  });

  const logOvulation = useMutation({
    mutationFn: async () => {
      await api.post('/api/v1/cycle/log', {
        event_type: 'ovulation',
        event_date: selectedDate,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cycle'] });
      Alert.alert('Logged', 'Ovulation recorded.');
    },
  });

  const logSymptoms = useMutation({
    mutationFn: async () => {
      await api.post('/api/v1/cycle/log', {
        event_type: 'symptom',
        event_date: selectedDate,
        symptoms,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cycle'] });
      Alert.alert('Logged', 'Symptoms recorded.');
      setSymptoms([]);
    },
  });

  const phase = cycleInfo?.current_phase;
  const phaseColor = PHASE_COLORS[phase?.phase ?? 'unknown'];

  // Date picker: last 7 days
  const dates = Array.from({ length: 7 }, (_, i) => {
    const d = subDays(new Date(), i);
    return format(d, 'yyyy-MM-dd');
  });

  return (
    <ScrollView
      className="flex-1 bg-obsidian-900"
      contentContainerStyle={{ padding: 16, paddingTop: 56, paddingBottom: 32 }}
    >
      <Text className="text-2xl font-display text-[#E8EDF5] mb-1">Cycle Tracking</Text>
      <Text className="text-sm text-[#526380] mb-6">Log your cycle for smarter experiments</Text>

      {/* Current phase */}
      {phase && phase.phase !== 'unknown' && (
        <View
          className="rounded-2xl p-4 mb-4"
          style={{ backgroundColor: `${phaseColor}10`, borderWidth: 1, borderColor: `${phaseColor}30` }}
        >
          <View className="flex-row items-center justify-between mb-1">
            <Text className="text-xs font-bold uppercase tracking-wider" style={{ color: phaseColor }}>
              {PHASE_LABELS[phase.phase]} Phase
            </Text>
            <Text className="text-xs" style={{ color: phaseColor }}>
              {phase.confidence} confidence
            </Text>
          </View>
          {phase.cycle_day && (
            <Text className="text-[#E8EDF5] text-lg font-display">Day {phase.cycle_day}</Text>
          )}
          <View className="flex-row gap-4 mt-2">
            {cycleInfo?.avg_cycle_length && (
              <Text className="text-xs text-[#526380]">Avg cycle: {cycleInfo.avg_cycle_length}d</Text>
            )}
            {phase.days_until_next_period != null && (
              <Text className="text-xs text-[#526380]">~{phase.days_until_next_period}d until next period</Text>
            )}
            {cycleInfo?.cycles_tracked != null && (
              <Text className="text-xs text-[#526380]">{cycleInfo.cycles_tracked} cycles tracked</Text>
            )}
          </View>
        </View>
      )}

      {/* Date selector */}
      <Text className="text-xs font-bold uppercase tracking-wider text-[#526380] mb-2">Date</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} className="mb-4">
        <View className="flex-row gap-2">
          {dates.map((d) => {
            const isSelected = d === selectedDate;
            const dayName = format(new Date(d + 'T12:00:00'), 'EEE');
            const dayNum = format(new Date(d + 'T12:00:00'), 'd');
            return (
              <TouchableOpacity
                key={d}
                onPress={() => setSelectedDate(d)}
                className="items-center px-3 py-2 rounded-xl"
                style={{
                  backgroundColor: isSelected ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.03)',
                  borderWidth: 1,
                  borderColor: isSelected ? 'rgba(0,212,170,0.3)' : 'rgba(255,255,255,0.06)',
                }}
              >
                <Text className="text-[10px]" style={{ color: isSelected ? '#00D4AA' : '#526380' }}>{dayName}</Text>
                <Text className="text-sm font-sansMedium" style={{ color: isSelected ? '#00D4AA' : '#E8EDF5' }}>{dayNum}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </ScrollView>

      {/* Quick log buttons */}
      <Text className="text-xs font-bold uppercase tracking-wider text-[#526380] mb-2">Log Event</Text>
      <View className="flex-row gap-2 mb-4">
        <TouchableOpacity
          onPress={() => logPeriodStart.mutate()}
          className="flex-1 items-center py-3 rounded-xl"
          style={{ backgroundColor: 'rgba(248,113,113,0.12)', borderWidth: 1, borderColor: 'rgba(248,113,113,0.3)' }}
          activeOpacity={0.7}
        >
          <Ionicons name="water-outline" size={18} color="#F87171" />
          <Text className="text-xs font-sansMedium mt-1" style={{ color: '#F87171' }}>Period Start</Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={() => logPeriodEnd.mutate()}
          className="flex-1 items-center py-3 rounded-xl"
          style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}
          activeOpacity={0.7}
        >
          <Ionicons name="stop-circle-outline" size={18} color="#8B97A8" />
          <Text className="text-xs font-sansMedium mt-1 text-[#8B97A8]">Period End</Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={() => logOvulation.mutate()}
          className="flex-1 items-center py-3 rounded-xl"
          style={{ backgroundColor: 'rgba(245,166,35,0.12)', borderWidth: 1, borderColor: 'rgba(245,166,35,0.3)' }}
          activeOpacity={0.7}
        >
          <Ionicons name="sunny-outline" size={18} color="#F5A623" />
          <Text className="text-xs font-sansMedium mt-1" style={{ color: '#F5A623' }}>Ovulation</Text>
        </TouchableOpacity>
      </View>

      {/* Flow intensity */}
      <Text className="text-xs font-bold uppercase tracking-wider text-[#526380] mb-2">Flow Intensity</Text>
      <View className="flex-row gap-2 mb-4">
        {FLOW_OPTIONS.map((f) => (
          <TouchableOpacity
            key={f}
            onPress={() => setFlow(flow === f ? null : f)}
            className="flex-1 items-center py-2 rounded-xl"
            style={{
              backgroundColor: flow === f ? 'rgba(248,113,113,0.12)' : 'rgba(255,255,255,0.03)',
              borderWidth: 1,
              borderColor: flow === f ? 'rgba(248,113,113,0.3)' : 'rgba(255,255,255,0.06)',
            }}
          >
            <Text className="text-xs" style={{ color: flow === f ? '#F87171' : '#8B97A8' }}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Symptoms */}
      <Text className="text-xs font-bold uppercase tracking-wider text-[#526380] mb-2">Symptoms</Text>
      <View className="flex-row flex-wrap gap-2 mb-4">
        {SYMPTOM_OPTIONS.map((s) => {
          const selected = symptoms.includes(s);
          return (
            <TouchableOpacity
              key={s}
              onPress={() => {
                setSymptoms(selected ? symptoms.filter((x) => x !== s) : [...symptoms, s]);
              }}
              className="px-3 py-1.5 rounded-full"
              style={{
                backgroundColor: selected ? 'rgba(167,139,250,0.12)' : 'rgba(255,255,255,0.03)',
                borderWidth: 1,
                borderColor: selected ? 'rgba(167,139,250,0.3)' : 'rgba(255,255,255,0.06)',
              }}
            >
              <Text className="text-xs" style={{ color: selected ? '#A78BFA' : '#8B97A8' }}>
                {s.replace(/_/g, ' ')}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Log symptoms button */}
      {symptoms.length > 0 && (
        <TouchableOpacity
          onPress={() => logSymptoms.mutate()}
          className="items-center py-3 rounded-xl mb-4"
          style={{ backgroundColor: '#A78BFA' }}
          activeOpacity={0.85}
        >
          <Text className="text-sm font-sansMedium" style={{ color: '#080B10' }}>
            Log {symptoms.length} Symptom{symptoms.length > 1 ? 's' : ''}
          </Text>
        </TouchableOpacity>
      )}
    </ScrollView>
  );
}
