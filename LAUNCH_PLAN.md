# Vitalix Production Launch Plan
**Target:** TestFlight live in 2 weeks · Real users in 4 weeks
**Generated:** 2026-03-15
**Domains:** vitalix.app · vitalix.health
**App Store Connect:** 6760475193 · Team: QAL9P7889F

---

## Open Questions (answer these first — they gate decisions)

| # | Question | Why it matters |
|---|---|---|
| Q1 | US-only launch or global? | GDPR compliance, Stripe currency, store availability |
| Q2 | Solo founder or team? | On-call monitoring, review workload |
| Q3 | Monthly infra budget comfortable with? | Tier choices below |
| Q4 | How many TestFlight testers lined up? | Sets urgency on build |
| Q5 | HIPAA compliance intent? | Changes hosting, BAA requirements, storage encryption |
| Q6 | Nutrition service — deploy it or hold for v1.1? | Affects infra scope |

---

## Critical Blockers (nothing ships without these)

| # | Blocker | Fix | Time |
|---|---|---|---|
| B1 | Render hobby API sleeps after 15 min of inactivity | Upgrade to paid tier (see infra section) | 30 min |
| B2 | Supabase free tier pauses after 1 week inactivity | Upgrade to Pro | 10 min |
| B3 | EAS project ID not set | `cd apps/mobile && eas init` | 10 min |
| B4 | `google-service-account.json` missing | Download from Play Console | 20 min |
| B5 | Mobile prod API URL still `localhost` | Set `EXPO_PUBLIC_API_URL` to production domain | 5 min |
| B6 | No privacy policy page | Required by Apple, Google, and Stripe | 2 hrs |
| B7 | No terms of service page | Required by Apple, Google, and Stripe | 1 hr |
| B8 | Stripe test keys active in production | Swap to live keys, live webhook | 30 min |
| B9 | Oura OAuth credentials not set | `OURA_CLIENT_ID` + `OURA_CLIENT_SECRET` from Oura portal | Async (Oura review ~3 days) |
| B10 | `oura_connections` Supabase table (SQL already run?) | Confirm in Supabase dashboard | 5 min |

---

## Infrastructure Upgrade Plan

### Current (hobby) → Production

| Service | Current | Problem | Upgrade | Monthly cost |
|---|---|---|---|---|
| **Render (MVP API)** | Free | Sleeps after 15 min, 512 MB RAM | Starter ($7) or Standard ($25) | $7–25 |
| **Supabase** | Free | Pauses, 500 MB DB, no backups | Pro | $25 |
| **Vercel (Frontend)** | Hobby | No commercial use allowed | Pro | $20 |
| **EAS Build** | Free | 30 builds/month | Free is fine initially | $0 |
| **Render (Nutrition)** | Not deployed | N/A | Deploy when ready | $7 |

**Minimum viable production infra: ~$52/month**
**Recommended (with nutrition service): ~$77/month**

### Domain Setup (Namecheap → Production)

- [ ] Point `api.vitalix.health` → Render service (A record or CNAME)
- [ ] Point `app.vitalix.health` → Vercel deployment
- [ ] Point `vitalix.app` → marketing/landing page (or same as app.vitalix.health)
- [ ] Enable Cloudflare (free tier) in front of API for DDoS protection + caching
- [ ] SSL auto-provisioned by Vercel and Render (nothing to do beyond DNS)

### Environment Variables — Production Values Needed

**`apps/mvp_api/.env` (production)**
```
USE_SANDBOX=false
OURA_USE_SANDBOX=false
OURA_CLIENT_ID=<from Oura portal>
OURA_CLIENT_SECRET=<from Oura portal>
OURA_REDIRECT_URI=https://app.vitalix.health/oura/callback
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_live_...
ANTHROPIC_API_KEY=<existing>
SUPABASE_URL=<existing>
SUPABASE_SERVICE_KEY=<existing>
```

**`apps/mobile/.env.local` (production build)**
```
EXPO_PUBLIC_API_URL=https://api.vitalix.health
EXPO_PUBLIC_SUPABASE_URL=<existing>
EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY=<existing>
EXPO_PUBLIC_EXPO_PROJECT_ID=<from eas init>
```

---

## Stress Test Plan

