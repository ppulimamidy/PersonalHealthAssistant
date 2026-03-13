import { View, Text, FlatList, TouchableOpacity, RefreshControl, ActivityIndicator } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/services/api';
import type { SymptomJournalEntry } from '@/types';
import { format } from 'date-fns';

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
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['symptoms'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/symptoms/journal', {
        params: { days: 30 },
      });
      const symptoms = Array.isArray(resp) ? resp : (resp?.symptoms ?? []);
      return symptoms as SymptomJournalEntry[];
    },
  });

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
