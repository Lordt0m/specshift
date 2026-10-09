"""Test golden demo fixture comparison, determinism, and key-order invariance."""

import json
from pathlib import Path
import pytest
import yaml

from api.comparison.engine import compare_specifications

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "demo"


def test_demo_fixture_golden_run():
    baseline_path = FIXTURES_DIR / "baseline.yaml"
    candidate_path = FIXTURES_DIR / "candidate.yaml"

    result = compare_specifications(baseline_path.read_bytes(), candidate_path.read_bytes())
    expected = json.loads((FIXTURES_DIR / "expected.json").read_text(encoding="utf-8"))

    # Summary checks
    summary = result["summary"]
    assert summary == expected["summary"]
    assert summary["breaking_count"] == 5
    # Metadata edits and the newly introduced path-level parameter are now
    # visible instead of being silently discarded by the old implementation.
    assert summary["review_count"] == 3
    assert summary["non_breaking_count"] == 3
    assert summary["total_findings"] == 11
    assert summary["coverage_gap_count"] == 1
    assert summary["conclusion"] == "Breaking changes found (1 coverage gap present)"

    # Rule IDs present
    rule_ids = {f["rule_id"] for f in result["findings"]}
    expected_rule_ids = {"OP-01", "OP-02", "MT-01", "MT-02", "RS-02", "SC-03", "SC-04", "SC-05", "SC-10", "UN-01"}
    assert rule_ids == expected_rule_ids
    assert rule_ids == set(expected["rule_ids"])

    # Verify multi-operation aggregation for shared schema
    sc03_finding = next(f for f in result["findings"] if f["rule_id"] == "SC-03")
    assert "GET /orders" in sc03_finding["affected_operations"]
    assert "GET /orders/{orderId}" in sc03_finding["affected_operations"]
    assert sc03_finding["affected_operations"] == expected["shared_response_operations"]

    sc05_finding = next(f for f in result["findings"] if f["rule_id"] == "SC-05")
    assert "GET /orders" in sc05_finding["affected_operations"]
    assert "GET /orders/{orderId}" in sc05_finding["affected_operations"]

    # Verify coverage gap
    assert len(result["coverage_gaps"]) == 1
    gap = result["coverage_gaps"][0]
    assert gap["construct"] == expected["coverage_construct"]


def test_determinism_repeated_runs():
    baseline_bytes = (FIXTURES_DIR / "baseline.yaml").read_bytes()
    candidate_bytes = (FIXTURES_DIR / "candidate.yaml").read_bytes()

    res1 = compare_specifications(baseline_bytes, candidate_bytes)
    res2 = compare_specifications(baseline_bytes, candidate_bytes)

    # Serialized outputs must be identical
    json1 = json.dumps(res1, sort_keys=True)
    json2 = json.dumps(res2, sort_keys=True)
    assert json1 == json2


def test_key_order_and_whitespace_invariance():
    baseline_bytes = (FIXTURES_DIR / "baseline.yaml").read_bytes()
    candidate_bytes = (FIXTURES_DIR / "candidate.yaml").read_bytes()

    res_original = compare_specifications(baseline_bytes, candidate_bytes)

    # Reorder keys in candidate by parsing to dict and reversing dict items
    cand_obj = yaml.safe_load(candidate_bytes)
    reordered_cand_yaml = yaml.dump(cand_obj, sort_keys=False)

    res_reordered = compare_specifications(baseline_bytes, reordered_cand_yaml.encode("utf-8"))

    # Summary and findings must match exactly
    assert res_original["summary"] == res_reordered["summary"]
    assert len(res_original["findings"]) == len(res_reordered["findings"])
    assert {f["id"] for f in res_original["findings"]} == {f["id"] for f in res_reordered["findings"]}


def test_html_report_generation():
    from api.comparison.report import generate_html_report
    baseline_bytes = (FIXTURES_DIR / "baseline.yaml").read_bytes()
    candidate_bytes = (FIXTURES_DIR / "candidate.yaml").read_bytes()
    res = compare_specifications(baseline_bytes, candidate_bytes)
    html_report = generate_html_report(res)

    assert "<!DOCTYPE html>" in html_report
    assert "SpecShift Compatibility Report" in html_report
    assert "Breaking changes found" in html_report
    assert "DELETE /orders/{orderId}" in html_report
    assert "<script" not in html_report.lower()  # Prohibit JS per security policy

