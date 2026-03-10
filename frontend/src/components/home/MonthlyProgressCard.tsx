'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { X } from 'lucide-react';

interface Props {
  mealsCount: number;
  symptomsCount: number;
  adherencePct: number;
  sleepDelta: number | null;
  month: string;
  onDismiss: () => void;
}

export function MonthlyProgressCard({
  mealsCount,
  symptomsCount,
  adherencePct,
  sleepDelta,
  month,
  onDismiss,
}: Props) {
  const nonZero = [mealsCount, symptomsCount, adherencePct, sleepDelta !== null ? 1 : 0].filter(
    (v) => v > 0
  ).length;

  const [visible, setVisible] = useState(true);

  useEffect(() => {
    try {
      const key = 'monthlyCard-' + new Date().toISOString().slice(0, 7);
      if (localStorage.getItem(key) === 'dismissed') setVisible(false);
    } catch { /* ignore */ }
  }, []);

  if (!visible || nonZero < 2) return null;

  const handleDismiss = () => {
    try {
      localStorage.setItem('monthlyCard-' + new Date().toISOString().slice(0, 7), 'dismissed');
    } catch { /* ignore */ }
    setVisible(false);
    onDismiss();
  };

  // Status message
  const isOnTrack = adherencePct >= 70 || (sleepDelta !== null && sleepDelta > 0);
  const statusMsg = isOnTrack
    ? 'On track — solid adherence and improving sleep'
    : 'Keep going — log consistently to see correlations';

  return (
    <div
      className="rounded-xl p-5"
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-semibold text-[#E8EDF5]">Your {month} recap</p>
        <button
          onClick={handleDismiss}
          className="text-[#3D4F66] hover:text-[#526380] transition-colors"
          aria-label="Dismiss"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Stats chips */}
      <div className="flex flex-wrap gap-2 mb-4">
        {mealsCount > 0 && (
          <span
            className="text-xs font-medium px-3 py-1 rounded-full"
            style={{ backgroundColor: 'rgba(251,146,60,0.1)', color: '#FB923C' }}
          >
            {mealsCount} meals
          </span>
        )}
        {adherencePct > 0 && (
          <span
            className="text-xs font-medium px-3 py-1 rounded-full"
            style={{ backgroundColor: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}
          >
            {Math.round(adherencePct)}% adherence
          </span>
        )}
        {symptomsCount > 0 && (
          <span
            className="text-xs font-medium px-3 py-1 rounded-full"
            style={{ backgroundColor: 'rgba(167,139,250,0.1)', color: '#A78BFA' }}
          >
            {symptomsCount} symptoms
          </span>
        )}
        {sleepDelta !== null && (
          <span
            className="text-xs font-medium px-3 py-1 rounded-full"
            style={{
              backgroundColor: sleepDelta >= 0 ? 'rgba(0,212,170,0.1)' : 'rgba(248,113,113,0.1)',
              color: sleepDelta >= 0 ? '#00D4AA' : '#F87171',
            }}
          >
            sleep {sleepDelta >= 0 ? '+' : ''}{sleepDelta.toFixed(0)}%
          </span>
        )}
      </div>

      {/* Status + CTA */}
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs" style={{ color: '#8B97A8' }}>
          {isOnTrack ? '🟢' : '📈'} {statusMsg}
        </p>
        <Link
          href="/doctor-prep?autogenerate=1&days=30"
          className="flex-shrink-0 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
          style={{ backgroundColor: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}
        >
          Share with doctor →
        </Link>
      </div>
    </div>
  );
}
