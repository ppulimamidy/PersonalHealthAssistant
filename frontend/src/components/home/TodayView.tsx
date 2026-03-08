'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  Utensils,
  ClipboardList,
  Sparkles,
  CheckCircle2,
  Circle,
  X,
  ArrowRight,
  Cpu,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { healthScoreService } from '@/services/healthScore';
import { ouraService } from '@/services/oura';
import { insightsService } from '@/services/insights';
import { symptomsService } from '@/services/symptoms';
import { nutritionService } from '@/services/nutrition';
import { medicationsService } from '@/services/medications';
import { healthConditionsService } from '@/services/healthConditions';
import { HealthScoreRing } from '@/components/ui/HealthScoreRing';

const CHECKLIST_KEY = 'setup-checklist-dismissed';

// ── Greeting ─────────────────────────────────────────────────────────────────

function greeting(name: string) {
  const h = new Date().getHours();
  const time = h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening';
  return `Good ${time}, ${name}`;
}

function todayLabel() {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric',
  });
}

// ── Skeleton ──────────────────────────────────────────────────────────────────

function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`bg-white/5 rounded animate-pulse ${className}`} />;
}

// ── Card wrapper ──────────────────────────────────────────────────────────────

function Panel({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl p-5 ${className}`}
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      {children}
    </div>
  );
}

// ── Setup checklist ───────────────────────────────────────────────────────────

interface ChecklistProps {
  ouraActive: boolean;
  conditionsCount: number;
  medsCount: number;
  hasMeal: boolean;
  hasSymptom: boolean;
}

function SetupChecklist({
  ouraActive,
  conditionsCount,
  medsCount,
  hasMeal,
  hasSymptom,
}: ChecklistProps) {
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    try {
      if (localStorage.getItem(CHECKLIST_KEY) === 'true') setDismissed(true);
    } catch { /* ignore */ }
  }, []);

  const dismiss = () => {
    setDismissed(true);
    try { localStorage.setItem(CHECKLIST_KEY, 'true'); } catch { /* ignore */ }
  };

  const allDone = ouraActive && conditionsCount > 0 && medsCount > 0 && hasMeal && hasSymptom;

  if (dismissed || allDone) return null;

  const items = [
    { done: ouraActive, label: 'Connect a wearable device', href: '/devices' },
    { done: conditionsCount > 0, label: 'Add a health condition', href: '/health-profile' },
    { done: medsCount > 0, label: 'Add a medication', href: '/medications' },
    { done: hasMeal, label: 'Log your first meal', href: '/nutrition' },
    { done: hasSymptom, label: 'Log your first symptom', href: '/symptoms' },
  ];

  const completedCount = items.filter((i) => i.done).length;

  return (
    <Panel>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-sm font-semibold text-[#E8EDF5]">Getting started</h2>
          <p className="text-xs text-[#526380] mt-0.5">
            {completedCount}/{items.length} complete
          </p>
        </div>
        <button
          onClick={dismiss}
          className="text-[#3D4F66] hover:text-[#526380] transition-colors"
          aria-label="Dismiss"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Progress bar */}
      <div className="h-1 w-full rounded-full bg-white/5 mb-4 overflow-hidden">
        <div
          className="h-full rounded-full bg-[#00D4AA] transition-all duration-500"
          style={{ width: `${(completedCount / items.length) * 100}%` }}
        />
      </div>

      <div className="space-y-2">
        {items.map(({ done, label, href }) => (
          <Link
            key={label}
            href={href}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors duration-150 ${
              done
                ? 'opacity-50 pointer-events-none'
                : 'hover:bg-white/[0.04]'
            }`}
          >
            {done
              ? <CheckCircle2 className="w-4 h-4 text-[#00D4AA] flex-shrink-0" />
              : <Circle className="w-4 h-4 text-[#3D4F66] flex-shrink-0" />
            }
            <span className={`text-xs ${done ? 'text-[#3D4F66] line-through' : 'text-[#8B97A8]'}`}>
              {label}
            </span>
            {!done && <ArrowRight className="w-3.5 h-3.5 text-[#3D4F66] ml-auto" />}
          </Link>
        ))}
      </div>
    </Panel>
  );
}

