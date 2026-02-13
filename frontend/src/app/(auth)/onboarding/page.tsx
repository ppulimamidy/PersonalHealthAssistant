'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { ouraService } from '@/services/oura';
import { useAuthStore } from '@/stores/authStore';
import { Activity, CheckCircle, Circle, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';

const OuraLogo = () => (
  <svg viewBox="0 0 24 24" className="w-12 h-12" fill="currentColor">
    <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
    <circle cx="12" cy="12" r="4" />
  </svg>
);

export default function OnboardingPage() {
  const router = useRouter();
  const { setOuraConnection } = useAuthStore();
  const [step, setStep] = useState(1);
  const [isConnecting, setIsConnecting] = useState(false);

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
            Connect your Oura Ring to start tracking your health
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
            {step >= 2 ? (
              <CheckCircle className="w-6 h-6 text-primary-600" />
            ) : (
              <div className="w-6 h-6 rounded-full border-2 border-primary-600 flex items-center justify-center">
                <span className="text-xs font-bold text-primary-600">2</span>
              </div>
            )}
            <span className="text-sm font-medium text-slate-900">Connect Device</span>
          </div>
          <div className="w-12 h-0.5 bg-slate-200" />
          <div className="flex items-center gap-2">
            <Circle className="w-6 h-6 text-slate-300" />
            <span className="text-sm text-slate-500">Dashboard</span>
          </div>
        </div>

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
      </div>
    </div>
  );
}
