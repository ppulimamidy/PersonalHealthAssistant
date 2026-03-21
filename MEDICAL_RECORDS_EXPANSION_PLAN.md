# Medical Records Expansion — Implementation Plan

> Design spec: `MEDICAL_RECORDS_EXPANSION.md`
> Estimated: 4 sessions, 12 tasks

---

## Session 1: API — Record Types + AI Extraction (P0)

### Task 1.1 — Medical records API module
**File:** New `apps/mvp_api/api/medical_records_api.py`

Endpoints:
- `POST /api/v1/medical-records` — create record (type + extracted_data)
- `GET /api/v1/medical-records?type=pathology` — list by type
- `GET /api/v1/medical-records/{id}` — get single record
- `DELETE /api/v1/medical-records/{id}` — delete record
- `POST /api/v1/medical-records/scan` — upload file, Claude extracts based on type

Uses `_supabase_upsert` for storage in `medical_records` table.

### Task 1.2 — Type-specific AI extraction prompts
**File:** `apps/mvp_api/api/medical_records_api.py`

Three extraction prompt templates:
- `_extract_pathology(image_bytes/text)` → pathology JSON
- `_extract_genomic(image_bytes/text)` → genomic JSON with mutations array
- `_extract_imaging(image_bytes/text)` → imaging JSON with findings array

Each uses Claude with type-specific system prompt. Supports PDF + image upload (reuse existing lab scan infrastructure for file handling).

### Task 1.3 — Post-upload intelligence for each type
**File:** `apps/mvp_api/api/medical_records_api.py`

`POST /api/v1/medical-records/{id}/insight`

Generates type-specific AI insight:
- Pathology: staging interpretation + NCCN treatment recommendation
- Genomic: mutation-drug matching + clinical trial suggestion
- Imaging: findings interpretation + follow-up guidance

Cross-references with user's conditions, medications, and other records.

### Task 1.4 — Register routes + Supabase migration
**File:** `apps/mvp_api/main.py`, new migration file

Register router at `/api/v1/medical-records`.
Create `medical_records` table if not exists (use `_supabase_upsert` which auto-creates, or add migration).

---

## Session 2: Mobile — Medical Records Screen (P0)

### Task 2.1 — Medical Records screen (replaces/extends Lab Results)
**File:** New `apps/mobile/app/(tabs)/log/medical-records.tsx`

Tabs: Blood Labs | Pathology | Genomic | Imaging
- Each tab lists records of that type
- FAB "+" button → type selector → scan/upload

### Task 2.2 — Record type selector modal
**File:** In medical-records screen

When user taps "+":
- "What type of record?"
- 4 options with icons: Blood Lab (flask), Pathology (microscope), Genomic (dna), Imaging (scan)
- Blood Lab → existing lab scan flow
- Others → new medical record scan flow

### Task 2.3 — Type-specific record cards
**Components:**

**PathologyCard:** Diagnosis badge, stage pills (T/N/M), grade, margins status, receptor chips
**GenomicCard:** Mutation table rows — gene, variant, tier badge, sensitivity badge, targeted therapy pills
**ImagingCard:** Modality badge, findings list with measurements, impression text, scoring badge

### Task 2.4 — Scan flow for new record types
Reuse existing photo/PDF upload pattern from lab scan:
1. Pick photo or file
2. Send to `/api/v1/medical-records/scan` with `record_type` param
3. Review extracted data
4. Save

---

## Session 3: Genomic Intelligence (P0)

### Task 3.1 — Mutation-therapy matching
**File:** `apps/mvp_api/api/medical_records_api.py`

When a genomic record is saved:
1. Extract mutations with their sensitive therapies
2. Cross-reference with user's current medications
3. Flag: "You have EGFR L858R — are you on Osimertinib? If not, discuss with oncologist"
4. Auto-search ClinicalTrials.gov for the specific mutations

### Task 3.2 — Genomic profile summary card
**File:** New `apps/mobile/src/components/GenomicProfileCard.tsx`

Shows at top of genomic tab when mutations exist:
- "Your Molecular Profile"
- Gene badges with mutation names
- Tier/Level classifications
- Matched therapies
- "Search clinical trials for your mutations" CTA → Clinical Research Agent

### Task 3.3 — Feed genomic data into Clinical Research Agent
**File:** `apps/mvp_api/api/clinical_research.py`

When user has genomic records, include in research context:
- Mutations list with classifications
- Sensitivity data
- Prompt enhancement: "Patient has EGFR L858R and Exon 20 insertion — focus on targeted therapies for this molecular profile"

---

## Session 4: Timeline Integration + Web Parity (P1)

### Task 4.1 — Medical records on timeline
**File:** `apps/mvp_api/api/timeline_actions.py`

Add medical records to timeline action overlay:
- Pathology: "Biopsy result: Stage IIB adenocarcinoma"
- Genomic: "Genomic profile: EGFR L858R, Exon 20 ins"
- Imaging: "CT Chest: 2.3cm LUL mass"

### Task 4.2 — Web medical records page
**File:** New `frontend/src/app/(dashboard)/medical-records/page.tsx`

Same functionality as mobile: tabs by record type, upload, type-specific cards.

### Task 4.3 — Update Track tab navigation
**Files:** Mobile log index, navigation

Add "Medical Records" option in Track tab alongside existing items.
Or rename "Lab Results" to "Medical Records" and add type tabs.

---

## Verification Checklist

### Session 1
- [ ] POST /medical-records creates records for all 3 new types
- [ ] Scan endpoint extracts pathology data from PDF/image
- [ ] Scan endpoint extracts genomic mutations from PDF/image
- [ ] Scan endpoint extracts imaging findings from PDF/image
- [ ] Post-upload insight generates type-specific analysis

### Session 2
- [ ] Medical records screen shows tabs by type
- [ ] Record type selector works
- [ ] PathologyCard renders staging + receptor status
- [ ] GenomicCard renders mutation table with therapies
- [ ] ImagingCard renders findings + measurements

### Session 3
- [ ] Genomic mutations match to targeted therapies
- [ ] Clinical Research Agent includes genomic context
- [ ] ClinicalTrials.gov search filtered by mutation

### Session 4
- [ ] Medical records appear on timeline
- [ ] Web medical records page works
- [ ] Track tab navigation updated
