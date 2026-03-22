'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import {
  Activity, Brain, FileText, Pill, Zap, Check, ArrowRight, Utensils,
  ClipboardList, Sparkles, TrendingUp, Cpu, ChevronRight, FlaskConical,
  Users, Target, User, Stethoscope, Dna, TestTube2, HeartPulse, Shield,
  AlertTriangle,
} from 'lucide-react';
import { PricingSection } from './PricingSection';
import { BetaSignupForm } from './BetaSignupForm';

// ── Design tokens ──────────────────────────────────────────────────────────
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

// ── Persistent disclaimer ───────────────────────────────────────────────────
function MedicalDisclaimer({ compact = false }: { compact?: boolean }) {
  if (compact) {
    return (
      <p className="text-[10px] mt-2" style={{ color: TEXT_3 }}>
        For informational purposes only. Not medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider.
      </p>
    );
  }
  return (
    <div className="flex items-start gap-2 p-3 rounded-xl mt-4" style={{ backgroundColor: 'rgba(251,191,36,0.04)', border: '1px solid rgba(251,191,36,0.1)' }}>
      <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: '#FBBF24' }} />
      <p className="text-[11px] leading-relaxed" style={{ color: TEXT_3 }}>
        Vitalix is an informational wellness tool, not a medical device. It does not diagnose, treat, cure, or prevent any disease. All content is for educational purposes and should not replace professional medical advice. Always consult your physician before making health decisions.
      </p>
    </div>
  );
}

// ── Features ────────────────────────────────────────────────────────────────

const features = [
  {
    icon: Brain,
    title: 'Context-Aware Health Insights',
    description: 'AI-generated educational insights tailored to your goals — whether you\'re optimizing sleep and fitness, managing a chronic condition, or navigating a new diagnosis. Designed to help you understand your data.',
    color: 'text-violet-400',
    bg: 'rgba(139,92,246,0.08)',
  },
  {
    icon: Sparkles,
    title: '27 AI Health Assistants',
    description: 'Specialized AI assistants trained in oncology support, endocrine health, cardiology, nutrition, and more. They organize your health data and help you prepare for doctor conversations — they are not medical professionals.',
    color: 'text-yellow-400',
    bg: 'rgba(250,204,21,0.08)',
  },
  {
    icon: Target,
    title: 'Personal Health Journaling',
    description: 'Track lifestyle changes and log how you feel. Keep a structured journal of what you try — diet changes, supplements, exercise — and review patterns over time with your provider.',
    color: 'text-pink-400',
    bg: 'rgba(244,114,182,0.08)',
  },
  {
    icon: Dna,
    title: 'Medical Records Organization',
    description: 'Upload pathology reports, genomic panels, or imaging results. AI helps extract and organize key data points — mutations, staging, findings — so you can discuss them clearly with your care team.',
    color: 'text-indigo-400',
    bg: 'rgba(129,140,248,0.08)',
  },
  {
    icon: FlaskConical,
    title: 'Lab Results Tracking',
    description: 'Enter or scan lab results. View trends over time for 50+ biomarkers. See which values fall outside reference ranges and bring a clear lab history to every appointment.',
    color: 'text-cyan-400',
    bg: 'rgba(34,211,238,0.08)',
  },
  {
    icon: TestTube2,
    title: 'Clinical Research Explorer',
    description: 'Explore published research, clinical trials, and treatment guidelines relevant to your conditions. AI summarizes findings — always discuss with your doctor before making decisions.',
    color: 'text-emerald-400',
    bg: 'rgba(52,211,153,0.08)',
  },
  {
    icon: Pill,
    title: 'Medication Information Hub',
    description: 'View educational information about medications relevant to your conditions — including published research on interactions, costs, and clinical evidence. Not a substitute for pharmacist or physician guidance.',
    color: 'text-red-400',
    bg: 'rgba(248,113,113,0.08)',
  },
  {
    icon: Utensils,
    title: 'Nutrition Logging & Insights',
    description: 'Log meals by photo with AI-assisted portion estimation. View calorie and macro trends. Get general nutrition information relevant to your health context — consult a dietitian for medical nutrition therapy.',
    color: 'text-orange-400',
    bg: 'rgba(251,146,60,0.08)',
  },
  {
    icon: FileText,
    title: 'Doctor Visit Preparation',
    description: 'Generate a summary of your recent health data — labs, symptoms, medications, and questions to discuss. Export as PDF or share a secure link with your provider before your appointment.',
    color: 'text-blue-400',
    bg: 'rgba(96,165,250,0.08)',
  },
];

