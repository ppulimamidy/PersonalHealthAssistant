import { useState, useRef, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, FlatList,
  KeyboardAvoidingView, Platform, ActivityIndicator,
} from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
}

export default function ConversationScreen() {
  const { conversationId, agentType } = useLocalSearchParams<{ conversationId: string; agentType?: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const listRef = useRef<FlatList>(null);

  // Load existing conversation
  useEffect(() => {
    if (conversationId && conversationId !== 'new') {
      api.get(`/api/v1/agents/conversations/${conversationId}`)
        .then(({ data }) => setMessages(data.messages ?? []))
        .catch(() => {});
    }
  }, [conversationId]);

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);
    try {
      const { data } = await api.post('/api/v1/agents/chat', {
        message: text,
        agent_type: agentType ?? 'general',
        conversation_id: conversationId !== 'new' ? conversationId : undefined,
        conversation_type: 'general',
      });
      setMessages(data.messages ?? [...messages, userMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: `err-${Date.now()}`, role: 'assistant', content: 'Sorry, I couldn\'t process that. Please try again.' },
      ]);
    } finally {
      setIsTyping(false);
    }
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
  }

  function MessageBubble({ msg }: { msg: Message }) {
    const isUser = msg.role === 'user';
    return (
      <View className={`mb-3 ${isUser ? 'items-end' : 'items-start'}`}>
        <View
          className={`max-w-xs rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-primary-500/20 border border-primary-500/40 rounded-br-sm'
              : 'bg-surface-raised border border-surface-border rounded-bl-sm'
          }`}
        >
          <Text className="text-[#E8EDF5] leading-5">{msg.content}</Text>
        </View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 83 : 0}
      className="flex-1 bg-obsidian-900"
    >
      {/* Header */}
      <View className="flex-row items-center px-4 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-3 p-1">
          <Ionicons name="arrow-back" size={22} color="#E8EDF5" />
        </TouchableOpacity>
        <Text className="text-[#E8EDF5] font-sansMedium text-lg flex-1" numberOfLines={1}>
          {agentType ? `${agentType.replace('_', ' ')} Agent` : 'Health Agent'}
        </Text>
      </View>

      {/* Messages */}
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <MessageBubble msg={item} />}
        contentContainerStyle={{ padding: 16, paddingBottom: 8 }}
        onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: false })}
        ListEmptyComponent={
          <View className="items-center py-12">
            <Ionicons name="chatbubble-ellipses-outline" size={48} color="#526380" />
            <Text className="text-[#526380] mt-4 text-center">Start a conversation{'\n'}Ask anything about your health</Text>
          </View>
        }
        ListFooterComponent={
          isTyping ? (
            <View className="items-start mb-3">
              <View className="bg-surface-raised border border-surface-border rounded-2xl rounded-bl-sm px-4 py-3">
                <ActivityIndicator size="small" color="#526380" />
              </View>
            </View>
          ) : null
        }
      />

      {/* Input */}
      <View className="flex-row items-end px-4 py-3 border-t border-surface-border gap-2">
        <TextInput
          className="flex-1 bg-surface-raised border border-surface-border rounded-2xl px-4 py-3 text-[#E8EDF5] text-base"
          value={input}
          onChangeText={setInput}
          placeholder="Ask anything..."
          placeholderTextColor="#526380"
          multiline
          maxLength={1000}
          style={{ maxHeight: 120 }}
          returnKeyType="send"
          onSubmitEditing={sendMessage}
        />
        <TouchableOpacity
          onPress={sendMessage}
          disabled={!input.trim() || loading}
          className="bg-primary-500 rounded-2xl p-3"
          style={{ opacity: !input.trim() || loading ? 0.4 : 1 }}
        >
          <Ionicons name="arrow-up" size={20} color="#080B10" />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}
