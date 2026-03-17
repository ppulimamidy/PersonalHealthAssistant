/**
 * Evidence Library — PubMed keyword search + RAG conversation with AI.
 * Moved here from profile/ because it's an understanding tool, not an account setting.
 *
 * POST /api/v1/research/search
 * GET  /api/v1/research/bookmarks
 * POST /api/v1/research/bookmarks
 * POST /api/v1/research/rag/chat
 */

import { useState, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, TextInput,
  ActivityIndicator, Alert, KeyboardAvoidingView, Platform,
} from 'react-native';
import { router } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import * as Haptics from 'expo-haptics';
import { api } from '@/services/api';

// ─── Types ────────────────────────────────────────────────────────────────────

interface ResearchArticle {
  id: string;
  pubmed_id?: string;
  title: string;
  abstract?: string;
  authors: string[];
  journal?: string;
  publication_date?: string;
  evidence_level: 'meta_analysis' | 'rct' | 'observational' | 'other';
  source_url: string;
  relevance_score?: number;
}

interface RAGMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources: string[];
}

type Tab = 'search' | 'chat' | 'bookmarks';

// ─── Evidence Level Badge ─────────────────────────────────────────────────────

const EVIDENCE_CONFIG: Record<string, { label: string; color: string }> = {
  meta_analysis: { label: 'Meta-Analysis', color: '#6EE7B7' },
  rct:           { label: 'RCT',           color: '#818CF8' },
  observational: { label: 'Observational', color: '#F5A623' },
  other:         { label: 'Other',         color: '#526380' },
};

function EvidenceBadge({ level }: { level: string }) {
  const cfg = EVIDENCE_CONFIG[level] ?? EVIDENCE_CONFIG.other;
  return (
    <View className="px-1.5 py-0.5 rounded" style={{ backgroundColor: `${cfg.color}20` }}>
      <Text className="text-xs" style={{ color: cfg.color }}>{cfg.label}</Text>
    </View>
  );
}

// ─── Article Card ─────────────────────────────────────────────────────────────

function ArticleCard({
  article,
  onBookmark,
  bookmarked,
}: {
  article: ResearchArticle;
  onBookmark: (id: string) => void;
  bookmarked: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <TouchableOpacity
      onPress={() => setExpanded((e) => !e)}
      className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2"
      activeOpacity={0.8}
    >
      <View className="flex-row items-start justify-between mb-2">
        <View className="flex-1 mr-2">
          <Text className="text-[#E8EDF5] font-sansMedium text-sm leading-5" numberOfLines={expanded ? undefined : 2}>
            {article.title}
          </Text>
          <View className="flex-row items-center gap-2 mt-1.5 flex-wrap">
            <EvidenceBadge level={article.evidence_level} />
            {article.journal && (
              <Text className="text-[#526380] text-xs" numberOfLines={1}>{article.journal}</Text>
            )}
            {article.publication_date && (
              <Text className="text-[#526380] text-xs">
                {format(new Date(article.publication_date), 'yyyy')}
              </Text>
            )}
          </View>
        </View>
        <TouchableOpacity onPress={() => onBookmark(article.id)} className="p-1 ml-1">
          <Ionicons
            name={bookmarked ? 'bookmark' : 'bookmark-outline'}
            size={18}
            color={bookmarked ? '#00D4AA' : '#526380'}
          />
        </TouchableOpacity>
      </View>

      {expanded && article.abstract && (
        <Text className="text-[#526380] text-xs leading-4 mt-1">{article.abstract}</Text>
      )}

      {article.authors.length > 0 && (
        <Text className="text-[#3A4A5C] text-xs mt-1.5" numberOfLines={1}>
          {article.authors.slice(0, 3).join(', ')}{article.authors.length > 3 ? ' et al.' : ''}
        </Text>
      )}
    </TouchableOpacity>
  );
}

// ─── Search Tab ───────────────────────────────────────────────────────────────

