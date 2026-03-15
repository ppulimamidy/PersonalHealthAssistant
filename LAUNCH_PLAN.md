# Vitalix Production Launch Plan
**Target:** TestFlight live in 2 weeks · Real users in 4 weeks
**Generated:** 2026-03-15 · Updated with: global launch, $1,500/mo budget, solo founder
**Domains:** vitalix.app · vitalix.health
**App Store Connect:** 6760475193 · Team: QAL9P7889F · Bundle: com.vitalix.app

---

## Budget Reality Check

**You won't need $1,500/month at launch. Here's what you actually spend:**

| Phase | Users | Monthly infra cost | Notes |
|---|---|---|---|
| Launch (now) | 0–100 | **~$155/mo** | Everything below |
| Growth | 100–500 | **~$280/mo** | Scale Render, add read replica |
| Scale | 500–1,500 | **~$550/mo** | Multiple Render instances, bigger Supabase |
| Comfortable max | 1,500–5,000 | **~$1,200/mo** | Full production stack |

**The $1,500/month budget is great — it means you have runway to scale to ~5,000 users without a billing crisis. Start spending ~$155/month and let it grow naturally with users.**

---

## Cost Breakdown — Launch Stack (~$155/month)

| Service | Tier | Monthly | Why |
|---|---|---|---|
| **Vercel** | Pro | $20 | Commercial use, no hobby restrictions, better edge performance globally |
| **Render (MVP API)** | Standard | $25 | No sleep, 2 GB RAM, handles ~200 concurrent connections |
| **Supabase** | Pro | $25 | No pausing, 8 GB DB, daily backups, PITR (point-in-time recovery) |
| **Cloudflare** | Free | $0 | DDoS protection, WAF, CDN, global anycast DNS — put in front of Render |
| **Sentry** | Team | $26 | Crash reporting — essential when solo, no one else watching prod |
| **UptimeRobot** | Free | $0 | Pings API every 5 min, emails you if down |
| **Resend** (email) | Free | $0 | 3,000 emails/month free — for welcome emails, weekly summaries |
| **EAS Build** | Free | $0 | 30 builds/month, more than enough at launch |
| **Namecheap domains** | Existing | ~$2.50 | Already paid |
| **Apple Developer** | Existing | ~$8.25 | $99/year already |
| **TOTAL** | | **~$106/mo** | + Stripe 2.9%+$0.30/txn |

**Variable costs on top:**
- Anthropic API: ~$0.003/message → $15/mo at 100 users
- Supabase bandwidth overage: unlikely until 500+ users ($0.09/GB over 250 GB)
- Render outbound bandwidth: $0.10/GB over 100 GB free

**Realistic all-in at launch: ~$130–160/month**

---

## Global Launch — Additional Requirements

### GDPR (EU users — legally required)
- [ ] Privacy policy must include: right of access, right to erasure, data portability, legal basis for processing, DPO contact (can be your email)
- [ ] Cookie consent banner on web app (even minimal analytics triggers this)
- [ ] User data deletion endpoint — confirm `/api/v1/health-data/source/{source}` covers all user data; add full account deletion if missing
- [ ] Data Processing Agreements (DPAs) with: Anthropic, Supabase, Stripe (all three have standard DPAs you click-through)
  - Anthropic DPA: https://privacy.anthropic.com/en/dpa
  - Supabase DPA: available in Supabase dashboard under Settings → Legal
  - Stripe DPA: auto-accepted when you enable Stripe for EU
- [ ] Supabase region: confirm your project is on `us-east-1`. For EU users, latency is ~120ms — acceptable for v1. Add EU region in v1.1 if EU becomes significant.

### CCPA (California users)
- [ ] "Do Not Sell My Personal Information" link in privacy policy footer
- [ ] Note: Vitalix does not sell data, so this is just a disclosure statement

### Stripe global / VAT
- [ ] Enable **Stripe Tax** in Stripe Dashboard (Settings → Tax)
  - Automatically calculates VAT/GST for EU, UK, Australia, Canada
  - $0.50 per transaction when tax is calculated, or included in Stripe fees
