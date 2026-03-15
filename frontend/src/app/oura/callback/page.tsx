'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/services/api';

// useSearchParams() must be inside a Suspense boundary in Next.js App Router
function OuraCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    const error = searchParams.get('error');
    const code = searchParams.get('code');

    if (error) {
      setErrorMessage(
        error === 'access_denied'
          ? 'You declined the Oura authorization request.'
          : `Authorization error: ${error}`
      );
      setStatus('error');
      return;
    }

    if (!code) {
      setErrorMessage('No authorization code received from Oura.');
      setStatus('error');
      return;
    }

    api
      .post('/api/v1/oura/callback', { code })
      .then(() => {
        setStatus('success');
        setTimeout(() => {
          router.push('/devices');
        }, 2000);
      })
      .catch((err) => {
        const detail =
          err?.response?.data?.detail ?? 'Failed to connect your Oura Ring.';
        setErrorMessage(typeof detail === 'string' ? detail : JSON.stringify(detail));
        setStatus('error');
      });
  }, [searchParams, router]);

  return (
    <div
      className="rounded-2xl p-8 flex flex-col items-center gap-6 max-w-sm w-full mx-4"
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      {/* Oura icon */}
      <div
        className="w-16 h-16 rounded-2xl flex items-center justify-center"
        style={{ backgroundColor: 'rgba(129,140,248,0.12)' }}
      >
        <svg
          width="32"
          height="32"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#818CF8"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      </div>

      {status === 'loading' && (
        <>
          <div
            className="w-10 h-10 rounded-full border-2 animate-spin"
            style={{
              borderColor: 'rgba(129,140,248,0.2)',
              borderTopColor: '#818CF8',
            }}
          />
          <div className="text-center">
            <p className="text-lg font-semibold mb-1" style={{ color: '#E8EDF5' }}>
              Connecting Oura Ring…
            </p>
            <p className="text-sm" style={{ color: '#526380' }}>
              Exchanging authorization code. Please wait.
            </p>
          </div>
        </>
      )}

      {status === 'success' && (
        <>
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center"
            style={{ backgroundColor: 'rgba(110,231,183,0.12)' }}
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#6EE7B7"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <div className="text-center">
            <p className="text-lg font-semibold mb-1" style={{ color: '#E8EDF5' }}>
              Connected!
            </p>
            <p className="text-sm" style={{ color: '#526380' }}>
              Your Oura Ring is now linked. Redirecting to devices…
            </p>
          </div>
        </>
      )}

      {status === 'error' && (
        <>
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center"
            style={{ backgroundColor: 'rgba(248,113,113,0.12)' }}
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#F87171"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <div className="text-center">
            <p className="text-lg font-semibold mb-2" style={{ color: '#E8EDF5' }}>
              Connection failed
            </p>
            <p className="text-sm mb-5" style={{ color: '#526380' }}>
              {errorMessage}
            </p>
            <a
              href="/devices"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-opacity hover:opacity-80"
              style={{
                backgroundColor: 'rgba(129,140,248,0.12)',
                border: '1px solid rgba(129,140,248,0.25)',
                color: '#818CF8',
              }}
            >
              Back to Devices
            </a>
          </div>
        </>
      )}
    </div>
  );
}

export default function OuraCallbackPage() {
  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ backgroundColor: '#0A0F1A' }}
    >
      <Suspense
        fallback={
          <div
            className="w-10 h-10 rounded-full border-2 animate-spin"
            style={{
              borderColor: 'rgba(129,140,248,0.2)',
              borderTopColor: '#818CF8',
            }}
          />
        }
      >
        <OuraCallbackContent />
      </Suspense>
    </div>
  );
}
