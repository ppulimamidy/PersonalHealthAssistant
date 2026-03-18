import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Terms of Service — Vitalix',
  description: 'Terms and conditions for using the Vitalix health intelligence platform.',
};

const EFFECTIVE_DATE = 'March 15, 2026';

export default function TermsOfService() {
  return (
    <div style={{ backgroundColor: '#0A0F1A', minHeight: '100vh' }}>
      {/* Nav */}
      <header
        className="border-b"
        style={{ borderColor: 'rgba(255,255,255,0.06)', backgroundColor: '#0A0F1A' }}
      >
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="text-lg font-bold" style={{ color: '#E8EDF5' }}>
            Vitalix
          </Link>
          <Link href="/privacy" className="text-sm" style={{ color: '#526380' }}>
            Privacy Policy
          </Link>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold mb-2" style={{ color: '#E8EDF5' }}>
          Terms of Service
        </h1>
        <p className="text-sm mb-10" style={{ color: '#526380' }}>
          Effective date: {EFFECTIVE_DATE} &nbsp;·&nbsp; Last updated: {EFFECTIVE_DATE}
        </p>

        {/* Medical disclaimer — prominent */}
        <div
          className="rounded-2xl p-5 mb-10"
          style={{
            backgroundColor: 'rgba(248,113,113,0.06)',
            border: '1px solid rgba(248,113,113,0.2)',
          }}
        >
          <p className="text-sm font-semibold mb-1" style={{ color: '#F87171' }}>
            Medical Disclaimer
          </p>
          <p className="text-sm" style={{ color: '#A0AEBF' }}>
            Vitalix is a personal wellness application, <strong style={{ color: '#E8EDF5' }}>not
            a medical device</strong> and <strong style={{ color: '#E8EDF5' }}>not a substitute
            for professional medical advice</strong>. Information and insights provided by
            Vitalix are for general wellness and informational purposes only. Always consult a
            qualified healthcare professional before making any medical decisions or changes to
            your health regimen.
          </p>
        </div>

        <div className="space-y-10" style={{ color: '#A0AEBF', lineHeight: '1.75' }}>

          <Section title="1. Acceptance of Terms">
            <p>
              By creating an account or using Vitalix (the &quot;Service&quot;), you agree to
              these Terms of Service (&quot;Terms&quot;). If you do not agree, do not use the
              Service. These Terms form a binding agreement between you and Vitalix
              (&quot;we&quot;, &quot;us&quot;, or &quot;our&quot;).
            </p>
          </Section>

          <Section title="2. Eligibility">
            <ul className="list-disc list-inside space-y-1">
              <li>You must be at least <strong style={{ color: '#E8EDF5' }}>18 years old</strong> to use Vitalix</li>
              <li>You must provide accurate account information</li>
              <li>You are responsible for all activity under your account</li>
              <li>One account per person — sharing accounts is not permitted</li>
            </ul>
          </Section>

          <Section title="3. The Service">
            <p>
              Vitalix provides a platform to aggregate health data from wearable devices
              (including Oura Ring, Apple Health, Google Health Connect, Dexcom, WHOOP, Garmin, and Fitbit), analyse that
              data using artificial intelligence, and present personalised wellness insights.
            </p>
            <p className="mt-3">
              We reserve the right to modify, suspend, or discontinue any part of the Service
              at any time with reasonable notice. We are not liable for any modification,
              suspension, or discontinuation.
            </p>
          </Section>

          <Section title="4. Subscriptions and Billing">
            <SubSection title="Plans">
              <p>Vitalix offers three tiers:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li><strong style={{ color: '#E8EDF5' }}>Free</strong> — basic features at no cost</li>
                <li><strong style={{ color: '#E8EDF5' }}>Pro ($9.99/month)</strong> — unlimited AI insights and nutrition tracking</li>
                <li><strong style={{ color: '#E8EDF5' }}>Pro+ ($19.99/month)</strong> — all Pro features plus advanced analysis</li>
              </ul>
            </SubSection>
            <SubSection title="Billing">
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Subscriptions are billed monthly in advance</li>
                <li>Payments are processed by Stripe — we do not store your card details</li>
                <li>Prices are in USD. Applicable VAT or sales tax may be added at checkout</li>
                <li>Subscriptions auto-renew unless cancelled before the renewal date</li>
              </ul>
            </SubSection>
            <SubSection title="Cancellation and refunds">
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>You may cancel your subscription at any time from Settings → Manage Subscription</li>
                <li>Cancellation takes effect at the end of the current billing period — you retain access until then</li>
                <li>We do not provide refunds for partial billing periods already paid</li>
                <li>If we materially change a paid feature, we will provide a pro-rated refund on request</li>
              </ul>
            </SubSection>
          </Section>

          <Section title="5. Your Health Data">
            <p>
              <strong style={{ color: '#E8EDF5' }}>You own your health data.</strong> By using
              Vitalix, you grant us a limited licence to store and process your health data
              solely to provide the Service to you. We do not sell your health data. We do not
              use your health data to train AI models without your explicit consent.
            </p>
            <p className="mt-3">
              You are responsible for the accuracy of data you manually enter (symptoms, lab
              results, medications). Vitalix insights are only as accurate as the underlying
              data.
            </p>
            <p className="mt-3">
              You may delete all your data at any time from Settings → Delete Account. Deletion
              is permanent and irreversible.
            </p>
          </Section>

          <Section title="6. Acceptable Use">
            <p>You agree not to:</p>
            <ul className="list-disc list-inside mt-2 space-y-1">
              <li>Use the Service for any unlawful purpose</li>
              <li>Attempt to gain unauthorised access to other users&apos; data</li>
              <li>Scrape, crawl, or systematically extract data from the Service</li>
              <li>Reverse-engineer, decompile, or disassemble the app</li>
              <li>Use automated tools to send requests at rates that degrade the Service for others</li>
              <li>Impersonate any person or entity</li>
              <li>Upload malicious code or content</li>
            </ul>
          </Section>

          <Section title="7. Third-Party Integrations">
            <p>
              Vitalix integrates with third-party services (Oura, Apple Health, Google Health, Dexcom, WHOOP, Garmin, Fitbit, and other supported
              Connect). Your use of those services is governed by their own terms and privacy
              policies. We are not responsible for the availability, accuracy, or conduct of
              third-party services.
            </p>
          </Section>

          <Section title="8. AI-Generated Content">
            <p>
              Insights and responses generated by Vitalix&apos;s AI are for informational
              purposes only. AI-generated content may be inaccurate, incomplete, or
              out-of-date. Do not make medical, financial, or other significant decisions
              based solely on AI-generated content without independent verification.
            </p>
          </Section>

          <Section title="9. Intellectual Property">
            <p>
              The Vitalix app, including its design, code, and branding, is owned by us and
              protected by intellectual property laws. You may not copy, reproduce, or create
              derivative works without our written consent.
            </p>
            <p className="mt-3">
              You retain all rights to your personal health data. You grant us no rights to
              your data beyond what is necessary to provide the Service.
            </p>
          </Section>

          <Section title="10. Disclaimer of Warranties">
            <p>
              THE SERVICE IS PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT
              WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
              WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
              NON-INFRINGEMENT. WE DO NOT WARRANT THAT THE SERVICE WILL BE UNINTERRUPTED,
              ERROR-FREE, OR FREE OF HARMFUL COMPONENTS.
            </p>
          </Section>

          <Section title="11. Limitation of Liability">
            <p>
              TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, VITALIX SHALL NOT BE LIABLE
              FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES,
              INCLUDING LOSS OF DATA, LOSS OF PROFITS, OR PERSONAL INJURY, ARISING FROM YOUR
              USE OF THE SERVICE.
            </p>
            <p className="mt-3">
              OUR TOTAL LIABILITY FOR ANY CLAIM ARISING FROM THESE TERMS OR THE SERVICE SHALL
              NOT EXCEED THE AMOUNT YOU PAID US IN THE 12 MONTHS PRECEDING THE CLAIM.
            </p>
          </Section>

          <Section title="12. Indemnification">
            <p>
              You agree to indemnify and hold harmless Vitalix and its officers, directors,
              and employees from any claims, damages, or expenses (including legal fees)
              arising from your use of the Service, your violation of these Terms, or your
              violation of any third-party rights.
            </p>
          </Section>

          <Section title="13. Governing Law and Disputes">
            <p>
              These Terms are governed by the laws of the State of Delaware, United States,
              without regard to its conflict of law provisions.
            </p>
            <p className="mt-3">
              Any dispute arising from these Terms shall first be attempted to be resolved
              informally by contacting{' '}
              <a href="mailto:support@vitalix.health" style={{ color: '#818CF8' }}>
                support@vitalix.health
              </a>.
              If not resolved within 30 days, disputes shall be submitted to binding
              arbitration under the rules of the American Arbitration Association, except that
              either party may seek injunctive relief in court for intellectual property
              violations.
            </p>
            <p className="mt-3">
              If you are an EU consumer, you may also submit a complaint to your local
              consumer protection authority or use the EU Online Dispute Resolution platform
              at{' '}
              <a
                href="https://ec.europa.eu/consumers/odr"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: '#818CF8' }}
              >
                ec.europa.eu/consumers/odr
              </a>.
            </p>
          </Section>

          <Section title="14. Changes to These Terms">
            <p>
              We may update these Terms from time to time. We will notify you by email and
              post the updated Terms with a new effective date. Continued use of the Service
              after changes take effect constitutes acceptance of the new Terms. If you
              disagree with material changes, you may cancel your account before they take
              effect.
            </p>
          </Section>

          <Section title="15. Contact">
            <p>Questions about these Terms:</p>
            <div className="mt-3 space-y-1">
              <p>
                <strong style={{ color: '#E8EDF5' }}>Email:</strong>{' '}
                <a href="mailto:support@vitalix.health" style={{ color: '#818CF8' }}>
                  support@vitalix.health
                </a>
              </p>
              <p>
                <strong style={{ color: '#E8EDF5' }}>Website:</strong>{' '}
                <a href="https://vitalix.health" style={{ color: '#818CF8' }}>
                  vitalix.health
                </a>
              </p>
            </div>
          </Section>

        </div>
      </main>

      {/* Footer */}
      <footer
        className="border-t mt-16 py-8"
        style={{ borderColor: 'rgba(255,255,255,0.06)' }}
      >
        <div className="max-w-3xl mx-auto px-6 flex flex-wrap gap-6 text-sm" style={{ color: '#526380' }}>
          <Link href="/" style={{ color: '#526380' }}>Home</Link>
          <Link href="/privacy" style={{ color: '#526380' }}>Privacy Policy</Link>
          <Link href="/terms" style={{ color: '#818CF8' }}>Terms of Service</Link>
          <a href="mailto:support@vitalix.health" style={{ color: '#526380' }}>Support</a>
        </div>
      </footer>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-lg font-semibold mb-3" style={{ color: '#E8EDF5' }}>
        {title}
      </h2>
      {children}
    </section>
  );
}

function SubSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mt-4">
      <h3 className="text-sm font-semibold mb-1" style={{ color: '#C8D3E0' }}>
        {title}
      </h3>
      {children}
    </div>
  );
}
