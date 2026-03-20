/**
 * Inline Nutrition Chat — collapsible bottom sheet chat panel.
 * Uses the nutrition_analyst agent with today's meal context pre-injected.
 */

import { useState, useRef, useEffect } from 'react';
import {
  View, Text, TouchableOpacity, TextInput, FlatList,
  KeyboardAvoidingView, Platform, Animated, Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/services/api';

const SCREEN_HEIGHT = Dimensions.get('window').height;
const COLLAPSED_HEIGHT = 56;
const EXPANDED_HEIGHT = SCREEN_HEIGHT * 0.65;

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

const QUICK_REPLIES = [
  'What should I eat next?',
  'Is this meal good for me?',
  'Lower carb option',
  'High protein ideas',
];

interface Props {
  visible: boolean;
  onClose: () => void;
  initialMessage?: string;
}

export default function InlineNutritionChat({ visible, onClose, initialMessage }: Readonly<Props>) {
  const [expanded, setExpanded] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const heightAnim = useRef(new Animated.Value(COLLAPSED_HEIGHT)).current;
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    if (visible && initialMessage && messages.length === 0) {
      setExpanded(true);
      sendMessage(initialMessage);
    }
  }, [visible, initialMessage]);

  useEffect(() => {
    Animated.spring(heightAnim, {
      toValue: expanded ? EXPANDED_HEIGHT : COLLAPSED_HEIGHT,
      useNativeDriver: false,
      tension: 65,
      friction: 11,
    }).start();
  }, [expanded]);

  async function sendMessage(text: string) {
    if (!text.trim() || loading) return;
    const userMsg: Message = { id: `u-${Date.now()}`, role: 'user', content: text.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const { data } = await api.post('/api/v1/agents/chat', {
        message: text.trim(),
        agent_type: 'nutrition_analyst',
        conversation_id: conversationId,
        conversation_type: 'nutrition_contextual',
      });
      // API returns full messages array — extract the last assistant message
      const allMsgs = data?.messages ?? [];
      const convId = data?.conversation_id ?? conversationId;
      if (convId) setConversationId(convId);
      if (allMsgs.length > 0) {
        // Map all messages to our format (API has the full history)
        setMessages(allMsgs.map((m: any, i: number) => ({
          id: m.id ?? `m-${i}`,
          role: m.role as 'user' | 'assistant',
          content: m.content,
        })));
      } else {
        // Fallback: try response/message field
        const reply = data?.response ?? data?.message ?? 'I couldn\'t generate a response.';
        setMessages((prev) => [...prev, { id: `a-${Date.now()}`, role: 'assistant', content: reply }]);
      }
    } catch {
      setMessages((prev) => [...prev, {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I couldn\'t connect to the nutrition coach right now.',
      }]);
    } finally {
      setLoading(false);
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
    }
  }

  if (!visible) return null;

  return (
    <Animated.View
      style={{ height: heightAnim }}
      className="absolute bottom-0 left-0 right-0 bg-[#0F1720] border-t border-surface-border rounded-t-2xl"
    >
      {/* Collapsed peek bar */}
      <TouchableOpacity
        onPress={() => setExpanded((e) => !e)}
        className="flex-row items-center justify-between px-5 py-3.5"
        activeOpacity={0.8}
      >
        <View className="flex-row items-center gap-2">
          <Ionicons name="sparkles" size={16} color="#00D4AA" />
          <Text className="text-[#E8EDF5] text-sm font-sansMedium">
            {expanded ? 'Nutrition Coach' : 'Ask your nutrition coach'}
          </Text>
        </View>
        <View className="flex-row items-center gap-2">
          {expanded && (
            <TouchableOpacity onPress={() => { setExpanded(false); onClose(); }} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
              <Ionicons name="close" size={18} color="#526380" />
            </TouchableOpacity>
          )}
          <Ionicons name={expanded ? 'chevron-down' : 'chevron-up'} size={16} color="#526380" />
        </View>
      </TouchableOpacity>

      {/* Expanded chat content */}
      {expanded && (
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          className="flex-1"
          keyboardVerticalOffset={0}
        >
          {/* Messages */}
          <FlatList
            ref={flatListRef}
            data={messages}
            keyExtractor={(m) => m.id}
            className="flex-1 px-4"
            contentContainerStyle={{ paddingBottom: 8, paddingTop: 4 }}
            renderItem={({ item }) => (
              <View
                className="mb-2 rounded-xl px-3 py-2 max-w-[85%]"
                style={{
                  alignSelf: item.role === 'user' ? 'flex-end' : 'flex-start',
                  backgroundColor: item.role === 'user' ? '#00D4AA18' : '#1E2A3B',
                }}
              >
                <Text
                  className="text-sm leading-5"
                  style={{ color: item.role === 'user' ? '#E8EDF5' : '#8B9BB4' }}
                >
                  {item.content}
                </Text>
              </View>
            )}
            ListEmptyComponent={
              <View className="items-center py-6">
                <Text className="text-[#3D4F66] text-xs text-center">
                  Ask about your meals, get suggestions, or plan ahead
                </Text>
              </View>
            }
          />

          {/* Typing indicator */}
          {loading && (
            <View className="px-4 pb-1">
              <View className="bg-[#1E2A3B] rounded-xl px-3 py-2 self-start">
                <Text className="text-[#526380] text-xs">Thinking...</Text>
              </View>
            </View>
          )}

          {/* Quick replies (only when no messages or after each response) */}
          {!loading && (messages.length === 0 || messages[messages.length - 1]?.role === 'assistant') && (
            <View className="px-4 pb-2">
              <FlatList
                horizontal
                showsHorizontalScrollIndicator={false}
                data={QUICK_REPLIES}
                keyExtractor={(item) => item}
                renderItem={({ item }) => (
                  <TouchableOpacity
                    onPress={() => sendMessage(item)}
                    className="mr-2 px-3 py-1.5 rounded-lg"
                    style={{ backgroundColor: '#00D4AA10', borderWidth: 1, borderColor: '#00D4AA25' }}
                    activeOpacity={0.7}
                  >
                    <Text className="text-[#00D4AA] text-[11px]">{item}</Text>
                  </TouchableOpacity>
                )}
              />
            </View>
          )}

          {/* Input bar */}
          <View className="flex-row items-center gap-2 px-4 pb-4 pt-2 border-t border-surface-border">
            <TextInput
              value={input}
              onChangeText={setInput}
              placeholder="Ask about nutrition..."
              placeholderTextColor="#3D4F66"
              className="flex-1 bg-surface-raised border border-surface-border rounded-xl px-3 py-2 text-[#E8EDF5] text-sm"
              multiline
              maxLength={500}
              onSubmitEditing={() => sendMessage(input)}
              returnKeyType="send"
            />
            <TouchableOpacity
              onPress={() => sendMessage(input)}
              disabled={!input.trim() || loading}
              className="rounded-xl p-2"
              style={{ backgroundColor: input.trim() ? '#00D4AA' : '#1E2A3B' }}
              activeOpacity={0.7}
            >
              <Ionicons name="send" size={16} color={input.trim() ? '#080B10' : '#526380'} />
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>
      )}
    </Animated.View>
  );
}
