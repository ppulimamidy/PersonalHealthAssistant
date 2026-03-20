import { useState, useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, RefreshControl, ActivityIndicator } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/services/api';
import type { SymptomJournalEntry } from '@/types';
import { format } from 'date-fns';
import SymptomInsightCard from '@/components/SymptomInsightCard';

function SymptomCard({ item }: { item: SymptomJournalEntry }) {
  const severityColor =
    item.severity >= 8 ? '#F87171' : item.severity >= 5 ? '#F5A623' : '#6EE7B7';

  return (
    <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-3">
      <View className="flex-row items-start justify-between">
        <View className="flex-1 mr-3">
          <Text className="text-[#E8EDF5] font-sansMedium capitalize">{item.symptom_type}</Text>
          {item.notes && (
            <Text className="text-[#526380] text-sm mt-1" numberOfLines={2}>{item.notes}</Text>
          )}
          <Text className="text-[#526380] text-xs mt-2">
            {format(new Date(item.created_at), 'MMM d, h:mm a')}
          </Text>
        </View>
        <View
          className="rounded-full w-10 h-10 items-center justify-center border"
          style={{ borderColor: severityColor, backgroundColor: `${severityColor}20` }}
        >
          <Text style={{ color: severityColor, fontWeight: '600' }}>{item.severity}</Text>
        </View>
      </View>
    </View>
  );
}

export default function SymptomsScreen() {
  const [insightData, setInsightData] = useState<any>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['symptoms'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/symptoms/journal', {
        params: { days: 30 },
      });
      const symptoms = Array.isArray(resp) ? resp : (resp?.symptoms ?? []);

      // Auto-fetch insight for the most recent symptom if logged today
      if (symptoms.length > 0 && !insightData) {
        const latest = symptoms[0] as SymptomJournalEntry;
        const today = new Date().toISOString().slice(0, 10);
        if ((latest.symptom_date ?? latest.created_at ?? '').slice(0, 10) === today) {
          try {
            const { data: insight } = await api.post('/api/v1/symptom-intelligence/post-log-insight', {
              symptom_type: latest.symptom_type,
              severity: latest.severity,
              notes: latest.notes,
            });
            setInsightData(insight);
          } catch { /* silent */ }
        }
      }

      return symptoms as SymptomJournalEntry[];
    },
  });

  const handleInsightAction = useCallback((action: string) => {
    if (action === 'Ask health coach') {
      router.push('/(tabs)/chat');
    }
    setInsightData(null);
  }, []);

  const listHeader = (
    <View>
      {insightData && (
        <SymptomInsightCard
          insight={insightData.insight ?? ''}
          frequencyThisWeek={insightData.frequency_this_week ?? 0}
          severityTrend={insightData.severity_trend ?? 'stable'}
          likelyTriggers={insightData.likely_triggers ?? []}
          quickActions={insightData.quick_actions ?? []}
          onAction={handleInsightAction}
          onDismiss={() => setInsightData(null)}
        />
      )}
    </View>
  );

  return (
    <View className="flex-1 bg-obsidian-900">
      <View className="px-6 pt-14 pb-4 flex-row items-center justify-between">
        <View>
          <Text className="text-2xl font-display text-[#E8EDF5]">Symptoms</Text>
          <Text className="text-[#526380] text-sm mt-0.5">Last 30 days</Text>
        </View>
        <TouchableOpacity
          onPress={() => router.push('/(tabs)/log/new-symptom')}
          className="bg-primary-500 rounded-full p-3"
        >
          <Ionicons name="add" size={20} color="#080B10" />
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <ActivityIndicator color="#00D4AA" className="mt-10" />
      ) : (
        <FlatList
          data={data ?? []}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <SymptomCard item={item} />}
          contentContainerStyle={{ padding: 16, paddingTop: 4 }}
          refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor="#00D4AA" />}
          ListHeaderComponent={listHeader}
          ListEmptyComponent={
            <View className="items-center py-12">
              <Ionicons name="thermometer-outline" size={48} color="#526380" />
              <Text className="text-[#526380] mt-4 text-center">No symptoms logged yet{'\n'}Tap + to add your first entry</Text>
            </View>
          }
        />
      )}
    </View>
  );
}
