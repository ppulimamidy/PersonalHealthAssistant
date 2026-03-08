'use client';

import { PricingTable } from '@/components/billing/PricingTable';

export function PricingSection() {
  return (
    <section className="py-20 px-6" id="pricing" style={{ backgroundColor: '#080B10' }}>
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: '#00D4AA' }}>Pricing</p>
          <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Syne, sans-serif', color: '#E8EDF5', letterSpacing: '-0.02em' }}>
            Simple, transparent pricing
          </h2>
          <p className="text-lg" style={{ color: '#8B97A8' }}>
            Start free. Upgrade when you need more.
          </p>
        </div>
        <PricingTable variant="dark" isPublicPage />
      </div>
    </section>
  );
}
