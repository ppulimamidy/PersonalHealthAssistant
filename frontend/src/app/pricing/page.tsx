import { PricingSection } from '@/components/landing/PricingSection';
import { Activity } from 'lucide-react';
import Link from 'next/link';

export const metadata = {
  title: 'Pricing — HealthAssist',
  description: 'Simple, transparent pricing for your personal health assistant.',
};

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-white">
      <nav className="border-b border-slate-200 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Activity className="w-8 h-8 text-primary-600" />
            <span className="text-xl font-bold text-slate-900">HealthAssist</span>
          </Link>
          <Link href="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900">
            Log in
          </Link>
        </div>
      </nav>
      <PricingSection />
    </div>
  );
}
