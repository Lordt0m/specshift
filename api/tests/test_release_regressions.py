"""Release regressions discovered during independent deployment verification."""
import json
import pytest
from api.comparison.engine import compare_specifications, _make_stable_id
from api.comparison.parse import ParseError, resolve_pointer, parse_specification
from rest_framework.test import APIClient


def document(schema=None):
    return {"openapi": "3.0.3", "info": {"title": "Synthetic", "version": "1"}, "paths": {
        "/test": {"get": {"responses": {"200": {"description": "ok", "content": {
            "application/json": {"schema": schema or {"type": "string"}}
        }}}}}
    }}


def compare(a, b):
    return compare_specifications(json.dumps(a), json.dumps(b))


@pytest.fixture(autouse=True)
def clean_rate_buckets():
    from api.middleware import _buckets
    _buckets.clear()


def test_recursive_reference_is_bounded():
    spec = document({"$ref": "#/components/schemas/Node"})
    spec["components"] = {"schemas": {"Node": {"type": "object", "properties": {
        "next": {"$ref": "#/components/schemas/Node"}
    }}}}
    assert compare(spec, spec)["summary"]["breaking_count"] == 0


def test_dangling_unused_reference_rejected():
    spec = document()
    spec["components"] = {"schemas": {"Unused": {"$ref": "#/missing"}}}
    with pytest.raises(ParseError):
        compare(spec, spec)


@pytest.mark.parametrize("value", ["1e999", "NaN", "Infinity"])
def test_nonfinite_values_rejected(value):
    raw = json.dumps(document()).replace('"type": "string"', '"type": "number", "minimum": ' + value)
    with pytest.raises(ParseError):
        parse_specification(raw)


def test_nonstring_yaml_keys_fail_cleanly():
    with pytest.raises(ParseError):
        parse_specification('openapi: 3.0.3\npaths: {}\n? [a, b]\n: value')


def test_unknown_keyword_prevents_clean_conclusion():
    spec = document({"type": "string", "futureConstraint": True})
    assert compare(spec, spec)["summary"]["coverage_gap_count"] > 0


def test_added_bound_is_not_silently_ignored():
    result = compare(document({"type": "string"}), document({"type": "string", "maxLength": 2}))
    assert result["summary"]["review_count"] > 0


def test_security_edit_is_review_required():
    base = document()
    cand = document()
    cand["security"] = [{"token": []}]
    assert compare(base, cand)["summary"]["review_count"] > 0


def test_exact_evidence_at_escaped_pointer():
    base = document({"type": "object", "properties": {"a/b~c": {"type": "string", "nullable": False}}})
    cand = document({"type": "object", "properties": {"a/b~c": {"type": "string", "nullable": True}}})
    result = compare(base, cand)
    for finding in result["findings"]:
        for prefix, spec, pointer_key in (("before", base, "origin_pointer"), ("after", cand, "candidate_pointer")):
            if finding[prefix + "_presence"] != "absent":
                assert resolve_pointer(spec, finding[pointer_key]) == finding[prefix]


def test_identifiers_preserve_case_and_punctuation():
    assert _make_stable_id("finding", "/A") != _make_stable_id("finding", "/a")
    assert _make_stable_id("finding", "/a/b") != _make_stable_id("finding", "/a-b")


def test_enum_reordering_is_not_a_change():
    a = document({"type": "string", "enum": ["a", "b"]})
    b = document({"type": "string", "enum": ["b", "a"]})
    result = compare(a, b)
    assert result["findings"] == []
    assert result["input_digests"]["baseline"] == result["input_digests"]["candidate"]


def test_public_rate_limit_and_reset():
    client = APIClient()
    payload = {"baseline": json.dumps(document()), "candidate": json.dumps(document())}
    for _ in range(10):
        assert client.post('/api/compare/', payload, format='json').status_code == 200
    assert client.post('/api/compare/', payload, format='json').status_code == 429


def test_transport_type_rejected_without_allocation():
    response = APIClient().post('/api/compare/', {"baseline": 1000000000, "candidate": "{}"}, format='json')
    assert response.status_code == 400