- [ ] Set your business address correctly in Stripe — determines tax nexus
- [ ] Price display: Keep USD for v1 (Stripe handles currency conversion display)

### App Store global availability
- [ ] App Store Connect → Pricing and Availability → select all territories (or all except restricted regions)
- [ ] Google Play Console → set distribution to all countries

### Content for global users
- [ ] Health disclaimer in English is fine for v1 — most health apps launch English-first
- [ ] Avoid health claims that are prohibited in EU (e.g., "treats", "diagnoses", "cures")
- [ ] Use "wellness" and "insights" language, not medical language

---

## Critical Blockers (10 items — nothing ships without these)

| # | Blocker | How to fix | Time |
|---|---|---|---|
| B1 | Render API sleeps after 15 min | Upgrade to Standard plan | 30 min |
| B2 | Supabase free tier pauses | Upgrade to Pro | 10 min |
| B3 | Vercel hobby (no commercial use) | Upgrade to Pro | 10 min |
| B4 | EAS project ID not set | `cd apps/mobile && eas init` | 10 min |
| B5 | `google-service-account.json` missing | Download from Play Console (see below) | 20 min |
| B6 | Mobile `EXPO_PUBLIC_API_URL` = localhost | Set to `https://api.vitalix.health` | 5 min |
| B7 | No privacy policy page | Create `frontend/src/app/(legal)/privacy/page.tsx` | 2 hrs |
| B8 | No terms of service page | Create `frontend/src/app/(legal)/terms/page.tsx` | 1 hr |
| B9 | Stripe on test keys | Swap to live keys + live webhook | 30 min |
| B10 | `USE_SANDBOX=false` not set in prod | Set in Render environment variables | 5 min |

---

## Infrastructure Setup (Day 1–2)

### Step 1 — Render upgrade
1. Go to render.com → your MVP API service → Settings → Instance Type → upgrade to **Standard ($25/mo)**
2. Add environment variables in Render dashboard (copy from `.env`, never commit secrets):
   ```
   USE_SANDBOX=false
   OURA_USE_SANDBOX=false
   OURA_CLIENT_ID=...
   OURA_CLIENT_SECRET=...
   OURA_REDIRECT_URI=https://app.vitalix.health/oura/callback
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_live_...
   ANTHROPIC_API_KEY=...
   SUPABASE_URL=...
   SUPABASE_SERVICE_KEY=...
   JWT_SECRET_KEY=...
   PYTHONPATH=/app
   ```
3. Set start command: `uvicorn apps.mvp_api.main:app --host 0.0.0.0 --port 8100`

### Step 2 — Cloudflare in front of Render (free, takes 20 min)
1. Add your domain in Cloudflare (free account)
2. Change Namecheap nameservers to Cloudflare's nameservers
3. Add DNS record: `api.vitalix.health` → CNAME → your Render URL → Proxy ON (orange cloud)
4. Add DNS record: `app.vitalix.health` → CNAME → your Vercel URL → Proxy OFF (Vercel handles SSL)
5. Cloudflare → SSL/TLS → Full (strict)
6. Cloudflare → Security → WAF → enable managed rules (free)

This gives you: DDoS protection, rate limiting at the edge, global CDN, and hides your Render URL.

### Step 3 — Supabase Pro upgrade
1. Supabase Dashboard → Settings → Billing → upgrade to Pro
2. Enable Point-in-Time Recovery (PITR) — included in Pro
3. Settings → Legal → accept DPA (required for GDPR)

### Step 4 — DNS records summary (add to Namecheap/Cloudflare)
```
api.vitalix.health    CNAME   your-app.onrender.com     (proxy via Cloudflare)
app.vitalix.health    CNAME   cname.vercel-dns.com      (direct, no Cloudflare proxy)
vitalix.health        CNAME   cname.vercel-dns.com      (marketing/landing)
vitalix.app           CNAME   cname.vercel-dns.com      (redirect to vitalix.health)
```

---

## Stripe Live Migration (Day 2)

1. Stripe Dashboard → top-left toggle → switch to **Live mode**
2. Products → recreate your three tiers:
   - Free (no product needed)
   - Pro: $9.99/month recurring → copy `price_live_xxx` ID
   - Pro+: $19.99/month recurring → copy `price_live_xxx` ID