### Step 1 — Automated backend tests (run now)
```bash
cd /Users/pulimap/PersonalHealthAssistant
PYTHONPATH=. pytest tests/test_ai_guard.py tests/test_robustness.py -v --tb=short
# Include rate-limit test:
PYTHONPATH=. pytest tests/test_robustness.py -v -m slow
```

### Step 2 — Load test with Locust
```bash
pip install locust
locust -f tests/locustfile.py --host=https://api.vitalix.health \
  --users=50 --spawn-rate=5 --run-time=5m --headless
```
File: `tests/locustfile.py` (to be written — see task list)

**Pass criteria:**
- p95 response time < 2s for all endpoints
- Zero 500 errors under 50 concurrent users
- Rate limiter returns 429 (not 500) at request 21+ per user per minute
- API recovers within 30s after load spike

### Step 3 — Mobile stress test checklist (real device, not simulator)

**Auth**
- [ ] Login with valid credentials → home loads < 3s
- [ ] Login with wrong password → clear error message shown
- [ ] Logout → session cleared, login screen shown
- [ ] Force-kill app during login → no stuck state on relaunch

**AI Chat**
- [ ] Send 25 messages rapidly → 429 shown gracefully after 20th, not blank/crash
- [ ] Send off-topic message ("write me python code") → polite refusal shown
- [ ] Health message → response appears within 10s
- [ ] Long message (2000 chars) → accepted
- [ ] Message over 2000 chars → validation error shown
- [ ] Close app mid-response → message still arrives on reopen (or retries)

**Health Sync**
- [ ] iOS: HealthKit sync on real iPhone → data appears in metric cards
- [ ] Android: Health Connect sync on real Android → data appears
- [ ] Sync twice → "no new data since last sync" shown (idempotent)
- [ ] Sync while offline → graceful error shown, not crash
- [ ] Oura: Connect via OAuth → authorization page opens in browser → returns to app → connected shown

**Billing**
- [ ] Tap "Upgrade to Pro" → Stripe checkout opens
- [ ] Complete test payment → tier updates to Pro in app
- [ ] Cancel checkout → returns to app without error

**Navigation**
- [ ] All 5 bottom tabs reachable without crash
- [ ] Back navigation works on all nested screens
- [ ] Deep link `vitalix://oura-callback?code=test` handled without crash

**Offline / Edge cases**
- [ ] Airplane mode → graceful error on all network calls
- [ ] Reconnect → app resumes normally
- [ ] Very slow connection (throttle to 3G) → loading states shown, no timeout crash
- [ ] Low memory (open 20+ apps, return) → Vitalix state preserved

### Step 4 — Web app stress test
- [ ] Login flow works end-to-end on vitalix.health domain
- [ ] Oura connect flow: auth URL → Oura page → `/oura/callback` → redirects to /devices
- [ ] Stripe checkout opens and completes
- [ ] All dashboard pages load without JS console errors
- [ ] API down → frontend shows error state, does not crash

---

## Stripe — Switch to Live

- [ ] Go to Stripe Dashboard → toggle from Test to Live mode
- [ ] Create Live products matching test products (Free, Pro $9.99, Pro+ $19.99)
- [ ] Copy live price IDs → update `STRIPE_PRICE_PRO` and `STRIPE_PRICE_PRO_PLUS` in production env
- [ ] Update `STRIPE_SECRET_KEY` to `sk_live_...`
- [ ] Re-register webhook endpoint: `https://api.vitalix.health/api/v1/billing/webhook`
  - Events to listen for: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`
- [ ] Update `STRIPE_WEBHOOK_SECRET` to live webhook signing secret
- [ ] Test live Stripe with a real $0.50 charge to verify end-to-end
- [ ] Enable Stripe Radar (free) for fraud protection
- [ ] **For Apple/Google IAP** *(future)*: Apple and Google each take 15-30% of IAP revenue; Stripe takes 2.9%+$0.30. Web-based subscription via Stripe avoids store cut but in-app upgrades for iOS must use Apple IAP if triggered from within the app (Apple policy). Two options:
  - Option A (simpler): Upgrade only via web app → no Apple cut
  - Option B: Implement StoreKit 2 (iOS) + Google Play Billing alongside Stripe

**⚠️ Apple IAP note:** If your iOS app lets users subscribe from within the app, Apple requires you use StoreKit. Pointing users to a web page to subscribe from within the app is against App Store guidelines. Recommended: show a "Manage subscription" link that opens Safari → avoids StoreKit complexity at launch.

---

## Legal / Compliance Pages Needed

Both app stores and Stripe require these before you can go live.

### Privacy Policy (REQUIRED)
Must cover:
- What health data you collect (symptoms, vitals, sleep, HRV, steps, lab results)
- How it's stored (Supabase, hosted on AWS us-east-1)
- How it's used (AI analysis, not sold to third parties)
- Data deletion process
- Third parties: Anthropic (AI), Oura (device data), Stripe (billing)
- Contact email for data requests
- **If US-only:** CCPA section required for California users
- **If global:** GDPR section required (right to erasure, data portability)

**⚠️ HIPAA note:** Vitalix processes health data but is a wellness/consumer app, not a covered entity. You are NOT required to be HIPAA compliant unless you contract with health insurers or providers. However, consider adding language that Vitalix is "not a HIPAA-covered entity and does not provide medical advice."

Hosting: Create at `https://vitalix.health/privacy` (static Next.js page)

