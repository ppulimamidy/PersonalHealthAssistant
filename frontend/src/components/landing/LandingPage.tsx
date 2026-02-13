'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import {
  Activity,
  Brain,
  FileText,
  Shield,
  Zap,
  Check,
  ArrowRight
} from 'lucide-react';

const features = [
  {
    icon: Activity,
    title: 'Smart Health Timeline',
    description: 'See your sleep, activity, and readiness scores in one beautiful view.',
  },
  {
    icon: Brain,
    title: 'AI-Powered Insights',
    description: 'Get personalized insights that explain the "why" behind your health trends.',
  },
  {
    icon: FileText,
    title: 'Doctor Visit Prep',
    description: 'Generate comprehensive reports to share with your healthcare provider.',
  },
  {
    icon: Shield,
    title: 'Privacy First',
    description: 'Your health data stays secure. We never sell or share your information.',
  },
];

const benefits = [
  'Connect your Oura Ring in seconds',
  'View 7 or 30 days of health data',
  'Understand your health trends with AI',
  'Export reports for doctor visits',
  'HIPAA-compliant data security',
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-8 h-8 text-primary-600" />
            <span className="text-xl font-bold text-slate-900">HealthAssist</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost">Log in</Button>
            </Link>
            <Link href="/signup">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-slate-900 leading-tight">
            Your Health Data,{' '}
            <span className="text-primary-600">Finally Understood</span>
          </h1>
          <p className="mt-6 text-xl text-slate-600 max-w-2xl mx-auto">
            Connect your Oura Ring and get AI-powered insights that actually make sense.
            Prepare for doctor visits with one click.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/signup">
              <Button size="lg" className="w-full sm:w-auto">
                Start Free Trial
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link href="#demo">
              <Button size="lg" variant="outline" className="w-full sm:w-auto">
                Watch Demo
              </Button>
            </Link>
          </div>
          <p className="mt-4 text-sm text-slate-500">
            No credit card required. Free for the first 30 days.
          </p>
        </div>
      </section>

      {/* Demo Preview */}
      <section className="py-16 px-6" id="demo">
        <div className="max-w-5xl mx-auto">
          <div className="bg-slate-900 rounded-2xl p-2 shadow-2xl">
            <div className="bg-slate-800 rounded-xl overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 bg-slate-700">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
              </div>
              <div className="p-8 bg-gradient-to-br from-slate-50 to-slate-100 min-h-[400px] flex items-center justify-center">
                <div className="text-center">
                  <div className="flex items-center justify-center gap-8 mb-8">
                    <div className="text-center">
                      <div className="w-24 h-24 rounded-full bg-indigo-100 flex items-center justify-center mb-2">
                        <span className="text-3xl font-bold text-indigo-600">85</span>
                      </div>
                      <span className="text-sm text-slate-600">Sleep</span>
                    </div>
                    <div className="text-center">
                      <div className="w-24 h-24 rounded-full bg-green-100 flex items-center justify-center mb-2">
                        <span className="text-3xl font-bold text-green-600">92</span>
                      </div>
                      <span className="text-sm text-slate-600">Activity</span>
                    </div>
                    <div className="text-center">
                      <div className="w-24 h-24 rounded-full bg-amber-100 flex items-center justify-center mb-2">
                        <span className="text-3xl font-bold text-amber-600">78</span>
                      </div>
                      <span className="text-sm text-slate-600">Readiness</span>
                    </div>
                  </div>
                  <p className="text-slate-600">Your health scores at a glance</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6 bg-slate-50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900">
              Everything You Need to Understand Your Health
            </h2>
            <p className="mt-4 text-lg text-slate-600">
              Simple, powerful, and designed for real people
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, idx) => (
              <div key={idx} className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-slate-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900">
              Get Started in 3 Minutes
            </h2>
          </div>
          <div className="space-y-12">
            <div className="flex items-start gap-6">
              <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold shrink-0">
                1
              </div>
              <div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">
                  Sign Up & Connect Oura
                </h3>
                <p className="text-slate-600">
                  Create your account and authorize access to your Oura Ring data.
                  We only read what we need.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-6">
              <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold shrink-0">
                2
              </div>
              <div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">
                  View Your Health Timeline
                </h3>
                <p className="text-slate-600">
                  See your sleep, activity, and readiness data in a simple,
                  scrollable timeline. Toggle between 7 and 30 day views.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-6">
              <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold shrink-0">
                3
              </div>
              <div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">
                  Get Insights & Prep for Visits
                </h3>
                <p className="text-slate-600">
                  AI analyzes your trends and explains them in plain language.
                  Export a summary for your next doctor appointment.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-20 px-6 bg-primary-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-12">
            Why Choose HealthAssist?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
            {benefits.map((benefit, idx) => (
              <div key={idx} className="flex items-center gap-3 text-white">
                <div className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center">
                  <Check className="w-4 h-4" />
                </div>
                <span>{benefit}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <Zap className="w-12 h-12 text-primary-600 mx-auto mb-6" />
          <h2 className="text-3xl font-bold text-slate-900 mb-4">
            Ready to Understand Your Health?
          </h2>
          <p className="text-lg text-slate-600 mb-8">
            Join thousands of people who use HealthAssist to make sense of their health data.
          </p>
          <Link href="/signup">
            <Button size="lg">
              Start Your Free Trial
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 bg-slate-900 text-slate-400">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <Activity className="w-6 h-6 text-primary-400" />
              <span className="text-white font-semibold">HealthAssist</span>
            </div>
            <div className="flex items-center gap-6 text-sm">
              <a href="#" className="hover:text-white">Privacy</a>
              <a href="#" className="hover:text-white">Terms</a>
              <a href="#" className="hover:text-white">Contact</a>
            </div>
            <p className="text-sm">
              &copy; 2024 HealthAssist. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