3. Update Render environment:
   ```
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_PRICE_PRO=price_live_xxx
   STRIPE_PRICE_PRO_PLUS=price_live_xxx
   ```
4. Webhooks → Add endpoint: `https://api.vitalix.health/api/v1/billing/webhook`
   - Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`
   - Copy signing secret → `STRIPE_WEBHOOK_SECRET=whsec_live_...`
5. Enable **Stripe Tax** → Settings → Tax → activate
6. Enable **Stripe Radar** → free fraud protection, on by default in live mode
7. Test with a real $0.01 charge to a real card before launch

**Apple IAP note:** Apple policy requires StoreKit for in-app purchases triggered within iOS apps. For v1, use this workaround: show a "Manage Subscription" button that opens Safari → `https://app.vitalix.health/pricing`. Users subscribe on web, app reflects the subscription via your backend. No 30% Apple cut, no StoreKit implementation needed.

---

## Stress Test Plan (Day 3–5)

### Run automated tests
```bash
cd /Users/pulimap/PersonalHealthAssistant

# Unit + integration tests (offline safe)
PYTHONPATH=. pytest tests/test_ai_guard.py -v

# Backend integration tests (needs API running)
PYTHONPATH=. pytest tests/test_robustness.py -v --tb=short -m "not slow"

# Include rate-limit test (fires 21 requests, ~60s)
PYTHONPATH=. pytest tests/test_robustness.py -v -m slow
```

### Run load test with Locust
```bash
pip install locust python-jose[cryptography] python-dotenv

# Interactive mode — open http://localhost:8089, set 50 users
locust -f tests/locustfile.py --host=http://localhost:8100

# Headless against localhost (quick smoke test)
locust -f tests/locustfile.py --host=http://localhost:8100 \
  --users=30 --spawn-rate=5 --run-time=3m --headless

# Against production (run after DNS is live)
locust -f tests/locustfile.py --host=https://api.vitalix.health \
  --users=50 --spawn-rate=5 --run-time=5m --headless --csv=tests/load_results
```

**Pass criteria:**
- p95 response time < 2,000ms (all endpoints except `/correlations`)
- Error rate (non-429) < 1%
- Off-topic AI chat returns refusal in < 5s (no LLM call)
- Rate limiter returns 429 at request 21+ per user per minute (not 500 or crash)
- Zero unhandled exceptions in Render logs during test

### Manual mobile stress test (run on real device, not simulator)
Complete the full checklist in `tests/robustness_checklist.md` — mobile sections.
Priority items for solo tester:
1. AI chat rate limit (send 25 messages fast) → should show graceful 429, not crash
2. Oura connect production OAuth flow end-to-end
3. Sync on real device (HealthKit on iPhone, Health Connect on Android)
4. Stripe checkout → payment completes → tier updates in app
5. All 5 tabs with fresh install (cold start, no cached data)

---

## Legal Pages (Day 2–3, can be done in parallel with infra)

### Create these two pages in the Next.js frontend:
- `frontend/src/app/(legal)/privacy/page.tsx` → hosted at `vitalix.health/privacy`
- `frontend/src/app/(legal)/terms/page.tsx` → hosted at `vitalix.health/terms`

