"""Comprehensive test suite for compatibility rules v1.

Verifies positive, negative, and reverse-direction behavior per policy v1.
"""

import pytest
from api.comparison.engine import compare_specifications


def _base_spec(paths_obj=None, schemas_obj=None):
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": paths_obj or {},
        "components": {"schemas": schemas_obj or {}}
    }


def _run_compare(base_dict, cand_dict):
    import json
    return compare_specifications(
        json.dumps(base_dict).encode("utf-8"),
        json.dumps(cand_dict).encode("utf-8")
    )


def test_op_rules():
    base = _base_spec(paths_obj={"/items": {"get": {"responses": {"200": {"description": "ok"}}}}})
    cand = _base_spec(paths_obj={"/items": {"post": {"responses": {"200": {"description": "ok"}}}}})

    res = _run_compare(base, cand)
    rule_ids = [f["rule_id"] for f in res["findings"]]
    assert "OP-01" in rule_ids  # Removed GET /items (Breaking)
    assert "OP-02" in rule_ids  # Added POST /items (Non-breaking)

    op01 = next(f for f in res["findings"] if f["rule_id"] == "OP-01")
    assert op01["classification"] == "breaking"
    op02 = next(f for f in res["findings"] if f["rule_id"] == "OP-02")
    assert op02["classification"] == "non_breaking"

    # Unchanged control
    res_control = _run_compare(base, base)
    assert len(res_control["findings"]) == 0


def test_parameter_rules():
    base = _base_spec(paths_obj={
        "/test": {
            "get": {
                "parameters": [
                    {"name": "filter", "in": "query", "required": False, "schema": {"type": "string"}},
                    {"name": "token", "in": "query", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "ok"}}
            }
        }
    })
    cand = _base_spec(paths_obj={
        "/test": {
            "get": {
                "parameters": [
                    {"name": "filter", "in": "query", "required": True, "schema": {"type": "string"}},  # PA-01 (opt to req)
                    {"name": "token", "in": "query", "required": False, "schema": {"type": "string"}},  # PA-02 (req to opt)
                    {"name": "new_req", "in": "query", "required": True, "schema": {"type": "string"}},  # PA-01 (add req)
                    {"name": "new_opt", "in": "query", "required": False, "schema": {"type": "string"}},  # PA-02 (add opt)
                ],
                "responses": {"200": {"description": "ok"}}
            }
        }
    })
    res = _run_compare(base, cand)
    pa01_findings = [f for f in res["findings"] if f["rule_id"] == "PA-01"]
    assert len(pa01_findings) == 2
    assert all(f["classification"] == "breaking" for f in pa01_findings)

    pa02_findings = [f for f in res["findings"] if f["rule_id"] == "PA-02"]
    assert len(pa02_findings) == 2
    assert all(f["classification"] == "non_breaking" for f in pa02_findings)


def test_request_body_and_media_type_rules():
    base = _base_spec(paths_obj={
        "/upload": {
            "post": {
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {"schema": {"type": "string"}},
                        "text/plain": {"schema": {"type": "string"}},
                    }
                },
                "responses": {"200": {"description": "ok"}}
            }
        }
    })
    cand = _base_spec(paths_obj={
        "/upload": {
            "post": {
                "requestBody": {
                    "required": False,  # RB-02: req to opt (Non-breaking)
                    "content": {
                        "application/json": {"schema": {"type": "string"}},
                        # text/plain removed: MD-01 (Breaking)
                        "application/xml": {"schema": {"type": "string"}},  # MD-02: add accepted (Non-breaking)
                    }
                },
                "responses": {"200": {"description": "ok"}}
            }
        }
    })
    res = _run_compare(base, cand)
    rule_ids = {f["rule_id"] for f in res["findings"]}
    assert "RB-02" in rule_ids
    assert "MD-01" in rule_ids
    assert "MD-02" in rule_ids

    # Reverse direction: cand -> base makes body required (RB-01: Breaking)
    rev = _run_compare(cand, base)
    rev_rule_ids = {f["rule_id"] for f in rev["findings"]}
    assert "RB-01" in rev_rule_ids
    rb01 = next(f for f in rev["findings"] if f["rule_id"] == "RB-01")
    assert rb01["classification"] == "breaking"


