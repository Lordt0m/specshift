"""Security, bounds, safe parsing, and hostile input test suite.

Verifies all constraints from security-and-privacy.md.
"""

import json
import pytest

from api.comparison.parse import (
    parse_specification,
    DocumentSizeLimitError,
    NestingDepthLimitError,
    DuplicateKeyError,
    ExternalReferenceError,
    MissingInternalReferenceError,
    UnsupportedOpenAPIVersionError,
    ParseError,
)


def test_valid_openapi_versions():
    for v in ["3.0.0", "3.0.1", "3.0.2", "3.0.3"]:
        spec = f'{{"openapi": "{v}", "info": {{"title": "T", "version": "1"}}, "paths": {{}}}}'
        parsed = parse_specification(spec)
        assert parsed["openapi"] == v


def test_unsupported_openapi_versions():
    for v in ["2.0", "3.1.0", "3.1.1", "3.0.4", "4.0.0"]:
        spec = f'{{"openapi": "{v}", "info": {{"title": "T", "version": "1"}}, "paths": {{}}}}'
        with pytest.raises(UnsupportedOpenAPIVersionError):
            parse_specification(spec)


def test_malformed_utf8():
    with pytest.raises(ParseError, match="Malformed UTF-8"):
        parse_specification(b"\xff\xfe\x00\x00")


def test_size_limit_exceeded():
    huge_data = " " * (1024 * 1024 + 10)  # > 1 MiB
    huge_spec = f'{{"openapi": "3.0.3", "info": {{"title": "{huge_data}", "version": "1"}}, "paths": {{}}}}'
    with pytest.raises(DocumentSizeLimitError):
        parse_specification(huge_spec)


def test_nesting_depth_limit():
    nested = '{"openapi": "3.0.3", "info": {"title": "T", "version": "1"}, "paths": '
    for _ in range(70):
        nested += '{"level": '
    nested += '1' + ('}' * 71)
    with pytest.raises(NestingDepthLimitError):
        parse_specification(nested)


def test_duplicate_keys_json():
    dup_json = '{"openapi": "3.0.3", "info": {"title": "T", "version": "1"}, "paths": {}, "paths": {}}'
    with pytest.raises(DuplicateKeyError):
        parse_specification(dup_json)


def test_duplicate_keys_yaml():
    dup_yaml = """
openapi: "3.0.3"
info:
  title: "T"
  version: "1"
paths: {}
paths: {}
"""
    with pytest.raises(ParseError, match="Duplicate mapping key"):
        parse_specification(dup_yaml)


def test_yaml_anchor_and_alias_rejection():
    # Anchor rejected
    yaml_with_anchor = """
openapi: "3.0.3"
info:
  title: &title "T"
  version: "1"
paths: {}
"""
    with pytest.raises(ParseError, match="YAML anchor"):
        parse_specification(yaml_with_anchor)

    # Alias rejected
    yaml_with_alias = """
openapi: "3.0.3"
info:
  title: "T"
  version: *title
paths: {}
"""
    with pytest.raises(ParseError, match="YAML alias"):
        parse_specification(yaml_with_alias)


def test_external_reference_rejection():
    # Prohibit external http/https/file/$ref
    external_refs = [
        "https://example.com/schema.json",
        "http://evil.com/spec.yaml",
        "file:///etc/passwd",
        "../common/models.yaml#/User",
    ]
    for ext_ref in external_refs:
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "T", "version": "1"},
            "paths": {},
            "components": {
                "schemas": {
                    "Model": {"$ref": ext_ref}
                }
            }
        }
        with pytest.raises(ExternalReferenceError):
            parse_specification(json.dumps(spec))


def test_missing_internal_reference_fails_resolution():
    from api.comparison.parse import resolve_pointer
    doc = {"openapi": "3.0.3", "components": {"schemas": {"A": {"type": "string"}}}}
    with pytest.raises(MissingInternalReferenceError):
        resolve_pointer(doc, "#/components/schemas/NonExistent")
