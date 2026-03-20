/**
 * Ask AI Hub — redesigned with 2 tools:
 * 1. Clinical Research (treatments, drugs, trials, guidelines)
 * 2. Health Chat (unified agent replacing 4 specialists)
 */

import { useState } from 'react';
import {
  View, Text, TouchableOpacity, ScrollView, TextInput, ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { api } from '@/services/api';

interface Conversation {
  id: string;
  primary_agent_type: string;
  primary_agent_name: string;
  last_message_at: string;
  messages: Array<{ role: string; content: string }>;
}

// Route keywords to the right tool
function isResearchQuery(q: string): boolean {
  const lower = q.toLowerCase();
  const keywords = [
    'treatment', 'trial', 'clinical', 'drug', 'medication option', 'alternative',
    'guideline', 'study', 'research', 'evidence', 'compare', 'efficacy',
    'side effect', 'cancer', 'therapy', 'immunotherapy', 'protocol',
    'first-line', 'second-line', 'standard of care', 'nccn', 'acc', 'ada',
  ];
  return keywords.some((k) => lower.includes(k));
}

function askHealthChat(question: string) {
  router.push({
    pathname: '/(tabs)/chat/[conversationId]',
    params: { conversationId: 'new', agentType: 'health_chat', initialMessage: question },
  } as never);
}

function openResearch(query?: string) {
  if (query) {
    router.push({
      pathname: '/(tabs)/chat/research',
      params: { initialQuery: query },
    } as never);
  } else {
    router.push('/(tabs)/chat/research' as never);
  }
}

const QUICK_QUESTIONS = [
  { label: 'Review my treatment plan', type: 'chat' },
  { label: 'What should I eat today?', type: 'chat' },
  { label: 'Am I improving this week?', type: 'chat' },
  { label: 'Latest research on my condition', type: 'research' },
];

const CONV_ICONS: Record<string, { icon: string; color: string }> = {
  clinical_research: { icon: 'flask-outline', color: '#818CF8' },
  research_assistant: { icon: 'flask-outline', color: '#818CF8' },
  health_chat: { icon: 'chatbubble-outline', color: '#00D4AA' },
  health_coach: { icon: 'chatbubble-outline', color: '#00D4AA' },
  nutrition_analyst: { icon: 'nutrition-outline', color: '#6EE7B7' },
  symptom_investigator: { icon: 'search-outline', color: '#F5A623' },
  medication_advisor: { icon: 'medical-outline', color: '#EC4899' },
  general: { icon: 'chatbubble-outline', color: '#00D4AA' },
};

export default function AskAIScreen() {
  const [question, setQuestion] = useState('');

  const { data: conversations, isLoading } = useQuery({
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
    if (isResearchQuery(q)) {
      openResearch(q);
    } else {
      askHealthChat(q);
    }
  }

  function resumeConversation(conv: Conversation) {
    router.push({
      pathname: '/(tabs)/chat/[conversationId]',
      params: { conversationId: conv.id, agentType: conv.primary_agent_type },
    } as never);
  }

  const recentConvs = (conversations ?? []).slice(0, 8);

  return (
    <ScrollView
      className="flex-1 bg-obsidian-900"
      contentContainerStyle={{ paddingBottom: 40 }}
      keyboardShouldPersistTaps="handled"
    >
      {/* Header */}
      <View className="px-6 pt-14 pb-2">
        <Text className="text-2xl font-display text-[#E8EDF5]">Ask AI</Text>
        <Text className="text-[#526380] text-sm mt-1">Your health intelligence</Text>
      </View>

      {/* Universal search bar */}
      <View className="px-6 mb-5">
        <View className="flex-row items-center bg-surface-raised border border-primary-500/40 rounded-2xl px-4 py-3 gap-3">
          <Ionicons name="sparkles-outline" size={18} color="#00D4AA" />
          <TextInput
            className="flex-1 text-[#E8EDF5] text-base"
            placeholder="Ask anything about your health..."
            placeholderTextColor="#526380"
            value={question}
            onChangeText={setQuestion}
            onSubmitEditing={handleAsk}
            returnKeyType="send"
          />
          {question.trim().length > 0 && (
            <TouchableOpacity onPress={handleAsk} activeOpacity={0.7}>
              <View className="w-8 h-8 rounded-full bg-primary-500 items-center justify-center">
                <Ionicons name="arrow-up" size={16} color="#080B10" />
              </View>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Two main tools */}
      <View className="px-6 mb-5">
        <View className="flex-row gap-3">
          {/* Clinical Research */}
          <TouchableOpacity
            onPress={() => openResearch()}
            className="flex-1 bg-surface-raised border border-surface-border rounded-2xl p-4"
            activeOpacity={0.7}
          >
            <View className="w-12 h-12 rounded-xl items-center justify-center mb-3" style={{ backgroundColor: '#818CF815' }}>
              <Ionicons name="flask-outline" size={24} color="#818CF8" />
            </View>
            <Text className="text-[#E8EDF5] font-sansMedium text-sm mb-1">Clinical Research</Text>
            <Text className="text-[#526380] text-[10px] leading-4">
              Treatments, drugs, clinical trials, guidelines & evidence
            </Text>
          </TouchableOpacity>

          {/* Health Chat */}
          <TouchableOpacity
            onPress={() => askHealthChat('')}
            className="flex-1 bg-surface-raised border border-surface-border rounded-2xl p-4"
            activeOpacity={0.7}
          >
            <View className="w-12 h-12 rounded-xl items-center justify-center mb-3" style={{ backgroundColor: '#00D4AA15' }}>
              <Ionicons name="chatbubble-outline" size={24} color="#00D4AA" />
            </View>
            <Text className="text-[#E8EDF5] font-sansMedium text-sm mb-1">Health Chat</Text>
            <Text className="text-[#526380] text-[10px] leading-4">
              Ask anything about your health data, nutrition, symptoms, or meds
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Quick questions */}
      <View className="px-6 mb-5">
        <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Quick Questions</Text>
        <View className="flex-row flex-wrap gap-2">
          {QUICK_QUESTIONS.map((q) => (
            <TouchableOpacity
              key={q.label}
              onPress={() => q.type === 'research' ? openResearch(q.label) : askHealthChat(q.label)}
              className="bg-surface-raised border border-surface-border rounded-full px-3 py-1.5 flex-row items-center gap-1"
              activeOpacity={0.7}
            >
              <Ionicons
                name={q.type === 'research' ? 'flask-outline' : 'chatbubble-outline'}
                size={10}
                color={q.type === 'research' ? '#818CF8' : '#00D4AA'}
              />
              <Text className="text-[#8B9BB4] text-xs">{q.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Recent conversations */}
      {isLoading ? (
        <ActivityIndicator color="#00D4AA" className="mt-4" />
      ) : recentConvs.length > 0 ? (
        <View className="px-6">
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3">Recent</Text>
          {recentConvs.map((conv) => {
            const cfg = CONV_ICONS[conv.primary_agent_type] ?? CONV_ICONS.general;
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
                <View className="w-9 h-9 rounded-xl items-center justify-center mr-3" style={{ backgroundColor: `${cfg.color}18` }}>
                  <Ionicons name={cfg.icon as never} size={16} color={cfg.color} />
                </View>
                <View className="flex-1 mr-2">
                  <Text className="text-[#E8EDF5] text-sm" numberOfLines={1}>
                    {snippet.length > 50 ? `${snippet.slice(0, 50)}...` : snippet}
                  </Text>
                  <Text className="text-[#3D4F66] text-[10px] mt-0.5">{conv.primary_agent_name}</Text>
                </View>
                <Text className="text-[#3A4A5C] text-xs">{dateLabel}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      ) : null}
    </ScrollView>
  );
}
