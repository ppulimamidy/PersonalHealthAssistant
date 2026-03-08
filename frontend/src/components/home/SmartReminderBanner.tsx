'use client';

import { useState } from 'react';
import { X, Bell } from 'lucide-react';

const SESSION_KEY = 'smart-banner-dismissed';

interface SmartReminderBannerProps {
  medsNotLogged: number;
  totalMeds: number;
  hasMealToday: boolean;
  insightsStale: boolean;
}

export function SmartReminderBanner({
  medsNotLogged,
  totalMeds,
  hasMealToday,
  insightsStale,
}: SmartReminderBannerProps) {
  const [dismissed, setDismissed] = useState(() => {
    try {
      return sessionStorage.getItem(SESSION_KEY) === 'true';
    } catch {
      return false;
    }
  });

  if (dismissed) return null;

  // Priority: meds > meals > insights
  let message = '';
  if (medsNotLogged > 0 && totalMeds > 0) {
    message = `${medsNotLogged} of ${totalMeds} medication${totalMeds > 1 ? 's' : ''} not logged today`;
  } else if (!hasMealToday) {
    message = 'No meal logged today';
  } else if (insightsStale) {
    message = 'Your AI insights may be stale — check the Insights tab';
  }

  if (!message) return null;

  const handleDismiss = () => {
    try { sessionStorage.setItem(SESSION_KEY, 'true'); } catch { /* ignore */ }
    setDismissed(true);
  };

  return (
    <div
      className="flex items-center gap-3 rounded-xl px-4 py-3"
      style={{
        backgroundColor: 'rgba(0,212,170,0.06)',
        border: '1px solid rgba(0,212,170,0.2)',
        borderLeftWidth: '3px',
        borderLeftColor: '#00D4AA',
      }}
    >
      <Bell className="w-4 h-4 text-[#00D4AA] flex-shrink-0" />
      <p className="text-xs text-[#8B97A8] flex-1">{message}</p>
      <button
        onClick={handleDismiss}
        className="text-[#526380] hover:text-[#8B97A8] transition-colors"
        aria-label="Dismiss"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