### Privacy policy must cover (for global GDPR + App Store):
- What data: health metrics, symptoms, lab results, device connections, usage analytics
- How stored: Supabase (AWS us-east-1), encrypted in transit (TLS 1.3) and at rest (AES-256)
- How used: personalized AI health insights, not sold to third parties
- Third parties: Anthropic (AI processing), Oura (device data), Stripe (billing), Vercel (web hosting)
- Retention: data kept until account deletion; deleted within 30 days of request
- Rights (GDPR): access, erasure, portability, restriction, objection
- Rights (CCPA): know, delete, opt-out of sale (we don't sell data)
- Data deletion: Settings → Delete Account (add this flow if missing)
- Contact: privacy@vitalix.health
- Effective date + "last updated" field

### Terms of service must cover:
- Service description: consumer wellness app, NOT a medical device
- Medical disclaimer: "Not medical advice. Consult a qualified healthcare provider."
- Age requirement: 18+ (health data)
- Subscription terms: monthly billing, cancel anytime, no refunds on used periods
- Acceptable use: no automated scraping, no sharing accounts
- Intellectual property: user owns their health data
- Limitation of liability
- Governing law: your state (specify)
- Dispute resolution

### Medical disclaimer (also add to mobile onboarding screen):
> "Vitalix is a personal wellness app, not a medical device. Information provided is for general wellness purposes only and does not constitute medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional for medical decisions."

---

## iOS Release Checklist (Day 5–10)

### App Store Connect setup
- [ ] Log into https://appstoreconnect.apple.com
- [ ] App: Vitalix (ID: 6760475193)
- [ ] App Information → Primary Language: English (US), Category: Health & Fitness
- [ ] Pricing: Free (with in-app purchases listed)
- [ ] App Privacy → Data Types:
  - Health & Fitness: yes (heart rate, steps, sleep, workout, HealthKit data)
  - Identifiers: User ID (for account), Email (for auth)
  - Usage Data: crash data, performance logs
  - For each: purpose = App Functionality, linked to user
- [ ] Age Rating: fill questionnaire → result should be 4+
- [ ] HealthKit capability: App Store Connect → your app → Capabilities → enable HealthKit

### Screenshots (take on iPhone 15 Pro Max simulator)
Minimum 3 per size. Suggested:
1. Home dashboard with health score + metric cards
2. AI chat screen showing a health response
3. Devices screen showing Apple Health connected
4. Insights screen
5. Profile screen

Sizes required:
- [ ] 6.7" (1290×2796): iPhone 15 Pro Max
- [ ] 6.1" (1179×2556): iPhone 15 — can auto-generate from 6.7" in App Store Connect

### App metadata
- [ ] Name: **Vitalix**
- [ ] Subtitle: **AI-Powered Health Intelligence** (30 chars)
- [ ] Description (write 4,000 chars — tell the story: Oura + HealthKit + AI)
- [ ] Keywords: `health,HRV,Oura Ring,sleep tracker,AI wellness,heart rate,HealthKit,fitness` (100 chars)
- [ ] Support URL: `https://vitalix.health/support` (create a simple page or mailto:)
- [ ] Marketing URL: `https://vitalix.app`
- [ ] Privacy Policy URL: `https://vitalix.health/privacy`

### Build and submit
```bash
cd apps/mobile

# One-time EAS setup
eas login
eas init    # generates EXPO_PUBLIC_EXPO_PROJECT_ID, adds to app.json

# Preview build → TestFlight internal (no Apple review)
eas build --platform ios --profile preview
# After build completes (~15 min), submit to TestFlight:
eas submit --platform ios

# OR for App Store production build:
eas build --platform ios --profile production
eas submit --platform ios
```

### TestFlight — internal (Days 7–14, no Apple review)
- Add testers in App Store Connect → TestFlight → Internal Testing → add emails
- Maximum 100 internal testers (must be in your Apple Developer team or invited)
- Build available within minutes

### TestFlight — external beta (Days 10–21, 1-day Apple review)
- App Store Connect → TestFlight → External Groups → create group → add testers
- Submit build for External Beta Review (~1 business day)
- Share link: `testflight.apple.com/join/...` — post in Oura subreddit, ProductHunt

### App Store submission (Day 21+)
- Create new version in App Store Connect
- Select production build
- Fill "What's New" (release notes)
- Submit for Review → typically 1–3 business days

---

## Android Release Checklist (Day 5–10, parallel with iOS)

### Get Google service account JSON (one-time setup)
1. Google Play Console → Setup → API access
2. Click "Go to Google Play Android Developer API" → enable it
3. Create service account → Grant "Release Manager" role in Play Console
4. Download JSON key → save as `apps/mobile/google-service-account.json`
5. Add to `.gitignore`:
   ```
   apps/mobile/google-service-account.json
   ```

### Google Play Console setup
1. Create app → App name: Vitalix, Default language: English, App type: App
2. Store listing:
   - Short description (80 chars): "AI health insights from your wearable data"
   - Full description (4,000 chars)
   - Screenshots: 2+ phone screenshots (1080×1920 min)
   - Feature graphic: 1024×500 banner
   - App icon: 512×512 (export from `assets/icon.png`)
3. Content rating → complete questionnaire → should result in "Everyone" or "Teen"
4. Target audience: 18+
5. Data safety form:
   - Health and fitness data: yes, collected, shared with service providers (Anthropic)
   - Personal info (email, user ID): yes, collected
   - Not sold to third parties
   - Users can delete their data
6. Privacy policy: `https://vitalix.health/privacy`

### Build and submit
```bash
cd apps/mobile

# Production AAB (Android App Bundle)
eas build --platform android --profile production

# Submit to internal testing track
eas submit --platform android --profile production
```

### Android testing tracks (do in order)
1. **Internal testing** (instant, your email) → test basic install + launch
2. **Closed testing** (invite specific testers) → 3–5 testers
3. **Open testing** (public beta) → anyone can join
4. **Production** → full release (review can take 3–7 days for new apps)

---

## Sentry Setup (Day 3, 2 hours)

### Backend (FastAPI)
```bash
pip install sentry-sdk[fastapi]
```
In `apps/mvp_api/main.py`, add after imports:
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN", ""),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,  # 10% of requests traced
    environment=os.environ.get("APP_ENV", "development"),
)
```

### Mobile (React Native / Expo)
```bash
cd apps/mobile
npx expo install @sentry/react-native
```
In `app/_layout.tsx`:
```typescript
import * as Sentry from '@sentry/react-native';