// ── Quick log strip ───────────────────────────────────────────────────────────

function QuickLogStrip() {
  const actions = [
    { label: 'Log meal', href: '/nutrition', icon: Utensils, color: 'text-orange-400' },
    { label: 'Log symptom', href: '/symptoms', icon: ClipboardList, color: 'text-purple-400' },
    { label: 'Ask AI', href: '/agents', icon: Sparkles, color: 'text-[#00D4AA]' },
  ];

  return (
    <div className="grid grid-cols-3 gap-3">
      {actions.map(({ label, href, icon: Icon, color }) => (
        <Link
          key={label}
          href={href}
          className="flex flex-col items-center gap-2 py-4 rounded-xl transition-all duration-150 hover:scale-[1.02]"
          style={{
            backgroundColor: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.06)',
          }}
        >
          <Icon className={`w-5 h-5 ${color}`} />
          <span className="text-xs font-medium text-[#8B97A8]">{label}</span>
        </Link>
      ))}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function TodayView() {
  const { user, ouraConnection } = useAuthStore();
  const firstName = user?.name?.split(' ')[0] || 'there';

  // ── Queries ─────────────────────────────────────────────────────────────────

  const ouraActive = !!(ouraConnection?.is_active);

  const { data: healthScore, isLoading: scoreLoading } = useQuery({
    queryKey: ['health-score'],
    queryFn: healthScoreService.getScore,
    staleTime: 60_000,
    enabled: ouraActive,
  });

  const { data: timeline, isLoading: timelineLoading } = useQuery({
    queryKey: ['timeline', 1],
    queryFn: () => ouraService.getTimeline(14),
    staleTime: 60_000,
    enabled: ouraActive,
  });

  const { data: insights, isLoading: insightsLoading } = useQuery({
    queryKey: ['insights'],
    queryFn: insightsService.getInsights,
    staleTime: 60_000,
  });

  const { data: symptomsData } = useQuery({
    queryKey: ['symptoms', 7],
    queryFn: () => symptomsService.getSymptoms({ days: 7 }),
    staleTime: 60_000,
  });

  const { data: mealsData } = useQuery({
    queryKey: ['meals', 7],
    queryFn: () => nutritionService.listMeals(14),
    staleTime: 60_000,
  });

  const { data: medsData } = useQuery({
    queryKey: ['medications'],
    queryFn: medicationsService.getMedications,
    staleTime: 60_000,
  });

  const { data: conditions } = useQuery({
    queryKey: ['conditions'],
    queryFn: healthConditionsService.listConditions,
    staleTime: 60_000,
  });

  // ── Checklist data ───────────────────────────────────────────────────────────

  const todayEntry = timeline?.[0];
  const sleepScore = todayEntry?.sleep?.sleep_score ?? null;
  const activityScore = todayEntry?.activity?.activity_score ?? null;
  const readinessScore = todayEntry?.readiness?.readiness_score ?? null;

  const hasMeal = (mealsData?.items?.length ?? 0) > 0;
  const hasSymptom = (symptomsData?.symptoms?.length ?? 0) > 0;
  const conditionsCount = (conditions ?? []).filter((c) => c.is_active).length;
  const activeMeds = (medsData?.medications ?? []).filter((m) => m.is_active !== false);

  const latestInsight = insights?.[0];
  const lastSymptom = symptomsData?.symptoms?.[0];
  const lastMeal = mealsData?.items?.[0];

  // Show first active medication as a reminder
  const nextMed = activeMeds[0];

  // ── Render ────────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-bold text-[#E8EDF5]">{greeting(firstName)}</h1>
        <p className="text-sm text-[#526380] mt-0.5">{todayLabel()}</p>
      </div>

      {/* Health snapshot (Oura-connected) */}
      {ouraActive ? (
        <Panel>
          <h2 className="text-sm font-semibold text-[#8B97A8] mb-4">Today&apos;s Health Snapshot</h2>
          {scoreLoading || timelineLoading ? (
            <div className="flex gap-8 justify-center">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex flex-col items-center gap-2">
                  <Skeleton className="w-20 h-20 rounded-full" />
                  <Skeleton className="w-16 h-3" />
                </div>
              ))}
            </div>
          ) : (
            <div className="flex gap-6 flex-wrap justify-center">
              {healthScore?.score != null && (
                <HealthScoreRing score={healthScore.score} label="Overall" size="md" />
              )}
              {sleepScore != null && (
                <HealthScoreRing score={sleepScore} label="Sleep" size="md" />
              )}
              {activityScore != null && (
                <HealthScoreRing score={activityScore} label="Activity" size="md" />
              )}
              {readinessScore != null && (
                <HealthScoreRing score={readinessScore} label="Readiness" size="md" />
              )}
            </div>
          )}
        </Panel>
      ) : (
        /* No Oura — device connect prompt */
        <Panel>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#00D4AA]/10 flex items-center justify-center">
                <Cpu className="w-5 h-5 text-[#00D4AA]" />
              </div>
              <div>
                <p className="text-sm font-semibold text-[#E8EDF5]">Connect a device</p>
                <p className="text-xs text-[#526380] mt-0.5">
                  Unlock sleep, activity, and readiness scores
                </p>
              </div>
            </div>
            <Link
              href="/devices"
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-[#00D4AA] bg-[#00D4AA]/10 hover:bg-[#00D4AA]/20 transition-colors"
            >
              Connect →
            </Link>
          </div>
        </Panel>
      )}

      {/* Setup checklist */}
      <SetupChecklist
        ouraActive={ouraActive}
        conditionsCount={conditionsCount}
        medsCount={activeMeds.length}
        hasMeal={hasMeal}
        hasSymptom={hasSymptom}
      />

      {/* Quick log strip */}
      <QuickLogStrip />

      {/* Latest insight */}
      {(insightsLoading || latestInsight) && (
        <Panel>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-[#8B97A8]">Latest Insight</h2>
            <Link
              href="/insights"
              className="text-xs text-[#526380] hover:text-[#00D4AA] transition-colors"
            >
              View all →
            </Link>
          </div>
          {insightsLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-2/3" />
            </div>
          ) : latestInsight ? (
            <div>
              <p className="text-sm font-medium text-[#C8D5E8]">{latestInsight.title}</p>
              <p className="text-xs text-[#526380] mt-1 line-clamp-2">
                {latestInsight.summary}
              </p>
            </div>
          ) : null}
        </Panel>
      )}

      {/* Recent activity strip */}
      {(lastSymptom || lastMeal || nextMed) && (
        <Panel>
          <h2 className="text-sm font-semibold text-[#8B97A8] mb-3">Recent Activity</h2>
          <div className="space-y-2">
            {lastMeal && (
              <Link
                href="/nutrition"
                className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/[0.04] transition-colors"
              >
                <Utensils className="w-4 h-4 text-orange-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-[#C8D5E8] truncate">
                    {lastMeal.meal_name ?? lastMeal.meal_type ?? 'Meal'}
                  </p>
                  <p className="text-[10px] text-[#3D4F66]">
                    {lastMeal.timestamp
                      ? new Date(lastMeal.timestamp).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
                      : 'Recent'}
                  </p>
                </div>
              </Link>
            )}
            {lastSymptom && (
              <Link
                href="/symptoms"
                className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/[0.04] transition-colors"
              >
                <ClipboardList className="w-4 h-4 text-purple-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-[#C8D5E8] truncate">
                    {String(lastSymptom.symptom_type ?? 'Symptom')}
                  </p>
                  <p className="text-[10px] text-[#3D4F66]">
                    Severity {lastSymptom.severity ?? '—'}/10
                  </p>
                </div>
              </Link>
            )}
            {nextMed && (
              <Link
                href="/medications"
                className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/[0.04] transition-colors"
              >
                <div className="w-4 h-4 flex-shrink-0 flex items-center justify-center">
                  <span className="w-2 h-2 rounded-full bg-blue-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-[#C8D5E8] truncate">
                    {nextMed.medication_name}
                  </p>
                  <p className="text-[10px] text-[#3D4F66]">Next dose today</p>
                </div>
              </Link>
            )}
          </div>
        </Panel>
      )}
    </div>
  );
}
