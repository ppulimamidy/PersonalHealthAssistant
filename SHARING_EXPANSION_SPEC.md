# Share with Care Team — Expansion Spec

**Date:** 2026-03-22
**Status:** IMPLEMENTING

## New Sharing Categories

| # | Permission Key | UI Label | Data Source | What's Shared |
|---|---------------|----------|-------------|---------------|
| 1 | `wearable_data` | Wearable Health Data | `native_health_data` + `health_metric_summaries` | 30-day trends: sleep, HRV, RHR, steps, recovery, SpO2, temp |
| 2 | `medical_records` | Medical Records | `medical_records` table | Pathology, genomic, imaging reports with AI summaries (unbundled from intelligence) |
| 3 | `nutrition` | Nutrition & Meals | `meal_logs` via nutrition service | 14-day meal logs with macros, calories |
| 4 | `doctor_prep` | Visit Prep Report | `doctor_prep.py` internal call | Full doctor prep report (key metrics, trends, concerns, intelligence) |
| 5 | `specialist_recs` | Specialist Recommendations | `agent_conversations` table | Latest specialist AI recommendations and conversation summaries |
| 6 | `cycle_tracking` | Cycle Data | `cycle_logs` table | Menstrual cycle phase, predictions, cycle-aware notes |

## Parity Fixes

- Web: Add `interventions`, `intelligence` to UI toggles (already in backend)
- Mobile: Add `intelligence` to UI toggles (already in backend)

## Files Changed

| File | Changes |
|------|---------|
| `apps/mvp_api/api/sharing.py` | Add 6 new permission blocks in `get_shared_summary()` |
| `frontend/src/types/index.ts` | Expand `SharePermission` union + `SharedHealthSummary` interface |
| `frontend/src/app/(dashboard)/settings/page.tsx` | Add all new permissions to `ALL_PERMISSIONS` array |
| `apps/mobile/app/(tabs)/profile/sharing.tsx` | Add all new permissions to `PERMISSIONS` array |
