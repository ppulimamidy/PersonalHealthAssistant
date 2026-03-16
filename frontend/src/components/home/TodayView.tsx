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
  Lightbulb,
  Users,
  FileText,
  Link2,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import type { InsightFollowUp } from '@/types';
import { api } from '@/services/api';
import { healthScoreService } from '@/services/healthScore';
import { ouraService } from '@/services/oura';
import { insightsService } from '@/services/insights';
import { symptomsService } from '@/services/symptoms';
import { nutritionService } from '@/services/nutrition';
import { medicationsService } from '@/services/medications';
import { healthConditionsService } from '@/services/healthConditions';
import { HealthScoreRing } from '@/components/ui/HealthScoreRing';
import { HealthRings, type RingData } from '@/components/ui/HealthRings';
import { ProgressSummaryCard } from './ProgressSummaryCard';
import { GoalsPanel } from './GoalsPanel';
import { CarePlanPanel } from './CarePlanPanel';
import { TrajectoryWidget } from './TrajectoryWidget';
import { DailyAdherenceStrip } from '@/components/medications/DailyAdherenceStrip';
import { SmartReminderBanner } from './SmartReminderBanner';
import { MonthlyProgressCard } from './MonthlyProgressCard';

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

// ── Provider home cards ───────────────────────────────────────────────────────

function ProviderHomeCards() {
  const cards = [
    {
      href: '/patients',
      icon: Users,
      color: '#818CF8',
      bg: 'rgba(129,140,248,0.08)',
      title: 'My Patients',
      sub: 'View your patient roster',
    },
    {
      href: '/doctor-prep',
      icon: FileText,
      color: '#00D4AA',
      bg: 'rgba(0,212,170,0.08)',
      title: 'Visit Prep',
      sub: 'Prepare for your next appointment',
    },
  ];
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wider text-[#526380] mb-3">
        Provider Tools
      </p>
      <div className="grid grid-cols-2 gap-3">
        {cards.map(({ href, icon: Icon, color, bg, title, sub }) => (
          <Link
            key={href}
            href={href}
            className="flex items-center gap-3 p-4 rounded-xl transition-all hover:scale-[1.02]"
            style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
          >
            <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: bg }}>
              <Icon className="w-4 h-4" style={{ color }} />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-[#E8EDF5] truncate">{title}</p>
              <p className="text-xs text-[#526380] mt-0.5 truncate">{sub}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

// ── Caregiver home cards ──────────────────────────────────────────────────────

function CaregiverHomeCards() {
  const { data: sharingData } = useQuery({
    queryKey: ['sharing', 'links'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/sharing/links');
      return data;
    },
    staleTime: 5 * 60_000,
  });

  const hasSharing = Array.isArray(sharingData)
    ? sharingData.length > 0
    : ((sharingData as { links?: unknown[] } | null)?.links?.length ?? 0) > 0;

  if (hasSharing) return null;

  return (
    <div
      className="flex items-start gap-3 p-4 rounded-xl"
      style={{ backgroundColor: 'rgba(129,140,248,0.06)', border: '1px solid rgba(129,140,248,0.2)' }}
    >
      <Link2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-indigo-400" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-[#E8EDF5]">Connect with your care recipient</p>
        <p className="text-xs text-[#526380] mt-0.5">
          Set up sharing so you can monitor their health data
        </p>
      </div>
      <Link
        href="/sharing"
        className="text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors whitespace-nowrap"
      >
        Set up →
      </Link>
    </div>
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
          className="flex flex-col items-center gap-2.5 p-5 rounded-xl transition-all duration-150 hover:scale-[1.02]"
          style={{
            backgroundColor: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.06)',
          }}
        >
          <Icon className={`w-6 h-6 ${color}`} />
          <span className="text-sm font-medium text-[#8B97A8]">{label}</span>
        </Link>
      ))}
    </div>
  );
}

// ── Insight follow-up banner ──────────────────────────────────────────────────

