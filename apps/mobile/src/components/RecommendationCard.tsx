import { useState } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

interface FoodSuggestion {
  name: string;
  reason: string;
  category: string;
}

interface PersonalHistory {
  status: string;
  times_tried: number;
  avg_effect: number;
  confidence: number;
}

interface TopRecommendation {
  pattern: string;
  title: string;
  description: string;
  evidence: {
    signals: string[];
    severity: string;
    data_points: number;
  };
  suggested_duration: number;
  expected_improvement: string | null;
  foods: FoodSuggestion[];
  category: string;
  severity: string;
  personal_history: PersonalHistory | null;
  cycle_guidance: { phase: string; cycle_day: number | null; note: string | null } | null;
}

export default function RecommendationCard() {
  const queryClient = useQueryClient();
  const [dismissed, setDismissed] = useState(false);

  const { data: rec, isLoading } = useQuery<TopRecommendation | null>({
    queryKey: ['top-recommendation'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/recommendations/top');
      return data || null;
    },
    staleTime: 5 * 60_000,
  });

  const startMutation = useMutation({
    mutationFn: async (r: TopRecommendation) => {
      const { data } = await api.post('/api/v1/interventions/from-recommendation', {
        recommendation_pattern: r.pattern,
        title: r.title,
        description: r.description,
        duration_days: r.suggested_duration,
        evidence: r.evidence,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['top-recommendation'] });
      queryClient.invalidateQueries({ queryKey: ['active-intervention'] });
    },
  });

  const dismissMutation = useMutation({
    mutationFn: async (pattern: string) => {
      await api.post(`/api/v1/recommendations/${pattern}/dismiss`, { reason: 'not_now' });
    },
    onSuccess: () => setDismissed(true),
  });

  if (isLoading || !rec || dismissed) return null;

  const severityColor =
    rec.severity === 'high' ? '#F87171' : rec.severity === 'moderate' ? '#F5A623' : '#6EE7B7';

  const ph = rec.personal_history;
  const historyBadge = ph?.status === 'proven'
    ? { label: `Worked for you (${ph.times_tried}x)`, color: '#00D4AA', bg: 'rgba(0,212,170,0.12)' }
    : ph?.status === 'inconclusive' && ph.times_tried > 0
    ? { label: `Tried ${ph.times_tried}x — worth retesting`, color: '#F5A623', bg: 'rgba(245,166,35,0.12)' }
    : !ph || ph.times_tried === 0
    ? { label: 'New — untested', color: '#60A5FA', bg: 'rgba(96,165,250,0.12)' }
    : null;

  return (
    <View
      className="rounded-2xl p-4 mb-4"
      style={{
        backgroundColor: 'rgba(0,212,170,0.04)',
        borderWidth: 1,
        borderColor: 'rgba(0,212,170,0.15)',
      }}
    >
      {/* Header */}
      <View className="flex-row items-center justify-between mb-3">
        <View className="flex-row items-center gap-2">
          <View
            className="w-7 h-7 rounded-lg items-center justify-center"
            style={{ backgroundColor: 'rgba(0,212,170,0.12)' }}
          >
            <Ionicons name="bulb-outline" size={14} color="#00D4AA" />
          </View>
          <Text className="text-[10px] font-bold uppercase tracking-wider text-primary-500">
            Suggested for You
          </Text>
        </View>
        <TouchableOpacity
          onPress={() => dismissMutation.mutate(rec.pattern)}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Ionicons name="close" size={16} color="#3D4F66" />
        </TouchableOpacity>
      </View>

      {/* Personal history badge */}
      {historyBadge && (
        <View className="self-start rounded-full px-2 py-0.5 mb-2" style={{ backgroundColor: historyBadge.bg }}>
          <Text className="text-[10px] font-sansMedium" style={{ color: historyBadge.color }}>
            {historyBadge.label}
          </Text>
        </View>
      )}

      {/* Title + description */}
      <Text className="text-sm font-sansMedium text-[#E8EDF5] mb-1">{rec.title}</Text>
      <Text className="text-xs text-[#8B97A8] leading-5 mb-3">{rec.description}</Text>

      {/* Evidence */}
      <View
        className="rounded-xl p-3 mb-3"
        style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.05)' }}
      >
        <Text className="text-[9px] font-bold uppercase tracking-wider text-[#526380] mb-1.5">
          Why this recommendation
        </Text>
        {rec.evidence.signals.map((signal, i) => (
          <View key={i} className="flex-row items-center gap-2 mb-1">
            <View className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: severityColor }} />
            <Text className="text-xs text-[#8B97A8] flex-1">{signal}</Text>
          </View>
        ))}
        <Text className="text-[10px] text-[#3D4F66] mt-1.5">
          Based on {rec.evidence.data_points} days of data
        </Text>
      </View>

      {/* Expected improvement */}
      {rec.expected_improvement && (
        <View className="flex-row items-center gap-1.5 mb-3">
          <Ionicons name="flask-outline" size={13} color="#6EE7B7" />
          <Text className="text-xs text-[#6EE7B7] flex-1">{rec.expected_improvement}</Text>
        </View>
      )}

      {/* Food tags */}
      {rec.foods.length > 0 && (
        <View className="flex-row flex-wrap gap-1.5 mb-4">
          {rec.foods.slice(0, 4).map((f) => (
            <View
              key={f.name}
              className="rounded-full px-2 py-1"
              style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
            >
              <Text className="text-[10px] text-[#8B97A8]">{f.name}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Cycle guidance */}
      {rec.cycle_guidance?.note && (
        <View className="flex-row items-center gap-1.5 mb-3">
          <View className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: '#A78BFA' }} />
          <Text className="text-[10px] flex-1" style={{ color: '#A78BFA' }}>{rec.cycle_guidance.note}</Text>
        </View>
      )}

      {/* CTAs */}
      <View className="flex-row items-center gap-3">
        <TouchableOpacity
          onPress={() => startMutation.mutate(rec)}
          disabled={startMutation.isPending}
          className="flex-row items-center gap-1.5 px-4 py-2.5 rounded-xl"
          style={{ backgroundColor: '#00D4AA', opacity: startMutation.isPending ? 0.6 : 1 }}
          activeOpacity={0.85}
        >
          {startMutation.isPending ? (
            <ActivityIndicator size="small" color="#080B10" />
          ) : (
            <>
              <Text className="text-sm font-sansMedium" style={{ color: '#080B10' }}>
                Try This ({rec.suggested_duration} days)
              </Text>
              <Ionicons name="chevron-forward" size={14} color="#080B10" />
            </>
          )}
        </TouchableOpacity>
        <TouchableOpacity onPress={() => dismissMutation.mutate(rec.pattern)}>
          <Text className="text-xs text-[#526380]">Not now</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
