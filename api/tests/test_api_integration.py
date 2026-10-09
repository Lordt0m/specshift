"""Integration and adversarial test suite for Django REST endpoints.

Tests health, policy, JSON compare, multipart file compare, HTML report,
size caps, and hostile XSS payloads.
"""

from pathlib import Path
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "demo"


@pytest.fixture
def api_client():
    return APIClient()


def test_health_endpoint(api_client):
    response = api_client.get("/api/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["engine_version"] == "1.0.0"
    assert data["policy_version"] == "v1"
    assert "3.0.3" in data["supported_openapi_versions"]


def test_policy_endpoint(api_client):
    response = api_client.get("/api/policy/v1/")
    assert response.status_code == 200
    data = response.json()
    assert data["policy_version"] == "v1"
    assert len(data["rules"]) > 0
    rule_ids = [r["id"] for r in data["rules"]]
    assert "OP-01" in rule_ids
    assert "SC-03" in rule_ids


def test_compare_json_payload(api_client):
    base_text = (FIXTURES_DIR / "baseline.yaml").read_text(encoding="utf-8")
    cand_text = (FIXTURES_DIR / "candidate.yaml").read_text(encoding="utf-8")

    payload = {
        "baseline": base_text,
        "candidate": cand_text,
    }
    response = api_client.post("/api/compare/", payload, format="json")
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["breaking_count"] == 5
    assert data["summary"]["conclusion"] == "Breaking changes found (1 coverage gap present)"


def test_compare_multipart_upload(api_client):
    base_bytes = (FIXTURES_DIR / "baseline.yaml").read_bytes()
    cand_bytes = (FIXTURES_DIR / "candidate.yaml").read_bytes()

    base_file = SimpleUploadedFile("baseline.yaml", base_bytes, content_type="text/yaml")
    cand_file = SimpleUploadedFile("candidate.yaml", cand_bytes, content_type="text/yaml")

    response = api_client.post(
        "/api/compare/",
        {"baseline": base_file, "candidate": cand_file},
        format="multipart"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_findings"] == 8


def test_compare_missing_input(api_client):
    response = api_client.post("/api/compare/", {"baseline": "foo"}, format="json")
    assert response.status_code == 400
    assert response.json()["code"] == "MISSING_INPUT"


def test_compare_size_limit_exceeded(api_client):
    huge_str = " " * (1024 * 1024 + 10)
    huge_spec = f'{{"openapi": "3.0.3", "info": {{"title": "{huge_str}", "version": "1"}}, "paths": {{}}}}'
    payload = {"baseline": huge_spec, "candidate": huge_spec}
    response = api_client.post("/api/compare/", payload, format="json")
    assert response.status_code == 413
    assert response.json()["code"] == "DOCUMENT_SIZE_EXCEEDED"


def test_compare_external_ref_prohibited(api_client):
    evil_spec = """
openapi: "3.0.3"
info:
  title: "T"
  version: "1"
paths: {}
components:
  schemas:
    Bad:
      $ref: "https://evil.attacker.com/leak"
"""
    payload = {
        "baseline": evil_spec,
        "candidate": evil_spec,
    }
    response = api_client.post("/api/compare/", payload, format="json")
    assert response.status_code == 400
    assert response.json()["code"] == "EXTERNAL_REFERENCE_PROHIBITED"


def test_report_endpoint_and_xss_escaping(api_client):
    hostile_base = """
openapi: "3.0.3"
info:
  title: "API"
  version: "1.0.0"
paths:
  /test:
    get:
      operationId: "<script>alert('xss-in-opid')</script>"
      responses:
        '200':
          description: "ok"
"""
    hostile_cand = """
openapi: "3.0.3"
info:
  title: "API"
  version: "1.0.0"
paths:
  /test:
    get:
      operationId: "cleanOpId"
      responses:
        '200':
          description: "ok"
"""
    payload = {
        "baseline": hostile_base,
        "candidate": hostile_cand,
    }
    response = api_client.post("/api/report/", payload, format="json")
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/html")
    assert "attachment" in response["Content-Disposition"]

    html_text = response.content.decode("utf-8")
    # Must NOT contain raw unescaped script tags
    assert "<script>alert('xss-in-opid')</script>" not in html_text
    assert "&lt;script&gt;alert('xss-in-opid')&lt;/script&gt;" in html_text or "xss-in-opid" in html_text
    assert "<script" not in html_text.lower()