Sentry.init({
  dsn: process.env.EXPO_PUBLIC_SENTRY_DSN,
  environment: process.env.APP_ENV ?? 'development',
  tracesSampleRate: 0.1,
});
```

### Add env vars
```
# Render (backend)
SENTRY_DSN=https://xxx@sentry.io/xxx
APP_ENV=production

# apps/mobile/.env.local
EXPO_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
```

Create two Sentry projects: `vitalix-api` and `vitalix-mobile`. Get DSNs from sentry.io.

---

## 4-Week Sprint Plan (Solo Founder)

### Week 1 (Days 1–7) — Fix, Build, Ship to TestFlight
**Day 1–2 (3–4 hours):**
- [ ] Upgrade Render → Standard
- [ ] Upgrade Supabase → Pro
- [ ] Upgrade Vercel → Pro
- [ ] Set up Cloudflare, point domains
- [ ] Copy production env vars to Render dashboard
- [ ] Submit Oura OAuth application (async — takes ~3 days)

**Day 2–3 (4–5 hours):**
- [ ] `eas init` in apps/mobile
- [ ] Set production API URL in mobile `.env.local`
- [ ] Write privacy policy page (can use a template + Claude's help)
- [ ] Write terms of service page
- [ ] Add medical disclaimer to mobile onboarding screen
- [ ] Swap Stripe to live keys, re-register webhook

**Day 3–5 (3–4 hours):**
- [ ] Set up Sentry (backend + mobile)
- [ ] Set up UptimeRobot (15 min — just add a monitor)
- [ ] Run `pytest` test suite against production API
- [ ] Run Locust: `locust -f tests/locustfile.py --host=https://api.vitalix.health --users=30 --spawn-rate=3 --run-time=3m --headless`
- [ ] Fix any issues found

**Day 5–7 (2–3 hours):**
- [ ] App Store Connect: fill metadata, screenshots, App Privacy form
- [ ] `eas build --platform ios --profile preview`
- [ ] Submit to TestFlight internal
- [ ] `eas build --platform android --profile production`
- [ ] Upload to Play Console internal track
- [ ] Add 2–3 friends as TestFlight testers

**Total week 1: ~15–18 hours. Doable solo on evenings + one weekend day.**

---

