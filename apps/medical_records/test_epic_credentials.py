"""
Test Epic FHIR Credentials

This file contains test credentials for Epic FHIR sandbox testing.
These are for development purposes only and should not be used in production.
"""

# Test Epic FHIR Sandbox Credentials
TEST_EPIC_CREDENTIALS = {
    "client_id": "test_client_id",
    "client_secret": "test_client_secret", 
    "environment": "sandbox",
    "redirect_uri": "http://localhost:8080/callback",
    "base_url": "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
    "oauth_url": "https://fhir.epic.com/interconnect-fhir-oauth/oauth2"
}

# Test Patient IDs (from Epic sandbox)
TEST_PATIENT_IDS = {
    "anna": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
    "henry": "a1",
    "john": "a2", 
    "omar": "a3",
    "kyle": "a4"
}

# Test MyChart Users
TEST_MYCHART_USERS = {
    "derrick": "derrick",
    "camilla": "camilla",
    "desiree": "desiree",
    "olivia": "olivia"
}
