'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  ChevronRight,
  ChevronLeft,
  Activity,
  Pill,
  Target,
  Plus,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { healthConditionsService } from '@/services/healthConditions';
import { medicationsService } from '@/services/medications';
import { healthTwinService } from '@/services/healthTwin';

const PANEL_KEY = 'health-panel-open';

// ── Skeleton loader ───────────────────────────────────────────────────────────

function SkeletonLine({ width = 'w-full' }: { width?: string }) {
  return (
    <div className={`h-3 rounded ${width} bg-white/5 animate-pulse`} />
  );
}

// ── Section wrapper ───────────────────────────────────────────────────────────

function Section({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5">
        <Icon className="w-3.5 h-3.5 text-[#3D4F66]" />
        <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[#3D4F66]">
          {title}
        </span>
      </div>
      {children}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function HealthContextPanel() {
  const [isOpen, setIsOpen] = useState(false);

  // Hydrate from localStorage after mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(PANEL_KEY);
      if (stored !== null) setIsOpen(stored === 'true');
    } catch {
      /* localStorage unavailable */
    }
  }, []);

  const toggle = () => {
    setIsOpen((prev) => {
      const next = !prev;
      try { localStorage.setItem(PANEL_KEY, String(next)); } catch { /* ignore */ }
      return next;
    });
  };

  const { user, profile } = useAuthStore();

  // ── Queries ─────────────────────────────────────────────────────────────────

  const { data: conditions, isLoading: condLoading } = useQuery({
    queryKey: ['conditions'],
    queryFn: healthConditionsService.listConditions,
    staleTime: 60_000,
    enabled: isOpen,
  });

  const { data: medsData, isLoading: medsLoading } = useQuery({
    queryKey: ['medications'],
    queryFn: medicationsService.getMedications,
    staleTime: 60_000,
    enabled: isOpen,
  });

  const { data: goals, isLoading: goalsLoading } = useQuery({
    queryKey: ['health-twin-goals', 'active'],
    queryFn: () => healthTwinService.getHealthTwinGoals('active'),
    staleTime: 60_000,
    enabled: isOpen,
  });

  // ── Derived data ─────────────────────────────────────────────────────────────

  const firstName = user?.name?.split(' ')[0] || 'User';

  const age = (() => {
    if (!profile?.date_of_birth) return profile?.age ?? null;
    const dob = new Date(profile.date_of_birth);
    const now = new Date();
    let a = now.getFullYear() - dob.getFullYear();
    const m = now.getMonth() - dob.getMonth();
    if (m < 0 || (m === 0 && now.getDate() < dob.getDate())) a--;
    return a;
  })();

  const bmi = (() => {
    if (!profile?.weight_kg || !profile?.height_cm) return null;
    const heightM = profile.height_cm / 100;
    return (profile.weight_kg / (heightM * heightM)).toFixed(1);
  })();

  const activeConditions = (conditions ?? []).filter((c) => c.is_active);
  const activeMeds = (medsData?.medications ?? []).filter((m) => m.is_active !== false);
  const topGoals = (goals ?? []).slice(0, 3);

  // ── Render ────────────────────────────────────────────────────────────────────

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={toggle}
        className="fixed right-0 top-1/2 -translate-y-1/2 z-30 w-5 h-16 flex items-center justify-center rounded-l-lg transition-all duration-200"
        style={{
          backgroundColor: '#0D1117',
          border: '1px solid rgba(255,255,255,0.06)',
          borderRight: 'none',
        }}
        title={isOpen ? 'Close health panel' : 'Open health panel'}
      >
        {isOpen
          ? <ChevronRight className="w-3 h-3 text-[#526380]" />
          : <ChevronLeft className="w-3 h-3 text-[#526380]" />
        }
      </button>

      {/* Panel */}
      <aside
        className="fixed top-0 right-0 h-full z-20 flex flex-col transition-transform duration-300 ease-in-out overflow-hidden"
        style={{
          width: '17rem',
          backgroundColor: '#0A0E14',
          borderLeft: '1px solid rgba(255,255,255,0.05)',
          transform: isOpen ? 'translateX(0)' : 'translateX(100%)',
        }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between h-14 px-4 flex-shrink-0"
          style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}
        >
          <span className="text-xs font-semibold text-[#8B97A8] uppercase tracking-widest">
            Health Context
          </span>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto py-4 px-4 space-y-5 scrollbar-thin">
          {/* User card */}
          <div
            className="rounded-xl p-3"
            style={{
              background: 'linear-gradient(135deg, rgba(0,212,170,0.07) 0%, rgba(255,255,255,0.02) 100%)',
              border: '1px solid rgba(0,212,170,0.12)',
            }}
          >
            <p className="text-sm font-semibold text-[#E8EDF5]">{firstName}</p>
            <div className="flex items-center gap-3 mt-1">
              {age !== null && (
                <span className="text-[11px] text-[#526380]">Age {age}</span>
              )}
              {bmi !== null && (
                <span className="text-[11px] text-[#526380]">BMI {bmi}</span>
              )}
              {age === null && bmi === null && (
                <span className="text-[11px] text-[#3D4F66]">Profile incomplete</span>
              )}
            </div>
          </div>

          {/* Active conditions */}
          <Section title="Conditions" icon={Activity}>
            {condLoading ? (
              <div className="space-y-1.5">
                <SkeletonLine width="w-3/4" />
                <SkeletonLine width="w-1/2" />
              </div>
            ) : activeConditions.length === 0 ? (
              <p className="text-[11px] text-[#3D4F66]">None tracked</p>
            ) : (
              <div className="space-y-1">
                {activeConditions.slice(0, 4).map((c) => (
                  <div
                    key={c.id}
                    className="flex items-center gap-2 px-2 py-1 rounded-lg"
                    style={{ backgroundColor: 'rgba(255,255,255,0.03)' }}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-[#00D4AA]/60 flex-shrink-0" />
                    <span className="text-[11px] text-[#8B97A8] truncate">
                      {c.condition_name}
                    </span>
                  </div>
                ))}
                {activeConditions.length > 4 && (
                  <p className="text-[10px] text-[#3D4F66] pl-2">
                    +{activeConditions.length - 4} more
                  </p>
                )}
              </div>
            )}
          </Section>

          {/* Active medications */}
          <Section title="Medications" icon={Pill}>
            {medsLoading ? (
              <div className="space-y-1.5">
                <SkeletonLine width="w-2/3" />
                <SkeletonLine width="w-1/2" />
              </div>
            ) : activeMeds.length === 0 ? (
              <p className="text-[11px] text-[#3D4F66]">None tracked</p>
            ) : (
              <div className="space-y-1">
                {activeMeds.slice(0, 4).map((m) => (
                  <div
                    key={m.id}
                    className="flex items-center gap-2 px-2 py-1 rounded-lg"
                    style={{ backgroundColor: 'rgba(255,255,255,0.03)' }}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400/60 flex-shrink-0" />
                    <span className="text-[11px] text-[#8B97A8] truncate">
                      {m.medication_name}
                    </span>
                  </div>
                ))}
                {activeMeds.length > 4 && (
                  <p className="text-[10px] text-[#3D4F66] pl-2">
                    +{activeMeds.length - 4} more
                  </p>
                )}
              </div>
            )}
          </Section>

          {/* Active goals */}
          <Section title="Goals" icon={Target}>
            {goalsLoading ? (
              <div className="space-y-1.5">
                <SkeletonLine width="w-4/5" />
                <SkeletonLine width="w-3/5" />
              </div>
            ) : topGoals.length === 0 ? (
              <p className="text-[11px] text-[#3D4F66]">No active goals</p>
            ) : (
              <div className="space-y-1">
                {topGoals.map((g) => (
                  <div
                    key={g.id}
                    className="px-2 py-1 rounded-lg"
                    style={{ backgroundColor: 'rgba(255,255,255,0.03)' }}
                  >
                    <p className="text-[11px] text-[#8B97A8] truncate">{g.goal_description}</p>
                    {g.target_date && (
                      <p className="text-[10px] text-[#3D4F66] mt-0.5">
                        Target: {new Date(g.target_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Section>
        </div>

        {/* Quick-log buttons */}
        <div
          className="px-4 py-3 space-y-2 flex-shrink-0"
          style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}
        >
          <Link
            href="/symptoms"
            className="flex items-center justify-center gap-2 w-full py-2 rounded-lg text-xs font-medium text-[#8B97A8] hover:text-[#00D4AA] transition-colors duration-150"
            style={{ backgroundColor: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
          >
            <Plus className="w-3.5 h-3.5" />
            Log symptom
          </Link>
          <Link
            href="/nutrition"
            className="flex items-center justify-center gap-2 w-full py-2 rounded-lg text-xs font-medium text-[#8B97A8] hover:text-[#00D4AA] transition-colors duration-150"
            style={{ backgroundColor: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
          >
            <Plus className="w-3.5 h-3.5" />
            Log meal
          </Link>
        </div>
      </aside>
    </>
  );
}
