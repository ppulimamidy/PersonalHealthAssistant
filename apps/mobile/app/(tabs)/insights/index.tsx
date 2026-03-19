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

// The core insight trio: what happened → why → what's next
const ANALYSIS_CARDS = [
  {
    label: 'Timeline',
    description: 'See what happened day-by-day across all your data',
    icon: 'time-outline' as const,
    iconColor: '#00D4AA',
    route: '/(tabs)/insights/timeline',
  },
  {
    label: 'Triggers & Causes',
    description: 'See what patterns and root causes drive your symptoms',
    icon: 'git-branch-outline' as const,
    iconColor: '#A78BFA',
    route: '/(tabs)/insights/correlations',
  },
  {
    label: 'Health Forecast',
    description: 'Predict how your health may trend over the next weeks',
    icon: 'telescope-outline' as const,
    iconColor: '#60A5FA',
    route: '/(tabs)/insights/predictions',
  },
] as const;

function AnalysisCard({ item }: { readonly item: { label: string; description: string; icon: string; iconColor: string; route: string } }) {
  return (
    <TouchableOpacity
      onPress={() => router.push(item.route as never)}
      className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-3"
      activeOpacity={0.7}
    >
      <View className="flex-row items-center gap-3">
        <View className="rounded-xl p-2.5" style={{ backgroundColor: `${item.iconColor}18` }}>
          <Ionicons name={item.icon} size={20} color={item.iconColor} />
        </View>
        <View className="flex-1">
          <Text className="text-[#E8EDF5] font-sansMedium text-sm">{item.label}</Text>
          <Text className="text-[#526380] text-xs mt-0.5 leading-4">{item.description}</Text>
        </View>
        <Ionicons name="chevron-forward" size={16} color="#3D4F66" />
      </View>
    </TouchableOpacity>
  );
}

function InsightsListHeader() {
  return (
    <View>
      {/* Page header */}
      <View className="px-6 pt-14 pb-4">
        <Text className="text-2xl font-display text-[#E8EDF5]">Insights</Text>
        <Text className="text-[#526380] text-sm mt-1">What happened, why, and what's next</Text>
      </View>

      {/* Analysis cards */}
      <View className="px-6 pb-4">
        {ANALYSIS_CARDS.map((item) => (
          <AnalysisCard key={item.label} item={item} />
        ))}
      </View>

      {/* Divider */}
      <View className="mx-6 mb-4 border-t border-surface-border" />
      <Text className="px-6 pb-3 text-xs text-[#526380] uppercase tracking-wider">Recent Insights</Text>
    </View>
  );
}

export default function InsightsScreen() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['insights'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/insights/');
      return (Array.isArray(resp) ? resp : (resp?.insights ?? [])) as AIInsight[];
    },
  });

  return (
    <View className="flex-1 bg-obsidian-900">
      {isLoading ? (
        <>
          <InsightsListHeader />
          <ActivityIndicator color="#00D4AA" className="mt-10" />
        </>
      ) : (
        <FlatList
          data={data ?? []}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <View className="px-6">
              <InsightCard item={item} />
            </View>
          )}
          ListHeaderComponent={<InsightsListHeader />}
          contentContainerStyle={{ paddingBottom: 24 }}
          refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor="#00D4AA" />}
          ListEmptyComponent={
            <View className="items-center py-8 px-6">
              <Ionicons name="bulb-outline" size={40} color="#526380" />
              <Text className="text-[#526380] mt-3 text-center text-sm">No insights yet{'\n'}Log more data to generate patterns</Text>
            </View>
          }
        />
      )}
    </View>
  );
}
