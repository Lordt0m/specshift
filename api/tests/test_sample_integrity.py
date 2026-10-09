"""Test that web/public/sample/result.json strictly matches the engine CLI output."""

import json
from pathlib import Path
from api.comparison.engine import compare_specifications

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "demo"
SAMPLE_JSON_PATH = Path(__file__).resolve().parent.parent.parent / "web" / "public" / "sample" / "result.json"


def test_public_sample_matches_engine_run():
    assert SAMPLE_JSON_PATH.is_file(), "web/public/sample/result.json must exist"

    baseline_bytes = (FIXTURES_DIR / "baseline.yaml").read_bytes()
    candidate_bytes = (FIXTURES_DIR / "candidate.yaml").read_bytes()

    fresh_result = compare_specifications(baseline_bytes, candidate_bytes)
    checked_in_result = json.loads(SAMPLE_JSON_PATH.read_text(encoding="utf-8"))

    assert checked_in_result == fresh_result