### Terms of Service (REQUIRED)
Must cover:
- Not a medical device, not medical advice
- User age requirements (13+ COPPA, 18+ for medical content)
- Subscription terms, cancellation policy
- Limitation of liability
- Governing law (your state)

Hosting: Create at `https://vitalix.health/terms`

### Medical Disclaimer (REQUIRED for health apps)
Apple specifically checks this. Must be visible in the app, not just on website.
Add to onboarding screen and Settings.

---

## iOS Release Checklist

### Prerequisites
- [ ] Fix B3: `eas init` to set project ID
- [ ] Fix B5: production API URL in mobile env
- [ ] Privacy policy live at a real URL
- [ ] Terms of service live at a real URL
- [ ] Medical disclaimer in onboarding screen

### App Store Connect Setup
- [ ] Log in to https://appstoreconnect.apple.com (App ID: 6760475193)
- [ ] App Information: confirm bundle ID `com.vitalix.app`, category = Health & Fitness
- [ ] App Privacy → fill Data Types section (health data, identifiers, usage data)
- [ ] Age Rating → complete questionnaire (select "No" for most, app is 4+)
- [ ] Capabilities → enable HealthKit in App Store Connect (separate from code)
- [ ] Pricing → Free with In-App Purchases (or free download)

### Screenshots Required (use simulator or real device)
- [ ] iPhone 6.7" (iPhone 15 Pro Max) — minimum 3 screens
- [ ] iPhone 6.1" (iPhone 15) — minimum 3 screens
- [ ] iPad Pro 12.9" — only if you support iPad
- Suggested screens: Home dashboard, AI chat, Health devices, Insights, Profile

### App Metadata
- [ ] App name: **Vitalix**
- [ ] Subtitle: "Your Personal Health Intelligence" (30 chars max)
- [ ] Description: (write 4000 char description)
- [ ] Keywords: `health tracker,HRV,Oura,sleep,AI health,wellness` (100 chars max)
- [ ] Support URL: `https://vitalix.health/support` (or email)
- [ ] Marketing URL: `https://vitalix.app`
- [ ] Privacy Policy URL: `https://vitalix.health/privacy`

### Build & Submit to TestFlight
```bash
cd apps/mobile

# Step 1: Set production env
cp .env.local .env.local.backup
# Edit .env.local with production values

# Step 2: Build for TestFlight
eas build --platform ios --profile preview
# This takes ~15 min, uploads to EAS servers

# Step 3: Submit to TestFlight
eas submit --platform ios --profile production
# OR download .ipa from EAS and upload manually via Transporter

# Step 4: In App Store Connect → TestFlight → Add testers
```

### TestFlight Internal Testing (Week 1-2)
- Internal group: up to 100 testers, no Apple review
- Add testers by email in App Store Connect → TestFlight → Internal Testing
- Share TestFlight link

### TestFlight External Beta (Week 2+)
- Up to 10,000 external testers
- Requires Apple beta review (~1 day)
- Create external group, submit for review

### App Store Submission (Week 3-4)
```bash
eas build --platform ios --profile production
eas submit --platform ios
```
Then in App Store Connect: select the build, fill release notes, submit for review.
Apple review typically takes 1–3 business days.

---

## Android Release Checklist

