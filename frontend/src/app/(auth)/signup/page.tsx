'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { supabase } from '@/lib/supabase';
import { useAuthStore } from '@/stores/authStore';
import { Activity } from 'lucide-react';
import toast from 'react-hot-toast';

const inputClass =
  'w-full px-4 py-2.5 border rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 ' +
  'focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors';

export default function SignupPage() {
  const router = useRouter();
  const { setUser } = useAuthStore();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const errors = {
    name: !name.trim() ? 'Full name is required' : '',
    email: !email ? 'Email is required' : '',
    password:
      !password
        ? 'Password is required'
        : password.length < 8
        ? 'Password must be at least 8 characters'
        : '',
  };

  const hasErrors = Object.values(errors).some(Boolean);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    if (hasErrors) return;

    setIsLoading(true);
    try {
      const { data, error } = await supabase.auth.signUp({
        email: email.trim().toLowerCase(),
        password,
        options: {
          data: { name: name.trim() },
        },
      });

      if (error) throw error;
      if (!data.user) throw new Error('Signup failed — please try again');
      // Profile row auto-created by database trigger on auth.users INSERT

      setUser({
        id: data.user.id,
        email: data.user.email!,
        name: name.trim(),
        created_at: data.user.created_at,
      });

      toast.success('Account created!');
      router.push('/onboarding');
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2">
            <Activity className="w-10 h-10 text-primary-600 dark:text-primary-400" />
            <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">Vitalix</span>
          </Link>
          <h1 className="mt-6 text-2xl font-bold text-slate-900 dark:text-slate-100">
            Create your account
          </h1>
          <p className="mt-2 text-slate-600 dark:text-slate-400">
            Start your free health journey
          </p>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-8">
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
                autoFocus
              />
              {submitted && errors.name && <p className="mt-1 text-xs text-red-500">{errors.name}</p>}
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
              {submitted && errors.email && <p className="mt-1 text-xs text-red-500">{errors.email}</p>}
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
      </div>
    </div>
  );
}
