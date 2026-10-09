"""Safe parser for OpenAPI 3.0.x JSON and restricted YAML contracts.

Enforces bounds, duplicate key detection, alias rejection, and reference safety
per security-and-privacy.md.
"""

import json
import math
import re
from typing import Any
import yaml

MAX_DOCUMENT_BYTES = 1024 * 1024  # 1 MiB
MAX_COMBINED_BYTES = 2 * 1024 * 1024  # 2 MiB
MAX_NESTING_DEPTH = 64
MAX_VALUES = 50000
MAX_OPERATIONS = 2000
SUPPORTED_VERSIONS = {"3.0.0", "3.0.1", "3.0.2", "3.0.3"}


class ParseError(ValueError):
    """Base error for document parsing and validation failures."""
    pass


class DocumentSizeLimitError(ParseError):
    """Raised when document exceeds size bounds."""
    pass


class NestingDepthLimitError(ParseError):
    """Raised when document exceeds maximum nesting depth."""
    pass


class DuplicateKeyError(ParseError):
    """Raised when JSON or YAML contains duplicate mapping keys."""
    pass


class UnsupportedOpenAPIVersionError(ParseError):
    """Raised when OpenAPI version is not in 3.0.0 - 3.0.3 allowlist."""
    pass


class ExternalReferenceError(ParseError):
    """Raised when a $ref targets an external URL or file."""
    pass


class MissingInternalReferenceError(ParseError):
    """Raised when an internal $ref cannot be resolved."""
    pass


def _check_finite_json_constant(value: str) -> None:
    raise ParseError(f"Non-finite JSON constant '{value}' is disallowed.")


def _detect_duplicate_pairs(pairs: list[tuple[Any, Any]]) -> dict[str, Any]:
    seen: set[str] = set()
    result: dict[str, Any] = {}
    for key, val in pairs:
        if not isinstance(key, str):
            key_str = str(key)
        else:
            key_str = key
        if key_str in seen:
            raise DuplicateKeyError(f"Duplicate mapping key '{key_str}' detected.")
        seen.add(key_str)
        result[key_str] = val
    return result


class RestrictedSafeYamlLoader(yaml.SafeLoader):
    """Safe YAML loader rejecting anchors, aliases, and duplicate keys with depth tracking."""
    depth: int = 0

    def compose_node(self, parent: Any, index: Any) -> yaml.Node:
        if self.check_event(yaml.events.AliasEvent):
            event = self.get_event()
            raise ParseError(f"YAML alias '*{getattr(event, 'anchor', '')}' rejected by security policy.")
        event = self.peek_event()
        if getattr(event, "anchor", None):
            raise ParseError(f"YAML anchor '&{event.anchor}' rejected by security policy.")

        self.depth += 1
        if self.depth > MAX_NESTING_DEPTH:
            raise NestingDepthLimitError(f"YAML nesting depth exceeded limit of {MAX_NESTING_DEPTH}.")
        try:
            return super().compose_node(parent, index)
        finally:
            self.depth -= 1

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        if not isinstance(node, yaml.MappingNode):
            raise ParseError(f"Expected mapping node, got {node.id}")
        seen_keys: set[Any] = set()
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, (str, int)) or isinstance(key, bool):
                raise ParseError("YAML keys must be strings (numeric response codes are accepted).")
            key = str(key)
            if key in seen_keys:
                raise DuplicateKeyError(f"Duplicate mapping key '{key}' detected in YAML.")
            seen_keys.add(key)
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


RestrictedSafeYamlLoader.add_constructor("tag:yaml.org,2002:timestamp", RestrictedSafeYamlLoader.construct_scalar)


