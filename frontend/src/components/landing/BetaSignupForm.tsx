'use client';

import { useState } from 'react';
import { ArrowRight, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { betaService } from '@/services/beta';
import toast from 'react-hot-toast';

export function BetaSignupForm() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || loading) return;

    setLoading(true);
    try {
      await betaService.signup(email, 'landing_page');
      setSubmitted(true);
      toast.success('You\'re on the list! We\'ll be in touch soon.');
    } catch {
      toast.error('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="text-center py-4">
        <p className="text-lg font-medium text-green-600">You're on the list!</p>
        <p className="text-sm text-slate-500 mt-1">We'll email you when your spot opens up.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Enter your email"
        required
        className="flex-1 px-4 py-3 rounded-lg border border-slate-300 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
      />
      <Button type="submit" size="lg" disabled={loading}>
        {loading ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <>
            Join Waitlist
            <ArrowRight className="w-5 h-5 ml-2" />
          </>
        )}
      </Button>
    </form>
  );
}
