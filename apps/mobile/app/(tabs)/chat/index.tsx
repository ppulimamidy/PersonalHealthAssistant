import { View, Text, FlatList, TouchableOpacity, ActivityIndicator } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/services/api';

const AGENT_COLORS: Record<string, string> = {
  general: '#00D4AA',
  nutrition: '#6EE7B7',
  sleep: '#818CF8',
  fitness: '#F59E0B',
  mental_health: '#EC4899',
};

export default function AgentsListScreen() {
  const { data: agents, isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/agents/agents');
      return resp?.agents ?? resp ?? [];
    },
  });

  const { data: conversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/agents/conversations');
      return resp?.conversations ?? resp ?? [];
    },
  });

  function startConversation(agentType: string) {
    const existing = conversations?.find((c: { primary_agent_type: string; id: string }) =>
      c.primary_agent_type === agentType
    );
    if (existing) {
      router.push(`/(tabs)/chat/${existing.id}` as never);
    } else {
      router.push({ pathname: '/(tabs)/chat/[conversationId]', params: { conversationId: 'new', agentType } } as never);
    }
  }

  return (
    <View className="flex-1 bg-obsidian-900">
      <View className="px-6 pt-14 pb-4">
        <Text className="text-2xl font-display text-[#E8EDF5]">AI Agents</Text>
        <Text className="text-[#526380] text-sm mt-1">Your health advisors</Text>
      </View>

      {isLoading ? (
        <ActivityIndicator color="#00D4AA" className="mt-10" />
      ) : (
        <FlatList<{ id: string; name: string; description: string; agent_type: string }>
          data={agents ?? []}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => {
            const color = AGENT_COLORS[item.agent_type] ?? '#00D4AA';
            return (
              <TouchableOpacity
                onPress={() => startConversation(item.agent_type)}
                className="flex-row items-center bg-surface-raised border border-surface-border rounded-xl p-4 mb-3 mx-4"
                activeOpacity={0.7}
              >
                <View className="w-12 h-12 rounded-2xl items-center justify-center mr-4" style={{ backgroundColor: `${color}20` }}>
                  <Ionicons name="chatbubble-ellipses-outline" size={22} color={color} />
                </View>
                <View className="flex-1">
                  <Text className="text-[#E8EDF5] font-sansMedium">{item.name}</Text>
                  <Text className="text-[#526380] text-sm mt-0.5" numberOfLines={2}>{item.description}</Text>
                </View>
                <Ionicons name="chevron-forward" size={16} color="#526380" />
              </TouchableOpacity>
            );
          }}
          contentContainerStyle={{ paddingTop: 4, paddingBottom: 24 }}
        />
      )}
    </View>
  );
}