### Week 2 (Days 7–14) — Internal Testing + Fix
**While friends test, do in parallel:**
- [ ] Monitor Sentry for crashes
- [ ] Set up Play Console store listing (screenshots, description)
- [ ] Submit Android for closed testing
- [ ] Submit iOS for TestFlight external beta review (~1 day)
- [ ] Wait for Oura OAuth approval → test real OAuth flow end-to-end
- [ ] Fix any bugs from testers (budget 2 days)
- [ ] Run full manual stress test checklist (see robustness_checklist.md)

**Tester brief for your friends:**
1. Create an account with real email
2. Connect Apple Health / Health Connect → sync
3. Chat with the AI (10 messages, including 2 off-topic)
4. Try to subscribe to Pro (use test card 4242 4242 4242 4242 if on test Stripe, or just browse pricing)
5. Report: any crashes, slow screens, confusing UX

---

### Week 3 (Days 14–21) — External Beta + Store Submissions
- [ ] External TestFlight beta live (post link on Reddit r/ouraring, r/HealthFitness, ProductHunt Ship)
- [ ] Monitor feedback, fix critical issues
- [ ] `eas build --platform ios --profile production` → submit for App Store review
- [ ] Android: promote from closed to open testing → then production

**While waiting for reviews:**
- [ ] Write App Store preview video (screen record + Descript)
- [ ] Set up landing page on vitalix.app
- [ ] Prepare launch tweet / social posts
- [ ] Set up support@vitalix.health email

---

### Week 4 (Days 21–28) — Launch
- [ ] App Store approval arrives (1–3 days after submission)
- [ ] Google Play approval arrives (3–7 days for new apps)
- [ ] Release iOS: App Store Connect → Release This Version
- [ ] Release Android: Play Console → Release to Production
- [ ] Announce: ProductHunt, Twitter/X, Reddit, Oura community
- [ ] Monitor Sentry + UptimeRobot for first 48 hours closely

---

## Where Oura OAuth Fits (Async track — start Day 1)

Oura OAuth review takes ~3 days. Start immediately, it runs in parallel with everything else.

1. Register at https://cloud.ouraring.com/oauth/applications
2. Fill: App name = Vitalix, Redirect URIs:
   - `https://app.vitalix.health/oura/callback` (web)
   - `vitalix://oura-callback` (mobile deep link)
3. Scopes: `daily personal heartrate workout session spo2`
4. Submit for review
5. While waiting: test sandbox mode still works
6. When approved: add `OURA_CLIENT_ID` + `OURA_CLIENT_SECRET` to Render env, set `OURA_USE_SANDBOX=false`

---

## Quick Reference — All Commands

```bash
# Tests
cd /Users/pulimap/PersonalHealthAssistant
PYTHONPATH=. pytest tests/test_ai_guard.py tests/test_robustness.py -v --tb=short -m "not slow"

# Load test (localhost)
pip install locust
locust -f tests/locustfile.py --host=http://localhost:8100 --users=30 --spawn-rate=5 --run-time=3m --headless

# Load test (production)
locust -f tests/locustfile.py --host=https://api.vitalix.health --users=50 --spawn-rate=5 --run-time=5m --headless

# EAS one-time setup
cd apps/mobile && npm install -g eas-cli && eas login && eas init

# TestFlight build
cd apps/mobile && eas build --platform ios --profile preview && eas submit --platform ios

# Production builds
cd apps/mobile && eas build --platform ios --profile production
cd apps/mobile && eas build --platform android --profile production
cd apps/mobile && eas submit --platform android
```

---

## Decisions — Recommendations Based on Your Context

| Decision | Recommendation | Reason |
|---|---|---|
| IAP strategy | **Stripe web-only for v1** | Saves weeks of StoreKit work, zero 30% Apple cut |
| HIPAA | **No for v1** (wellness disclaimer) | You're B2C wellness, not a covered entity |
| Nutrition service | **Deploy in Week 2** | It's built, just needs a Render service + env |
| Render tier | **Standard $25** | Handles global traffic without sleep issues |
| Support email | **support@vitalix.health** | Builds trust, required by App Store |
| Beta testers beyond friends | **Post on r/ouraring** | Perfect audience — Oura users who want more insights |
| Monitor solo | **Sentry + UptimeRobot** | Gets you paged when something breaks at 3am |
