'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { supabase } from '@/lib/supabase';
import { useAuthStore } from '@/stores/authStore';
import { Activity, User, Stethoscope, Users, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';
import type { BiologicalSex, UserRole } from '@/types';

// ── Role options ──────────────────────────────────────────────────────────────

const ROLE_OPTIONS: {
  value: UserRole;
  label: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  {
    value: 'patient',
    label: 'Patient / Personal Health',
    subtitle: 'Track your health data, get AI insights, and manage your wellbeing',
    icon: User,
  },
  {
    value: 'provider',
    label: 'Healthcare Provider',
    subtitle: 'Monitor patients who share access, review care plans and lab results',
    icon: Stethoscope,
  },
  {
    value: 'caregiver',
    label: 'Caregiver / Family Member',
    subtitle: "Monitor a family member's health and help coordinate their care",
    icon: Users,
  },
];

const SEX_OPTIONS: { value: BiologicalSex; label: string }[] = [
  { value: 'female', label: 'Female' },
  { value: 'male', label: 'Male' },
  { value: 'other', label: 'Other' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
];

const inputClass =
  'w-full px-4 py-2 border rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 ' +
  'focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors';

const ROLE_LABELS: Record<UserRole, string> = {
  patient: 'Patient / Personal Health',
  provider: 'Healthcare Provider',
  caregiver: 'Caregiver / Family Member',
};

const ROLE_ICONS: Record<UserRole, React.ComponentType<{ className?: string }>> = {
  patient: User,
  provider: Stethoscope,
  caregiver: Users,
};

// ── Page ──────────────────────────────────────────────────────────────────────

export default function SignupPage() {
  const router = useRouter();
  const { setUser } = useAuthStore();

  // formStep 0 = role selection, 1 = account details form
  const [formStep, setFormStep] = useState(0);
  const [role, setRole] = useState<UserRole | ''>('');

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [dob, setDob] = useState('');
  const [sex, setSex] = useState<BiologicalSex | ''>('');
  const [weight, setWeight] = useState<number | ''>('');
  const [weightUnit, setWeightUnit] = useState<'lb' | 'kg'>('lb');
  const [isLoading, setIsLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const weightKg = useMemo(() => {
    if (typeof weight !== 'number' || weight <= 0) return undefined;
    return weightUnit === 'kg' ? weight : Math.round((weight / 2.20462) * 10) / 10;
  }, [weight, weightUnit]);

  // Earliest allowed DOB: 13 years ago
  const maxDob = useMemo(() => {
    const d = new Date();
    d.setFullYear(d.getFullYear() - 13);
    return d.toISOString().split('T')[0];
  }, []);

  const errors = {
    name: !name.trim() ? 'Full name is required' : '',
    email: !email ? 'Email is required' : '',
    password:
      !password
        ? 'Password is required'
        : password.length < 8
        ? 'Password must be at least 8 characters'
        : '',
    dob: !dob ? 'Date of birth is required' : '',
    sex: !sex ? 'Please select a biological sex' : '',
    weight: !weightKg ? 'Please enter a valid weight' : '',
  };

  const hasErrors = Object.values(errors).some(Boolean);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);

    if (hasErrors || !weightKg || !sex || !dob) return;

    setIsLoading(true);
    try {
      // 1. Create auth user
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            name,
            date_of_birth: dob,
            biological_sex: sex,
            weight_kg: weightKg,
            user_role: role || 'patient',
          },
        },
      });

      if (error) throw error;
      if (!data.user) throw new Error('Signup failed — please try again');

      // 2. Upsert profile row with user_role
      const { error: profileError } = await supabase
        .from('profiles')
        .upsert(
          {
            id: data.user.id,
            full_name: name.trim(),
            date_of_birth: dob,
            biological_sex: sex,
            weight_kg: weightKg,
            user_role: role || 'patient',
          },
          { onConflict: 'id' },
        );

      if (profileError) {
        // Non-fatal — profile fields can be completed later
        console.warn('profiles upsert:', profileError.message);
      }

      setUser({
        id: data.user.id,
        email: data.user.email!,
        name: name.trim(),
        created_at: data.user.created_at,
      });

      toast.success('Account created!');
      // Pass role to onboarding so it can branch the experience
      router.push(`/onboarding?role=${role || 'patient'}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Signup failed';
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const fieldBorder = (field: keyof typeof errors) =>
    submitted && errors[field]
      ? 'border-red-400 dark:border-red-500'
      : 'border-slate-300 dark:border-slate-600';

  const FieldError = ({ field }: { field: keyof typeof errors }) =>
    submitted && errors[field] ? (
      <p className="mt-1 text-xs text-red-500">{errors[field]}</p>
    ) : null;

  const RoleIcon = role ? ROLE_ICONS[role] : null;

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2">
            <Activity className="w-10 h-10 text-primary-600 dark:text-primary-400" />
            <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">HealthAssist</span>
          </Link>
          <h1 className="mt-6 text-2xl font-bold text-slate-900 dark:text-slate-100">
            {formStep === 0 ? 'Who are you?' : 'Create your account'}
          </h1>
          <p className="mt-2 text-slate-600 dark:text-slate-400">
            {formStep === 0
              ? 'This helps us set up the right experience for you.'
              : 'Start your free 30-day trial'}
          </p>
        </div>

        {/* ── Step 0: Role Selection ─────────────────────────────── */}
        {formStep === 0 && (
          <div className="space-y-3">
            {ROLE_OPTIONS.map(({ value, label, subtitle, icon: Icon }) => (
              <button
                key={value}
                type="button"
                onClick={() => {
                  setRole(value);
                  setFormStep(1);
                }}
                className="w-full flex items-center gap-4 p-5 rounded-xl border-2 text-left transition-all
                  border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800
                  hover:border-primary-400 dark:hover:border-primary-600 hover:shadow-md"
              >
                <div className="w-12 h-12 rounded-xl bg-slate-100 dark:bg-slate-700 flex items-center justify-center flex-shrink-0">
                  <Icon className="w-6 h-6 text-slate-500 dark:text-slate-400" />
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-sm text-slate-900 dark:text-slate-100">{label}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 leading-snug">{subtitle}</p>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 ml-auto flex-shrink-0" />
              </button>
            ))}

            <p className="text-center text-sm text-slate-500 dark:text-slate-400 pt-2">
              Already have an account?{' '}
              <Link href="/login" className="text-primary-600 dark:text-primary-400 hover:underline font-medium">
                Sign in
              </Link>
            </p>
          </div>
        )}

        {/* ── Step 1: Account Form ───────────────────────────────── */}
        {formStep === 1 && (
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-8">
            {/* Selected role badge */}
            {role && RoleIcon && (
              <div className="flex items-center justify-between mb-5 pb-4 border-b border-slate-200 dark:border-slate-700">
                <div className="flex items-center gap-2">
                  <RoleIcon className="w-4 h-4 text-primary-500" />
                  <span className="text-sm font-medium text-primary-700 dark:text-primary-300">
                    {ROLE_LABELS[role]}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setFormStep(0)}
                  className="text-xs text-slate-500 dark:text-slate-400 hover:text-primary-600 dark:hover:text-primary-400"
                >
                  Change
                </button>
              </div>
            )}

            <form onSubmit={handleSubmit} noValidate className="space-y-5">

              {/* Full name */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                  Full Name
                </label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className={`${inputClass} ${fieldBorder('name')}`}
                  placeholder="Jane Smith"
                  autoComplete="name"
                />
                <FieldError field="name" />
              </div>

              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={`${inputClass} ${fieldBorder('email')}`}
                  placeholder="you@example.com"
                  autoComplete="email"
                />
                <FieldError field="email" />
              </div>

              {/* Password */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`${inputClass} ${fieldBorder('password')}`}
                  placeholder="••••••••"
                  autoComplete="new-password"
                />
                {submitted && errors.password ? (
                  <p className="mt-1 text-xs text-red-500">{errors.password}</p>
                ) : (
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">At least 8 characters</p>
                )}
              </div>

              <hr className="border-slate-200 dark:border-slate-700" />
              <p className="text-xs text-slate-500 dark:text-slate-400 -mt-1">
                Used for personalised health baselines — only you can see this.
              </p>

              {/* Date of birth */}
              <div>
                <label htmlFor="dob" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                  Date of Birth
                </label>
                <input
                  id="dob"
                  type="date"
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                  max={maxDob}
                  className={`${inputClass} ${fieldBorder('dob')}`}
                />
                <FieldError field="dob" />
              </div>

              {/* Biological sex */}
              <div>
                <p className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                  Biological Sex
                </p>
                <div className={`grid grid-cols-2 gap-2 rounded-lg p-0.5 ${submitted && errors.sex ? 'ring-1 ring-red-400' : ''}`}>
                  {SEX_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setSex(opt.value)}
                      className={`px-3 py-2 rounded-lg border text-sm font-medium transition-colors ${
                        sex === opt.value
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                          : 'border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-400 hover:border-slate-400'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
                {submitted && errors.sex ? (
                  <p className="mt-1 text-xs text-red-500">{errors.sex}</p>
                ) : (
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    Used for clinical reference ranges and metabolic calculations.
                  </p>
                )}
              </div>

              {/* Weight */}
              <div>
                <p className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                  Weight
                </p>
                <div className="flex gap-3">
                  <input
                    type="number"
                    value={weight}
                    onChange={(e) => setWeight(e.target.value === '' ? '' : Number(e.target.value))}
                    min={1}
                    className={`flex-1 ${inputClass} ${fieldBorder('weight')}`}
                    placeholder={weightUnit === 'lb' ? 'e.g. 160' : 'e.g. 72'}
                  />
                  <div className="flex rounded-lg border border-slate-300 dark:border-slate-600 overflow-hidden">
                    {(['lb', 'kg'] as const).map((unit) => (
                      <button
                        key={unit}
                        type="button"
                        onClick={() => setWeightUnit(unit)}
                        className={`px-4 py-2 text-sm font-medium transition-colors ${
                          weightUnit === unit
                            ? 'bg-primary-500 text-white'
                            : 'bg-white dark:bg-slate-700 text-slate-600 dark:text-slate-400'
                        }`}
                      >
                        {unit}
                      </button>
                    ))}
                  </div>
                </div>
                <FieldError field="weight" />
              </div>

              <Button type="submit" className="w-full" isLoading={isLoading}>
                Create Account
              </Button>
            </form>

            <p className="mt-5 text-xs text-center text-slate-500 dark:text-slate-400">
              By signing up, you agree to our{' '}
              <a href="/terms" className="text-primary-600 dark:text-primary-400 hover:underline">Terms</a>
              {' '}and{' '}
              <a href="/privacy" className="text-primary-600 dark:text-primary-400 hover:underline">Privacy Policy</a>
            </p>

            <div className="mt-5 text-center text-sm">
              <span className="text-slate-600 dark:text-slate-400">Already have an account? </span>
              <Link href="/login" className="text-primary-600 dark:text-primary-400 hover:underline font-medium">
                Sign in
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
