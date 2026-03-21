# Medical Records Expansion — Design Spec

> **Goal:** Expand "Lab Results" into a comprehensive Medical Records system that handles blood labs, pathology/biopsy reports, genomic/molecular profiles, and imaging reports — all feeding into the Clinical Research Agent for personalized treatment intelligence.

---

## Current State

- Lab Results screen handles **blood panels only**: numeric biomarkers with reference ranges
- AI extraction (Claude) parses lab PDFs/images for biomarker tables
- Intelligence layer: system-grouped summary, recommended tests, supplement gaps, retest schedule
- Clinical Research Agent: treatment reports, drug profiles, clinical trial matching

---

## New Record Types

### Type 1: Blood Labs (Existing — No Change)
- Numeric biomarkers: value + unit + reference range + status
- Examples: CBC, metabolic panel, lipid panel, thyroid, A1C
- Already fully implemented with intelligence layer

### Type 2: Pathology / Biopsy Reports (New)
**What they contain:**
- **Specimen**: tissue type, collection site, collection date
- **Diagnosis**: cancer type, histological subtype (e.g., adenocarcinoma, squamous cell)
- **Stage**: TNM staging (T1N0M0), overall stage (Stage IIA)
- **Grade**: differentiation (well/moderate/poor, Gleason score for prostate)
- **Margins**: clear/positive/close with distance
- **Receptor status**: ER/PR/HER2 (breast), PD-L1 TPS (lung)
- **Lymphovascular invasion**: present/absent
- **Additional findings**: necrosis, perineural invasion, etc.

**AI extraction targets:**
```json
{
  "record_type": "pathology",
  "specimen": "Left upper lobe lung biopsy",
  "diagnosis": "Non-small cell lung cancer, adenocarcinoma",
  "stage": { "T": "T2a", "N": "N1", "M": "M0", "overall": "Stage IIB" },
  "grade": "Moderately differentiated",
  "margins": { "status": "clear", "distance_mm": 5 },
  "receptor_status": { "PD-L1_TPS": "60%", "ALK": "negative", "ROS1": "negative" },
  "lymphovascular_invasion": "absent",
  "pathologist": "Dr. Shaikhali Barodawala",
  "lab": "CAP Accredited Laboratory",
  "report_date": "2025-12-25"
}
```

### Type 3: Genomic / Molecular Reports (New)
**What they contain:**
- **Test type**: NGS panel, PCR, FISH, IHC
- **Genes tested**: EGFR, BRCA1/2, KRAS, ALK, ROS1, BRAF, HER2, etc.
- **Mutations found**: gene + exon + variant + protein change + VAF
- **Classification**: Tier I-IV (AMP/ASCO/CAP guidelines), Level A-D evidence
- **Therapeutic sensitivity**: which drugs the mutation responds to
- **Therapeutic resistance**: which drugs won't work
- **Clinical significance**: pathogenic, likely pathogenic, VUS, benign

**AI extraction targets:**
```json
{
  "record_type": "genomic",
  "test_type": "Next-Generation Sequencing (NGS)",
  "specimen": "Lung biopsy tissue",
  "mutations": [
    {
      "gene": "EGFR",
      "exon": "Exon 21",
      "variant": "c.2573T>G",
      "protein_change": "p.Leu858Arg (L858R)",
      "vaf": "18.41%",
      "classification": { "tier": "Tier I", "level": "Level A" },
      "clinical_significance": "Pathogenic",
      "sensitive_therapies": ["Osimertinib", "Erlotinib", "Gefitinib", "Afatinib", "Dacomitinib"],
      "resistant_therapies": [],
      "sensitivity": "Sensitive"
    },
    {
      "gene": "EGFR",
      "exon": "Exon 20",
      "variant": "c.2310_2311insGGT",
      "protein_change": "p.Asp770_Asn771insGly",
      "vaf": "4.39%",
      "classification": { "tier": "Tier I", "level": "Level A" },
      "clinical_significance": "Pathogenic",
      "sensitive_therapies": ["Amivantamab", "Sunvozertinib", "Erlotinib", "Gefitinib"],
      "resistant_therapies": [],
      "sensitivity": "Sensitive"
    }
  ],
  "genes_tested_negative": ["KRAS", "ALK", "ROS1", "BRAF", "MET"],
  "tumor_mutational_burden": null,
  "microsatellite_instability": null,
  "lab": "CAP Accredited",
  "pathologist": "Dr. Shaikhali Barodawala",
  "genomics_consultant": "Dr. Monisha Banerjee",
  "report_date": "2025-12-25"
}
```

