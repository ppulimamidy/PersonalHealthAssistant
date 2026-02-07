import os
from apps.medical_records.config.epic_fhir_config import epic_fhir_config

print("--- Epic FHIR Config ---")
for field in epic_fhir_config.__fields__:
    print(f"{field}: {getattr(epic_fhir_config, field, None)}")

print("\n--- Environment Variables (EPIC_FHIR_*) ---")
for key, value in os.environ.items():
    if key.startswith("EPIC_FHIR_"):
        print(f"{key}: {value}") 