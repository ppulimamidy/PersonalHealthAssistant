import { useState } from 'react';
import {
  View, Text, TouchableOpacity, ScrollView, TextInput,
  ActivityIndicator, Platform, Alert,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import * as Device from 'expo-device';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '@/services/api';
import { registerForPushNotifications } from '@/services/notifications';

const ONBOARDING_PENDING_KEY = 'onboarding_pending';

// ── Types ────────────────────────────────────────────────────────────────────

type Intent = 'condition' | 'goal' | 'exploring' | '';

interface SpecialistInfo {
  agent_type: string;
  agent_name: string;
  specialty: string;
  description: string;
}

interface JourneyProposal {
  key: string;
  title: string;
  phases: Array<{ name: string; description: string; phase_type: string }>;
  total_phases: number;
}

interface QuickQuestion {
  id: string;
  question: string;
  input_type: string;
  options?: string[];
  text_prompt?: string;
  data_field: string;
}

// ── Goal icons ───────────────────────────────────────────────────────────────

const GOAL_ICONS: Record<string, string> = {
  sleep_optimization: 'moon-outline',
  weight_loss: 'scale-outline',
  muscle_building: 'barbell-outline',
  mental_health: 'leaf-outline',
  general_wellness: 'flash-outline',
  cardiac_rehab: 'heart-outline',
};

// ── Fallback data (used when API fails, e.g. auth token not ready) ───────

const FALLBACK_CONDITION_CATEGORIES: Record<string, string[]> = {
  Metabolic: ['Type 2 Diabetes', 'PCOS', 'Hypothyroidism', 'Prediabetes'],
  'Heart & Blood': ['Hypertension', 'High Cholesterol', 'Heart Disease'],
  Digestive: ['IBS', 'GERD', 'Celiac Disease', 'Food Sensitivities'],
  'Mental Health': ['Anxiety', 'Depression', 'Insomnia', 'ADHD'],
  "Women's Health": ['Perimenopause', 'Endometriosis', 'PMS / PMDD'],
  'Autoimmune & Pain': ['Rheumatoid Arthritis', 'Fibromyalgia', 'Migraine'],
  Other: ['Asthma', 'Sleep Apnea', 'Kidney Disease', 'Cancer Support'],
};

const FALLBACK_GOAL_OPTIONS = [
  { value: 'sleep_optimization', label: 'Sleep better' },
  { value: 'weight_loss', label: 'Lose weight' },
  { value: 'muscle_building', label: 'Build muscle' },
  { value: 'mental_health', label: 'Reduce stress' },
  { value: 'general_wellness', label: 'More energy' },
  { value: 'cardiac_rehab', label: 'Heart health' },
];

// ── HealthKit helper ─────────────────────────────────────────────────────────

async function requestHealthKit(): Promise<boolean> {
  try {
    const HealthKit = (await import('@kingstinct/react-native-healthkit')).default;
    const available = await HealthKit.isHealthDataAvailable();
    if (!available) return false;

    await HealthKit.requestAuthorization({
      toRead: [
        'HKQuantityTypeIdentifierStepCount',
        'HKQuantityTypeIdentifierHeartRate',
        'HKQuantityTypeIdentifierHeartRateVariabilitySDNN',
        'HKQuantityTypeIdentifierActiveEnergyBurned',
        'HKQuantityTypeIdentifierRestingHeartRate',
        'HKCategoryTypeIdentifierSleepAnalysis',
      ] as any[],
    });
    return true;
  } catch {
    return false;
  }
}

// ── Step dots ────────────────────────────────────────────────────────────────

function StepDots({ current, total }: { current: number; total: number }) {
  return (
    <View className="flex-row items-center justify-center gap-2 mb-6">
      {Array.from({ length: total }, (_, i) => (
        <View
          key={i}
          className="h-1.5 rounded-full"
          style={{
            width: i === current ? 24 : 8,
            backgroundColor: i <= current ? '#00D4AA' : 'rgba(255,255,255,0.1)',
          }}
        />
      ))}
    </View>
  );
}

// ── Device row component ─────────────────────────────────────────────────────

function DeviceRow({ icon, color, name, description, connected, connecting, onConnect }: {
  icon: string; color: string; name: string; description: string;
  connected: boolean; connecting: boolean; onConnect: () => void;
}) {
  return (
    <TouchableOpacity
      onPress={onConnect}
      disabled={connected || connecting}
      className="flex-row items-center gap-3 p-4 rounded-xl mb-2"
      style={{
        backgroundColor: connected ? `${color}08` : 'rgba(255,255,255,0.03)',
        borderWidth: 1,
        borderColor: connected ? `${color}30` : 'rgba(255,255,255,0.06)',
      }}
      activeOpacity={0.7}
    >
      <View className="w-10 h-10 rounded-xl items-center justify-center" style={{ backgroundColor: `${color}18` }}>
        <Ionicons name={icon as never} size={20} color={color} />
      </View>
      <View className="flex-1">
        <Text className="text-sm font-sansMedium text-[#E8EDF5]">{name}</Text>
        <Text className="text-xs text-[#526380] mt-0.5">{description}</Text>
      </View>
      {connecting ? (
        <ActivityIndicator size="small" color={color} />
      ) : connected ? (
        <View className="flex-row items-center gap-1">
          <Ionicons name="checkmark-circle" size={16} color="#00D4AA" />
          <Text className="text-xs" style={{ color: '#00D4AA' }}>Connected</Text>
        </View>
      ) : (
        <Text className="text-xs font-sansMedium" style={{ color }}>Connect</Text>
      )}
    </TouchableOpacity>
  );
}

// ── Main ─────────────────────────────────────────────────────────────────────

export default function OnboardingScreen() {
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);

  // Step 0
  const [intent, setIntent] = useState<Intent>('');

  // Step 1
  const [conditionCategories, setConditionCategories] = useState<Record<string, string[]>>({});
  const [goalOptions, setGoalOptions] = useState<Array<{ value: string; label: string }>>([]);

  // Step 2 + 3
  const [specialist, setSpecialist] = useState<SpecialistInfo | null>(null);
  const [journeyProposal, setJourneyProposal] = useState<JourneyProposal | null>(null);
  const [quickQuestions, setQuickQuestions] = useState<QuickQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [connectedDevices, setConnectedDevices] = useState<Set<string>>(new Set());

  const totalSteps = intent === 'exploring' ? 2 : quickQuestions.length > 0 ? 4 : 3;

  // ── Step 0: Intent ─────────────────────────────────────────────────────────

  async function handleIntent(selected: Intent) {
    setIntent(selected);
    setLoading(true);

    // Try API call, but use local fallback data if it fails (e.g. auth token not ready)
    try {
      const { data } = await api.post('/api/v1/onboarding/intent', { intent: selected });
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

      if (selected === 'condition') {
        setConditionCategories(data.categories || FALLBACK_CONDITION_CATEGORIES);
        setStep(1);
      } else if (selected === 'goal') {
        setGoalOptions(data.options || FALLBACK_GOAL_OPTIONS);
        setStep(1);
      } else {
        setSpecialist(data.specialist || { agent_type: 'health_coach', agent_name: 'Health Coach', specialty: 'General Wellness', description: 'Your personal health and wellness guide.' });
        setStep(3);
      }
    } catch {
      // API failed (auth not ready) — use local data, save intent for replay later
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      await AsyncStorage.setItem(ONBOARDING_PENDING_KEY, JSON.stringify({ intent: selected })).catch(() => {});
      if (selected === 'condition') {
        setConditionCategories(FALLBACK_CONDITION_CATEGORIES);
        setStep(1);
      } else if (selected === 'goal') {
        setGoalOptions(FALLBACK_GOAL_OPTIONS);
        setStep(1);
      } else {
        setSpecialist({ agent_type: 'health_coach', agent_name: 'Health Coach', specialty: 'General Wellness', description: 'Your personal health and wellness guide.' });
        setStep(3);
      }
    } finally {
      setLoading(false);
    }
  }

  // ── Step 1: Select ─────────────────────────────────────────────────────────

  async function handleSelect(value: string) {
    setLoading(true);
    try {
      const { data } = await api.post('/api/v1/onboarding/select', {
        type: intent === 'condition' ? 'condition' : 'goal',
        value,
      });
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      setSpecialist(data.specialist || null);
      setJourneyProposal(data.journey_proposal || null);
      setQuickQuestions(data.quick_questions || []);
      // If we have quick questions, show them; otherwise skip to connect+guide
      setStep(data.quick_questions?.length > 0 ? 2 : 3);
    } catch {
      // API failed — save selection locally for replay, use fallback specialist
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      const pending = { intent, type: intent === 'condition' ? 'condition' : 'goal', value };
      await AsyncStorage.setItem(ONBOARDING_PENDING_KEY, JSON.stringify(pending)).catch(() => {});
      setSpecialist({ agent_type: 'health_coach', agent_name: 'Health Coach', specialty: 'General Wellness', description: 'Your personal health and wellness guide. We\'ll start analyzing your data once you connect a device.' });
      setStep(3);
    } finally {
      setLoading(false);
    }
  }

  // ── Step 2: Context ────────────────────────────────────────────────────────

  async function handleContextDone() {
    setLoading(true);
    try {
      if (Object.keys(answers).length > 0) {
        await api.post('/api/v1/onboarding/context', { answers });
      }
    } catch { /* non-fatal */ }
    setLoading(false);
    setStep(3);
  }

  // ── Step 3: Start / Skip ───────────────────────────────────────────────────

  async function replayPendingOnboarding() {
    try {
      const raw = await AsyncStorage.getItem(ONBOARDING_PENDING_KEY);
      if (!raw) return;
      const pending = JSON.parse(raw);

      if (pending.intent) {
        await api.post('/api/v1/onboarding/intent', { intent: pending.intent }).catch(() => {});
      }
      if (pending.type && pending.value) {
        await api.post('/api/v1/onboarding/select', {
          type: pending.type,
          value: pending.value,
        }).catch(() => {});
      }
      if (Object.keys(answers).length > 0) {
        await api.post('/api/v1/onboarding/context', { answers }).catch(() => {});
      }

      await AsyncStorage.removeItem(ONBOARDING_PENDING_KEY);
    } catch { /* non-fatal */ }
  }

  async function handleStartJourney() {
    setLoading(true);
    try {
      await replayPendingOnboarding();
      await api.post('/api/v1/onboarding/start-journey', {
        journey_template_key: journeyProposal?.key,
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch {
      try { await api.post('/api/v1/onboarding/complete', { skipped_journey: false }); } catch {}
    }
    setLoading(false);
    router.replace('/(tabs)/home');
  }

  async function handleSkip() {
    await replayPendingOnboarding();

    try {
      await api.post('/api/v1/onboarding/complete', { skipped_journey: !journeyProposal });
    } catch { /* non-fatal */ }

    if (connectedDevices.size > 0) {
      triggerInitialSync();
    }

    router.replace('/(tabs)/home');
  }

  const [connectingDevice, setConnectingDevice] = useState<string | null>(null);

  async function handleConnectOura() {
    setConnectingDevice('oura');
    try {
      const mobileRedirectUri = 'vitalix://oura-callback';
      const { data } = await api.get('/api/v1/oura/auth-url', {
        params: { redirect_uri: mobileRedirectUri },
      });
      if (data?.sandbox_mode) {
        setConnectedDevices((s) => new Set(s).add('oura'));
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        // Trigger Oura sync in background
        api.post('/api/v1/oura/sync').catch(() => {});
      } else if (data?.auth_url) {
        const { openAuthSessionAsync } = await import('expo-web-browser');
        const result = await openAuthSessionAsync(data.auth_url, mobileRedirectUri);
        if (result.type === 'success' && result.url) {
          const url = new URL(result.url);
          const code = url.searchParams.get('code');
          if (code) {
            await api.post('/api/v1/oura/callback', { code, redirect_uri: mobileRedirectUri });
            setConnectedDevices((s) => new Set(s).add('oura'));
            await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            // Trigger Oura sync in background
            api.post('/api/v1/oura/sync').catch(() => {});
          }
        }
      }
    } catch {
      Alert.alert('Connection Issue', 'Could not connect Oura Ring. You can try again from Profile → Devices.');
    } finally {
      setConnectingDevice(null);
    }
  }

  async function handleConnectAppleHealth() {
    setConnectingDevice('healthkit');
    try {
      const ok = await requestHealthKit();
      if (ok) {
        setConnectedDevices((s) => new Set(s).add('healthkit'));
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

        // Trigger initial sync in the background so Home has data
        triggerInitialSync();
      } else {
        Alert.alert(
          'Apple Health',
          'Apple Health is not available. Please check that Health is enabled in your device settings.',
          [{ text: 'OK' }],
        );
      }
    } catch {
      Alert.alert('Connection Issue', 'Could not connect to Apple Health.');
    } finally {
      setConnectingDevice(null);
    }
  }

  function triggerInitialSync() {
    // Fire-and-forget: use same mock/real sync as Profile → Devices
    (async () => {
      try {
        const { format: fmtDate, subDays } = await import('date-fns');

        if (!Device.isDevice) {
          // Simulator: use same mock data as devices page
          const workoutTypes = ['yoga', 'running', 'cycling', 'strength', 'walking'];
          const points: Array<{ metric_type: string; date: string; value_json: object }> = [];
          for (let i = 6; i >= 0; i--) {
            const date = fmtDate(subDays(new Date(), i), 'yyyy-MM-dd');
            points.push({ metric_type: 'steps', date, value_json: { steps: 6000 + Math.floor(Math.random() * 6000) } });
            points.push({ metric_type: 'resting_heart_rate', date, value_json: { bpm: 58 + Math.floor(Math.random() * 18) } });
            points.push({ metric_type: 'hrv_sdnn', date, value_json: { ms: 38 + Math.round(Math.random() * 24 * 10) / 10 } });
            points.push({ metric_type: 'spo2', date, value_json: { pct: 96 + Math.round(Math.random() * 3 * 10) / 10 } });
            points.push({ metric_type: 'sleep', date, value_json: { hours: 5.5 + Math.round(Math.random() * 3 * 10) / 10 } });
            points.push({ metric_type: 'active_calories', date, value_json: { kcal: 250 + Math.floor(Math.random() * 350) } });
            if (i !== 1 && i !== 4) {
              const type = workoutTypes[Math.floor(Math.random() * workoutTypes.length)];
              const mins = 25 + Math.floor(Math.random() * 45);
              points.push({ metric_type: 'workout', date, value_json: { minutes: mins, sessions: 1, active_calories: Math.round(mins * 4.5), types: [type] } });
            }
          }
          await api.post('/api/v1/health-data/ingest', {
            source: 'healthkit',
            data_points: points,
            sync_timestamp: new Date().toISOString(),
          });
          console.log('[onboarding] Simulator sync: uploaded', points.length, 'data points');
          return;
        }

        // Real device: quick HealthKit sync (steps, HR, HRV, sleep — 14 days)
        const HealthKit = (await import('@kingstinct/react-native-healthkit')).default;
        const now = new Date();
        const anchor = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const start = subDays(now, 14);

        const METRIC_MAP: Record<string, string> = {
          HKQuantityTypeIdentifierStepCount: 'steps',
          HKQuantityTypeIdentifierRestingHeartRate: 'resting_heart_rate',
          HKQuantityTypeIdentifierHeartRateVariabilitySDNN: 'hrv_sdnn',
          HKQuantityTypeIdentifierActiveEnergyBurned: 'active_calories',
        };

        const dataPoints: Array<{ metric_type: string; date: string; value_json: object }> = [];
        for (const [identifier, metricName] of Object.entries(METRIC_MAP)) {
          try {
            const results = await HealthKit.queryStatisticsCollectionForQuantity(
              identifier as any,
              ['cumulativeSum', 'discreteAverage'],
              anchor,
              { day: 1 },
              { from: start, to: now } as any,
            );
            for (const bucket of results) {
              if (!bucket.startDate) continue;
              const day = fmtDate(bucket.startDate, 'yyyy-MM-dd');
              const val = (bucket as any).sumQuantity?.quantity ?? (bucket as any).averageQuantity?.quantity;
              if (val != null) {
                dataPoints.push({ metric_type: metricName, date: day, value_json: { value: val } });
              }
            }
          } catch { /* skip */ }
        }

        if (dataPoints.length > 0) {
          await api.post('/api/v1/health-data/ingest', {
            source: 'apple_health',
            data_points: dataPoints,
            sync_timestamp: now.toISOString(),
          });
          console.log('[onboarding] HealthKit sync: uploaded', dataPoints.length, 'data points');
        }
      } catch (err) {
        console.warn('[onboarding] Initial sync failed (non-fatal):', err);
      }
    })();
  }

  async function handleConnectHealthConnect() {
    setConnectingDevice('health_connect');
    // Health Connect integration placeholder — show guidance
    Alert.alert(
      'Health Connect',
      'Health Connect integration coming soon. You can connect from Profile → Devices.',
      [{ text: 'OK' }],
    );
    setConnectingDevice(null);
  }

  // ── Provider / Caregiver ───────────────────────────────────────────────────

  async function handleProviderComplete() {
    try { await api.patch('/api/v1/profile/role', { user_role: 'provider' }); } catch {}
    router.replace('/(tabs)/home');
  }

  async function handleCaregiverComplete() {
    try { await api.patch('/api/v1/profile/role', { user_role: 'caregiver' }); } catch {}
    router.replace('/(tabs)/home');
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <ScrollView
      className="flex-1 bg-obsidian-900"
      contentContainerStyle={{ padding: 24, paddingTop: 60, paddingBottom: 40 }}
      keyboardShouldPersistTaps="handled"
    >
      <StepDots current={step} total={totalSteps} />

      {loading && <ActivityIndicator color="#00D4AA" className="mb-4" />}

      {/* ── Step 0: What brings you here? ────────────────────────── */}
      {step === 0 && (
        <View>
          <Text className="text-2xl font-display text-[#E8EDF5] text-center mb-2">What brings you to Vitalix?</Text>
          <Text className="text-sm text-[#526380] text-center mb-6">This shapes your entire experience</Text>

          <TouchableOpacity
            onPress={() => handleIntent('condition')}
            className="flex-row items-center gap-3 p-4 rounded-xl mb-3"
            style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}
            activeOpacity={0.7}
          >
            <View className="w-11 h-11 rounded-xl items-center justify-center" style={{ backgroundColor: 'rgba(248,113,113,0.1)' }}>
              <Ionicons name="heart-outline" size={20} color="#F87171" />
            </View>
            <View className="flex-1">
              <Text className="text-sm font-sansMedium text-[#E8EDF5]">Managing a health condition</Text>
              <Text className="text-xs text-[#526380] mt-0.5">PCOS, diabetes, thyroid, IBS, etc.</Text>
            </View>
            <Ionicons name="chevron-forward" size={16} color="#3D4F66" />
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => handleIntent('goal')}
            className="flex-row items-center gap-3 p-4 rounded-xl mb-3"
            style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}
            activeOpacity={0.7}
          >
            <View className="w-11 h-11 rounded-xl items-center justify-center" style={{ backgroundColor: 'rgba(0,212,170,0.1)' }}>
              <Ionicons name="flag-outline" size={20} color="#00D4AA" />
            </View>
            <View className="flex-1">
              <Text className="text-sm font-sansMedium text-[#E8EDF5]">Improve my health</Text>
              <Text className="text-xs text-[#526380] mt-0.5">Sleep, weight, fitness, stress, energy</Text>
            </View>
            <Ionicons name="chevron-forward" size={16} color="#3D4F66" />
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => handleIntent('exploring')}
            className="flex-row items-center gap-3 p-4 rounded-xl mb-3"
            style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}
            activeOpacity={0.7}
          >
            <View className="w-11 h-11 rounded-xl items-center justify-center" style={{ backgroundColor: 'rgba(96,165,250,0.1)' }}>
              <Ionicons name="search-outline" size={20} color="#60A5FA" />
            </View>
            <View className="flex-1">
              <Text className="text-sm font-sansMedium text-[#E8EDF5]">Just exploring</Text>
              <Text className="text-xs text-[#526380] mt-0.5">See what my health data can tell me</Text>
            </View>
            <Ionicons name="chevron-forward" size={16} color="#3D4F66" />
          </TouchableOpacity>

          <TouchableOpacity onPress={() => setStep(-1)} className="mt-4 self-center">
            <Text className="text-xs text-[#526380]">Healthcare provider or caregiver? →</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* ── Step -1: Provider / Caregiver ────────────────────────── */}
      {step === -1 && (
        <View>
          <Text className="text-xl font-display text-[#E8EDF5] text-center mb-6">Professional access</Text>
          <TouchableOpacity onPress={handleProviderComplete} className="flex-row items-center gap-3 p-4 rounded-xl mb-3"
            style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }} activeOpacity={0.7}>
            <Ionicons name="medical-outline" size={20} color="#818CF8" />
            <View className="flex-1">
              <Text className="text-sm font-sansMedium text-[#E8EDF5]">Healthcare Provider</Text>
              <Text className="text-xs text-[#526380]">Monitor patients, review care plans</Text>
            </View>
          </TouchableOpacity>
          <TouchableOpacity onPress={handleCaregiverComplete} className="flex-row items-center gap-3 p-4 rounded-xl mb-3"
            style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }} activeOpacity={0.7}>
            <Ionicons name="people-outline" size={20} color="#6EE7B7" />
            <View className="flex-1">
              <Text className="text-sm font-sansMedium text-[#E8EDF5]">Caregiver / Family</Text>
              <Text className="text-xs text-[#526380]">Support a family member's health</Text>
            </View>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => setStep(0)} className="mt-4 self-center">
            <Text className="text-xs text-[#526380]">← Back</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* ── Step 1: Condition picker ──────────────────────────────── */}
      {step === 1 && intent === 'condition' && (
        <View>
          <Text className="text-xl font-display text-[#E8EDF5] text-center mb-1">Primary condition?</Text>
          <Text className="text-xs text-[#526380] text-center mb-5">You can add more later</Text>

          {Object.entries(conditionCategories).map(([cat, conditions]) => (
            <View key={cat} className="mb-4">
              <Text className="text-[9px] font-bold uppercase tracking-wider text-[#526380] mb-2">{cat}</Text>
              <View className="flex-row flex-wrap gap-2">
                {conditions.map((c) => (
                  <TouchableOpacity key={c} onPress={() => handleSelect(c)} disabled={loading}
                    className="px-3 py-2 rounded-lg" activeOpacity={0.7}
                    style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}>
                    <Text className="text-xs text-[#E8EDF5]">{c}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          ))}

          <TouchableOpacity onPress={() => setStep(0)} className="mt-2 self-center">
            <Text className="text-xs text-[#526380]">← Back</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* ── Step 1: Goal picker ───────────────────────────────────── */}
      {step === 1 && intent === 'goal' && (
        <View>
          <Text className="text-xl font-display text-[#E8EDF5] text-center mb-1">Your #1 health goal?</Text>
          <Text className="text-xs text-[#526380] text-center mb-5">Pick the one that matters most</Text>

          <View className="flex-row flex-wrap gap-3 justify-center">
            {goalOptions.map((g) => {
              const iconName = GOAL_ICONS[g.value] || 'flag-outline';
              return (
                <TouchableOpacity key={g.value} onPress={() => handleSelect(g.value)} disabled={loading}
                  className="items-center p-4 rounded-xl" activeOpacity={0.7}
                  style={{ width: '45%', backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}>
                  <Ionicons name={iconName as never} size={24} color="#00D4AA" />
                  <Text className="text-sm font-sansMedium text-[#E8EDF5] mt-2 text-center">{g.label}</Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <TouchableOpacity onPress={() => setStep(0)} className="mt-4 self-center">
            <Text className="text-xs text-[#526380]">← Back</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* ── Step 2: Quick context ─────────────────────────────────── */}
      {step === 2 && (
        <View>
          <Text className="text-xl font-display text-[#E8EDF5] text-center mb-1">Quick questions</Text>
          <Text className="text-xs text-[#526380] text-center mb-5">Helps personalize your plan</Text>

          {quickQuestions.map((q) => (
            <View key={q.id} className="rounded-xl p-4 mb-3"
              style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}>
              <Text className="text-sm font-sansMedium text-[#E8EDF5] mb-3">{q.question}</Text>

              {(q.input_type === 'choice' || q.input_type === 'choice_then_text') && q.options && (
                <View className="flex-row flex-wrap gap-2">
                  {q.options.map((opt) => {
                    const sel = answers[q.data_field] === opt;
                    return (
                      <TouchableOpacity key={opt}
                        onPress={() => { setAnswers({ ...answers, [q.data_field]: opt }); Haptics.selectionAsync(); }}
                        className="px-3 py-1.5 rounded-lg"
                        style={{
                          backgroundColor: sel ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.03)',
                          borderWidth: 1, borderColor: sel ? 'rgba(0,212,170,0.3)' : 'rgba(255,255,255,0.06)',
                        }}>
                        <Text className="text-xs" style={{ color: sel ? '#00D4AA' : '#8B97A8' }}>{opt}</Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              )}

              {q.input_type === 'multi_choice' && q.options && (
                <View className="flex-row flex-wrap gap-2">
                  {q.options.map((opt) => {
                    const arr = (answers[q.data_field] as string[]) || [];
                    const sel = arr.includes(opt);
                    return (
                      <TouchableOpacity key={opt}
                        onPress={() => {
                          const updated = sel ? arr.filter((x) => x !== opt) : [...arr, opt];
                          setAnswers({ ...answers, [q.data_field]: updated });
                          Haptics.selectionAsync();
                        }}
                        className="px-3 py-1.5 rounded-lg"
                        style={{
                          backgroundColor: sel ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.03)',
                          borderWidth: 1, borderColor: sel ? 'rgba(0,212,170,0.3)' : 'rgba(255,255,255,0.06)',
                        }}>
                        <Text className="text-xs" style={{ color: sel ? '#00D4AA' : '#8B97A8' }}>{opt}</Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              )}

              {(q.input_type === 'text' || (q.input_type === 'choice_then_text' && answers[q.data_field] === q.options?.[0])) && (
                <TextInput
                  placeholder={q.text_prompt || 'Type here...'}
                  placeholderTextColor="#3D4F66"
                  value={(answers[`${q.data_field}_text`] as string) || ''}
                  onChangeText={(t) => setAnswers({ ...answers, [`${q.data_field}_text`]: t })}
                  className="mt-2 px-3 py-2 rounded-lg text-sm text-[#E8EDF5]"
                  style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}
                />
              )}
            </View>
          ))}

          <View className="flex-row gap-3 mt-4">
            <TouchableOpacity onPress={handleContextDone} disabled={loading}
              className="flex-1 py-3 rounded-xl items-center" style={{ backgroundColor: '#00D4AA' }} activeOpacity={0.85}>
              <Text className="text-sm font-sansMedium" style={{ color: '#080B10' }}>
                {loading ? 'Saving...' : 'Continue'}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setStep(3)} className="px-4 py-3 items-center justify-center">
              <Text className="text-xs text-[#526380]">Skip</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* ── Step 3: Connect + Meet Guide ──────────────────────────── */}
      {step === 3 && (
        <View>
          <Text className="text-lg font-display text-[#E8EDF5] text-center mb-2">Connect your data</Text>
          <Text className="text-xs text-[#526380] text-center mb-4">
            {specialist ? `Your ${specialist.agent_name} needs health data to get started` : 'Connect a device to start tracking'}
          </Text>

          {/* Apple Health (iOS) / Health Connect (Android) — shown first as default */}
          {Platform.OS === 'ios' ? (
            <DeviceRow
              icon="fitness-outline"
              color="#F87171"
              name="Apple Health"
              description="Steps, sleep, heart rate, workouts"
              connected={connectedDevices.has('healthkit')}
              connecting={connectingDevice === 'healthkit'}
              onConnect={handleConnectAppleHealth}
            />
          ) : (
            <DeviceRow
              icon="fitness-outline"
              color="#34D399"
              name="Health Connect"
              description="Steps, sleep, heart rate, workouts"
              connected={connectedDevices.has('health_connect')}
              connecting={connectingDevice === 'health_connect'}
              onConnect={handleConnectHealthConnect}
            />
          )}

          {/* Oura Ring */}
          <DeviceRow
            icon="ellipse-outline"
            color="#818CF8"
            name="Oura Ring"
            description="Sleep score, readiness, HRV, temperature"
            connected={connectedDevices.has('oura')}
            connecting={connectingDevice === 'oura'}
            onConnect={handleConnectOura}
          />

          {/* Skip note */}
          {connectedDevices.size === 0 && (
            <Text className="text-[10px] text-[#3D4F66] text-center mt-1 mb-3">
              You can connect more devices from Profile → Devices later
            </Text>
          )}

          {/* Specialist + Journey */}
          {specialist && (
            <View className="rounded-xl p-4 mt-3" style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}>
              <View className="flex-row items-center gap-3 mb-3">
                <View className="w-10 h-10 rounded-xl items-center justify-center" style={{ backgroundColor: 'rgba(0,212,170,0.1)' }}>
                  <Ionicons name="medkit-outline" size={20} color="#00D4AA" />
                </View>
                <View>
                  <Text className="text-sm font-sansMedium" style={{ color: '#00D4AA' }}>Your {specialist.agent_name}</Text>
                  <Text className="text-xs text-[#526380]">{specialist.specialty}</Text>
                </View>
              </View>

              <Text className="text-xs text-[#8B97A8] leading-5 mb-3">{specialist.description}</Text>

              {journeyProposal && (
                <View className="rounded-lg p-3 mb-3" style={{ backgroundColor: 'rgba(96,165,250,0.04)', borderWidth: 1, borderColor: 'rgba(96,165,250,0.12)' }}>
                  <Text className="text-xs font-sansMedium mb-2" style={{ color: '#60A5FA' }}>{journeyProposal.title}</Text>
                  {journeyProposal.phases.map((phase, i) => (
                    <View key={i} className="flex-row items-center gap-2 mb-1.5">
                      <View className="w-5 h-5 rounded-full items-center justify-center" style={{ backgroundColor: 'rgba(96,165,250,0.1)' }}>
                        <Text className="text-[8px] font-bold" style={{ color: '#60A5FA' }}>{i + 1}</Text>
                      </View>
                      <View className="flex-1">
                        <Text className="text-xs text-[#E8EDF5]">{phase.name}</Text>
                      </View>
                    </View>
                  ))}
                </View>
              )}

              <View className="flex-row gap-3">
                {journeyProposal && (
                  <TouchableOpacity onPress={handleStartJourney} disabled={loading}
                    className="flex-1 py-3 rounded-xl items-center" style={{ backgroundColor: '#00D4AA', opacity: loading ? 0.6 : 1 }} activeOpacity={0.85}>
                    <Text className="text-sm font-sansMedium" style={{ color: '#080B10' }}>
                      {loading ? 'Starting...' : 'Start My Journey'}
                    </Text>
                  </TouchableOpacity>
                )}
                <TouchableOpacity onPress={handleSkip} className="px-4 py-3 items-center justify-center">
                  <Text className="text-xs text-[#526380]">{journeyProposal ? 'Maybe Later' : 'Continue'}</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {!specialist && (
            <TouchableOpacity onPress={handleSkip}
              className="py-3 rounded-xl items-center mt-4" style={{ backgroundColor: '#00D4AA' }} activeOpacity={0.85}>
              <Text className="text-sm font-sansMedium" style={{ color: '#080B10' }}>Get Started</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
    </ScrollView>
  );
}
