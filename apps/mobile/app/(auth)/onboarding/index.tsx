import { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, ScrollView,
  ActivityIndicator, Platform,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import Constants from 'expo-constants';
import * as Device from 'expo-device';
import { api } from '@/services/api';

// ─── Types ─────────────────────────────────────────────────────────────────────

type UserRole = 'patient' | 'provider' | 'caregiver';
type HKStatus = 'idle' | 'connecting' | 'connected' | 'skipped';

// ─── Constants ─────────────────────────────────────────────────────────────────

const TOTAL_STEPS = 5;

const VALUE_PROPS = [
  { icon: 'heart-outline' as const,            color: '#F87171', title: 'Track everything in one place',  body: 'Symptoms, meds, nutrition, labs and wearable data — all connected.' },
  { icon: 'bulb-outline' as const,             color: '#00D4AA', title: 'AI that explains your patterns', body: "Spot what's affecting your sleep, energy and pain before your next appointment." },
  { icon: 'document-text-outline' as const,    color: '#818CF8', title: 'Walk in prepared',               body: 'Auto-generate a doctor-ready summary of your recent health history.' },
  { icon: 'shield-checkmark-outline' as const, color: '#6EE7B7', title: 'Private by design',              body: 'Your data is encrypted, never sold, and yours to export any time.' },
];

const ROLES: Array<{ key: UserRole; label: string; description: string; icon: React.ComponentProps<typeof Ionicons>['name'] }> = [
  { key: 'patient',   label: 'Patient',   description: 'Track my own health',          icon: 'person-outline' },
  { key: 'provider',  label: 'Provider',  description: 'Manage patients & care plans', icon: 'medical-outline' },
  { key: 'caregiver', label: 'Caregiver', description: 'Support a family member',      icon: 'people-outline' },
];

const COMMON_CONDITIONS = [
  'Type 2 Diabetes', 'Type 1 Diabetes', 'Hypertension', 'High Cholesterol',
  'Hypothyroidism', 'Asthma', 'COPD', 'Heart Disease', 'Atrial Fibrillation',
  'Rheumatoid Arthritis', 'Lupus', "Crohn's Disease", 'IBS', 'Celiac Disease',
  'GERD', 'Depression', 'Anxiety', 'ADHD', 'Sleep Apnea', 'Insomnia',
  'PCOS', 'Fibromyalgia', 'Chronic Fatigue', 'Migraines', 'Osteoarthritis',
  'Osteoporosis', 'Anemia', 'Kidney Disease', 'Multiple Sclerosis', 'Psoriasis',
];

const GOAL_OPTIONS = [
  'Improve sleep quality', 'Manage chronic condition', 'Lose weight', 'Reduce stress',
  'Improve fitness', 'Track medications', 'Understand lab results', 'Prepare for doctor visits',
];

// ─── HealthKit helper ──────────────────────────────────────────────────────────

async function requestHealthKitPermission(): Promise<'granted' | 'simulator' | 'error'> {
  if (Constants.executionEnvironment === 'storeClient') return 'error';
  if (!Device.isDevice) return 'simulator';
  try {
    const { requireNativeModule } = await import('expo-modules-core');
    const HK = requireNativeModule('VitalixHealthKit');
    await HK.requestAuthorization();
    return 'granted';
  } catch {
    return 'error';
  }
}

// ─── Onboarding submit ────────────────────────────────────────────────────────

interface OnboardingData {
  role: UserRole;
  weightKg: string;
  heightCm: string;
  selectedConditions: string[];
  noneConditions: boolean;
  selectedGoals: string[];
}

async function submitOnboarding(data: OnboardingData): Promise<void> {
  await api.patch('/api/v1/profile/role', { user_role: data.role }).catch(() => {});

  const conditions = data.noneConditions ? [] : data.selectedConditions;
  await api.patch('/api/v1/profile/checkin', {
    weight_kg: data.weightKg ? Number.parseFloat(data.weightKg) : undefined,
    height_cm: data.heightCm ? Number.parseFloat(data.heightCm) : undefined,
    new_conditions: conditions.length > 0 ? conditions : undefined,
  }).catch(() => {});

  if (data.selectedGoals.length > 0) {
    await api.post('/api/v1/health-questionnaire', {
      answers: { health_goals: data.selectedGoals },
    }).catch(() => {});
  }

  await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
}

// ─── Shared chip ──────────────────────────────────────────────────────────────

function Chip({ label, selected, onPress }: Readonly<{ label: string; selected: boolean; onPress: () => void }>) {
  return (
    <TouchableOpacity
      onPress={onPress}
      className={`px-3 py-2 rounded-full border mr-2 mb-2 ${selected ? 'bg-primary-500/20 border-primary-500' : 'bg-surface-raised border-surface-border'}`}
    >
      <Text className={selected ? 'text-primary-500 text-sm' : 'text-[#E8EDF5] text-sm'}>{label}</Text>
    </TouchableOpacity>
  );
}

// ─── Step components ──────────────────────────────────────────────────────────

function StepValueProp() {
  return (
    <View className="pt-16">
      <View className="items-center mb-10">
        <View className="w-20 h-20 rounded-3xl bg-primary-500/20 border border-primary-500/30 items-center justify-center mb-5">
          <Ionicons name="pulse" size={36} color="#00D4AA" />
        </View>
        <Text className="text-3xl font-display text-[#E8EDF5] text-center mb-2">Welcome to Vitalix</Text>
        <Text className="text-[#526380] text-center text-base leading-6">Your personal health intelligence platform</Text>
      </View>
      <View className="gap-4">
        {VALUE_PROPS.map((vp) => (
          <View key={vp.title} className="flex-row items-start gap-4 bg-surface-raised border border-surface-border rounded-2xl p-4">
            <View className="w-10 h-10 rounded-xl items-center justify-center mt-0.5" style={{ backgroundColor: `${vp.color}18` }}>
              <Ionicons name={vp.icon} size={20} color={vp.color} />
            </View>
            <View className="flex-1">
              <Text className="text-[#E8EDF5] font-sansMedium mb-1">{vp.title}</Text>
              <Text className="text-[#526380] text-sm leading-5">{vp.body}</Text>
            </View>
          </View>
        ))}
      </View>
    </View>
  );
}

function StepRole({ role, setRole }: Readonly<{ role: UserRole; setRole: (r: UserRole) => void }>) {
  return (
    <View>
      <Text className="text-2xl font-display text-[#E8EDF5] mb-2">How will you use Vitalix?</Text>
      <Text className="text-[#526380] mb-8">This helps us personalise your experience</Text>
      <View className="gap-3">
        {ROLES.map((r) => {
          const selected = role === r.key;
          return (
            <TouchableOpacity
              key={r.key}
              onPress={() => setRole(r.key)}
              className="flex-row items-center p-4 rounded-2xl border"
              style={{ backgroundColor: selected ? 'rgba(0,212,170,0.08)' : 'rgba(255,255,255,0.03)', borderColor: selected ? '#00D4AA' : '#1E2A3B' }}
              activeOpacity={0.7}
            >
              <View className="w-12 h-12 rounded-2xl items-center justify-center mr-4" style={{ backgroundColor: selected ? 'rgba(0,212,170,0.15)' : 'rgba(255,255,255,0.05)' }}>
                <Ionicons name={r.icon} size={22} color={selected ? '#00D4AA' : '#526380'} />
              </View>
              <View className="flex-1">
                <Text className="font-sansMedium text-base" style={{ color: selected ? '#E8EDF5' : '#8A9BB0' }}>{r.label}</Text>
                <Text className="text-sm mt-0.5" style={{ color: selected ? '#526380' : '#3A4A5C' }}>{r.description}</Text>
              </View>
              {selected ? <Ionicons name="checkmark-circle" size={20} color="#00D4AA" /> : null}
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

function StepPersonalDetails({ weightKg, setWeightKg, heightCm, setHeightCm }: Readonly<{
  weightKg: string; setWeightKg: (v: string) => void;
  heightCm: string; setHeightCm: (v: string) => void;
}>) {
  return (
    <View>
      <Text className="text-2xl font-display text-[#E8EDF5] mb-2">Personal Details</Text>
      <Text className="text-[#526380] mb-8">Help us personalise your health insights</Text>
      <View className="gap-4">
        <View>
          <Text className="text-sm text-[#526380] mb-2">Weight (kg) — optional</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] text-base"
            value={weightKg} onChangeText={setWeightKg}
            keyboardType="decimal-pad" placeholderTextColor="#526380" placeholder="70"
          />
        </View>
        <View>
          <Text className="text-sm text-[#526380] mb-2">Height (cm) — optional</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] text-base"
            value={heightCm} onChangeText={setHeightCm}
            keyboardType="decimal-pad" placeholderTextColor="#526380" placeholder="170"
          />
        </View>
      </View>
    </View>
  );
}

function StepConditions({ selectedConditions, noneConditions, onToggle, onToggleNone }: Readonly<{
  selectedConditions: string[];
  noneConditions: boolean;
  onToggle: (c: string) => void;
  onToggleNone: () => void;
}>) {
  return (
    <View>
      <Text className="text-2xl font-display text-[#E8EDF5] mb-2">Health Conditions</Text>
      <Text className="text-[#526380] mb-6">Select any conditions you manage — we'll tailor your tracking</Text>
      <View className="flex-row flex-wrap mb-4">
        {COMMON_CONDITIONS.map((c) => (
          <Chip key={c} label={c} selected={!noneConditions && selectedConditions.includes(c)} onPress={() => onToggle(c)} />
        ))}
      </View>
      <TouchableOpacity
        onPress={onToggleNone}
        className="flex-row items-center gap-3 p-4 rounded-2xl border mb-2"
        style={{ backgroundColor: noneConditions ? 'rgba(0,212,170,0.08)' : 'rgba(255,255,255,0.03)', borderColor: noneConditions ? '#00D4AA' : '#1E2A3B' }}
      >
        <Ionicons name={noneConditions ? 'checkmark-circle' : 'ellipse-outline'} size={20} color={noneConditions ? '#00D4AA' : '#526380'} />
        <Text className="text-[#E8EDF5] font-sansMedium">None currently</Text>
      </TouchableOpacity>
    </View>
  );
}

function HealthKitCard({ hkStatus, onConnect }: Readonly<{ hkStatus: HKStatus; onConnect: () => void }>) {
  const connected = hkStatus === 'connected';
  const bgColor = connected ? 'rgba(0,212,170,0.08)' : 'rgba(255,255,255,0.03)';
  const borderColor = connected ? '#00D4AA' : '#1E2A3B';
  const iconBg = connected ? 'rgba(0,212,170,0.15)' : 'rgba(255,255,255,0.05)';
  const subtitle = connected ? 'Connected — steps, sleep, heart rate & more' : 'Sync steps, sleep, heart rate & HRV';

  return (
    <>
      <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3">Connect Health Data</Text>
      <TouchableOpacity
        onPress={connected ? undefined : onConnect}
        className="flex-row items-center p-4 rounded-2xl border mb-2"
        style={{ backgroundColor: bgColor, borderColor }}
        activeOpacity={connected ? 1 : 0.7}
      >
        <View className="w-12 h-12 rounded-2xl items-center justify-center mr-4" style={{ backgroundColor: iconBg }}>
          {hkStatus === 'connecting'
            ? <ActivityIndicator size="small" color="#00D4AA" />
            : <Ionicons name={connected ? 'heart' : 'heart-outline'} size={22} color={connected ? '#00D4AA' : '#526380'} />}
        </View>
        <View className="flex-1">
          <Text className="font-sansMedium text-[#E8EDF5]">Apple Health</Text>
          <Text className="text-sm mt-0.5 text-[#526380]">{subtitle}</Text>
        </View>
        {connected
          ? <Ionicons name="checkmark-circle" size={20} color="#00D4AA" />
          : <Text className="text-primary-500 font-sansMedium text-sm">Connect</Text>}
      </TouchableOpacity>
      <Text className="text-[#3A4A5C] text-xs mt-1 mb-4">
        Read-only · Revocable anytime in iOS Settings · You can also connect later in Profile → Devices
      </Text>
    </>
  );
}

function StepGoalsAndHealth({ selectedGoals, onToggleGoal, hkStatus, onConnectHK }: Readonly<{
  selectedGoals: string[];
  onToggleGoal: (g: string) => void;
  hkStatus: HKStatus;
  onConnectHK: () => void;
}>) {
  return (
    <View>
      <Text className="text-2xl font-display text-[#E8EDF5] mb-2">Your Goals</Text>
      <Text className="text-[#526380] mb-6">Select all that apply</Text>
      <View className="flex-row flex-wrap mb-8">
        {GOAL_OPTIONS.map((goal) => (
          <Chip key={goal} label={goal} selected={selectedGoals.includes(goal)} onPress={() => onToggleGoal(goal)} />
        ))}
      </View>
      {Platform.OS === 'ios' ? <HealthKitCard hkStatus={hkStatus} onConnect={onConnectHK} /> : null}
    </View>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

export default function OnboardingScreen() {
  const [step, setStep]                           = useState(0);
  const [role, setRole]                           = useState<UserRole>('patient');
  const [weightKg, setWeightKg]                   = useState('');
  const [heightCm, setHeightCm]                   = useState('');
  const [selectedConditions, setSelectedConditions] = useState<string[]>([]);
  const [noneConditions, setNoneConditions]       = useState(false);
  const [selectedGoals, setSelectedGoals]         = useState<string[]>([]);
  const [hkStatus, setHkStatus]                   = useState<HKStatus>('idle');
  const [loading, setLoading]                     = useState(false);

  function toggleCondition(c: string) {
    setNoneConditions(false);
    setSelectedConditions((prev) => prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]);
  }

  function toggleNoneConditions() {
    setNoneConditions((v) => !v);
    setSelectedConditions([]);
  }

  function toggleGoal(g: string) {
    setSelectedGoals((prev) => prev.includes(g) ? prev.filter((x) => x !== g) : [...prev, g]);
  }

  async function handleConnectHealthKit() {
    if (Platform.OS !== 'ios') { setHkStatus('skipped'); return; }
    setHkStatus('connecting');
    const result = await requestHealthKitPermission();
    setHkStatus(result === 'granted' || result === 'simulator' ? 'connected' : 'skipped');
  }

  async function handleFinish() {
    setLoading(true);
    try {
      await submitOnboarding({ role, weightKg, heightCm, selectedConditions, noneConditions, selectedGoals });
    } catch { /* non-blocking */ } finally {
      setLoading(false);
      router.replace('/(tabs)/home');
    }
  }

  function goNext() { setStep((s) => Math.min(s + 1, TOTAL_STEPS - 1)); }
  function goBack() {
    if (step > 0) setStep((s) => s - 1);
    else router.replace('/(tabs)/home');
  }

  const stepContent = [
    <StepValueProp key="value-prop" />,
    <StepRole key="role" role={role} setRole={setRole} />,
    <StepPersonalDetails key="personal" weightKg={weightKg} setWeightKg={setWeightKg} heightCm={heightCm} setHeightCm={setHeightCm} />,
    <StepConditions key="conditions" selectedConditions={selectedConditions} noneConditions={noneConditions} onToggle={toggleCondition} onToggleNone={toggleNoneConditions} />,
    <StepGoalsAndHealth key="goals" selectedGoals={selectedGoals} onToggleGoal={toggleGoal} hkStatus={hkStatus} onConnectHK={handleConnectHealthKit} />,
  ];

  const isLastStep = step === TOTAL_STEPS - 1;

  return (
    <View className="flex-1 bg-obsidian-900">
      {step > 0 ? (
        <View className="flex-row gap-2 px-6 pt-16 pb-6">
          {Array.from({ length: TOTAL_STEPS - 1 }, (_, i) => (
            <View key={i} className={`h-1 flex-1 rounded-full ${i < step ? 'bg-primary-500' : 'bg-surface-border'}`} />
          ))}
        </View>
      ) : null}

      <ScrollView className="flex-1 px-6" keyboardShouldPersistTaps="handled">
        {stepContent[step]}
        <View style={{ height: 24 }} />
      </ScrollView>

      <View className="px-6 pb-10 pt-4 gap-3">
        {isLastStep ? (
          <TouchableOpacity onPress={handleFinish} disabled={loading} className="bg-primary-500 rounded-xl py-4 items-center" activeOpacity={0.8}>
            {loading ? <ActivityIndicator color="#080B10" /> : <Text className="text-obsidian-900 font-sansMedium text-base">Finish Setup</Text>}
          </TouchableOpacity>
        ) : (
          <TouchableOpacity onPress={goNext} className="bg-primary-500 rounded-xl py-4 items-center" activeOpacity={0.8}>
            <Text className="text-obsidian-900 font-sansMedium text-base">{step === 0 ? 'Get Started' : 'Continue'}</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity onPress={goBack} className="items-center py-2">
          <Text className="text-[#526380] text-sm">{step > 0 ? 'Back' : 'Skip for now'}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