def test_response_status_rules():
    base = _base_spec(paths_obj={"/test": {"get": {"responses": {"200": {"description": "ok"}, "404": {"description": "not found"}}}}})
    cand = _base_spec(paths_obj={"/test": {"get": {"responses": {"200": {"description": "ok"}, "500": {"description": "error"}}}}})

    res = _run_compare(base, cand)
    rule_ids = {f["rule_id"] for f in res["findings"]}
    assert "RS-01" in rule_ids  # 404 removed (Review required)
    assert "RS-02" in rule_ids  # 500 added (Review required)
    for f in res["findings"]:
        assert f["classification"] == "review_required"


def test_schema_enum_direction_rules():
    # In request: remove enum is Breaking (SC-02), add enum is Non-breaking (SC-03)
    base_req = _base_spec(
        paths_obj={"/test": {"post": {"requestBody": {"content": {"application/json": {"schema": {"type": "string", "enum": ["A", "B"]}}}}, "responses": {"200": {"description": "ok"}}}}}
    )
    cand_req = _base_spec(
        paths_obj={"/test": {"post": {"requestBody": {"content": {"application/json": {"schema": {"type": "string", "enum": ["B", "C"]}}}}, "responses": {"200": {"description": "ok"}}}}}
    )
    res_req = _run_compare(base_req, cand_req)
    sc02_req = next(f for f in res_req["findings"] if f["rule_id"] == "SC-02")
    assert sc02_req["classification"] == "breaking"
    sc03_req = next(f for f in res_req["findings"] if f["rule_id"] == "SC-03")
    assert sc03_req["classification"] == "non_breaking"

    # In response: add enum is Breaking under exhaustive-client assumption (SC-03), remove enum is Non-breaking (SC-02)
    base_resp = _base_spec(
        paths_obj={"/test": {"get": {"responses": {"200": {"content": {"application/json": {"schema": {"type": "string", "enum": ["A", "B"]}}}}}}}}
    )
    cand_resp = _base_spec(
        paths_obj={"/test": {"get": {"responses": {"200": {"content": {"application/json": {"schema": {"type": "string", "enum": ["B", "C"]}}}}}}}}
    )
    res_resp = _run_compare(base_resp, cand_resp)
    sc03_resp = next(f for f in res_resp["findings"] if f["rule_id"] == "SC-03")
    assert sc03_resp["classification"] == "breaking"
    sc02_resp = next(f for f in res_resp["findings"] if f["rule_id"] == "SC-02")
    assert sc02_resp["classification"] == "non_breaking"


def test_schema_nullability_and_bounds_rules():
    base = _base_spec(
        paths_obj={"/test": {"post": {
            "requestBody": {
                "content": {"application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "age": {"type": "integer", "minimum": 18, "nullable": False},
                            "name": {"type": "string", "maxLength": 100, "nullable": True}
                        }
                    }
                }}
            },
            "responses": {"200": {"description": "ok"}}
        }}}
    )
    cand = _base_spec(
        paths_obj={"/test": {"post": {
            "requestBody": {
                "content": {"application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "age": {"type": "integer", "minimum": 21, "nullable": True},  # min tightened: SC-10 (Breaking); null allowed: SC-08 (Non-breaking)
                            "name": {"type": "string", "maxLength": 50, "nullable": False}  # max tightened: SC-10 (Breaking); null forbidden: SC-09 (Breaking)
                        }
                    }
                }}
            },
            "responses": {"200": {"description": "ok"}}
        }}}
    )
    res = _run_compare(base, cand)
    rule_ids = {f["rule_id"] for f in res["findings"]}
    assert "SC-10" in rule_ids
    assert "SC-08" in rule_ids
    assert "SC-09" in rule_ids


def test_additional_properties_rules():
    base = _base_spec(
        paths_obj={"/test": {"post": {
            "requestBody": {"content": {"application/json": {"schema": {"type": "object", "additionalProperties": True}}}},
            "responses": {"200": {"description": "ok"}}
        }}}
    )
    cand = _base_spec(
        paths_obj={"/test": {"post": {
            "requestBody": {"content": {"application/json": {"schema": {"type": "object", "additionalProperties": False}}}},
            "responses": {"200": {"description": "ok"}}
        }}}
    )
    res = _run_compare(base, cand)
    sc12 = next(f for f in res["findings"] if f["rule_id"] == "SC-12")
    assert sc12["classification"] == "breaking"

    # Reverse: cand -> base opens additionalProperties (SC-13: non-breaking in request)
    rev = _run_compare(cand, base)
    sc13 = next(f for f in rev["findings"] if f["rule_id"] == "SC-13")
    assert sc13["classification"] == "non_breaking"
