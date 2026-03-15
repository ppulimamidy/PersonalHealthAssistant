# Vitalix Pre-Launch Robustness QA Checklist

**Generated:** 2026-03-15
**Demo user:** sarah.chen.demo@example.com (UUID: 22144dc2-f352-48aa-b34b-aebfa9f7e638)

Automated tests cover the backend items. Frontend and mobile items are manual.

---

## Run automated tests

```bash
cd /Users/pulimap/PersonalHealthAssistant
PYTHONPATH=/Users/pulimap/PersonalHealthAssistant \
  pytest tests/test_ai_guard.py tests/test_robustness.py -v --tb=short -m "not slow"

# Include rate-limit test (slow):
pytest tests/test_robustness.py -v -m slow
```

---

## Backend — MVP API (port 8100)

### Health check
- [ ] `GET /health` → 200, `{"status": "healthy"}`

### Auth enforcement
- [ ] All protected endpoints → 401 without token
- [ ] Garbage token → 401
- [ ] Expired token → 401
- [ ] Valid token → 200

### Health Data Ingest (`POST /api/v1/health-data/ingest`)
- [ ] Valid payload → 201, `accepted >= 1`
- [ ] No auth → 401
- [ ] Invalid source (`fitbit_invalid`) → 422
- [ ] > 500 data points → 422
- [ ] Duplicate ingest same date/metric → 201 (idempotent upsert)
- [ ] `GET /api/v1/health-data/status` with auth → 200

### AI Agents — List
- [ ] 5+ agents returned with correct fields (id, agent_type, agent_name, capabilities, is_active)

### AI Agents — Chat
- [ ] No auth → 401
- [ ] Missing `message` field → 422
- [ ] Empty `message` → 422
- [ ] `message` > 2000 chars → 422
- [ ] **Off-topic message** → 200 BUT response contains refusal text (no LLM call)
- [ ] Health message → 200, non-empty assistant reply, not the refusal
- [ ] Conversation `id` returned in response
- [ ] Subsequent message with `conversation_id` appends to existing thread

### AI Agents — Conversations
- [ ] `GET /conversations` → 200, list
- [ ] `GET /conversations/{nonexistent}` → 404

### Core endpoints (authenticated)
- [ ] `GET /api/v1/insights/` → 200 or 404
- [ ] `GET /api/v1/symptoms/` → 200 or 404
- [ ] `POST /api/v1/symptoms/` empty body → 422
- [ ] `GET /api/v1/health/timeline` → 200 or 404
- [ ] `GET /api/v1/health-score` → 200 or 404
- [ ] `GET /api/v1/correlations/` → 200 or 404

### Input validation
- [ ] Non-UUID path param → 404 or 422
- [ ] Invalid date format in ingest → 201 or 422 (consistent)

### Rate limiting
- [ ] 21 chat requests in 60s → at least one 429

---

## Backend — Nutrition Service (port 8007)

- [ ] `GET /health` → 200
- [ ] `GET /api/v1/nutrition/search-foods?query=apple` no auth → 401
- [ ] `GET /api/v1/nutrition/search-foods?query=apple` with auth → 200 (or 500 if USDA key missing)
- [ ] `GET /api/v1/nutrition/nutrition-summary` with auth → 200 or 404
- [ ] `GET /api/v1/nutrition/daily-nutrition/not-a-date` → 422
- [ ] `POST /api/v1/nutrition/log-meal` no auth → 401

---

## AI Agent Topic Guard (automated via `test_ai_guard.py`)

### Must be blocked (off-topic)
- [ ] "Write me a Python function to sort a list of integers"
- [ ] "Can you debug this JavaScript code for me?"
- [ ] "Explain how Kubernetes works"
- [ ] "Tell me a joke about programmers"
- [ ] "Write a poem about the ocean at sunset"
- [ ] "Write a short story about a dragon"
- [ ] "Explain quantum entanglement to me like I'm five"
- [ ] "What is string theory and how does it relate to black holes?"
- [ ] "Give me stock market investment advice"
- [ ] "Should I buy Bitcoin right now? I need investment tips"
- [ ] "What is the capital of Australia?"
- [ ] "Translate 'good morning' into Japanese"
- [ ] "Help me plan a trip to Bali"
- [ ] "Proofread my cover letter for me"
- [ ] "Write me a Python script for web scraping"

