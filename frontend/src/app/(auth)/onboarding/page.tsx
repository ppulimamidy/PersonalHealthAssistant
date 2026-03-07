'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { ouraService } from '@/services/oura';
import { useAuthStore } from '@/stores/authStore';
import {
  CheckCircle,
  Circle,
  ArrowRight,
  Dumbbell,
  Moon,
  Leaf,
  Heart,
  Brain,
  Zap,
  Pill,
  BarChart2,
  Activity,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { supabase } from '@/lib/supabase';

// ── Goal options ─────────────────────────────────────────────────────────────

const GOAL_OPTIONS = [
  { value: 'improve_sleep', label: 'Improve Sleep', icon: Moon },
  { value: 'lose_weight', label: 'Lose Weight', icon: Leaf },
  { value: 'build_muscle', label: 'Build Muscle', icon: Dumbbell },
  { value: 'manage_stress', label: 'Manage Stress', icon: Brain },
  { value: 'improve_energy', label: 'Boost Energy', icon: Zap },
  { value: 'heart_health', label: 'Heart Health', icon: Heart },
  { value: 'manage_condition', label: 'Manage a Condition', icon: Pill },
  { value: 'track_metrics', label: 'Track Metrics', icon: BarChart2 },
];

// ── Condition options ─────────────────────────────────────────────────────────

const COMMON_CONDITIONS = [
  'Type 2 Diabetes', 'Prediabetes', 'Hypertension', 'High Cholesterol',
  'Hypothyroidism', 'Hyperthyroidism', 'Asthma', 'COPD',
  'IBS / IBD', 'GERD / Acid Reflux', 'PCOS', 'Endometriosis',
  'Anxiety', 'Depression', 'ADHD', 'Insomnia',
  'Osteoporosis', 'Arthritis', 'Fibromyalgia', 'Chronic Fatigue',
  'Anemia', 'Celiac Disease', 'Food Allergies', 'Lupus',
  'Psoriasis', 'Eczema', 'Migraine', 'Sleep Apnea',
];

const CONDITION_CATEGORY_MAP: Record<string, string> = {
  'Type 2 Diabetes': 'metabolic', 'Prediabetes': 'metabolic',
  'Hypertension': 'cardiovascular', 'High Cholesterol': 'cardiovascular',
  'Hypothyroidism': 'metabolic', 'Hyperthyroidism': 'metabolic',
  'Asthma': 'other', 'COPD': 'other',
  'IBS / IBD': 'digestive', 'GERD / Acid Reflux': 'digestive',
  'PCOS': 'metabolic', 'Endometriosis': 'other',
  'Anxiety': 'mental_health', 'Depression': 'mental_health',
  'ADHD': 'mental_health', 'Insomnia': 'other',
  'Osteoporosis': 'other', 'Arthritis': 'other',
  'Fibromyalgia': 'other', 'Chronic Fatigue': 'other',
  'Anemia': 'other', 'Celiac Disease': 'digestive',
  'Food Allergies': 'digestive', 'Lupus': 'autoimmune',
  'Psoriasis': 'autoimmune', 'Eczema': 'autoimmune',
  'Migraine': 'other', 'Sleep Apnea': 'other',
};

// ── Step indicator ────────────────────────────────────────────────────────────

function StepIndicator({ step }: Readonly<{ step: number }>) {
  const steps = [
    { label: 'Account', num: 0 },
    { label: 'Goals', num: 1 },
    { label: 'Conditions', num: 2 },
    { label: 'Device', num: 3 },
  ];
  return (
    <div className="flex items-center justify-center gap-3 mb-8">
      {steps.map((s, i) => {
        let icon;
        if (s.num < step || s.num === 0) {
          icon = <CheckCircle className="w-5 h-5 text-primary-600 dark:text-primary-400" />;
        } else if (s.num === step) {
          icon = (
            <div className="w-5 h-5 rounded-full border-2 border-primary-600 dark:border-primary-400 flex items-center justify-center">
              <span className="text-xs font-bold text-primary-600 dark:text-primary-400">{s.num}</span>
            </div>
          );
        } else {
          icon = <Circle className="w-5 h-5 text-slate-300 dark:text-slate-600" />;
        }
        return (
        <div key={s.num} className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            {icon}
            <span className={`text-xs font-medium ${s.num <= step ? 'text-slate-900 dark:text-slate-100' : 'text-slate-400 dark:text-slate-500'}`}>
              {s.label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div className="w-8 h-0.5 bg-slate-200 dark:bg-slate-700" />
          )}
        </div>
        );
      })}
    </div>
  );
}

