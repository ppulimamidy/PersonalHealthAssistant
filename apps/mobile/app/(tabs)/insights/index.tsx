/**
 * Insights Hub — redesigned as a command center.
 *
 * Layout (top → bottom):
 * 1. "Today's Top Insight" — prominent actionable card with CTA
 * 2. Recent Insights — horizontal scroll of compact cards
 * 3. "Dig Deeper" — 3 analysis cards in a compact row
 * 4. Weekly Review — summary card (when available)
 */

import { useState } from 'react';
import {
  View, Text, ScrollView, FlatList, RefreshControl, ActivityIndicator,
  TouchableOpacity, Dimensions,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { api } from '@/services/api';
import type { AIInsight } from '@/types';
import { formatDistanceToNow } from 'date-fns';

const SCREEN_WIDTH = Dimensions.get('window').width;
const INSIGHT_CARD_WIDTH = SCREEN_WIDTH * 0.62;
const INSIGHT_CARD_GAP = 10;

// ─── Top Insight Card ─────────────────────────────────────────────────────────

function TopInsightCard({ insight }: Readonly<{ insight: AIInsight }>) {
  const typeColor = insight.type === 'alert' ? '#F87171'
    : insight.type === 'recommendation' ? '#F5A623'
    : '#6EE7B7';
  const typeIcon = insight.type === 'alert' ? 'warning-outline'
    : insight.type === 'recommendation' ? 'bulb-outline'
    : 'trending-up-outline';
  const typeLabel = insight.type === 'alert' ? 'Alert'
    : insight.type === 'recommendation' ? 'Recommendation'
    : 'Pattern';

  return (
    <View
      className="bg-surface-raised rounded-2xl p-5 mb-4 border border-surface-border"
      style={{ borderLeftWidth: 3, borderLeftColor: typeColor }}
    >
      <View className="flex-row items-center gap-2 mb-2">
        <View className="rounded-lg p-1.5" style={{ backgroundColor: `${typeColor}20` }}>
          <Ionicons name={typeIcon as never} size={14} color={typeColor} />
        </View>
        <Text className="text-xs font-sansMedium uppercase tracking-wider" style={{ color: typeColor }}>
          {typeLabel}
        </Text>
      </View>
      <Text className="text-[#E8EDF5] font-sansMedium text-base leading-6 mb-1">
        {insight.title}
      </Text>
      <Text className="text-[#526380] text-sm leading-5 mb-3" numberOfLines={3}>
        {insight.summary}
      </Text>
      {insight.type === 'recommendation' && (
        <TouchableOpacity
          onPress={() => router.push('/(tabs)/insights/correlations')}
          className="self-start flex-row items-center gap-1 px-3 py-1.5 rounded-lg"
          style={{ backgroundColor: `${typeColor}15`, borderWidth: 1, borderColor: `${typeColor}30` }}
          activeOpacity={0.7}
        >
          <Text className="text-xs font-sansMedium" style={{ color: typeColor }}>Explore pattern</Text>
          <Ionicons name="arrow-forward" size={12} color={typeColor} />
        </TouchableOpacity>
      )}
    </View>
  );
}

// ─── Horizontal Insight Card ──────────────────────────────────────────────────

function HorizontalInsightCard({ item }: Readonly<{ item: AIInsight }>) {
  const typeColor = item.type === 'alert' ? '#F87171'
    : item.type === 'recommendation' ? '#F5A623'
    : '#6EE7B7';
  const timeAgo = item.created_at
    ? formatDistanceToNow(new Date(item.created_at), { addSuffix: true })
    : '';

  return (
    <TouchableOpacity
      activeOpacity={0.8}
      className="bg-surface-raised border border-surface-border rounded-xl p-3.5"
      style={{ width: INSIGHT_CARD_WIDTH, marginRight: INSIGHT_CARD_GAP }}
    >
      <View className="flex-row items-center gap-1.5 mb-1.5">
        <View className="w-2 h-2 rounded-full" style={{ backgroundColor: typeColor }} />
        <Text className="text-[10px] uppercase tracking-wider" style={{ color: typeColor }}>
          {item.type}
        </Text>
        {timeAgo ? (
          <Text className="text-[#3D4F66] text-[10px] ml-auto">{timeAgo}</Text>
        ) : null}
      </View>
      <Text className="text-[#E8EDF5] text-sm font-sansMedium leading-5" numberOfLines={2}>
        {item.title}
      </Text>
      <Text className="text-[#526380] text-xs mt-1 leading-4" numberOfLines={2}>
        {item.summary}
      </Text>
    </TouchableOpacity>
  );
}

// ─── Compact Analysis Row ─────────────────────────────────────────────────────

const ANALYSIS_ITEMS = [
  { label: 'Timeline', icon: 'time-outline' as const, color: '#00D4AA', route: '/(tabs)/insights/timeline' },
  { label: 'Triggers', icon: 'git-branch-outline' as const, color: '#A78BFA', route: '/(tabs)/insights/correlations' },
  { label: 'Forecast', icon: 'telescope-outline' as const, color: '#60A5FA', route: '/(tabs)/insights/predictions' },
  { label: 'Trends', icon: 'trending-up-outline' as const, color: '#6EE7B7', route: '/(tabs)/insights/trends' },
] as const;

function AnalysisRow({ badges }: Readonly<{ badges: Record<string, number> }>) {
  return (
    <View className="flex-row gap-2 mb-5">
      {ANALYSIS_ITEMS.map((item) => {
        const count = badges[item.label] ?? 0;
        return (
          <TouchableOpacity
            key={item.label}
            onPress={() => router.push(item.route as never)}
            className="flex-1 bg-surface-raised border border-surface-border rounded-xl py-3 items-center"
            activeOpacity={0.7}
          >
            <View>
              <View className="rounded-lg p-1.5 mb-1" style={{ backgroundColor: `${item.color}15` }}>
                <Ionicons name={item.icon as never} size={18} color={item.color} />
              </View>
              {count > 0 && (
                <View
                  className="absolute items-center justify-center rounded-full"
                  style={{
                    top: -4,
                    right: -6,
                    minWidth: 16,
                    height: 16,
                    paddingHorizontal: 3,
                    backgroundColor: item.color,
                  }}
                >
                  <Text className="text-[#0B1120] text-[9px] font-sansMedium">
                    {count > 9 ? '9+' : count}
                  </Text>
                </View>
              )}
            </View>
            <Text className="text-[#8B9BB4] text-[10px] font-sansMedium">{item.label}</Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

// ─── Weekly Review Card ───────────────────────────────────────────────────────

interface WeeklyReview {
  summary: string;
  metrics: Record<string, { current: number; previous: number; delta: number }>;
  top_achievement?: string | null;
  watch_area?: string | null;
}

function WeeklyReviewCard({ review }: Readonly<{ review: WeeklyReview }>) {
  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-4">
      <View className="flex-row items-center gap-2 mb-2">
        <Ionicons name="calendar-outline" size={14} color="#526380" />
        <Text className="text-[#526380] text-xs uppercase tracking-wider">This Week</Text>
      </View>
      <Text className="text-[#E8EDF5] text-sm leading-5 mb-3">{review.summary}</Text>

      {/* Metric pills */}
      <View className="flex-row flex-wrap gap-2 mb-2">
        {Object.entries(review.metrics).slice(0, 4).map(([key, m]) => {
          const isPositive = m.delta > 0;
          const color = isPositive ? '#00D4AA' : m.delta < 0 ? '#F87171' : '#526380';
          const label = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
          return (
            <View key={key} className="flex-row items-center gap-1 bg-white/5 rounded-lg px-2 py-1">
              <Ionicons
                name={isPositive ? 'trending-up' : m.delta < 0 ? 'trending-down' : 'remove'}
                size={10}
                color={color}
              />
              <Text className="text-[#8B9BB4] text-[10px]">{label}</Text>
              <Text className="text-[10px] font-sansMedium" style={{ color }}>
                {m.delta > 0 ? '+' : ''}{Math.round(m.delta)}
              </Text>
            </View>
          );
        })}
      </View>

      {review.top_achievement && (
        <View className="flex-row items-center gap-1.5 mt-1">
          <Ionicons name="checkmark-circle" size={12} color="#00D4AA" />
          <Text className="text-[#6EE7B7] text-xs">{review.top_achievement}</Text>
        </View>
      )}
      {review.watch_area && (
        <View className="flex-row items-center gap-1.5 mt-1">
          <Ionicons name="eye-outline" size={12} color="#F5A623" />
          <Text className="text-[#F5A623] text-xs">{review.watch_area}</Text>
        </View>
      )}
    </View>
  );
}

// ─── Quick Access Row ─────────────────────────────────────────────────────────

function ToolBadge({ count, color }: Readonly<{ count: number; color: string }>) {
  if (count <= 0) return null;
  return (
    <View
      className="rounded-full items-center justify-center"
      style={{ minWidth: 16, height: 16, paddingHorizontal: 3, backgroundColor: color }}
    >
      <Text className="text-[#0B1120] text-[9px] font-sansMedium">
        {count > 9 ? '9+' : count}
      </Text>
    </View>
  );
}

function QuickAccessRow({ badges }: Readonly<{ badges: Record<string, number> }>) {
  const tools = [
    { label: 'Visit Prep', icon: 'document-text-outline' as const, color: '#2DD4BF', route: '/(tabs)/insights/doctor-prep' },
    { label: 'Research', icon: 'book-outline' as const, color: '#818CF8', route: '/(tabs)/insights/research' },
    { label: 'Analysis', icon: 'analytics-outline' as const, color: '#F5A623', route: '/(tabs)/insights/meta-analysis' },
  ];

  return (
    <View className="mb-4">
      <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Tools</Text>
      <View className="flex-row gap-2">
        {tools.map((t) => (
          <TouchableOpacity
            key={t.label}
            onPress={() => router.push(t.route as never)}
            className="flex-1 bg-surface-raised border border-surface-border rounded-xl p-3 flex-row items-center gap-2"
            activeOpacity={0.7}
          >
            <Ionicons name={t.icon as never} size={16} color={t.color} />
            <Text className="text-[#8B9BB4] text-xs font-sansMedium flex-1">{t.label}</Text>
            <ToolBadge count={badges[t.label] ?? 0} color={t.color} />
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function InsightsScreen() {
  const { data: insights, isLoading, refetch } = useQuery({
    queryKey: ['insights'],
    queryFn: async () => {
      // Use batch endpoint (same as Home) — avoids usage gate throttle on /insights/ direct call
      try {
        const { data: batch } = await api.get('/api/v1/batch', {
          params: { resources: 'insights' },
        });
        const raw = batch?.resources?.insights ?? batch?.insights;
        if (raw) {
          const list = Array.isArray(raw) ? raw : (raw?.insights ?? []);
          if (list.length > 0) return list as AIInsight[];
        }
      } catch { /* fall through to direct call */ }
      // Fallback: direct endpoint
      try {
        const { data: resp } = await api.get('/api/v1/insights/');
        return (Array.isArray(resp) ? resp : (resp?.insights ?? [])) as AIInsight[];
      } catch {
        return [] as AIInsight[];
      }
    },
  });

  const { data: weeklyReview } = useQuery<WeeklyReview | null>({
    queryKey: ['weekly-review'],
    queryFn: async () => {
      try {
        const { data: resp } = await api.get('/api/v1/insights/weekly-review');
        return resp as WeeklyReview;
      } catch {
        return null;
      }
    },
    staleTime: 5 * 60 * 1000,
  });

  // Lightweight badge counts for Explore tiles + Tools
  const { data: badgeCounts } = useQuery<Record<string, number>>({
    queryKey: ['explore-badges'],
    queryFn: async () => {
      const badges: Record<string, number> = {};
      try {
        const [corrResp, metaResp, reportsResp, bookmarksResp] = await Promise.all([
          api.get('/api/v1/correlations?days=14').catch(() => null),
          api.get('/api/v1/specialist-agents/meta-analysis/cached').catch(() => null),
          api.get('/api/v1/doctor-prep/reports').catch(() => null),
          api.get('/api/v1/research/bookmarks').catch(() => null),
        ]);
        // Explore: Triggers
        const corrs = corrResp?.data?.correlations ?? [];
        if (corrs.length > 0) badges['Triggers'] = corrs.length;
        // Explore + Tools: Analysis
        const meta = metaResp?.data;
        const findingsCount = (meta?.findings?.length ?? 0) + (meta?.secondary_findings?.length ?? 0);
        if (findingsCount > 0) {
          badges['Analysis'] = findingsCount;
        }
        // Tools: Visit Prep (number of reports generated)
        const reports = Array.isArray(reportsResp?.data) ? reportsResp.data : (reportsResp?.data?.reports ?? []);
        if (reports.length > 0) badges['Visit Prep'] = reports.length;
        // Tools: Research (number of bookmarked articles)
        const bookmarks = Array.isArray(bookmarksResp?.data) ? bookmarksResp.data : (bookmarksResp?.data?.bookmarks ?? []);
        if (bookmarks.length > 0) badges['Research'] = bookmarks.length;
      } catch { /* silent */ }
      return badges;
    },
    staleTime: 2 * 60 * 1000,
  });

  const allInsights = insights ?? [];
  const topInsight = allInsights[0] ?? null;
  const restInsights = allInsights.slice(1);
  const [activeCardIndex, setActiveCardIndex] = useState(0);

  return (
    <ScrollView
      className="flex-1 bg-obsidian-900"
      contentContainerStyle={{ paddingBottom: 32 }}
      refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor="#00D4AA" />}
    >
      {/* Header */}
      <View className="px-6 pt-14 pb-2">
        <Text className="text-2xl font-display text-[#E8EDF5]">Insights</Text>
        <Text className="text-[#526380] text-sm mt-1">What happened, why, and what's next</Text>
      </View>

      {isLoading ? (
        <ActivityIndicator color="#00D4AA" className="mt-10" />
      ) : (
        <View className="px-6 pt-4">
          {/* 1. Top Insight */}
          {topInsight ? (
            <TopInsightCard insight={topInsight} />
          ) : (
            <View className="bg-surface-raised border border-surface-border rounded-2xl p-5 mb-4 items-center">
              <Ionicons name="bulb-outline" size={32} color="#526380" />
              <Text className="text-[#526380] text-sm mt-2 text-center">
                Log more data to generate your first insight
              </Text>
            </View>
          )}

          {/* 2. Recent Insights — horizontal scroll with pagination dots */}
          {restInsights.length > 0 && (
            <View className="mb-5">
              <View className="flex-row items-center justify-between mb-2">
                <Text className="text-[#526380] text-xs uppercase tracking-wider">Recent</Text>
              </View>
              <FlatList
                data={restInsights}
                keyExtractor={(item) => item.id}
                horizontal
                showsHorizontalScrollIndicator={false}
                snapToInterval={INSIGHT_CARD_WIDTH + INSIGHT_CARD_GAP}
                decelerationRate="fast"
                renderItem={({ item }) => <HorizontalInsightCard item={item} />}
                contentContainerStyle={{ paddingRight: 16 }}
                onScroll={(e) => {
                  const idx = Math.round(e.nativeEvent.contentOffset.x / (INSIGHT_CARD_WIDTH + INSIGHT_CARD_GAP));
                  setActiveCardIndex(idx);
                }}
                scrollEventThrottle={64}
              />
              {/* Pagination dots */}
              {restInsights.length > 1 && (
                <View className="flex-row items-center justify-center gap-1.5 mt-2">
                  {restInsights.map((_, i) => (
                    <View
                      key={i}
                      className="rounded-full"
                      style={{
                        width: activeCardIndex === i ? 16 : 6,
                        height: 6,
                        backgroundColor: activeCardIndex === i ? '#00D4AA' : '#1E2A3B',
                      }}
                    />
                  ))}
                </View>
              )}
            </View>
          )}

          {/* 3. Dig Deeper — compact row with badge counts */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Explore</Text>
          <AnalysisRow badges={badgeCounts ?? {}} />

          {/* 4. Weekly Review */}
          {weeklyReview && <WeeklyReviewCard review={weeklyReview} />}

          {/* 5. Quick Access — Tools */}
          <QuickAccessRow badges={badgeCounts ?? {}} />
        </View>
      )}
    </ScrollView>
  );
}
