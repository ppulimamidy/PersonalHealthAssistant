from urllib.parse import urlencode

# Hardcode the correct Epic OAuth2 endpoint
authorize_endpoint = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize"

# Use minimal scope
scope = "launch/patient patient/*.read"
state = "test_state_123"
# Use the correct client ID and redirect URI (update these as needed)
client_id = "0f7c15aa-0f82-4166-8bed-71b398fadcb7"
redirect_uri = "http://localhost:8005/api/v1/medical-records/epic-fhir/callback"

params = {
    "response_type": "code",
    "client_id": client_id,
    "redirect_uri": redirect_uri,
    "scope": scope,
    "state": state
}

url = f"{authorize_endpoint}?{urlencode(params)}"

print("\n==== Epic FHIR SMART on FHIR Authorization URL (correct endpoint, minimal scope) ====")
print(url)
print("\n==== Instructions ====")
print("1. Open the above URL in your browser.")
print("2. Log in and authorize the app (use Epic sandbox credentials if prompted).")
print(f"3. After authorization, Epic will redirect you to: {redirect_uri}")
print("4. The URL will include a 'code' parameter, e.g. ?code=...&state=...")
print("5. Copy the 'code' value and use it to test the /epic-fhir/callback endpoint (or let your app handle it).\n") 