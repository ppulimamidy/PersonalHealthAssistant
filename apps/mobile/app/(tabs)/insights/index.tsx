import { useState } from 'react';
import { View, Text, FlatList, RefreshControl, ActivityIndicator, TouchableOpacity } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { api } from '@/services/api';
import type { AIInsight } from '@/types';
import { format } from 'date-fns';

function InsightCard({ item }: { item: AIInsight }) {
  const typeColor = item.type === 'alert' ? '#F87171' : item.type === 'recommendation' ? '#F5A623' : '#6EE7B7';
  return (
    <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-3">
      <View className="flex-row items-start gap-3">
        <View className="rounded-lg p-2 mt-0.5" style={{ backgroundColor: `${typeColor}20` }}>
          <Ionicons name="bulb-outline" size={16} color={typeColor} />
        </View>
        <View className="flex-1">
          <Text className="text-[#E8EDF5] font-sansMedium leading-5">{item.title}</Text>
          <Text className="text-[#526380] text-sm mt-1 leading-5" numberOfLines={3}>{item.summary}</Text>
          {item.created_at && (
            <Text className="text-[#526380] text-xs mt-2">{format(new Date(item.created_at), 'MMM d')}</Text>
          )}
        </View>
      </View>
    </View>
  );
}

export default function InsightsScreen() {
  const [advancedExpanded, setAdvancedExpanded] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['insights'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/insights/');
      return (Array.isArray(resp) ? resp : (resp?.insights ?? [])) as AIInsight[];
    },
  });

  return (
    <View className="flex-1 bg-obsidian-900">
      <View className="px-6 pt-14 pb-4">
        <View className="flex-row items-center justify-between">
          <Text className="text-2xl font-display text-[#E8EDF5]">Insights</Text>
          <TouchableOpacity
            onPress={() => router.push('/(tabs)/insights/doctor-prep')}
            className="flex-row items-center gap-1.5 bg-surface-raised border border-surface-border rounded-xl px-3 py-2"
            activeOpacity={0.7}
          >
            <Ionicons name="document-text-outline" size={16} color="#00D4AA" />
            <Text className="text-primary-500 text-xs font-sansMedium">Doctor Prep</Text>
          </TouchableOpacity>
        </View>
        <Text className="text-[#526380] text-sm mt-1">Understand what's affecting your health</Text>
      </View>

      {/* Quick nav — Tier 1 */}
      <View className="px-6 pb-1 gap-2">
        <View className="flex-row gap-2">
          {[
            { label: 'Trends',        icon: 'analytics-outline' as const,  route: '/(tabs)/insights/trends' },
            { label: 'Timeline',      icon: 'calendar-outline' as const,    route: '/(tabs)/insights/timeline' },
            { label: 'Symptom\nTriggers', icon: 'git-branch-outline' as const, route: '/(tabs)/insights/correlations' },
            { label: 'Health\nForecast',  icon: 'telescope-outline' as const,  route: '/(tabs)/insights/predictions' },
          ].map((item) => (
            <TouchableOpacity
              key={item.label}
              onPress={() => router.push(item.route as never)}
              className="flex-1 bg-surface-raised border border-surface-border rounded-xl py-2.5 items-center gap-1"
              activeOpacity={0.7}
            >
              <Ionicons name={item.icon} size={16} color="#526380" />
              <Text className="text-[#526380] text-xs text-center">{item.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Tier 2 — Advanced Analysis (collapsible) */}
        <TouchableOpacity
          onPress={() => setAdvancedExpanded((v) => !v)}
          className="flex-row items-center justify-between py-2 mt-1"
          activeOpacity={0.7}
        >
          <Text className="text-[#526380] text-xs uppercase tracking-wider">Advanced Analysis</Text>
          <Ionicons
            name={advancedExpanded ? 'chevron-up' : 'chevron-down'}
            size={13}
            color="#526380"
          />
        </TouchableOpacity>

        {advancedExpanded && (
          <View className="flex-row gap-2 flex-wrap">
            {[
              { label: 'Root\nCauses',       icon: 'arrow-forward-circle-outline' as const, route: '/(tabs)/insights/causal-graph' },
              { label: 'Research\nEvidence', icon: 'people-outline' as const,               route: '/(tabs)/insights/meta-analysis' },
              { label: 'Evidence\nLibrary',  icon: 'library-outline' as const,              route: '/(tabs)/insights/research' },
              { label: 'Simulate\nChanges',  icon: 'construct-outline' as const,            route: '/(tabs)/profile/health-twin' },
            ].map((item) => (
              <TouchableOpacity
                key={item.label}
                onPress={() => router.push(item.route as never)}
                className="flex-1 bg-surface-raised border border-surface-border rounded-xl py-2.5 items-center gap-1"
                activeOpacity={0.7}
              >
                <Ionicons name={item.icon} size={16} color="#526380" />
                <Text className="text-[#526380] text-xs text-center">{item.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </View>

      {isLoading ? (
        <ActivityIndicator color="#00D4AA" className="mt-10" />
      ) : (
        <FlatList
          data={data ?? []}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <InsightCard item={item} />}
          contentContainerStyle={{ padding: 16, paddingTop: 4 }}
          refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor="#00D4AA" />}
          ListEmptyComponent={
            <View className="items-center py-12">
              <Ionicons name="bulb-outline" size={48} color="#526380" />
              <Text className="text-[#526380] mt-4 text-center">No insights yet{'\n'}Log more data to generate patterns</Text>
            </View>
          }
        />
      )}
    </View>
  );
}
