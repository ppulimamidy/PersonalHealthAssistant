import { useState } from 'react';
import {
  View, Text, TouchableOpacity, ActivityIndicator,
  ScrollView, TextInput,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { api } from '@/services/api';

const AGENT_COLORS: Record<string, string> = {
  health_coach: '#00D4AA',
  nutrition_analyst: '#6EE7B7',
  symptom_investigator: '#F5A623',
  research_assistant: '#818CF8',
  medication_advisor: '#EC4899',
  general: '#00D4AA',
};

const AGENT_ICONS: Record<string, React.ComponentProps<typeof Ionicons>['name']> = {
  health_coach: 'fitness-outline',
  nutrition_analyst: 'nutrition-outline',
  symptom_investigator: 'search-outline',
  research_assistant: 'book-outline',
  medication_advisor: 'medical-outline',
  general: 'chatbubble-ellipses-outline',
};

const QUICK_SUGGESTIONS = [
  'Why do I feel tired?',
  'Review my medications',
  'Explain my latest labs',
  "What's affecting my sleep?",
  'Am I improving this week?',
];

interface Agent {
  id: string;
  agent_name: string;
  agent_description: string;
  agent_type: string;
}

interface Conversation {
  id: string;
  primary_agent_type: string;
  primary_agent_name: string;
  last_message_at: string;
  messages: Array<{ role: string; content: string }>;
}

function askQuestion(question: string) {
  router.push({
    pathname: '/(tabs)/chat/[conversationId]',
    params: { conversationId: 'new', agentType: 'health_coach', initialMessage: question },
  } as never);
}

function startNewConversation(agentType: string) {
  router.push({
    pathname: '/(tabs)/chat/[conversationId]',
    params: { conversationId: 'new', agentType },
  } as never);
}

function resumeConversation(conv: Conversation) {
  router.push({
    pathname: '/(tabs)/chat/[conversationId]',
    params: { conversationId: conv.id, agentType: conv.primary_agent_type },
  } as never);
}

export default function AgentsListScreen() {
  const [question, setQuestion] = useState('');
  const [specialistsExpanded, setSpecialistsExpanded] = useState(false);

  const { data: agents, isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/agents/agents');
      return (resp?.agents ?? resp ?? []) as Agent[];
    },
  });

  const { data: conversations, isLoading: convsLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/agents/conversations');
      return (resp?.conversations ?? resp ?? []) as Conversation[];
    },
    staleTime: 30_000,
  });

  function handleAsk() {
    const q = question.trim();
    if (!q) return;
    setQuestion('');
    askQuestion(q);
  }

  if (agentsLoading || convsLoading) {
    return (
      <View className="flex-1 bg-obsidian-900 items-center justify-center">
        <ActivityIndicator color="#00D4AA" />
      </View>
    );
  }

  const recentConvs = (conversations ?? []).slice(0, 8);

  return (
    <ScrollView
      className="flex-1 bg-obsidian-900"
      contentContainerStyle={{ paddingBottom: 40 }}
      keyboardShouldPersistTaps="handled"
    >
      {/* Header */}
      <View className="px-6 pt-14 pb-4">
        <Text className="text-2xl font-display text-[#E8EDF5]">Agents</Text>
        <Text className="text-[#526380] text-sm mt-1">Your AI health advisors</Text>
      </View>

      {/* Ask-anything bar */}
      <View className="px-6 mb-4">
        <View className="flex-row items-center bg-surface-raised border border-primary-500/40 rounded-2xl px-4 py-3 gap-3">
          <Ionicons name="sparkles-outline" size={18} color="#00D4AA" />
          <TextInput
            className="flex-1 text-[#E8EDF5] text-base"
            placeholder="Ask anything about your health…"
            placeholderTextColor="#526380"
            value={question}
            onChangeText={setQuestion}
            onSubmitEditing={handleAsk}
            returnKeyType="send"
            multiline={false}
          />
          {question.trim().length > 0 && (
            <TouchableOpacity onPress={handleAsk} activeOpacity={0.7}>
              <View className="w-8 h-8 rounded-full bg-primary-500 items-center justify-center">
                <Ionicons name="arrow-up" size={16} color="#080B10" />
              </View>
            </TouchableOpacity>
          )}
        </View>

        {/* Quick suggestion chips */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          className="mt-3 -mx-1"
          contentContainerStyle={{ paddingHorizontal: 4, gap: 8 }}
        >
          {QUICK_SUGGESTIONS.map((s) => (
            <TouchableOpacity
              key={s}
              onPress={() => askQuestion(s)}
              className="bg-surface-raised border border-surface-border rounded-full px-3 py-1.5"
              activeOpacity={0.7}
            >
              <Text className="text-[#526380] text-xs">{s}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Choose a specialist (collapsible) */}
      <View className="px-6 mb-4">
        <TouchableOpacity
          onPress={() => setSpecialistsExpanded((v) => !v)}
          className="flex-row items-center justify-between py-2"
          activeOpacity={0.7}
        >
          <Text className="text-[#526380] text-xs uppercase tracking-wider">Choose a specialist</Text>
          <Ionicons
            name={specialistsExpanded ? 'chevron-up' : 'chevron-down'}
            size={14}
            color="#526380"
          />
        </TouchableOpacity>

        {specialistsExpanded && (agents ?? []).map((agent) => {
          const color = AGENT_COLORS[agent.agent_type] ?? '#00D4AA';
          const icon = AGENT_ICONS[agent.agent_type] ?? 'chatbubble-ellipses-outline';
          return (
            <TouchableOpacity
              key={agent.id}
              onPress={() => startNewConversation(agent.agent_type)}
              className="flex-row items-center bg-surface-raised border border-surface-border rounded-xl p-4 mb-2"
              activeOpacity={0.7}
            >
              <View className="w-10 h-10 rounded-xl items-center justify-center mr-3" style={{ backgroundColor: `${color}20` }}>
                <Ionicons name={icon} size={18} color={color} />
              </View>
              <View className="flex-1">
                <Text className="text-[#E8EDF5] font-sansMedium text-sm">{agent.agent_name}</Text>
                <Text className="text-[#526380] text-xs mt-0.5" numberOfLines={1}>{agent.agent_description}</Text>
              </View>
              <Ionicons name="chevron-forward" size={14} color="#526380" />
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Recent conversations */}
      {recentConvs.length > 0 && (
        <View className="px-6">
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3">Recent Chats</Text>
          {recentConvs.map((conv) => {
            const color = AGENT_COLORS[conv.primary_agent_type] ?? '#00D4AA';
            const icon = AGENT_ICONS[conv.primary_agent_type] ?? 'chatbubble-ellipses-outline';
            const firstUserMsg = conv.messages?.find((m) => m.role === 'user');
            const snippet = firstUserMsg?.content ?? 'No messages yet';
            const dateLabel = conv.last_message_at ? format(new Date(conv.last_message_at), 'MMM d') : '';

            return (
              <TouchableOpacity
                key={conv.id}
                onPress={() => resumeConversation(conv)}
                className="flex-row items-center bg-surface-raised border border-surface-border rounded-xl p-3.5 mb-2"
                activeOpacity={0.7}
              >
                <View className="w-9 h-9 rounded-xl items-center justify-center mr-3" style={{ backgroundColor: `${color}18` }}>
                  <Ionicons name={icon} size={16} color={color} />
                </View>
                <View className="flex-1 mr-2">
                  <Text className="text-[#E8EDF5] font-sansMedium text-sm">{conv.primary_agent_name}</Text>
                  <Text className="text-[#526380] text-xs mt-0.5" numberOfLines={1}>
                    {snippet.length > 55 ? `${snippet.slice(0, 55)}…` : snippet}
                  </Text>
                </View>
                <Text className="text-[#3A4A5C] text-xs">{dateLabel}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      )}
    </ScrollView>
  );
}
