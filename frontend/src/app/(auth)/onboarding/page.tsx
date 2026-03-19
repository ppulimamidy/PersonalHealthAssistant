'use client';

import { useState, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/stores/authStore';
import { supabase } from '@/lib/supabase';
import { api } from '@/services/api';
import { ouraService } from '@/services/oura';
import {
  Activity, Heart, Stethoscope, Users, Target, Search,
  Moon, Dumbbell, Brain, Zap, ChevronRight, Check,
} from 'lucide-react';
import toast from 'react-hot-toast';

// ── Types ────────────────────────────────────────────────────────────────────

interface SpecialistInfo {
  agent_type: string;
  agent_name: string;
  specialty: string;
  description: string;
}

interface JourneyProposal {
  key: string;
  title: string;
  goal_type: string;
  duration_type: string;
  target_metrics: string[];
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

// ── Step indicator ───────────────────────────────────────────────────────────

function StepDots({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-8">
      {Array.from({ length: total }, (_, i) => (
        <div
          key={i}
          className="h-1.5 rounded-full transition-all duration-300"
          style={{
            width: i === current ? 24 : 8,
            backgroundColor: i <= current ? '#00D4AA' : 'rgba(255,255,255,0.1)',
          }}
        />
      ))}
    </div>
  );
}

// ── Goal icons ───────────────────────────────────────────────────────────────

const GOAL_ICONS: Record<string, typeof Moon> = {
  sleep_optimization: Moon,
  weight_loss: Target,
  muscle_building: Dumbbell,
  mental_health: Brain,
  general_wellness: Zap,
  cardiac_rehab: Heart,
};

// ── Main ─────────────────────────────────────────────────────────────────────

function OnboardingFlow() {
  const router = useRouter();
  const { user, setProfile, setOuraConnection } = useAuthStore();

  const [step, setStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  // Step 0 state: intent
  const [intent, setIntent] = useState<string>('');

  // Step 1 state: condition/goal selection
  const [conditionCategories, setConditionCategories] = useState<Record<string, string[]>>({});
  const [goalOptions, setGoalOptions] = useState<Array<{ value: string; label: string; icon: string }>>([]);
  const [selectedValue, setSelectedValue] = useState('');

  // Step 2 state: quick context + specialist + journey
  const [specialist, setSpecialist] = useState<SpecialistInfo | null>(null);
  const [journeyProposal, setJourneyProposal] = useState<JourneyProposal | null>(null);
  const [quickQuestions, setQuickQuestions] = useState<QuickQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, any>>({});

  // ── Step 0: What brings you here? ──────────────────────────────────────────

  const handleIntent = async (selectedIntent: string) => {
    setIntent(selectedIntent);
    setIsLoading(true);
    try {
      const { data } = await api.post('/api/v1/onboarding/intent', { intent: selectedIntent });

      if (selectedIntent === 'condition') {
        setConditionCategories(data.categories || {});
        setStep(1);
      } else if (selectedIntent === 'goal') {
        setGoalOptions(data.options || []);
        setStep(1);
      } else {
        // Exploring — skip to step 3 (connect + guide)
        setSpecialist(data.specialist || null);
        setStep(3);
      }
    } catch (err) {
      toast.error('Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // ── Step 1: Pick condition or goal ─────────────────────────────────────────

  const handleSelect = async (value: string) => {
    setSelectedValue(value);
    setIsLoading(true);
    try {
      const { data } = await api.post('/api/v1/onboarding/select', {
        type: intent === 'condition' ? 'condition' : 'goal',
        value,
      });
      setSpecialist(data.specialist || null);
      setJourneyProposal(data.journey_proposal || null);
      setQuickQuestions(data.quick_questions || []);
      setStep(2);
    } catch (err) {
      toast.error('Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // ── Step 2: Quick context questions ────────────────────────────────────────

  const handleContextDone = async () => {
    setIsLoading(true);
    try {
      if (Object.keys(answers).length > 0) {
        await api.post('/api/v1/onboarding/context', { answers });
      }
      setStep(3);
    } catch {
      // Non-fatal
      setStep(3);
    } finally {
      setIsLoading(false);
    }
  };

  // ── Step 3: Connect + Meet Guide ───────────────────────────────────────────

  const handleStartJourney = async () => {
    setIsLoading(true);
    try {
      await api.post('/api/v1/onboarding/start-journey', {
        journey_template_key: journeyProposal?.key,
      });
      toast.success('Your journey has started!');
      router.push('/home');
    } catch (err) {
      toast.error('Could not start journey. Redirecting to home.');
      router.push('/home');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipJourney = async () => {
    try {
      await api.post('/api/v1/onboarding/complete', { skipped_journey: true });
    } catch {
      // Non-fatal
    }
    router.push('/home');
  };

  const handleConnectOura = async () => {
    try {
      const resp = await ouraService.getAuthUrl();
      if (resp?.auth_url) {
        window.location.href = resp.auth_url;
      } else {
        setOuraConnection({ id: 'sandbox', user_id: user?.id ?? '', is_active: true, is_sandbox: true });
        toast.success('Wearable connected (sandbox)');
      }
    } catch {
      toast.error('Could not connect. You can do this later from Devices.');
    }
  };

  // ── Provider/Caregiver quick onboarding ────────────────────────────────────

  const handleProviderComplete = async () => {
    try {
      await api.patch('/api/v1/profile/role', { user_role: 'provider' });
      await supabase.from('profiles').update({ onboarding_completed_at: new Date().toISOString() }).eq('id', user?.id);
    } catch { /* non-fatal */ }
    router.push('/patients');
  };

  const handleCaregiverComplete = async () => {
    try {
      await api.patch('/api/v1/profile/role', { user_role: 'caregiver' });
      await supabase.from('profiles').update({ onboarding_completed_at: new Date().toISOString() }).eq('id', user?.id);
    } catch { /* non-fatal */ }
    router.push('/home');
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  const totalSteps = intent === 'exploring' ? 2 : quickQuestions.length > 0 ? 4 : 3;

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12" style={{ backgroundColor: '#080B10' }}>
      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="text-center mb-6">
          <Link href="/" className="inline-flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#00D4AA]/10 flex items-center justify-center">
              <Activity className="w-4 h-4 text-[#00D4AA]" />
            </div>
            <span className="text-lg font-semibold text-[#E8EDF5]">
              Vital<span className="text-[#00D4AA]">ix</span>
            </span>
          </Link>
        </div>

        <StepDots current={step} total={totalSteps} />

        {/* ── Step 0: What brings you here? ──────────────────────── */}
        {step === 0 && (
          <div className="space-y-4">
            <h1 className="text-2xl font-bold text-[#E8EDF5] text-center mb-2">What brings you to Vitalix?</h1>
            <p className="text-sm text-[#526380] text-center mb-6">This shapes your entire experience</p>

            <button
              onClick={() => handleIntent('condition')}
              disabled={isLoading}
              className="w-full flex items-center gap-4 p-5 rounded-xl text-left transition-all hover:scale-[1.01]"
              style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <div className="w-12 h-12 rounded-xl bg-[#F87171]/10 flex items-center justify-center flex-shrink-0">
                <Heart className="w-5 h-5 text-[#F87171]" />
              </div>
              <div className="flex-1">
                <p className="font-semibold text-sm text-[#E8EDF5]">I&apos;m managing a health condition</p>
                <p className="text-xs text-[#526380] mt-0.5">PCOS, diabetes, thyroid, IBS, anxiety, etc.</p>
              </div>
              <ChevronRight className="w-4 h-4 text-[#3D4F66]" />
            </button>

            <button
              onClick={() => handleIntent('goal')}
              disabled={isLoading}
              className="w-full flex items-center gap-4 p-5 rounded-xl text-left transition-all hover:scale-[1.01]"
              style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <div className="w-12 h-12 rounded-xl bg-[#00D4AA]/10 flex items-center justify-center flex-shrink-0">
                <Target className="w-5 h-5 text-[#00D4AA]" />
              </div>
              <div className="flex-1">
                <p className="font-semibold text-sm text-[#E8EDF5]">I want to improve my health</p>
                <p className="text-xs text-[#526380] mt-0.5">Sleep, weight, fitness, stress, energy</p>
              </div>
              <ChevronRight className="w-4 h-4 text-[#3D4F66]" />
            </button>

            <button
              onClick={() => handleIntent('exploring')}
              disabled={isLoading}
              className="w-full flex items-center gap-4 p-5 rounded-xl text-left transition-all hover:scale-[1.01]"
              style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <div className="w-12 h-12 rounded-xl bg-[#60A5FA]/10 flex items-center justify-center flex-shrink-0">
                <Search className="w-5 h-5 text-[#60A5FA]" />
              </div>
              <div className="flex-1">
                <p className="font-semibold text-sm text-[#E8EDF5]">Just exploring</p>
                <p className="text-xs text-[#526380] mt-0.5">See what my health data can tell me</p>
              </div>
              <ChevronRight className="w-4 h-4 text-[#3D4F66]" />
            </button>

            {/* Provider/Caregiver link */}
            <div className="text-center pt-4">
              <button
                onClick={() => setStep(-1)}
                className="text-xs text-[#526380] hover:text-[#8B97A8] transition-colors"
              >
                Healthcare provider or caregiver? →
              </button>
            </div>
          </div>
        )}

        {/* ── Step -1: Provider/Caregiver ─────────────────────────── */}
        {step === -1 && (
          <div className="space-y-4">
            <h1 className="text-xl font-bold text-[#E8EDF5] text-center mb-6">Professional access</h1>
            <button
              onClick={handleProviderComplete}
              className="w-full flex items-center gap-4 p-5 rounded-xl text-left transition-all hover:scale-[1.01]"
              style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <Stethoscope className="w-5 h-5 text-[#818CF8]" />
              <div>
                <p className="font-semibold text-sm text-[#E8EDF5]">Healthcare Provider</p>
                <p className="text-xs text-[#526380] mt-0.5">Monitor patients, review care plans</p>
              </div>
            </button>
            <button
              onClick={handleCaregiverComplete}
              className="w-full flex items-center gap-4 p-5 rounded-xl text-left transition-all hover:scale-[1.01]"
              style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <Users className="w-5 h-5 text-[#6EE7B7]" />
              <div>
                <p className="font-semibold text-sm text-[#E8EDF5]">Caregiver / Family Member</p>
                <p className="text-xs text-[#526380] mt-0.5">Support a family member&apos;s health</p>
              </div>
            </button>
            <button onClick={() => setStep(0)} className="text-xs text-[#526380] hover:text-[#8B97A8] mx-auto block mt-4">
              ← Back
            </button>
          </div>
        )}

        {/* ── Step 1: Pick condition or goal ───────────────────────── */}
        {step === 1 && intent === 'condition' && (
          <div>
            <h1 className="text-xl font-bold text-[#E8EDF5] text-center mb-2">What&apos;s your primary condition?</h1>
            <p className="text-xs text-[#526380] text-center mb-6">You can add more later</p>

            <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
              {Object.entries(conditionCategories).map(([category, conditions]) => (
                <div key={category}>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-[#526380] mb-2">{category}</p>
                  <div className="flex flex-wrap gap-2">
                    {conditions.map((c) => (
                      <button
                        key={c}
                        onClick={() => handleSelect(c)}
                        disabled={isLoading}
                        className="px-3 py-2 rounded-lg text-xs font-medium transition-all hover:scale-[1.02]"
                        style={{
                          backgroundColor: selectedValue === c ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.03)',
                          border: `1px solid ${selectedValue === c ? 'rgba(0,212,170,0.3)' : 'rgba(255,255,255,0.06)'}`,
                          color: selectedValue === c ? '#00D4AA' : '#E8EDF5',
                        }}
                      >
                        {c}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <button onClick={() => setStep(0)} className="text-xs text-[#526380] hover:text-[#8B97A8] mx-auto block mt-6">
              ← Back
            </button>
          </div>
        )}

        {step === 1 && intent === 'goal' && (
          <div>
            <h1 className="text-xl font-bold text-[#E8EDF5] text-center mb-2">What&apos;s your #1 health goal?</h1>
            <p className="text-xs text-[#526380] text-center mb-6">Pick the one that matters most right now</p>

            <div className="grid grid-cols-2 gap-3">
              {goalOptions.map((g) => {
                const Icon = GOAL_ICONS[g.value] || Target;
                return (
                  <button
                    key={g.value}
                    onClick={() => handleSelect(g.value)}
                    disabled={isLoading}
                    className="flex flex-col items-center gap-2 p-5 rounded-xl transition-all hover:scale-[1.02]"
                    style={{
                      backgroundColor: 'rgba(255,255,255,0.03)',
                      border: '1px solid rgba(255,255,255,0.06)',
                    }}
                  >
                    <Icon className="w-6 h-6 text-[#00D4AA]" />
                    <span className="text-sm font-medium text-[#E8EDF5]">{g.label}</span>
                  </button>
                );
              })}
            </div>

            <button onClick={() => setStep(0)} className="text-xs text-[#526380] hover:text-[#8B97A8] mx-auto block mt-6">
              ← Back
            </button>
          </div>
        )}

        {/* ── Step 2: Quick context questions ──────────────────────── */}
        {step === 2 && (
          <div>
            <h1 className="text-xl font-bold text-[#E8EDF5] text-center mb-2">Quick questions</h1>
            <p className="text-xs text-[#526380] text-center mb-6">Helps personalize your experience</p>

            <div className="space-y-4">
              {quickQuestions.map((q) => (
                <div
                  key={q.id}
                  className="rounded-xl p-4"
                  style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
                >
                  <p className="text-sm font-medium text-[#E8EDF5] mb-3">{q.question}</p>

                  {(q.input_type === 'choice' || q.input_type === 'choice_then_text') && q.options && (
                    <div className="flex flex-wrap gap-2">
                      {q.options.map((opt) => {
                        const selected = answers[q.data_field] === opt;
                        return (
                          <button
                            key={opt}
                            onClick={() => setAnswers({ ...answers, [q.data_field]: opt })}
                            className="px-3 py-1.5 rounded-lg text-xs transition-all"
                            style={{
                              backgroundColor: selected ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.03)',
                              border: `1px solid ${selected ? 'rgba(0,212,170,0.3)' : 'rgba(255,255,255,0.06)'}`,
                              color: selected ? '#00D4AA' : '#8B97A8',
                            }}
                          >
                            {opt}
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {q.input_type === 'multi_choice' && q.options && (
                    <div className="flex flex-wrap gap-2">
                      {q.options.map((opt) => {
                        const currentArr = (answers[q.data_field] as string[]) || [];
                        const selected = currentArr.includes(opt);
                        return (
                          <button
                            key={opt}
                            onClick={() => {
                              const updated = selected
                                ? currentArr.filter((x) => x !== opt)
                                : [...currentArr, opt];
                              setAnswers({ ...answers, [q.data_field]: updated });
                            }}
                            className="px-3 py-1.5 rounded-lg text-xs transition-all"
                            style={{
                              backgroundColor: selected ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.03)',
                              border: `1px solid ${selected ? 'rgba(0,212,170,0.3)' : 'rgba(255,255,255,0.06)'}`,
                              color: selected ? '#00D4AA' : '#8B97A8',
                            }}
                          >
                            {selected && <Check className="w-3 h-3 inline mr-1" />}
                            {opt}
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {(q.input_type === 'text' || (q.input_type === 'choice_then_text' && answers[q.data_field] === q.options?.[0])) && (
                    <input
                      type="text"
                      placeholder={q.text_prompt || 'Type here...'}
                      value={(answers[`${q.data_field}_text`] as string) || ''}
                      onChange={(e) => setAnswers({ ...answers, [`${q.data_field}_text`]: e.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg text-sm text-[#E8EDF5] placeholder-[#3D4F66]"
                      style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
                    />
                  )}
                </div>
              ))}
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={handleContextDone}
                disabled={isLoading}
                className="flex-1 py-2.5 rounded-lg text-sm font-medium transition-all"
                style={{ backgroundColor: '#00D4AA', color: '#080B10' }}
              >
                {isLoading ? 'Saving...' : 'Continue'}
              </button>
              <button
                onClick={() => setStep(3)}
                className="px-4 py-2.5 rounded-lg text-xs text-[#526380] hover:text-[#8B97A8]"
              >
                Skip
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: Connect + Meet Your Guide ────────────────────── */}
        {step === 3 && (
          <div className="space-y-5">
            {/* Device connection */}
            <div>
              <h2 className="text-lg font-bold text-[#E8EDF5] text-center mb-2">Connect your data</h2>
              <p className="text-xs text-[#526380] text-center mb-4">
                {specialist ? `Your ${specialist.agent_name} needs health data to get started` : 'Connect a device to start tracking'}
              </p>

              <button
                onClick={handleConnectOura}
                className="w-full flex items-center gap-4 p-4 rounded-xl transition-all hover:scale-[1.01]"
                style={{ backgroundColor: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.15)' }}
              >
                <div className="w-10 h-10 rounded-xl bg-[#00D4AA]/10 flex items-center justify-center flex-shrink-0">
                  <Activity className="w-5 h-5 text-[#00D4AA]" />
                </div>
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium text-[#E8EDF5]">Connect Wearable Device</p>
                  <p className="text-xs text-[#526380] mt-0.5">Sleep, HRV, heart rate, activity</p>
                </div>
                <ChevronRight className="w-4 h-4 text-[#00D4AA]" />
              </button>
            </div>

            {/* Specialist + Journey proposal */}
            {specialist && (
              <div
                className="rounded-xl p-5"
                style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl bg-[#00D4AA]/10 flex items-center justify-center flex-shrink-0">
                    <Stethoscope className="w-5 h-5 text-[#00D4AA]" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[#00D4AA]">Your {specialist.agent_name}</p>
                    <p className="text-xs text-[#526380]">{specialist.specialty}</p>
                  </div>
                </div>

                <p className="text-xs text-[#8B97A8] leading-relaxed mb-4">
                  {specialist.description}
                </p>

                {journeyProposal && (
                  <div
                    className="rounded-lg p-3 mb-4"
                    style={{ backgroundColor: 'rgba(96,165,250,0.04)', border: '1px solid rgba(96,165,250,0.12)' }}
                  >
                    <p className="text-xs font-semibold text-[#60A5FA] mb-2">{journeyProposal.title}</p>
                    <div className="space-y-1.5">
                      {journeyProposal.phases.map((phase, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <div className="w-5 h-5 rounded-full bg-[#60A5FA]/10 flex items-center justify-center flex-shrink-0">
                            <span className="text-[9px] font-bold text-[#60A5FA]">{i + 1}</span>
                          </div>
                          <div>
                            <p className="text-xs text-[#E8EDF5]">{phase.name}</p>
                            {phase.description && (
                              <p className="text-[10px] text-[#526380]">{phase.description}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex gap-3">
                  {journeyProposal && (
                    <button
                      onClick={handleStartJourney}
                      disabled={isLoading}
                      className="flex-1 py-2.5 rounded-lg text-sm font-medium transition-all"
                      style={{ backgroundColor: '#00D4AA', color: '#080B10' }}
                    >
                      {isLoading ? 'Starting...' : 'Start My Journey'}
                    </button>
                  )}
                  <button
                    onClick={handleSkipJourney}
                    className="px-4 py-2.5 rounded-lg text-xs text-[#526380] hover:text-[#8B97A8] transition-colors"
                  >
                    {journeyProposal ? 'Maybe Later' : 'Continue to Home'}
                  </button>
                </div>
              </div>
            )}

            {/* No specialist (exploring path) */}
            {!specialist && (
              <button
                onClick={handleSkipJourney}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all"
                style={{ backgroundColor: '#00D4AA', color: '#080B10' }}
              >
                Get Started
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Export with Suspense (for useSearchParams) ───────────────────────────────

export default function OnboardingPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" style={{ backgroundColor: '#080B10' }} />}>
      <OnboardingFlow />
    </Suspense>
  );
}