### Type 4: Imaging Reports (New)
**What they contain:**
- **Modality**: CT, MRI, PET, X-ray, Ultrasound, Mammogram
- **Body region**: chest, abdomen, brain, breast, etc.
- **Findings**: lesion descriptions, measurements, characteristics
- **Impression/Conclusion**: summary diagnosis
- **Comparison**: comparison to prior imaging if available
- **Scoring**: BIRADS (breast), TIRADS (thyroid), Lung-RADS, PI-RADS (prostate)
- **Recommendations**: follow-up timeline, biopsy recommendation

**AI extraction targets:**
```json
{
  "record_type": "imaging",
  "modality": "CT Chest with Contrast",
  "body_region": "Chest",
  "date": "2025-12-10",
  "findings": [
    { "location": "Left upper lobe", "description": "2.3 cm spiculated mass", "measurement_cm": 2.3 },
    { "location": "Mediastinal lymph nodes", "description": "Enlarged level 7 node, 1.5 cm", "measurement_cm": 1.5 }
  ],
  "impression": "Left upper lobe mass suspicious for primary lung malignancy with possible mediastinal lymph node involvement",
  "comparison": "No prior imaging for comparison",
  "scoring": null,
  "recommendations": "Tissue biopsy recommended",
  "radiologist": "Dr. Smith"
}
```

---

## Database Schema

### New Table: `medical_records`
```sql
CREATE TABLE medical_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  record_type TEXT NOT NULL CHECK (record_type IN ('blood_lab', 'pathology', 'genomic', 'imaging', 'procedure')),
  title TEXT,
  report_date DATE,
  provider_name TEXT,
  facility_name TEXT,
  extracted_data JSONB NOT NULL DEFAULT '{}',
  raw_text TEXT,
  ai_summary TEXT,
  file_url TEXT,
  original_filename TEXT,
  tags TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_medical_records_user ON medical_records(user_id, record_type, report_date DESC);
```

The `extracted_data` JSONB stores type-specific structured data (pathology staging, genomic mutations, imaging findings). This allows flexible schema per record type while keeping a single table.

Existing `lab_results` table continues to work for blood labs. `medical_records` handles the new types. Over time, blood labs could migrate here too.

---

## AI Extraction Prompts

### Pathology Report Prompt
```
Extract structured data from this pathology/biopsy report.
Return ONLY valid JSON with these fields:
- specimen, diagnosis, histological_subtype
- stage: { T, N, M, overall }
- grade, margins: { status, distance_mm }
- receptor_status: { key: value } for all receptors tested
- lymphovascular_invasion, perineural_invasion
- pathologist, lab, report_date
- additional_findings (array of strings)
```

### Genomic Report Prompt
```
Extract structured data from this genomic/molecular report.
Return ONLY valid JSON with:
- test_type, specimen
- mutations: array of { gene, exon, variant, protein_change, vaf,
  classification: { tier, level }, clinical_significance,
  sensitive_therapies: [], resistant_therapies: [], sensitivity }
- genes_tested_negative: []
- tumor_mutational_burden, microsatellite_instability
- lab, pathologist, genomics_consultant, report_date
```

### Imaging Report Prompt
```
Extract structured data from this imaging/radiology report.
Return ONLY valid JSON with:
- modality, body_region, date
- findings: array of { location, description, measurement_cm }
- impression, comparison
- scoring (BIRADS/TIRADS/Lung-RADS if applicable)
- recommendations, radiologist
```

---

## Integration with Clinical Research Agent

When a user has genomic data, the Clinical Research Agent can:
1. **Match mutations to targeted therapies** with NCCN guideline references
2. **Search ClinicalTrials.gov** filtered by specific mutations (e.g., "EGFR Exon 20 insertion")
3. **Compare drugs** for the specific mutation profile
4. **Generate questions for oncologist** referencing the molecular profile
5. **Track response** when imaging reports are uploaded over time

---

## Mobile & Web UI

### Upload Flow (Same Pattern as Lab Scan)
1. User taps "Add Record" on the Medical Records screen
2. Selects record type: Blood Lab | Pathology | Genomic | Imaging
3. Scans/uploads PDF or photo
4. Claude extracts structured data based on record type
5. User reviews and confirms
6. Record saved with intelligence cards

### Display
Each record type renders differently:
- **Blood Labs**: Biomarker table with status colors (existing)
- **Pathology**: Diagnosis card with staging badge, grade, margins, receptor status
- **Genomic**: Mutation table with gene, variant, tier/level, targeted therapies (color-coded by sensitivity)
- **Imaging**: Findings list with measurements, impression, scoring badge

### Intelligence
After upload, the appropriate intelligence card appears:
- **Pathology**: "Stage IIB adenocarcinoma — per NCCN, surgical resection + adjuvant chemotherapy is standard"
- **Genomic**: "EGFR L858R + Exon 20 ins — Osimertinib is first-line, but Exon 20 ins may benefit from Amivantamab. Search clinical trials?"
- **Imaging**: "2.3cm mass in LUL — recommend comparing with baseline imaging after treatment initiation"
