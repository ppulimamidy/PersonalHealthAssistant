import pytest
import requests
import json

BASE_URL = "http://localhost:8005/api/v1/medical-records/clinical-reports"
TEMPLATES_URL = "http://localhost:8005/api/v1/medical-records/clinical-reports/templates/"
CATEGORIES_URL = "http://localhost:8005/api/v1/medical-records/clinical-reports/categories/"
STATS_URL = "http://localhost:8005/api/v1/medical-records/clinical-reports/statistics/"

JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyMjIyMjIyMi0yMjIyLTIyMjItMjIyMi0yMjIyMjIyMjIyMjIiLCJ1c2VyX2lkIjoiMjIyMjIyMjItMjIyMi0yMjIyLTIyMjItMjIyMjIyMjIyMjIyIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwidXNlcl90eXBlIjoidXNlciIsInBlcm1pc3Npb25zIjpbIm1lZGljYWxfcmVjb3JkczpyZWFkIiwibWVkaWNhbF9yZWNvcmRzOndyaXRlIl0sImV4cCI6MTc1MTMzNTM0NCwiaWF0IjoxNzUxMzMxNzQ0LCJpc3MiOiJtZWRpY2FsLXJlY29yZHMtc2VydmljZSJ9.zj-JuKAf6CVwEt_mz3sjj_hIFeAFHV28u5dL2d7YHaI"
HEADERS = {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json"}

def pretty(resp):
    print(f"Status: {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)

@pytest.fixture
def report_id():
    data = {
        "patient_id": "11111111-1111-1111-1111-111111111111",
        "report_type": "DISCHARGE_SUMMARY",
        "status": "DRAFT",
        "priority": "NORMAL",
        "category": "DISCHARGE",
        "title": "Test Discharge Summary",
        "content": "Patient discharged in good health.",
        "author_id": "22222222-2222-2222-2222-222222222222",
        "template_id": None
    }
    resp = requests.post(BASE_URL + "/", headers=HEADERS, json=data)
    if resp.status_code == 201:
        return resp.json()["id"]
    else:
        pytest.skip(f"Could not create test report: {resp.status_code}")

def test_create_report():
    data = {
        "patient_id": "11111111-1111-1111-1111-111111111111",
        "report_type": "DISCHARGE_SUMMARY",
        "status": "DRAFT",
        "priority": "NORMAL",
        "category": "DISCHARGE",
        "title": "Test Discharge Summary",
        "content": "Patient discharged in good health.",
        "author_id": "22222222-2222-2222-2222-222222222222",
        "template_id": None
    }
    resp = requests.post(BASE_URL + "/", headers=HEADERS, json=data)
    pretty(resp)
    assert resp.status_code == 200

def test_get_report(report_id):
    resp = requests.get(f"{BASE_URL}/{report_id}", headers=HEADERS)
    pretty(resp)
    assert resp.status_code == 200

def test_update_report(report_id):
    data = {"title": "Updated Title", "content": "Updated content."}
    resp = requests.put(f"{BASE_URL}/{report_id}", headers=HEADERS, json=data)
    pretty(resp)
    assert resp.status_code == 200

def test_versions(report_id):
    resp = requests.get(f"{BASE_URL}/{report_id}/versions", headers=HEADERS)
    pretty(resp)
    assert resp.status_code == 200

def test_audit_logs(report_id):
    resp = requests.get(f"{BASE_URL}/{report_id}/audit-logs", headers=HEADERS)
    pretty(resp)
    assert resp.status_code == 200

def test_search():
    data = {"query": "discharge", "limit": 5}
    resp = requests.post(BASE_URL + "/search", headers=HEADERS, json=data)
    pretty(resp)
    assert resp.status_code == 200

def test_templates():
    resp = requests.get(TEMPLATES_URL, headers=HEADERS)
    pretty(resp)
    assert resp.status_code == 200

def test_categories():
    resp = requests.get(CATEGORIES_URL, headers=HEADERS)
    pretty(resp)
    assert resp.status_code == 200

def test_statistics():
    resp = requests.get(STATS_URL, headers=HEADERS)
    pretty(resp)
    assert resp.status_code == 200
