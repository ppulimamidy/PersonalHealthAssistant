'use client';

import { PricingTable } from '@/components/billing/PricingTable';

export function PricingSection() {
  return (
    <section className="py-20 px-6 bg-slate-50" id="pricing">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-900">
            Simple, Transparent Pricing
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Start free. Upgrade when you need more.
          </p>
        </div>
        <PricingTable />
      </div>
    </section>
  );
}