def _verify_depth(obj: Any, current_depth: int = 0) -> None:
    if current_depth > MAX_NESTING_DEPTH:
        raise NestingDepthLimitError(f"Nesting depth exceeded maximum limit of {MAX_NESTING_DEPTH}.")
    if isinstance(obj, dict):
        for v in obj.values():
            _verify_depth(v, current_depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            _verify_depth(item, current_depth + 1)


def _verify_values(obj: Any) -> None:
    pending = [obj]
    count = 0
    while pending:
        value = pending.pop()
        count += 1
        if count > MAX_VALUES:
            raise DocumentSizeLimitError("Document exceeds the 50,000-value complexity limit.")
        if isinstance(value, dict):
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
        elif isinstance(value, float) and not math.isfinite(value):
            raise ParseError("Non-finite numbers are prohibited.")
        elif value is not None and not isinstance(value, (str, bool, int, float)):
            raise ParseError("Only JSON-compatible scalar values are supported.")


def parse_specification(content: str | bytes, name: str = "document") -> dict[str, Any]:
    """Parse UTF-8 JSON or restricted YAML string/bytes into Python dict with security checks."""
    if isinstance(content, str):
        raw_bytes = content.encode("utf-8")
    elif isinstance(content, bytes):
        raw_bytes = content
        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ParseError(f"Malformed UTF-8 in {name}: {e}")
    else:
        raise ParseError(f"Invalid content type for {name}: {type(content)}")

    if len(raw_bytes) > MAX_DOCUMENT_BYTES:
        raise DocumentSizeLimitError(
            f"{name} size ({len(raw_bytes)} bytes) exceeds limit of {MAX_DOCUMENT_BYTES} bytes (1 MiB)."
        )

    # First attempt JSON parse
    parsed: Any = None
    trimmed = content.strip()
    if trimmed.startswith("{") or trimmed.startswith("["):
        try:
            parsed = json.loads(
                content,
                object_pairs_hook=_detect_duplicate_pairs,
                parse_constant=_check_finite_json_constant
            )
        except RecursionError:
            raise NestingDepthLimitError("JSON exceeds the nesting limit.") from None
        except json.JSONDecodeError as e:
            # If it started like JSON, report JSON error
            raise ParseError(f"Malformed JSON in {name}: {e.msg} at line {e.lineno} column {e.colno}")
        except DuplicateKeyError:
            raise
    else:
        # Restricted YAML parse
        try:
            parsed = yaml.load(content, Loader=RestrictedSafeYamlLoader)
        except (yaml.YAMLError, ParseError) as e:
            raise ParseError(f"Malformed YAML in {name}: {e}")

    if not isinstance(parsed, dict):
        raise ParseError(f"{name} must be a top-level JSON/YAML mapping object.")

    _verify_depth(parsed)
    _verify_values(parsed)

    # Validate OpenAPI version
    openapi_version = parsed.get("openapi")
    if not openapi_version or not isinstance(openapi_version, str):
        raise ParseError(f"{name} is missing a valid 'openapi' string version declaration.")
    
    version_clean = openapi_version.strip()
    if version_clean not in SUPPORTED_VERSIONS:
        raise UnsupportedOpenAPIVersionError(
            f"Unsupported OpenAPI version '{version_clean}' in {name}. "
            f"Supported versions: {', '.join(sorted(SUPPORTED_VERSIONS))}."
        )

    # Validate references across the document
    _validate_references_safety(parsed, name)
    pending = [parsed]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if "$ref" in value:
                resolve_pointer(parsed, value["$ref"])
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)

    paths = parsed.get("paths")
    if not isinstance(paths, dict):
        raise ParseError("OpenAPI paths must be a mapping.")
    methods = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
    operations = 0
    for path, item in paths.items():
        if not path.startswith("/") or not isinstance(item, dict):
            raise ParseError("Each path must start with '/' and contain a mapping.")
        for method, operation in item.items():
            if method in methods:
                operations += 1
                if not isinstance(operation, dict) or not isinstance(operation.get("responses"), dict):
                    raise ParseError("Each operation must be a mapping with responses.")
    if operations > MAX_OPERATIONS:
        raise DocumentSizeLimitError("Document exceeds the 2,000-operation limit.")

    return parsed


def _validate_references_safety(obj: Any, name: str, current_path: str = "#") -> None:
    """Ensure all $ref elements are internal '#/...' pointers only."""
    if isinstance(obj, dict):
        if "$ref" in obj:
            ref = obj["$ref"]
            if not isinstance(ref, str):
                raise ParseError(f"Invalid non-string $ref at {current_path} in {name}.")
            if not ref.startswith("#/"):
                raise ExternalReferenceError(
                    f"External reference '{ref}' at {current_path} in {name} is prohibited by security policy. "
                    "Only internal '#/...' references are supported."
                )
            # Validate every target, including unused components.
            # The root is supplied separately during the initial validation below.
        for k, v in obj.items():
            escaped_key = k.replace("~", "~0").replace("/", "~1")
            _validate_references_safety(v, name, f"{current_path}/{escaped_key}")
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _validate_references_safety(item, name, f"{current_path}/{idx}")


def resolve_pointer(document: dict[str, Any], pointer: str) -> Any:
    """Resolve an internal JSON pointer like '#/components/schemas/Order' against document."""
    if not pointer.startswith("#"):
        raise ExternalReferenceError(f"Cannot resolve non-internal pointer '{pointer}'.")
    if pointer == "#" or pointer == "#/":
        return document
    
    parts = pointer[2:].split("/")
    current: Any = document
    for part in parts:
        token = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise MissingInternalReferenceError(f"Internal reference '{pointer}' target '{token}' not found.")
            current = current[token]
        elif isinstance(current, list):
            try:
                idx = int(token)
                if idx < 0 or idx >= len(current):
                    raise MissingInternalReferenceError(f"Reference array index '{idx}' out of bounds in '{pointer}'.")
                current = current[idx]
            except ValueError:
                raise MissingInternalReferenceError(f"Invalid array index '{token}' in reference '{pointer}'.")
        else:
            raise MissingInternalReferenceError(f"Cannot traverse into primitive at '{token}' in '{pointer}'.")
    return current