// ── Oura logo ─────────────────────────────────────────────────────────────────

const OuraLogo = () => (
  <svg viewBox="0 0 24 24" className="w-12 h-12" fill="currentColor">
    <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
    <circle cx="12" cy="12" r="4" />
  </svg>
);

// ── Main page ─────────────────────────────────────────────────────────────────

export default function OnboardingPage() {
  const router = useRouter();
  const { user, setProfile, setOuraConnection } = useAuthStore();
  const [step, setStep] = useState(1);
  const [isSaving, setIsSaving] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
  const [selectedConditions, setSelectedConditions] = useState<string[]>([]);
  const [noConditions, setNoConditions] = useState(false);

  // ── Step 1: Goals ────────────────────────────────────────────────────────

  const toggleGoal = (value: string) => {
    setSelectedGoals((prev) =>
      prev.includes(value) ? prev.filter((g) => g !== value) : [...prev, value]
    );
  };

  const handleSaveGoals = async () => {
    if (!user) return;
    setIsSaving(true);
    try {
      // Persist to profiles.primary_goals
      const { error: profileErr } = await supabase
        .from('profiles')
        .update({ primary_goals: selectedGoals })
        .eq('id', user.id);
      if (profileErr) console.warn('profiles goals update:', profileErr.message);

      // Upsert user_health_profile.health_goals
      const { error: uhpErr } = await supabase
        .from('user_health_profile')
        .upsert({ user_id: user.id, health_goals: selectedGoals }, { onConflict: 'user_id' });
      if (uhpErr) console.warn('user_health_profile upsert:', uhpErr.message);

      setStep(2);
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : 'Failed to save goals');
    } finally {
      setIsSaving(false);
    }
  };

  // ── Step 2: Conditions ───────────────────────────────────────────────────

  const toggleCondition = (name: string) => {
    setNoConditions(false);
    setSelectedConditions((prev) =>
      prev.includes(name) ? prev.filter((c) => c !== name) : [...prev, name]
    );
  };

  const handleNoneCurrently = () => {
    setNoConditions(true);
    setSelectedConditions([]);
  };

  const handleSaveConditions = async () => {
    if (!user) return;
    setIsSaving(true);
    try {
      if (selectedConditions.length > 0) {
        const rows = selectedConditions.map((name) => ({
          user_id: user.id,
          condition_name: name,
          condition_category: CONDITION_CATEGORY_MAP[name] ?? 'other',
          is_active: true,
        }));
        const { error } = await supabase.from('health_conditions').insert(rows);
        if (error) console.warn('health_conditions insert:', error.message);
      }

      // Mark onboarding complete
      const { error: profileErr } = await supabase
        .from('profiles')
        .update({ onboarding_completed_at: new Date().toISOString() })
        .eq('id', user.id);
      if (profileErr) console.warn('profiles onboarding_completed_at:', profileErr.message);

      setProfile({ profile_completed: true });
      setStep(3);
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : 'Failed to save conditions');
    } finally {
      setIsSaving(false);
    }
  };

  // ── Step 3: Oura ─────────────────────────────────────────────────────────

  const handleConnectOura = async () => {
    setIsConnecting(true);
    try {
      const response = await ouraService.getAuthUrl();
      if (response.sandbox_mode) {
        toast.success('Connected to Oura (Sandbox Mode)');
        setOuraConnection({
          id: 'sandbox',
          user_id: 'sandbox',
          is_active: true,
          is_sandbox: true,
        });
        setTimeout(() => router.push('/timeline'), 1000);
      } else if (response.auth_url) {
        globalThis.location.href = response.auth_url;
      } else {
        toast.error('Oura integration not configured');
        setIsConnecting(false);
      }
    } catch {
      toast.error('Failed to initiate Oura connection');
      setIsConnecting(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900 px-4 py-12">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-6">
          <Activity className="w-10 h-10 text-primary-600 dark:text-primary-400 mx-auto" />
          <h1 className="mt-4 text-2xl font-bold text-slate-900 dark:text-slate-100">
            {step === 1 && 'What are your health goals?'}
            {step === 2 && 'Any health conditions to track?'}
            {step === 3 && 'Connect your Oura Ring'}
          </h1>
          <p className="mt-1 text-slate-500 dark:text-slate-400 text-sm">
            {step === 1 && 'Select all that apply — you can change these later.'}
            {step === 2 && 'This helps us tailor insights to what matters most to you.'}
            {step === 3 && 'Sync your sleep, activity, and readiness data.'}
          </p>
        </div>

        <StepIndicator step={step} />

        {/* Step 1 — Goals */}
        {step === 1 && (
          <Card>
            <div className="grid grid-cols-2 gap-3">
              {GOAL_OPTIONS.map(({ value, label, icon: Icon }) => {
                const active = selectedGoals.includes(value);
                return (
                  <button
                    key={value}
                    type="button"
                    onClick={() => toggleGoal(value)}
                    className={`flex items-center gap-3 p-4 rounded-xl border-2 text-left transition-colors ${
                      active
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                    }`}
                  >
                    <Icon
                      className={`w-5 h-5 flex-shrink-0 ${active ? 'text-primary-600 dark:text-primary-400' : 'text-slate-400 dark:text-slate-500'}`}
                    />
                    <span
                      className={`text-sm font-medium ${active ? 'text-primary-700 dark:text-primary-300' : 'text-slate-700 dark:text-slate-300'}`}
                    >
                      {label}
                    </span>
                  </button>
                );
              })}
            </div>
            <div className="mt-6 space-y-3">
              <Button
                onClick={handleSaveGoals}
                className="w-full"
                isLoading={isSaving}
                disabled={selectedGoals.length === 0}
              >
                Continue
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
              <button
                type="button"
                onClick={() => setStep(2)}
                className="w-full text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              >
                Skip for now
              </button>
            </div>
          </Card>
        )}

        {/* Step 2 — Health conditions */}
        {step === 2 && (
          <Card>
            <div className="flex flex-wrap gap-2">
              {COMMON_CONDITIONS.map((name) => {
                const active = selectedConditions.includes(name);
                return (
                  <button
                    key={name}
                    type="button"
                    onClick={() => toggleCondition(name)}
                    className={`px-3 py-1.5 rounded-full border text-sm font-medium transition-colors ${
                      active
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                        : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-500'
                    }`}
                  >
                    {name}
                  </button>
                );
              })}
            </div>

            <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
              <button
                type="button"
                onClick={handleNoneCurrently}
                className={`w-full py-2 rounded-lg border text-sm font-medium transition-colors ${
                  noConditions
                    ? 'border-slate-500 bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-slate-100'
                    : 'border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:border-slate-300'
                }`}
              >
                None currently
              </button>
            </div>

            <div className="mt-5 space-y-3">
              <Button
                onClick={handleSaveConditions}
                className="w-full"
                isLoading={isSaving}
                disabled={selectedConditions.length === 0 && !noConditions}
              >
                Continue
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
              <button
                type="button"
                onClick={() => setStep(1)}
                className="w-full text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              >
                Back
              </button>
            </div>
          </Card>
        )}

        {/* Step 3 — Oura */}
        {step === 3 && (
          <Card>
            <div className="text-center">
              <div className="w-20 h-20 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-6">
                <OuraLogo />
              </div>

              <div className="space-y-3 mb-8 text-left">
                {[
                  { title: 'Read-only access', desc: 'We only read your data, never modify it' },
                  { title: 'Secure connection', desc: 'Data is encrypted in transit and at rest' },
                  { title: 'Revoke anytime', desc: 'Disconnect your device whenever you want' },
                ].map(({ title, desc }) => (
                  <div key={title} className="flex items-start gap-3 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-slate-900 dark:text-slate-100">{title}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              <Button onClick={handleConnectOura} className="w-full" isLoading={isConnecting}>
                Connect Oura Ring
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>

              <button
                type="button"
                onClick={() => router.push('/timeline')}
                className="mt-4 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              >
                Skip for now
              </button>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
