'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { ouraService } from '@/services/oura';
import { useAuthStore } from '@/stores/authStore';
import { Activity, CheckCircle, Circle, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { supabase } from '@/lib/supabase';
import type { Gender, UserProfile } from '@/types';

const OuraLogo = () => (
  <svg viewBox="0 0 24 24" className="w-12 h-12" fill="currentColor">
    <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
    <circle cx="12" cy="12" r="4" />
  </svg>
);

export default function OnboardingPage() {
  const router = useRouter();
  const { user, profile, setProfile, setOuraConnection } = useAuthStore();
  const [step, setStep] = useState(1);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  const [age, setAge] = useState<number | ''>('');
  const [gender, setGender] = useState<Gender | ''>('');
  const [weight, setWeight] = useState<number | ''>('');
  const [weightUnit, setWeightUnit] = useState<'kg' | 'lb'>('lb');

  useEffect(() => {
    // Prefill from persisted authStore / Supabase metadata if present
    if (profile?.age && age === '') setAge(profile.age);
    if (profile?.gender && gender === '') setGender(profile.gender);
    if (profile?.weight_kg && weight === '') {
      // default UI is lb; convert from kg for display
      setWeightUnit('lb');
      setWeight(Math.round(profile.weight_kg * 2.20462));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile]);

  const canContinueProfile = useMemo(() => {
    return (
      typeof age === 'number' &&
      age >= 13 &&
      age <= 120 &&
      typeof weight === 'number' &&
      weight > 0 &&
      Boolean(gender)
    );
  }, [age, weight, gender]);

  const weightKg = useMemo(() => {
    if (typeof weight !== 'number') return undefined;
    const kg = weightUnit === 'kg' ? weight : weight / 2.20462;
    return Math.round(kg * 10) / 10;
  }, [weight, weightUnit]);

  const handleSaveProfile = async () => {
    if (!canContinueProfile || !weightKg || gender === '' || age === '') return;
    setIsSavingProfile(true);
    try {
      const nextProfile: UserProfile = {
        age: age as number,
        gender: gender as Gender,
        weight_kg: weightKg,
        profile_completed: true,
      };

      const { error } = await supabase.auth.updateUser({
        data: {
          age: nextProfile.age,
          gender: nextProfile.gender,
          weight_kg: nextProfile.weight_kg,
          profile_completed: true,
        },
      });
      if (error) throw error;

      setProfile(nextProfile);
      toast.success('Profile saved');
      setStep(2);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to save profile';
      toast.error(msg);
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleConnectOura = async () => {
    setIsConnecting(true);
    try {
      const response = await ouraService.getAuthUrl();

      // Check if we're in sandbox mode
      if (response.sandbox_mode) {
        // In sandbox mode, automatically connect without OAuth
        toast.success('Connected to Oura (Sandbox Mode)');
        setOuraConnection({
          id: 'sandbox',
          user_id: 'sandbox',
          is_active: true,
          is_sandbox: true,
        });

        // Redirect to timeline after a short delay
        setTimeout(() => {
          router.push('/timeline');
        }, 1000);
      } else if (response.auth_url) {
        // Production mode - redirect to OAuth
        window.location.href = response.auth_url;
      } else {
        toast.error('Oura integration not configured');
        setIsConnecting(false);
      }
    } catch (error) {
      console.error('Failed to connect Oura:', error);
      toast.error('Failed to initiate Oura connection');
      setIsConnecting(false);
    }
  };

  const handleSkip = () => {
    router.push('/timeline');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <Activity className="w-12 h-12 text-primary-600 mx-auto" />
          <h1 className="mt-4 text-2xl font-bold text-slate-900">
            Let's Get You Set Up
          </h1>
          <p className="mt-2 text-slate-600">
            Add a few basics so we can personalize your insights
          </p>
        </div>

        {/* Progress */}
        <div className="flex items-center justify-center gap-4 mb-8">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-6 h-6 text-primary-600" />
            <span className="text-sm font-medium text-slate-900">Account</span>
          </div>
          <div className="w-12 h-0.5 bg-slate-200" />
          <div className="flex items-center gap-2">
            {step >= 1 ? (
              <CheckCircle className="w-6 h-6 text-primary-600" />
            ) : (
              <div className="w-6 h-6 rounded-full border-2 border-primary-600 flex items-center justify-center">
                <span className="text-xs font-bold text-primary-600">2</span>
              </div>
            )}
            <span className="text-sm font-medium text-slate-900">Profile</span>
          </div>
          <div className="w-12 h-0.5 bg-slate-200" />
          <div className="flex items-center gap-2">
            {step >= 2 ? (
              <div className="w-6 h-6 rounded-full border-2 border-primary-600 flex items-center justify-center">
                <span className="text-xs font-bold text-primary-600">2</span>
              </div>
            ) : (
              <Circle className="w-6 h-6 text-slate-300" />
            )}
            <span className="text-sm font-medium text-slate-900">Connect Device</span>
          </div>
        </div>

        {step === 1 ? (
          <Card>
            <div>
              <h2 className="text-xl font-semibold text-slate-900 mb-2">Your profile</h2>
              <p className="text-slate-600 mb-6">
                This helps us tailor insights and generate better doctor-visit questions.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Age</label>
                  <input
                    type="number"
                    value={age}
                    onChange={(e) => setAge(e.target.value === '' ? '' : Number(e.target.value))}
                    min={13}
                    max={120}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g. 32"
                  />
                  <p className="mt-1 text-xs text-slate-500">We only use this for context, not diagnosis.</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Gender</label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value as Gender)}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select…</option>
                    <option value="female">Female</option>
                    <option value="male">Male</option>
                    <option value="other">Other</option>
                    <option value="prefer_not_to_say">Prefer not to say</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Weight</label>
                  <div className="flex gap-3">
                    <input
                      type="number"
                      value={weight}
                      onChange={(e) => setWeight(e.target.value === '' ? '' : Number(e.target.value))}
                      min={1}
                      className="flex-1 px-4 py-2 border border-slate-300 rounded-lg bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder={weightUnit === 'lb' ? 'e.g. 160' : 'e.g. 72'}
                    />
                    <select
                      value={weightUnit}
                      onChange={(e) => setWeightUnit(e.target.value as 'kg' | 'lb')}
                      className="w-28 px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="lb">lb</option>
                      <option value="kg">kg</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-3">
                <Button onClick={handleSaveProfile} className="w-full" isLoading={isSavingProfile} disabled={!canContinueProfile}>
                  Continue
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
                <button onClick={() => setStep(2)} className="w-full text-sm text-slate-500 hover:text-slate-700">
                  Skip for now
                </button>
              </div>
            </div>
          </Card>
        ) : (
          <Card>
            <div className="text-center">
              <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <OuraLogo />
              </div>
              <h2 className="text-xl font-semibold text-slate-900 mb-2">
                Connect Your Oura Ring
              </h2>
              <p className="text-slate-600 mb-8">
                We'll sync your sleep, activity, and readiness data to provide
                personalized health insights.
              </p>

              <div className="space-y-4 mb-8 text-left">
                <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-slate-900">Read-only access</p>
                    <p className="text-xs text-slate-500">We only read your data, never modify it</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-slate-900">Secure connection</p>
                    <p className="text-xs text-slate-500">Data is encrypted in transit and at rest</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-slate-900">Revoke anytime</p>
                    <p className="text-xs text-slate-500">Disconnect your device whenever you want</p>
                  </div>
                </div>
              </div>

              <Button
                onClick={handleConnectOura}
                className="w-full"
                isLoading={isConnecting}
              >
                Connect Oura Ring
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>

              <button
                onClick={handleSkip}
                className="mt-4 text-sm text-slate-500 hover:text-slate-700"
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
