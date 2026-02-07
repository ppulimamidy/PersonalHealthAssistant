import os
import sys
import requests

API_BASE_URL = os.environ.get("EPIC_FHIR_API_BASE_URL", "http://localhost:8000")
TOKEN = os.environ.get("EPIC_FHIR_API_TOKEN")
OUTPUT_FILE = "epic_public_key.pem"

if len(sys.argv) > 1:
    API_BASE_URL = sys.argv[1]
if len(sys.argv) > 2:
    TOKEN = sys.argv[2]

url = f"{API_BASE_URL.rstrip('/')}/epic-fhir/public-key"
headers = {}
if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"

print(f"Fetching public key from: {url}")
response = requests.get(url, headers=headers)
if response.status_code != 200:
    print(f"Failed to fetch public key: {response.status_code} - {response.text}")
    sys.exit(1)

data = response.json()
public_key = data.get("public_key")
if not public_key:
    print("No public_key found in response.")
    sys.exit(1)

with open(OUTPUT_FILE, "w") as f:
    f.write(public_key)

print(f"Public key saved to {OUTPUT_FILE}") 