// ── Demo steps ──────────────────────────────────────────────────────────────

const demoSteps = [
  {
    label: 'Onboard',
    time: '0–30 s',
    title: 'Tell us your health focus, get matched with an AI assistant',
    description: 'Select your health concern. AI matches you with a specialized assistant and suggests an educational health journey tailored to your situation.',
    ctas: ['General Wellness', 'Cancer Support', 'Diabetes', 'PCOS'],
  },
  {
    label: 'Organize',
    time: '30–90 s',
    title: 'Your health data, organized and summarized',
    description: 'Upload lab results, medical records, or log symptoms. AI organizes and summarizes your data — helping you and your doctor see the full picture.',
    ctas: ['Upload records', 'View medication info', 'Explore research'],
  },
  {
    label: 'Prepare',
    time: '90–180 s',
    title: 'Walk into your appointment with the right questions',
    description: 'AI generates discussion topics and questions based on your health data — so you and your doctor can make the most of your visit time.',
    ctas: ['Export PDF', 'Share with provider', 'Review questions'],
  },
];

// ── Demo Mockups ────────────────────────────────────────────────────────────

function DemoStep0() {
  return (
    <div className="space-y-4">
      <div>
        <p className="text-lg font-semibold" style={{ color: TEXT_1, fontFamily: 'Syne, sans-serif' }}>What brings you here?</p>
        <p className="text-xs mt-1" style={{ color: TEXT_3 }}>We&apos;ll match you with an AI health assistant</p>
      </div>
      {[
        { label: 'Just staying healthy', icon: Activity, assistant: 'Personal Health Coach', color: '#00D4AA' },
        { label: 'Cancer Support', icon: HeartPulse, assistant: 'Oncology Support Assistant', color: '#F87171' },
        { label: 'PCOS / Hormonal', icon: TrendingUp, assistant: 'Endocrine Health Assistant', color: '#818CF8' },
        { label: 'Type 2 Diabetes', icon: Target, assistant: 'Metabolic Health Assistant', color: '#FBBF24' },
      ].map(({ label, icon: Icon, assistant, color }) => (
        <div key={label} className="rounded-xl p-4 flex items-center gap-3 transition-all cursor-pointer" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
          <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${color}15` }}>
            <Icon className="w-5 h-5" style={{ color }} />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium" style={{ color: TEXT_1 }}>{label}</p>
            <p className="text-[10px]" style={{ color: TEXT_3 }}>{assistant}</p>
          </div>
          <ChevronRight className="w-4 h-4" style={{ color: TEXT_3 }} />
        </div>
      ))}
      <div className="rounded-xl p-4" style={{ backgroundColor: `${ACCENT}08`, border: `1px solid ${ACCENT}20` }}>
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="w-4 h-4" style={{ color: ACCENT }} />
          <p className="text-xs font-semibold" style={{ color: ACCENT }}>SUGGESTED JOURNEY</p>
        </div>
        <p className="text-sm font-medium" style={{ color: TEXT_1 }}>4-phase educational support program</p>
        <p className="text-xs mt-1" style={{ color: TEXT_3 }}>Records review, research exploration, question preparation, ongoing monitoring</p>
      </div>
      <MedicalDisclaimer compact />
    </div>
  );
}

function DemoStep1() {
  return (
    <div className="space-y-4">
      <p className="text-sm font-semibold" style={{ color: TEXT_2 }}>Health Information Summary</p>
      {/* Medication information */}
      <div className="rounded-xl p-4" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4" style={{ color: ACCENT }} />
          <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: ACCENT }}>Medications to Discuss with Your Doctor</p>
        </div>
        {[
          { name: 'Osimertinib (Tagrisso)', badge: 'Discuss with oncologist', color: '#F87171', note: 'Published research available' },
          { name: 'Afatinib (Gilotrif)', badge: 'Discuss with oncologist', color: '#F87171', note: 'Published research available' },
        ].map(({ name, badge, color, note }) => (
          <div key={name} className="flex items-start gap-2 py-2" style={{ borderBottom: `1px solid ${BORDER}` }}>
            <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5" style={{ backgroundColor: `${color}15` }}>
              <FileText className="w-3.5 h-3.5" style={{ color }} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium" style={{ color: TEXT_1 }}>{name}</p>
              <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                <span className="text-[9px] px-1.5 py-0.5 rounded-full" style={{ backgroundColor: `${color}15`, color }}>{badge}</span>
                <span className="text-[9px]" style={{ color: TEXT_3 }}>{note}</span>
              </div>
            </div>
          </div>
        ))}
        <p className="text-[9px] mt-2" style={{ color: TEXT_3 }}>Based on published clinical literature. Not a prescription or medical recommendation.</p>
      </div>
      {/* Nutrition info */}
      <div className="rounded-xl p-4" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
        <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: '#6EE7B7' }}>General Nutrition Information</p>
        <p className="text-xs" style={{ color: TEXT_2 }}>Research suggests anti-inflammatory foods may support general wellness. Consider discussing dietary changes with your care team.</p>
        <div className="flex flex-wrap gap-1 mt-2">
          {['Salmon', 'Broccoli', 'Avocado', 'Blueberries', 'Walnuts'].map((f) => (
            <span key={f} className="text-[9px] px-1.5 py-0.5 rounded" style={{ backgroundColor: 'rgba(110,231,183,0.1)', color: '#6EE7B7' }}>{f}</span>
          ))}
        </div>
      </div>
      {/* Genomic data */}
      <div className="rounded-xl p-4" style={{ backgroundColor: 'rgba(129,140,248,0.05)', border: `1px solid rgba(129,140,248,0.15)` }}>
        <div className="flex items-center gap-2 mb-2">
          <Dna className="w-4 h-4 text-indigo-400" />
          <p className="text-xs font-semibold" style={{ color: '#818CF8' }}>UPLOADED GENOMIC DATA</p>
        </div>
        <p className="text-xs" style={{ color: TEXT_2 }}>EGFR L858R mutation identified in uploaded report. Published literature discusses targeted therapy options — bring this summary to your oncologist for interpretation.</p>
      </div>
      <MedicalDisclaimer compact />
    </div>
  );
}

function DemoStep2() {
  return (
    <div className="space-y-4">
      <p className="text-sm font-semibold" style={{ color: TEXT_2 }}>Doctor Visit Preparation</p>
      <div className="rounded-xl p-4" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(96,165,250,0.1)' }}>
            <FileText className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <p className="text-sm font-semibold" style={{ color: TEXT_1 }}>30-Day Health Summary</p>
            <p className="text-xs" style={{ color: TEXT_3 }}>Prepared for your next appointment</p>
          </div>
        </div>
        {[
          { label: 'Health conditions', value: 'Cancer Support', delta: 'Uploaded genomic + pathology reports' },
          { label: 'Organized findings', value: '2 mutations identified', delta: 'From uploaded genomic panel' },
          { label: 'Suggested lab work', value: 'CBC, CMP, tumor markers', delta: 'Based on general guidelines' },
          { label: 'Research topics', value: '4 topics to explore', delta: 'Targeted therapies, clinical trials' },
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
      {/* Questions */}
      <div className="rounded-xl p-4" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}>
        <p className="text-xs font-semibold mb-3" style={{ color: TEXT_3 }}>SUGGESTED QUESTIONS FOR YOUR DOCTOR</p>
        {[
          'What are the first-line therapy options for my EGFR mutation profile?',
          'Are there clinical trials I should consider given my genomic findings?',
          'What monitoring schedule do you recommend during treatment?',
        ].map((q) => (
          <div key={q} className="flex items-start gap-2 py-1.5">
            <div className="w-4 h-4 rounded-full flex-shrink-0 flex items-center justify-center mt-0.5" style={{ backgroundColor: ACCENT_BG }}>
              <Sparkles className="w-2.5 h-2.5" style={{ color: ACCENT }} />
            </div>
            <p className="text-xs" style={{ color: TEXT_2 }}>{q}</p>
          </div>
        ))}
        <p className="text-[9px] mt-2" style={{ color: TEXT_3 }}>Questions generated from your uploaded health data. Your doctor will determine appropriate next steps.</p>
      </div>
      <div className="flex gap-2">
        <div className="flex-1 text-center py-2 rounded-lg text-xs font-medium" style={{ backgroundColor: ACCENT, color: '#000' }}>Export PDF</div>
        <div className="flex-1 text-center py-2 rounded-lg text-xs font-medium" style={{ backgroundColor: 'rgba(255,255,255,0.04)', border: `1px solid ${BORDER_MED}`, color: TEXT_2 }}>Share with Provider</div>
      </div>
    </div>
  );
}

const DEMO_PANELS = [DemoStep0, DemoStep1, DemoStep2];

// ── Who It's For ────────────────────────────────────────────────────────────

const WHO_ITS_FOR = [
  {
    icon: Activity,
    title: 'Wellness Seekers',
    subtitle: 'Staying healthy proactively',
    points: [
      'Connect your wearable — track sleep, activity, heart rate trends',
      'Log meals by photo and see nutrition patterns over time',
      'AI coach surfaces insights on sleep, stress, and energy',
      'Preventive screening reminders based on age and profile',
      'Share a health summary with your doctor at annual check-ups',
    ],
    color: ACCENT,
    bg: ACCENT_BG,
  },
  {
    icon: User,
    title: 'Patients',
    subtitle: 'Managing a health condition',
    points: [
      'AI health assistant matched to your condition at sign-up',
      'Medical records, labs, and genomics — organized and summarized',
      'Educational medication and research information for doctor discussions',
      'Visit preparation with AI-suggested questions for your provider',
      'Structured health journal to track what you try and how you feel',
    ],
    color: '#F87171',
    bg: 'rgba(248,113,113,0.10)',
  },
  {
    icon: Users,
    title: 'Caregivers',
    subtitle: 'Supporting a loved one',
    points: [
      'View shared health data with granular permissions',
      'Alerts when tracked values move outside reference ranges',
      'See medications, labs, symptoms, and AI-organized summaries',
      'Dedicated Family dashboard for multiple profiles',
      'Privacy-first: revocable access at any time',
    ],
    color: '#818cf8',
    bg: 'rgba(129,140,248,0.10)',
  },
  {
    icon: Stethoscope,
    title: 'Healthcare Providers',
    subtitle: 'Better-informed patient visits',
    points: [
      'Patients share organized health records via secure link',
      'Review uploaded genomic profiles, lab trends, and symptom history',
      'Pre-visit summaries with patient-generated discussion points',
      'No account needed — access via shared link',
      'Encrypted sharing with audit logging',
    ],
    color: '#60a5fa',
    bg: 'rgba(96,165,250,0.10)',
  },
];

// ── Main Component ──────────────────────────────────────────────────────────

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
            <span className="text-lg font-bold" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1 }}>Vitalix</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#demo" className="text-sm hidden sm:block" style={{ color: TEXT_2 }}>How It Works</a>
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

      {/* ── Hero ──────────────────────────────────────────────────────── */}
      <section className="pt-36 pb-24 px-6 text-center relative overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full pointer-events-none" style={{ background: 'radial-gradient(ellipse, rgba(0,212,170,0.07) 0%, transparent 70%)', filter: 'blur(40px)' }} />
        <div className="max-w-4xl mx-auto relative">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium mb-8" style={{ backgroundColor: ACCENT_BG, border: `1px solid rgba(0,212,170,0.2)`, color: ACCENT }}>
            <Zap className="w-3 h-3" />
            Health information organized by AI
          </div>
          <h1 className="text-5xl md:text-6xl font-bold leading-tight mb-6" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1, letterSpacing: '-0.02em' }}>
            Your health, <span style={{ color: ACCENT }}>organized</span><br />
            and understood.
          </h1>
          <p className="text-xl max-w-2xl mx-auto mb-10" style={{ color: TEXT_2 }}>
            Whether you&apos;re managing a condition or simply staying on top of your wellness — AI assistants organize your health data, surface patterns, and help you prepare for every doctor visit.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/signup">
              <button className="flex items-center gap-2 px-6 py-3 rounded-xl text-base font-semibold transition-all hover:brightness-110" style={{ backgroundColor: ACCENT, color: '#000' }}>
                Get Started Free
                <ArrowRight className="w-4 h-4" />
              </button>
            </Link>
            <a href="#demo">
              <button className="flex items-center gap-2 px-6 py-3 rounded-xl text-base font-medium transition-all" style={{ backgroundColor: 'rgba(255,255,255,0.04)', border: `1px solid ${BORDER_MED}`, color: TEXT_2 }}>
                See how it works
              </button>
            </a>
          </div>
          {/* Condition pills */}
          <div className="flex items-center justify-center gap-2 mt-8 flex-wrap">
            <span className="text-xs" style={{ color: TEXT_3 }}>Built for:</span>
            {['General Wellness', 'Cancer Support', 'Diabetes', 'PCOS', 'Cardiac', 'Autoimmune', 'Mental Health'].map((c) => (
              <span key={c} className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium" style={{ backgroundColor: 'rgba(255,255,255,0.04)', border: `1px solid ${BORDER_MED}`, color: TEXT_2 }}>
                {c}
              </span>
            ))}
          </div>
          <p className="mt-6 text-xs max-w-lg mx-auto" style={{ color: TEXT_3 }}>
            Vitalix is an informational wellness tool. It does not provide medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider before making health decisions.
          </p>
        </div>
      </section>

      {/* ── Demo Flow ─────────────────────────────────────────────────── */}
      <section className="py-20 px-6" id="demo">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: ACCENT }}>How It Works</p>
            <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1 }}>From sign-up to visit-ready in minutes</h2>
            <p className="text-lg" style={{ color: TEXT_2 }}>Click through each step to see the app experience</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
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
                        {active && <p className="text-xs mt-2" style={{ color: TEXT_3 }}>{step.description}</p>}
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

            <div className="rounded-2xl overflow-hidden shadow-2xl" style={{ backgroundColor: BG_SURFACE, border: `2px solid rgba(0,212,170,0.2)`, boxShadow: '0 0 40px rgba(0,0,0,0.6)' }}>
              <div className="flex items-center gap-2 px-4 py-3" style={{ backgroundColor: BG_RAISED, borderBottom: `1px solid ${BORDER}` }}>
                <div className="w-3 h-3 rounded-full bg-red-500/60" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
                <div className="w-3 h-3 rounded-full bg-green-500/60" />
                <div className="flex-1 mx-3 px-3 py-1 rounded-md text-xs" style={{ backgroundColor: 'rgba(255,255,255,0.04)', color: TEXT_3 }}>
                  vitalix.health/{['onboarding', 'health-summary', 'visit-prep'][activeStep]}
                </div>
              </div>
              <div className="flex items-center gap-4 px-4 py-2 text-xs" style={{ backgroundColor: '#0A0E14', borderBottom: `1px solid ${BORDER}` }}>
                <Activity className="w-4 h-4" style={{ color: ACCENT }} />
                {['Home', 'Track', 'Insights', 'Ask AI', 'Profile'].map((t) => {
                  const activeTab = ['Home', 'Insights', 'Profile'][activeStep];
                  return <span key={t} className="font-medium" style={{ color: t === activeTab ? ACCENT : TEXT_3 }}>{t}</span>;
                })}
              </div>
              <div className="p-5 overflow-hidden" style={{ minHeight: '420px', maxHeight: '500px', overflowY: 'auto' }}>
                <DemoPanel />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────────────── */}
      <section className="py-20 px-6" id="features" style={{ backgroundColor: BG_SURFACE }}>
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: ACCENT }}>Features</p>
            <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1 }}>Organization and preparation, not diagnosis</h2>
            <p className="text-lg" style={{ color: TEXT_2 }}>Every feature helps you organize your health data and prepare for better conversations with your care team</p>
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
          <MedicalDisclaimer />
        </div>
      </section>

      {/* ── Who It's For ──────────────────────────────────────────────── */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: ACCENT }}>Who it&apos;s for</p>
            <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1 }}>One platform, three experiences</h2>
            <p className="text-lg" style={{ color: TEXT_2 }}>Whether you&apos;re optimizing your wellness, managing a condition, supporting a loved one, or preparing for a patient visit</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
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
                      Get started free
                    </button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Why Vitalix ──────────────────────────────────────────────── */}
      <section className="py-20 px-6 relative overflow-hidden" style={{ backgroundColor: BG_SURFACE }}>
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 60% 50% at 50% 50%, rgba(0,212,170,0.05) 0%, transparent 70%)' }} />
        <div className="max-w-4xl mx-auto relative">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1 }}>Why Vitalix?</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              '27 AI health assistants across 14 health areas (not medical professionals)',
              'Works for general wellness tracking and specific health conditions alike',
              'Upload and organize medical records, genomic panels, and imaging reports',
              'Educational medication information from published clinical literature',
              'Structured health journal to track lifestyle changes and outcomes',
              'AI-suggested discussion questions specific to your health data',
              'General nutrition information based on your health context',
              'Share organized health records with any provider via secure link',
              'Privacy-first: encrypted data, row-level security, audit logging',
              'Available on web and mobile (iOS + Android)',
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

      {/* ── Pricing ──────────────────────────────────────────────────── */}
      <PricingSection />

      {/* ── CTA ──────────────────────────────────────────────────────── */}
      <section className="py-24 px-6 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 50% 60% at 50% 100%, rgba(0,212,170,0.06) 0%, transparent 70%)' }} />
        <div className="max-w-3xl mx-auto text-center relative">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-6" style={{ backgroundColor: ACCENT_BG, border: `1px solid rgba(0,212,170,0.2)` }}>
            <TrendingUp className="w-7 h-7" style={{ color: ACCENT }} />
          </div>
          <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Syne, sans-serif', color: TEXT_1 }}>Be better prepared for every appointment</h2>
          <p className="text-lg mb-10" style={{ color: TEXT_2 }}>Organize your health data and walk in with the right questions.</p>
          <BetaSignupForm />
          <p className="text-xs mt-6" style={{ color: TEXT_3 }}>
            Vitalix does not provide medical advice, diagnosis, or treatment. Content is for informational and educational purposes only.
          </p>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="py-10 px-6" style={{ backgroundColor: BG_SURFACE, borderTop: `1px solid ${BORDER}` }}>
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5" style={{ color: ACCENT }} />
            <span className="font-semibold" style={{ color: TEXT_1, fontFamily: 'Syne, sans-serif' }}>Vitalix</span>
          </div>
          <p className="text-xs text-center max-w-md" style={{ color: TEXT_3 }}>
            Vitalix is an informational wellness tool. It is not a medical device, does not provide medical advice, and is not a substitute for professional healthcare. Always consult your physician.
          </p>
          <p className="text-xs" style={{ color: TEXT_3 }}>
            &copy; 2026 Vitalix
          </p>
        </div>
      </footer>
    </div>
  );
}
