import { View, Text, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { api } from '@/services/api';

interface Phase {
  name: string;
  description: string;
  phase_type: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  outcome_summary: string | null;
  checkpoints: Array<{ action?: string; recorded_at?: string }>;
}

interface JourneyDetail {
  id: string;
  title: string;
  status: string;
  phases: Phase[];
  current_phase: number;
  total_phases: number;
  progress_pct: number;
  days_active: number;
  started_at: string;
  baseline_snapshot: Record<string, number | null> | null;
  outcome_snapshot: Record<string, number | null> | null;
}

const PHASE_ICONS: Record<string, string> = {
  completed: 'checkmark-circle',
  active: 'flask',
  skipped: 'play-skip-forward',
  pending: 'ellipse-outline',
};
const PHASE_COLORS: Record<string, string> = {
  completed: '#00D4AA', active: '#60A5FA', skipped: '#3D4F66', pending: '#1E2A3B',
};

export default function JourneyDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const queryClient = useQueryClient();

  const { data: journey, isLoading } = useQuery<JourneyDetail>({
    queryKey: ['journey', id],
    queryFn: async () => { const { data } = await api.get(`/api/v1/journeys/${id}`); return data; },
    enabled: !!id,
  });

  const advanceMutation = useMutation({
    mutationFn: async (skip: boolean) => { await api.post(`/api/v1/journeys/${id}/advance`, { skip }); },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journey', id] });
      queryClient.invalidateQueries({ queryKey: ['active-journey'] });
    },
  });

  const pauseMutation = useMutation({
    mutationFn: async () => { await api.patch(`/api/v1/journeys/${id}/pause`); },
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['journey', id] }); queryClient.invalidateQueries({ queryKey: ['active-journey'] }); },
  });

  const resumeMutation = useMutation({
    mutationFn: async () => { await api.patch(`/api/v1/journeys/${id}/resume`); },
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['journey', id] }); queryClient.invalidateQueries({ queryKey: ['active-journey'] }); },
  });

  const abandonMutation = useMutation({
    mutationFn: async () => { await api.patch(`/api/v1/journeys/${id}/abandon`); },
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['journey', id] }); queryClient.invalidateQueries({ queryKey: ['active-journey'] }); },
  });

  if (isLoading) return <View className="flex-1 bg-obsidian-900 items-center justify-center"><ActivityIndicator color="#00D4AA" /></View>;
  if (!journey) return <View className="flex-1 bg-obsidian-900 items-center justify-center"><Text className="text-[#526380]">Journey not found</Text></View>;

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ padding: 16, paddingTop: 56, paddingBottom: 32 }}>
      <View className="flex-row items-center gap-2 mb-1">
        <Ionicons name="flag-outline" size={20} color="#60A5FA" />
        <Text className="text-xl font-display text-[#E8EDF5]">{journey.title}</Text>
      </View>
      <Text className="text-sm text-[#526380] mb-6">
        {journey.days_active}d active · {Math.round(journey.progress_pct)}% complete
      </Text>

      {/* Phase stepper */}
      {journey.phases.map((phase, i) => {
        const color = PHASE_COLORS[phase.status] || '#1E2A3B';
        const icon = PHASE_ICONS[phase.status] || 'ellipse-outline';
        const isCurrent = i === journey.current_phase && journey.status === 'active';

        return (
          <View
            key={i}
            className="rounded-xl p-4 mb-2"
            style={{
              backgroundColor: isCurrent ? 'rgba(96,165,250,0.04)' : 'rgba(255,255,255,0.03)',
              borderWidth: 1,
              borderColor: isCurrent ? 'rgba(96,165,250,0.15)' : 'rgba(255,255,255,0.06)',
            }}
          >
            <View className="flex-row items-start gap-3">
              <Ionicons name={icon as never} size={16} color={color} style={{ marginTop: 2 }} />
              <View className="flex-1">
                <View className="flex-row items-center gap-2">
                  <Text className="text-sm font-sansMedium text-[#E8EDF5]">{phase.name}</Text>
                  {isCurrent && (
                    <View className="rounded-full px-1.5 py-0.5" style={{ backgroundColor: 'rgba(96,165,250,0.15)' }}>
                      <Text className="text-[8px] font-bold uppercase" style={{ color: '#60A5FA' }}>Current</Text>
                    </View>
                  )}
                </View>
                {phase.description ? <Text className="text-xs text-[#8B97A8] mt-1 leading-5">{phase.description}</Text> : null}
                {phase.started_at && (
                  <Text className="text-[10px] text-[#3D4F66] mt-1">
                    Started {format(new Date(phase.started_at), 'MMM d')}
                    {phase.completed_at && ` · Done ${format(new Date(phase.completed_at), 'MMM d')}`}
                  </Text>
                )}
                {phase.outcome_summary ? <Text className="text-xs mt-1" style={{ color: '#6EE7B7', fontStyle: 'italic' }}>{phase.outcome_summary}</Text> : null}
              </View>
            </View>
          </View>
        );
      })}

      {/* Actions */}
      {journey.status === 'active' && (
        <View className="flex-row items-center gap-3 mt-4">
          <TouchableOpacity
            onPress={() => advanceMutation.mutate(false)}
            disabled={advanceMutation.isPending}
            className="px-4 py-2.5 rounded-xl"
            style={{ backgroundColor: '#60A5FA', opacity: advanceMutation.isPending ? 0.6 : 1 }}
            activeOpacity={0.85}
          >
            <Text className="text-sm font-sansMedium" style={{ color: '#080B10' }}>
              {advanceMutation.isPending ? 'Advancing...' : 'Complete Phase'}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => advanceMutation.mutate(true)}>
            <Text className="text-xs text-[#526380]">Skip</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => pauseMutation.mutate()} className="ml-auto">
            <Ionicons name="pause" size={16} color="#526380" />
          </TouchableOpacity>
          <TouchableOpacity onPress={() => Alert.alert('Abandon', 'Abandon this journey?', [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Abandon', style: 'destructive', onPress: () => abandonMutation.mutate() },
          ])}>
            <Ionicons name="close-circle-outline" size={16} color="#526380" />
          </TouchableOpacity>
        </View>
      )}

      {journey.status === 'paused' && (
        <View className="flex-row items-center gap-3 mt-4">
          <TouchableOpacity
            onPress={() => resumeMutation.mutate()}
            className="flex-row items-center gap-1.5 px-4 py-2.5 rounded-xl"
            style={{ backgroundColor: '#00D4AA' }}
            activeOpacity={0.85}
          >
            <Ionicons name="play" size={14} color="#080B10" />
            <Text className="text-sm font-sansMedium" style={{ color: '#080B10' }}>Resume</Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}