function InsightFollowUpBanner({ followups }: { followups: InsightFollowUp[] }) {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed || followups.length === 0) return null;
  const count = followups.length;
  const hasBetter = followups.some((f) => f.direction === 'better');
  const hasWorse = followups.some((f) => f.direction === 'worse');
  const sentiment = hasWorse ? 'worse' : hasBetter ? 'better' : 'stable';
  const color = sentiment === 'better' ? '#00D4AA' : sentiment === 'worse' ? '#F87171' : '#FBB124';
  const bgColor = sentiment === 'better' ? 'rgba(0,212,170,0.06)' : sentiment === 'worse' ? 'rgba(248,113,113,0.06)' : 'rgba(251,177,36,0.06)';
  const borderColor = sentiment === 'better' ? 'rgba(0,212,170,0.2)' : sentiment === 'worse' ? 'rgba(248,113,113,0.2)' : 'rgba(251,177,36,0.2)';

  return (
    <div className="flex items-start gap-3 p-4 rounded-xl"
      style={{ backgroundColor: bgColor, border: `1px solid ${borderColor}` }}>
      <Lightbulb className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color }} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium" style={{ color: '#E8EDF5' }}>
          {count === 1 ? '1 finding' : `${count} findings`} from ~30 days ago — see what changed
        </p>
        <p className="text-xs mt-0.5 line-clamp-1" style={{ color: '#8B97A8' }}>
          {followups.slice(0, 2).map((f) => f.label).join(', ')}
          {count > 2 ? ` +${count - 2} more` : ''}
        </p>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <Link href="/insights" className="text-xs font-medium underline" style={{ color }}>
          View →
        </Link>
        <button onClick={() => setDismissed(true)} className="p-0.5 rounded"
          style={{ color: '#526380' }}>
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function TodayView() {
  const { user, profile, ouraConnection } = useAuthStore();
  const firstName = user?.name?.split(' ')[0] || 'there';
  const userRole = profile?.user_role ?? 'patient';

  // ── Queries ─────────────────────────────────────────────────────────────────

  const ouraActive = !!(ouraConnection?.is_active);

  const { data: healthScore, isLoading: scoreLoading } = useQuery({
    queryKey: ['health-score'],
    queryFn: healthScoreService.getScore,
    staleTime: 60_000,
    enabled: ouraActive,
  });

  const { data: summariesData } = useQuery({
    queryKey: ['health-summaries'],
    queryFn: async () => {
      try {
        const { data: resp } = await api.get('/api/v1/health-data/summaries');
        return resp as Record<string, { latest_value: number | null; avg_30d: number | null }>;
      } catch {
        return null;
      }
    },
    staleTime: 5 * 60_000,
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

  const { data: symptoms28d } = useQuery({
    queryKey: ['symptoms', 28],
    queryFn: () => symptomsService.getSymptoms({ days: 28 }),
    staleTime: 60_000,
  });

  const { data: adherenceStats } = useQuery({
    queryKey: ['adherence-stats'],
    queryFn: () => medicationsService.getAdherenceStats(30),
    staleTime: 60_000,
  });

  const { data: todayAdherence } = useQuery({
    queryKey: ['adherence-today'],
    queryFn: medicationsService.getTodayAdherence,
    staleTime: 30_000,
  });

  const { data: followups } = useQuery({
    queryKey: ['insight-followups'],
    queryFn: insightsService.getFollowups,
    staleTime: 5 * 60_000,
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

  // Smart banner data
  const todayMeds = todayAdherence?.medications ?? [];
  const medsNotLogged = todayMeds.filter((m) => m.logs.length === 0).length;
  const hasMealToday = (() => {
    const today = new Date().toISOString().slice(0, 10);
    return (mealsData?.items ?? []).some((m) => m.timestamp?.startsWith(today));
  })();
  const latestInsightDate = insights?.[0]?.created_at;
  const insightsStale = latestInsightDate
    ? (Date.now() - new Date(latestInsightDate).getTime()) / (1000 * 60 * 60 * 24) > 7
    : false;

  // ── Sleep delta (for MonthlyProgressCard) ────────────────────────────────────

  const sleepDelta: number | null = (() => {
    if (!timeline || timeline.length < 8) return null;
    const avg = (arr: (number | null | undefined)[]) => {
      const valid = arr.filter((v): v is number => v != null);
      return valid.length ? valid.reduce((a, b) => a + b, 0) / valid.length : null;
    };
    const recent = avg(timeline.slice(0, 7).map((e) => e.sleep?.sleep_score));
    const prev = avg(timeline.slice(7, 14).map((e) => e.sleep?.sleep_score));
    if (recent == null || prev == null || prev === 0) return null;
    return ((recent - prev) / prev) * 100;
  })();

  // ── Derived state for Doctor Prep card + streak ───────────────────────────────

  const currentMonth = new Date().toISOString().slice(0, 7);
  const [doctorPrepDismissed, setDoctorPrepDismissed] = useState(false);
  useEffect(() => {
    try {
      if (localStorage.getItem('doctorPrepCard-' + currentMonth) === 'dismissed') {
        setDoctorPrepDismissed(true);
      }
    } catch { /* ignore */ }
  }, [currentMonth]);
  const showDoctorPrepCard = !doctorPrepDismissed && (insights?.length ?? 0) >= 3;

  // Streak: prefer adherenceStats.current_streak, fall back to todayAdherence
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const currentStreak: number = (adherenceStats as any)?.current_streak ?? (todayAdherence as any)?.current_streak ?? 0;

  // ── Render ────────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Greeting + streak badge */}
      <div>
        <div className="flex items-center gap-2 flex-wrap">
          <h1 className="text-2xl font-bold text-[#E8EDF5]">{greeting(firstName)}</h1>
          {currentStreak > 1 && (
            <span
              className="text-xs font-medium px-2 py-0.5 rounded-full"
              style={{ backgroundColor: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}
            >
              {currentStreak}-day streak
            </span>
          )}
        </div>
        <p className="text-sm text-[#526380] mt-0.5">{todayLabel()}</p>
      </div>

      {/* Role-specific quick-access cards */}
      {userRole === 'provider' && <ProviderHomeCards />}
      {userRole === 'caregiver' && <CaregiverHomeCards />}

      {/* Daily adherence strip — time-sensitive, near top */}
      <DailyAdherenceStrip />

      {/* Quick log strip — primary daily action */}
      <QuickLogStrip />

      {/* Smart reminder banner */}
      <SmartReminderBanner
        medsNotLogged={medsNotLogged}
        totalMeds={todayMeds.length}
        hasMealToday={hasMealToday}
        insightsStale={insightsStale}
      />

      {/* Insight follow-up banner */}
      <InsightFollowUpBanner followups={followups ?? []} />

      {/* Monthly progress recap card */}
      <MonthlyProgressCard
        mealsCount={mealsData?.items?.length ?? 0}
        symptomsCount={symptoms28d?.symptoms?.length ?? 0}
        adherencePct={(adherenceStats as any)?.adherence_pct ?? 0}
        sleepDelta={sleepDelta}
        month={new Date().toLocaleString('en-US', { month: 'long' })}
        onDismiss={() => {/* state managed internally by MonthlyProgressCard */}}
      />

      {/* Health snapshot — rings when summaries available, score rings otherwise */}
      {(ouraActive || (summariesData && Object.keys(summariesData).length > 0)) ? (
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
          ) : summariesData && Object.keys(summariesData).length > 0 ? (
            <HealthRings
              data={{
                sleep: { value: summariesData.sleep?.latest_value ?? 0, goal: 8 },
                heart: { value: summariesData.hrv_sdnn?.latest_value ?? 0, goal: Math.max((summariesData.hrv_sdnn?.avg_30d ?? 50) * 1.1, 50) },
                activity: { value: summariesData.steps?.latest_value ?? 0, goal: 8000 },
                recovery: { value: healthScore?.score ?? (readinessScore ?? 0), goal: 100 },
                overallScore: healthScore?.score ?? null,
              }}
              size={200}
            />
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

      {/* Health trajectory composite score */}
      <TrajectoryWidget />

      {/* Progress summary card */}
      <ProgressSummaryCard
        timeline={timeline ?? undefined}
        symptomsData={symptoms28d ?? undefined}
        adherenceStats={adherenceStats ?? undefined}
        healthScore={undefined}
      />

      {/* Care Plan */}
      <CarePlanPanel
        ouraSteps={(() => {
          const steps = (timeline ?? []).slice(0, 7).map((e) => e.activity?.steps).filter((s): s is number => s != null);
          return steps.length ? Math.round(steps.reduce((a, b) => a + b, 0) / steps.length) : undefined;
        })()}
        ouraSlpScore={timeline?.[0]?.sleep?.sleep_score ?? undefined}
      />

      {/* Goals */}
      <GoalsPanel />

      {/* Doctor Prep contextual card — shows when ≥3 insights this month */}
      {showDoctorPrepCard && (
        <Panel>
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase" style={{ color: '#00D4AA' }}>
                Appointment Ready
              </p>
              <p className="font-medium text-[#E8EDF5] mt-1">
                {insights?.length} insight{insights?.length !== 1 ? 's' : ''} from the past 30 days
              </p>
              <p className="text-sm mt-0.5" style={{ color: '#8B97A8' }}>
                Generate a structured report to share with your doctor.
              </p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <Link
                href="/doctor-prep?autogenerate=1&days=30"
                className="px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap"
                style={{ backgroundColor: '#00D4AA', color: '#080B10' }}
              >
                Prepare report
              </Link>
              <button
                onClick={() => {
                  try { localStorage.setItem('doctorPrepCard-' + currentMonth, 'dismissed'); } catch { /* ignore */ }
                  setDoctorPrepDismissed(true);
                }}
                className="text-xs"
                style={{ color: '#526380' }}
              >
                Not now
              </button>
            </div>
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