function SearchTab() {
  const queryClient = useQueryClient();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<ResearchArticle[]>([]);
  const [bookmarkedIds, setBookmarkedIds] = useState<Set<string>>(new Set());

  const searchMutation = useMutation({
    mutationFn: async (q: string) => {
      const { data } = await api.post('/api/v1/research/search', {
        query: q,
        max_results: 20,
        sort: 'relevance',
      });
      return (data?.articles ?? []) as ResearchArticle[];
    },
    onSuccess: (articles) => setResults(articles),
    onError: () => Alert.alert('Search failed', 'Could not query PubMed'),
  });

  const bookmarkMutation = useMutation({
    mutationFn: async (articleId: string) => {
      await api.post('/api/v1/research/bookmarks', { article_id: articleId, tags: [] });
      return articleId;
    },
    onSuccess: (id) => {
      setBookmarkedIds((prev) => new Set([...prev, id]));
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      queryClient.invalidateQueries({ queryKey: ['research-bookmarks'] });
    },
    onError: () => Alert.alert('Error', 'Could not bookmark article'),
  });

  return (
    <>
      <View className="flex-row gap-2 mb-4">
        <TextInput
          className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] flex-1"
          value={query}
          onChangeText={setQuery}
          placeholder="Search PubMed (e.g. HRV sleep quality)"
          placeholderTextColor="#526380"
          returnKeyType="search"
          onSubmitEditing={() => query.trim().length >= 3 && searchMutation.mutate(query.trim())}
        />
        <TouchableOpacity
          onPress={() => query.trim().length >= 3 && searchMutation.mutate(query.trim())}
          disabled={searchMutation.isPending || query.trim().length < 3}
          className="bg-primary-500 rounded-xl px-4 items-center justify-center"
          activeOpacity={0.8}
        >
          {searchMutation.isPending ? (
            <ActivityIndicator size="small" color="#080B10" />
          ) : (
            <Ionicons name="search" size={20} color="#080B10" />
          )}
        </TouchableOpacity>
      </View>

      {results.length === 0 && !searchMutation.isPending && (
        <View className="items-center py-10">
          <Ionicons name="library-outline" size={44} color="#526380" />
          <Text className="text-[#526380] text-base mt-3">Search medical literature</Text>
          <Text className="text-[#526380] text-sm mt-1 text-center">
            Powered by PubMed. Enter at least 3 characters.
          </Text>
        </View>
      )}

      {results.map((a) => (
        <ArticleCard
          key={a.id}
          article={a}
          bookmarked={bookmarkedIds.has(a.id)}
          onBookmark={(id) => bookmarkMutation.mutate(id)}
        />
      ))}
    </>
  );
}

// ─── Chat Tab ─────────────────────────────────────────────────────────────────