### Prerequisites
- [ ] Fix B4: Download `google-service-account.json` from Google Play Console
  - Play Console → Setup → API access → Create service account → Grant permissions
  - Download JSON → place at `apps/mobile/google-service-account.json`
  - **Add to .gitignore** (it's a secret key)
- [ ] Fix B3: `eas init`

### Google Play Console Setup
- [ ] Create app at https://play.google.com/console
- [ ] App name: **Vitalix**, Language: English, App type: App, Category: Health & Fitness
- [ ] Set up store listing (description, screenshots, icon)
- [ ] Complete Data safety form (Health and fitness data collected, purpose: app functionality)
- [ ] Content rating questionnaire
- [ ] Target audience: 18+ (health data)
- [ ] Privacy policy URL required here too

### Screenshots Required
- [ ] Phone screenshots (minimum 2): 1080×1920 or similar
- [ ] 7-inch tablet (optional)
- [ ] Feature graphic: 1024×500 px banner

### Build & Submit
```bash
cd apps/mobile

# Step 1: Build release AAB
eas build --platform android --profile production
# Downloads a signed .aab

# Step 2: Submit to internal testing track
eas submit --platform android --profile production
# OR upload .aab manually in Play Console

# Step 3: Internal testing → promote to Closed testing → Open testing → Production
```

Google review for new apps: 3–7 business days for first submission.

---

## Parallel Work Schedule (4-week plan)

### Days 1–3 (Immediate — while waiting on Oura OAuth approval)
**Do in parallel:**
- [ ] Upgrade Render to paid tier (30 min)
- [ ] Upgrade Supabase to Pro (10 min)
- [ ] Upgrade Vercel to Pro (10 min)
- [ ] Point domains in Namecheap → Render and Vercel (30 min + DNS propagation)
- [ ] `eas init` in apps/mobile (10 min)
- [ ] Swap Stripe to live keys in production env (30 min)
- [ ] Write privacy policy page (2 hrs) — **submit Oura OAuth application in parallel**
- [ ] Write terms of service page (1 hr)
- [ ] Write locust stress test file (1 hr, or ask Claude to write it)
- [ ] Add medical disclaimer to onboarding screen in mobile app (30 min)

**Waiting on:** Oura OAuth approval (~3 days), DNS propagation (~1 hr)

### Days 3–7 (Build week)
**Do in parallel:**
- [ ] Run locust load test against production API
- [ ] Run full automated test suite against production endpoints
- [ ] Fix any issues found
- [ ] Build iOS preview build: `eas build --platform ios --profile preview`
- [ ] Build Android release: `eas build --platform android --profile production`
- [ ] App Store Connect: fill metadata, screenshots, App Privacy form
- [ ] Google Play Console: fill store listing, Data safety form

### Days 7–14 (TestFlight + internal testing)
- [ ] Submit iOS to TestFlight internal (no Apple review needed)
- [ ] Submit Android to internal testing track
- [ ] Recruit 10–20 internal testers (friends, family, Oura users)
- [ ] Run manual stress test checklist from this document
- [ ] Fix reported bugs (budget 3–4 days for fixes)
- [ ] Submit iOS for External Beta review (takes ~1 day)
- [ ] Set up error monitoring (Sentry — see below)

### Days 14–21 (External beta + store submission prep)
- [ ] External beta live on TestFlight (up to 10K testers)
- [ ] Submit Android app for Play Store review
- [ ] Monitor Sentry for crashes in beta
- [ ] Fix any critical issues found
- [ ] Prepare App Store submission (production build)
- [ ] Prepare marketing: landing page on vitalix.app, social accounts

### Days 21–28 (Launch week)
- [ ] Submit iOS for App Store review
- [ ] Both store approvals expected by this week
- [ ] Flip `USE_SANDBOX=false` in production API
- [ ] Announce launch

---

## Monitoring & Observability (set up in week 1)

| Tool | Purpose | Cost | Setup time |
|---|---|---|---|
| **Sentry** | Crash reporting for mobile + API | Free (5K errors/mo) | 2 hrs |
| **Render metrics** | API uptime, response times | Included | 0 |
| **Vercel analytics** | Web page performance | Free | 0 |
| **Supabase dashboard** | DB queries, slow logs | Included | 0 |
| **UptimeRobot** | External uptime ping every 5 min | Free | 20 min |

### Sentry setup
```bash
# Mobile
cd apps/mobile && npx expo install @sentry/react-native
# API
pip install sentry-sdk[fastapi]
```

---

## Cost Analysis

### Monthly Infrastructure (production)

| Service | Tier | Monthly |
|---|---|---|
| Vercel | Pro | $20 |
| Render (MVP API) | Starter ($7) or Standard ($25) | $7–25 |
| Render (Nutrition) | Starter | $7 |
| Supabase | Pro | $25 |
| Sentry | Free | $0 |
| UptimeRobot | Free | $0 |
| Cloudflare | Free | $0 |
| Namecheap domains | ~$30/yr | ~$2.50 |
| **Total minimum** | | **~$61/mo** |
| **Total recommended** | | **~$79/mo** |

### Variable costs (per usage)

| Service | Rate | At 100 users | At 1,000 users |
|---|---|---|---|
| Anthropic API | ~$0.003/msg (Sonnet) | ~$15/mo | ~$150/mo |
| Supabase storage overage | $0.021/GB | ~$0 | ~$5/mo |
| Stripe processing | 2.9% + $0.30/txn | ~$5/mo | ~$50/mo |
| EAS builds | Free (30/mo) | $0 | $0–99/mo |

### Revenue vs Cost breakeven

| Users | Free | Pro ($9.99) | Pro+ ($19.99) | Monthly revenue | Monthly cost | Profit |
|---|---|---|---|---|---|---|
| 100 users | 70 | 20 | 10 | $400 | ~$100 | $300 |
| 500 users | 300 | 150 | 50 | $2,498 | ~$200 | $2,298 |
| 1,000 users | 600 | 300 | 100 | $4,998 | ~$350 | $4,648 |

*Assumes 20% free → Pro conversion, 10% Pro → Pro+ at typical SaaS rates*

### Apple / Google store fees
- Apple App Store: **30%** of IAP revenue (15% for small business program if <$1M/yr)
- Google Play: **30%** of IAP revenue (15% for first $1M)
- **Stripe (web)**: 2.9% + $0.30 per transaction
- **Recommendation:** Drive subscriptions via web at launch — zero store cut, full Stripe rate

---

## Missing Items Specific to Vitalix

### Must fix before App Store submission
1. **Medical disclaimer in onboarding** — Apple reviewer will check this for HealthKit apps
2. **Privacy policy live URL** — both stores reject without it
3. **Stripe live keys** — test keys obviously can't charge real users
4. **`USE_SANDBOX=false`** on production API — sandbox returns fake data to real users

### Recommended before launch (not hard blockers)
1. **Sentry** crash reporting — you need visibility when real users hit bugs
2. **Email for support** — App Store requires a support contact
3. **Password reset flow** — verify it works end-to-end on production Supabase
4. **In-app "Report a problem"** link — good practice, reduces negative reviews
5. **Locust load test results** — confirm API handles 50 concurrent users

### Nice to have for marketing (week 3-4)
1. Landing page on vitalix.app (public-facing, not the app)
2. App preview video for App Store (increases conversion ~25%)
3. Press kit with screenshots and logo

---

## Quick Reference — Commands

```bash
# Run tests
cd /Users/pulimap/PersonalHealthAssistant
PYTHONPATH=. pytest tests/test_ai_guard.py tests/test_robustness.py -v

# EAS setup (one-time)
cd apps/mobile && npm install -g eas-cli && eas login && eas init

# TestFlight build
cd apps/mobile && eas build --platform ios --profile preview

# Production iOS build
cd apps/mobile && eas build --platform ios --profile production

# Production Android build
cd apps/mobile && eas build --platform android --profile production

# Submit iOS
cd apps/mobile && eas submit --platform ios

# Submit Android
cd apps/mobile && eas submit --platform android
```

---

## Decisions Needed From You

| Decision | Options | Recommendation |
|---|---|---|
| IAP strategy | Stripe web-only vs StoreKit+Stripe | **Stripe web-only for v1** — faster, no 30% cut |
| HIPAA | Yes (expensive) vs No (wellness app) | **No for v1** — add disclaimer, revisit if B2B |
| Launch region | US-only vs Global | **US-only for v1** — simpler GDPR/compliance |
| Nutrition service | Ship with v1 vs v1.1 | **v1.1** — not blocking core experience |
| Render tier | Starter $7 vs Standard $25 | **Standard $25** if expecting >50 concurrent users |
| Support email | Dedicated support@ vs personal | **support@vitalix.health** — creates trust |
