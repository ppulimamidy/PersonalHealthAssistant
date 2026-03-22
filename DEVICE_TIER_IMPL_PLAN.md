# Device Tier Awareness & Bug Fixes — Implementation Plan

**Date:** 2026-03-22
**Status:** IMPLEMENTED

---

## Changes Summary

### Backend (Python)

| # | Issue | File | Change |
|---|-------|------|--------|
| P2 | Tier classification | `common/metrics/device_tiers.py` | NEW — DeviceTier enum, tier maps, detection, unlock hints |
| P1 | Doctor prep zeros | `apps/mvp_api/api/doctor_prep.py` | Omit sections when no data (None instead of zero-fill), add tier detection |
| P5+P9 | Score confidence | `apps/mvp_api/api/health_score.py` | Add score_confidence, active_pillars, data_tier, missing_pillars to response |
| P3+P8 | Unlock hints | `apps/mvp_api/api/recommendations.py` | Add UnlockHint model, compute tier + hints in endpoint |
| P4 | Alt inflammation | `apps/mvp_api/api/recommendations.py` | Alternative inflammation detection without temp_trend |
| P6 | Oura extraction | `apps/mvp_api/api/correlations.py` | Docstring: mark as legacy fallback, canonical-first via _build_health_daily |

### Web Frontend (TypeScript)

| # | Issue | File | Change |
|---|-------|------|--------|
| P7 | ouraActive var | `frontend/src/components/home/TodayView.tsx` | Renamed to anyWearableActive |
| P7 | oura_days_available | `frontend/src/components/correlations/CorrelationsView.tsx` | Fallback to wearable_days_available |
| P7 | Types | `frontend/src/types/index.ts` | Added wearable_days_available field |
| P7 | useHealthData | `frontend/src/hooks/useHealthData.ts` | Added TODO for service rename |
| P10 | Sparsity messaging | `frontend/src/components/correlations/CorrelationsView.tsx` | Tier-aware empty state hints |

### Mobile (React Native/TypeScript)

| # | Issue | File | Change |
|---|-------|------|--------|
| Bug | Med scan | `apps/mobile/app/(tabs)/log/medications.tsx` | ScanPrescriptionModal + Scan button |
| Bug | Session stale | `apps/mobile/src/services/api.ts` | Token caching (30s TTL) + refreshTokenCache export |
| Bug | Session stale | `apps/mobile/app/_layout.tsx` | AppStateListener invalidates all queries on foreground |
| Bug | Session stale | `apps/mobile/app/(tabs)/log/nutrition.tsx` | enabled: !!user guards on queries |

---

## File Inventory (16 files changed, 1 new)

### New Files
1. `common/metrics/device_tiers.py`

### Modified Files
2. `apps/mvp_api/api/health_score.py`
3. `apps/mvp_api/api/doctor_prep.py`
4. `apps/mvp_api/api/recommendations.py`
5. `apps/mvp_api/api/correlations.py`
6. `apps/mobile/src/services/api.ts`
7. `apps/mobile/app/_layout.tsx`
8. `apps/mobile/app/(tabs)/log/medications.tsx`
9. `apps/mobile/app/(tabs)/log/nutrition.tsx`
10. `frontend/src/components/home/TodayView.tsx`
11. `frontend/src/components/correlations/CorrelationsView.tsx`
12. `frontend/src/types/index.ts`
13. `frontend/src/hooks/useHealthData.ts`

### Design Docs
14. `DEVICE_TIER_DESIGN_SPEC.md`
15. `DEVICE_TIER_IMPL_PLAN.md`

---

## Testing Checklist

- [ ] Health score endpoint returns score_confidence, active_pillars, data_tier for real user
- [ ] Health score _empty_score returns all missing_pillars
- [ ] Doctor prep report omits sleep/readiness sections when no wearable connected
- [ ] Doctor prep report shows activity data for phone-only users
- [ ] Recommendations endpoint returns unlock_hints for T1 user
- [ ] Recommendations detects inflammation without temp_trend (alternative path)
- [ ] Mobile: Scan button appears on medications screen
- [ ] Mobile: Camera + gallery → AI scan → editable form → save works
- [ ] Mobile: App doesn't spin after long idle (token cache + query guards)
- [ ] Mobile: Nutrition screen loads immediately with enabled guard
- [ ] Web: ouraActive renamed to anyWearableActive (no regressions)
- [ ] Web: Correlations show tier-aware empty state messaging