function ChatTab() {
  const [messages, setMessages] = useState<RAGMessage[]>([]);
  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const scrollRef = useRef<ScrollView>(null);

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      const { data } = await api.post('/api/v1/research/rag/chat', {
        conversation_id: conversationId,
        message,
        context_article_ids: [],
      });
      return data;
    },
    onSuccess: (data) => {
      if (data?.id && !conversationId) setConversationId(data.id);
      const msgs: RAGMessage[] = data?.messages ?? [];
      setMessages(msgs);
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
    },
    onError: () => Alert.alert('Error', 'Chat request failed'),
  });

  function handleSend() {
    const msg = input.trim();
    if (!msg) return;
    setInput('');
    const userMsg: RAGMessage = {
      role: 'user',
      content: msg,
      timestamp: new Date().toISOString(),
      sources: [],
    };
    setMessages((prev) => [...prev, userMsg]);
    chatMutation.mutate(msg);
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={{ flex: 1 }}
    >
      <ScrollView ref={scrollRef} className="flex-1" contentContainerStyle={{ paddingBottom: 8 }}>
        {messages.length === 0 && (
          <View className="items-center py-10">
            <Ionicons name="chatbubble-ellipses-outline" size={44} color="#526380" />
            <Text className="text-[#526380] text-base mt-3">Ask about your health</Text>
            <Text className="text-[#526380] text-sm mt-1 text-center">
              AI answers are grounded in PubMed medical literature
            </Text>
          </View>
        )}

        {messages.map((m, i) => (
          <View
            key={i}
            className={`mb-3 ${m.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <View
              className="rounded-2xl px-4 py-3"
              style={{
                backgroundColor: m.role === 'user' ? '#00D4AA20' : '#1E2A3B',
                borderWidth: 1,
                borderColor: m.role === 'user' ? '#00D4AA40' : '#2A3A4E',
                maxWidth: '85%',
              }}
            >
              <Text className={`text-sm leading-5 ${m.role === 'user' ? 'text-primary-500' : 'text-[#E8EDF5]'}`}>
                {m.content}
              </Text>
              {m.sources.length > 0 && (
                <Text className="text-[#526380] text-xs mt-1.5">
                  Sources: {m.sources.slice(0, 2).join(', ')}
                  {m.sources.length > 2 ? ` +${m.sources.length - 2}` : ''}
                </Text>
              )}
            </View>
          </View>
        ))}

        {chatMutation.isPending && (
          <View className="items-start mb-3">
            <View className="bg-surface-raised border border-surface-border rounded-2xl px-4 py-3">
              <ActivityIndicator size="small" color="#526380" />
            </View>
          </View>
        )}
      </ScrollView>

      <View className="flex-row gap-2 pt-2">
        <TextInput
          className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] flex-1"
          value={input}
          onChangeText={setInput}
          placeholder="Ask a health question…"
          placeholderTextColor="#526380"
          returnKeyType="send"
          onSubmitEditing={handleSend}
          multiline
        />
        <TouchableOpacity
          onPress={handleSend}
          disabled={!input.trim() || chatMutation.isPending}
          className="bg-primary-500 rounded-xl px-4 items-center justify-center"
          activeOpacity={0.8}
          style={{ opacity: !input.trim() ? 0.4 : 1 }}
        >
          <Ionicons name="send" size={18} color="#080B10" />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

// ─── Bookmarks Tab ────────────────────────────────────────────────────────────

function BookmarksTab() {
  const { data, isLoading } = useQuery<{ bookmarks: Array<{ id: string; article: ResearchArticle }> }>({
    queryKey: ['research-bookmarks'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/research/bookmarks');
      return resp;
    },
  });

  const bookmarks = data?.bookmarks ?? [];

  if (isLoading) return <ActivityIndicator color="#00D4AA" className="mt-8" />;

  if (bookmarks.length === 0) {
    return (
      <View className="items-center py-12">
        <Ionicons name="bookmark-outline" size={40} color="#526380" />
        <Text className="text-[#526380] text-base mt-3">No bookmarks yet</Text>
        <Text className="text-[#526380] text-sm mt-1 text-center">
          Bookmark articles from the Search tab
        </Text>
      </View>
    );
  }

  return (
    <>
      {bookmarks.map((b) => (
        <ArticleCard
          key={b.id}
          article={b.article}
          bookmarked
          onBookmark={() => {}}
        />
      ))}
    </>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

const TABS: Array<{ id: Tab; label: string; icon: React.ComponentProps<typeof Ionicons>['name'] }> = [
  { id: 'search',    label: 'Search',  icon: 'search-outline' },
  { id: 'chat',      label: 'AI Chat', icon: 'chatbubble-outline' },
  { id: 'bookmarks', label: 'Saved',   icon: 'bookmark-outline' },
];

export default function EvidenceLibraryScreen() {
  const [tab, setTab] = useState<Tab>('search');

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      className="flex-1 bg-obsidian-900"
    >
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 40, flexGrow: 1 }}
        keyboardShouldPersistTaps="handled"
      >
        {/* Header */}
        <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
          <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
            <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
          </TouchableOpacity>
          <View className="flex-1">
            <Text className="text-xl font-display text-[#E8EDF5]">Research</Text>
            <Text className="text-[#526380] text-xs mt-0.5">Medical literature · PubMed</Text>
          </View>
        </View>

        {/* Outer tab switcher: AI Analysis / Literature Search */}
        <View className="flex-row mx-4 mt-4 mb-1 p-1 rounded-xl gap-1"
          style={{ backgroundColor: 'rgba(255,255,255,0.04)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}>
          {([
            { label: 'AI Analysis',       icon: 'analytics-outline' as const },
            { label: 'Literature Search', icon: 'library-outline'   as const },
          ] as const).map((t) => (
            <TouchableOpacity
              key={t.label}
              onPress={() => {
                if (t.label === 'AI Analysis') {
                  router.back();
                }
              }}
              className="flex-1 flex-row items-center justify-center gap-1.5 py-2 rounded-lg"
              style={{
                backgroundColor: t.label === 'Literature Search' ? 'rgba(0,212,170,0.12)' : 'transparent',
                borderWidth: t.label === 'Literature Search' ? 1 : 0,
                borderColor: 'rgba(0,212,170,0.2)',
              }}
              activeOpacity={0.7}
            >
              <Ionicons name={t.icon} size={14} color={t.label === 'Literature Search' ? '#00D4AA' : '#526380'} />
              <Text className="text-sm font-sansMedium" style={{ color: t.label === 'Literature Search' ? '#00D4AA' : '#526380' }}>
                {t.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Tabs */}
        <View className="flex-row px-6 pt-4 gap-2">
          {TABS.map((t) => (
            <TouchableOpacity
              key={t.id}
              onPress={() => setTab(t.id)}
              className="flex-1 py-2.5 rounded-xl items-center border flex-row justify-center gap-1"
              style={{
                backgroundColor: tab === t.id ? '#00D4AA20' : 'transparent',
                borderColor: tab === t.id ? '#00D4AA' : '#1E2A3B',
              }}
            >
              <Ionicons name={t.icon} size={14} color={tab === t.id ? '#00D4AA' : '#526380'} />
              <Text className="text-xs font-sansMedium" style={{ color: tab === t.id ? '#00D4AA' : '#526380' }}>
                {t.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <View className="px-6 pt-4 flex-1">
          {tab === 'search' && <SearchTab />}
          {tab === 'chat' && <ChatTab />}
          {tab === 'bookmarks' && <BookmarksTab />}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