### Must be allowed (health on-topic)
- [ ] "What should I eat to lower my blood sugar?"
- [ ] "I've been feeling really tired lately, what could be causing that?"
- [ ] "Can you explain the side effects of metformin?"
- [ ] "My HRV has been low this week, what does that mean?"
- [ ] "I logged a headache and fatigue symptom, do you see any patterns?"
- [ ] "What foods are high in magnesium?"
- [ ] "How does sleep affect my immune system?"
- [ ] "I'm on lisinopril for hypertension — any interaction concerns?"
- [ ] "My A1C came back at 6.4, is that pre-diabetic?"
- [ ] "How many steps per day should I aim for to improve cardiovascular health?"

---

## Frontend — Web App (port 3000)

### Page loads (no console errors)
- [ ] `/` → 200, renders without JS errors
- [ ] `/login` → 200
- [ ] `/dashboard` (authenticated) → 200, no console errors
- [ ] `/symptoms` → 200
- [ ] `/insights` → 200
- [ ] `/profile` → 200
- [ ] `/devices` → 200

### Auth flow
- [ ] Login with valid demo credentials → redirects to dashboard
- [ ] Login with wrong password → error message shown
- [ ] Logout → session cleared, redirected to login
- [ ] Refresh page while logged in → session persists
- [ ] Direct visit to `/dashboard` without auth → redirected to login

### Key feature rendering
- [ ] Dashboard shows health score widget
- [ ] Dashboard shows at least one data card
- [ ] Symptoms page shows symptom log or empty state (not blank/broken)
- [ ] Insights page shows AI insight cards or empty state
- [ ] Devices page shows Google Health Connect / Apple Health connection status
- [ ] Timeline renders (no infinite spinner)

### Error resilience
- [ ] Stop MVP API → frontend shows error state, does not crash
- [ ] Restart MVP API → frontend recovers on next request

---

## Mobile — iOS (Simulator)

### Launch & auth
- [ ] App starts without crash on fresh launch
- [ ] Splash screen appears then dismisses
- [ ] Login screen renders
- [ ] Login with demo credentials → Home tab loads
- [ ] Logout and re-login works

### Navigation
- [ ] All 5 bottom tabs reachable (Home, Insights, Log, Ask AI, Profile)
- [ ] Back navigation works on all nested screens
- [ ] No tab causes crash on first visit

### Health data
- [ ] Devices screen → Connect & Sync → HealthKit permission prompt appears (device) or mock data synced (simulator)
- [ ] Sync completes, metric cards populate with data
- [ ] Second sync → "No new data since last sync" message shown (simulator)

### AI Chat
- [ ] Chat screen opens, agent list visible
- [ ] Sending health message → response displayed
- [ ] **Sending off-topic message** → polite refusal response (not blank/crash)
- [ ] Conversation persists after navigating away and back

### Offline
- [ ] Airplane mode → graceful error shown, app does not crash
- [ ] Reconnect → app resumes normally

---

## Mobile — Android (Emulator)

### Launch & auth
- [ ] App installs and launches (PID visible in adb logcat)
- [ ] Metro bundler connection established
- [ ] Login with demo credentials → Home tab loads
- [ ] DNS resolves Supabase host (emulator started with `-dns-server 8.8.8.8`)

### Health Connect
- [ ] Devices screen → Connect & Sync → Health Connect permission dialog appears (device) or mock data synced (emulator)
- [ ] `HealthConnectPermissionDelegate.setPermissionDelegate(this)` prevents lateinit crash
- [ ] Mock sync completes, metric cards populate

### AI Chat
- [ ] Sending off-topic message → refusal response shown

### Navigation
- [ ] All bottom tabs accessible without crash

---

## Known issues / exclusions at launch

| Item | Status | Notes |
|------|--------|-------|
| Oura Ring OAuth (production) | Sandbox only | Full OAuth after launch |
| HealthKit on iOS device | Requires Apple Developer Portal toggle | Device testing pre-App Store |
| Push notifications | Configured but not tested end-to-end | Post-launch |
| Rate limit recovery | Manual test only | Automated test fires 21 requests |
