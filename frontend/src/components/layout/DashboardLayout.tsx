'use client';

import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { TopNav } from './TopNav';
import { HealthContextPanel } from './HealthContextPanel';
import { UpgradeModal } from '@/components/billing/UpgradeModal';
import { VitalsCheckinModal } from '@/components/home/VitalsCheckinModal';
import { WeeklyCheckinModal } from '@/components/home/WeeklyCheckinModal';
import { FloatingActionButton } from '@/components/ui/FloatingActionButton';
import { QuickSymptomModal } from '@/components/symptoms/QuickSymptomModal';

export function DashboardLayout({ children }: { readonly children: React.ReactNode }) {
  const { isLoading } = useAuth(true);
  const [showQuickSymptom, setShowQuickSymptom] = useState(false);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#080B10' }}>
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-transparent border-t-[#00D4AA] animate-spin" />
          <span className="text-xs text-[#526380] font-mono tracking-wider uppercase">Loading</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen transition-colors duration-200" style={{ backgroundColor: 'var(--bg-base)' }}>
      {/* Fixed top navigation */}
      <TopNav />

      {/* Fixed right context panel */}
      <HealthContextPanel />

      {/* Main content — offset below top nav (TopNav h-14 + optional SubNav h-10 = up to 24) */}
      <main className="pt-24 min-h-screen">
        <div className="max-w-5xl mx-auto px-8 py-8 animate-fade-in">
          {children}
        </div>
      </main>

      <UpgradeModal />
      <VitalsCheckinModal />
      <WeeklyCheckinModal />

      {/* Floating action button + quick symptom modal */}
      <FloatingActionButton onSymptomClick={() => setShowQuickSymptom(true)} />
      <QuickSymptomModal
        isOpen={showQuickSymptom}
        onClose={() => setShowQuickSymptom(false)}
      />
    </div>
  );
}
