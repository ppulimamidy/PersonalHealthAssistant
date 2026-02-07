import asyncio
from apps.medical_records.services.epic_fhir_client import EpicFHIRClient, EpicFHIRClientConfig
from apps.medical_records.config.epic_fhir_config import epic_fhir_config

async def main():
    # Use config from environment or epic_fhir_config
    config = EpicFHIRClientConfig(
        client_id=epic_fhir_config.client_id,
        client_secret=epic_fhir_config.client_secret,
        epic_environment=epic_fhir_config.environment,
        scope=epic_fhir_config.default_scope,
        launch_type="client_credentials"
    )
    client = EpicFHIRClient(config)

    print("Authenticating with Epic FHIR (client credentials)...")
    token = await client._authenticate_client_credentials()
    print(f"Access token: {token.access_token[:12]}... (expires in {token.expires_in}s)")

    # Example: Read a Patient resource (replace with a real patient ID from Epic sandbox)
    test_patient_id = list(epic_fhir_config.test_patients.values())[0]
    print(f"Fetching Patient resource for patient_id: {test_patient_id}")
    patient = await client._make_epic_request("GET", f"Patient/{test_patient_id}")
    print("Patient resource:")
    print(patient)

    # You can add more FHIR workflows here, e.g.:
    # - Observation read: await client._make_epic_request("GET", f"Observation?patient={test_patient_id}")
    # - Encounter read: await client._make_epic_request("GET", f"Encounter?patient={test_patient_id}")

if __name__ == "__main__":
    asyncio.run(main())