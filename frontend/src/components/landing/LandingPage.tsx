'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import {
  Activity,
  Brain,
  FileText,
  Pill,
  Zap,
  Check,
  ArrowRight,
  Utensils,
  ClipboardList,
  Sparkles,
  TrendingUp,
  Cpu,
  ChevronRight,
  FlaskConical,
  Users,
  Target,
  User,
  Stethoscope,
} from 'lucide-react';
import { PricingSection } from './PricingSection';
import { BetaSignupForm } from './BetaSignupForm';

// ── Design tokens (match the app's dark system) ─────────────────────────────
const BG_BASE     = '#080B10';
const BG_SURFACE  = '#12161D';
const BG_RAISED   = '#161B24';
const BORDER      = 'rgba(255,255,255,0.06)';
const BORDER_MED  = 'rgba(255,255,255,0.10)';
const ACCENT      = '#00D4AA';
const ACCENT_BG   = 'rgba(0,212,170,0.10)';
const TEXT_1      = '#E8EDF5';
const TEXT_2      = '#8B97A8';
const TEXT_3      = '#526380';

// ── Features ────────────────────────────────────────────────────────────────

const features = [
  {
    icon: Activity,
    title: 'Smart Health Timeline',
    description: 'Sleep, activity, and readiness trends in one view. Compare last 14 days to your 30-day baseline.',
    color: 'text-[#00D4AA]',
    bg: 'rgba(0,212,170,0.08)',
  },
  {
    icon: Brain,
    title: 'AI-Powered Insights',
    description: 'Personalised insights that explain the "why" behind your trends — connecting sleep, glucose, symptoms, and medications into one picture.',
    color: 'text-violet-400',
    bg: 'rgba(139,92,246,0.08)',
  },
  {
    icon: FlaskConical,
    title: 'Lab Results & Biomarkers',
    description: 'Enter or scan your labs. AI flags abnormal values instantly and tracks every biomarker over time — glucose, LDL, TSH, and 50+ more.',
    color: 'text-cyan-400',
    bg: 'rgba(34,211,238,0.08)',
  },
  {
    icon: Target,
    title: 'Care Plans & Goals',
    description: 'Set clinical care plan targets — weight, adherence, blood pressure. Track progress daily. Doctors can prescribe goals directly to your app.',
    color: 'text-pink-400',
    bg: 'rgba(244,114,182,0.08)',
  },
  {
    icon: FileText,
    title: 'Doctor Visit Prep',
    description: 'Generate a clinician-ready 30-day summary before every appointment — adherence stats, lab highlights, AI-suggested questions. One click, PDF ready.',
    color: 'text-blue-400',
    bg: 'rgba(96,165,250,0.08)',
  },
  {
    icon: Users,
    title: 'Care Team Sharing',
    description: 'Share your full health record with your doctor, nutritionist, or family — granular permissions, no account required on their end. Revoke any time.',
    color: 'text-indigo-400',
    bg: 'rgba(129,140,248,0.08)',
  },
  {
    icon: Utensils,
    title: 'Nutrition Tracking',
    description: 'Log meals by photo scan. Get calories, macros, and AI-analysed meal patterns — including correlations with your symptoms and energy levels.',
    color: 'text-orange-400',
    bg: 'rgba(251,146,60,0.08)',
  },
  {
    icon: Pill,
    title: 'Medications & Symptoms',
    description: 'Track every medication, dosage, and adherence streak. Log symptoms with severity and triggers. AI surfaces correlations between what you take and how you feel.',
    color: 'text-red-400',
    bg: 'rgba(248,113,113,0.08)',
  },
  {
    icon: Sparkles,
    title: 'AI Health Agents',
    description: '5 specialised agents — Cardiologist, Nutritionist, Sleep Analyst, Endocrinologist, and more. Ask anything, get evidence-backed answers.',
    color: 'text-yellow-400',
    bg: 'rgba(250,204,21,0.08)',
  },
];

// ── Demo steps ───────────────────────────────────────────────────────────────