def test_disable_public_comparison(monkeypatch):
    monkeypatch.setenv('PUBLIC_COMPARE_ENABLED', 'false')
    assert APIClient().post('/api/compare/', {}, format='json').status_code == 503


SCHEMA_CASES = [
    ({"type": "string"}, {"type": "integer"}, "SC-01", "review_required", "review_required"),
    ({"type": "string", "enum": ["a", "b"]}, {"type": "string", "enum": ["a"]}, "SC-02", "breaking", "non_breaking"),
    ({"type": "string", "enum": ["a"]}, {"type": "string", "enum": ["a", "b"]}, "SC-03", "non_breaking", "breaking"),
    ({"type": "object", "properties": {"name": {"type": "string"}}}, {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}, "SC-04", "breaking", "non_breaking"),
    ({"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}, {"type": "object", "properties": {"name": {"type": "string"}}}, "SC-05", "non_breaking", "breaking"),
    ({"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}, {"type": "object", "properties": {}}, "SC-06", "review_required", "breaking"),
    ({"type": "object"}, {"type": "object", "properties": {"name": {"type": "string"}}}, "SC-07", "non_breaking", "non_breaking"),
    ({"type": "string", "nullable": False}, {"type": "string", "nullable": True}, "SC-08", "non_breaking", "breaking"),
    ({"type": "string", "nullable": True}, {"type": "string", "nullable": False}, "SC-09", "breaking", "non_breaking"),
    ({"type": "integer", "minimum": 1}, {"type": "integer", "minimum": 2}, "SC-10", "breaking", "non_breaking"),
    ({"type": "integer", "minimum": 2}, {"type": "integer", "minimum": 1}, "SC-11", "non_breaking", "breaking"),
    ({"type": "object", "additionalProperties": True}, {"type": "object", "additionalProperties": False}, "SC-12", "breaking", "non_breaking"),
    ({"type": "object", "additionalProperties": False}, {"type": "object", "additionalProperties": True}, "SC-13", "non_breaking", "breaking"),
]


def schema_document(schema, context):
    spec = document(schema)
    if context == 'request':
        spec['paths']['/test'] = {'post': {
            'responses': {'200': {'description': 'ok'}},
            'requestBody': {'content': {'application/json': {'schema': schema}}}
        }}
    return spec


@pytest.mark.parametrize('before,after,rule,request_class,response_class', SCHEMA_CASES)
@pytest.mark.parametrize('context', ['request', 'response'])
def test_directional_schema_rule_matrix(before, after, rule, request_class, response_class, context):
    baseline = schema_document(before, context)
    candidate = schema_document(after, context)
    result = compare(baseline, candidate)
    findings = [f for f in result['findings'] if f['rule_id'] == rule]
    assert len(findings) == 1
    assert findings[0]['classification'] == (request_class if context == 'request' else response_class)
    assert findings[0]['affected_operations'] == [('POST' if context == 'request' else 'GET') + ' /test']
    assert compare(baseline, baseline)['findings'] == []


def test_work_deadline_is_a_controlled_error():
    from api.comparison.engine import ComparisonEngine, ComparisonTimeoutError
    engine = ComparisonEngine(document(), document())
    engine.deadline = 0
    with pytest.raises(ComparisonTimeoutError):
        engine.run()


def test_non_schema_reference_is_an_explicit_gap():
    spec = document()
    spec['components'] = {'parameters': {'q': {'name': 'q', 'in': 'query', 'schema': {'type': 'string'}}}}
    spec['paths']['/test']['get']['parameters'] = [{'$ref': '#/components/parameters/q'}]
    result = compare(spec, spec)
    assert result['summary']['coverage_gap_count'] == 1
    assert result['summary']['covered_operations'] == 0


def test_readonly_field_is_not_falsely_classified_as_request_break():
    before = {'type': 'object', 'properties': {'id': {'type': 'string', 'readOnly': True}}}
    after = {**before, 'required': ['id']}
    result = compare(schema_document(before, 'request'), schema_document(after, 'request'))
    assert result['summary']['breaking_count'] == 0
    assert result['summary']['coverage_gap_count'] > 0
