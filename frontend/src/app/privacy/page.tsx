import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Privacy Policy — Vitalix',
  description: 'How Vitalix collects, uses, and protects your personal health data.',
};

const EFFECTIVE_DATE = 'March 15, 2026';

export default function PrivacyPolicy() {
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
          <Link
            href="/terms"
            className="text-sm"
            style={{ color: '#526380' }}
          >
            Terms of Service
          </Link>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold mb-2" style={{ color: '#E8EDF5' }}>
          Privacy Policy
        </h1>
        <p className="text-sm mb-10" style={{ color: '#526380' }}>
          Effective date: {EFFECTIVE_DATE} &nbsp;·&nbsp; Last updated: {EFFECTIVE_DATE}
        </p>

        <div className="space-y-10" style={{ color: '#A0AEBF', lineHeight: '1.75' }}>

          <section>
            <p>
              Vitalix (&quot;we&quot;, &quot;us&quot;, or &quot;our&quot;) is a personal wellness application that
              helps you understand your health data through AI-powered insights. This Privacy
              Policy explains what information we collect, how we use it, and your rights
              regarding your data.
            </p>
            <p className="mt-4">
              Vitalix is a <strong style={{ color: '#E8EDF5' }}>consumer wellness application</strong>,
              not a medical device. We are not a HIPAA-covered entity. Nothing in this app
              constitutes medical advice — always consult a qualified healthcare professional
              for medical decisions.
            </p>
          </section>

          <Section title="1. Information We Collect">
            <SubSection title="Health and fitness data">
              <p>When you connect a device or sync health data, we collect:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Sleep duration and quality metrics</li>
                <li>Heart rate and heart rate variability (HRV)</li>
                <li>Daily steps, active calories, and workout sessions</li>
                <li>Blood oxygen (SpO₂) and respiratory rate</li>
                <li>Readiness and recovery scores</li>
                <li>Symptoms and wellness journal entries you log manually</li>
                <li>Lab results you upload (PDF or manual entry)</li>
              </ul>
            </SubSection>
            <SubSection title="Account information">
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Email address (used for authentication)</li>
                <li>Name (optional, used to personalise your experience)</li>
                <li>Subscription tier and billing history (via Stripe — we do not store card numbers)</li>
              </ul>
            </SubSection>
            <SubSection title="Usage data">
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>App interactions (screens visited, features used)</li>
                <li>Crash reports and performance logs</li>
                <li>Device type and operating system version</li>
              </ul>
            </SubSection>
            <SubSection title="Information we do NOT collect">
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Payment card numbers (handled entirely by Stripe)</li>
                <li>Precise GPS location</li>
                <li>Contacts or social graph</li>
                <li>Any data from your device other than health metrics you explicitly sync</li>
              </ul>
            </SubSection>
          </Section>

          <Section title="2. How We Use Your Information">
            <ul className="list-disc list-inside space-y-2">
              <li><strong style={{ color: '#E8EDF5' }}>Provide the service:</strong> generate personalised health insights, health scores, correlations, and AI agent responses using your data</li>
              <li><strong style={{ color: '#E8EDF5' }}>AI analysis:</strong> your health data is sent to Anthropic&apos;s API to generate insights — see Section 4 for details</li>
              <li><strong style={{ color: '#E8EDF5' }}>Billing:</strong> manage your subscription through Stripe</li>
              <li><strong style={{ color: '#E8EDF5' }}>Communications:</strong> send weekly health summaries and important account notices (you can opt out of summaries at any time)</li>
              <li><strong style={{ color: '#E8EDF5' }}>Improve the app:</strong> analyse aggregated, anonymised usage patterns to fix bugs and improve features</li>
              <li><strong style={{ color: '#E8EDF5' }}>Security:</strong> detect and prevent fraud or abuse</li>
            </ul>
            <p className="mt-4">
              We <strong style={{ color: '#E8EDF5' }}>do not sell your personal data</strong> to third
              parties. We do not use your health data for advertising.
            </p>
          </Section>

          <Section title="3. Legal Basis for Processing (GDPR)">
            <p>If you are in the European Economic Area (EEA), United Kingdom, or Switzerland, we process your data under the following legal bases:</p>
            <ul className="list-disc list-inside mt-3 space-y-2">
              <li><strong style={{ color: '#E8EDF5' }}>Contract performance:</strong> processing necessary to provide the Vitalix service you signed up for</li>
              <li><strong style={{ color: '#E8EDF5' }}>Legitimate interests:</strong> improving the app, preventing fraud, maintaining security</li>
              <li><strong style={{ color: '#E8EDF5' }}>Consent:</strong> sending marketing emails and optional health summary emails — you can withdraw consent at any time</li>
              <li><strong style={{ color: '#E8EDF5' }}>Explicit consent (Article 9):</strong> processing special category health data — you provide this by choosing to sync health data into the app</li>
            </ul>
          </Section>

          <Section title="4. Third-Party Services">
            <p>We share data with these service providers solely to operate Vitalix. Each has its own privacy policy and, where required, a Data Processing Agreement (DPA) with us.</p>
            <div className="mt-4 space-y-4">
              <ThirdParty
                name="Supabase"
                purpose="Database and authentication (stores your account and health data)"
                location="AWS us-east-1 (United States)"
                link="https://supabase.com/privacy"
              />
              <ThirdParty
                name="Anthropic"
                purpose="AI analysis — your health data is sent to generate insights and AI agent responses"
                location="United States"
                link="https://www.anthropic.com/privacy"
              />
              <ThirdParty
                name="Oura"
                purpose="If you connect your Oura Ring, we receive your ring data via Oura's API"
                location="United States / Finland"
                link="https://ouraring.com/privacy-policy"
              />
              <ThirdParty
                name="Stripe"
                purpose="Payment processing and subscription management"
                location="United States"
                link="https://stripe.com/privacy"
              />
              <ThirdParty
                name="Vercel"
                purpose="Web application hosting"
                location="Global edge network"
                link="https://vercel.com/legal/privacy-policy"
              />
              <ThirdParty
                name="Sentry"
                purpose="Crash reporting and error monitoring (may include device info and stack traces)"
                location="United States"
                link="https://sentry.io/privacy/"
              />
            </div>
          </Section>

          <Section title="5. Data Storage and Security">
            <ul className="list-disc list-inside space-y-2">
              <li>All data is encrypted in transit using TLS 1.3</li>
              <li>All data is encrypted at rest using AES-256 (Supabase / AWS)</li>
              <li>Access to your data is controlled by Row Level Security — only you can read your health records</li>
              <li>We use Supabase Pro with daily backups and point-in-time recovery</li>
              <li>Employees and contractors do not have routine access to individual health records</li>
            </ul>
          </Section>

          <Section title="6. Data Retention">
            <ul className="list-disc list-inside space-y-2">
              <li>Your health data and account are retained for as long as your account is active</li>
              <li>If you delete your account, all personal data is deleted within <strong style={{ color: '#E8EDF5' }}>30 days</strong></li>
              <li>Anonymised, aggregated analytics data may be retained longer</li>
              <li>Billing records are retained for 7 years as required by tax law</li>
            </ul>
          </Section>

          <Section title="7. Your Rights">
            <p>Depending on where you live, you have the following rights:</p>

            <SubSection title="All users">
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li><strong style={{ color: '#E8EDF5' }}>Access:</strong> request a copy of your personal data</li>
                <li><strong style={{ color: '#E8EDF5' }}>Deletion:</strong> delete your account and all associated data from Settings → Delete Account, or by emailing us</li>
                <li><strong style={{ color: '#E8EDF5' }}>Correction:</strong> update your profile information in-app at any time</li>
                <li><strong style={{ color: '#E8EDF5' }}>Opt-out of emails:</strong> unsubscribe link in every marketing email</li>
              </ul>
            </SubSection>

            <SubSection title="EU / EEA / UK users (GDPR)">
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li><strong style={{ color: '#E8EDF5' }}>Data portability:</strong> receive your data in a machine-readable format (JSON export — email us to request)</li>
                <li><strong style={{ color: '#E8EDF5' }}>Restriction:</strong> ask us to stop processing your data while a dispute is resolved</li>
                <li><strong style={{ color: '#E8EDF5' }}>Objection:</strong> object to processing based on legitimate interests</li>
                <li><strong style={{ color: '#E8EDF5' }}>Withdraw consent:</strong> at any time, without affecting prior processing</li>
                <li><strong style={{ color: '#E8EDF5' }}>Lodge a complaint:</strong> with your local data protection authority</li>
              </ul>
            </SubSection>

            <SubSection title="California users (CCPA)">
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li><strong style={{ color: '#E8EDF5' }}>Right to know</strong> what personal information we collect</li>
                <li><strong style={{ color: '#E8EDF5' }}>Right to delete</strong> your personal information</li>
                <li><strong style={{ color: '#E8EDF5' }}>Right to opt-out of sale</strong> — we do not sell personal information</li>
                <li><strong style={{ color: '#E8EDF5' }}>Non-discrimination</strong> for exercising your rights</li>
              </ul>
            </SubSection>

            <p className="mt-4">
              To exercise any of these rights, email{' '}
              <a href="mailto:privacy@vitalix.health" style={{ color: '#818CF8' }}>
                privacy@vitalix.health
              </a>. We respond within 30 days (10 days for CCPA requests).
            </p>
          </Section>

          <Section title="8. Children's Privacy">
            <p>
              Vitalix is intended for users aged <strong style={{ color: '#E8EDF5' }}>18 and older</strong>.
              We do not knowingly collect personal information from anyone under 18. If you
              believe a minor has provided us with personal data, contact us at{' '}
              <a href="mailto:privacy@vitalix.health" style={{ color: '#818CF8' }}>
                privacy@vitalix.health
              </a>{' '}
              and we will delete it promptly.
            </p>
          </Section>

          <Section title="9. International Data Transfers">
            <p>
              Vitalix is operated from the United States. If you access the service from the
              EU, EEA, or UK, your data will be transferred to and processed in the United
              States. We rely on Standard Contractual Clauses (SCCs) with our service
              providers (Supabase, Anthropic, Stripe) as the legal mechanism for these
              transfers under GDPR.
            </p>
          </Section>

          <Section title="10. Cookies and Tracking">
            <p>
              The Vitalix web app uses strictly necessary cookies for authentication (session
              tokens). We do not use third-party advertising cookies or cross-site tracking.
              We may use first-party analytics to understand how features are used —
              this data is anonymised and not shared with third parties.
            </p>
          </Section>

          <Section title="11. Changes to This Policy">
            <p>
              We may update this Privacy Policy from time to time. When we do, we will update
              the &quot;Last updated&quot; date at the top and notify you by email if changes are
              material. Continued use of Vitalix after changes constitutes acceptance.
            </p>
          </Section>

          <Section title="12. Contact Us">
            <p>For privacy questions, data requests, or concerns:</p>
            <div className="mt-3 space-y-1">
              <p>
                <strong style={{ color: '#E8EDF5' }}>Email:</strong>{' '}
                <a href="mailto:privacy@vitalix.health" style={{ color: '#818CF8' }}>
                  privacy@vitalix.health
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
          <Link href="/privacy" style={{ color: '#818CF8' }}>Privacy Policy</Link>
          <Link href="/terms" style={{ color: '#526380' }}>Terms of Service</Link>
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

function ThirdParty({
  name,
  purpose,
  location,
  link,
}: {
  name: string;
  purpose: string;
  location: string;
  link: string;
}) {
  return (
    <div
      className="rounded-xl p-4"
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-semibold text-sm" style={{ color: '#E8EDF5' }}>{name}</p>
          <p className="text-sm mt-0.5">{purpose}</p>
          <p className="text-xs mt-1" style={{ color: '#526380' }}>📍 {location}</p>
        </div>
        <a
          href={link}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs shrink-0 mt-0.5"
          style={{ color: '#818CF8' }}
        >
          Privacy policy ↗
        </a>
      </div>
    </div>
  );
}
