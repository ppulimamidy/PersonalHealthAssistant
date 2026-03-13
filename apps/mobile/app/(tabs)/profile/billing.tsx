/**
 * Phase 2: Billing / Upgrade screen.
 *
 * Uses expo-web-browser to open Stripe Checkout in an in-app browser.
 * Apple IAP is required before App Store submission (see docs/MOBILE_ARCHITECTURE.md
 * Section 3.9 and Q10). For TestFlight beta, Stripe web checkout is acceptable.
 */

import { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity,
  ActivityIndicator, Alert,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as WebBrowser from 'expo-web-browser';
import { format } from 'date-fns';
import { api } from '@/services/api';

// ─── Types ────────────────────────────────────────────────────────────────────

interface SubscriptionResponse {
  tier: string;
  status: string;
  current_period_end?: string;
  cancel_at_period_end?: boolean;
  usage: {
    ai_calls_today: number;
    ai_calls_limit: number;
    insights_today: number;
    insights_limit: number;
  };
}

interface PlanFeature {
  text: string;
  included: boolean;
}

const PLANS: Array<{
  tier: string;
  label: string;
  price: string;
  period: string;
  color: string;
  features: PlanFeature[];
}> = [
  {
    tier: 'free',
    label: 'Free',
    price: '$0',
    period: '/month',
    color: '#526380',
    features: [
      { text: '5 AI queries/day', included: true },
      { text: 'Symptom & medication logging', included: true },
      { text: 'Basic insights', included: true },
      { text: 'Advanced AI analysis', included: false },
      { text: 'Doctor prep reports', included: false },
      { text: 'Trend correlations', included: false },
    ],
  },
  {
    tier: 'pro',
    label: 'Pro',
    price: '$19',
    period: '/month',
    color: '#00D4AA',
    features: [
      { text: '50 AI queries/day', included: true },
      { text: 'Symptom & medication logging', included: true },
      { text: 'Advanced insights', included: true },
      { text: 'Advanced AI analysis', included: true },
      { text: 'Doctor prep reports', included: true },
      { text: 'Trend correlations', included: false },
    ],
  },
  {
    tier: 'pro_plus',
    label: 'Pro+',
    price: '$39',
    period: '/month',
    color: '#818CF8',
    features: [
      { text: 'Unlimited AI queries', included: true },
      { text: 'Symptom & medication logging', included: true },
      { text: 'Advanced insights', included: true },
      { text: 'Advanced AI analysis', included: true },
      { text: 'Doctor prep reports', included: true },
      { text: 'Trend correlations', included: true },
    ],
  },
];

// ─── Screen ────────────────────────────────────────────────────────────────────

export default function BillingScreen() {
  const queryClient = useQueryClient();
  const [upgradingTier, setUpgradingTier] = useState<string | null>(null);
  const [openingPortal, setOpeningPortal] = useState(false);

  const { data: sub, isLoading } = useQuery<SubscriptionResponse>({
    queryKey: ['subscription'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/billing/subscription');
      return data;
    },
  });

  const checkoutMutation = useMutation({
    mutationFn: async (tier: string) => {
      const { data } = await api.post('/api/v1/billing/create-checkout-session', { tier });
      return data.checkout_url as string;
    },
    onSuccess: async (url) => {
      const result = await WebBrowser.openBrowserAsync(url, {
        presentationStyle: WebBrowser.WebBrowserPresentationStyle.PAGE_SHEET,
      });
      // Refresh subscription after returning
      if (result.type === 'dismiss' || result.type === 'cancel') {
        queryClient.invalidateQueries({ queryKey: ['subscription'] });
      }
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : 'Could not open checkout';
      Alert.alert('Checkout Error', msg);
    },
    onSettled: () => setUpgradingTier(null),
  });

  async function handleUpgrade(tier: string) {
    setUpgradingTier(tier);
    checkoutMutation.mutate(tier);
  }

  async function handleManageSubscription() {
    setOpeningPortal(true);
    try {
      const { data } = await api.post('/api/v1/billing/create-portal-session');
      await WebBrowser.openBrowserAsync(data.portal_url, {
        presentationStyle: WebBrowser.WebBrowserPresentationStyle.PAGE_SHEET,
      });
      queryClient.invalidateQueries({ queryKey: ['subscription'] });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Could not open billing portal';
      Alert.alert('Error', msg);
    } finally {
      setOpeningPortal(false);
    }
  }

  const currentTier = sub?.tier ?? 'free';
  const isActive = sub?.status === 'active';

  const TIER_COLOR: Record<string, string> = {
    free: '#526380',
    pro: '#00D4AA',
    pro_plus: '#818CF8',
  };

  const tierColor = TIER_COLOR[currentTier] ?? '#526380';

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <Text className="text-xl font-display text-[#E8EDF5]">Plan & Billing</Text>
      </View>

      <View className="px-6 pt-6">
        {/* Current plan card */}
        {isLoading ? (
          <View className="bg-surface-raised border border-surface-border rounded-2xl p-6 mb-6 items-center">
            <ActivityIndicator color="#00D4AA" />
          </View>
        ) : (
          <View className="bg-surface-raised border border-surface-border rounded-2xl p-5 mb-6">
            <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3">Current Plan</Text>
            <View className="flex-row items-center justify-between mb-4">
              <View className="flex-row items-center gap-3">
                <View
                  className="w-12 h-12 rounded-2xl items-center justify-center"
                  style={{ backgroundColor: `${tierColor}20` }}
                >
                  <Ionicons name="shield-checkmark" size={22} color={tierColor} />
                </View>
                <View>
                  <Text className="text-[#E8EDF5] font-sansMedium text-base capitalize">
                    {currentTier.replace('_', ' ')}
                  </Text>
                  <Text className="text-[#526380] text-xs mt-0.5 capitalize">
                    {isActive ? 'Active' : sub?.status ?? 'Free'}
                    {sub?.cancel_at_period_end ? ' · Cancels at period end' : ''}
                  </Text>
                </View>
              </View>
              {sub?.current_period_end && (
                <Text className="text-[#526380] text-xs">
                  Renews {format(new Date(sub.current_period_end), 'MMM d')}
                </Text>
              )}
            </View>

            {/* Usage meters */}
            {sub?.usage && (
              <View className="gap-3 mb-4">
                <UsageMeter
                  label="AI queries today"
                  used={sub.usage.ai_calls_today}
                  limit={sub.usage.ai_calls_limit}
                  color={tierColor}
                />
                <UsageMeter
                  label="Insights today"
                  used={sub.usage.insights_today}
                  limit={sub.usage.insights_limit}
                  color={tierColor}
                />
              </View>
            )}

            {currentTier !== 'free' && (
              <TouchableOpacity
                onPress={handleManageSubscription}
                disabled={openingPortal}
                className="border border-surface-border rounded-xl py-3 items-center flex-row justify-center gap-2"
                activeOpacity={0.7}
              >
                {openingPortal ? (
                  <ActivityIndicator size="small" color="#526380" />
                ) : (
                  <>
                    <Ionicons name="settings-outline" size={16} color="#526380" />
                    <Text className="text-[#526380] text-sm font-sansMedium">Manage Subscription</Text>
                  </>
                )}
              </TouchableOpacity>
            )}
          </View>
        )}

        {/* Plan cards */}
        <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3">Choose a Plan</Text>
        <View className="gap-4">
          {PLANS.map((plan) => {
            const isCurrent = plan.tier === currentTier;
            const isUpgrading = upgradingTier === plan.tier;

            return (
              <View
                key={plan.tier}
                className="bg-surface-raised border rounded-2xl p-5"
                style={{
                  borderColor: isCurrent ? plan.color : '#1E2A3B',
                  borderWidth: isCurrent ? 1.5 : 1,
                }}
              >
                {/* Plan header */}
                <View className="flex-row items-center justify-between mb-1">
                  <View className="flex-row items-center gap-2">
                    <Text className="text-[#E8EDF5] font-sansMedium text-base">{plan.label}</Text>
                    {isCurrent && (
                      <View
                        className="px-2 py-0.5 rounded-full"
                        style={{ backgroundColor: `${plan.color}20` }}
                      >
                        <Text className="text-xs font-sansMedium" style={{ color: plan.color }}>Current</Text>
                      </View>
                    )}
                  </View>
                  <View className="flex-row items-baseline gap-0.5">
                    <Text className="text-[#E8EDF5] font-display text-2xl">{plan.price}</Text>
                    <Text className="text-[#526380] text-xs">{plan.period}</Text>
                  </View>
                </View>

                {/* Features */}
                <View className="gap-2 mt-3 mb-4">
                  {plan.features.map((f) => (
                    <View key={f.text} className="flex-row items-center gap-2">
                      <Ionicons
                        name={f.included ? 'checkmark-circle' : 'close-circle-outline'}
                        size={16}
                        color={f.included ? plan.color : '#3A4A5C'}
                      />
                      <Text
                        className="text-sm"
                        style={{ color: f.included ? '#E8EDF5' : '#3A4A5C' }}
                      >
                        {f.text}
                      </Text>
                    </View>
                  ))}
                </View>

                {/* CTA */}
                {plan.tier !== 'free' && !isCurrent && (
                  <TouchableOpacity
                    onPress={() => handleUpgrade(plan.tier)}
                    disabled={upgradingTier !== null}
                    className="rounded-xl py-3 items-center flex-row justify-center gap-2"
                    style={{ backgroundColor: plan.color }}
                    activeOpacity={0.8}
                  >
                    {isUpgrading ? (
                      <ActivityIndicator size="small" color="#080B10" />
                    ) : (
                      <>
                        <Ionicons name="arrow-up-circle" size={18} color="#080B10" />
                        <Text className="text-obsidian-900 font-sansMedium">
                          Upgrade to {plan.label}
                        </Text>
                      </>
                    )}
                  </TouchableOpacity>
                )}
              </View>
            );
          })}
        </View>

        {/* Beta note */}
        <View className="bg-amber-500/10 border border-amber-500/30 rounded-xl px-4 py-3 mt-5 flex-row gap-3">
          <Ionicons name="information-circle-outline" size={16} color="#F5A623" style={{ marginTop: 1 }} />
          <Text className="text-amber-500 text-xs leading-4 flex-1">
            Payments are processed securely via Stripe. App Store in-app purchases will be
            available in a future release. See docs/MOBILE_ARCHITECTURE.md Section 3.9.
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

// ─── UsageMeter ───────────────────────────────────────────────────────────────

function UsageMeter({
  label, used, limit, color,
}: { label: string; used: number; limit: number; color: string }) {
  const pct = limit > 0 ? Math.min(used / limit, 1) : 0;
  const unlimited = limit >= 999;

  return (
    <View>
      <View className="flex-row justify-between mb-1">
        <Text className="text-[#526380] text-xs">{label}</Text>
        <Text className="text-[#526380] text-xs">
          {used} / {unlimited ? '∞' : limit}
        </Text>
      </View>
      {!unlimited && (
        <View className="h-1.5 bg-surface rounded-full overflow-hidden">
          <View
            className="h-full rounded-full"
            style={{ width: `${pct * 100}%`, backgroundColor: pct > 0.8 ? '#F87171' : color }}
          />
        </View>
      )}
    </View>
  );
}