const demoSteps = [
  {
    label: 'Set Up',
    time: '0–60 s',
    title: 'Sign up, connect your device, start logging',
    description: 'Create your account in 30 seconds. Connect your Oura Ring or log manually. Your personalised dashboard is ready instantly.',
    ctas: ['Connect Oura', 'Log a meal', 'Log a symptom'],
  },
  {
    label: 'Insights',
    time: '60–120 s',
    title: 'Your health at a glance — scored and explained',
    description: 'See today\'s sleep, activity, and readiness scores. The AI surfaces 3 high-signal insights: what changed, why it matters, and what to watch.',
    ctas: ['Sleep breakdown', '14-day trend', 'AI explains why'],
  },
  {
    label: 'Doctor Prep',
    time: '120–180 s',
    title: 'One-click report for your next appointment',
    description: 'Generate a clinician-ready summary of your last 30 days. Share trends, medications, symptoms, and suggested questions — in seconds.',
    ctas: ['Export PDF', 'Share with doctor', 'Share with family'],
  },
];

// ── Demo Mockups ─────────────────────────────────────────────────────────────

function DemoStep0() {
  return (
    <div className="space-y-4">
      {/* Greeting row */}
      <div>
        <p className="text-lg font-semibold" style={{ color: TEXT_1, fontFamily: 'Syne, sans-serif' }}>Good morning, Sarah</p>
        <p className="text-xs" style={{ color: TEXT_3 }}>Sunday, March 8</p>
      </div>
      {/* Connect device card */}
      <div className="rounded-xl p-4 flex items-center justify-between" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ backgroundColor: ACCENT_BG }}>
            <Cpu className="w-4 h-4" style={{ color: ACCENT }} />
          </div>
          <div>
            <p className="text-sm font-medium" style={{ color: TEXT_1 }}>Connect a device</p>
            <p className="text-xs" style={{ color: TEXT_3 }}>Unlock sleep & readiness scores</p>
          </div>
        </div>
        <span className="text-xs font-medium px-3 py-1 rounded-lg" style={{ color: ACCENT, backgroundColor: ACCENT_BG }}>Connect →</span>
      </div>
      {/* Checklist */}
      <div className="rounded-xl p-4" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-semibold" style={{ color: TEXT_1 }}>Getting started</p>
          <p className="text-xs" style={{ color: TEXT_3 }}>0/5 complete</p>
        </div>
        <div className="h-1 rounded-full mb-3" style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}>
          <div className="h-full rounded-full w-0" style={{ backgroundColor: ACCENT }} />
        </div>
        {[
          'Connect a wearable device',
          'Add a health condition',
          'Add a medication',
          'Log your first meal',
          'Log your first symptom',
        ].map((item) => (
          <div key={item} className="flex items-center gap-2 py-1.5">
            <div className="w-3.5 h-3.5 rounded-full border flex-shrink-0" style={{ borderColor: TEXT_3 }} />
            <span className="text-xs" style={{ color: TEXT_2 }}>{item}</span>
            <ChevronRight className="w-3 h-3 ml-auto" style={{ color: TEXT_3 }} />
          </div>
        ))}
      </div>
      {/* Quick log strip */}
      <div className="grid grid-cols-3 gap-2">
        {[
          { label: 'Log meal', icon: Utensils, color: 'text-orange-400' },
          { label: 'Log symptom', icon: ClipboardList, color: 'text-purple-400' },
          { label: 'Ask AI', icon: Sparkles, color: 'text-[#00D4AA]' },
        ].map(({ label, icon: Icon, color }) => (
          <div key={label} className="flex flex-col items-center gap-1.5 py-3 rounded-xl" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
            <Icon className={`w-4 h-4 ${color}`} />
            <span className="text-[10px]" style={{ color: TEXT_2 }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DemoStep1() {
  const scores = [
    { label: 'Overall', value: 88, color: ACCENT, bg: 'rgba(0,212,170,0.15)' },
    { label: 'Sleep', value: 85, color: '#818cf8', bg: 'rgba(129,140,248,0.15)' },
    { label: 'Activity', value: 92, color: '#4ade80', bg: 'rgba(74,222,128,0.15)' },
    { label: 'Readiness', value: 78, color: '#fbbf24', bg: 'rgba(251,191,36,0.15)' },
  ];
  return (
    <div className="space-y-4">
      <p className="text-sm font-semibold" style={{ color: TEXT_2 }}>Today&apos;s Health Snapshot</p>
      {/* Score rings */}
      <div className="rounded-xl p-4" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
        <div className="flex justify-around">
          {scores.map(({ label, value, color, bg }) => (
            <div key={label} className="flex flex-col items-center gap-1">
              <div className="w-14 h-14 rounded-full flex items-center justify-center" style={{ backgroundColor: bg, border: `2px solid ${color}` }}>
                <span className="text-base font-bold font-data" style={{ color }}>{value}</span>
              </div>
              <span className="text-[10px]" style={{ color: TEXT_3 }}>{label}</span>
            </div>
          ))}
        </div>
      </div>
      {/* Insights */}
      <div className="rounded-xl p-4" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-semibold" style={{ color: TEXT_2 }}>Latest Insight</p>
          <span className="text-xs" style={{ color: TEXT_3 }}>View all →</span>
        </div>
        <p className="text-sm font-medium mb-1" style={{ color: TEXT_1 }}>Sleep efficiency dropped 12% this week</p>
        <p className="text-xs line-clamp-2" style={{ color: TEXT_3 }}>Your deep sleep has been shorter than your 30-day baseline on 4 of the last 7 nights, coinciding with later meal times. Consider finishing dinner 2–3 hours before bedtime.</p>
      </div>
      {/* Trend mini chart */}
      <div className="rounded-xl p-4" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
        <p className="text-xs font-semibold mb-3" style={{ color: TEXT_3 }}>14-DAY SLEEP TREND</p>
        <div className="flex items-end gap-1 h-12">
          {[72,78,85,80,75,88,85,82,79,84,87,81,85,85].map((v, i) => (
            <div key={i} className="flex-1 rounded-sm" style={{ height: `${(v / 100) * 100}%`, backgroundColor: i >= 12 ? ACCENT : 'rgba(0,212,170,0.3)' }} />
          ))}
        </div>
      </div>
    </div>
  );
}

function DemoStep2() {
  return (
    <div className="space-y-4">
      <p className="text-sm font-semibold" style={{ color: TEXT_2 }}>Doctor Visit Prep</p>
      {/* Report card */}
      <div className="rounded-xl p-4" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(96,165,250,0.1)' }}>
            <FileText className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <p className="text-sm font-semibold" style={{ color: TEXT_1 }}>30-Day Health Summary</p>
            <p className="text-xs" style={{ color: TEXT_3 }}>Ready for Dr. Johnson · Mar 8, 2026</p>
          </div>
        </div>
        {[
          { label: 'Average sleep score', value: '83 / 100', delta: '−5 vs baseline' },
          { label: 'Active days', value: '18 / 30', delta: '+2 vs baseline' },
          { label: 'Symptoms logged', value: '7 events', delta: 'headache × 3, fatigue × 4' },
          { label: 'Medications', value: '2 active', delta: 'Metformin, Lisinopril' },
        ].map(({ label, value, delta }) => (
          <div key={label} className="flex items-center justify-between py-2" style={{ borderBottom: `1px solid ${BORDER}` }}>
            <span className="text-xs" style={{ color: TEXT_2 }}>{label}</span>
            <div className="text-right">
              <span className="text-xs font-medium" style={{ color: TEXT_1 }}>{value}</span>
              <p className="text-[10px]" style={{ color: TEXT_3 }}>{delta}</p>
            </div>
          </div>
        ))}
      </div>
      {/* Questions to ask */}
      <div className="rounded-xl p-4" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
        <p className="text-xs font-semibold mb-3" style={{ color: TEXT_3 }}>AI-GENERATED QUESTIONS TO ASK</p>
        {[
          'Could reduced sleep quality be related to Metformin timing?',
          'Should I adjust my activity level given the fatigue pattern?',
        ].map((q) => (
          <div key={q} className="flex items-start gap-2 py-1.5">
            <div className="w-4 h-4 rounded-full flex-shrink-0 flex items-center justify-center mt-0.5" style={{ backgroundColor: ACCENT_BG }}>
              <Sparkles className="w-2.5 h-2.5" style={{ color: ACCENT }} />
            </div>
            <p className="text-xs" style={{ color: TEXT_2 }}>{q}</p>
          </div>
        ))}
      </div>
      {/* Export button */}
      <div className="flex gap-2">
        <div className="flex-1 text-center py-2 rounded-lg text-xs font-medium" style={{ backgroundColor: ACCENT, color: '#000' }}>Export PDF</div>
        <div className="flex-1 text-center py-2 rounded-lg text-xs font-medium" style={{ backgroundColor: 'rgba(255,255,255,0.04)', border: `1px solid ${BORDER_MED}`, color: TEXT_2 }}>Share Link</div>
      </div>
    </div>
  );
}

const DEMO_PANELS = [DemoStep0, DemoStep1, DemoStep2];

// ── Who It's For data ────────────────────────────────────────────────────────

const WHO_ITS_FOR = [
  {
    icon: User,
    title: 'Patients',
    subtitle: 'Managing your own health',
    points: [
      'Wearable + labs + symptoms in one place',
      'AI explains what your data means',
      'Doctor visit prep in one click',
      'Care plan goals — set by you or your provider',
    ],
    color: ACCENT,
    bg: ACCENT_BG,
  },
  {
    icon: Users,
    title: 'Caregivers',
    subtitle: 'Supporting a loved one',
    points: [
      'View health data your family member shares',
      'See their medications, labs, and symptoms',
      'Dedicated Family tab in your dashboard',
      'Privacy-first: revocable access at any time',
    ],
    color: '#818cf8',
    bg: 'rgba(129,140,248,0.10)',
  },
  {
    icon: Stethoscope,
    title: 'Healthcare Providers',
    subtitle: 'Monitoring your patients',
    points: [
      'Patients share access via a secure token',
      'Review care plans, labs, and goal progress',
      'Alerts when metrics drift out of range',
      'Pin clinical instructions to the patient app',
    ],
    color: '#60a5fa',
    bg: 'rgba(96,165,250,0.10)',
  },
];

// ── Main Component ───────────────────────────────────────────────────────────

export function LandingPage() {
  const [activeStep, setActiveStep] = useState(0);
  const DemoPanel = DEMO_PANELS[activeStep];

  return (
    <div className="min-h-screen" style={{ backgroundColor: BG_BASE, color: TEXT_1 }}>

      {/* ── Nav ─────────────────────────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 h-14 flex items-center px-6" style={{ backgroundColor: 'rgba(8,11,16,0.85)', backdropFilter: 'blur(12px)', borderBottom: `1px solid ${BORDER}` }}>
        <div className="max-w-6xl mx-auto w-full flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-7 h-7" style={{ color: ACCENT }} />
            <span className="text-lg font-bold" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1 }}>HealthAssist</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#demo" className="text-sm hidden sm:block" style={{ color: TEXT_2 }}>Demo</a>
            <a href="#features" className="text-sm hidden sm:block" style={{ color: TEXT_2 }}>Features</a>
            <a href="#pricing" className="text-sm hidden sm:block" style={{ color: TEXT_2 }}>Pricing</a>
            <Link href="/login">
              <button className="text-sm font-medium" style={{ color: TEXT_2 }}>Log in</button>
            </Link>
            <Link href="/signup">
              <button className="px-4 py-1.5 rounded-lg text-sm font-semibold transition-all hover:brightness-110" style={{ backgroundColor: ACCENT, color: '#000' }}>
                Get Started
              </button>
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <section className="pt-36 pb-24 px-6 text-center relative overflow-hidden">
        {/* Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full pointer-events-none" style={{ background: 'radial-gradient(ellipse, rgba(0,212,170,0.07) 0%, transparent 70%)', filter: 'blur(40px)' }} />
        <div className="max-w-4xl mx-auto relative">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium mb-8" style={{ backgroundColor: ACCENT_BG, border: `1px solid rgba(0,212,170,0.2)`, color: ACCENT }}>
            <Zap className="w-3 h-3" />
            Private beta — limited early access
          </div>
          <h1 className="text-5xl md:text-6xl font-bold leading-tight mb-6" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1, letterSpacing: '-0.02em' }}>
            Understand your health<br />
            <span style={{ color: ACCENT }}>before</span> it becomes a problem
          </h1>
          <p className="text-xl max-w-2xl mx-auto mb-10" style={{ color: TEXT_2 }}>
            Your wearables, lab results, symptoms, and medications — connected by AI into a single picture of your health.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/signup">
              <button className="flex items-center gap-2 px-6 py-3 rounded-xl text-base font-semibold transition-all hover:brightness-110" style={{ backgroundColor: ACCENT, color: '#000' }}>
                Join the private beta
                <ArrowRight className="w-4 h-4" />
              </button>
            </Link>
            <a href="#demo">
              <button className="flex items-center gap-2 px-6 py-3 rounded-xl text-base font-medium transition-all" style={{ backgroundColor: 'rgba(255,255,255,0.04)', border: `1px solid ${BORDER_MED}`, color: TEXT_2 }}>
                See the 3-minute demo
              </button>
            </a>
          </div>
          {/* Role pills */}
          <div className="flex items-center justify-center gap-2 mt-8 flex-wrap">
            <span className="text-xs" style={{ color: TEXT_3 }}>Built for:</span>
            {[
              { label: 'Patients', icon: User },
              { label: 'Caregivers', icon: Users },
              { label: 'Healthcare Providers', icon: Stethoscope },
            ].map(({ label, icon: Icon }) => (
              <span key={label} className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium" style={{ backgroundColor: 'rgba(255,255,255,0.04)', border: `1px solid ${BORDER_MED}`, color: TEXT_2 }}>
                <Icon className="w-3 h-3" />
                {label}
              </span>
            ))}
          </div>
          <p className="mt-4 text-xs" style={{ color: TEXT_3 }}>Not medical advice. Designed to support better clinician conversations.</p>
        </div>
      </section>

      {/* ── 3-Minute Demo Flow ──────────────────────────────────────────── */}
      <section className="py-20 px-6" id="demo">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: ACCENT }}>3-Minute Demo</p>
            <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1 }}>From sign-up to insights in 3 minutes</h2>
            <p className="text-lg" style={{ color: TEXT_2 }}>Click through each step to see the actual app experience</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
            {/* Left — steps */}
            <div className="space-y-3">
              {demoSteps.map((step, i) => {
                const active = activeStep === i;
                return (
                  <button
                    key={i}
                    onClick={() => setActiveStep(i)}
                    className="w-full text-left rounded-2xl p-5 transition-all duration-200"
                    style={{
                      backgroundColor: active ? 'rgba(0,212,170,0.07)' : 'rgba(255,255,255,0.02)',
                      border: `1px solid ${active ? 'rgba(0,212,170,0.25)' : BORDER}`,
                    }}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full flex-shrink-0 flex items-center justify-center font-bold text-sm" style={{ backgroundColor: active ? ACCENT : 'rgba(255,255,255,0.05)', color: active ? '#000' : TEXT_3, fontFamily: 'Syne, sans-serif' }}>
                        {i + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-xs font-semibold" style={{ color: active ? ACCENT : TEXT_3 }}>{step.label}</span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ backgroundColor: 'rgba(255,255,255,0.04)', color: TEXT_3 }}>{step.time}</span>
                        </div>
                        <p className="text-sm font-semibold" style={{ color: active ? TEXT_1 : TEXT_2 }}>{step.title}</p>
                        {active && (
                          <p className="text-xs mt-2" style={{ color: TEXT_3 }}>{step.description}</p>
                        )}
                      </div>
                    </div>
                    {active && (
                      <div className="flex gap-2 mt-4 flex-wrap">
                        {step.ctas.map((cta) => (
                          <span key={cta} className="px-2.5 py-1 rounded-lg text-xs font-medium" style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: TEXT_2, border: `1px solid ${BORDER}` }}>{cta}</span>
                        ))}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Right — browser mock */}
            <div className="rounded-2xl overflow-hidden shadow-2xl" style={{ backgroundColor: BG_SURFACE, border: `2px solid rgba(0,212,170,0.2)`, boxShadow: '0 0 40px rgba(0,0,0,0.6)' }}>
              {/* Browser chrome */}
              <div className="flex items-center gap-2 px-4 py-3" style={{ backgroundColor: BG_RAISED, borderBottom: `1px solid ${BORDER}` }}>
                <div className="w-3 h-3 rounded-full bg-red-500/60" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
                <div className="w-3 h-3 rounded-full bg-green-500/60" />
                <div className="flex-1 mx-3 px-3 py-1 rounded-md text-xs" style={{ backgroundColor: 'rgba(255,255,255,0.04)', color: TEXT_3 }}>
                  localhost:3000/{['home', 'insights', 'doctor-prep'][activeStep]}
                </div>
              </div>
              {/* App chrome — top nav strip */}
              <div className="flex items-center gap-4 px-4 py-2 text-xs" style={{ backgroundColor: '#0A0E14', borderBottom: `1px solid ${BORDER}` }}>
                <Activity className="w-4 h-4" style={{ color: ACCENT }} />
                {['Home', 'Track', 'Insights', 'Agents', 'Profile'].map((t) => {
                  const activeTab = ['Home', 'Insights', 'Profile'][activeStep];
                  return (
                    <span key={t} className="font-medium" style={{ color: t === activeTab ? ACCENT : TEXT_3 }}>{t}</span>
                  );
                })}
              </div>
              {/* Content */}
              <div className="p-5 overflow-hidden" style={{ minHeight: '420px', maxHeight: '500px', overflowY: 'auto' }}>
                <DemoPanel />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────────────────────── */}
      <section className="py-20 px-6" id="features" style={{ backgroundColor: BG_SURFACE }}>
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: ACCENT }}>Features</p>
            <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1 }}>Everything you need to understand your health</h2>
            <p className="text-lg" style={{ color: TEXT_2 }}>Simple, powerful, and designed for real people</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map((f, idx) => (
              <div key={idx} className="rounded-2xl p-6 transition-all duration-200 hover:translate-y-[-2px]" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
                <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-4" style={{ backgroundColor: f.bg }}>
                  <f.icon className={`w-5 h-5 ${f.color}`} />
                </div>
                <h3 className="text-base font-semibold mb-2" style={{ color: TEXT_1 }}>{f.title}</h3>
                <p className="text-sm" style={{ color: TEXT_2 }}>{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Who It's For ────────────────────────────────────────────────── */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: ACCENT }}>Who it&apos;s for</p>
            <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1 }}>One platform, three experiences</h2>
            <p className="text-lg" style={{ color: TEXT_2 }}>Whether you&apos;re managing your own health, supporting someone you love, or monitoring a patient panel</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {WHO_ITS_FOR.map(({ icon: Icon, title, subtitle, points, color, bg }) => (
              <div key={title} className="rounded-2xl p-6" style={{ backgroundColor: 'rgba(255,255,255,0.02)', border: `1px solid rgba(255,255,255,0.07)` }}>
                <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4" style={{ backgroundColor: bg }}>
                  <Icon className="w-6 h-6" style={{ color }} />
                </div>
                <p className="text-xl font-bold mb-1" style={{ color: TEXT_1, fontFamily: 'Syne, sans-serif' }}>{title}</p>
                <p className="text-sm mb-5" style={{ color: TEXT_3 }}>{subtitle}</p>
                <ul className="space-y-2.5">
                  {points.map((pt) => (
                    <li key={pt} className="flex items-start gap-2.5">
                      <div className="w-4 h-4 rounded-full flex-shrink-0 flex items-center justify-center mt-0.5" style={{ backgroundColor: bg }}>
                        <Check className="w-2.5 h-2.5" style={{ color }} />
                      </div>
                      <span className="text-sm" style={{ color: TEXT_2 }}>{pt}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-6">
                  <Link href="/signup">
                    <button className="w-full py-2 rounded-xl text-sm font-semibold transition-all hover:brightness-110" style={{ backgroundColor: bg, color, border: `1px solid ${color}33` }}>
                      Get started →
                    </button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ────────────────────────────────────────────────── */}
      <section className="py-20 px-6" style={{ backgroundColor: BG_SURFACE }}>
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: ACCENT }}>How it works</p>
            <h2 className="text-4xl font-bold" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1 }}>Get Started in 3 Minutes</h2>
          </div>
          <div className="space-y-10">
            {[
              { n: '1', title: 'Sign Up & Choose Your Role', body: 'Create your account in 30 seconds and tell us who you are — patient, caregiver, or healthcare provider. Each role gets a tailored dashboard from the start.', badge: '30 seconds' },
              { n: '2', title: 'Connect & Start Logging', body: 'Link your Oura Ring or start logging manually. Add medications, health conditions, and log meals by photo. It all feeds a single, unified health picture.', badge: '1 minute' },
              { n: '3', title: 'Get Insights & Prep for Visits', body: 'We surface 3 high-signal insights: what changed, why it might matter, and what questions to ask your doctor. Share your full record with your care team in one click.', badge: '2 minutes' },
            ].map(({ n, title, body, badge }) => (
              <div key={n} className="flex items-start gap-6">
                <div className="flex flex-col items-center gap-2 flex-shrink-0">
                  <div className="w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg" style={{ backgroundColor: ACCENT_BG, border: `1px solid rgba(0,212,170,0.3)`, color: ACCENT, fontFamily: 'Syne, sans-serif' }}>{n}</div>
                </div>
                <div className="pt-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-semibold" style={{ color: TEXT_1 }}>{title}</h3>
                    <span className="px-2 py-0.5 rounded-full text-xs" style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: TEXT_3 }}>{badge}</span>
                  </div>
                  <p style={{ color: TEXT_2 }}>{body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Why HealthAssist ────────────────────────────────────────────── */}
      <section className="py-20 px-6 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 60% 50% at 50% 50%, rgba(0,212,170,0.05) 0%, transparent 70%)' }} />
        <div className="max-w-4xl mx-auto relative">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1 }}>Why HealthAssist?</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              'Wearables, lab results, symptoms, and medications — all in one place',
              'AI connects the dots across your entire health picture',
              '5 specialised AI health agents available 24/7',
              'One-click doctor-ready report — PDF in seconds',
              'Share your record with family or providers — no account needed on their end',
              'Lab anomaly detection — flagged and explained the moment you log',
              'Care plans with progress tracking — set by you or your doctor',
              'Privacy-first: encrypted, row-level security, never sold',
            ].map((item) => (
              <div key={item} className="flex items-center gap-3 px-4 py-3 rounded-xl" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
                <div className="w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center" style={{ backgroundColor: ACCENT_BG }}>
                  <Check className="w-3.5 h-3.5" style={{ color: ACCENT }} />
                </div>
                <span className="text-sm" style={{ color: TEXT_2 }}>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pricing ─────────────────────────────────────────────────────── */}
      <PricingSection />

      {/* ── CTA / Beta Signup ───────────────────────────────────────────── */}
      <section className="py-24 px-6 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 50% 60% at 50% 100%, rgba(0,212,170,0.06) 0%, transparent 70%)' }} />
        <div className="max-w-3xl mx-auto text-center relative">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-6" style={{ backgroundColor: ACCENT_BG, border: `1px solid rgba(0,212,170,0.2)` }}>
            <TrendingUp className="w-7 h-7" style={{ color: ACCENT }} />
          </div>
          <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1 }}>Ready to understand your health?</h2>
          <p className="text-lg mb-10" style={{ color: TEXT_2 }}>Join the waitlist for early access. Limited spots available.</p>
          <BetaSignupForm />
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="py-10 px-6" style={{ backgroundColor: BG_SURFACE, borderTop: `1px solid ${BORDER}` }}>
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5" style={{ color: ACCENT }} />
            <span className="font-semibold" style={{ color: TEXT_1, fontFamily: 'Syne, sans-serif' }}>HealthAssist</span>
          </div>
          <div className="flex items-center gap-6 text-sm">
            <a href="mailto:hello@healthassist.app" style={{ color: TEXT_3 }} className="hover:text-white transition-colors">Contact</a>
          </div>
          <p className="text-xs" style={{ color: TEXT_3 }}>
            &copy; 2026 HealthAssist. Not medical advice.
          </p>
        </div>
      </footer>
    </div>
  );
}
